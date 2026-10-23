import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch
import zipfile

from support import init_repo, cleanup_repo, git
from diagnostic_fixtures import FIXTURES, write_backend
from vita_tree import diagnostics_contract as contract
from vita_tree.execution import ExecutionInspector, no_links
from vita_tree.workspace import Workspace
from vita_tree.outcomes import safe_outcome
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import test_observability as http_support


class ContractTests(unittest.TestCase):
    def test_pinned_upstream_success_and_failure_fixtures(self):
        for stem in ('success','failure'):
            raw=json.loads((FIXTURES/(stem+'.process.json')).read_text())
            value=contract.process(raw,raw['trace_id'],raw['process_id'])
            self.assertEqual(value['status'],raw['status'])
            event=json.loads((FIXTURES/(stem+'.events.jsonl')).read_text())
            self.assertEqual(contract.event(event,raw['trace_id'],raw['process_id'])['details'],event['details'])
        self.assertEqual(value['failure']['details']['category'],'overloaded')
        self.assertEqual(value['failure']['details']['http_status'],503)

    def test_defensive_field_types_and_safe_error_evidence(self):
        data=contract.details({'category':'overloaded','http_status':503,'retryable':True,'request_id_sha256':'e'*64,
                               'location':'$.criteria[0].status','exception_type':'JSONDecodeError',
                               'effective_model':'fixture-private-key','prompt':'private-canary','response':'private-canary',
                               'delay_seconds':float('nan'),'credential_origin':'/private/person'},
                              ['fixture-private-key'])
        self.assertIsNone(data['effective_model'])
        self.assertEqual(data['category'],'overloaded')
        self.assertEqual(data['credential_origin'],'unreported')
        self.assertNotIn('delay_seconds',data)
        self.assertNotIn('private',json.dumps(data))
        for version in (2,True,'1',None):
            with self.assertRaises(ValueError):contract.check({'schema_version':version,'trace_id':'1'*32},'1'*32)

    def test_oversized_numeric_fields_cannot_hide_other_safe_provider_details(self):
        value=contract.details({'category':'overloaded','http_status':503,'retry_after_seconds':10**1000,'bytes':10**1000})
        self.assertEqual(value,{'category':'overloaded','http_status':503})
        self.assertIsNone(contract.number(10**1000))

    def test_artifact_grammar_cannot_echo_tampered_values_or_html(self):
        ref={'kind':'response','capture_status':'redacted'}
        raw={'schema_version':1,'kind':'response','capture_status':'redacted','data':{'type':'str','value':'<script>private-canary</script>','chars':40}}
        with self.assertRaises(ValueError):contract.artifact(raw,ref)

        raw['data']['value']='[REDACTED]'
        self.assertEqual(contract.artifact(raw,ref)['data']['value'],'[REDACTED]')
        raw['data']={'type':'object','fields':[{'field':'private-canary','value':{}}],'field_count':1}
        with self.assertRaises(ValueError):contract.artifact(raw,ref)

    def test_outcomes_keep_safe_known_error_details_without_provider_prose(self):
        value=safe_outcome({'schema_version':1,'run_id':'a'*32,'status':'failed',
            'attempts':[{'number':1,'category':'overloaded','mode':'validated_prompt','http_status':503,'retry_delay_seconds':.2}],
            'error':{'code':'provider_error','category':'overloaded','status':503,'retryable':True,
                     'provider':'gemini','model':'fixture-model','action':'private-provider-canary'}})
        self.assertEqual(value['attempts'][0]['category'],'overloaded')
        self.assertEqual(value['attempts'][0]['details']['delay_seconds'],.2)
        self.assertEqual(value['errorDetails']['http_status'],503)
        self.assertTrue(value['errorDetails']['retryable'])
        self.assertNotIn('private-provider-canary',json.dumps(value))


class InspectorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        self.root=init_repo(Path(self.temp.name))
        self.workspace=Workspace(self.root)
        self.inspector=self.workspace.inspector

    def tearDown(self):
        self.workspace.close()
        cleanup_repo(self.temp)

    def record(self, parent=None, model='fixture-model', status='failed'):
        ident=uuid.uuid4().hex
        record={'id':ident,'branch':'master','traceId':parent['traceId'] if parent else ident,
                'rootRunId':parent['rootRunId'] if parent else ident,'parentRunId':parent['id'] if parent else None,
                'attempt':parent['attempt']+1 if parent else 1,'status':status,'step':'failed',
                'provider':'gemini','model':model,'reasoning':'medium','language':'en',
                'createdAt':time.time(),'startedAt':time.time()-1,'finishedAt':time.time() if status!='running' else None,
                'stages':[{'id':'analyze','status':'failed' if status=='failed' else 'running'}],
                'stepConfig':{'analyze':{'provider':'gemini','model':model,'reasoning':'medium','connection':''}}}
        self.workspace.jobs[ident]=record
        context={'env':{'TEST_API_KEY':'private-key-canary'},'keys':{},
                 'checkpointInputs':{key:'a'*64 for key in ('source','job','config','criteria','backend')},
                 'baseCommit':'b'*40}
        self.inspector.begin(record,context,{'analyze':'shared'})
        self.inspector.finish(record)
        self.workspace._persist_job(record)
        return record

    def backend(self,record,scenario='overloaded',capture='unavailable',**kwargs):
        span=self.inspector.read_tree(record)['configuration']['analyze']['spanId']
        return write_backend(self.inspector.destination,record['traceId'],span,scenario=scenario,capture=capture,**kwargs)

    def test_known_provider_and_validation_failures_preserve_phase_status_and_retryability(self):
        for category in ('authentication','overloaded','timeout','invalid_json','validation_error'):
            with self.subTest(category=category):
                record=self.record();self.backend(record,category)
                detail=self.inspector.public_detail(record['id'])
                self.assertEqual(detail['backend']['state'],'available')
                self.assertEqual(detail['overview']['category'],category)
                failure=detail['backend']['processes'][0]['failure']
                self.assertEqual(failure['details']['retryable'],category in {'overloaded','timeout'})
                self.assertEqual(failure['frames'][0]['module'],'helpers/structured_output.py')
                self.assertEqual(detail['backend']['events'][0]['parent_span_id'],self.inspector.read_tree(record)['configuration']['analyze']['spanId'])
                if category=='overloaded':
                    self.assertEqual(failure['details']['http_status'],503)
                    self.assertTrue(any(e['details'].get('delay_seconds')==.125 for e in detail['backend']['events']))

    def test_backend_state_is_explicit_for_old_unknown_and_incomplete_contracts(self):
        record=self.record()
        self.assertEqual(self.inspector.public_detail(record['id'])['backend']['state'],'limited')
        self.backend(record)
        manifest=self.inspector.path(record['traceId'],'manifest.json')
        value=json.loads(manifest.read_text());value['schema_version']=2;manifest.write_text(json.dumps(value))
        self.assertEqual(self.inspector.public_detail(record['id'])['backend']['state'],'unavailable')
        value['schema_version']=1;manifest.write_text(json.dumps(value))
        proc=next(self.inspector.path(record['traceId']).glob('process-*.json'))
        raw=json.loads(proc.read_text());raw.update(status='running',logging_complete=False);proc.write_text(json.dumps(raw))
        detail=self.inspector.public_detail(record['id'])
        self.assertEqual(detail['backend']['processes'][0]['status'],'incomplete_or_running')
        self.assertTrue(detail['backend']['warnings'])

    def test_capture_states_missing_and_tampered_artifacts(self):
        for status in ('disabled','suppressed','truncated','unavailable','redacted'):
            record=self.record();proc,_=self.backend(record,'success',status)
            ref=proc['diagnostic_artifacts'][0]
            value=self.inspector.artifact(record['id'],ref['id'])
            self.assertEqual(value['reference']['capture_status'],status)
            self.assertNotIn('path',value['reference'])
            if status in {'truncated','redacted'}:
                self.assertEqual(value['state'],'available')
                target=self.inspector.path(record['traceId'],ref['path'])
                target.unlink()
                self.assertEqual(self.inspector.artifact(record['id'],ref['id'])['state'],'unavailable')
        record=self.record();proc,_=self.backend(record,'success','redacted')
        ref=proc['diagnostic_artifacts'][0]
        path=self.inspector.path(record['traceId'],ref['path'])
        raw=json.loads(path.read_text());raw['data']['value']='private-canary';path.write_text(json.dumps(raw))
        self.assertNotIn('private-canary',json.dumps(self.inspector.artifact(record['id'],ref['id'])))
        self.assertEqual(self.inspector.artifact(record['id'],ref['id'])['state'],'unavailable')

    def test_artifact_ids_paths_links_and_cross_execution_boundaries(self):
        first=self.record();proc,_=self.backend(first,'success','redacted')
        second=self.record();self.backend(second)
        ref=proc['diagnostic_artifacts'][0]
        for invalid in ('../manifest.json','/etc/passwd','a'*31,'<img>'):
            with self.assertRaises(ValueError):self.inspector.artifact(first['id'],invalid)
        with self.assertRaises(ValueError):self.inspector.artifact(second['id'],ref['id'])
        owned=self.inspector.path(first['traceId'],ref['path'])
        original=owned.read_bytes()
        external=self.root/'foreign-diagnostic.json';external.write_bytes(original)
        owned.unlink()
        try:
            owned.symlink_to(external)
        except OSError:
            owned.write_bytes(original)
        else:
            self.assertEqual(self.inspector.artifact(first['id'],ref['id'])['state'],'unavailable')
            owned.unlink();owned.write_bytes(original)
        process=self.inspector.path(first['traceId'],f"process-{proc['process_id']}.json")
        raw=json.loads(process.read_text());raw['diagnostic_artifacts'][0]['path']='../../private-canary'
        process.write_text(json.dumps(raw))
        self.assertEqual(self.inspector.backend(first)['state'],'unavailable')
        # Link checks are tested where creating links is supported.
        target=self.root/'outside';target.mkdir()
        link=self.root/'linked-traces'
        try:link.symlink_to(target,target_is_directory=True)
        except OSError:return
        with self.assertRaises(ValueError):no_links(link/'manifest.json')

    def test_resume_identity_configuration_changes_restart_and_concurrent_trace_isolation(self):
        parent=self.record();self.backend(parent)
        child=self.record(parent,model='changed-model');self.backend(child,'timeout')
        other=self.record();self.backend(other,'authentication')
        value=self.inspector.public_detail(child['id'])
        self.assertEqual(value['run']['traceId'],parent['traceId'])
        self.assertNotEqual(value['run']['id'],parent['id'])
        self.assertTrue(value['tree']['configurationChanged'])
        self.assertEqual(value['overview']['category'],'timeout')
        self.assertEqual(len(value['backend']['processes']),1)
        self.assertEqual(len(value['lineage']),2)
        self.assertEqual(self.inspector.public_detail(parent['id'])['overview']['category'],'overloaded')
        reopened=Workspace(self.root)
        try:
            self.assertEqual(reopened.inspector.public_detail(child['id'])['overview']['category'],'timeout')
            self.assertEqual(reopened.inspector.public_detail(other['id'])['overview']['category'],'authentication')
        finally:reopened.close()

    def test_tree_errors_and_read_only_storage_preserve_original_exception(self):
        for phase in ('staging','pdf','checkpoint','publication'):
            record=self.record(status='running')
            error=PermissionError(13,'private-path-canary','/private/person')
            with self.assertRaises(PermissionError) as caught:
                with self.inspector.phase(record,phase,'analyze'):raise error
            self.assertIs(caught.exception,error)
            record['status']='failed';self.inspector.finish(record)
            detail=self.inspector.public_detail(record['id'])
            self.assertEqual(detail['overview']['phase'],phase)
            self.assertEqual(detail['overview']['category'],'filesystem')
            self.assertNotIn('private-path-canary',json.dumps(detail))
            event=next(item for item in self.workspace.diagnostics.snapshot()['events'] if item['event']=='execution_phase')
            self.assertEqual((event['run_id'],event['trace_id'],event['status']),(record['id'],record['traceId'],'error'))
        record=self.record(status='running')
        with patch('vita_tree.execution.atomic_write_bytes',side_effect=PermissionError('private-canary')):
            with self.assertRaises(RuntimeError):
                with self.inspector.phase(record,'publication'):raise RuntimeError('original-error')
        self.assertIn('could not be fully saved',self.inspector.storage()['error'])
        self.assertNotIn('private-canary',json.dumps(self.inspector.public_detail(record['id'])))

    def test_support_export_allowlist_is_inspectable_and_excludes_bodies_and_paths(self):
        record=self.record();proc,_=self.backend(record,'success','redacted')
        manifest=self.inspector.path(record['traceId'],f"process-{proc['process_id']}.json")
        raw=json.loads(manifest.read_text())
        raw['environment']={'API_KEY':'private-key-canary'};raw['failure']={'phase':'provider_request','details':{'prompt':'private-canary','effective_model':'private-key-canary'},'frames':[{'module':'/private/person.py','line':2}]}
        manifest.write_text(json.dumps(raw))
        summary=self.inspector.export(record['id'],preview=True)
        self.assertIn('Artifact bodies',summary['omitted'])
        with zipfile.ZipFile(io.BytesIO(self.inspector.export(record['id']))) as archive:
            self.assertEqual(set(archive.namelist()),{'diagnostics.json','README.txt'})
            content=archive.read('diagnostics.json').decode()
            for secret in ('private-canary','private-key-canary',str(self.root),'SENSITIVE_CONTENT','[REDACTED]'):
                self.assertNotIn(secret,content)
            self.assertIn('sanitization is not anonymization',archive.read('README.txt').decode())

    def test_paginated_listing_events_ignored_logs_and_conservative_retention(self):
        record=self.record();proc,events=self.backend(record)
        path=self.inspector.path(record['traceId'],f"events-{proc['process_id']}-0.jsonl")
        path.write_text('\n'.join(json.dumps({**events[0],'sequence':i+1}) for i in range(210))+'\n')
        self.assertEqual(len(self.inspector.public_detail(record['id'])['backend']['events']),100)
        self.assertEqual(len(self.inspector.public_detail(record['id'],offset=200)['backend']['events']),10)
        self.assertEqual(git(self.root,'check-ignore','.vita/logs/traces/'+record['traceId']+'/manifest.json'),'.vita/logs/traces/'+record['traceId']+'/manifest.json')
        old=self.inspector.path(record['traceId']);os.utime(old,(1,1))
        active=self.record(status='running');active_path=self.inspector.path(active['traceId']);os.utime(active_path,(1,1))
        self.record()
        self.assertFalse(old.exists())
        self.assertTrue(active_path.exists())
        self.assertIn(record['id'],self.workspace.jobs)  # History survives trace retention.

    def test_invalid_alternative_destination_stays_memory_only(self):
        with patch.dict(os.environ,{'VITA_DIAGNOSTICS_DIR':'relative-private-dir'}):
            inspector=ExecutionInspector(self.workspace)
        self.assertIn('absolute path',inspector.storage()['error'])
        self.assertFalse(inspector.valid_destination)

    def test_cleanup_preserves_unknown_ownership_and_malformed_records_do_not_break_work(self):
        record=self.record()
        folder=self.inspector.path(record['traceId'])
        file=folder/('tree-'+record['id']+'.json')
        file.write_text('[]')
        os.utime(folder,(1,1))
        next_record=self.record()
        self.assertTrue(folder.exists())
        self.assertTrue(self.inspector.read_tree(next_record))
        # Even a terminal-looking future record cannot authorize deletion.
        file.write_text(json.dumps({'treeVersion':2,'traceId':record['traceId'],'runId':record['id'],'status':'failed'}))
        os.utime(folder,(1,1))
        self.record()
        self.assertTrue(folder.exists())
        reservation=self.inspector.destination/('.reserve-'+'e'*32+'.json')
        reservation.write_text('[]')
        safe=self.record()
        self.assertTrue(self.inspector.read_tree(safe))
        self.assertIn('could not be fully saved',self.inspector.storage()['error'])

    def test_protected_trace_count_limit_degrades_logging_without_deleting_evidence(self):
        self.inspector.destination.mkdir(parents=True)
        for number in range(1,101):
            folder=self.inspector.destination/format(number,'032x')
            folder.mkdir()
            (folder/('tree-'+'a'*32+'.json')).write_text(json.dumps({'treeVersion':2,'status':'failed'}))
        record=self.record()
        self.assertEqual(sum(p.is_dir() for p in self.inspector.destination.iterdir()),100)
        self.assertTrue(self.inspector.read_tree(record))
        self.assertIn('could not be fully saved',self.inspector.storage()['error'])
        self.assertEqual(self.inspector.environment(record,'analyze')['VITA_DIAGNOSTICS_DIR'],'diagnostics-unavailable')

    def test_workflow_reservation_protects_between_steps_and_releases_after_restart(self):
        active=self.record(status='running')
        reservation=self.inspector.destination/('.reserve-'+active['id']+'.json')
        self.assertTrue(reservation.is_file())
        self.assertEqual(json.loads(reservation.read_text())['trace_id'],active['traceId'])
        self.assertEqual(self.inspector.environment(active,'analyze')['VITA_DIAGNOSTICS_DIR'],str(self.inspector.destination))
        # A restarted server owns history recovery, so its formerly running
        # Tree reservation can be released; independent backend ones remain.
        foreign=self.inspector.destination/('.reserve-'+'f'*32+'.json')
        foreign.write_text(json.dumps({'trace_id':active['traceId'],'bytes':1024}))
        reopened=Workspace(self.root)
        try:
            self.assertEqual(reopened.jobs[active['id']]['status'],'interrupted')
            self.assertFalse(reservation.exists())
            self.assertTrue(foreign.exists())
        finally:reopened.close()

    def test_malformed_tree_metadata_and_future_event_versions_are_unavailable(self):
        record=self.record();proc,events=self.backend(record)
        path=self.inspector.path(record['traceId'],f"events-{proc['process_id']}-0.jsonl")
        events[-1]['schema_version']=2
        path.write_text('\n'.join(json.dumps(e) for e in events)+'\n')
        self.assertEqual(self.inspector.backend(record)['state'],'unavailable')
        tree=self.inspector.path(record['traceId'],'tree-'+record['id']+'.json')
        raw=json.loads(tree.read_text());raw['configuration']=['private-canary'];tree.write_text(json.dumps(raw))
        self.inspector.memory.clear()
        self.assertEqual(self.inspector.read_tree(record),{})
        self.assertIn('could not be read safely',self.inspector.storage()['error'])
        self.assertNotIn('private-canary',json.dumps(self.inspector.public_detail(record['id'])))


class InspectorHTTPTests(unittest.TestCase):
    def setUp(self):
        http_support.HTTPDiagnosticsTests.setUp(self)
        self.workspace=self.server.workspace
        self.inspector=self.workspace.inspector
    tearDown=http_support.HTTPDiagnosticsTests.tearDown

    def test_inspection_export_and_artifact_routes_reject_foreign_origins_and_arbitrary_paths(self):
        record=InspectorTests.record(self)
        proc,_=InspectorTests.backend(self,record,'success','redacted')
        with urlopen(self.base+'/api/execution?id='+record['id']) as response:
            detail=json.load(response)
        self.assertEqual(detail['backend']['state'],'available')
        artifact=proc['diagnostic_artifacts'][0]['id']
        with urlopen(self.base+'/api/execution-artifact?id='+record['id']+'&artifact='+artifact) as response:
            self.assertEqual(json.load(response)['state'],'available')
        with urlopen(self.base+'/api/execution-export?id='+record['id']) as response:
            self.assertEqual(response.headers.get_content_type(),'application/zip')
            self.assertEqual(len(zipfile.ZipFile(io.BytesIO(response.read())).namelist()),2)
        for route in ('/api/executions','/api/execution?id='+record['id'],'/api/execution-artifact?id='+record['id']+'&artifact='+artifact,'/api/execution-export?id='+record['id']):
            with self.assertRaises(HTTPError) as rejected:
                urlopen(Request(self.base+route,headers={'Origin':'https://untrusted.invalid'}))
            self.assertEqual(rejected.exception.code,403)
        for route in ('/api/execution?id=../../private-canary','/api/execution-artifact?id='+record['id']+'&artifact=../private-canary',
                      '/api/executions?offset=private-canary','/api/execution?id='+record['id']+'&offset=-1'):
            with self.assertRaises(HTTPError) as rejected:urlopen(self.base+route)
            self.assertEqual(rejected.exception.code,400)
            self.assertNotIn('private-canary',rejected.exception.read().decode())
