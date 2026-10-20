import json
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from vita_tree.workspace import Workspace, digest
from support import init_repo, SOURCE, git, cleanup_repo


class ApplicationPresentationTests(TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        self.root=init_repo(Path(self.temp.name));self.workspace=Workspace(self.root)

    def tearDown(self):
        self.workspace.close();cleanup_repo(self.temp)

    def test_friendly_name_preserves_spaces_punctuation_and_persists(self):
        app=self.workspace.create_application('master','Acme — ML Engineer','A role',digest(SOURCE))
        self.assertEqual(app['branch'],'acme-ml-engineer')
        self.assertEqual(app['displayName'],'Acme — ML Engineer')
        self.assertEqual(git(self.root,'branch','--show-current'),'master')
        self.assertEqual(app['content'],SOURCE)
        reopened=Workspace(self.root)
        try:
            names={item['name']:item['displayName'] for item in reopened.applications()['branches']}
            self.assertEqual(names['acme-ml-engineer'],'Acme — ML Engineer')
            self.assertEqual(names['master'],'master')
        finally:reopened.close()
        with self.assertRaisesRegex(ValueError,'already exists'):
            self.workspace.create_application('master','ACME — ML ENGINEER','A role',digest(SOURCE))

    def test_distinct_friendly_names_can_share_a_normalized_internal_name(self):
        first=self.workspace.create_application('master','Acme — Engineer','A role',digest(SOURCE))
        second=self.workspace.create_application('master','Acme / Engineer','Another role',digest(SOURCE))
        self.assertNotEqual(first['branch'],second['branch'])
        self.assertEqual(second['displayName'],'Acme / Engineer')

    def test_non_ascii_and_invalid_application_names(self):
        app=self.workspace.create_application('master','研究職','A role',digest(SOURCE))
        self.assertEqual(app['displayName'],'研究職')
        self.assertTrue(app['branch'].startswith('application-'))
        for label in ('', 'a'*101, 'bad\nname', '\x00', None):
            with self.assertRaises(ValueError):self.workspace.create_application('master',label,'A role',digest(SOURCE))

    def test_corrupt_optional_label_does_not_hide_existing_cvs(self):
        path=self.workspace.metadata_path('master');path.parent.mkdir(parents=True)
        path.write_text('invalid json')
        self.assertEqual(self.workspace.applications()['branches'][0]['displayName'],'master')

    def test_draft_detection_covers_job_edits_and_pending_sync(self):
        app=self.workspace.create_application('master','Save states','A role',digest(SOURCE))
        location=Path(app['worktree']);self.assertTrue(app['saveState']['draft'])
        git(location,'add','main.tex','job.md');git(location,'commit','-m','Save fixture')
        current=self.workspace.snapshot(app['branch']);self.assertFalse(current['saveState']['draft'])
        self.workspace.save(app['branch'],'job.md',current['jobRevision'],'Updated job only')
        current=self.workspace.snapshot(app['branch'])
        self.assertFalse(current['dirty']);self.assertTrue(current['saveState']['draft'])
        reverted=self.workspace.save(app['branch'],'job.md',current['jobRevision'],'A role')
        self.assertFalse(reverted['saveState']['draft'])
        self.workspace.save(app['branch'],'job.md',reverted['revision'],'Updated job only')
        git(location,'add','job.md');git(location,'commit','-m','Update role')
        remote=self.root/'.git/local-remote.git';git(self.root,'init','--bare',str(remote))
        git(location,'remote','add','origin',str(remote));git(location,'push','--set-upstream','origin',app['branch'])
        self.assertEqual(self.workspace.snapshot(app['branch'])['saveState']['ahead'],0)
        (location/'main.tex').write_text(SOURCE+'\n% Another version')
        git(location,'add','main.tex');git(location,'commit','-m','Next version')
        self.assertEqual(self.workspace.snapshot(app['branch'])['saveState'],{'draft':False,'ahead':1})

    def test_connection_label_omits_usernames_passwords_and_query_tokens(self):
        at = chr(64)  # Synthetic credentials; avoid email-shaped literals in distributed fixtures.
        for url in ('https://account:private-canary' + at + 'github.com/team/cvs.git?token=private-canary',
                    'git' + at + 'github.com:team/cvs.git'):
            process=subprocess.CompletedProcess([],0,url+'\n','')
            with patch.object(self.workspace,'_git_process',return_value=process):
                label=self.workspace.connection_label(self.root,'origin')
            self.assertEqual(label,'GitHub · team/cvs')
            self.assertNotIn('private-canary',label)
