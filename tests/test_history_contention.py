"""History formatting must not hold the shared orchestration/edit lock."""
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from support import SOURCE, init_repo, cleanup_repo
from vita_tree.workspace import Workspace, digest


class HistoryContentionTests(unittest.TestCase):
    def test_slow_history_formatting_allows_draft_save_and_keeps_snapshot(self):
        temporary=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        workspace=Workspace(init_repo(Path(temporary.name)))
        entered,release,acquired=threading.Event(),threading.Event(),threading.Event()
        rows,errors=[],[]
        ident='1'*32
        workspace.jobs[ident]=dict(id=ident,branch='master',status='succeeded',createdAt=1,
                                   message='Captured message',stages=[],outcomes={},stepConfig={})
        original=workspace._public_job
        def slow(record,**kwargs):
            entered.set()
            if not release.wait(10):raise TimeoutError('Test formatter was not released')
            return original(record,**kwargs)
        def history():
            try:rows.extend(workspace.list_jobs()['runs'])
            except Exception as error:errors.append(error)
        def edit():
            try:
                with workspace.lock:
                    workspace.jobs[ident]['message']='New message'
                    workspace.jobs[ident]['stages'].append({'id':'analyze','status':'succeeded'})
                    acquired.set()
                workspace.save('master','main.tex',digest(SOURCE),SOURCE+'\n% independent draft')
            except Exception as error:errors.append(error)
        reader=threading.Thread(target=history);writer=threading.Thread(target=edit)
        try:
            with patch.object(workspace,'_public_job',side_effect=slow):
                reader.start()
                self.assertTrue(entered.wait(5))
                writer.start()
                # A held formatter must not block a writer from even acquiring
                # the lock. This fails deterministically with the old code.
                self.assertTrue(acquired.wait(2),'History formatter held the workspace lock')
                release.set()
                reader.join(timeout=15);writer.join(timeout=15)
            self.assertFalse(reader.is_alive() or writer.is_alive())
            self.assertEqual(errors,[])
            self.assertEqual(rows[0]['message'],'Captured message')
            self.assertEqual(rows[0]['stages'],[])
            self.assertIn('independent draft',workspace.read('master','main.tex'))
        finally:
            release.set()
            if reader.ident:reader.join(timeout=15)
            if writer.ident:writer.join(timeout=15)
            workspace.close()
            cleanup_repo(temporary)
