"""Real Structure editing and all-page long-PDF UI over the synthetic corpus."""
import argparse
import base64
import json
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from playwright.sync_api import expect, sync_playwright
from template_matrix import CORPUS, hashes, load_corpus, make_repository, sha, sources
from vita_tree.server import VitaTreeServer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=('chrome', 'chromium'), default='chromium')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Use a fresh browser evidence directory'
    args.output.mkdir(parents=True)
    expect.set_options(timeout=60000)
    evidence = []
    errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome' if args.browser == 'chrome' else None)
        report = dict(schemaVersion=1, corpusVersion=load_corpus()['corpusVersion'],
                      corpusSha256=sha((CORPUS/'manifest.json').read_bytes()), browserVersion=browser.version,
                      harnessSha256=sha(Path(__file__).read_bytes()),
                      appSha256=sha((ROOT/'src/vita_tree/static/app.js').read_bytes()), results=evidence)
        for fixture in load_corpus()['fixtures']:
            root = make_repository(args.output/fixture['id'], fixture)
            expected = sources(fixture)
            server = VitaTreeServer(('127.0.0.1', 0), root, 'main.tex', None, log_dir=root/'.git/test-logs')
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            # Each fixture is a different local project/server. Dispose its
            # polling page before stopping that server or reusing a port.
            page = browser.new_page(viewport={'width': 1440, 'height': 1050})
            held = []
            pause_refresh = False
            page.route('**/api/workspace?*', lambda route: held.append(route) if pause_refresh else route.continue_())
            page.on('pageerror', lambda error: errors.append(error.stack))
            try:
                page.goto(f'http://127.0.0.1:{server.server_port}/?branch=master')
                expect(page.locator('#branch-title')).to_have_text('master')
                expect(page.locator('#cv-file')).to_be_enabled()
                if fixture['structure']['status'] == 'invalid':
                    expect(page.locator('#current-document')).to_contain_text('Structure cannot preview')
                for change in fixture['edits']:
                    page.locator('#cv-file').select_option(change['path'])
                    document = server.workspace.snapshot('master')
                    file = next(item for item in document['files'] if item['path'] == change['path'])
                    candidates = [(key, leaf) for key, leaf in file['document']['leaves'].items()
                                  if leaf['text'] == change['find']]
                    key, leaf = candidates[change['occurrence']]
                    page.locator(f'#current-document [data-leaf="{key}"]').dblclick()
                    expect(page.locator('#edit-origin')).to_contain_text(change['path'])
                    page.locator('#edit-text').fill(change['replacement'])
                    pause_refresh = fixture['id'] == 'native-environments'
                    page.locator('#edit-form button[type=submit]').click()
                    expect(page.locator('#edit-dialog')).not_to_be_visible()
                    if pause_refresh:
                        # A slow refresh must not leave the old file picker usable
                        # with a null snapshot, even for a queued change event.
                        expect(page.locator('#cv-file')).to_be_disabled()
                        page.locator('#cv-file').dispatch_event('change')
                        page.wait_for_timeout(100)
                        assert len(held) == 1
                        pause_refresh = False
                        held.pop().continue_()
                    expect(page.locator('#cv-file')).to_be_enabled()
                    expect(page.locator('#current-document')).to_contain_text(change['replacement'])
                    source = expected[change['path']]
                    expected[change['path']] = source[:leaf['start']] + change['replacementSource'] + source[leaf['end']:]
                    # Check bytes, including untouched class files and same text in another include.
                    assert {name: (root/name).read_bytes() for name in expected} == {
                        name: value.encode('utf-8') for name, value in expected.items()}
                record = {'id': fixture['id'], 'before': hashes(sources(fixture)), 'after': hashes(expected),
                          'edits': len(fixture['edits']), 'pages': []}
                if fixture['id'] == 'dynamic-include':
                    expect(page.locator('#include-problems')).to_be_visible()
                    page.locator('#include-problems').click()
                    expect(page.locator('#include-diagnostics')).to_contain_text('Computed paths and unbraced inputs need an external editor.')
                image = args.output/(fixture['id']+'-structure.png')
                page.screenshot(path=str(image))
                record['structureImageSha256'] = sha(image.read_bytes())
                if fixture['id'] == 'long-document':
                    page.get_by_role('tab', name='PDF preview', exact=True).click()
                    page.locator('#compile').click()
                    for side in ('original', 'current'):
                        expect(page.locator(f'#{side}-pdf .textLayer')).to_have_count(8, timeout=180000)
                        for number in range(1, 9):
                            layer = page.locator(f'#{side}-pdf .textLayer').nth(number-1)
                            expect(layer).to_contain_text(f'Page{number:02}Start.')
                            expect(layer).to_contain_text(f'Page{number:02}End.')
                            # A screenshot of an overflowing page can contain
                            # unrelated UI outside the scrollport. Capture the
                            # complete PDF.js canvas, then independently prove
                            # that both page ends can be reached in the real UI.
                            path = args.output/f'long-{side}-page-{number}.png'
                            canvas = layer.locator('..').locator('canvas')
                            encoded = canvas.evaluate("node => node.toDataURL('image/png').split(',')[1]")
                            path.write_bytes(base64.b64decode(encoded, validate=True))
                            frames = []
                            for anchor in ('Start', 'End'):
                                marker = layer.get_by_text(f'Page{number:02}{anchor}.', exact=True)
                                marker.scroll_into_view_if_needed()
                                expect(marker).to_be_in_viewport()
                                frame = args.output/f'long-{side}-page-{number}-{anchor.lower()}-viewport.png'
                                page.locator(f'#{side}-pdf').locator('..').screenshot(path=str(frame))
                                frames.append(dict(anchor=anchor, image=frame.name, imageSha256=sha(frame.read_bytes())))
                            record['pages'].append({'side': side, 'number': number, 'image': path.name,
                                                    'imageSha256': sha(path.read_bytes()), 'viewportFrames': frames})
                    expect(page.locator('#current-pdf .textLayer').nth(3)).to_contain_text('ReviewedPage04Row06')
                    expect(page.locator('#original-pdf .textLayer').nth(3)).not_to_contain_text('ReviewedPage04Row06')
                evidence.append(record)
                (args.output/'browser-results.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
                print('PASS: Structure/source-map UI '+fixture['id'], flush=True)
            finally:
                page.close()
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
        assert not errors, errors
        browser.close()


if __name__ == '__main__':
    main()
