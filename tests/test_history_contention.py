"""History formatting must not hold the shared orchestration/edit lock."""
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

from support import SOURCE, init_repo, cleanup_repo
from vita_tree.workspace import Workspace, digest


class HistoryContentionTests(unittest.TestCase):
    def reader_workspace(self):
        # Exercise the refresh protocol without Git/PDF setup; the other test
        # below verifies its real workspace locking and source-write boundary.
        workspace=Workspace.__new__(Workspace)
        workspace._history_lock=threading.Lock()
        workspace._history_read=None
        return workspace

    def test_overlapping_readers_share_only_the_current_refresh(self):
        workspace=self.reader_workspace()
        entered,release=threading.Event(),threading.Event()
        barrier=threading.Barrier(4)
        calls=[]
        def format_history():
            calls.append(len(calls)+1);entered.set()
            if not release.wait(5):raise TimeoutError('Test refresh was not released')
            return {'runs':[{'revision':len(calls)}]}
        def read():barrier.wait(timeout=5);return workspace.list_jobs()
        with patch.object(workspace,'_list_jobs',side_effect=format_history),ThreadPoolExecutor(max_workers=3) as pool:
            futures=[pool.submit(read) for _ in range(3)]
            try:
                barrier.wait(timeout=5);self.assertTrue(entered.wait(5))
                for future in futures:
                    with self.assertRaises(FutureTimeout):future.result(timeout=.1)
            finally:release.set()
            rows=[future.result(timeout=5) for future in futures]
            self.assertEqual(calls,[1])
            self.assertTrue(all(row['runs'][0]['revision']==1 for row in rows))
            rows[0]['runs'][0]['revision']=999
            self.assertEqual(rows[1]['runs'][0]['revision'],1)
            self.assertEqual(workspace.list_jobs()['runs'][0]['revision'],2)
            self.assertEqual(calls,[1,2],'A completed refresh was cached')

    def test_failed_refresh_unblocks_readers_and_next_request_can_recover(self):
        workspace=self.reader_workspace()
        entered,release=threading.Event(),threading.Event()
        barrier=threading.Barrier(3)
        def fail():
            entered.set();release.wait(5)
            raise ValueError('Synthetic history failure')
        def read():barrier.wait(timeout=5);return workspace.list_jobs()
        with patch.object(workspace,'_list_jobs',side_effect=fail) as refresh,ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(read) for _ in range(2)]
            try:
                barrier.wait(timeout=5);self.assertTrue(entered.wait(5))
                for future in futures:
                    with self.assertRaises(FutureTimeout):future.result(timeout=.1)
            finally:release.set()
            for future in futures:
                with self.assertRaises((ValueError,RuntimeError)):future.result(timeout=5)
            self.assertEqual(refresh.call_count,1)
        with patch.object(workspace,'_list_jobs',return_value={'runs':[]}):
            self.assertEqual(workspace.list_jobs(),{'runs':[]})

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
