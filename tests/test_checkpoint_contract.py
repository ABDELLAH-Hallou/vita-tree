import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from support import cleanup_repo
from vita_tree.outcomes import execute, read_outcome
from vita_tree import checkpoints


class CheckpointContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        self.root=Path(self.temp.name)

    def tearDown(self):cleanup_repo(self.temp)

    def test_backend_structured_trace_is_sanitized_and_nonce_bound(self):
        folder=self.root/'.vita/results';folder.mkdir(parents=True)
        def backend():
            (folder/'analyze.outcome.json').write_text(json.dumps({
                'schema_version':1,'run_id':'a'*32,'step':'analyze','status':'success',
                'attempts':[{'number':1,'category':'invalid_json','mode':'validated_prompt','detail':'private-canary'},
                            {'number':2,'category':'valid','mode':'native_schema','route':{'secret':'private-canary'}}],
                'error':None,'prompt':'private-canary'}))
            return True
        previous=Path.cwd()
        try:
            os.chdir(self.root)
            self.assertTrue(execute('analyze',backend,'nonce'))
        finally:os.chdir(previous)
        value=read_outcome(self.root,'analyze','nonce')
        self.assertTrue(value['verified'])
        self.assertEqual([a['category'] for a in value['backend']['attempts']],['invalid_json','valid'])
        self.assertNotIn('private-canary',json.dumps(value))
        self.assertIsNone(read_outcome(self.root,'analyze','another-execution'))

    def test_missing_or_failed_backend_contract_is_never_a_verified_checkpoint(self):
        previous=Path.cwd()
        try:
            os.chdir(self.root)
            execute('analyze',lambda:True,'one')
            self.assertFalse(read_outcome(self.root,'analyze','one')['verified'])
            execute('adapt',lambda:False,'two')
            self.assertEqual(read_outcome(self.root,'adapt','two')['status'],'failed')
            def broken():raise RuntimeError('private-canary')
            with self.assertRaises(RuntimeError):execute('cover',broken,'three')
            self.assertNotIn('private-canary',(self.root/'.vita/results/tree-cover.outcome.json').read_text())
        finally:os.chdir(previous)

    def test_stale_native_success_is_removed_before_call(self):
        folder=self.root/'.vita/results';folder.mkdir(parents=True)
        (folder/'extract.outcome.json').write_text('{"schema_version":1,"status":"success"}')
        previous=Path.cwd()
        try:
            os.chdir(self.root)
            execute('extract',lambda:False,'execution')
        finally:os.chdir(previous)
        self.assertIsNone(read_outcome(self.root,'extract','execution')['backend'])

    def test_checkpoint_manifest_and_dependency_hashes_are_authoritative(self):
        files={name:None for name in checkpoints.ARTIFACTS};files['main.tex']='Source'
        root=self.root/'checkpoints';ident='a'*32
        outcome={'status':'success','verified':True,'backend':None}
        self.assertTrue(checkpoints.write_checkpoint(root,ident,'adapt','1'*64,files,outcome))
        self.assertIsNotNone(checkpoints.load_checkpoint(root,ident,'adapt'))
        (root/ident/'adapt/files/main.tex').write_text('Changed source')
        self.assertIsNone(checkpoints.load_checkpoint(root,ident,'adapt'))
        self.assertIsNone(checkpoints.load_checkpoint(root,'../outside','adapt'))

    def test_retention_count_bytes_and_active_attempt_protection(self):
        root=self.root/'checkpoints';now=time.time();jobs={}
        ids=['a'*32,'b'*32,'c'*32]
        for i,ident in enumerate(ids):
            folder=root/ident;folder.mkdir(parents=True);(folder/'data').write_bytes(b'x'*1024)
            jobs[ident]={'id':ident,'status':'failed','finishedAt':now-10+i}
        jobs[ids[0]]['status']='running'
        with patch.object(checkpoints,'MAX_RUNS',2):
            result=checkpoints.cleanup(root,jobs,now=now)
        self.assertEqual(result['removed'],[ids[1]])
        self.assertTrue((root/ids[0]).exists())
        with patch.object(checkpoints,'MAX_TOTAL_BYTES',1024):
            result=checkpoints.cleanup(root,jobs,now=now)
        self.assertEqual(result['removed'],[ids[2]])
        self.assertTrue((root/ids[0]).exists())

    def test_oversized_checkpoint_is_skipped_without_deleting_existing_outputs(self):
        files={name:None for name in checkpoints.ARTIFACTS};files['main.tex']='Keep source'
        with patch.object(checkpoints,'MAX_CHECKPOINT_BYTES',1):
            self.assertFalse(checkpoints.write_checkpoint(self.root/'checkpoints','a'*32,'adapt','key',files,{}))
        self.assertFalse((self.root/'checkpoints').exists())
