"""Date-scoped imports and one-shot alias edits, with synthetic local data only."""

import json
import threading
import time
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from playwright.sync_api import expect, sync_playwright

from support import init_repo, set_theme
from vita_tree.server import VitaTreeServer


def main():
    artifacts = Path('.test-artifacts/jobenu-ux')
    artifacts.mkdir(parents=True, exist_ok=True)
    root = init_repo((artifacts / ('fixture-' + str(time.time_ns()))).resolve())
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    applications = [
        dict(id='today-a', company='North Robotics', position='Robotics Engineer', createdAt=today + 'T00:30:00+14:00'),
        dict(id='today-b', company='Signal Research', position='Research Engineer', createdAt=today),
        dict(id='older', company='Cedar Systems', position='Systems Engineer', createdAt=yesterday, updatedAt=today),
        dict(id='undated', company='Harbor Labs', position='Lab Engineer', createdAt='invalid'),
        dict(id='duplicate', company='Field Robotics', position='Robotics Engineer', createdAt=today),
    ]
    export = dict(applications=[dict(description='Synthetic role description', status='SAVED', **a) for a in applications])
    server = VitaTreeServer(('127.0.0.1', 0), root, 'main.tex', log_dir=root / '.git/test-logs')
    manager = server.workspace.jobenu
    previews = []

    def invoke(command, env, args, **kwargs):
        if '--help' in args:
            return 0, b'--json --plan-id --approve-plan', b''
        assert '--dry-run' in args, 'This test must never start AI work'
        # Use the same filtered export file that is passed to Vita CV.
        source = Path(args[2])
        selected = json.loads(source.read_text(encoding='utf-8'))['applications']
        previews.append([a['id'] for a in selected])
        config = root / '.vita/extensions.json'
        aliases = json.loads(config.read_text(encoding='utf-8')).get('role_aliases', {}) if config.exists() else {}
        return 0, json.dumps(dict(schema_version=1, status='planned', plan_id='plan-' + str(len(previews)), entries=[
            dict(company=a['company'], position=a['position'], branch='application-' + a['id'], action='create',
                 role_resolution='alias' if a['position'] in aliases else 'slug_fallback') for a in selected
        ])).encode(), b''

    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with patch.object(manager, 'command', return_value=(['fixture'], {})), patch.object(manager, 'invoke', side_effect=invoke), sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport=dict(width=1440, height=1000))
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            session_requests, capability_requests = [], []
            page.route('**/api/session', lambda route: session_requests.append(route), times=1)
            page.on('request', lambda request: capability_requests.append(request) if '/api/jobenu/capability' in request.url else None)
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.locator('#open-jobenu').click()
            page.locator('#jobenu-file').set_input_files(dict(name='synthetic-dated-jobs.json', mimeType='application/json', buffer=json.dumps(export).encode()))
            assert session_requests and not capability_requests, 'Import must wait for the initial session token'
            session_requests[0].continue_()
            expect(page.locator('#jobenu-selection tbody tr')).to_have_count(5)
            page.locator('#jobenu-base').fill('master')
            page.locator('#jobenu-preview').click()
            expect(page.locator('#jobenu-start')).to_be_enabled()
            for width in (1440, 768, 390):
                page.set_viewport_size(dict(width=width, height=1000))
                before = artifacts / f'before-{width}.png'
                if not before.exists():
                    page.screenshot(path=str(before), full_page=True)
            page.get_by_role('button', name='Today', exact=True).click()
            expect(page.locator('#jobenu-selection tbody tr')).to_have_count(3)
            expect(page.locator('#jobenu-start')).to_be_disabled()
            expect(page.locator('#jobenu-selection-summary')).to_contain_text('3 selected')
            page.locator('#jobenu-preview').click()
            expect(page.locator('#jobenu-aliases input')).to_have_count(2)
            assert previews[-1] == ['today-a', 'today-b', 'duplicate'], previews
            inputs = page.locator('#jobenu-aliases input')
            inputs.nth(0).fill('robotics')
            inputs.nth(1).fill('research')
            assert len(previews) == 2, 'Typing must not trigger previews'
            save = page.get_by_role('button', name='Save aliases & update preview', exact=True)
            page.route('**/api/jobenu/aliases', lambda route: route.fulfill(status=400, json={'error': 'Synthetic write failure'}), times=1)
            save.click()
            expect(page.locator('#jobenu-alias-error')).to_contain_text('Synthetic write failure')
            expect(inputs.nth(0)).to_have_value('robotics')
            expect(inputs.nth(1)).to_have_value('research')
            expect(page.locator('#jobenu-start')).to_be_disabled()
            assert len(previews) == 2
            for theme in ('light', 'dark'):
                set_theme(page, theme)
                for width in (1440, 768, 390):
                    page.set_viewport_size(dict(width=width, height=1000))
                    page.evaluate('scrollTo(0,0)')
                    page.screenshot(path=str(artifacts / f'aliases-{theme}-{width}.png'), full_page=True)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                snapshot = page.evaluate("""() => {
                    const doc = document.documentElement.cloneNode(true);
                    // Scope static inspection to the visible import screen. The skill's
                    // title probe otherwise selects the first h1 in an inactive screen.
                    doc.querySelectorAll('#board[hidden],#workspace[hidden]').forEach(e => e.remove());
                    doc.querySelectorAll('script,link[rel=modulepreload]').forEach(e => e.remove());
                    doc.querySelectorAll('link[href]').forEach(e => { const path=new URL(e.getAttribute('href'),location.href).pathname; e.setAttribute('href','../../src/vita_tree/static'+path); });
                    document.querySelectorAll('#jobenu-import input').forEach((source, i) => {
                        const target=doc.querySelectorAll('#jobenu-import input')[i];
                        if(source.type !== 'file') target.setAttribute('value',source.value);
                        if(source.checked) target.setAttribute('checked',''); else target.removeAttribute('checked');
                    });
                    return '<!doctype html>'+doc.outerHTML;
                }""")
                (artifacts / f'inspect-{theme}.html').write_text(snapshot, encoding='utf-8')
            save.focus()
            page.keyboard.press('Enter')
            expect(page.locator('#jobenu-aliases input')).to_have_count(0)
            expect(page.locator('#jobenu-feedback')).to_contain_text('2 role aliases saved')
            expect(page.locator('#jobenu-start')).to_be_enabled()
            assert len(previews) == 3
            aliases = json.loads((root / '.vita/extensions.json').read_text())['role_aliases']
            assert aliases == {'Robotics Engineer': 'robotics', 'Research Engineer': 'research'}
            page.get_by_role('button', name='All dates', exact=True).click()
            expect(page.locator('#jobenu-selection tbody tr')).to_have_count(5)
            page.locator('#jobenu-date-field').select_option('updatedAt')
            page.get_by_role('button', name='Today', exact=True).click()
            expect(page.locator('#jobenu-selection tbody tr')).to_have_count(1)
            expect(page.locator('#jobenu-selection')).to_contain_text('Cedar Systems')
            page.locator('#jobenu-date-from').fill('2000-01-01')
            page.locator('#jobenu-date-to').fill('2000-01-01')
            expect(page.locator('#jobenu-selection-summary')).to_contain_text('No jobs match')
            expect(page.locator('#jobenu-preview')).to_be_disabled()
            page.locator('#jobenu-date-to').fill('1999-01-01')
            expect(page.locator('#jobenu-date-error')).to_contain_text('end date')
            page.get_by_role('button', name='All dates', exact=True).click()
            expect(page.locator('#jobenu-selection tbody tr')).to_have_count(5)
            page.locator('#jobenu-select-all').uncheck()
            expect(page.locator('#jobenu-preview')).to_be_disabled()
            page.locator('#jobenu-select-all').check()
            expect(page.locator('#jobenu-preview')).to_be_enabled()
            page.route('**/__fixture_axe.js', lambda route: route.fulfill(path=str(Path('node_modules/axe-core/axe.min.js').resolve()), content_type='application/javascript'))
            page.add_script_tag(url='/__fixture_axe.js')
            violations = page.evaluate("async()=> (await axe.run('#jobenu-import',{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))")
            assert not violations, violations
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join(5)
    print('PASS: date filters, local Today, missing dates, visible selection, batch aliases, deduplication, failure preservation, keyboard, themes and responsive screenshots.')


if __name__ == '__main__':
    main()
