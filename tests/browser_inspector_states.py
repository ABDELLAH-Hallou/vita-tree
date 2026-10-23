"""Failure/capture compatibility matrix in the real UI; no provider calls."""
import argparse
import json
from pathlib import Path
import sys
import threading
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from playwright.sync_api import sync_playwright,expect
from vita_tree.server import VitaTreeServer
from diagnostic_fixtures import seed_run
from support import init_repo,set_theme


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=('chrome','chromium'),default='chromium')
    args=parser.parse_args();expect.set_options(timeout=30000)
    artifacts=Path('.test-artifacts').resolve()
    root=init_repo(artifacts/('inspector-states-'+str(time.time_ns())))
    server=VitaTreeServer(('127.0.0.1',0),root,'main.tex',log_dir=root/'.git/test-logs')
    cases=[]
    for category in ('authentication','overloaded','rate_limit','invalid_model','timeout','invalid_json','validation_error'):
        record=seed_run(server.workspace,category)
        cases.append((record,category,'available'))
    for phase in ('staging','pdf','publication'):
        record=seed_run(server.workspace,phase=phase,backend=False)
        cases.append((record,phase,'limited'))
    old=seed_run(server.workspace,backend=False);cases.append((old,None,'limited'))
    future=seed_run(server.workspace)
    manifest=server.workspace.inspector.path(future['traceId'],'manifest.json')
    value=json.loads(manifest.read_text());value['schema_version']=2;manifest.write_text(json.dumps(value))
    cases.append((future,None,'unavailable'))
    error_body=seed_run(server.workspace,'authentication',capture='redacted',artifact_kind='provider_error')
    cases.append((error_body,'authentication','available'))
    expired=seed_run(server.workspace,backend=False)
    expired['stepConfig']['analyze']['connection']='e'*32
    server.workspace._persist_job(expired)
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    errors=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome' if args.browser=='chrome' else None)
            page=browser.new_page(viewport={'width':1440,'height':1000})
            page.on('pageerror',lambda error:errors.append(str(error)))
            url=f'http://127.0.0.1:{server.server_port}'
            page.goto(url);page.locator('#show-activity').click()
            expect(page.locator('#execution-list .execution-row')).to_have_count(len(cases)+1)
            for record,expected,state in cases:
                page.locator('[data-run="'+record['id']+'"]').click()
                expect(page.locator('#execution-reference')).to_contain_text(record['traceId'])
                page.get_by_role('tab',name='Overview',exact=True).click()
                if expected:
                    expect(page.locator('#inspector-panel-overview')).to_contain_text(expected.replace('_',' '))
                expect(page.locator('#execution-contract')).to_contain_text('diagnostics v1' if state=='available' else 'did not record diagnostics' if state=='limited' else 'unsupported contract')
                page.get_by_role('tab',name='Error',exact=True).click()
                if expected:
                    panel=page.locator('#inspector-panel-error')
                    panel.locator('summary').first.click()
                    expect(panel).to_contain_text('PermissionError' if expected in {'staging','pdf','publication'} else expected)
                    if expected=='validation_error':expect(panel).to_contain_text('$.criteria[0].status')
                page.get_by_role('tab',name='Response',exact=True).click()
                if expected=='timeout':expect(page.locator('#inspector-panel-response')).to_contain_text('whether content exists is unknown')
                if record['id']==error_body['id']:expect(page.locator('#inspector-panel-response')).to_contain_text('Provider error response')
                assert 'private-filesystem-canary' not in page.locator('#execution-inspector').inner_text()
            # HTTP routes reject path-like IDs instead of serving arbitrary files.
            rejected=page.request.get(url+'/api/execution-artifact?id='+old['id']+'&artifact=../../private-canary')
            assert rejected.status==400 and 'private-canary' not in rejected.text()
            page.get_by_role('tab',name='Overview',exact=True).click()
            page.locator('#execution-detail-title').scroll_into_view_if_needed()
            page.screenshot(path=str(artifacts/'inspector-failure-overview.png'))
            page.keyboard.press('Escape');expect(page.locator('#diagnostics-dialog')).to_be_hidden()
            expect(page.locator('#show-activity')).to_be_focused()
            # A stale session handle cannot hide the explicit repair choice or
            # start generation without a verified plan.
            page.locator('#show-activity').click()
            page.locator('[data-run="'+expired['id']+'"]').click()
            page.locator('#execution-retry').click()
            expect(page.locator('#resume-dialog')).to_be_visible()
            expect(page.locator('#resume-error')).to_contain_text('connection')
            expect(page.locator('#resume-current-config')).to_be_visible()
            expect(page.locator('#confirm-resume')).to_be_disabled()
            page.locator('#resume-dialog .close-dialog').filter(has_text='Cancel').click()
            assert len(server.workspace.jobs)==len(cases)+1
            set_theme(page,'light')
            assert not errors,errors
            browser.close()
        print('PASS: UI authentication/401, overload/503, rate-limit/429, invalid model, timeout with unknown response, malformed JSON, validation locations, Tree staging/PDF/publication errors, old and unsupported backends, provider-error body distinction, traversal rejection, keyboard focus restoration, no browser errors or live calls.')
    finally:
        server.shutdown();server.server_close();worker.join()


if __name__=='__main__':main()
