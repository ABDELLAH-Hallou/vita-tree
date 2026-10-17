"""UI coverage for concurrent AI processes; all providers are local fixtures."""
import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from playwright.sync_api import sync_playwright, expect
from vita_tree.server import VitaTreeServer
from support import init_repo, git


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=('chrome', 'chromium'), default='chromium')
    args = parser.parse_args()
    artifacts = Path('.test-artifacts').resolve()
    root = init_repo(artifacts / ('jobs-ui-' + str(time.time_ns())))
    control = root / '.git/ai-control'; control.mkdir()
    config = root / '.vita'; config.mkdir()
    (config / 'extensions.json').write_text(json.dumps({'llm_providers': {'openai': {'model': 'fixture-model'}}}))
    server = VitaTreeServer(('127.0.0.1', 0), root, 'main.tex')
    server.workspace.vita_source = None
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    command = [sys.executable, str(Path(__file__).with_name('fake_ai_process.py').resolve())]
    errors = []
    try:
        with patch.object(server.workspace, 'vita_command', return_value=command), patch.dict(os.environ, {'VITA_TEST_CONTROL': str(control), 'VITA_TEST_SECRET': 'private-ui-fixture-value'}), sync_playwright() as p:
            browser = p.chromium.launch(**({'channel': 'chrome'} if args.browser == 'chrome' else {}))
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            expect(page.get_by_role('button', name='Open master', exact=True)).to_be_visible(timeout=30000)
            for label, mode in (('alpha', 'success'), ('beta', 'provider-fail'), ('gamma', 'success')):
                page.locator('#new-branch').click()
                page.locator('#base-branch').select_option('master')
                page.locator('#branch-name').fill(label)
                page.locator('#new-job').fill(json.dumps({'label': label, 'mode': mode}))
                page.locator('#create-form button[type=submit]').click()
                expect(page.locator('#current-label')).to_have_text(label, timeout=30000)
                page.get_by_role('tab', name='Job & AI', exact=False).click()
                page.locator('#provider').select_option('openai')
                page.locator('#model').select_option('fixture-model')
                page.locator('#run-adapt').click()
                expect(page.locator('#job-description')).to_have_attribute('readonly', '')
                page.locator('#back').click()
                expect(page.get_by_role('button', name='Open '+label, exact=True).locator('.branch-run')).to_contain_text('Analyzing', timeout=30000)
            page.locator('#show-runs').click()
            expect(page.locator('#runs-list .run-card')).to_have_count(3)
            expect(page.locator('#runs-summary')).to_contain_text('3 running')
            assert (control/'alpha.started').exists() and (control/'beta.started').exists()
            assert (control/'gamma.started').exists()
            page.locator('#theme').select_option('dark')
            expect(page.locator('.run-footer button').first).to_have_css('background-color', 'rgb(28, 40, 53)')
            page.screenshot(path=str(artifacts/'ai-runs-dark.png'), full_page=True)
            page.reload()
            page.locator('#show-runs').click()
            expect(page.locator('#runs-summary')).to_contain_text('3 running', timeout=30000)
            (control/'beta.release').touch()
            expect(page.locator('#run-notifications')).to_contain_text('Failed: beta', timeout=30000)
            public = page.request.get(f'http://127.0.0.1:{server.server_port}/api/jobs').text()
            for secret in ('private-ui-fixture-value', 'VITA_TEST_SECRET', 'provider-fail', 'main.tex', 'env', 'stdout'):
                assert secret not in public, 'Private run details leaked into the global API'
            expect(page.get_by_role('button', name='Open gamma', exact=True).locator('.branch-run')).to_contain_text('Analyzing', timeout=30000)
            (control/'alpha.release').touch()
            expect(page.locator('#run-notifications')).to_contain_text('Completed: alpha', timeout=30000)
            page.locator('#run-notifications').get_by_role('button', name='Completed: alpha — Review', exact=True).click()
            expect(page.locator('#current-label')).to_have_text('alpha', timeout=30000)
            expect(page.locator('#ai-panel')).to_be_visible()
            expect(page.locator('#selected-run-files')).to_contain_text('alpha analyze')
            expect(page.locator('#run-notifications')).not_to_contain_text('Completed: alpha', timeout=15000)
            expect(page.locator('#run-notifications')).to_contain_text('Failed: beta')
            assert 'alpha systems' in server.workspace.read('alpha', 'main.tex')
            (control/'gamma.release').touch()
            expect(page.locator('#run-notifications')).to_contain_text('Completed: gamma', timeout=30000)
            page.reload()
            expect(page.locator('#run-notifications')).to_contain_text('Failed: beta', timeout=15000)
            expect(page.locator('#run-notifications')).not_to_contain_text('Completed: alpha')
            page.locator('#show-runs').click()
            page.locator('#theme').select_option('light')
            page.screenshot(path=str(artifacts/'ai-runs-light.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Runs view overflows mobile screen'
            page.screenshot(path=str(artifacts/'ai-runs-mobile.png'), full_page=True)
            page.locator('#run-notifications').get_by_role('button', name='Failed: beta — Review', exact=True).click()
            expect(page.locator('#current-label')).to_have_text('beta', timeout=30000)
            expect(page.locator('#selected-run-info')).to_contain_text('Failed')
            expect(page.locator('#run-notifications')).to_contain_text('Completed: gamma')
            # Commit the fixture locally, then leaving releases only this clean worktree.
            location = server.workspace.location('beta')
            git(location, 'add', 'job.md', 'main.tex'); git(location, 'commit', '-m', 'Saved fixture')
            page.locator('#back').click()
            expect(page.locator('#toast')).to_contain_text('Clean worktree released', timeout=30000)
            assert not location.exists()
            git(root, 'checkout', 'beta')  # No longer blocked by Vita Tree's worktree.
            git(root, 'checkout', 'master')
            # Unsaved AI results on other branches must remain on disk.
            assert server.workspace.location('alpha').is_dir()
            assert not errors, errors
            browser.close()
        print('PASS: independent concurrent processes without a queue, global status, navigation, notifications, review, refresh, clean worktree release, dark/light/mobile UI.')
    finally:
        for label in ('alpha', 'beta', 'gamma'):
            (control / (label + '.release')).touch()
        server.shutdown(); server.server_close(); thread.join()
        for worker in list(server.workspace._ai_threads):
            worker.join(timeout=15)


if __name__ == '__main__':
    main()
