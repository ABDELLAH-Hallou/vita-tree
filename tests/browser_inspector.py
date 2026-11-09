"""Execution inspection with deterministic backend diagnostics; no live models."""
import argparse
import io
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from playwright.sync_api import sync_playwright, expect
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest
from diagnostic_fixtures import write_backend
from support import init_repo, SOURCE, set_theme


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=('chrome','chromium'),default='chromium')
    args=parser.parse_args();expect.set_options(timeout=30000)
    artifacts=Path('.test-artifacts').resolve()
    root=init_repo(artifacts/('inspector-ui-'+str(time.time_ns())))
    control=root/'.git/control';control.mkdir()
    config=root/'.vita';config.mkdir()
    (config/'extensions.json').write_text(json.dumps({'llm_providers':{'openai':{'model':'fixture-model'}}}))
    source=root/'.git/fake-vita'
    prompts=source/'vita/assets/prompts';prompts.mkdir(parents=True)
    for step in ('extract','review','cover'):(prompts/(step+'.md')).write_text('Fixture task')
    server=VitaTreeServer(('127.0.0.1',0),root,'main.tex',source,log_dir=root/'.git/test-logs')
    label='inspector-opportunity'
    branch=server.workspace.create('master',label,json.dumps({'label':label,'pipeline':True,'extraction':True,'diagnostics':'overloaded'}),digest(SOURCE))
    fail=control/(label+'.cover.fail');fail.touch()
    (control/(label+'.release')).touch()
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    command=[sys.executable,str(Path(__file__).with_name('fake_ai_process.py').resolve())]
    errors=[]
    try:
        with patch.object(server.workspace,'vita_command',return_value=command),patch.dict(os.environ,{'VITA_TEST_CONTROL':str(control)}),sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome' if args.browser=='chrome' else None)
            page=browser.new_page(viewport={'width':1440,'height':1050})
            page.on('pageerror',lambda error:errors.append(str(error)))
            url=f'http://127.0.0.1:{server.server_port}'
            page.goto(url);page.get_by_role('button',name='Open '+label,exact=True).click()
            page.get_by_role('tab',name='Job details & AI',exact=False).click()
            page.locator('#provider').select_option('openai')
            page.locator('#model').fill('fixture-model');page.locator('#model').press('Tab')
            page.locator('#run-all').click()
            expect(page.locator('.dag-node[data-step=cover]')).to_have_attribute('data-status','failed',timeout=60000)
            parent=next(iter(server.workspace.jobs.values()))
            assert parent['checkpointSteps']==['extract','analyze','adapt','review'],parent
            # Graph selection retains its configuration controls and opens evidence.
            page.locator('.dag-node[data-step=cover]').click()
            page.locator('#inspect-step-dialog').click()
            expect(page.locator('#diagnostics-dialog')).to_be_visible()
            expect(page.locator('#execution-step')).to_have_value('cover')
            expect(page.locator('#execution-contract')).to_contain_text('diagnostics v1')
            expect(page.locator('#inspector-panel-overview')).to_contain_text('overloaded')
            expect(page.locator('#inspector-panel-overview')).to_contain_text('temporarily overloaded')
            page.get_by_role('tab',name='Response',exact=True).click()
            expect(page.locator('#inspector-panel-response')).to_contain_text('No model response produced')
            page.get_by_role('tab',name='Error',exact=True).click()
            page.locator('#inspector-panel-error summary').first.click()
            expect(page.locator('#inspector-panel-error pre').first).to_contain_text('"http_status": 503')
            expect(page.locator('#inspector-panel-error pre').first).to_contain_text('"retryable": true')
            # Keyboard tabs, retry delays, requested/effective origins.
            page.get_by_role('tab',name='Overview',exact=True).focus();page.keyboard.press('ArrowRight')
            expect(page.get_by_role('tab',name='Timeline',exact=True)).to_be_focused()
            expect(page.locator('#inspector-panel-timeline')).to_contain_text('retry delay 0.125s')
            page.keyboard.press('ArrowRight')
            expect(page.locator('#inspector-panel-request')).to_contain_text('Shared settings')
            page.locator('#inspector-panel-request summary').filter(has_text='Backend-reported').first.click()
            expect(page.locator('#inspector-panel-request')).to_contain_text('model_origin')
            # Capture state distinctions and safe lazy artifact viewing.
            span=server.workspace.inspector.read_tree(parent)['configuration']['cover']['spanId']
            refs=[]
            for status in ('disabled','suppressed','truncated','redacted'):
                proc,_=write_backend(server.workspace.inspector.destination,parent['traceId'],span,'cover','success',status)
                refs.append(proc['diagnostic_artifacts'][0])
            page.locator('#refresh-executions').click()
            page.get_by_role('tab',name='Response',exact=True).click()
            for message in ('content capture disabled','privacy suppression','structure truncated','source values removed'):
                expect(page.locator('#inspector-panel-response')).to_contain_text(message)
            button=page.locator('#inspector-panel-response [data-artifact="'+refs[-1]['id']+'"]')
            button.click()
            expect(page.locator('#inspector-panel-response [data-artifact-content]')).to_contain_text('[REDACTED]')
            target=server.workspace.inspector.path(parent['traceId'],refs[-1]['path'])
            raw=json.loads(target.read_text());raw['data']['value']='<img src=x onerror=alert("private-canary")>';target.write_text(json.dumps(raw))
            button.click()
            expect(page.locator('#inspector-panel-response [data-artifact-content]')).to_contain_text('unsafe')
            assert not page.locator('#execution-inspector img,#execution-inspector script').count()
            assert 'private-canary' not in page.locator('#execution-inspector').inner_text()
            # The export can be inspected before download; bodies and paths stay out.
            page.get_by_role('tab',name='Artifacts',exact=True).click()
            page.get_by_role('button',name='Review support export',exact=True).click()
            expect(page.locator('[data-export-review]')).to_contain_text('not anonymization')
            link=page.get_by_role('link',name='Download inspected support bundle')
            response=page.request.get(url+link.get_attribute('href'))
            assert response.status==200
            with zipfile.ZipFile(io.BytesIO(response.body())) as archive:
                content=archive.read('diagnostics.json').decode()
                assert 'private-canary' not in content and str(root) not in content and 'Jordan Lee' not in content
            # Both themes and a narrow dialog must remain usable.
            set_theme(page,'light');page.screenshot(path=str(artifacts/'inspector-light.png'))
            page.get_by_role('button',name='Close activity and support',exact=True).click()
            set_theme(page,'dark');page.locator('#inspect-run').click()
            expect(page.locator('#execution-detail')).to_be_visible()
            page.screenshot(path=str(artifacts/'inspector-dark.png'))
            page.set_viewport_size({'width':390,'height':844})
            assert page.locator('#diagnostics-dialog').evaluate('el=>el.scrollWidth<=el.clientWidth')
            page.screenshot(path=str(artifacts/'inspector-mobile.png'))
            page.set_viewport_size({'width':1440,'height':1050})
            page.get_by_role('button',name='Close activity and support',exact=True).click()
            # Explicit changed setup is optional; inspector Retry preserves the old route.
            page.locator('#model').fill('different-model');page.locator('#model').press('Tab')
            page.locator('#inspect-run').click()
            page.locator('#execution-retry').click()
            expect(page.locator('#resume-summary')).to_contain_text('Preserves the AI setup')
            expect(page.locator('#resume-reuse')).to_contain_text('Tailor CV')
            page.locator('#resume-current-config').check()
            expect(page.locator('#resume-reuse')).to_contain_text('None')
            page.locator('#resume-current-config').uncheck()
            expect(page.locator('#resume-reuse')).to_contain_text('Tailor CV')
            page.locator('#resume-dialog .close-dialog').filter(has_text='Cancel').click()
            assert len(server.workspace.jobs)==1
            page.locator('#inspect-run').click();page.locator('#execution-retry').click()
            page.locator('#confirm-resume').click()
            expect(page.locator('#workflow-run option:checked')).to_contain_text('Attempt 2',timeout=60000)
            expect(page.locator('.dag-node[data-step=cover]')).to_have_attribute('data-status','failed',timeout=60000)
            assert len(server.workspace.jobs)==2
            assert server.workspace.read(label,'main.tex')==SOURCE
            fail.unlink()
            page.locator('#inspect-run').click();page.locator('#execution-retry').click();page.locator('#confirm-resume').click()
            expect(page.locator('.dag-node[data-step=cover]')).to_have_attribute('data-status','succeeded',timeout=60000)
            assert len((control/(label+'.adapt.calls')).read_text().splitlines())==1
            latest=max(server.workspace.jobs.values(),key=lambda item:item['attempt'])
            assert latest['traceId']==parent['traceId'] and latest['attempt']==3
            assert not server.workspace.inspector.read_tree(latest)['configurationChanged']
            # Navigation/reload preserves evidence and search; no live provider called.
            page.reload();page.locator('#inspect-run').click()
            page.locator('#execution-search').fill(parent['traceId'])
            expect(page.locator('#execution-list .execution-row')).to_have_count(3)
            page.locator('#execution-status').select_option('failed')
            expect(page.locator('#execution-list .execution-row')).to_have_count(2)
            assert not errors,errors
            browser.close()
        print('PASS: correlated failure inspector, graph links, effective/requested routes, keyboard evidence tabs, response availability, safe lazy artifacts, inspected support export, themes/mobile, captured-route checkpoint retry, cancellation, repeated failure and successful resume with draft protection, reload/filter history.')
    finally:
        server.shutdown();server.server_close();worker.join()
        for thread in list(server.workspace._ai_threads):thread.join(timeout=15)


if __name__=='__main__':main()
