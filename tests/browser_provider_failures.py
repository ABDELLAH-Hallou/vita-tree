"""Typed failures, explicit generation checks, Apply/Cancel, and retry lineage.
No real providers or repository data are contacted or published.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parent)]
from browser_support import BROWSERS, launch_browser
from playwright.sync_api import sync_playwright, expect
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest
from vita_tree.outcomes import safe_outcome
from diagnostic_fixtures import seed_run
from test_provider_status import outcome
from support import init_repo, SOURCE, set_theme


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=BROWSERS,default='chromium')
    args=parser.parse_args();expect.set_options(timeout=40000)
    artifacts=Path('.test-artifacts').resolve();root=init_repo(artifacts/('provider-ui-'+str(time.time_ns())))
    control=root/'.git/control';control.mkdir()
    source=root/'.git/fake-vita';prompts=source/'vita/assets/prompts';prompts.mkdir(parents=True)
    for step in ('extract','review','cover'):(prompts/(step+'.md')).write_text('Fixture',encoding='utf-8')
    (source/'vita/helpers').mkdir();(source/'vita/helpers/llm.py').write_text('# Bridge fixture',encoding='utf-8')
    server=VitaTreeServer(('127.0.0.1',0),root,'main.tex',source,log_dir=root/'.git/test-logs')
    label='provider-recovery'
    branch=server.workspace.create('master',label,json.dumps({'label':label,'pipeline':True,'extraction':True,'provider_error':'overloaded'}),digest(SOURCE))
    flag=control/(label+'.analyze.fail');flag.touch();(control/(label+'.release')).touch()
    cases=[]
    for category in ('overloaded','rate_limit','authentication','invalid_model','invalid_json'):
        record=seed_run(server.workspace,backend=False)
        record.update(provider='codex',model='shared-codex-model')
        record['outcomes']={'analyze':{'status':'failed','verified':False,'backend':safe_outcome(outcome(category))}}
        server.workspace._persist_job(record);cases.append((record,category))
    calls=control/'generation.calls'
    command=[sys.executable,str(Path(__file__).with_name('fake_provider_dispatch.py').resolve())]
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();errors=[];network=None;workspace_requests=[]
    try:
        with patch.object(server.workspace,'vita_command',return_value=command),patch('vita_tree.providers.codex_efforts',return_value={'fixture-codex':['low','medium','high']}),patch.dict(os.environ,{'VITA_TEST_CONTROL':str(control),'VITA_TEST_CHECK_CALLS':str(calls),'GEMINI_API_KEY':'PRIVATE-SESSION-KEY'}),sync_playwright() as pw:
            browser=launch_browser(pw,args.browser)
            page=browser.new_page(viewport={'width':1500,'height':1050})
            def report_error(error):
                errors.append(str(error));print('Browser error:',error,flush=True)
            page.on('pageerror',report_error)
            page.on('console',lambda msg:print('Browser console:',msg.text,flush=True) if msg.type=='error' else None)
            network=(artifacts/'provider-browser-requests.log').open('w',encoding='utf-8')
            def request_log(kind,request):
                if kind=='start' and '/api/workspace?' in request.url:workspace_requests.append(request.url)
                if '/api/' in request.url or kind=='failed':
                    network.write(str(time.time())+' '+kind+' '+request.url+'\n');network.flush()
            page.on('request',lambda r:request_log('start',r))
            page.on('requestfinished',lambda r:request_log('done',r))
            page.on('requestfailed',lambda r:request_log('failed',r))
            url=f'http://127.0.0.1:{server.server_port}';page.goto(url)
            assert page.locator('.dag-failure').count()==0
            # Action panel/history show all typed failures without diagnosing every error as credentials.
            page.get_by_role('button',name='Open master',exact=True).click()
            for record,category in cases:
                page.locator('#workflow-run').select_option(record['id'])
                expect(page.locator('#workflow-next-help')).to_contain_text(category.replace('_',' '))
                expect(page.locator('#workflow-next-help')).to_contain_text('Effective: gemini / fixture-model')
                expect(page.locator('#workflow-summary')).to_contain_text('3 provider attempts')
                before=len(workspace_requests)
                page.locator('#view-run').click()
                expect(page.locator('#attempt-history')).to_contain_text(category.replace('_',' '))
                assert len(workspace_requests)==before, 'Opening same-application history should not reload the workspace'
            page.locator('[data-open-diagnostics]:visible').click()
            expect(page.locator('#execution-list')).to_contain_text('Service temporarily busy')
            expect(page.locator('#execution-list')).to_contain_text('Sign-in or API key rejected')
            page.keyboard.press('Escape')
            page.locator('#back').click()
            page.get_by_role('button',name='Open '+label,exact=True).click()
            page.get_by_role('tab',name='Job details & AI',exact=False).click()
            page.locator('#provider').select_option('codex');page.locator('#model').fill('fixture-codex');page.locator('#model').press('Tab')
            page.locator('#reasoning').select_option('high')
            # Listing models and opening/cancelling a check never sends a generation.
            assert not calls.exists()
            page.locator('#shared-ai-fields [data-check-generation]').click()
            expect(page.locator('#generation-check-dialog')).to_contain_text('may consume paid usage')
            page.locator('#generation-check-dialog').screenshot(path=str(artifacts/'provider-generation-confirm.png'))
            page.locator('#cancel-generation-check').click();assert not calls.exists()
            page.locator('#shared-ai-fields [data-check-generation]').click()
            page.locator('#confirm-generation-check').click()
            expect(page.locator('#generation-check-result')).to_contain_text('Generation succeeded')
            assert calls.read_text(encoding='utf-8').splitlines()==['codex / fixture-codex']
            page.locator('#cancel-generation-check').click()
            # Inherited component routes can be checked without creating an override.
            page.locator('.dag-node[data-step=extract]').click()
            expect(page.locator('#step-ai-shared')).to_be_checked()
            expect(page.locator('#step-ai-fields [data-check-generation]')).to_be_enabled()
            page.locator('#step-ai-fields [data-check-generation]').click()
            expect(page.locator('#generation-check-route')).to_contain_text('Shared setup')
            page.locator('#confirm-generation-check').click()
            expect(page.locator('#generation-check-result')).to_contain_text('Generation succeeded')
            page.locator('#cancel-generation-check').click();page.locator('#step-ai-cancel').click()
            assert len(calls.read_text(encoding='utf-8').splitlines())==2
            # Check an unapplied popup draft, then cancel it: no override saved.
            page.locator('.dag-node[data-step=extract]').click();page.locator('#step-ai-custom').check()
            page.locator('#popup-provider').select_option('gemini');page.locator('#popup-model').fill('overloaded')
            page.locator('#step-ai-fields [data-check-generation]').click()
            page.locator('#confirm-generation-check').click()
            expect(page.locator('#generation-check-result')).to_contain_text('Service temporarily busy')
            expect(page.locator('#generation-check-result')).to_contain_text('3 provider attempts')
            page.locator('#cancel-generation-check').click();page.locator('#step-ai-cancel').click()
            expect(page.locator('.dag-node[data-step=extract] .dag-model')).to_have_text('fixture-codex')
            # Applying a separate Extract route still works; Escape discards another draft.
            page.locator('.dag-node[data-step=extract]').click();page.locator('#step-ai-custom').check()
            page.locator('#popup-provider').select_option('gemini');page.locator('#popup-model').fill('extract-model')
            page.locator('#step-ai-apply').click()
            expect(page.locator('.dag-node[data-step=extract] .dag-model')).to_have_text('extract-model')
            page.locator('.dag-node[data-step=extract]').click();page.locator('#popup-model').fill('discarded')
            page.keyboard.press('Escape');expect(page.locator('.dag-node[data-step=extract] .dag-model')).to_have_text('extract-model')
            # Failed inherited Codex step and checkpoint retry use frozen configuration.
            for step in ('extract','analyze','adapt','review','cover'):page.locator('#step-'+step).set_checked(step in ('extract','analyze'))
            page.locator('#run-adapt').click()
            expect(page.locator('.dag-node[data-step=analyze]')).to_have_attribute('data-status','failed')
            expect(page.locator('#workflow-next-help')).to_contain_text('Effective: codex / fixture-codex')
            expect(page.locator('#workflow-summary')).to_contain_text('Wait a little')
            page.locator('#workflow-graph').screenshot(path=str(artifacts/'provider-failed-graph.png'))
            page.locator('#model').fill('new-shared-model');page.locator('#model').press('Tab')
            page.locator('#resume-run').press('Enter')
            expect(page.locator('#resume-summary')).to_contain_text('Preserves the AI setup')
            expect(page.locator('#resume-reuse')).to_contain_text('Identify job requirements')
            page.locator('#resume-current-config').check()
            expect(page.locator('#resume-summary')).to_contain_text('currently shown')
            # close() changes `open` synchronously but dispatches `close` later.
            # Complete Cancel (including its state-reset handler) before opening
            # a new review; a rapid reopen must not inherit the old close event.
            page.evaluate('''() => {window.__resumeCancelComplete=false;
              document.querySelector('#resume-dialog').addEventListener('close',()=>{window.__resumeCancelComplete=true;},{once:true});}''')
            page.locator('#resume-dialog .close-dialog').last.click()
            page.wait_for_function('()=>window.__resumeCancelComplete===true')
            assert len([r for r in server.workspace.jobs.values() if r['branch']==label])==1
            page.locator('#resume-run').press('Enter');expect(page.locator('#resume-current-config')).not_to_be_checked()
            expect(page.locator('#confirm-resume')).to_be_enabled();page.locator('#confirm-resume').press('Enter')
            expect(page.locator('#workflow-run')).to_contain_text('Attempt 2')
            expect(page.locator('.dag-node[data-step=analyze]')).to_have_attribute('data-status','failed')
            expect(page.locator('#workflow-next-help')).to_contain_text('Effective: codex / fixture-codex')
            page.locator('#view-run').click()
            expect(page.locator('#attempt-history')).to_contain_text('Captured setup preserved')
            # Explicit changed-config attempt; Extract remains reusable and local CV untouched.
            flag.unlink();page.locator('#resume-run').press('Enter');page.locator('#resume-current-config').check();expect(page.locator('#confirm-resume')).to_be_enabled();page.locator('#confirm-resume').press('Enter')
            expect(page.locator('#workflow-run')).to_contain_text('Attempt 3')
            expect(page.locator('.dag-node[data-step=validating]')).to_have_attribute('data-status','succeeded')
            page.locator('#view-run').click();expect(page.locator('#attempt-history')).to_contain_text('Changed setup')
            assert len((control/(label+'.extract.calls')).read_text(encoding='utf-8').splitlines())==1
            assert Path(branch['worktree']).joinpath('main.tex').read_text(encoding='utf-8')==SOURCE
            assert 'PRIVATE' not in json.dumps(server.workspace.list_jobs())
            assert 'PRIVATE' not in page.locator('body').inner_text()
            denied=page.request.post(url+'/api/generation-check',data={'branch':label,'step':'extract','confirmed':True})
            assert denied.status==403
            set_theme(page,'light');page.screenshot(path=str(artifacts/'provider-errors-light.png'),full_page=True)
            set_theme(page,'dark');page.screenshot(path=str(artifacts/'provider-errors-dark.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(artifacts/'provider-errors-mobile.png'),full_page=True)
            page.reload();page.locator('#view-run').click();expect(page.locator('#attempt-history .attempt-row')).to_have_count(3)
            assert not errors,errors
            browser.close()
        print('PASS: typed graph/history errors, explicit generation usage confirmation/cancel/success/failure, popup Apply/Cancel/Escape, captured and changed-config checkpoint retry lineage, repeated failure, local drafts preserved, themes/mobile, auth boundary, no live providers.')
    finally:
        if network:network.close()
        server.shutdown();server.server_close();worker.join()
        for thread in list(server.workspace._ai_threads):thread.join(timeout=15)


if __name__=='__main__':main()
