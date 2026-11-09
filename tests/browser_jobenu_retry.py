"""Failed-only and individual native batch retries, without real providers."""

import json
import threading
import time
from pathlib import Path
from unittest.mock import patch

from playwright.sync_api import expect, sync_playwright

from support import git, init_repo, set_theme
from vita_tree.fileio import atomic_write_bytes
from vita_tree.server import VitaTreeServer


def main():
    artifacts = Path('.test-artifacts/jobenu-retry')
    artifacts.mkdir(parents=True, exist_ok=True)
    root = init_repo((artifacts / ('fixture-' + str(time.time_ns()))).resolve())
    server = VitaTreeServer(('127.0.0.1', 0), root, 'main.tex', log_dir=root / '.git/test-logs')
    manager = server.workspace.jobenu
    applications = [dict(id=str(i), company=company, position='Research Engineer', description='Synthetic job', status='SAVED')
                    for i, company in enumerate(['North Robotics', 'Signal Research', 'Cedar Systems', 'Harbor Labs'])]
    uploaded = manager.upload('synthetic-retries.json', json.dumps(dict(applications=applications)))
    states = [dict(application_id=a['id'], company=a['company'], position=a['position'], key='k'+a['id'],
                   fingerprint='f'+a['id'], branch='app-'+a['id'], action='existing',
                   status='failed' if i<2 else 'awaiting_approval' if i==2 else 'complete',
                   current_step='adapt', completed_steps=['extract','analyze']) for i,a in enumerate(applications)]
    states[2]['pending'] = dict(step='adapt', revision='fixture-review')
    for state in states:
        git(root, 'branch', state['branch'])
    plan = dict(schema_version=1, plan_id='original-plan', base_commit=git(root,'rev-parse','master'),
                routing_sha256='fixture-routing', preferences_sha256='fixture-preferences', entries=states)
    record = manager.record(uploaded['id'])
    record.update(status='failed', startedAt=100, finishedAt=110, attempt=1, plan=plan,
                  options=dict(id=record['id'], ids=[a['id'] for a in applications], base='master', run=True,
                               approval='human', source='', provider='', language='', statuses=['SAVED']),
                  capturedRoutes={'adapt': {'provider':'codex', 'model':'fixture-model'}}, result=dict(results=states))
    manager.save(record)
    original = json.loads(json.dumps(record))
    calls = []
    release = threading.Event()

    def publish():
        index = dict(applications={row['key']: dict(versions={row['fingerprint']:row}) for row in states})
        atomic_write_bytes(root / '.vita/imports/jobenu/index.json', json.dumps(index).encode())

    publish()

    def invoke(command, env, args, **kwargs):
        if '--help' in args:
            return 0, b'--json --plan-id --approve-plan', b''
        assert args[:2] == ['import','jobenu'], args
        source = json.loads(Path(args[2]).read_text(encoding='utf-8'))
        ids = [a['id'] for a in source['applications']]
        selected = [row for row in states if row['application_id'] in ids]
        assert '--rerun' not in args
        if '--dry-run' in args:
            return 0, json.dumps({**plan, 'status':'planned', 'entries':selected, 'plan_id':'retry-'+''.join(ids)}).encode(), b''
        calls.append(ids)
        assert env['ADAPT_MODEL'] == 'fixture-model'
        for row in selected:
            row['status'] = 'running'
        publish()
        assert release.wait(30), 'The browser did not release its synthetic provider'
        for row in selected:
            row['status'] = 'failed' if len(calls)==1 and row['application_id']=='0' else 'complete'
        publish()
        failed = any(row['status']=='failed' for row in selected)
        return (1 if failed else 0), json.dumps(dict(schema_version=1, status='failed' if failed else 'complete', results=selected)).encode(), b''

    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with patch.object(manager,'command',return_value=(['fixture'],{})), patch.object(manager,'invoke',side_effect=invoke), sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport=dict(width=1440,height=1000))
            errors = []
            page.on('pageerror',lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.locator('#open-jobenu').click()
            expect(page.locator('#jobenu-history')).to_contain_text('North Robotics')
            for width in (1440,768,390):
                page.set_viewport_size(dict(width=width,height=1000))
                before = artifacts / f'before-{width}.png'
                if not before.exists():
                    page.screenshot(path=str(before),full_page=True)
            page.get_by_role('button',name='Retry North Robotics',exact=True).click()
            assert page.locator('#jobenu-history .jobenu-scroll').evaluate('(region)=>region.scrollWidth<=region.clientWidth+1')
            dialog = page.get_by_role('dialog',name='Retry failed jobs',exact=True)
            expect(dialog).to_be_visible()
            expect(dialog.locator('tbody tr')).to_have_count(1)
            expect(dialog).to_contain_text('Tailor CV')
            expect(dialog).to_contain_text('fixture-model')
            page.keyboard.press('Escape')
            expect(dialog).not_to_be_visible()
            expect(page.get_by_role('button',name='Retry North Robotics',exact=True)).to_be_focused()
            assert not calls
            page.get_by_role('button',name='Retry failed jobs',exact=True).click()
            expect(dialog.locator('tbody tr')).to_have_count(2)
            expect(dialog).not_to_contain_text('Cedar Systems')
            expect(dialog).not_to_contain_text('Harbor Labs')
            for theme in ('light','dark'):
                page.keyboard.press('Escape')
                expect(dialog).not_to_be_visible()
                set_theme(page,theme)
                snapshot = page.evaluate("""() => {
                    const doc = document.documentElement.cloneNode(true);
                    doc.querySelectorAll('#board[hidden],#workspace[hidden],script,link[rel=modulepreload]').forEach(e=>e.remove());
                    doc.querySelectorAll('link[href]').forEach(e=>e.setAttribute('href','../../src/vita_tree/static'+new URL(e.getAttribute('href'),location.href).pathname));
                    return '<!doctype html>'+doc.outerHTML;
                }""")
                (artifacts / f'inspect-{theme}.html').write_text(snapshot,encoding='utf-8')
                page.get_by_role('button',name='Retry failed jobs',exact=True).click()
                expect(dialog.locator('tbody tr')).to_have_count(2)
                for width in (1440,768,390):
                    page.set_viewport_size(dict(width=width,height=1000))
                    page.screenshot(path=str(artifacts / f'confirm-{theme}-{width}.png'))
                    expect(page.locator('#jobenu-retry-confirm')).to_be_in_viewport()
                    expect(page.locator('#jobenu-retry-cancel')).to_be_in_viewport()
                    assert dialog.locator('table').evaluate('(table)=>table.scrollWidth<=table.parentElement.clientWidth+1')
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
            page.locator('#jobenu-retry-confirm').focus()
            page.keyboard.press('Enter')
            expect(dialog).not_to_be_visible()
            expect(page.locator('#jobenu-history')).to_contain_text('In progress')
            expect(page.get_by_role('button',name='Retry failed jobs',exact=True)).to_be_disabled()
            release.set()
            expect(page.locator('#jobenu-history')).to_contain_text('1 failed job',timeout=15000)
            page.get_by_role('button',name='Retry North Robotics',exact=True).click()
            expect(dialog.locator('tbody tr')).to_have_count(1)
            page.locator('#jobenu-retry-confirm').click()
            expect(dialog).not_to_be_visible()
            expect(page.locator('#jobenu-history')).to_contain_text('Waiting for review',timeout=15000)
            expect(page.get_by_role('button',name='Retry North Robotics',exact=True)).to_have_count(0)
            expect(page.locator('#jobenu-history .jobenu-batch')).to_have_count(1)
            assert calls == [['0','1'],['0']], calls
            assert manager.record(record['id']) == original
            pending_bridge = []
            page.route('**/assets/frontend-app-*.js',lambda route: pending_bridge.append(route),times=1)
            page.reload()
            page.get_by_role('button',name='Navigation',exact=True).click()
            page.get_by_role('menuitem',name='Import jobs',exact=True).click()
            assert pending_bridge, 'The feature-controller fixture should still be loading'
            pending_bridge[0].continue_()
            expect(page.locator('#jobenu-import')).to_be_visible()
            expect(page.get_by_text('Attempts (3)',exact=True)).to_be_visible()
            page.get_by_text('Attempts (3)',exact=True).click()
            expect(page.locator('#jobenu-history')).to_contain_text('Retry')
            page.route('**/__fixture_axe.js',lambda route: route.fulfill(path=str(Path('node_modules/axe-core/axe.min.js').resolve()),content_type='application/javascript'))
            page.add_script_tag(url='/__fixture_axe.js')
            violations = page.evaluate("async()=> (await axe.run('#jobenu-import',{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))")
            assert not violations, violations
            assert not errors,errors
            browser.close()
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        worker.join(5)
    print('PASS: individual/bulk failed-only retries, cancellation, frozen model, repeated failure, native continuation, parent preservation, attempts after reload, keyboard and responsive themes.')


if __name__ == '__main__':
    main()
