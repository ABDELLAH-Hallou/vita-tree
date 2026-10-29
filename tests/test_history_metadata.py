"""Batch history reads retain validation, consistent revisions and fresh reads."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from support import init_repo, cleanup_repo
from vita_tree.workspace import Workspace, digest
from vita_tree import factual_review, requirements_review


class HistoryMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        self.root=init_repo(Path(self.temporary.name))
        self.workspace=Workspace(self.root)
        self.ids=[f'{i:032x}' for i in range(1,5)]
        for ident in self.ids:
            self.workspace.jobs[ident]=dict(id=ident,branch='master',status='failed',attempt=1,
                createdAt=1,stages=[],outcomes={},stepConfig={})

    def tearDown(self):
        self.workspace.close()
        cleanup_repo(self.temporary)

    def facts(self,ident,state='pending'):
        folder=self.workspace.root/'factual-reviews'/ident
        folder.mkdir(parents=True,exist_ok=True)
        data=dict(schemaVersion=1,state=state,step='adapt',revision='fc-'+'a'*64,
                  resolvedRevision='fc-'+'a'*64,count=1,decidedAt=1)
        (folder/'manifest.json').write_text(json.dumps(data))
        return folder

    def requirements(self):
        base=self.workspace.root/'fixture-approval';base.mkdir(parents=True)
        approval,review=base/'approved.json',base/'review.json'
        source_hash=digest('Synthetic job')
        approval.write_text(json.dumps(dict(schema_version=1,source_sha256=source_hash,revision='a'*64)))
        review.write_text('{"state":"approved"}')
        bindings=self.workspace.root/'run-requirements';bindings.mkdir()
        for ident in self.ids:
            self.workspace.jobs[ident]['requirementsRevision']='a'*64
            (bindings/(ident+'.binding.json')).write_text(json.dumps(dict(revision='a'*64,sourceHash=source_hash,
                approval=str(approval),review=str(review))))
        return approval,review,source_hash

    def test_factual_batch_matches_individual_validation_and_refreshes(self):
        self.facts(self.ids[0]);self.facts(self.ids[1],'resolved')
        incomplete=self.workspace.root/'factual-reviews'/self.ids[2];incomplete.mkdir()
        (incomplete/'proposal.json').write_text('{}')
        expected={ident:factual_review.summary(self.workspace,ident) for ident in self.ids}
        self.assertEqual(factual_review.summaries(self.workspace,self.ids),expected)
        first={row['id']:row['factualReview'] for row in self.workspace.list_jobs()['runs']}
        self.assertEqual(first,expected)
        self.facts(self.ids[0],'resolved')
        second={row['id']:row['factualReview'] for row in self.workspace.list_jobs()['runs']}
        self.assertEqual(second[self.ids[0]]['state'],'resolved')
        self.assertIsNone(second[self.ids[3]])
        self.assertEqual(factual_review.summaries(self.workspace,['../outside'])['../outside'],{'state':'unavailable'})

    def test_shared_approval_is_consistent_within_refresh_and_fresh_afterwards(self):
        approval,_,source_hash=self.requirements()
        read=requirements_review.read
        def changed(path):
            value=read(path)
            if path==approval:
                approval.write_text(json.dumps(dict(schema_version=1,source_sha256=source_hash,revision='b'*64)))
            return value
        with patch.object(requirements_review,'read',side_effect=changed):
            rows=self.workspace.list_jobs()['runs']
        self.assertTrue(all(row['requirementsStatus']=='current' for row in rows))
        self.assertTrue(all(row['requirementsStatus']=='superseded' for row in self.workspace.list_jobs()['runs']))
        self.assertEqual(requirements_review.run_status(self.workspace,self.workspace.jobs[self.ids[0]]),'superseded')

    def test_invalid_shared_approval_recovers_on_next_refresh(self):
        approval,_,_=self.requirements()
        valid=approval.read_text();approval.write_text('invalid JSON')
        read=requirements_review.read
        def repaired(path):
            try:return read(path)
            except ValueError:
                if path==approval:approval.write_text(valid)
                raise
        with patch.object(requirements_review,'read',side_effect=repaired):
            self.assertTrue(all(row['requirementsStatus']=='unavailable' for row in self.workspace.list_jobs()['runs']))
        self.assertTrue(all(row['requirementsStatus']=='current' for row in self.workspace.list_jobs()['runs']))

    def link(self,target,path):
        path.parent.mkdir(parents=True,exist_ok=True)
        if os.name=='nt':
            result=subprocess.run(['cmd','/c','mklink','/J',str(path),str(target)],capture_output=True)
            if result.returncode:self.skipTest('Junction creation is unavailable')
        else:os.symlink(target,path,target_is_directory=True)

    def test_factual_child_and_namespace_escapes_stay_unavailable(self):
        outside=self.root/'outside';outside.mkdir()
        (outside/'manifest.json').write_text(json.dumps(dict(schemaVersion=1,state='pending',step='adapt',revision='fc-'+'a'*64,count=1)))
        base=self.workspace.root/'factual-reviews'
        self.link(outside,base/self.ids[0])
        self.assertEqual(factual_review.summaries(self.workspace,self.ids)[self.ids[0]],{'state':'unavailable'})
        # Keep the test link within its temporary repository; remove the link
        # itself, never recursively remove or traverse its target.
        if os.name=='nt':os.rmdir(base/self.ids[0])
        else:(base/self.ids[0]).unlink()
        base.rmdir()
        self.link(outside,base)
        self.assertTrue(all(value=={'state':'unavailable'} for value in factual_review.summaries(self.workspace,self.ids).values()))
