"""Release promotion checks use fake APIs and local bytes; no publication."""
import base64
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from support import git, init_repo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import promote_release as promotion


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
        self.directory = Path(self.temp.name)
        self.version = '1.4.0'
        self.commit = 'a' * 40
        self.merged = 'b' * 40
        self.repository = 'example/vita-tree'
        self.data = {name: name.encode() for name in promotion.filenames(self.version)}
        for name, data in self.data.items():
            (self.directory / name).write_bytes(data)
        self.record = promotion.make_manifest(self.version, self.commit, 123, self.directory)
        self.path = promotion.PROMOTIONS + '/1.4.0.json'
        self.pr = {'merged': True, 'merge_commit_sha': self.merged, 'changed_files': 1,
                   'base': {'ref': 'main', 'repo': {'full_name': self.repository}},
                   'head': {'ref': 'release/pypi-v1.4.0', 'repo': {'full_name': self.repository}}}
        self.run = {'status': 'completed', 'conclusion': 'success', 'head_sha': self.commit,
                    'path': '.github/workflows/release.yml', 'event': 'push'}
        self.files = [{'filename': self.path, 'status': 'added'}]

    def tearDown(self):
        self.temp.cleanup()

    def fake_api(self, path, data=None):
        if path.endswith('/pulls/42'):
            return self.pr
        if '/pulls/42/files?' in path:
            return self.files
        if path.endswith('/actions/runs/123'):
            return self.run
        self.fail('Unexpected API call: ' + path)

    def fake_git(self, *args):
        if args[0] == 'show':
            self.assertEqual(args[1], self.merged + ':' + self.path)
            return json.dumps(self.record)
        if args[0] == 'rev-parse':
            self.assertEqual(args[1], 'refs/tags/v1.4.0^{commit}')
            return self.commit
        self.assertEqual(args[:2], ('merge-base', '--is-ancestor'))
        return ''

    def approve(self):
        with patch.object(promotion, 'api', side_effect=self.fake_api), patch.object(promotion, 'git', side_effect=self.fake_git):
            return promotion.verify_approval(self.repository, 42)

    def test_candidate_requires_exact_files_and_detects_modified_bytes(self):
        promotion.verify_bytes(self.record, self.directory)
        first = next(iter(self.data))
        (self.directory / first).write_bytes(b'changed after testing')
        with self.assertRaisesRegex(ValueError, 'differs'):
            promotion.verify_bytes(self.record, self.directory)
        (self.directory / 'extra.whl').write_bytes(b'unreviewed')
        with self.assertRaises(ValueError):
            promotion.make_manifest(self.version, self.commit, 123, self.directory)

    def test_manifest_rejects_unsafe_paths_versions_and_provenance(self):
        variants = [dict(self.record, version='../1.4.0'), dict(self.record, sourceCommit='main'),
                    dict(self.record, testRunId=True), dict(self.record, testRunId=0),
                    dict(self.record, files={'../other.whl': 'f'*64}), dict(self.record, extra='field')]
        for record in variants:
            with self.subTest(record=record), self.assertRaises(ValueError):
                promotion.validate_manifest(record)

    def metadata(self):
        return {'info': {'version': self.version}, 'urls': [
            {'filename': name, 'url': 'https://test-files.pythonhosted.org/' + name,
             'digests': {'sha256': self.record['files'][name]}, 'yanked': False} for name in self.data]}

    def test_download_validates_remote_metadata_and_every_downloaded_byte(self):
        metadata = self.metadata()
        def download(url, **kwargs):
            return io.BytesIO(self.data[url.rsplit('/', 1)[-1]])
        with patch.object(promotion, 'json_from_url', return_value=metadata), patch.object(promotion, 'urlopen', side_effect=download):
            promotion.download_candidate(self.record, self.directory)
        with patch.object(promotion, 'json_from_url', return_value=metadata), patch.object(promotion, 'urlopen', return_value=io.BytesIO(b'tampered')):
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                promotion.download_candidate(self.record, self.directory)

    def test_download_rejects_changed_remote_hashes_extra_files_and_hosts(self):
        changes = [('url', 'https://example.invalid/file'), ('yanked', True),
                   ('digests', {'sha256': 'c'*64})]
        for index in range(len(self.data)):
            for field, value in changes:
                metadata = self.metadata(); metadata['urls'][index][field] = value
                with self.subTest(index=index, field=field), patch.object(promotion, 'json_from_url', return_value=metadata), patch.object(promotion, 'urlopen') as download:
                    with self.assertRaises(ValueError):
                        promotion.download_candidate(self.record, self.directory)
                    download.assert_not_called()
        metadata = self.metadata(); metadata['urls'].append({'filename': 'extra.whl'})
        with patch.object(promotion, 'json_from_url', return_value=metadata), self.assertRaises(ValueError):
            promotion.download_candidate(self.record, self.directory)

    def test_only_merged_same_repository_promotion_can_approve(self):
        self.assertEqual(self.approve(), self.record)
        original = copy.deepcopy(self.pr)
        for modify in (lambda p: p.update(merged=False), lambda p: p['head'].update(repo=None),
                       lambda p: p['head']['repo'].update(full_name='fork/vita-tree'),
                       lambda p: p['base'].update(ref='develop'), lambda p: p['head'].update(ref='feature/test')):
            self.pr = copy.deepcopy(original); modify(self.pr)
            with self.subTest(pr=self.pr), self.assertRaises(ValueError):
                self.approve()

    def test_changed_files_and_failed_or_unrelated_workflows_block_publication(self):
        self.pr['changed_files'] = 2
        with self.assertRaises(ValueError):
            self.approve()
        self.pr['changed_files'] = 1
        self.files[0]['status'] = 'modified'
        with self.assertRaises(ValueError):
            self.approve()
        self.files[0]['status'] = 'added'
        for field, value in [('status', 'in_progress'), ('conclusion', 'failure'), ('head_sha', 'c'*40),
                             ('path', '.github/workflows/ci.yml'), ('event', 'pull_request')]:
            with self.subTest(field=field), patch.dict(self.run, {field: value}), self.assertRaises(ValueError):
                self.approve()
        with patch.dict(self.record, sourceCommit='c'*40), self.assertRaisesRegex(ValueError, 'tag'):
            self.approve()

    def test_open_promotion_creates_only_manifest_and_never_merges(self):
        calls = []
        def fake(path, data=None):
            calls.append((path, data))
            if 'matching-refs' in path or '/pulls?' in path:
                return []
            if path.endswith('/git/ref/heads/main'):
                return {'object': {'sha': 'b'*40}}
            if path.endswith('/git/commits/' + 'b'*40):
                return {'tree': {'sha': 'c'*40}}
            if path.endswith('/pulls'):
                return {'html_url': 'https://github.com/example/vita-tree/pull/42'}
            return {'sha': 'd'*40}
        with patch.object(promotion, 'api', side_effect=fake), patch('builtins.print'):
            promotion.open_promotion(self.record, self.repository)
        tree = next(data for path, data in calls if path.endswith('/git/trees'))
        self.assertEqual([entry['path'] for entry in tree['tree']], [self.path])
        pr = next(data for path, data in calls if path.endswith('/pulls'))
        self.assertEqual(pr['head'], 'release/pypi-v1.4.0')
        self.assertIn('Merge this PR only after', pr['body'])
        self.assertFalse(any('/merge' in path for path, _ in calls))

    def test_retry_reuses_pr_without_updating_reviewed_candidate(self):
        calls = []
        def fake(path, data=None):
            calls.append(data)
            if 'matching-refs' in path:
                return [{'ref': 'refs/heads/release/pypi-v1.4.0'}]
            if '/contents/' in path:
                return {'content': base64.b64encode(json.dumps(self.record).encode()).decode()}
            return [{'state': 'open', 'html_url': 'https://github.com/example/vita-tree/pull/42'}]
        with patch.object(promotion, 'api', side_effect=fake), patch('builtins.print'):
            promotion.open_promotion(self.record, self.repository)
            self.assertTrue(all(data is None for data in calls))
            changed = dict(self.record, testRunId=456)
            with self.assertRaisesRegex(ValueError, 'different provenance'):
                promotion.open_promotion(changed, self.repository)

    def test_pypi_retry_accepts_identical_partial_upload_but_rejects_collision(self):
        with patch.object(promotion, 'json_from_url', side_effect=HTTPError('https://pypi.org', 404, '', {}, None)):
            promotion.check_existing_pypi(self.record)
        metadata = self.metadata(); metadata['urls'] = metadata['urls'][:1]
        with patch.object(promotion, 'json_from_url', return_value=metadata):
            promotion.check_existing_pypi(self.record)
            metadata['urls'][0]['digests']['sha256'] = 'c'*64
            with self.assertRaisesRegex(ValueError, 'different'):
                promotion.check_existing_pypi(self.record)

    def test_approval_reads_actual_merged_manifest_and_rejects_moved_tag(self):
        repo = init_repo(self.directory / 'repository')
        self.record['sourceCommit'] = git(repo, 'rev-parse', 'HEAD')
        self.run['head_sha'] = self.record['sourceCommit']
        git(repo, 'tag', 'v1.4.0')
        target = repo / self.path
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(self.record), encoding='utf-8')
        git(repo, 'add', self.path); git(repo, 'commit', '-m', 'Approve fixture')
        self.pr['merge_commit_sha'] = git(repo, 'rev-parse', 'HEAD')
        git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        with patch.object(promotion, 'api', side_effect=self.fake_api), patch.object(promotion, 'git', side_effect=lambda *args: git(repo, *args)):
            self.assertEqual(promotion.verify_approval(self.repository, 42), self.record)
            git(repo, 'tag', '-f', 'v1.4.0')
            with self.assertRaisesRegex(ValueError, 'tag'):
                promotion.verify_approval(self.repository, 42)


if __name__ == '__main__':
    unittest.main()
