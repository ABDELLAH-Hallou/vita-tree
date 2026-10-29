"""Branch-scoped language discovery and frozen workflow language delivery."""
import json
from pathlib import Path
import unittest

import test_jobs as job_support
from support import git
from vita_tree.languages import BUILTIN, configured, discover


class LanguageTests(unittest.TestCase):
    setUp = job_support.JobTests.setUp
    tearDown = job_support.JobTests.tearDown
    branch = job_support.JobTests.branch
    start = job_support.JobTests.start
    release = job_support.JobTests.release
    wait = job_support.JobTests.wait
    finished = job_support.JobTests.finished
    pipeline_source = job_support.JobTests.pipeline_source
    pipeline_branch = job_support.JobTests.pipeline_branch

    def write(self, folder, data):
        path = folder/'.vita/extensions.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding='utf-8')

    def names(self, branch):
        return {item['code']: item['name'] for item in discover(self.workspace, branch)}

    def test_builtin_merge_normalization_validation_and_secret_isolation(self):
        raw = json.dumps({'language_map': {'SV':'Swedish','en':'English override','pt-BR':'Portuguese (Brazil)',
            '_note':'SECRET','bad code':'Bad','--help':'Bad','x'*65:'Bad','empty':' ',
            'null':None,'object':{},'newline':'Bad\nlabel'},'api_key':'SECRET'})
        names = {item['code']:item['name'] for item in configured(raw)}
        self.assertEqual(names, {**BUILTIN,'en':'English override','sv':'Swedish','pt-br':'Portuguese (Brazil)'})
        self.assertNotIn('SECRET', json.dumps(configured(raw)))
        for value in ('{','null','[]','{"language_map":[]}','{"language_map":null}'):
            self.assertEqual({item['code']:item['name'] for item in configured(value)}, BUILTIN)

    def test_selected_application_config_matches_capture_precedence(self):
        self.write(self.root, {'language_map':{'sv':'Swedish'}})
        branch = self.branch('local-language')
        location = Path(branch['worktree'])
        self.assertEqual(self.names('local-language')['sv'], 'Swedish')
        self.write(location, {'language_map':{'nb':'Norsk','en':'Local English'}})
        self.assertNotIn('sv', self.names('local-language'))
        self.assertEqual(self.names('local-language')['nb'], 'Norsk')
        self.assertEqual(self.names('master')['sv'], 'Swedish')
        capture = self.workspace._ai_context(location,branch['content'],branch['job'],[],'','','')
        self.assertEqual(json.loads(capture['config']['extensions.json'])['language_map'], {'nb':'Norsk','en':'Local English'})
        self.write(location, {})
        self.assertEqual(self.names('local-language'), BUILTIN)
        self.assertEqual(self.workspace.providers('local-language')['languages'], discover(self.workspace,'local-language'))

    def test_committed_and_uncommitted_maps_refresh_without_cross_branch_union(self):
        self.write(self.root, {'language_map':{'sv':'Swedish'}})
        git(self.root,'add','-f','.vita/extensions.json');git(self.root,'commit','-m','Synthetic Swedish map')
        git(self.root,'branch','committed-language')
        self.write(self.root, {'language_map':{'da':'Danish'}})
        self.assertEqual(self.names('committed-language')['sv'], 'Swedish')
        self.assertNotIn('da', self.names('committed-language'))
        self.assertEqual(self.names('master')['da'], 'Danish')
        self.write(self.root, {'language_map':{'sv':'Svenska'}})
        self.assertEqual(self.names('master')['sv'], 'Svenska')

    def test_swedish_reaches_adapt_cover_and_checkpoint_retry(self):
        self.pipeline_source()
        branch = self.pipeline_branch('swedish-run', record_language=True)
        location = Path(branch['worktree'])
        self.write(location, {'language_map':{'sv':'Swedish'}})
        failed = self.control/'swedish-run.cover.fail'
        failed.touch();self.release('swedish-run')
        run = self.start(branch, language='sv', workflow={'steps':['adapt','cover']})
        result = self.finished(run['id'])
        self.assertEqual(result['status'],'failed')
        self.assertEqual(result['language'],'sv')
        for step in ('adapt','cover'):
            self.assertEqual((self.control/f'swedish-run.{step}.language').read_text(), 'sv')
            self.assertEqual(json.loads((self.control/f'swedish-run.{step}.languages.json').read_text()), {'sv':'Swedish'})
        snap = self.workspace.snapshot('swedish-run')
        preview = self.workspace.resume_ai(run['id'],snap['revision'],snap['jobRevision'],preview=True)
        self.assertEqual(preview['reuse'],['adapt'])
        failed.unlink()
        child = self.workspace.resume_ai(run['id'],snap['revision'],snap['jobRevision'],token=preview['token'])
        self.assertEqual(child['language'],'sv')
        self.assertEqual(self.finished(child['id'])['status'],'succeeded')
