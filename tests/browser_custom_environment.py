"""Issue #37: open, edit, validate and preview a real custom-environment CV."""
import argparse
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader
from vita_tree.server import VitaTreeServer
from support import CUSTOM_ENVIRONMENT_SOURCE, git, init_repo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=('chrome', 'chromium'), default='chromium')
    args = parser.parse_args()
    expect.set_options(timeout=30000)
    artifacts = Path('.test-artifacts').resolve()
    root = init_repo(artifacts / ('custom-environment-' + str(time.time_ns())))
    (root / 'main.tex').write_text(CUSTOM_ENVIRONMENT_SOURCE, encoding='utf-8')
    git(root, 'add', 'main.tex')
    git(root, 'commit', '-m', 'Custom environment fixture')
    server = VitaTreeServer(('127.0.0.1', 0), root, 'main.tex', log_dir=root/'.git/test-logs')
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    errors = []
    try:
        with patch.object(server.workspace, 'vita_command', return_value=None), sync_playwright() as pw:
            browser = pw.chromium.launch(channel='chrome' if args.browser == 'chrome' else None)
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.get_by_role('button', name='Open master', exact=True).click()
            expect(page.locator('#current-document')).to_contain_text('Sample experience.')
            expect(page.locator('#notice')).to_contain_text('Use PDF preview to check the final layout')
            expect(page.locator('#message-details')).to_contain_text('approximate layout')
            assert not page.locator('#notice').evaluate("el => el.classList.contains('error')")
            page.locator('#current-document [data-leaf]').filter(has_text='Sample experience.').dblclick()
            page.locator('#edit-text').fill('Reviewed experience.')
            page.locator('#edit-form').get_by_role('button', name='Save draft', exact=True).click()
            expect(page.locator('#current-document')).to_contain_text('Reviewed experience.')
            expected = CUSTOM_ENVIRONMENT_SOURCE.replace('Sample experience.', 'Reviewed experience.')
            assert (root/'main.tex').read_text(encoding='utf-8') == expected
            page.locator('.dag-node[data-step=validating]').click()
            page.locator('#task-run').click()
            expect(page.locator('.dag-node[data-step=validating]')).to_have_attribute('data-status', 'succeeded')
            assert (root/'main.tex').read_text(encoding='utf-8') == expected
            page.get_by_role('tab', name='PDF preview', exact=True).click()
            page.get_by_role('button', name='Create PDF previews', exact=True).click()
            expect(page.locator('#current-pdf .textLayer')).to_have_count(1, timeout=180000)
            expect(page.locator('#original-pdf .textLayer')).to_have_count(1, timeout=180000)
            expect(page.locator('#current-pdf .textLayer')).to_contain_text('Reviewed experience.')
            expect(page.locator('#original-pdf .textLayer')).to_contain_text('Sample experience.')
            assert not errors, errors
            for path in server.compiler.results.values():
                pdf = PdfReader(path)
                assert len(pdf.pages) == 1
                assert 'experience.' in pdf.pages[0].extract_text()
            page.screenshot(path=str(artifacts/'custom-environment-pdf.png'), full_page=True)
            browser.close()
        print('PASS: custom environment opens, source-map edit preserves definition, validation-only succeeds without AI, original/current PDFs compile and have selectable text; no browser errors.')
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
        for thread in list(server.workspace._ai_threads):
            thread.join(timeout=15)


if __name__ == '__main__':
    main()
