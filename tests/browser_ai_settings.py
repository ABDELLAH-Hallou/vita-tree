"""AI setup UX and mixed-provider execution; all AI calls use local fixtures."""
import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from browser_support import BROWSERS, launch_browser
from playwright.sync_api import sync_playwright, expect
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest
from support import init_repo, SOURCE, set_theme


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--browser', choices=BROWSERS, default='chromium')
    args=parser.parse_args()
    expect.set_options(timeout=30000)
    artifacts = Path('.test-artifacts').resolve()
    root = init_repo(artifacts / ('ai-settings-' + str(time.time_ns())))
    control = root / '.git/control'; control.mkdir()
    source = root / '.git/fake-vita'
    prompts = source/'vita/assets/prompts'; prompts.mkdir(parents=True)
    for step in ('extract', 'review', 'cover'):
        (prompts/(step+'.md')).write_text('Fixture task')
    helpers=source/'vita/helpers';helpers.mkdir()
    (helpers/'llm.py').write_text('# Reasoning bridge fixture')
    server = VitaTreeServer(('127.0.0.1', 0), root, 'main.tex', source, log_dir=root/'.git/test-logs')
    server.workspace.create('master', 'custom-ai', json.dumps({'label': 'custom-ai', 'pipeline': True, 'extraction': True}), digest(SOURCE))
    (control/'custom-ai.release').touch()
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    command = [sys.executable, str(Path(__file__).with_name('fake_ai_process.py').resolve())]
    errors=[]
    try:
        with patch.object(server.workspace, 'vita_command', return_value=command), patch('vita_tree.providers.codex_efforts', return_value={'fixture-codex':['low','medium','high']}), patch.dict(os.environ, {'VITA_TEST_CONTROL': str(control)}), sync_playwright() as p:
            browser=launch_browser(p,args.browser)
            page=browser.new_page(viewport={'width': 1512, 'height': 1100})
            def page_error(error):
                errors.append(str(error))
                print('Browser error:', error)
            page.on('pageerror', page_error)
            url=f'http://127.0.0.1:{server.server_port}'
            page.goto(url)
            page.get_by_role('button', name='Open custom-ai', exact=True).click()
            page.get_by_role('tab', name='Job details & AI', exact=False).click()
            expect(page.locator('#provider option')).to_have_count(13)
            page.locator('#provider').select_option('openai')
            page.locator('#model').fill('my-custom-writing-model')
            expect(page.locator('#reasoning')).to_be_disabled()
            page.locator('#shared-ai-fields [data-add-key]').click()
            page.locator('#connection-name').fill('Personal API account')
            page.locator('#connection-key').fill('fixture-private-api-key')
            page.locator('#add-connection').click()
            expect(page.locator('#connection-dialog')).not_to_be_visible()
            expect(page.locator('#connection option:checked')).to_have_text('Personal API account')
            # Open per-step configuration directly from a workflow component.
            page.locator('.dag-node[data-step=review]').click()
            expect(page.locator('#step-ai-dialog')).to_be_visible()
            expect(page.locator('#step-ai-title')).to_have_text('Review CV with AI')
            expect(page.locator('#step-ai-shared')).to_be_checked()
            expect(page.locator('#popup-model')).to_be_disabled()
            page.locator('#step-ai-custom').check()
            page.locator('#popup-provider').select_option('codex')
            page.locator('#popup-model').fill('fixture-codex');page.locator('#popup-model').press('Tab')
            page.locator('#popup-reasoning').select_option('high')
            expect(page.locator('#popup-reasoning')).to_have_value('high')
            expect(page.locator('#popup-connection option:checked')).to_have_text('Local Codex login')
            page.locator('#step-ai-apply').click()
            expect(page.locator('#step-ai-dialog')).not_to_be_visible()
            expect(page.locator('[data-ai-summary=review]')).to_contain_text('High')
            expect(page.locator('.dag-node[data-step=review] .dag-model')).to_have_text('fixture-codex')
            # Cancel and Escape discard a local edit, and invalid IDs stay in the dialog.
            page.locator('.dag-node[data-step=review]').click()
            page.locator('#popup-model').fill('cancelled-model')
            page.locator('#step-ai-cancel').click()
            expect(page.locator('.dag-node[data-step=review] .dag-model')).to_have_text('fixture-codex')
            page.locator('.dag-node[data-step=review]').click()
            page.locator('#popup-model').fill('invalid model id')
            page.locator('#step-ai-apply').click()
            expect(page.locator('#step-ai-error')).to_contain_text('without spaces')
            page.keyboard.press('Escape')
            page.locator('.dag-node[data-step=review]').focus();page.keyboard.press('Enter')
            expect(page.locator('#popup-model')).to_have_value('fixture-codex')
            page.locator('#step-ai-shared').check()
            page.locator('#step-ai-apply').click()
            expect(page.locator('#step-ai-dialog')).not_to_be_visible()
            expect(page.locator('#override-count')).to_have_text('All use shared setup')
            # Configure extraction from the CV tab, where the inline AI panel is hidden.
            page.get_by_role('tab', name='Edit CV', exact=True).click()
            page.locator('.dag-node[data-step=extract]').click()
            expect(page.locator('#step-ai-dialog')).to_be_visible()
            page.locator('#step-ai-custom').check()
            page.locator('#popup-provider').select_option('gemini')
            page.locator('#popup-model').fill('my-custom-fast-model')
            page.locator('#step-ai-fields [data-add-key]').click()
            page.locator('#connection-name').fill('Job requirements account')
            page.locator('#connection-key').fill('fixture-private-gemini-key')
            page.locator('#add-connection').click()
            expect(page.locator('#connection-dialog')).not_to_be_visible()
            expect(page.locator('#step-ai-dialog')).to_be_visible()
            expect(page.locator('#popup-model')).to_have_value('my-custom-fast-model')
            page.screenshot(path=str(artifacts/'step-ai-popup-light.png'))
            page.locator('#step-ai-apply').click()
            expect(page.locator('#step-ai-dialog')).not_to_be_visible()
            set_theme(page, 'dark')
            page.locator('.dag-node[data-step=extract]').click()
            page.screenshot(path=str(artifacts/'step-ai-popup-dark.png'))
            page.set_viewport_size({'width':390,'height':844})
            assert page.locator('#step-ai-dialog').evaluate('(el) => el.scrollWidth <= el.clientWidth'), 'Popup overflows on mobile'
            page.screenshot(path=str(artifacts/'step-ai-popup-mobile.png'))
            page.set_viewport_size({'width':1512,'height':1100})
            page.locator('#step-ai-apply').click()
            expect(page.locator('#step-ai-dialog')).not_to_be_visible()
            expect(page.locator('.dag-node[data-step=extract] .dag-model')).to_have_text('my-custom-fast-model')
            expect(page.locator('.dag-node[data-step=adapt] .dag-model')).to_have_text('my-custom-writing-model')
            # Apply saves without requiring a separate trip to Advanced settings.
            page.reload()
            page.locator('.dag-node[data-step=extract]').click()
            expect(page.locator('#popup-model')).to_have_value('my-custom-fast-model')
            expect(page.locator('#popup-connection option:checked')).to_have_text('Job requirements account')
            page.keyboard.press('Escape')
            page.get_by_role('tab', name='Job details & AI', exact=False).click()
            page.locator('#ai-advanced > summary').click()
            extract=page.locator('.ai-step-setting').nth(0)
            extract.locator('summary').click()
            expect(page.locator('#extract-custom-ai')).to_be_checked()
            expect(page.locator('#override-count')).to_have_text('1 custom step')
            # The override survives shared model changes; inherited steps follow them.
            page.locator('#model').fill('my-final-writing-model')
            page.locator('#model').press('Tab')
            expect(page.locator('[data-ai-summary=extract]')).to_contain_text('my-custom-fast-model')
            expect(page.locator('[data-ai-summary=adapt]')).to_contain_text('my-final-writing-model')
            page.locator('#save-ai-setup').click()
            expect(page.locator('#ai-setup-status')).to_contain_text('Setup saved')
            page.reload()
            expect(page.locator('#model')).to_have_value('my-final-writing-model')
            expect(page.locator('#override-count')).to_have_text('1 custom step')
            expect(page.locator('#connection option:checked')).to_have_text('Personal API account')
            page.locator('#ai-advanced > summary').click()
            page.locator('.ai-step-setting').nth(0).locator('summary').click()
            expect(page.locator('#extract-model')).to_have_value('my-custom-fast-model')
            page.locator('#step-extract').check();page.locator('#step-review').uncheck()
            # Capture the real UI in both themes and at a narrow viewport.
            page.locator('#ai-configuration').scroll_into_view_if_needed()
            page.screenshot(path=str(artifacts/'ai-settings-light.png'), full_page=True)
            set_theme(page, 'dark')
            page.screenshot(path=str(artifacts/'ai-settings-dark.png'), full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile page overflows'
            page.screenshot(path=str(artifacts/'ai-settings-mobile.png'), full_page=True)
            page.set_viewport_size({'width':1512,'height':1100})
            for step, provider, model, key in [('extract','gemini','my-custom-fast-model','fixture-private-gemini-key'),
                                              ('analyze','openai','my-final-writing-model','fixture-private-api-key'),
                                              ('adapt','openai','my-final-writing-model','fixture-private-api-key')]:
                (control/f'custom-ai.{step}.expected-ai.json').write_text(json.dumps(dict(provider=provider, model=model, key=key)))
            page.locator('#run-adapt').click()
            expect(page.locator('.dag-node[data-step=adapt]')).to_have_attribute('data-status','succeeded')
            expect(page.locator('.dag-node[data-step=extract] .dag-model')).to_have_text('my-custom-fast-model')
            page.locator('.dag-node[data-step=extract]').click()
            expect(page.locator('#step-ai-context')).to_have_text('Recorded run · view only')
            expect(page.locator('#popup-model')).to_have_value('my-custom-fast-model')
            expect(page.locator('#popup-model')).to_be_disabled()
            expect(page.locator('#step-ai-apply')).to_be_hidden()
            page.locator('#step-ai-next').click()
            expect(page.locator('#popup-model')).to_be_enabled()
            page.locator('#popup-model').fill('not-applied-to-history')
            page.locator('#step-ai-cancel').click()
            expect(page.locator('#task-description')).to_contain_text('my-custom-fast-model')
            expect(page.locator('#task-description')).to_contain_text('Job requirements account')
            # No secret can be fetched back, persisted, or placed in browser storage.
            response=page.request.get(url+'/api/connections').text()
            assert 'fixture-private' not in response
            assert 'fixture-private' not in page.request.get(url+'/api/jobs').text()
            assert 'fixture-private' not in page.evaluate('JSON.stringify(localStorage)')
            unauthorized=page.request.post(url+'/api/connections',data={'name':'Test','provider':'openai','apiKey':'secret'})
            assert unauthorized.status==403
            # Removing a key makes its old references visibly actionable.
            page.locator('#shared-ai-fields [data-remove-key]').click()
            expect(page.locator('#ai-config-validation')).to_contain_text('connection again')
            expect(page.locator('#run-adapt')).to_be_disabled()
            page.locator('#connection').select_option('')
            expect(page.locator('#run-adapt')).to_be_enabled()
            page.locator('#reset-ai-steps').click()
            expect(page.locator('#override-count')).to_have_text('All use shared setup')
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown();server.server_close();worker.join()
    print('PASS: 13 providers, custom model IDs, named session keys, step inheritance and overrides, saved setup, mixed-provider execution, run provenance, secret isolation, CSRF, expired connections, light/dark/mobile layouts, zero browser errors.')


if __name__=='__main__':
    main()
