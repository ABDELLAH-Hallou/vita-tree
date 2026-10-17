"""Create a reviewable PyPI promotion and verify its immutable TestPyPI artifacts."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.parse import urlencode, urlparse
from urllib.error import HTTPError
from urllib.request import urlopen

from validate_release import validate

PROMOTIONS = '.github/pypi-releases'
BOT = {'name': 'github-actions[bot]', 'email': '41898282+github-actions[bot]@users.noreply.github.com'}


def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()


def api(path, data=None):
    command = ['gh', 'api', path]
    if data is not None:
        command += ['--method', 'POST', '--input', '-']
    result = subprocess.run(command, input=json.dumps(data) if data is not None else None,
                            capture_output=True, text=True, encoding='utf-8', check=True)
    return json.loads(result.stdout)


def filenames(version):
    validate('v' + version, version)
    return {f'vita_tree-{version}-py3-none-any.whl', f'vita_tree-{version}.tar.gz'}


def validate_manifest(record):
    if not isinstance(record, dict) or set(record) != {'version', 'sourceCommit', 'testRunId', 'files'}:
        raise ValueError('Invalid promotion manifest fields')
    expected = filenames(record['version'])
    if not re.fullmatch(r'[0-9a-f]{40}', record['sourceCommit']):
        raise ValueError('Invalid source commit')
    if type(record['testRunId']) is not int or record['testRunId'] <= 0:
        raise ValueError('Invalid TestPyPI workflow run ID')
    if not isinstance(record['files'], dict) or set(record['files']) != expected:
        raise ValueError('Promotion must contain exactly the versioned wheel and source archive')
    if any(not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value)
           for value in record['files'].values()):
        raise ValueError('Invalid artifact SHA-256')
    return record


def make_manifest(version, commit, run_id, directory):
    expected = filenames(version)
    if {path.name for path in directory.iterdir()} != expected:
        raise ValueError('Distribution folder must contain exactly the candidate wheel and source archive')
    return validate_manifest({'version': version, 'sourceCommit': commit, 'testRunId': run_id,
                              'files': {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                                        for name in sorted(expected)}})


def verify_bytes(record, directory):
    validate_manifest(record)
    if {path.name for path in directory.iterdir()} != set(record['files']):
        raise ValueError('Downloaded distribution file list differs from approved promotion')
    for name, expected in record['files'].items():
        path = directory / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'TestPyPI artifact differs from the tested candidate: {name}')


def json_from_url(url):
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def download_candidate(record, directory):
    """Use TestPyPI only for this package, never to resolve its dependencies."""
    validate_manifest(record)
    metadata = json_from_url(f'https://test.pypi.org/pypi/vita-tree/{record["version"]}/json')
    if metadata['info']['version'] != record['version']:
        raise ValueError('TestPyPI returned a different version')
    remote = {item['filename']: item for item in metadata['urls']}
    if set(remote) != set(record['files']):
        raise ValueError('TestPyPI file list differs from the tested candidate')
    # Reject the whole candidate before downloading either artifact. PyPI's
    # metadata order need not match the manifest's filename order.
    for name, expected in record['files'].items():
        item = remote[name]
        parsed = urlparse(item['url'])
        if (parsed.scheme != 'https' or parsed.hostname not in {'test-files.pythonhosted.org', 'files.pythonhosted.org'}
                or parsed.username or parsed.password or parsed.port not in (None, 443)):
            raise ValueError('Unexpected TestPyPI download host')
        if item.get('yanked') or item['digests']['sha256'] != expected:
            raise ValueError(f'TestPyPI digest mismatch or withdrawn artifact: {name}')
    directory.mkdir(parents=True, exist_ok=True)
    for name, expected in record['files'].items():
        item = remote[name]
        with urlopen(item['url'], timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'Downloaded artifact digest mismatch: {name}')
        target = directory / name
        if target.is_symlink():
            raise ValueError('Refusing to overwrite a symlink')
        target.write_bytes(data)
    verify_bytes(record, directory)


def check_existing_pypi(record):
    """Permit retrying a partial upload only when existing files match exactly."""
    validate_manifest(record)
    try:
        metadata = json_from_url(f'https://pypi.org/pypi/vita-tree/{record["version"]}/json')
    except HTTPError as error:
        if error.code == 404:
            return
        raise
    for item in metadata['urls']:
        if (item['filename'] not in record['files'] or item.get('yanked')
                or item['digests']['sha256'] != record['files'][item['filename']]):
            raise ValueError('PyPI already contains a different or withdrawn artifact for this version')


def promotion_body(record, repository):
    version = record['version']
    hashes = '\n'.join(f'- `{name}`: `{sha}`' for name, sha in record['files'].items())
    return f'''## Publish vita-tree {version} to PyPI

Stage 2 of 2. This candidate was published to TestPyPI and passed automated installation checks.
Merge this PR only after you finish testing it. Merging publishes the exact wheel and source
archive below to PyPI; it does not rebuild from the current main branch.

TestPyPI: https://test.pypi.org/project/vita-tree/{version}/
Source: {record['sourceCommit']}
Verification: https://github.com/{repository}/actions/runs/{record['testRunId']}

### Try the candidate in a fresh environment

```sh
python -m venv .venv-vita-test
# Activate that environment first, then:
python -m pip download --no-deps --only-binary=:all: --index-url https://test.pypi.org/simple/ --dest candidate vita-tree=={version}
python -m pip install "./candidate/vita_tree-{version}-py3-none-any.whl[ai]"
vt run /path/to/a/test-cv-repository
```

Only vita-tree is downloaded from TestPyPI; dependencies resolve through your normal pip index.
If testing finds a bug, leave this PR unmerged (or close it) and release a new version with the fix.
Do not edit the candidate or reuse its version number.

### Approved SHA-256 digests

{hashes}
'''


def open_promotion(record, repository):
    validate_manifest(record)
    version = record['version']
    branch = f'release/pypi-v{version}'
    path = f'{PROMOTIONS}/{version}.json'
    prefix = f'repos/{repository}'
    content = json.dumps(record, indent=2) + '\n'
    matches = api(f'{prefix}/git/matching-refs/heads/{branch}')
    existing = next((ref for ref in matches if ref['ref'] == 'refs/heads/' + branch), None)
    if existing:
        saved = api(f'{prefix}/contents/{path}?{urlencode({"ref": branch})}')
        if json.loads(base64.b64decode(saved['content'])) != record:
            raise ValueError('An existing promotion has different provenance. Rerun its original workflow or use a new version; never overwrite a reviewed candidate.')
    else:
        base = api(f'{prefix}/git/ref/heads/main')['object']['sha']
        tree = api(f'{prefix}/git/commits/{base}')['tree']['sha']
        blob = api(f'{prefix}/git/blobs', {'content': content, 'encoding': 'utf-8'})['sha']
        tree = api(f'{prefix}/git/trees', {'base_tree': tree, 'tree': [
            {'path': path, 'mode': '100644', 'type': 'blob', 'sha': blob}]})['sha']
        commit = api(f'{prefix}/git/commits', {'message': f'chore: approve vita-tree {version} for PyPI',
                     'tree': tree, 'parents': [base], 'author': BOT, 'committer': BOT})['sha']
        api(f'{prefix}/git/refs', {'ref': 'refs/heads/' + branch, 'sha': commit})
    query = urlencode({'head': repository.split('/')[0] + ':' + branch, 'base': 'main', 'state': 'all'})
    prs = api(f'{prefix}/pulls?{query}')
    if prs:
        pr = prs[0]
        if pr['state'] == 'closed' and not pr.get('merged_at'):
            raise ValueError('This promotion PR was closed without merging. Use a new version for a replacement candidate.')
    else:
        pr = api(f'{prefix}/pulls', {'title': f'chore: publish vita-tree {version} to PyPI', 'head': branch,
                                    'base': 'main', 'body': promotion_body(record, repository)})
    print(pr['html_url'])
    return pr


def verify_approval(repository, number):
    prefix = f'repos/{repository}'
    pr = api(f'{prefix}/pulls/{number}')
    if (not pr.get('merged') or pr['base']['ref'] != 'main'
            or pr['base']['repo']['full_name'] != repository
            or not pr['head'].get('repo') or pr['head']['repo']['full_name'] != repository):
        raise ValueError('Production publishing requires a merged promotion PR from this repository into main')
    match = re.fullmatch(r'release/pypi-v(\d+\.\d+\.\d+)', pr['head']['ref'])
    if not match:
        raise ValueError('Unexpected promotion branch')
    version = match[1]
    filenames(version)
    path = f'{PROMOTIONS}/{version}.json'
    # A promotion approves only an immutable manifest, never extra code changes.
    changed = api(f'{prefix}/pulls/{number}/files?per_page=100')
    if (pr['changed_files'] != 1 or len(changed) != 1
            or changed[0]['filename'] != path or changed[0]['status'] != 'added'):
        raise ValueError('Promotion PR must add exactly its versioned manifest and no other files')
    merged = pr['merge_commit_sha']
    if not re.fullmatch(r'[0-9a-f]{40}', merged):
        raise ValueError('Invalid merge commit')
    git('merge-base', '--is-ancestor', merged, 'origin/main')
    record = validate_manifest(json.loads(git('show', f'{merged}:{path}')))
    if record['version'] != version:
        raise ValueError('Promotion branch and manifest versions differ')
    source = git('rev-parse', f'refs/tags/v{version}^{{commit}}')
    if source != record['sourceCommit']:
        raise ValueError('Release tag no longer matches the tested source')
    git('merge-base', '--is-ancestor', source, merged)
    run = api(f'{prefix}/actions/runs/{record["testRunId"]}')
    if (run['status'] != 'completed' or run['conclusion'] != 'success'
            or run['head_sha'] != source or run['path'].split('@')[0] != '.github/workflows/release.yml'
            or run['event'] not in ('push', 'workflow_dispatch')):
        raise ValueError('The referenced TestPyPI release workflow did not succeed for this source')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare')
    prepare.add_argument('--dist', type=Path, required=True)
    prepare.add_argument('--output', type=Path, required=True)
    download = commands.add_parser('download')
    download.add_argument('--manifest', type=Path, required=True)
    download.add_argument('--dest', type=Path, required=True)
    download.add_argument('--check-pypi', action='store_true')
    create = commands.add_parser('open-pr')
    create.add_argument('--manifest', type=Path, required=True)
    approval = commands.add_parser('approve')
    approval.add_argument('--pr', type=int, required=True)
    approval.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        version = os.environ['RELEASE_TAG'].removeprefix('v')
        validate(os.environ['RELEASE_TAG'], version)
        record = make_manifest(version, os.environ['GITHUB_SHA'], int(os.environ['GITHUB_RUN_ID']), args.dist)
        args.output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    elif args.command == 'download':
        record = validate_manifest(json.loads(args.manifest.read_text(encoding='utf-8')))
        for attempt in range(10):
            try:
                download_candidate(record, args.dest)
                break
            except (OSError, KeyError) as error:
                if attempt == 9:
                    raise
                print(f'TestPyPI not ready ({type(error).__name__}); retrying in 10 seconds', flush=True)
                time.sleep(10)
        if args.check_pypi:
            check_existing_pypi(record)
    elif args.command == 'open-pr':
        record = json.loads(args.manifest.read_text(encoding='utf-8'))
        open_promotion(record, os.environ['GITHUB_REPOSITORY'])
    else:
        if args.pr <= 0:
            raise ValueError('A valid merged PR number is required')
        record = verify_approval(os.environ['GITHUB_REPOSITORY'], args.pr)
        args.output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
