"""Fail publication checks on private files, unapproved emails or home paths.

Reports locations and categories only, never matched values. This complements a
credential scanner and human review; it cannot identify every form of private data.
"""
import argparse
import io
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import zipfile

EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
HOME = re.compile(r'(?:[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9_.-]+[\\/]|/(?:Users|home)/[A-Za-z0-9_.-]+/)')
PRIVATE_KEY = re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----')
PRIVATE_PARTS = {'.git', '.vita', '.env', '.pypirc', '.test-artifacts', '.venv', 'node_modules', '__pycache__'}
PRIVATE_SUFFIXES = {'.pem', '.key', '.p12', '.pfx', '.bundle', '.pdf', '.tex', '.log', '.pyc'}
# The project author explicitly approved publishing this contact address.
# Keep exceptions exact: other personal contacts must still fail the scan.
PUBLIC_CONTACT_EMAILS = {'abdeallahhallou33@gmail.com', 'noreply@github.com'}


def email_is_public(value):
    # GitHub's web-flow committer uses this public service address for PR merge
    # commits. Allow the exact address, not personal addresses at github.com.
    if value.lower() in PUBLIC_CONTACT_EMAILS:
        return True
    domain = value.rsplit('@', 1)[1].lower()
    return domain in {'example.com', 'example.org', 'example.net', 'users.noreply.github.com'} or domain.endswith('.invalid')


def inspect(name, data):
    path = PurePosixPath(name.replace('\\', '/'))
    problems = []
    if set(path.parts) & PRIVATE_PARTS or path.suffix.lower() in PRIVATE_SUFFIXES or path.name.startswith('.env.'):
        problems.append((name, 'private file type/path'))
    # Original third-party code includes standard emulated /home paths and
    # encoded font dictionaries resembling email addresses. Preserve upstream
    # files and license attribution; scan them separately with Gitleaks.
    if 'static/vendor/' in str(path):
        return problems
    text = data.decode('utf-8-sig', errors='replace')
    for match in EMAIL.finditer(text):
        if not email_is_public(match.group()):
            problems.append((name, f'personal email at line {text[:match.start()].count(chr(10)) + 1}'))
    for pattern, category in ((HOME, 'user home path'), (PRIVATE_KEY, 'private key')):
        for match in pattern.finditer(text):
            problems.append((name, f'{category} at line {text[:match.start()].count(chr(10)) + 1}'))
    return problems


def git(*args):
    return subprocess.check_output(['git', *args])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dist', type=Path)
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    findings, count = [], 0
    paths = git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')
    for name in sorted(set(paths) - {''}):
        if Path(name).is_file():
            findings.extend(inspect(name, Path(name).read_bytes())); count += 1
    if args.dist:
        archives = sorted(args.dist.glob('*.whl')) + sorted(args.dist.glob('*.tar.gz'))
        if not archives:
            raise SystemExit('No distribution archives found')
        for archive in archives:
            if archive.suffix == '.whl':
                with zipfile.ZipFile(archive) as package:
                    for name in package.namelist():
                        findings.extend(inspect(archive.name + '/' + name, package.read(name))); count += 1
            else:
                with tarfile.open(archive) as package:
                    for member in package.getmembers():
                        if member.isfile():
                            findings.extend(inspect(archive.name + '/' + member.name, package.extractfile(member).read())); count += 1
    if args.history:
        # Publication refs only; editor recovery/checkpoint refs are local data
        # and must not be mirrored to a public remote.
        commits = git('rev-list', 'HEAD', '--branches', '--tags', '--remotes').decode().splitlines()
        for commit in commits:
            metadata = git('show', '-s', '--format=%an <%ae>%n%cn <%ce>%n%B', commit)
            findings.extend(inspect(commit[:7] + '/commit-metadata', metadata))
            with tarfile.open(fileobj=io.BytesIO(git('archive', '--format=tar', commit))) as archive:
                for member in archive.getmembers():
                    if member.isfile():
                        findings.extend(inspect(commit[:7] + '/' + member.name, archive.extractfile(member).read())); count += 1
    if findings:
        for location, reason in findings:
            print(f'{location}: {reason} (value redacted)')
        raise SystemExit(f'FAIL: {len(findings)} privacy findings')
    print(f'PASS: {count} files checked; no disallowed email, user-home path, private key or private file found.')


if __name__ == '__main__':
    main()
