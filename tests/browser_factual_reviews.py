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
from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest
from support import SOURCE, init_repo, set_theme


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=('chrome','chromium'),default='chromium')
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
    branch=server.workspace.create('master','facts',json.dumps({'label':'facts','pipeline':True}),digest(SOURCE))
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();errors=[];applications=[]
    try:
        with patch.object(server.workspace,'vita_command',return_value=command),sync_playwright() as pw:
            run=server.workspace.start_ai('facts',branch['revision'],branch['jobRevision'],provider='codex',workflow={'steps':['adapt','cover']})
            browser=pw.chromium.launch(channel='chrome' if args.browser=='chrome' else None)
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
            page.locator('#review-facts').click()
            cards=page.locator('.factual-change');expect(cards).to_have_count(3)
            expect(cards.first).to_contain_text('main.tex');expect(cards.first).to_contain_text('Original wording')
            expect(cards.nth(1)).to_contain_text('acronym');expect(cards.nth(1)).to_contain_text('not verified')
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
            page.locator('#apply-factual-review').click()
            expect(page.locator('#factual-review-title')).to_have_text('Your factual decisions')
            expect(page.locator('#factual-provenance')).to_contain_text('Explicit local-user review')
            assert len(applications)==1
            assert server.workspace.read('facts','main.tex')==SOURCE
            page.reload();expect(page.locator('#branch-title')).to_have_text('facts')
            page.locator('#review-facts').click();expect(page.locator('#factual-provenance')).to_be_visible()
            page.locator('#cancel-factual-review').click()
            page.locator('#resume-run').click();expect(page.locator('#resume-reuse')).to_contain_text('Tailor CV')
            page.locator('#confirm-resume').click()
            expect(page.locator('.dag-node[data-step=cover] .dag-status')).to_have_text('Needs factual review')
            page.locator('#review-facts').click();expect(page.locator('.factual-change')).to_have_count(1)
            cover=server.workspace.factual_review(server.workspace.list_jobs()['runs'][0]['id'])
            assert 'dependable systems' in cover['proposed'] and 'TypeScript' in cover['proposed']
            assert 'Built OOP services' not in cover['proposed']
            page.locator('.factual-change input[value=accept]').check();page.locator('#confirm-factual-meaning').check()
            page.locator('#apply-factual-review').click();expect(page.locator('#factual-review-title')).to_have_text('Your factual decisions')
            page.locator('#cancel-factual-review').click();page.locator('#resume-run').click()
            expect(page.locator('#resume-reuse')).to_contain_text('Cover letter');page.locator('#confirm-resume').click()
            expect(page.locator('.dag-node[data-step=validating]')).to_have_attribute('data-status','succeeded')
            page.locator('#view-run').click();page.locator('#open-run-cover-pdf').click()
            expect(page.locator('#cover-pdf .textLayer').first).to_be_visible()
            final=server.workspace.list_jobs()['runs'][0]
            pdf=server.workspace.cover_pdf_result(final['id'])
            extracted='\n'.join(p.extract_text() or '' for p in PdfReader(pdf['pdf']).pages)
            assert 'dependable' in extracted and 'TypeScript' in extracted and 'OOP' not in extracted
            # An external edit after capture produces an actionable conflict.
            stale=server.workspace.create('master','stale-facts',json.dumps({'label':'stale','pipeline':True}),digest(SOURCE))
            stale_run=server.workspace.start_ai('stale-facts',stale['revision'],stale['jobRevision'],provider='codex',workflow={'steps':['adapt']})
            page.locator('#back').click();page.locator('#refresh').click()
            page.get_by_role('button',name='Open stale-facts',exact=True).click()
            expect(page.locator('.dag-node[data-step=adapt] .dag-status')).to_have_text('Needs factual review')
            page.locator('#review-facts').click()
            expect(page.locator('.factual-change')).to_have_count(3)
            (Path(stale['worktree'])/'main.tex').write_text(SOURCE+'\n% external user draft',encoding='utf-8')
            for radio in page.locator('.factual-change input[value=accept]').all():radio.check()
            page.locator('#confirm-factual-meaning').check();page.locator('#apply-factual-review').click()
            expect(page.locator('#factual-review-error')).to_contain_text('application changed')
            assert 'external user draft' in server.workspace.read('stale-facts','main.tex')
            set_theme(page,'dark');page.locator('#factual-review-panel').screenshot(path=str(artifacts/'factual-review-dark.png'))
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            assert page.locator('#factual-review-panel .panel-footer').evaluate('el => el.scrollWidth <= el.clientWidth + 1')
            page.locator('#factual-review-panel').screenshot(path=str(artifacts/'factual-review-mobile.png'))
            response=page.request.post(f'http://127.0.0.1:{server.server_port}/api/factual-review/apply',data={})
            assert response.status==403
            public=json.dumps(server.workspace.list_jobs())
            assert 'Built OOP services' not in public and SOURCE not in public
            assert not errors,errors
            browser.close()
            print('PASS: keyboard accept/reject/edit, source-linked review, cancellation, explicit approval, restart-visible provenance, checkpoint retries, rejected wording excluded from Cover, real selectable PDF, stale-draft conflict, themes/mobile, graph configuration and auth boundary; no providers.')
    finally:
        server.shutdown();server.server_close();worker.join(timeout=5)


if __name__=='__main__':main()
