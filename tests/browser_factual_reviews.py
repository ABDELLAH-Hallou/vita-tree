"""Keyboard factual decisions, draft conflicts and real PDF, using Vita CV's gate."""
import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from browser_support import BROWSERS, launch_browser
from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest
from support import SOURCE, init_repo, set_theme


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=BROWSERS,default='chromium')
    parser.add_argument('--vita-source',type=Path)
    args=parser.parse_args()
    if args.vita_source:
        sys.path.insert(0,str(args.vita_source.resolve()))
        os.environ['PYTHONPATH']=str(args.vita_source.resolve())+os.pathsep+os.environ.get('PYTHONPATH','')
    import vita
    expect.set_options(timeout=40000)
    artifacts=ROOT/'.test-artifacts';root=init_repo(artifacts/('facts-ui-'+str(time.time_ns())))
    source=Path(vita.__file__).resolve().parent.parent
    server=VitaTreeServer(('127.0.0.1',0),root,'main.tex',source,log_dir=root/'.git/test-logs')
    command=[sys.executable,str(Path(__file__).parent/'smoke/factual_ai.py')]
    control=root/'.git/factual-control';control.mkdir()
    branch=server.workspace.create('master','facts',json.dumps({'label':'facts','pipeline':True}),digest(SOURCE))
    from requirements_fixtures import seed
    seed(server.workspace,'facts')
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();errors=[];applications=[]
    try:
        with patch.object(server.workspace,'vita_command',return_value=command),patch.dict(os.environ,{'VITA_TEST_CANONICAL':'1','VITA_TEST_CONTROL':str(control)}),sync_playwright() as pw:
            run=server.workspace.start_ai('facts',branch['revision'],branch['jobRevision'],provider='codex',workflow={'steps':['adapt','cover']})
            browser=launch_browser(pw,args.browser)
            page=browser.new_page(viewport={'width':1500,'height':1050})
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('request',lambda req:applications.append(req.url) if '/api/factual-review/apply' in req.url else None)
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.get_by_role('button',name='Open facts',exact=True).click()
            expect(page.locator('.dag-node[data-step=adapt] .dag-status')).to_have_text('Needs factual review')
            expect(page.locator('#resume-run')).to_be_hidden()
            # Graph clicks continue opening ordinary captured AI settings.
            page.locator('.dag-node[data-step=adapt]').click()
            expect(page.locator('#step-ai-dialog')).to_be_visible();page.locator('#step-ai-cancel').click()
            expect(page.locator('.dag-node[data-step=adapt]')).to_have_attribute('data-status','review')
            page.locator('#workflow-next').click()
            cards=page.locator('.factual-change');expect(cards).to_have_count(3)
            expect(cards.first).to_contain_text('main.tex');expect(cards.first).to_contain_text('Original wording')
            expect(cards.nth(1)).to_contain_text('abbreviation');expect(cards.nth(1)).to_contain_text('not verified')
            cards.first.locator('input[value=accept]').focus();page.keyboard.press('Space')
            page.locator('#cancel-factual-review').click();expect(page.locator('#factual-review-panel')).to_be_hidden()
            assert not applications
            page.locator('#review-facts').click();expect(page.locator('.factual-change input:checked')).to_have_count(0)
            page.locator('#apply-factual-review').click();assert not applications
            for index,choice in enumerate(('accept','reject','edit')):
                cards.nth(index).locator(f'input[value={choice}]').focus();page.keyboard.press('Space')
            expect(cards.nth(2).locator('textarea')).to_be_focused()
            cards.nth(2).locator('textarea').fill(r'Languages & Python, SQL, TypeScript \\')
            page.locator('#confirm-factual-meaning').focus();page.keyboard.press('Space')
            page.locator('#factual-review-panel').screenshot(path=str(artifacts/'factual-review-light.png'))
            def unavailable_continuation(route):
                route.fulfill(status=503,json={'error':'Synthetic continuation unavailable; your approval is saved.'})
            page.route('**/api/review-continue',unavailable_continuation)
            page.locator('#apply-factual-review').click()
            expect(page.locator('#factual-review-error')).to_contain_text('Synthetic continuation unavailable')
            expect(page.locator('#factual-source-preview')).to_contain_text('TypeScript')
            expect(page.locator('.factual-change input')).to_have_count(0)
            assert len(applications)==1
            page.unroute('**/api/review-continue',unavailable_continuation)
            page.locator('#apply-factual-review').click()
            expect(page.locator('#factual-review-panel')).to_be_hidden()
            assert len(applications)==1
            assert page.locator('.dag-failure').count()==0
            expect(page.locator('.dag-node[data-step=cover] .dag-status')).to_have_text('Needs factual review')
            cover_run=server.workspace.list_jobs()['runs'][0]
            page.locator('#workflow-run').select_option(run['id'])
            page.locator('#review-facts').click()
            expect(page.locator('#factual-source-preview')).to_contain_text('TypeScript')
            expect(page.locator('#factual-source-preview')).not_to_contain_text('Built OOP services')
            expect(page.locator('#factual-source-preview').locator('..').locator('summary')).to_have_text('Approved LaTeX · your decisions applied')
            page.locator('#cancel-factual-review').click()
            page.locator('#workflow-run').select_option(cover_run['id'])
            page.locator('#review-facts').click();expect(page.locator('.factual-change')).to_have_count(1)
            cover=server.workspace.factual_review(server.workspace.list_jobs()['runs'][0]['id'])
            assert 'dependable systems' in cover['proposed'] and 'TypeScript' in cover['proposed']
            assert 'Built OOP services' not in cover['proposed']
            page.locator('.factual-change input[value=accept]').check();page.locator('#confirm-factual-meaning').check()
            page.locator('#apply-factual-review').click();expect(page.locator('#factual-review-panel')).to_be_hidden()
            expect(page.locator('.dag-node[data-step=validating]')).to_have_attribute('data-status','succeeded')
            page.locator('#view-run').click();page.locator('#open-run-cover-pdf').click()
            expect(page.locator('#cover-pdf .textLayer').first).to_be_visible()
            final=server.workspace.list_jobs()['runs'][0]
            pdf=server.workspace.cover_pdf_result(final['id'])
            extracted='\n'.join(p.extract_text() or '' for p in PdfReader(pdf['pdf']).pages)
            assert 'dependable' in extracted and 'TypeScript' in extracted and 'OOP' not in extracted
            assert 'TypeScript' in server.workspace.read('facts','main.tex')
            assert 'Built OOP services' not in server.workspace.read('facts','main.tex')
            # An external edit after capture produces an actionable conflict.
            stale=server.workspace.create('master','stale-facts',json.dumps({'label':'stale','pipeline':True}),digest(SOURCE))
            seed(server.workspace,'stale-facts')
            stale_run=server.workspace.start_ai('stale-facts',stale['revision'],stale['jobRevision'],provider='codex',workflow={'steps':['adapt']})
            page.locator('#back').click();page.locator('#refresh').click()
            page.get_by_role('button',name='Open stale-facts',exact=True).click()
            expect(page.locator('.dag-node[data-step=adapt] .dag-status')).to_have_text('Needs factual review')
            page.locator('#review-facts').click()
            expect(page.locator('.factual-change')).to_have_count(3)
            (Path(stale['worktree'])/'main.tex').write_text(SOURCE+'\n% external user draft',encoding='utf-8')
            page.locator('#accept-all-facts').click();expect(page.locator('.factual-change input[value=accept]:checked')).to_have_count(3)
            page.locator('#confirm-factual-meaning').check();page.locator('#apply-factual-review').click()
            expect(page.locator('#factual-review-error')).to_contain_text('application changed')
            assert 'external user draft' in server.workspace.read('stale-facts','main.tex')
            page.locator('#cancel-factual-review').click();set_theme(page,'dark');page.locator('#review-facts').click();page.locator('#factual-review-panel').screenshot(path=str(artifacts/'factual-review-dark.png'))
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            assert page.locator('#factual-review-panel .panel-footer').evaluate('el => el.scrollWidth <= el.clientWidth + 1')
            page.locator('#factual-review-panel .review-scroll').evaluate('el=>el.scrollTop=el.scrollHeight')
            for control in ['#close-factual-review','#apply-factual-review','#cancel-factual-review']:
                box=page.locator(control).bounding_box();assert box and box['y']>=0 and box['y']+box['height']<=844,box
            page.locator('#factual-review-panel').screenshot(path=str(artifacts/'factual-review-mobile.png'))
            response=page.request.post(f'http://127.0.0.1:{server.server_port}/api/factual-review/apply',data={})
            assert response.status==403
            public=json.dumps(server.workspace.list_jobs())
            assert 'Built OOP services' not in public and SOURCE not in public
            page.locator('#cancel-factual-review').click()
            assert page.evaluate('''async()=>{const {renderGraph}=await import('/workflow.js');const host=document.createElement('div');renderGraph(host,{run:{id:'new',createdAt:2,stages:[{id:'extract',status:'skipped'}]},history:[{id:'old',createdAt:1,stages:[{id:'extract',status:'succeeded'}]}],options:{steps:[]},available:{},select:()=>{}});return host.querySelector('[data-step=extract]').dataset.status==='previous'&&host.textContent.includes('Historical result · not loaded');}''')
            page.set_viewport_size({'width':1500,'height':1050});page.screenshot(path=str(artifacts/'guided-workspace-dark.png'))
            # Requirements approval also starts the remaining steps without a Retry dialog.
            guided=server.workspace.create('master','guided-requirements-ui',json.dumps({'label':'guided-requirements-ui','pipeline':True}),digest(SOURCE))
            page.locator('#back').click();page.locator('#refresh').click()
            page.get_by_role('button',name='Open guided-requirements-ui',exact=True).click()
            page.get_by_role('tab',name='Job details & AI',exact=False).click()
            page.locator('#provider').select_option('codex');page.locator('#model').fill('fixture-model');page.locator('#model').press('Tab')
            expect(page.locator('#review-policy')).to_have_value('manual')
            for step in ('analyze','review','cover'):page.locator('#step-'+step).uncheck()
            for step in ('extract','adapt'):page.locator('#step-'+step).check()
            page.locator('#run-adapt').click()
            expect(page.locator('#workflow-next')).to_have_text('Review job requirements',timeout=90000)
            page.locator('#workflow-next').click();expect(page.locator('#requirements-dialog')).to_be_visible()
            page.locator('#requirements-confirm').check();page.locator('#requirements-approve').click()
            expect(page.locator('#requirements-dialog')).not_to_be_visible()
            expect(page.locator('#workflow-next')).to_have_text('Review CV changes',timeout=90000)
            page.locator('#workflow-next').click();page.locator('#accept-all-facts').click();page.locator('#confirm-factual-meaning').check()
            # A fast checkpoint-only continuation can finish before its HTTP
            # response arrives. It must still refresh the visible CV, without Retry.
            def completed_continuation(route):
                response=route.fetch()
                child=response.json()
                deadline=time.monotonic()+60
                while server.workspace.get_job(child['id'])['status'] in ('running','queued') and time.monotonic()<deadline:
                    time.sleep(.05)
                finished=server.workspace.get_job(child['id'])
                assert finished['status']=='succeeded',finished
                assert 'adapt' in finished['checkpointSteps'],finished
                route.fulfill(response=response,json=finished)
            page.route('**/api/review-continue',completed_continuation)
            page.locator('#apply-factual-review').click();expect(page.locator('#factual-review-panel')).to_be_hidden()
            expect(page.locator('.dag-node[data-step=validating]')).to_have_attribute('data-status','succeeded',timeout=90000)
            assert 'dependable systems' in server.workspace.read('guided-requirements-ui','main.tex')
            expect(page.locator('#current-document')).to_contain_text('dependable systems')
            page.get_by_role('tab',name='Source · Advanced',exact=True).click()
            expect(page.locator('#current-source')).to_contain_text('dependable systems')
            page.screenshot(path=str(artifacts/('approved-cv-'+args.browser+'.png')))
            page.unroute('**/api/review-continue',completed_continuation)
            # Automatic mode is an explicit UI choice; the real contract still gates publication.
            automatic=server.workspace.create('master','automatic-ui',json.dumps({'label':'automatic-ui','pipeline':True}),digest(SOURCE))
            seed(server.workspace,'automatic-ui')
            page.locator('#back').click();page.locator('#refresh').click()
            page.get_by_role('button',name='Open automatic-ui',exact=True).click()
            page.get_by_role('tab',name='Job details & AI',exact=False).click()
            page.locator('#provider').select_option('codex');page.locator('#model').fill('fixture-model');page.locator('#model').press('Tab')
            for step in ('extract','analyze','review'):page.locator('#step-'+step).uncheck()
            for step in ('adapt','cover'):page.locator('#step-'+step).check()
            page.locator('#review-policy').select_option('automatic')
            page.locator('#run-adapt').click()
            expect(page.locator('.dag-node[data-step=validating]')).to_have_attribute('data-status','succeeded',timeout=180000)
            expect(page.locator('#factual-review-panel')).to_be_hidden()
            auto=server.workspace.list_jobs()['runs'][0]
            assert auto['reviewPolicy']=='automatic' and auto['attempt']==3,auto
            assert 'Built OOP services' in server.workspace.read('automatic-ui','main.tex')
            assert 'Built OOP services' in server.workspace.read('automatic-ui','cover-letter.tex')
            assert auto['stages'][2]['reusedFrom']
            page.locator('#back').click();page.get_by_role('button',name='Open facts',exact=True).click()
            expect(page.locator('#review-policy')).to_have_value('manual')
            assert not errors,errors
            browser.close()
            print('PASS: fixed review controls; keyboard and bulk accept/reject/edit; requirements approval continues to Adapt; approved wording reaches main.tex and Cover; explicit automatic mode and manual reset; historical completion labels; real selectable PDF; stale-draft conflict; light/dark/mobile; graph configuration; authentication; no providers.')
    finally:
        server.shutdown();server.server_close();worker.join(timeout=5)


if __name__=='__main__':main()
