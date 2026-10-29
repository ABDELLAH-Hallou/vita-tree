"""Synthetic load setup, private control plane and bounded resource sampling."""
import hashlib
import json
import math
import os
import platform
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from support import init_repo,git,SOURCE
from vita_tree.ai_config import credential_name

PROFILES=ROOT/'tests/fixtures/load_profiles.json'
LOAD_SOURCE=SOURCE.replace(r'\end{document}',r'\input{sections/extra}'+'\n'+r'\end{document}')


def sha(value):return hashlib.sha256(value if isinstance(value,bytes) else value.encode()).hexdigest()


def processor_label():
    if sys.platform.startswith('linux'):
        try:
            for line in Path('/proc/cpuinfo').read_text().splitlines():
                key,_,value=line.partition(':')
                if key.strip()=='model name':return value.strip()
        except OSError:pass
    return platform.processor() or None


def distribution(values):
    values=sorted(values)
    return dict(count=len(values),p50=values[max(0,math.ceil(len(values)*.50)-1)] if values else None,
                p95=values[max(0,math.ceil(len(values)*.95)-1)] if values else None,
                maximum=max(values) if values else None)


def advisory_budget(key, value, advisory_orchestration=False):
    actual=value.get('actual')
    return (advisory_orchestration and key=='orchestrationP95Ms'
            and type(actual) in (int,float) and math.isfinite(actual) and actual>=0)


def budget_gate(results, enforce=False, advisory_orchestration=False):
    if not enforce:return True
    return all(value['passed'] or advisory_budget(key,value,advisory_orchestration)
               for key,value in results.items())


def profile(name):
    data=json.loads(PROFILES.read_text())
    assert data['schemaVersion']==1 and data['version']=='1.0.0'
    return data['profiles'][name]


def prepare(root, config):
    init_repo(root)
    (root/'main.tex').write_text(LOAD_SOURCE,encoding='utf-8')
    (root/'sections').mkdir()
    (root/'sections/extra.tex').write_text('Untouched included section.\n',encoding='utf-8')
    git(root,'add','.');git(root,'commit','-m','Synthetic included load source')
    commit=git(root,'rev-parse','HEAD')
    updates=''.join(f'create refs/heads/history-{i:03} {commit}\n' for i in range(config['historyBranches']))
    subprocess.run(['git','update-ref','--stdin'],cwd=root,input=updates.encode(),capture_output=True,check=True)
    control=root/'.git/load-control';control.mkdir()
    (root/'.vita').mkdir()
    (root/'.vita/extensions.json').write_text('{"llm_providers":{"openai":{"model":"fixture-model"}}}')
    backend=root/'.git/fake-vita/vita/assets/prompts';backend.mkdir(parents=True)
    for step in ('extract','review','cover'):(backend/(step+'.md')).write_text('Synthetic fixture')
    history=root/'.git/vita-tree/job-history';history.mkdir(parents=True)
    approvals=control/'archived-approval.json';review=control/'archived-review.json'
    revision='1'*64;job_hash=sha('Synthetic archived job')
    approvals.write_text(json.dumps(dict(schema_version=1,source_sha256=job_hash,revision=revision)))
    review.write_text('{"state":"approved"}')
    bindings=root/'.git/vita-tree/run-requirements';bindings.mkdir()
    for i in range(config['history']):
        ident=f'{i+1:032x}'
        record=dict(id=ident,branch=f"history-{i%config['historyBranches']:03}",status='succeeded',step='completed',
                    createdAt=1700000000+i,startedAt=1700000000+i,finishedAt=1700000001+i,reviewed=True,
                    provider='openai',model='fixture-model',message='Synthetic completed history',
                    stages=[],stepConfig={},outcomes={},checkpointSteps=[],attempt=1,traceId=ident,rootRunId=ident)
        if i%2==0:
            record['requirementsRevision']=revision
            (bindings/(ident+'.binding.json')).write_text(json.dumps(dict(revision=revision,sourceHash=job_hash,
                approval=str(approvals.resolve()),review=str(review.resolve()))))
        if i%5==0:
            folder=root/'.git/vita-tree/factual-reviews'/ident;folder.mkdir(parents=True)
            (folder/'manifest.json').write_text(json.dumps(dict(schemaVersion=1,state='resolved',step='adapt',
                revision='fc-'+revision,resolvedRevision='fc-'+revision,count=1,decidedAt=1700000001+i)))
        (history/(ident+'.json')).write_text(json.dumps(record))
    return control


def wait_for(predicate, seconds=30):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        value=predicate()
        if value:return value
        time.sleep(.03)
    raise TimeoutError('Synthetic load deadline exceeded')


class LoadServer:
    def __init__(self, root, pdf='simulated'):
        self.root,self.pdf=root.resolve(),pdf
        self.control=self.root/'.git/load-control'
        self.samples=[]
        self.samples_lock=threading.Lock()
        self.secrets=[]
        self.process=None
        self.port=0

    def start(self):
        ready=self.control/'ready.json';ready.unlink(missing_ok=True)
        (self.control/'stop').unlink(missing_ok=True)
        env={k:v for k,v in os.environ.items() if not credential_name(k)}
        env.update(PYTHONUTF8='1',PYTHONPATH=str(ROOT/'src')+os.pathsep+str(ROOT/'tests'),VITA_TEST_CONTROL=str(self.control))
        started=time.monotonic()
        self.process=subprocess.Popen([sys.executable,str(ROOT/'tests/load_server.py'),'--root',str(self.root),
             '--port',str(self.port),'--pdf',self.pdf],env=env,stdin=subprocess.PIPE,
             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def available():
            if self.process.poll() is not None:raise RuntimeError('Synthetic server exited during startup')
            try:return json.loads(ready.read_text())
            except (FileNotFoundError,ValueError):return None
        state=wait_for(available)
        self.port=state['port'];self.base=f'http://127.0.0.1:{self.port}'
        self.server_pid=state['pid']
        self.token=self.api('/api/session')['token']
        self.secrets.append(self.token)
        return (time.monotonic()-started)*1000

    def api(self, route, data=None, expected=200, measure=True, timeout=30):
        if getattr(self,'deadline',float('inf')) < time.monotonic():
            raise TimeoutError('Declared load profile deadline exceeded')
        headers={'Origin':self.base}
        if data is not None:headers.update({'Content-Type':'application/json','X-Vita-Token':self.token})
        request=Request(self.base+route,headers=headers,data=json.dumps(data).encode() if data is not None else None)
        started=time.monotonic();status=0;body=b''
        try:
            try:
                with urlopen(request,timeout=timeout) as response:status=response.status;body=response.read()
            except HTTPError as error:status=error.code;body=error.read()
            assert status==expected,f'Unexpected HTTP status {status} for {route.split("?")[0]}'
            return json.loads(body)
        finally:
            if measure:
                with self.samples_lock:self.samples.append(dict(route=route.split('?')[0],ms=(time.monotonic()-started)*1000,
                    status=status,expected=expected,bytes=len(body)))

    def snapshot(self, branch):return self.api('/api/workspace?branch='+branch)

    def create(self, label, **load):
        source=self.snapshot('master')
        job=dict(label=label,pipeline=True,extraction=True,require_analysis=True,require_adapted=True,load=load)
        branch=self.api('/api/create',dict(base='master',name=label,revision=source['revision'],projectRevision=source['projectRevision'],job=json.dumps(job)))
        location=Path(branch['worktree'])
        git(location,'add','main.tex','job.md');git(location,'commit','-m','Synthetic captured job')
        (self.control/(label+'.release')).touch()  # fake_ai_process legacy analyze gate
        return self.snapshot(label)

    def connection(self, label):
        key='SYNTHETIC-LOAD-KEY-'+label
        self.secrets.append(key)
        result=self.api('/api/connections',dict(name='Fixture '+label,provider='openai',apiKey=key))
        return dict(default=dict(provider='openai',model='fixture-model',reasoning='',connection=result['id']),steps={}),key

    def launch(self, branch, config, steps=None):
        return self.api('/api/adapt',dict(branch=branch['branch'],revision=branch['revision'],jobRevision=branch['jobRevision'],
            workflow=dict(steps=steps or ['extract','analyze','adapt','cover']),aiConfig=config,reviewPolicy='automatic'))

    def finished(self, run, seconds=60):
        return wait_for(lambda:(row if (row:=self.api('/api/job?id='+run['id']))['status'] not in ('running','queued') else None),seconds)

    def retry(self, run, config=None):
        branch=self.snapshot(run['branch'])
        data=dict(id=run['id'],revision=branch['revision'],jobRevision=branch['jobRevision'])
        if config is not None:data['aiConfig']=config
        preview=self.api('/api/resume-preview',data)
        child=self.api('/api/resume',{**data,'token':preview['token']})
        assert child['parentRunId']==run['id'] and child['attempt']==run['attempt']+1
        return child,preview

    def stop(self, abrupt=False):
        import psutil
        started=time.monotonic()
        children=[]
        try:children=[(p.pid,p.create_time()) for p in psutil.Process(self.server_pid).children(recursive=True)]
        except psutil.Error:pass
        if abrupt:
            actual=psutil.Process(self.server_pid)
            assert actual.pid==self.process.pid or self.process.pid in [p.pid for p in actual.parents()]
            actual.kill()
        else:
            (self.control/'stop').touch()
        self.process.wait(timeout=20);self.process.stdin.close()
        def remaining():
            result=[]
            for pid,created in children:
                try:
                    p=psutil.Process(pid)
                    if p.create_time()==created and p.status()!=psutil.STATUS_ZOMBIE:result.append(pid)
                except psutil.Error:pass
            return result
        deadline=time.monotonic()+5
        while remaining() and time.monotonic()<deadline:time.sleep(.03)
        zombies=0
        for pid,created in children:
            try:
                p=psutil.Process(pid)
                zombies+=p.create_time()==created and p.status()==psutil.STATUS_ZOMBIE
            except psutil.Error:pass
        return dict(ms=(time.monotonic()-started)*1000,orphans=len(remaining()),zombies=zombies)


class ResourceSampler:
    def __init__(self, pid, interval=.05):
        self.pid,self.interval=pid,interval
        self.rows=[];self.cpu={};self.server_cpu=[];self.stop_event=threading.Event()
        self.thread=threading.Thread(target=self.sample,daemon=True)

    def sample(self):
        import psutil
        while not self.stop_event.is_set():
            try:
                server=psutil.Process(self.pid);children=server.children(recursive=True)
                rss=server.memory_info().rss
                self.server_cpu.append(sum(server.cpu_times()[:2]))
                handles=server.num_handles() if os.name=='nt' else server.num_fds()
                child_rss=0
                for p in [server,*children]:
                    try:
                        self.cpu[(p.pid,p.create_time())]=sum(p.cpu_times()[:2])
                        if p.pid!=self.pid:child_rss+=p.memory_info().rss
                    except psutil.Error:pass
                self.rows.append(dict(at=time.monotonic(),serverRss=rss,childRss=child_rss,children=len(children),handles=handles))
            except psutil.Error:pass
            self.stop_event.wait(self.interval)

    def start(self):self.thread.start();return self

    def finish(self):
        self.stop_event.set();self.thread.join(timeout=2)
        assert self.rows,'No resource samples were collected'
        return dict(samples=len(self.rows),intervalMs=self.interval*1000,
                    serverPeakRssMiB=max(r['serverRss'] for r in self.rows)/2**20,
                    descendantsPeakRssMiB=max(r['childRss'] for r in self.rows)/2**20,
                    serverRssGrowthMiB=(self.rows[-1]['serverRss']-self.rows[0]['serverRss'])/2**20,
                    peakDescendants=max(r['children'] for r in self.rows),handleGrowth=self.rows[-1]['handles']-self.rows[0]['handles'],
                    serverCpuSeconds=self.server_cpu[-1]-self.server_cpu[0],
                    sampledDescendantCpuSeconds=sum(v for (pid,_),v in self.cpu.items() if pid!=self.pid),
                    note='CPU is a sampled lower bound; short-lived processes may finish between samples. Descendant RSS sums shared pages.')
