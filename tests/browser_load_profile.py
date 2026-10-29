"""Measure browser work against a declared synthetic history and live local runs."""
import argparse
import json
from pathlib import Path
import platform
import time

from load_support import ROOT, PROFILES, LoadServer, prepare, profile, distribution, sha, wait_for, git, LOAD_SOURCE, processor_label


def measure(output, name, browser_name, enforce):
    from playwright.sync_api import sync_playwright, expect
    config = profile(name)
    output.mkdir(parents=True, exist_ok=False)
    root = output/'repository'
    control = prepare(root, config)
    server = LoadServer(root)
    started=time.monotonic()
    server.deadline=started+config['deadlineSeconds']
    errors, requests, interactions = [], [], []
    result = dict(schemaVersion=1, profile=name, concurrency=config['concurrency'],
                  history=config['history'], pdfMode='simulated', passed=False,
                  profileVersion='1.0.0',profileSha256=sha(PROFILES.read_bytes()),
                  treeCommit=git(ROOT,'rev-parse','HEAD'),python=platform.python_version(),platform=platform.system(),processor=processor_label(),
                  sourceSha256=sha(LOAD_SOURCE),
                  codeSha256={p:sha((ROOT/p).read_bytes()) for p in ('tests/browser_load_profile.py','tests/load_provider.py',
                      'src/vita_tree/static/app.js','src/vita_tree/static/runs.js','src/vita_tree/workspace.py')})
    try:
        server.start()
        runs, prepared = [], []
        for i in range(config['concurrency']):
            label = f'browser-{i}'
            settings, key = server.connection(label)
            branch = server.create(label, gate='browser', gateSeconds=config['deadlineSeconds'], keySha256=sha(key), delayMs=150)
            if i == config['concurrency']-1:
                (control/(label+'.cover.fail')).touch()
            prepared.append((branch,settings))
        for branch,settings in prepared:runs.append(server.launch(branch, settings))
        wait_for(lambda: len(list(control.glob('*.started.json'))) >= config['concurrency'], 45)
        with sync_playwright() as p:
            browser = p.chromium.launch(**({'channel':'chrome'} if browser_name=='chrome' else {}))
            result['browserVersion'] = browser.version
            page = browser.new_page(viewport={'width':1440, 'height':1000})
            page.on('pageerror', lambda error: errors.append(type(error).__name__))
            pending=set();peak_pollers=[0]
            def request(value):
                if '/api/jobs' in value.url:
                    pending.add(value);peak_pollers[0]=max(peak_pollers[0],len(pending))
            def finished(value):
                if value in pending:
                    # Remove before response(): a synchronous Playwright call
                    # can dispatch the next request event while it is waiting.
                    pending.discard(value)
                    response=value.response()
                    requests.append(dict(status=response.status if response else 0,timing=value.timing))
            page.on('request',request)
            page.on('requestfinished',finished)
            page.on('requestfailed',finished)
            page.add_init_script("""window.__loadTasks=[];
                new PerformanceObserver(list => window.__loadTasks.push(...list.getEntries().map(e=>e.duration)))
                .observe({entryTypes:['longtask']});""")
            cdp = page.context.new_cdp_session(page)
            cdp.send('Performance.enable')
            page.goto(server.base)
            expect(page.get_by_role('button',name='Open master',exact=True)).to_be_visible(timeout=60000)
            expect(page.locator('#filter-running')).to_have_text(str(config['concurrency']),timeout=60000)
            before = {r['name']:r['value'] for r in cdp.send('Performance.getMetrics')['metrics']}
            # Dispatch-to-next-paint includes the synchronous filter/render work,
            # excluding driver/network latency. Two frames permit a paint.
            for value in ['history-0', '', 'browser-', '', 'master', '']*3:
                interactions.append(page.evaluate("""async value => {
                    const input=document.querySelector('#search'), start=performance.now();
                    input.value=value; input.dispatchEvent(new Event('input',{bubbles:true}));
                    await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
                    return performance.now()-start;
                }""",value))
            page.get_by_role('button',name='Open master',exact=True).click()
            expect(page.locator('#current-label')).to_have_text('master',timeout=60000)
            page.get_by_role('tab',name='Source · Advanced',exact=True).click()
            # Native source editor input goes through CodeMirror. Preserve an
            # unsaved draft while runs on other applications finish.
            editor = page.locator('#current-source .cm-content')
            editor.click()
            editor.press('ControlOrMeta+End')
            editor.press('Enter')
            editor.press_sequentially('% unsaved browser load draft')
            (control/'browser.release').touch()
            for run in runs:
                finished=server.finished(run)
                assert finished['status']==('failed' if run==runs[-1] else 'succeeded')
            expect(editor).to_contain_text('unsaved browser load draft',timeout=60000)
            expect(page.locator('#filter-failed')).to_have_text('1',timeout=60000)
            expect(page.locator('#filter-running')).to_have_text('0',timeout=60000)
            page.locator('#save-source').click()
            expect(page.locator('#save-state')).to_have_text('Draft saved on this computer',timeout=60000)
            # Natural polling must stay single-flight and unchanged histories
            # must not repeatedly replace the branch list.
            page.locator('#back').click()
            expect(page.locator('#branch-list')).to_be_visible()
            expect(page.locator('#refresh')).to_be_enabled(timeout=60000)
            page.wait_for_timeout(1800)
            page.evaluate("""window.__mutations=0;new MutationObserver(r=>window.__mutations+=r.length)
                .observe(document.querySelector('#branch-list'),{childList:true,subtree:true});""")
            page.wait_for_timeout(3300)
            assert page.evaluate('window.__mutations')==0, 'Idle history caused DOM churn'
            assert peak_pollers[0]==1,'Browser job polling overlapped'
            # Rows use content-visibility:auto. Verify that offscreen rows
            # actually paint when reached; a full-page screenshot alone can
            # contain intentionally deferred (blank) offscreen content.
            last=page.locator('#branch-list .branch-row').last
            last.scroll_into_view_if_needed()
            expect(last.locator('.branch-name')).to_be_visible()
            page.wait_for_function("""() => {
                const rows=document.querySelectorAll('#branch-list .branch-row');
                const row=rows[rows.length-1];
                const names=document.querySelectorAll('#branch-list .branch-row .branch-name');
                if(!row)return false;
                const box=row.getBoundingClientRect();
                if(box.top<0||box.bottom>innerHeight){row.scrollIntoView({block:'end'});return false;}
                return row.checkVisibility({contentVisibilityAuto:true})&&names[names.length-1]?.checkVisibility({contentVisibilityAuto:true});
            }""")
            page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
            page.screenshot(path=str(output/'synthetic-history-bottom.png'))
            page.evaluate('window.scrollTo(0,0)')
            after = {r['name']:r['value'] for r in cdp.send('Performance.getMetrics')['metrics']}
            result.update(interactionMs=distribution(interactions), longTasksMs=distribution(page.evaluate('window.__loadTasks')),
                          browserCosts={k:after[k]-before[k] for k in ('ScriptDuration','LayoutDuration','TaskDuration')},
                          heapMiB=after['JSHeapUsedSize']/2**20, domNodes=after['Nodes'], polls=requests,
                          peakConcurrentPolls=peak_pollers[0],pageErrors=errors, idleBranchMutations=page.evaluate('window.__mutations'))
            page.screenshot(path=str(output/'synthetic-history.png'))
            result['budgetResults']={
                'uiInteractionP95Ms':dict(actual=result['interactionMs']['p95'],maximum=config['budgets']['uiInteractionP95Ms']),
                'uiHeapMiB':dict(actual=result['heapMiB'],maximum=config['budgets']['uiHeapMiB'])}
            for budget in result['budgetResults'].values():budget['passed']=budget['actual']<=budget['maximum']
            result['passed']=not errors and all(r['status']==200 for r in requests) and (not enforce or all(v['passed'] for v in result['budgetResults'].values()))
            browser.close()
    except Exception as error:
        result['failureCategory']=type(error).__name__
        print(type(error).__name__,str(error))
    finally:
        # Keep observed slow interactions and failed polls even if a later
        # safety assertion prevents completion of the scenario.
        result.setdefault('interactionMs',distribution(interactions))
        result.setdefault('polls',requests)
        result.setdefault('pageErrors',errors)
        result['elapsedMs']=(time.monotonic()-started)*1000
        (control/'browser.release').touch()
        if server.process and server.process.poll() is None:
            result['shutdown']=server.stop()
            result['passed'] &= result['shutdown']['orphans']==0
        (output/'browser-results.json').write_text(json.dumps(result,indent=2)+'\n')
    return result['passed']


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--profile',choices=['ci','sustained'],default='ci')
    parser.add_argument('--browser',choices=['chromium','chrome'],default='chromium')
    parser.add_argument('--enforce-budgets',action='store_true')
    args=parser.parse_args()
    raise SystemExit(not measure(args.output.resolve(),args.profile,args.browser,args.enforce_budgets))
