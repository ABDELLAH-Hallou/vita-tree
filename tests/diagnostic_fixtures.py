"""Deterministic Vita CV v1 fixtures; no provider/network activity."""
import json
import os
import sys
import time
from pathlib import Path
import uuid

FIXTURES = Path(__file__).with_name('fixtures')/'diagnostics'


def write_backend(store, trace_id, parent_span, step='analyze', scenario='overloaded', capture='unavailable', artifact_kind='response',
                  provider='gemini', model='fixture-model', reasoning='medium'):
    pid, sid, aid = (uuid.uuid4().hex for _ in range(3))
    folder = Path(store)/trace_id
    folder.mkdir(parents=True,exist_ok=True)
    manifest = {'schema_version':1,'trace_id':trace_id,'product':'vita-cv','product_version':'2.6.3',
                'ownership':'project','process_manifests':'process-*.json','events':'events-*.jsonl',
                'artifact_limit_bytes':16384,'content_policy':'source-aware-structure-only','trace_context_status':'accepted'}
    (folder/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    proc = json.loads((FIXTURES/('success.process.json' if scenario=='success' else 'failure.process.json')).read_text())
    proc.update(trace_id=trace_id,process_id=pid)
    categories = {'authentication':401,'overloaded':503,'rate_limit':429,'invalid_model':400,'timeout':None,'invalid_json':None,'validation_error':None,'success':None}
    phase = 'decoding' if scenario=='invalid_json' else 'validation' if scenario=='validation_error' else 'provider_request'
    detail = {'category':scenario if scenario!='success' else 'unclassified',
              'effective_provider':provider,'effective_model':model,'requested_provider':provider,
              'requested_model':model,'reasoning':reasoning,'model_origin':'explicit','provider_origin':'explicit',
              'reasoning_origin':'extensions','credential_origin':'process','credential_present':True,
              'http_status':categories.get(scenario),'retryable':scenario in {'overloaded','timeout'},
              'attempt':1,'request_id_sha256':'e'*64}
    if detail['http_status'] is None:
        detail.pop('http_status')
    if scenario=='validation_error':
        detail['location']='$.criteria[0].status'
    proc['failure'] = None if scenario=='success' else {'phase':phase,'details':detail,'frames':[{'module':'helpers/structured_output.py','line':153}]}
    ref = proc['diagnostic_artifacts'][0]
    ref.update(id=aid,step_id=sid,attempt_id='5'*32,kind=artifact_kind,capture_status=capture,
               reason={'disabled':'content_capture_off','redacted':'all_source_values_removed','suppressed':'cannot_establish_safe_structure',
                       'truncated':'artifact_size_limit','captured':'host_safe_summary'}.get(capture,'no_model_response_produced'),
               content_exists=None if scenario=='timeout' else scenario not in {'authentication','overloaded'})
    if capture=='unavailable':
        ref['reason']='no_model_response_produced' if ref['content_exists'] is False else 'not_observed'
    body = None
    if capture in {'redacted','captured','truncated'}:
        if artifact_kind=='request':
            body={'sections':[{'label':'system','content':'[SENSITIVE_CONTENT]','chars':123,'lines':2}], 'exact_prompt_captured':False}
            ref.update(content_exists=True,reason='sensitive_sections_replaced')
        else:
            body={'type':'str','value':'[REDACTED]','chars':15}
            ref['content_exists']=True
        if capture=='truncated':
            body={'content':'[SUPPRESSED_SIZE_LIMIT]'}
        payload={'schema_version':1,'kind':artifact_kind,'capture_status':capture,'data':body}
        ref['path']=f'artifacts/{pid}-{aid}.json'
        path=folder/ref['path'];path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(payload),encoding='utf-8')
        ref['bytes']=path.stat().st_size
    proc['capture_enabled']=capture not in {'disabled','unavailable'}
    (folder/f'process-{pid}.json').write_text(json.dumps(proc),encoding='utf-8')
    base=json.loads((FIXTURES/'failure.events.jsonl').read_text())
    base.update(trace_id=trace_id,process_id=pid,workflow_id=uuid.uuid4().hex,step=step,step_id=sid,
                parent_span_id=parent_span,phase=phase,details=detail,status='ok' if scenario=='success' else 'error')
    events=[{**base,'sequence':1,'event':'route','phase':'configuration'},
            {**base,'sequence':2,'event':'attempt'},
            {**base,'sequence':3,'event':'retry','details':{'attempt':1,'delay_seconds':.125,'category':scenario}}] if scenario=='overloaded' else [{**base,'sequence':1,'event':'attempt'}]
    events.append({**base,'sequence':len(events)+1,'event':'span_end'})
    (folder/f'events-{pid}-0.jsonl').write_text('\n'.join(json.dumps(e) for e in events)+'\n',encoding='utf-8')
    return proc, events


def from_environment(step, scenario):
    parent=os.environ['VITA_TRACEPARENT'].split('-')
    provider=sys.argv[sys.argv.index('--provider')+1]
    config=json.loads(Path('.vita/extensions.json').read_text())
    model=config['llm_providers'][provider]['model']
    return write_backend(os.environ['VITA_DIAGNOSTICS_DIR'],parent[1],parent[2],step,scenario,
                         provider=provider,model=model,reasoning=os.environ.get('VITA_TREE_REASONING',''))


def seed_run(workspace, scenario='authentication', phase=None, capture='unavailable', artifact_kind='response', backend=True):
    """Seed a synthetic history entry for UI/contract tests, without execution."""
    from support import SOURCE,git
    from vita_tree.workspace import digest
    ident=uuid.uuid4().hex
    step='cover' if phase=='pdf' else 'analyze'
    record={'id':ident,'traceId':ident,'rootRunId':ident,'parentRunId':None,'attempt':1,'branch':'master',
            'opportunity':'Fixture opportunity','createdAt':time.time(),'startedAt':time.time()-1,'finishedAt':None,
            'status':'running','step':step,'message':'Synthetic preparation fixture.','provider':'gemini','model':'fixture-model',
            'reasoning':'medium','language':'en','reviewed':False,'stages':[{'id':step,'status':'failed'}],
            'stepConfig':{step:{'provider':'gemini','model':'fixture-model','reasoning':'medium','connection':''}}}
    workspace.jobs[ident]=record
    context={'env':{},'keys':{},'checkpointInputs':{key:digest(SOURCE) for key in ('source','job','config','criteria','backend')},
             'baseCommit':git(workspace.repository,'rev-parse','HEAD')}
    workspace.inspector.begin(record,context,{step:'shared'})
    if backend:
        span=workspace.inspector.read_tree(record)['configuration'][step]['spanId']
        write_backend(workspace.inspector.destination,ident,span,step,scenario,capture,artifact_kind)
    if phase:
        try:
            with workspace.inspector.phase(record,phase,step):
                raise PermissionError(13,'private-filesystem-canary','/private/person')
        except PermissionError:
            pass
    record.update(status='failed',step='failed',finishedAt=time.time())
    workspace.inspector.finish(record)
    workspace._persist_job(record)
    return record
