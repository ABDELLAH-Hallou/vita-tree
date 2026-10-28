"""Project-owned execution inspection; backend files remain backend-owned."""
from contextlib import contextmanager
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import re
import shutil
import threading
import time
import traceback
import uuid
import zipfile

from . import diagnostics_contract as contract
from .fileio import atomic_write_bytes

TREE_PHASES = {'staging','subprocess','pdf','checkpoint','publication','validation','recovery'}
TREE_CATEGORIES = {'filesystem','timeout','subprocess_exit','validation','conflict','interrupted','unclassified'}
LIMIT = 50 * 1024 * 1024
ACTIONS = {
    'authentication': 'Check the selected AI connection or sign in to its CLI again.',
    'permission': 'Check model access and the account permissions for this service.',
    'overloaded': 'The service is temporarily overloaded. Retry when it is available.',
    'rate_limit': 'Wait for the service limit to reset, then retry.',
    'quota_exceeded': 'Check the account quota before retrying.',
    'timeout': 'Check the connection and service status before retrying.',
    'invalid_model': 'Choose a model available to this account.',
    'invalid_json': 'The response could not be decoded. Inspect the schema and attempt history.',
    'schema_error': 'The generated structure did not match the required schema.',
    'validation_error': 'Inspect the recorded validation location before retrying.',
    'filesystem': 'Check project folder permissions and available disk space. Local drafts are preserved.',
    'conflict': 'Review the latest application edits before planning a retry.',
}


def project_settings(repository):
    values = {}
    try:
        file = repository/'.vita/.env'
        if file.is_symlink() or file.stat().st_size > 200_000:
            return values
        for line in file.read_text(encoding='utf-8').splitlines():
            key, sep, value = line.partition('=')
            if sep and key.strip() in {'VITA_DIAGNOSTICS_DIR','VITA_DIAGNOSTIC_CONTENT'}:
                value = value.strip()
                if value.startswith(("'", '"')):
                    value = value[1:value.find(value[0], 1)] if value.find(value[0], 1) >= 0 else ''
                else:
                    value = re.split(r'\s+#', value, maxsplit=1)[0].rstrip()
                values[key.strip()] = value
    except (OSError, UnicodeError):
        pass
    return values


def no_links(path):
    """Reject links/junctions at every existing component, before resolving."""
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part, 'is_junction', lambda:False)():
            raise ValueError('Linked diagnostic locations are not supported')
    return path


@contextmanager
def storage_lock(base):
    # Same cross-process lock name/protocol as Vita CV v1. Do not remove it.
    path = no_links(base/'.storage.lock')
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    acquired = False
    try:
        if not os.fstat(fd).st_size:
            os.write(fd, b'0')
        for _ in range(100):
            try:
                if os.name == 'nt':
                    import msvcrt
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except (BlockingIOError, PermissionError):
                time.sleep(.01)
        if not acquired:
            raise OSError('Diagnostic store is busy')
        yield
    finally:
        if acquired:
            if os.name == 'nt':
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


class ExecutionInspector:
    def __init__(self, workspace):
        self.workspace = workspace
        self.lock = threading.RLock()
        self.memory = {}
        self.secrets = set()
        self.error = None
        self.backend_writable = False
        settings = {**project_settings(workspace.repository), **os.environ}
        self.capture = 'sanitized' if settings.get('VITA_DIAGNOSTIC_CONTENT') == 'sanitized' else 'off'
        raw = settings.get('VITA_DIAGNOSTICS_DIR')
        self.destination = Path(raw) if raw else workspace.repository.resolve()/'.vita/logs/traces'
        self.configured = bool(raw)
        self.valid_destination = self.destination.is_absolute()
        if not self.destination.is_absolute():
            self.error = 'VITA_DIAGNOSTICS_DIR must be an absolute path. Execution details are available in this session only.'
        self.destination = Path(os.path.abspath(self.destination))
        self._remember(os.environ)

    def _remember(self, env):
        self.secrets.update(v for k,v in env.items() if isinstance(v,str) and v and any(x in k.upper() for x in ('KEY','TOKEN','SECRET','PASSWORD')))

    def storage(self):
        return {'path':str(self.destination), 'configured':self.configured, 'capture':self.capture,
                'error':self.error, 'policy':'Technical metadata and value-free structure; no raw prompts or model prose.',
                'retention':'Completed traces: 7 days, 100 traces, 50 MiB shared with Vita CV. Active/incomplete traces are protected.'}

    def path(self, trace_id, relative=''):
        if not contract.ident(trace_id):
            raise ValueError('Invalid trace identifier')
        if relative and not re.fullmatch(r'(?:tree-[a-f0-9]{32}\.json|manifest\.json|process-[a-f0-9]{32}\.json|events-[a-f0-9]{32}-\d{1,8}\.jsonl|artifacts/[a-f0-9]{32}-[a-f0-9]{32}\.json)', relative):
            raise ValueError('Invalid diagnostic artifact identifier')
        return no_links(self.destination/trace_id/relative)

    def _ignore(self):
        try:
            relative = self.destination.relative_to(self.workspace.repository.resolve()).as_posix()
        except ValueError:
            return
        exclude = self.workspace.root.parent/'info/exclude'
        no_links(exclude)
        old = exclude.read_text(encoding='utf-8') if exclude.exists() else ''
        # Escape pattern metacharacters; callers cannot inject a second pattern.
        if any(c in relative for c in '\r\n'):
            raise ValueError('Unsupported diagnostics destination')
        pattern = '/' + re.sub(r'([\\*?\[\]#! ])', r'\\\1', relative) + '/'
        if pattern not in old.splitlines():
            atomic_write_bytes(exclude, (old.rstrip()+'\n# Local execution diagnostics\n'+pattern+'\n').encode())

    def _save(self, data):
        self.memory[data['runId']] = data
        try:
            if not self.valid_destination:
                return
            no_links(self.destination)
            self.destination.mkdir(parents=True, exist_ok=True, mode=0o700)
            self._ignore()
            with storage_lock(self.destination):
                reservation = no_links(self.destination/('.reserve-'+data['runId']+'.json'))
                if data['status'] in {'running','queued'} and not reservation.exists():
                    # Vita CV's collector understands this reservation. Keep
                    # the whole workflow protected between backend processes.
                    atomic_write_bytes(reservation,json.dumps({'trace_id':data['traceId'],'bytes':1_000_000}).encode())
                self._cleanup_locked(data['traceId'])
                folder = self.path(data['traceId'])
                if not folder.exists() and sum(p.is_dir() and bool(contract.ident(p.name)) for p in self.destination.iterdir()) >= 100:
                    raise OSError('Diagnostic trace-count budget reached')
                folder.mkdir(exist_ok=True, mode=0o700)
                payload = json.dumps(data, allow_nan=False).encode()
                if len(payload) > 1_000_000:
                    raise ValueError('Diagnostic record limit reached')
                reservations = 0
                for reservation in self.destination.glob('.reserve-*.json'):
                    raw_reservation = contract.load(no_links(reservation),16384)
                    if not isinstance(raw_reservation,dict) or not contract.ident(raw_reservation.get('trace_id')):
                        raise ValueError('Invalid diagnostic reservation identity')
                    reserved = raw_reservation.get('bytes')
                    if type(reserved) is not int or not 0 <= reserved <= 2*1024*1024:
                        raise ValueError('Invalid diagnostic reservation')
                    reservations += reserved
                if self._bytes()+reservations+len(payload) > LIMIT:
                    raise OSError('Diagnostic quota reached')
                atomic_write_bytes(self.path(data['traceId'], 'tree-'+data['runId']+'.json'), payload)
                self.backend_writable = True
        except (OSError, ValueError):
            self.backend_writable = False
            self.error = 'Execution diagnostics could not be fully saved. Check the trace folder permissions, disk space, and configured destination. The original operation is unchanged.'

    def begin(self, record, context, origins):
        with self.lock:
            self._remember(context['env'])
            self.secrets.update(v for v in context.get('keys',{}).values() if isinstance(v,str) and v)
            config = {}
            for step,route in record['stepConfig'].items():
                config[step] = {'requested': contract.details({'requested_provider':route['provider'], 'requested_model':route['model'], 'reasoning':route['reasoning']}, self.secrets),
                                'origin':origins.get(step,'captured'), 'spanId':uuid.uuid4().hex[:16]}
            parent = self.read_tree(self.workspace.jobs.get(record.get('parentRunId')))
            previous = parent.get('configuration',{})
            changed = bool(parent and any({k:v for k,v in r.items() if k != 'spanId'} != {k:v for k,v in previous.get(s,{}).items() if k != 'spanId'} for s,r in config.items()))
            inputs = context['checkpointInputs']
            data = {'treeVersion':1, 'runId':record['id'], 'traceId':record['traceId'],
                    'parentRunId':record.get('parentRunId'), 'rootRunId':record['rootRunId'], 'attempt':record['attempt'],
                    'status':'running', 'configurationChanged':changed, 'configuration':config,
                    'inputs':{**{k:inputs[k] for k in ('source','job','config','criteria','backend')},
                              'commit':context['baseCommit']},
                    'events':[], 'stepInputs':{}, 'createdAt':record['createdAt']}
            self._save(data)

    def read_tree(self, record):
        try:
            return self._read_tree(record)
        except (OSError,ValueError,TypeError,AttributeError,RecursionError):
            self.error = 'Tree execution metadata could not be read safely. The preparation result is unchanged; historical evidence may be unavailable.'
            return {}

    def _read_tree(self, record):
        if not record or not contract.ident(record.get('traceId')) or not contract.ident(record.get('id')):
            return {}
        with self.lock:
            if record['id'] in self.memory:
                raw = self.memory[record['id']]
            else:
                try:
                    raw = contract.load(self.path(record['traceId'], 'tree-'+record['id']+'.json'), 1_000_000)
                except (OSError, ValueError, TypeError, RecursionError):
                    return {}
            if raw.get('treeVersion') != 1 or raw.get('runId') != record['id'] or raw.get('traceId') != record['traceId']:
                return {}
            # Reapply this allowlist to hand-edited history and every API/export.
            routes = {}
            for step,route in raw.get('configuration',{}).items():
                if step not in contract.STEPS or not isinstance(route,dict):
                    continue
                routes[step] = {'requested':contract.details(route.get('requested'), self.secrets),
                                'origin':route.get('origin') if route.get('origin') in {'shared','step_override','captured'} else 'captured',
                                'spanId':contract.ident(route.get('spanId'),16)}
            events = []
            for item in raw.get('events',[])[:512]:
                if not isinstance(item,dict) or item.get('phase') not in TREE_PHASES or item.get('status') not in {'running','ok','error','interrupted','reused','not_retained'}:
                    continue
                events.append({'phase':item['phase'],'status':item['status'],'timestamp':contract.timestamp(item.get('timestamp')),
                               'duration_ms':contract.number(item.get('duration_ms')), 'spanId':contract.ident(item.get('spanId'),16),
                               'step':item.get('step') if item.get('step') in contract.STEPS|{'validating','preparing'} else None,
                               'category':item.get('category') if item.get('category') in TREE_CATEGORIES else None,
                               'errorType':item.get('errorType') if item.get('errorType') in contract.EXCEPTIONS|{'AIRunError','TimeoutExpired','ConflictError','PreparationConflict'} else None,
                               'errno':contract.number(item.get('errno')), 'winerror':contract.number(item.get('winerror')),
                               'frames':contract.frames(item.get('frames')),
                               'reusedFrom':contract.ident(item.get('reusedFrom'))})
            return {'treeVersion':1,'runId':record['id'],'traceId':record['traceId'],
                    'parentRunId':contract.ident(raw.get('parentRunId')), 'rootRunId':contract.ident(raw.get('rootRunId')),
                    'attempt':raw.get('attempt') if type(raw.get('attempt')) is int and 1 <= raw['attempt'] <= 100 else None,
                    'configurationChanged':raw.get('configurationChanged') is True, 'configuration':routes,
                    'inputs':{k:v for k,v in (raw.get('inputs') or {}).items() if k in {'source','job','config','criteria','backend','commit'} and contract.ident(v,40 if k=='commit' else 64)},
                    'stepInputs':{step:{key:value for key,value in data.items() if key in {'source_sha256','dependency_sha256','checkpoint_signature'} and contract.ident(value,64)}
                                  for step,data in raw.get('stepInputs',{}).items() if step in contract.STEPS and isinstance(data,dict)},
                    'events':events, 'status':record['status'], 'createdAt':record.get('createdAt')}

    def mark(self, record, phase, status='ok', step=None, span_id=None, started=None, error=None, reused_from=None):
        with self.lock:
            data = self.read_tree(record)
            if not data:
                return
            category = ('timeout' if isinstance(error,TimeoutError) or type(error).__name__=='TimeoutExpired' else
                        'filesystem' if isinstance(error,OSError) else 'conflict' if type(error).__name__ in {'ConflictError','PreparationConflict'} else
                        'subprocess_exit' if phase=='subprocess' else 'validation' if phase=='validation' else 'unclassified') if error else None
            data['events'].append({'phase':phase,'status':status,'step':step,'spanId':span_id,
                                   'timestamp':datetime.now(timezone.utc).isoformat(),
                                   'duration_ms':round((time.monotonic()-started)*1000,3) if started else None,
                                   'category':category,'errorType':type(error).__name__ if error else None,'reusedFrom':reused_from,
                                   'errno':getattr(error,'errno',None), 'winerror':getattr(error,'winerror',None),
                                   'frames':[{'module':'external','line':frame.lineno} for frame in traceback.extract_tb(error.__traceback__)[-8:]] if error else []})
            data['events'] = data['events'][-512:]
            self._save(data)
            self.workspace.diagnostics.record('execution_phase', 'ERROR' if error else 'INFO', run_id=record['id'], trace_id=record['traceId'], operation=phase, step=step, status=status)

    def capture_step(self, record, step, source_hash, dependency_hash, signature):
        with self.lock:
            data = self.read_tree(record)
            if data:
                data['stepInputs'][step] = {'source_sha256':source_hash,'dependency_sha256':dependency_hash,'checkpoint_signature':signature}
                self._save(data)

    @contextmanager
    def phase(self, record, phase, step=None):
        span_id = self.read_tree(record).get('configuration',{}).get(step,{}).get('spanId') if phase == 'subprocess' else None
        span_id = span_id or uuid.uuid4().hex[:16]
        self.mark(record,phase,'running',step,span_id)
        started = time.monotonic()
        try:
            yield span_id
        except BaseException as error:
            self.mark(record,phase,'error',step,span_id,started,error)
            raise
        else:
            self.mark(record,phase,'ok',step,span_id,started)

    def environment(self, record, step):
        tree = self.read_tree(record)
        span_id = tree.get('configuration',{}).get(step,{}).get('spanId') or uuid.uuid4().hex[:16]
        return {'VITA_PROJECT_ROOT':str(self.workspace.repository.resolve()),
                # Invalid destinations fail closed in the backend contract too.
                # Do not let the backend write unignored files after Tree's
                # storage/ignore check failed.
                'VITA_DIAGNOSTICS_DIR':str(self.destination) if self.backend_writable else 'diagnostics-unavailable',
                'VITA_TRACEPARENT':'00-'+record['traceId']+'-'+span_id+'-01',
                'VITA_DIAGNOSTIC_CONTENT':self.capture}

    def backend(self, record, step=None):
        trace_id = record.get('traceId')
        result = {'state':'limited','message':'This backend did not record diagnostics v1. Historical request and response details cannot be reconstructed.',
                  'processes':[],'events':[],'artifacts':[],'warnings':[]}
        if not trace_id:
            return result
        try:
            manifest_path = self.path(trace_id,'manifest.json')
            if not manifest_path.exists():
                return result
            manifest = contract.load(manifest_path, 16384)
            contract.check(manifest, trace_id)
            if (manifest.get('product') != 'vita-cv' or manifest.get('ownership') != 'project'
                    or manifest.get('content_policy') != 'source-aware-structure-only'
                    or not contract.token(manifest.get('product_version'),self.secrets)
                    or manifest.get('process_manifests') != 'process-*.json' or manifest.get('events') != 'events-*.jsonl'
                    or type(manifest.get('artifact_limit_bytes')) is not int or not 1 <= manifest['artifact_limit_bytes'] <= 16384
                    or manifest.get('trace_context_status') not in {'accepted','generated','rejected'}):
                raise ValueError('Unsupported diagnostics contract')
            tree = self.read_tree(record)
            spans = {v['spanId']:s for s,v in tree.get('configuration',{}).items() if v.get('spanId')}
            folder = self.path(trace_id)
            files = sorted(folder.iterdir())
            if sum(p.stat().st_size for p in files if p.is_file() and not p.is_symlink()) > 8*1024*1024:
                raise ValueError('Diagnostic read budget reached')
            if len(files) > 1000:
                raise ValueError('Diagnostic file limit reached')
            processes = {}
            for file in files:
                match = re.fullmatch(r'process-([a-f0-9]{32})\.json',file.name)
                if not match:
                    continue
                pid = match[1]
                processes[pid] = contract.process(contract.load(self.path(trace_id,file.name), 262144), trace_id,pid,self.secrets)
            joined = {}
            for file in files:
                match = re.fullmatch(r'events-([a-f0-9]{32})-\d{1,8}\.jsonl',file.name)
                if not match or match[1] not in processes:
                    continue
                path = self.path(trace_id,file.name)
                if path.stat().st_size > 262144:
                    raise ValueError('Diagnostic event file limit reached')
                lines = path.read_text(encoding='utf-8').splitlines()
                for line in lines:
                    try:
                        item = contract.event(json.loads(line),trace_id,match[1],self.secrets)
                    except contract.UnsupportedContract:
                        raise
                    except (ValueError,TypeError,RecursionError):
                        result['warnings'].append('An invalid or incomplete event was omitted.')
                        continue
                    # Direct parent span proves which submitted Tree step owns a
                    # backend process; timestamps alone do not establish causality.
                    if item['parent_span_id'] in spans:
                        joined[match[1]] = spans[item['parent_span_id']]
                    result['events'].append(item)
                    if len(result['events']) > 5000:
                        result['warnings'].append('Event display limit reached.')
                        break
            allowed = {pid:s for pid,s in joined.items() if not step or s==step}
            result['events'] = [e for e in result['events'] if e['process_id'] in allowed][:5000]
            for pid,s in allowed.items():
                proc = processes[pid]
                proc['step'] = s
                result['artifacts'].extend({**ref,'step':s} for ref in proc.pop('diagnostic_artifacts'))
                result['processes'].append(proc)
            references = [ref['id'] for ref in result['artifacts']]
            if len(references) != len(set(references)):
                raise ValueError('Ambiguous diagnostic artifact identities')
            result['state'] = 'available' if allowed else 'limited'
            result['message'] = 'Vita CV diagnostics v1.' if allowed else 'No backend process is correlated with this execution. Diagnostics may be unavailable, incomplete, or from an older backend.'
            result['warnings'] = list(dict.fromkeys(result['warnings']))[:10]
            if any(not p['logging_complete'] for p in result['processes']):
                result['warnings'].append('Backend logging was incomplete; some evidence is unavailable.')
        except FileNotFoundError:
            pass
        except (OSError,ValueError,TypeError,AttributeError,RecursionError):
            result.update(state='unavailable',message='Diagnostics could not be read or use an unsupported contract. The original preparation result is unchanged.',
                          processes=[],events=[],artifacts=[])
        return result

    def record(self, run_id):
        with self.workspace.lock:
            record = self.workspace.jobs.get(run_id)
            if not record or not contract.ident(run_id):
                raise ValueError('Preparation not found')
            return dict(record)

    def listing(self, offset=0, query='', status=''):
        if type(offset) is not int or offset < 0 or offset > 100000 or not isinstance(query,str) or len(query)>160:
            raise ValueError('Invalid execution filter')
        rows = []
        with self.workspace.lock:
            records = [dict(r) for r in self.workspace.jobs.values()]
        for r in sorted(records,key=lambda r:r.get('createdAt') or 0,reverse=True):
            failed = next((s['id'] for s in r.get('stages') or [] if s['status'] in {'failed','interrupted'}),None)
            row = {'id':r['id'],'traceId':r.get('traceId'),'status':r['status'],'failedStep':failed,
                   'provider':contract.details({'effective_provider':r.get('provider')}).get('effective_provider'),'model':contract.token(r.get('model'),self.secrets),
                   'createdAt':r.get('createdAt'),'elapsedSeconds':max(0,(r.get('finishedAt') or time.time())-(r.get('startedAt') or time.time())),
                   'attempt':r.get('attempt'),'branch':r['branch']}
            with self.workspace.lock:
                public = self.workspace._public_job(r)
            row.update(failures=public['failures'],parentRunId=r.get('parentRunId'),configurationChanged=public['configurationChanged'])
            if status and status != row['status']:
                continue
            if query and query.lower() not in json.dumps(row).lower():
                continue
            rows.append(row)
        return {'runs':rows[offset:offset+20],'total':len(rows),'offset':offset,'storage':self.storage()}

    def detail(self, run_id, step=None, offset=0):
        if step and step not in contract.STEPS|{'validating','preparing'} or type(offset) is not int or not 0 <= offset <= 10000:
            raise ValueError('Invalid execution selection')
        r = self.record(run_id)
        tree = self.read_tree(r)
        backend = self.backend(r,step)
        events = sorted(backend['events'],key=lambda e:(e['timestamp'],e['process_id'],e['sequence']))
        backend['routes'] = [event for event in events if event['event']=='route'][-100:]
        total = len(events)
        backend['events'] = events[offset:offset+100]
        backend.update(totalEvents=total,offset=offset)
        if step:
            tree['events'] = [e for e in tree.get('events',[]) if e['step'] in {None,step}]
        failure = next((p['failure'] for p in reversed(backend['processes']) if p['failure']),None)
        tree_error = next((e for e in tree.get('events',[]) if e['status']=='error'),None)
        category = (failure or {}).get('details',{}).get('category') or (tree_error or {}).get('category')
        phase = (failure or {}).get('phase') or (tree_error or {}).get('phase')
        lineage = []
        with self.workspace.lock:
            for other in self.workspace.jobs.values():
                if (other.get('rootRunId') or other['id']) == (r.get('rootRunId') or run_id):
                    lineage.append({'id':other['id'],'parentRunId':other.get('parentRunId'),'attempt':other.get('attempt'),'status':other['status']})
        return {'run':{k:r.get(k) for k in ('id','traceId','status','parentRunId','rootRunId','attempt','resumeAvailable')},
                'resumeAvailable':r.get('status') in {'failed','interrupted'} and bool(r.get('attempt')),
                'overview':{'phase':phase,'category':category,'nextAction':ACTIONS.get(category,'Review the timeline and captured configuration. Retry uses the verified-checkpoint plan; unavailable evidence cannot be recovered.')},
                'tree':tree,'backend':backend,'lineage':sorted(lineage,key=lambda a:a.get('attempt') or 0),
                'storage':self.storage()}

    def artifact(self, run_id, artifact_id):
        if not contract.ident(artifact_id):
            raise ValueError('Invalid artifact identifier')
        r = self.record(run_id)
        backend = self.backend(r)
        ref = next((v for v in backend['artifacts'] if v['id']==artifact_id),None)
        if not ref:
            raise ValueError('Artifact is not associated with this execution')
        safe_ref = {k:v for k,v in ref.items() if k != 'path'}
        if not ref['path'] or ref['capture_status'] not in {'captured','redacted','truncated'}:
            return {'reference':safe_ref,'state':ref['capture_status'],'content':None}
        try:
            content = contract.artifact(contract.load(self.path(r['traceId'],ref['path']),16384),ref)
            return {'reference':safe_ref,'state':'available','content':content}
        except (OSError,ValueError,TypeError,RecursionError):
            return {'reference':safe_ref,'state':'unavailable','content':None,
                    'message':'The historical artifact is missing, unsafe, or no longer matches the supported contract.'}

    def public_detail(self, *args, **kwargs):
        value = self.detail(*args,**kwargs)
        value['backend']['artifacts'] = [{k:v for k,v in ref.items() if k!='path'} for ref in value['backend']['artifacts']]
        return value

    def export(self, run_id, preview=False):
        # Export only revalidated metadata. No artifact bodies, paths, labels,
        # personal documents, stdout, stderr, or arbitrary project files.
        result = self.public_detail(run_id)
        result.pop('storage',None)
        included = ['Execution identities and resume lineage','Captured route identifiers and input hashes','Sanitized phase/attempt metadata','Capture availability indicators']
        omitted = ['Artifact bodies','CV and job documents','Raw prompts and model output','Credentials and environment values','Local paths and application names','Raw process logs']
        summary = {'included':included,'omitted':omitted,'notice':'Technical identifiers may still be identifying. Inspect the report before sharing; sanitization is not anonymization.'}
        if preview:
            return summary
        # Include all retained events, bounded by the reader, rather than only
        # the first page that happened to be open in the UI.
        result['backend']['events'] = self.backend(self.record(run_id))['events']
        result['export'] = summary
        output = io.BytesIO()
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('diagnostics.json',json.dumps(result,indent=2,allow_nan=False))
            archive.writestr('README.txt',summary['notice']+'\nIncluded: '+', '.join(included)+'\nOmitted: '+', '.join(omitted)+'\n')
        return output.getvalue()

    def _bytes(self):
        size = 0
        for index, path in enumerate(self.destination.rglob('*')):
            if index >= 20000:
                raise ValueError('Diagnostic file-count budget reached')
            no_links(path)
            if path.is_file():
                size += path.stat().st_size
        return size

    def _cleanup_locked(self, current=None):
        active = {r.get('traceId') for r in self.workspace.jobs.values() if r['status'] in {'queued','running'}}
        reserved = set()
        for file in self.destination.glob('.reserve-*.json'):
            try:
                data=contract.load(no_links(file),16384)
                if not isinstance(data,dict) or not contract.ident(data.get('trace_id')):
                    return
                reserved.add(data['trace_id'])
            except (OSError,ValueError,TypeError):
                # Unknown reservations cannot justify deleting any trace.
                return
        folders = [p for p in self.destination.iterdir() if p.is_dir() and contract.ident(p.name)]
        size = self._bytes()
        for folder in sorted(folders,key=lambda p:p.stat().st_mtime):
            if folder.name in active|reserved|{current}:
                continue
            no_links(folder)
            # Most saves cannot evict these young traces. Check eligibility
            # before reopening and parsing every completed trace's records;
            # ownership validation remains mandatory before any deletion.
            try:
                if size < LIMIT-2*1024*1024 and len(folders)<100 and time.time()-folder.stat().st_mtime<7*86400:
                    continue
            except OSError:
                continue
            tree_files = list(folder.glob('tree-*.json'))
            if not tree_files:
                continue  # Tree does not own standalone Vita CV traces.
            try:
                states = []
                for file in tree_files:
                    data=contract.load(no_links(file),1_000_000)
                    expected=re.fullmatch(r'tree-([a-f0-9]{32})\.json',file.name)
                    if (not isinstance(data,dict) or not expected or data.get('treeVersion') != 1
                            or data.get('runId') != expected[1] or data.get('traceId') != folder.name):
                        raise ValueError('Unverified trace ownership')
                    states.append(data.get('status'))
                for file in folder.glob('process-*.json'):
                    data=contract.load(no_links(file),262144)
                    expected=re.fullmatch(r'process-([a-f0-9]{32})\.json',file.name)
                    contract.check(data,folder.name)
                    if not expected or data.get('process_id') != expected[1]:
                        raise ValueError('Unverified process identity')
                    states.append(data.get('status'))
                if not states or any(s not in {'succeeded','failed','interrupted','success'} for s in states):
                    continue
                # Verify every descendant before recursive deletion.
                for path in folder.rglob('*'):
                    no_links(path)
                resolved = folder.resolve()
                if resolved.parent != self.destination.resolve():
                    continue
                old = sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())
                shutil.rmtree(resolved)
                size -= old
                folders.remove(folder)
            except (OSError,ValueError,TypeError,AttributeError):
                continue

    def finish(self, record):
        with self.lock:
            data = self.read_tree(record)
            if data:
                data['status'] = record['status']
                self._save(data)
            if record['status'] not in {'running','queued'}:
                try:
                    reservation = no_links(self.destination/('.reserve-'+record['id']+'.json'))
                    if reservation.exists():
                        with storage_lock(self.destination):
                            reservation.unlink()
                except (OSError,ValueError):
                    self.error = 'The finished workflow reservation could not be released. Check diagnostics storage; incomplete reservations are preserved.'
            # Bound memory too; disk history remains lazy-loaded.
            for ident in list(self.memory):
                if len(self.memory)<=100:
                    break
                if self.memory[ident]['status'] not in {'running','queued'}:
                    del self.memory[ident]
