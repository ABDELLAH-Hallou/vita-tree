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
from support import init_repo, git, set_theme


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=('chrome', 'chromium'), default='chromium')
    args = parser.parse_args()
    artifacts = Path('.test-artifacts').resolve()
    root = init_repo(artifacts / ('jobs-ui-' + str(time.time_ns())))
    control = root / '.git/ai-control'; control.mkdir()
    config = root / '.vita'; config.mkdir()
    (config / 'extensions.json').write_text(json.dumps({'llm_providers': {'openai': {'model': 'fixture-model'}}}))
    server = VitaTreeServer(('127.0.0.1', 0), root, 'main.tex', log_dir=root/'.git/test-logs')
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
            page.locator('[data-filter=running]').click()
            expect(page.locator('#branch-list .branch-row')).to_have_count(3)
            expect(page.locator('#filter-running')).to_have_text('3')
            # The UI enters Analyzing before the child writes its startup marker.
            deadline=time.monotonic()+30
            while not all((control/(label+'.started')).exists() for label in ('alpha','beta','gamma')) and time.monotonic()<deadline:
                time.sleep(.04)
            assert all((control/(label+'.started')).exists() for label in ('alpha','beta','gamma')), server.workspace.list_jobs()
            set_theme(page, 'dark')
            expect(page.locator('#theme .theme-moon')).to_be_visible()
            page.screenshot(path=str(artifacts/'ai-runs-dark.png'), full_page=True)
            page.reload()
            page.locator('[data-filter=running]').click()
            expect(page.locator('#filter-running')).to_have_text('3', timeout=30000)
            expect(page.locator('#branch-list .branch-row')).to_have_count(3)
            (control/'beta.release').touch()
            expect(page.locator('#filter-failed')).to_have_text('1', timeout=30000)
            public = page.request.get(f'http://127.0.0.1:{server.server_port}/api/jobs').text()
            for secret in ('private-ui-fixture-value', 'VITA_TEST_SECRET', 'provider-fail', 'main.tex', 'env', 'stdout'):
                assert secret not in public, 'Private run details leaked into the global API'
            expect(page.get_by_role('button', name='Open gamma', exact=True).locator('.branch-run')).to_contain_text('Analyzing', timeout=30000)
            (control/'alpha.release').touch()
            expect(page.locator('#filter-review')).to_have_text('1', timeout=30000)
            page.locator('[data-filter=review]').click()
            page.get_by_role('button', name='Open alpha', exact=True).click()
            expect(page.locator('#current-label')).to_have_text('alpha', timeout=30000)
            expect(page.locator('#ai-panel')).to_be_visible()
            expect(page.locator('#selected-run-files')).to_contain_text('alpha analyze')
            alpha = next(run for run in server.workspace.list_jobs()['runs'] if run['branch']=='alpha')
            assert not alpha['reviewed'], 'Opening a result must not dismiss it'
            before = server.workspace.read('alpha', 'main.tex')
            page.locator('#view-run').click()
            expect(page.locator('#mark-run-reviewed')).to_be_enabled()
            assert not server.workspace.get_job(alpha['id'])['reviewed']
            # Reproduce the real disk-permission error, including the memory/disk rollback.
            with patch('vita_tree.workspace.atomic_write',side_effect=PermissionError(13,'private-persistence-canary','/private/person/file')):
                with page.expect_response(lambda response: response.url.endswith('/api/job-reviewed')) as pending:
                    page.locator('#mark-run-reviewed').click()
                failure=pending.value.json()
                expect(page.locator('#notice')).to_contain_text('Review state could not be saved')
                expect(page.locator('#mark-run-reviewed')).to_have_text('Mark as reviewed')
                expect(page.locator('#mark-run-reviewed')).to_be_enabled()
                assert not server.workspace.get_job(alpha['id'])['reviewed']
                history=server.workspace.root/'job-history'/(alpha['id']+'.json')
                assert not json.loads(history.read_text())['reviewed']
            expect(page.locator('#filter-review')).to_have_text('1')
            page.locator('#workspace [data-open-diagnostics]').click()
            expect(page.locator('#diagnostics-dialog')).to_be_visible()
            page.locator('#diagnostics-search').fill(failure['requestId'])
            expect(page.locator('#diagnostics-events')).to_contain_text('PermissionError')
            expect(page.locator('#diagnostics-events')).to_contain_text('errno 13')
            expect(page.locator('#diagnostics-events')).to_contain_text(alpha['id'])
            assert 'private-persistence-canary' not in page.locator('#diagnostics-dialog').inner_text()
            with page.expect_download() as exported:
                page.locator('#download-diagnostics').click()
            bundle=Path(exported.value.path()).read_text()
            assert 'private-persistence-canary' not in bundle and '/private/person' not in bundle
            assert 'path' not in json.loads(bundle)['logging']
            page.locator('#diagnostics-search').fill('')
            page.screenshot(path=str(artifacts/'activity-errors-dark.png'),full_page=True)
            page.get_by_role('button',name='Close activity and logs').click()
            page.locator('#mark-run-reviewed').click()
            expect(page.locator('#mark-run-reviewed')).to_have_text('Reviewed')
            expect(page.locator('#mark-run-reviewed')).to_be_disabled()
            expect(page.locator('#filter-review')).to_have_text('0')
            assert server.workspace.get_job(alpha['id'])['reviewed']
            assert server.workspace.read('alpha', 'main.tex') == before
            assert 'alpha systems' in before
            (control/'gamma.release').touch()
            expect(page.locator('#filter-review')).to_have_text('1', timeout=30000)
            page.reload()
            expect(page.locator('#mark-run-reviewed')).to_have_text('Reviewed', timeout=15000)
            expect(page.locator('#filter-review')).to_have_text('1')
            page.locator('#back').click()
            page.locator('[data-filter=review]').click()
            expect(page.locator('#branch-list .branch-row')).to_have_count(1)
            expect(page.get_by_role('button', name='Open gamma', exact=True)).to_be_visible()
            expect(page.get_by_role('button', name='Open alpha', exact=True)).to_have_count(0)
            expect(page.locator('#run-notifications')).to_have_count(0)
            set_theme(page, 'light')
            page.screenshot(path=str(artifacts/'review-inbox-light.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Review inbox overflows mobile screen'
            page.screenshot(path=str(artifacts/'review-inbox-mobile.png'), full_page=True)
            page.locator('#show-activity').click()
            expect(page.locator('#metric-failed')).to_have_text('1')
            assert page.locator('#diagnostics-dialog').evaluate('el=>el.scrollWidth<=el.clientWidth'), 'Activity panel overflows mobile'
            page.screenshot(path=str(artifacts/'activity-mobile.png'),full_page=True)
            page.get_by_role('button',name='Close activity and logs').click()
            page.locator('[data-filter=failed]').click()
            page.get_by_role('button', name='Open beta', exact=True).click()
            page.locator('#view-run').click()
            expect(page.locator('#current-label')).to_have_text('beta', timeout=30000)
            expect(page.locator('#selected-run-info')).to_contain_text('Failed')
            expect(page.locator('#filter-review')).to_have_text('1')
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
        print('PASS: independent concurrent processes without a queue, global status, sidebar review inbox, real permission failure rollback, diagnostic correlation and export, acknowledgement and retry, persisted review state, navigation, refresh, clean worktree release, dark/light/mobile UI.')
    finally:
        for label in ('alpha', 'beta', 'gamma'):
            (control / (label + '.release')).touch()
        server.shutdown(); server.server_close(); thread.join()
        for worker in list(server.workspace._ai_threads):
            worker.join(timeout=15)


if __name__ == '__main__':
    main()
