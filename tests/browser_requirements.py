"""Canonical requirements review with the actual backend and no AI calls."""
import argparse
import os
from pathlib import Path
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from playwright.sync_api import sync_playwright, expect
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest
from vita_tree import requirements_review as review
from requirements_fixtures import JD,seed
from support import SOURCE,init_repo,set_theme


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=('chrome','chromium'),default='chromium');parser.add_argument('--vita-source',type=Path)
    args=parser.parse_args()
    if args.vita_source:
        sys.path.insert(0,str(args.vita_source.resolve()))
        os.environ['PYTHONPATH']=str(args.vita_source.resolve())+os.pathsep+os.environ.get('PYTHONPATH','')
    import vita
    expect.set_options(timeout=40000)
    artifacts=ROOT/'.test-artifacts';root=init_repo(artifacts/('requirements-ui-'+str(time.time_ns())))
    server=VitaTreeServer(('127.0.0.1',0),root,'main.tex',Path(vita.__file__).resolve().parent.parent,log_dir=root/'.git/test-logs')
    server.workspace.create('master','requirements',JD,digest(SOURCE));seed(server.workspace,'requirements',False)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();errors=[];writes=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome' if args.browser=='chrome' else None)
            page=browser.new_page(viewport={'width':1500,'height':1050});page.on('pageerror',lambda e:(errors.append(str(e)),print('Browser error:',str(e))))
            page.on('request',lambda req:writes.append(req.url) if req.method=='POST' and '/api/requirements/' in req.url else None)
            page.goto(f'http://127.0.0.1:{server.server_port}');page.get_by_role('button',name='Open requirements',exact=True).click()
            # Ordinary graph config remains reachable; nested review does not cancel it.
            page.locator('.dag-node[data-step=extract]').click();expect(page.locator('#step-ai-dialog')).to_be_visible()
            page.locator('#step-ai-custom').check()
            page.locator('#step-requirements').click();expect(page.locator('#requirements-dialog')).to_be_visible()
            cards=page.locator('.requirement-card');expect(cards).to_have_count(4)
            expect(page.locator('#requirements-items')).to_contain_text('Employment conditions · not scored')
            assert sorted(el.input_value() for el in cards.get_by_label('Classification',exact=True).all())==['preferred','required','required','unclear']
            # Source quote is in a textarea; select the row using its canonical ID.
            hub=cards.filter(has=page.locator('textarea')).all()
            hub=next(card for card in hub if 'HubSpot' in card.get_by_label('Criterion',exact=True).input_value())
            hub.get_by_role('button',name='View source',exact=False).focus();page.keyboard.press('Enter')
            expect(page.locator('#requirements-source [data-line="3"]')).to_be_focused()
            expect(page.locator('#requirements-source [data-line="3"]')).to_have_class('source-selected')
            hub.get_by_label('Criterion',exact=True).fill('Unsaved correction')
            page.locator('#requirements-cancel').click();expect(page.locator('#requirements-dialog')).not_to_be_visible()
            expect(page.locator('#step-ai-dialog')).to_be_visible();expect(page.locator('#step-ai-custom')).to_be_checked();assert not writes
            page.locator('#step-requirements').click();expect(page.get_by_label('Criterion',exact=True).first).not_to_have_value('Unsaved correction')
            # Invalid corrections leave the revision and approval unchanged.
            first=cards.first.get_by_label('Criterion',exact=True);previous=first.input_value();first.fill('')
            page.locator('#requirements-save').click();expect(page.locator('#requirements-error')).to_contain_text('Invalid definition')
            first.fill(previous+' (reviewed)');page.locator('#requirements-save').click()
            expect(page.locator('#requirements-status')).to_have_text('Review required · dependent steps are paused.')
            page.locator('#requirements-confirm').focus();page.keyboard.press('Space')
            page.locator('#requirements-dialog').screenshot(path=str(artifacts/'requirements-light.png'))
            page.locator('#requirements-approve').click();expect(page.locator('#requirements-dialog')).not_to_be_visible()
            page.locator('#step-ai-cancel').click()
            # A recorded assessment uses its captured definition forever.
            captured=review.view(server.workspace,'requirements')['definition'];now=time.time()
            run={'id':'c'*32,'branch':'requirements','status':'succeeded','step':'completed','message':'Synthetic assessment',
                 'createdAt':now,'startedAt':now,'finishedAt':now,'reviewed':True,'attempt':1,'requirementsRevision':captured['revision'],
                 'stages':[dict(id='analyze',status='succeeded',startedAt=now,finishedAt=now)]}
            review.retain_run(server.workspace,run,review.context_for(server.workspace,'requirements'),captured)
            server.workspace._persist_job(run);server.workspace.jobs[run['id']]=run
            # Reload restores the shared approved revision, and a new edit creates a draft.
            page.reload();page.locator('#requirements-current-open').click();expect(page.locator('#requirements-status')).to_contain_text('Approved definition')
            page.get_by_label('Criterion',exact=True).first.fill('Another deliberate correction');page.locator('#requirements-save').click()
            expect(page.locator('#requirements-status')).to_contain_text('Review required')
            page.locator('#requirements-cancel').click()
            expect(page.locator('.dag-node[data-step=analyze] .dag-status')).to_contain_text('requirements changed')
            page.locator('#requirements-captured').click();expect(page.locator('#requirements-status')).to_contain_text('view only')
            expect(page.locator('#requirements-save')).to_be_hidden();expect(page.locator('#requirement-add')).to_be_hidden()
            expect(page.locator('#requirements-revision')).to_have_text(captured['revision'])
            expect(page.locator('#requirements-current')).to_contain_text('Earlier assessments need to be rerun')
            page.locator('#requirements-current-button').click();expect(page.locator('#requirements-save')).to_be_visible()
            page.locator('#requirements-cancel').click();set_theme(page,'dark');page.locator('#requirements-current-open').click();expect(page.locator('#requirements-dialog')).to_be_visible();page.locator('#requirements-dialog').screenshot(path=str(artifacts/'requirements-dark.png'))
            page.set_viewport_size({'width':390,'height':844})
            assert page.locator('#requirements-dialog').evaluate('el=>el.scrollWidth<=el.clientWidth+1')
            page.locator('#requirements-dialog').screenshot(path=str(artifacts/'requirements-mobile.png'))
            response=page.request.post(f'http://127.0.0.1:{server.server_port}/api/requirements/approve',data={});assert response.status==403
            assert JD not in str(server.workspace.list_jobs()) and 'HubSpot' not in str(server.workspace.list_jobs())
            assert not errors,errors
            browser.close()
            print('PASS: separate Extract review, keyboard source navigation, conditions/classifications, correction validation, cancellation, immutable approval, reload, AI Apply/Cancel preservation, themes/mobile and auth; no providers.')
    except Exception:
        if 'page' in locals() and not page.is_closed():
            print('UI notices:',page.locator('#notice').text_content())
            page.screenshot(path=str(artifacts/'requirements-failure.png'))
        raise
    finally:
        server.shutdown();server.server_close();worker.join(timeout=5)


if __name__=='__main__':main()
