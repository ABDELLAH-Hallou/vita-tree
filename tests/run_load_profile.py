"""Bounded synthetic multi-branch load. No live provider option is provided."""
import argparse
import datetime
import json
from pathlib import Path
import platform
import importlib.metadata
import shutil
import subprocess
import sys
import threading
import time

from load_support import (ROOT,PROFILES,LOAD_SOURCE,LoadServer,ResourceSampler,distribution,
                          git,prepare,profile,sha,wait_for)


def benchmark(output, name, pdf, enforce=False):
    config=profile(name)
    assert not output.exists(),'Use a fresh evidence directory'
    output.mkdir(parents=True)
    root=output/'repository';control=root/'.git/load-control'
    server=LoadServer(root,pdf)
    report=dict(schemaVersion=1,profile=name,profileVersion='1.0.0',profileSha256=sha(PROFILES.read_bytes()),
        at=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),platform=platform.system(),
        treeCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        sourceSha256=sha(LOAD_SOURCE),fixtureSha256=sha((ROOT/'tests/load_provider.py').read_bytes()),
        codeSha256={p:sha((ROOT/p).read_bytes()) for p in ('src/vita_tree/workspace.py','src/vita_tree/processes.py','src/vita_tree/pdf.py',
            'src/vita_tree/static/runs.js','src/vita_tree/static/app.js','tests/run_load_profile.py','tests/load_support.py')},
        declared=dict(concurrency=config['concurrency'],waves=config['waves'],history=config['history'],historyBranches=config['historyBranches'],
            historyRequirementsFraction=.5,historyFactualFraction=.2,pollers=config['pollers'],pollIntervalMs=config['pollIntervalMs'],pdfMode=pdf),
        budgets=config['budgets'],runs=[],checks=[],shutdowns=[],startupMs=[],phases={},failures=[],providerOverlapSamples=[],
        limits=['Synthetic provider sleeps are not a provider throughput benchmark.',
                'Fixture barrier time, measured sleep and local subprocess overhead are separate; phases may be nested and must not be summed blindly.',
                'Simulated PDF mode measures a 40 ms stub, not TeX performance. Real mode retains restricted compiler flags.',
                'No live AI provider, credentials, prompts, stdout or private source are included.'])
    stop=threading.Event();pollers=[];sampler=None;resources=[];began=time.monotonic();run_ids=[]
    server.deadline=began+config['deadlineSeconds']
    import psutil
    report['machine']=dict(logicalCpus=psutil.cpu_count(),physicalCpus=psutil.cpu_count(logical=False),
                           totalMemoryMiB=psutil.virtual_memory().total/2**20,
                           psutil=importlib.metadata.version('psutil'),osRelease=platform.release())
    report['engine']={'mode':pdf,'version':None}
    if pdf=='real':
        executable=shutil.which('pdflatex')
        if executable:
            # This is a bounded version probe, never a package installer.
            probe=subprocess.run([executable,'--version'],stdin=subprocess.DEVNULL,capture_output=True,timeout=10)
            report['engine']['version']=probe.stdout.decode(errors='replace').splitlines()[0]
    def check(label, value):
        report['checks'].append(dict(name=label,passed=bool(value)))
        assert value,'Safety check failed: '+label
    def poll():
        while not stop.is_set():
            try:server.api('/api/jobs')
            except (OSError,AssertionError,ValueError):pass  # raw status=0/failed sample remains in evidence
            stop.wait(config['pollIntervalMs']/1000)
    def save_report():
        (output/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    def capture(run, expected='succeeded', reason='normal'):
        result=server.finished(run)
        run_ids.append(run['id'])
        detail=server.api('/api/execution?id='+run['id'])
        phases=detail['tree'].get('events',[])
        ms={}
        for event in phases:
            if event.get('duration_ms') is not None and event['status'] in ('ok','error'):
                ms[event['phase']]=ms.get(event['phase'],0)+event['duration_ms']
                report['phases'].setdefault(event['phase'],[]).append(event['duration_ms'])
        wall=(result['finishedAt']-result['startedAt'])*1000
        pdf_work=[json.loads(p.read_text()) for p in control.glob('*.pdf.json')]
        pdf_ms=sum(p['ms'] for p in pdf_work if p['label']==run['branch'] and result['startedAt']<=p['startedAt']<=result['finishedAt'])
        report['runs'].append(dict(id=run['id'],branch=run['branch'],status=result['status'],attempt=result['attempt'],
            expectedStatus=expected,reason=reason,censored=result['status']=='interrupted',
            parentRunId=result.get('parentRunId'),wallMs=wall,phaseMs=ms,pdfMs=pdf_ms,
            localOutsideSubprocessAndPdfMs=None if result['status']=='interrupted' else max(0,wall-ms.get('subprocess',0)-pdf_ms)))
        check('expected terminal state '+run['id'],result['status']==expected)
        return result
    def started(labels, step='extract'):
        def all_started():
            rows=[]
            for path in control.glob('*.started.json'):
                try:rows.append(json.loads(path.read_text()))
                except ValueError:continue
            return {row['label'] for row in rows if row['step']==step} >= set(labels)
        wait_for(all_started,45)
    try:
        setup_started=time.monotonic()
        prepare(root,config)
        report['fixtureSetupMs']=(time.monotonic()-setup_started)*1000
        report['startupMs'].append(server.start())
        server.api('/api/jobs')  # warm history/HTTP before the resource baseline
        sampler=ResourceSampler(server.server_pid,config['sampleIntervalMs']/1000).start()
        for _ in range(config['pollers']):
            t=threading.Thread(target=poll,daemon=True);t.start();pollers.append(t)
        idle=server.create('editing')
        idle_source=idle['content']
        for wave in range(config['waves']):
            assert time.monotonic()-began<config['deadlineSeconds'],'Profile wall-clock deadline'
            group=[];labels=[];prepared=[]
            for index in range(config['concurrency']):
                label=f'wave-{wave:02}-{index:02}'
                cfg,key=server.connection(label)
                branch=server.create(label,gate=f'wave-{wave}',gateSeconds=config['deadlineSeconds'],delayMs=config['providerDelayMs'][index%len(config['providerDelayMs'])],keySha256=sha(key))
                prepared.append((branch,cfg));labels.append(label)
                if index==config['concurrency']-1:(control/(label+'.cover.fail')).touch()
            for branch,cfg in prepared:group.append(server.launch(branch,cfg))
            started(labels)
            evidence=[json.loads(p.read_text()) for p in control.glob('*.started.json')]
            alive=[r for r in evidence if r['label'] in labels and r['step']=='extract' and psutil.pid_exists(r['pid'])]
            report['providerOverlapSamples'].append(len(alive))
            check(f'wave {wave} has declared simultaneous providers',len(alive)==config['concurrency'])
            # One unrelated application remains editable while every provider is waiting.
            idle=server.snapshot('editing')
            changed=idle_source+f'\n% independent wave {wave}'
            server.api('/api/save',dict(branch='editing',path='main.tex',revision=idle['revision'],projectRevision=idle['projectRevision'],content=changed))
            active=server.snapshot(labels[0])
            server.api('/api/save',dict(branch=labels[0],path='main.tex',revision=active['revision'],content='forbidden'),expected=409)
            server.api('/api/adapt',dict(branch=labels[0],revision=active['revision'],jobRevision=active['jobRevision']),expected=409)
            for label in labels:
                check('active worktree retained '+label,server.api('/api/release-worktree',dict(branch=label))['reason']=='active')
            (control/(f'wave-{wave}.release')).touch()
            for index,run in enumerate(group):
                wanted='failed' if index==len(group)-1 else 'succeeded'
                result=capture(run,wanted,'provider failure' if wanted=='failed' else 'normal')
                check('deterministic outcome '+run['branch'],result['status']==wanted)
                if wanted=='failed':
                    snap=server.snapshot(run['branch'])
                    check('failed attempt does not publish adaptation',snap['content']==LOAD_SOURCE)
                    child,plan=server.retry(result)
                    check('retry reuses verified adapted source',set(plan['reuse'])=={'extract','analyze','adapt'})
                    result=capture(child,'failed','repeated provider failure')
                    check('repeated retry leaves original draft',server.snapshot(run['branch'])['content']==LOAD_SOURCE)
                    (control/(run['branch']+'.cover.fail')).unlink()
                    child,plan=server.retry(result)
                    result=capture(child)
                    check('checkpoint retry succeeds',result['status']=='succeeded')
                snap=server.snapshot(run['branch'])
                check('branch-isolated adaptation '+run['branch'],run['branch']+' systems' in snap['content'])
                check('include unchanged '+run['branch'],snap['files'][1]['content']=='Untouched included section.\n')
                # Dirty/ignored output is intentionally retained, then explicitly
                # versioned by the test before requesting clean worktree cleanup.
                location=Path(snap['worktree'])
                if location.exists():
                    git(location,'add','main.tex','job.md','cover-letter.tex');git(location,'add','-f','.vita/results')
                    git(location,'commit','-m','Synthetic load result')
                    check('clean owned worktree released '+run['branch'],server.api('/api/release-worktree',dict(branch=run['branch']))['released'])
            check('independent draft survives',server.snapshot('editing')['content']==changed)
            save_report()

        # External edits during generation must block atomic publication.
        cfg,key=server.connection('conflict');branch=server.create('conflict',gate='conflict',keySha256=sha(key))
        conflict=server.launch(branch,cfg);started(['conflict'])
        target=Path(branch['worktree'])/'sections/extra.tex'
        target.write_text('Concurrent included-file edit.\n',encoding='utf-8')
        (control/'conflict.release').touch()
        check('concurrent include edit blocks publication',capture(conflict,'failed','concurrent edit')['status']=='failed')
        check('external source preserved',target.read_text()=='Concurrent included-file edit.\n')
        check('stale adaptation not published',server.snapshot('conflict')['content']==LOAD_SOURCE)

        # Removing a session key affects future submissions, never captured work.
        cfg,key=server.connection('removed');branch=server.create('removed',gate='removed',keySha256=sha(key))
        removed=server.launch(branch,cfg);started(['removed'])
        server.api('/api/connections/remove',dict(id=cfg['default']['connection']))
        other=server.create('unavailable',keySha256=sha(key))
        server.api('/api/adapt',dict(branch='unavailable',revision=other['revision'],jobRevision=other['jobRevision'],aiConfig=cfg),expected=400)
        (control/'removed.release').touch()
        check('captured connection finishes after removal',capture(removed)['status']=='succeeded')

        # Both graceful shutdown and abrupt death happen with a live descendant.
        stop.set()
        for t in pollers:t.join(timeout=35)
        resources.append(sampler.finish());sampler=None
        for abrupt in (False,True):
            label='crash' if abrupt else 'shutdown'
            cfg,key=server.connection(label)
            branch=server.create(label,gate=label,keySha256=sha(key),spawnChild=True)
            running=server.launch(branch,cfg);started([label])
            if sampler:resources.append(sampler.finish());sampler=None
            report['shutdowns'].append(dict(abrupt=abrupt,**server.stop(abrupt)))
            check(label+' has no executing orphan',report['shutdowns'][-1]['orphans']==0)
            report['startupMs'].append(server.start())
            sampler=ResourceSampler(server.server_pid,config['sampleIntervalMs']/1000).start()
            capture(running,'interrupted',label)
            check(label+' recovered interrupted',server.api('/api/job?id='+running['id'])['status']=='interrupted')
            check(label+' did not publish',server.snapshot(label)['content']==LOAD_SOURCE)
            check(label+' clears session connections',not server.api('/api/connections')['connections'])
            cfg,key=server.connection(label)  # explicit reconnection/override after restart
            (control/(label+'.release')).touch()
            child,plan=server.retry(server.api('/api/job?id='+running['id']),cfg)
            check(label+' retry succeeds',capture(child)['status']=='succeeded')
        public=json.dumps(server.api('/api/jobs'))
        check('public history contains no session credentials',all(secret not in public for secret in server.secrets))
        retained_files=0;retained_bytes=0;credentials_preserved=True
        for name in ('runs','checkpoints','job-history'):
            for path in (root/'.git/vita-tree'/name).rglob('*'):
                if path.is_file():
                    body=path.read_bytes();retained_files+=1;retained_bytes+=len(body)
                    credentials_preserved &= all(secret.encode() not in body for secret in server.secrets)
        check('retained credential isolation',credentials_preserved)
        report['retainedStorage']=dict(files=retained_files,bytes=retained_bytes)
        # Only the deliberately dirty editing/conflict/removed/recovery drafts
        # may remain. A clean idle branch must be available in ordinary Git.
        untouched=server.create('clean-idle')
        check('idle clean worktree releases',server.api('/api/release-worktree',dict(branch='clean-idle'))['released'])
        check('ordinary Git can open released branch',git(root,'worktree','list','--porcelain').count('refs/heads/clean-idle')==0)
    except Exception as error:
        report['failures'].append(dict(category=type(error).__name__,phase='load_profile'))
        print('FAIL:',type(error).__name__,str(error),file=sys.stderr)
    finally:
        stop.set()
        for t in pollers:t.join(timeout=35)
        if sampler:resources.append(sampler.finish())
        if server.process and server.process.poll() is None:
            try:report['shutdowns'].append(dict(abrupt=False,**server.stop()))
            except Exception as error:
                report['failures'].append(dict(category=type(error).__name__,phase='final_shutdown'))
                server.process.kill();server.process.wait(timeout=5)
        report['resources']=resources
        report['requests']=server.samples
        report['distributions']={route:distribution([s['ms'] for s in server.samples if s['route']==route]) for route in sorted({s['route'] for s in server.samples})}
        timings=[]
        for path in control.glob('*.timing.json'):
            row=json.loads(path.read_text());timings.append({k:row[k] for k in ('step','waitMs','barrierMs','credentialValid','status')})
        report['providerFixture']=dict(calls=timings,waitMs=distribution([t['waitMs'] for t in timings]),barrierMs=distribution([t['barrierMs'] for t in timings]),
            interruptedWithoutOutcome=len(list(control.glob('*.started.json')))-len(timings))
        report['phaseDistributions']={key:distribution(value) for key,value in report['phases'].items()}
        pdf_calls=[json.loads(p.read_text()) for p in control.glob('*.pdf.json')]
        report['pdfWork']=dict(mode=pdf,calls=pdf_calls,ms=distribution([p['ms'] for p in pdf_calls]))
        report['wallMs']=distribution([r['wallMs'] for r in report['runs']])
        report['outcomes']={status:sum(r['status']==status for r in report['runs']) for status in ('succeeded','failed','interrupted')}
        report['outcomes']['failedFraction']=report['outcomes']['failed']/len(report['runs']) if report['runs'] else None
        report['requestFailures']=dict(timeouts=sum(s['status']==0 for s in server.samples),
            unexpectedStatuses=sum(s['status']!=s['expected'] for s in server.samples))
        metrics=dict(submitP95Ms=report['distributions'].get('/api/adapt',{}).get('p95'),pollP95Ms=report['distributions'].get('/api/jobs',{}).get('p95'),
            orchestrationP95Ms=distribution([r['localOutsideSubprocessAndPdfMs'] for r in report['runs'] if not r['censored']])['p95'],
            pdfP95Ms=report['pdfWork']['ms']['p95'],shutdownMs=max((s['ms'] for s in report['shutdowns']),default=0),
            unexpectedFailures=len(report['failures'])+sum(s['status']!=s['expected'] for s in server.samples),
            orphans=sum(s['orphans'] for s in report['shutdowns']),cleanWorktreeLeaks=sum(not c['passed'] for c in report['checks'] if c['name'].startswith('clean owned')))
        for field in ('serverPeakRssMiB','serverRssGrowthMiB','peakDescendants','handleGrowth'):
            metrics[field]=max((r[field] for r in resources),default=None)
        report['budgetResults']={key:dict(actual=value,maximum=config['budgets'][key],passed=value is not None and value<=config['budgets'][key]) for key,value in metrics.items()}
        report['elapsedMs']=(time.monotonic()-began)*1000
        safety=all(metrics[key]==0 for key in ('unexpectedFailures','orphans','cleanWorktreeLeaks'))
        report['passed']=safety and all(c['passed'] for c in report['checks']) and (not enforce or all(v['passed'] for v in report['budgetResults'].values()))
        save_report()
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--profile',choices=['ci','sustained'],default='ci');parser.add_argument('--pdf',choices=['real','simulated'],default='simulated')
    parser.add_argument('--enforce-budgets',action='store_true');args=parser.parse_args()
    report=benchmark(args.output.resolve(),args.profile,args.pdf,args.enforce_budgets)
    print(json.dumps(dict(passed=report['passed'],runs=len(report['runs']),budgetResults=report['budgetResults']),indent=2))
    raise SystemExit(not report['passed'])


if __name__=='__main__':main()
