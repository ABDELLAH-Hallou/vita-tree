"""Real canonical Vita CV contract, synthetic AI only, temporary Git repositories."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import subprocess
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from test_jobs import JobTests
from support import SOURCE
from vita_tree.workspace import Workspace, ConflictError, digest
from vita_tree import requirements_review as review
from requirements_fixtures import JD, seed


class RequirementsTests(unittest.TestCase):
    tearDown=JobTests.tearDown
    wait=JobTests.wait
    finished=JobTests.finished
    release=JobTests.release

    def setUp(self):
        JobTests.setUp(self)
        import vita
        self.workspace.vita_source=Path(vita.__file__).resolve().parent.parent

    def branch(self,raw=JD,name='requirements'):
        self.labels.append(name)
        return self.workspace.create('master',name,raw,digest(SOURCE))

    def change(self,view,items=None,approve=False):
        return review.change(self.workspace,'requirements',view['token'],view['revision'],items,approve,approve)

    def test_backend_classification_sources_conditions_approval_and_cancellation(self):
        self.branch();original=seed(self.workspace,'requirements',False)
        view=review.view(self.workspace,'requirements')
        self.assertEqual(view['state'],'pending')
        units={item['key']:item for item in view['definition']['requirements']}
        self.assertEqual({k:v['classification'] for k,v in units.items()},dict(hubspot='required',**{'6sense':'preferred','ai':'unclear'}))
        self.assertEqual(len(view['definition']['employment_conditions']),1)
        self.assertEqual(view['definition']['employment_conditions'][0]['weight'],0)
        # Reading/cancelling has no side effects.
        self.assertEqual(review.view(self.workspace,'requirements'),view)
        with self.assertRaises(ValueError):review.change(self.workspace,'requirements',view['token'],view['revision'],approve=True)
        approved=self.change(view,approve=True)
        self.assertEqual(approved['state'],'approved')
        self.assertEqual(approved['definition'],original)
        context=review.context_for(self.workspace,'requirements')
        store,pointer,_=review.paths(self.workspace,context)
        self.assertEqual(review.read(pointer)['revision'],original['revision'])
        self.assertEqual(review.read(store/'revisions'/(original['revision']+'.json')),original)

    def test_invalid_definitions_cannot_publish_or_approve(self):
        self.branch();seed(self.workspace,'requirements',False)
        view=review.view(self.workspace,'requirements')
        items=view['definition']['requirements']+view['definition']['employment_conditions']
        for mutation in ('blank','source','classification','duplicate','condition'):
            bad=copy.deepcopy(items)
            if mutation=='blank':bad[0]['criterion']=''
            elif mutation=='source':bad[0]['source_refs'][0]['quote']='not in the source'
            elif mutation=='classification':
                next(i for i in bad if i['key']=='hubspot')['classification']='preferred'
            elif mutation=='duplicate':bad.append(copy.deepcopy(bad[0]))
            else:next(i for i in bad if i['category']=='employment_condition')['category']='hard_skills'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.change(view,bad)
            self.assertEqual(review.view(self.workspace,'requirements'),view)
        empty=self.change(view,[])
        with self.assertRaises(ValueError):self.change(empty,approve=True)

    def test_new_immutable_revision_stale_tokens_restart_and_inherited_definition(self):
        self.branch();first=seed(self.workspace,'requirements')
        old=review.view(self.workspace,'requirements')
        items=copy.deepcopy(first['requirements']+first['employment_conditions'])
        items[0]['criterion']='Human-reviewed atomic capability'
        draft=self.change(old,items)
        self.assertNotEqual(draft['revision'],first['revision'])
        self.assertEqual(draft['parentRevision'],first['revision'])
        self.assertEqual(draft['approvedRevision'],first['revision'])
        self.assertEqual(draft['state'],'pending')
        with self.assertRaises(ConflictError):self.change(old,approve=True)
        self.change(draft,approve=True)
        self.branch(name='inherited')
        inherited=review.view(self.workspace,'inherited')
        self.assertEqual(inherited['approvedRevision'],draft['revision'])
        self.assertEqual(inherited['originBranch'],'requirements')
        self.branch(JD+'\nAdditional requirement',name='different')
        self.assertIsNone(review.view(self.workspace,'different')['definition'])
        source=self.workspace.vita_source
        self.workspace.close();self.workspace=Workspace(self.root,vita_source=source)
        self.assertEqual(review.view(self.workspace,'inherited')['approvedRevision'],draft['revision'])
        store,_,_=review.paths(self.workspace,review.context_for(self.workspace,'requirements'))
        self.assertEqual(review.read(store/'revisions'/(first['revision']+'.json')),first)

    def test_extract_gate_checkpoint_retry_and_exact_run_revision(self):
        raw=json.dumps(dict(label='requirements',pipeline=True))
        branch=self.branch(raw);self.release('requirements')
        with patch.dict(os.environ,{'VITA_TEST_CANONICAL':'1'}):
            run=self.workspace.start_ai('requirements',branch['revision'],branch['jobRevision'],provider='codex',workflow={'steps':['extract','analyze']})
            parent=self.finished(run['id'])
        self.assertEqual(parent['status'],'failed',parent)
        self.assertTrue(parent['requirementsApprovalNeeded'])
        self.assertEqual(parent['checkpointSteps'],['extract'])
        self.assertEqual(next(i['status'] for i in parent['stages'] if i['id']=='extract'),'succeeded')
        self.assertFalse((self.control/'requirements.analyze.calls').exists())
        self.assertEqual(self.workspace.read('requirements','main.tex'),SOURCE)
        view=review.view(self.workspace,'requirements');self.change(view,approve=True)
        self.assertTrue(self.workspace.get_job(parent['id'])['resumeAvailable'])
        preview=self.workspace.resume_ai(parent['id'],branch['revision'],branch['jobRevision'],preview=True)
        self.assertEqual(preview['reuse'],['extract'])
        child=self.workspace.resume_ai(parent['id'],branch['revision'],branch['jobRevision'],token=preview['token'])
        final=self.finished(child['id']);self.assertEqual(final['status'],'succeeded',final)
        self.assertEqual(final['requirementsRevision'],view['revision'])
        self.assertEqual(final['requirementsStatus'],'current')
        history=review.view(self.workspace,'requirements',child['id'])
        self.assertTrue(history['readOnly']);self.assertEqual(history['definition']['revision'],view['revision'])
        # Later approvals do not rewrite what a finished assessment used.
        items=copy.deepcopy(view['definition']['requirements']);items[0]['criterion']='Corrected engineering capability'
        draft=self.change(review.view(self.workspace,'requirements'),items)
        self.assertEqual(self.workspace.get_job(child['id'])['requirementsStatus'],'pending')
        self.change(draft,approve=True)
        self.assertEqual(self.workspace.get_job(child['id'])['requirementsStatus'],'superseded')
        self.assertEqual(review.view(self.workspace,'requirements',child['id'])['definition']['revision'],view['revision'])
        self.assertEqual(review.view(self.workspace,'requirements',child['id'])['approvedRevision'],draft['revision'])
        source=self.workspace.vita_source;self.workspace.close();self.workspace=Workspace(self.root,vita_source=source)
        self.assertEqual(review.view(self.workspace,'requirements',child['id'])['definition']['revision'],view['revision'])
        self.assertEqual(self.workspace.get_job(child['id'])['requirementsStatus'],'superseded')

    def test_requirement_change_invalidates_downstream_checkpoints_and_reports(self):
        raw=json.dumps(dict(label='requirements',pipeline=True))
        branch=self.branch(raw);data=seed(self.workspace,'requirements');self.release('requirements')
        flag=self.control/'requirements.adapt.fail';flag.touch()
        run=self.workspace.start_ai('requirements',branch['revision'],branch['jobRevision'],provider='codex',workflow={'steps':['extract','analyze','adapt']})
        parent=self.finished(run['id']);self.assertEqual(parent['checkpointSteps'],['extract','analyze'],parent)
        old=review.view(self.workspace,'requirements');items=copy.deepcopy(data['requirements']);items[0]['criterion']='Changed capability'
        new=self.change(old,items);self.change(new,approve=True)
        preview=self.workspace.resume_ai(parent['id'],branch['revision'],branch['jobRevision'],preview=True)
        self.assertEqual(preview['reuse'],['extract']);self.assertIn('analyze',preview['rerun'])
        from vita_tree.workflow import reusable_reports
        reports={'.vita/results/analysis.json':json.dumps({'metadata':{'job_sha256':digest(raw),'requirements_revision':data['revision']}}),'.vita/results/analysis.md':'obsolete'}
        self.assertEqual(reusable_reports(reports,digest(raw),new['revision']),{})

    def test_pending_definition_during_run_conflicts_and_preserves_application(self):
        raw=json.dumps(dict(label='requirements',pipeline=True,hold='analyze'))
        branch=self.branch(raw);data=seed(self.workspace,'requirements');self.release('requirements')
        run=self.workspace.start_ai('requirements',branch['revision'],branch['jobRevision'],provider='codex',workflow={'steps':['analyze']})
        self.wait(lambda:(self.control/'requirements.analyze.started').exists())
        # Another application shares the definition; its edit must invalidate this run.
        self.branch(raw,name='shared');view=review.view(self.workspace,'shared')
        items=copy.deepcopy(data['requirements']);items[0]['criterion']='Changed while another application runs'
        review.change(self.workspace,'shared',view['token'],view['revision'],items)
        (self.control/'requirements.analyze.release').touch()
        final=self.finished(run['id']);self.assertEqual(final['status'],'failed',final)
        self.assertIn('changed during preparation',final['message'])
        self.assertEqual(self.workspace.read('requirements','main.tex'),SOURCE)
        self.assertFalse((Path(branch['worktree'])/'.vita/results/analysis.json').exists())

    def test_real_generation_is_jd_only_routed_and_retains_structured_failure(self):
        branch=self.branch();stage=Path(branch['worktree'])
        (stage/'main.tex').write_text(SOURCE+'\n% PRIVATE-CANDIDATE',encoding='utf-8')
        execution='f'*32
        environment={**os.environ,'PYTHONPATH':str(self.workspace.vita_source)+os.pathsep+str(ROOT/'src')+os.pathsep+str(ROOT/'tests'),
                     'VITA_REQUIREMENTS_DIR':str(stage/'isolated-store'),'VITA_TREE_EXECUTION_ID':execution,
                     'EXTRACTION_PROVIDER':'codex','EXTRACTION_MODEL':'fixture-model','VITA_TREE_REASONING':'high'}
        command=[sys.executable,str(Path(__file__).with_name('requirements_generation.py'))]
        from vita_tree.outcomes import read_outcome
        success=subprocess.run(command,cwd=stage,env=environment,capture_output=True)
        self.assertEqual(success.returncode,0,success.stderr.decode('utf-8',errors='replace'))
        self.assertTrue((stage/'isolated-generation').is_file())
        self.assertEqual(review.read(stage/'.vita/results/tree-requirements.json')['executionId'],execution)
        self.assertTrue(read_outcome(stage,'extract',execution)['verified'])
        self.assertFalse((stage/'isolated-store/approved').exists())
        failure=subprocess.run(command+['fail'],cwd=stage,env=environment,capture_output=True)
        self.assertEqual(failure.returncode,1,failure.stderr.decode('utf-8',errors='replace'))
        outcome=read_outcome(stage,'extract',execution)
        self.assertEqual(outcome['status'],'failed')
        self.assertEqual(outcome['backend']['providerError']['category'],'authentication')

    def test_cli_draft_can_be_reviewed_and_local_validation_does_not_need_approval(self):
        branch=self.branch()
        from requirements_fixtures import compile_definition
        data=compile_definition(JD)
        context=review.context_for(self.workspace,'requirements')
        store,_,_=review.paths(self.workspace,context);review.retain(store,data)
        review.write(Path(branch['worktree'])/'.vita/requirements-state.json',
                     dict(schema_version=1,source_sha256=digest(JD),revision=data['revision']))
        view=review.view(self.workspace,'requirements');self.assertEqual(view['definition'],data);self.assertEqual(view['state'],'pending')
        validation=self.workspace.start_ai('requirements',branch['revision'],branch['jobRevision'],workflow={'steps':['validating']})
        self.assertEqual(self.finished(validation['id'])['status'],'succeeded')
        self.change(view,approve=True)
        self.assertEqual(review.view(self.workspace,'requirements')['state'],'approved')
        with self.assertRaises(ConflictError):self.change(review.view(self.workspace,'requirements'),approve=True)

    def test_damaged_state_is_not_approval_and_changed_job_conflicts(self):
        branch=self.branch();seed(self.workspace,'requirements',False)
        view=review.view(self.workspace,'requirements')
        (Path(branch['worktree'])/'job.md').write_text(JD+'\nChanged by another editor',encoding='utf-8')
        with self.assertRaises(ConflictError):self.change(view,approve=True)
        (Path(branch['worktree'])/'job.md').write_text(JD,encoding='utf-8')
        context=review.context_for(self.workspace,'requirements');_,pointer,marker=review.paths(self.workspace,context)
        marker_before=review.read(marker);review.write(marker,[])
        with self.assertRaises(ValueError):review.view(self.workspace,'requirements')
        review.write(marker,marker_before);review.write(pointer,dict(revision=view['revision']))
        with self.assertRaises(ValueError):review.view(self.workspace,'requirements')

    def test_approval_change_during_capture_cannot_mislabel_the_run(self):
        branch=self.branch();old=seed(self.workspace,'requirements')
        context=review.context_for(self.workspace,'requirements')
        items=copy.deepcopy(old['requirements']+old['employment_conditions']);items[0]['criterion']='New capability during capture'
        changed=review.backend(self.workspace,dict(action='edit',definition=old,source=JD,items=items))
        store,pointer,_=review.paths(self.workspace,context);review.retain(store,changed)
        from vita_tree.workspace import capture_resume_inputs
        def race(workspace,context,record):
            review.write(pointer,dict(schema_version=1,source_sha256=digest(JD),revision=changed['revision']))
            return capture_resume_inputs(workspace,context,record)
        with patch('vita_tree.workspace.capture_resume_inputs',side_effect=race),self.assertRaisesRegex(ConflictError,'approval changed'):
            self.workspace.start_ai('requirements',branch['revision'],branch['jobRevision'],provider='codex',workflow={'steps':['analyze']})
        self.assertFalse(self.workspace.jobs)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--vita-source',type=Path);args=parser.parse_args()
    if args.vita_source:
        sys.path.insert(0,str(args.vita_source.resolve()))
        os.environ['PYTHONPATH']=str(args.vita_source.resolve())+os.pathsep+os.environ.get('PYTHONPATH','')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RequirementsTests))
    raise SystemExit(not result.wasSuccessful())


if __name__=='__main__':main()
