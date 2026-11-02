"""Focused import routing and backup controls with synthetic processes only."""
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

from playwright.sync_api import expect, sync_playwright

from support import SOURCE, git, init_repo, set_theme
from vita_tree.server import VitaTreeServer


def main():
    expect.set_options(timeout=30000)
    artifacts = Path('.test-artifacts/jobenu-routing').resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    root = init_repo(artifacts / ('fixture-' + str(time.time_ns())))
    source = root / '.git/fake-vita'
    prompts = source / 'vita/assets/prompts'
    prompts.mkdir(parents=True)
    for step in ('extract', 'review', 'cover'):
        (prompts / (step + '.md')).write_text('Synthetic task')
    (source / 'vita/helpers').mkdir()
    (source / 'vita/helpers/llm.py').write_text('# Synthetic bridge')
    location = root / '.vita/imports/jobenu/worktrees/synthetic'
    location.parent.mkdir(parents=True)
    git(root, 'worktree', 'add', '-b', 'imported-application', str(location), 'master')
    (location / 'job.md').write_text(json.dumps({'label': 'routing', 'pipeline': True}))
    (location / '.vita').mkdir(exist_ok=True)
    (location / '.vita/.env').write_text('ANALYSIS_PROVIDER=codex\nANALYSIS_MODEL=fixture-old\n')
    control = root / '.git/control'
    control.mkdir()
    (control / 'routing.release').touch()
    (control / 'routing.analyze.expected-ai.json').write_text(json.dumps({
        'provider': 'openai', 'model': 'fixture-new', 'key': 'synthetic-primary-key'}))
    (control / 'routing.analyze.expected-backup.json').write_text(json.dumps({
        'provider': 'gemini', 'model': 'fixture-backup', 'key': 'synthetic-backup-key'}))
    server = VitaTreeServer(('127.0.0.1', 0), root, 'main.tex', source, log_dir=root / '.git/test-logs')
    ws = server.workspace
    ws._fallback_capabilities = {'version': 'provider-fallback/1',
                                'default_categories': ['timeout'],
                                'allowed_categories': ['timeout', 'invalid_model']}
    manager = ws.jobenu
    exported = json.dumps({'applications': [{'id': 'one', 'company': 'North Robotics',
                                            'position': 'Research Engineer', 'description': 'Synthetic role', 'status': 'SAVED'}]})
    for _ in range(2):
        manager.upload('synthetic-unused.json', exported)
    record = manager.record(manager.upload('synthetic-active.json', exported)['id'])
    row = {'key': 'k', 'fingerprint': 'f', 'branch': 'imported-application', 'workspace': str(location),
           'company': 'North Robotics', 'position': 'Research Engineer', 'status': 'failed',
           'current_step': 'analyze', 'completed_steps': []}
    record.update(status='failed', startedAt=time.time(), finishedAt=time.time(),
                  result={'results': [row]}, capturedRoutes={'analyze': {'provider': 'codex', 'model': 'fixture-old'}})
    manager.save(record)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    command = [sys.executable, str(Path(__file__).with_name('fake_ai_process.py').resolve())]
    try:
        with patch.object(ws, 'vita_command', return_value=command), patch.dict(os.environ, {'VITA_TEST_CONTROL': str(control)}), sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.locator('#open-jobenu').click()
            expect(page.locator('#jobenu-history')).to_contain_text('North Robotics')
            expect(page.locator('#jobenu-history')).not_to_contain_text('synthetic-unused')
            page.get_by_role('button', name='Open workspace', exact=True).click()
            expect(page.locator('#workspace')).to_be_visible()
            expect(page.locator('#workspace')).not_to_have_attribute('aria-busy', 'true')
            expect(page.locator('#workflow-next')).to_have_text('Start selected steps')
            expect(page.locator('.dag-node[data-step=analyze] .dag-model')).to_have_text('fixture-old')
            page.get_by_role('tab', name='Job details & AI', exact=False).click()
            page.locator('#provider').select_option('openai')
            page.locator('#model').fill('fixture-new')
            page.locator('#model').press('Tab')
            page.locator('#shared-ai-fields > .ai-route-fields > .connection-actions [data-add-key]').click()
            page.locator('#connection-name').fill('Primary account')
            page.locator('#connection-key').fill('synthetic-primary-key')
            page.locator('#add-connection').click()
            backup = page.locator('#shared-ai-fields > .ai-route-fields > .ai-backup')
            backup.get_by_role('checkbox', name='Use a backup if this AI fails', exact=True).check()
            page.locator('#backup-provider').select_option('gemini')
            page.locator('#backup-model').fill('fixture-backup')
            page.locator('#backup-model').press('Tab')
            backup.locator('[data-add-key]').click()
            page.locator('#connection-name').fill('Backup account')
            page.locator('#connection-key').fill('synthetic-backup-key')
            page.locator('#add-connection').click()
            page.locator('#save-ai-setup').click()
            expect(page.locator('#ai-setup-status')).to_contain_text('Setup saved')
            page.reload()
            expect(page.locator('#workspace')).to_be_visible()
            expect(page.locator('#workspace')).not_to_have_attribute('aria-busy', 'true')
            page.get_by_role('tab', name='Job details & AI', exact=False).click()
            expect(page.locator('#backup-model')).to_have_value('fixture-backup')
            expect(page.locator('#model')).to_have_value('fixture-new')
            for theme in ('light', 'dark'):
                set_theme(page, theme)
                snapshot = page.evaluate("""() => {
                    const doc = document.documentElement.cloneNode(true);
                    const originals = document.querySelectorAll('input,select,textarea');
                    doc.querySelectorAll('input,select,textarea').forEach((el,index)=>{
                        const current=originals[index];
                        if(el.tagName==='SELECT')Array.from(el.options).forEach((option,i)=>option.toggleAttribute('selected',current.options[i].selected));
                        else if(el.tagName==='TEXTAREA')el.textContent=current.value;
                        else if(!['file','password'].includes(el.type)){
                            el.setAttribute('value',current.value);el.toggleAttribute('checked',current.checked);
                        }
                    });
                    doc.querySelectorAll('#board[hidden],script,link[rel=modulepreload]').forEach(el=>el.remove());
                    doc.querySelectorAll('link[href]').forEach(el=>el.setAttribute('href','../../src/vita_tree/static'+new URL(el.getAttribute('href'),location.href).pathname));
                    return '<!doctype html>'+doc.outerHTML;
                }""")
                (artifacts / f'inspect-{theme}.html').write_text(snapshot, encoding='utf-8')
                for width in (1440, 768, 390):
                    page.set_viewport_size({'width': width, 'height': 1000})
                    page.locator('#shared-ai-fields > .ai-route-fields > .ai-backup').evaluate("el => el.scrollIntoView({block:'start'})")
                    page.screenshot(path=str(artifacts / f'backup-{theme}-{width}.png'))
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            page.set_viewport_size({'width': 1440, 'height': 1000})
            # Starting this component creates a new captured run, not a native batch replay.
            page.locator('.dag-node[data-step=analyze]').click()
            page.keyboard.press('Escape')
            page.locator('#task-run').click()
            expect(page.locator('.dag-node[data-step=analyze]')).to_have_attribute('data-status', 'succeeded', timeout=30000)
            assert (control / 'routing.analyze.verified-ai').is_file()
            assert (control / 'routing.analyze.verified-backup').is_file()
            expect(page.locator('.dag-node[data-step=analyze] .dag-model')).to_have_text('fixture-backup · Backup')
            assert manager.record(record['id'])['capturedRoutes']['analyze']['model'] == 'fixture-old'
            jobs = page.request.get(f'http://127.0.0.1:{server.server_port}/api/jobs').text()
            assert 'synthetic-primary-key' not in jobs and 'synthetic-backup-key' not in jobs
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
    print('PASS: unused previews hidden; imported workspace runs the newly selected primary and native backup settings; both themes and three widths; no real providers.')


if __name__ == '__main__':
    main()
