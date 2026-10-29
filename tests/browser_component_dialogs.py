"""Issue 44: reachable actions without covering scrollable settings. No AI calls."""
import argparse
from pathlib import Path
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from browser_support import BROWSERS, launch_browser, tab_to as keyboard_tab_to
from playwright.sync_api import expect, sync_playwright
from vita_tree.server import VitaTreeServer
from support import init_repo, set_theme


def reachable(page, selector):
    """Visibility alone does not exclude clipping or an overlapping footer."""
    expect(page.locator(selector)).to_be_visible()
    # Focus/constraint-validation scrolling can complete at the next paint.
    page.wait_for_function('''selector=>{const el=document.querySelector(selector);if(!el)return false;
      const r=el.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
      return r.left>=0&&r.top>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1&&!!hit&&(el===hit||el.contains(hit));}''',arg=selector,timeout=5000)
    result = page.locator(selector).evaluate("""el => {
      const r=el.getBoundingClientRect(), hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
      return {inside:r.left>=0 && r.top>=0 && r.right<=innerWidth+1 && r.bottom<=innerHeight+1,
              hit:!!hit && (el===hit || el.contains(hit))};
    }""")
    assert result == {'inside': True, 'hit': True}, (selector, result)


def layout(page, dialog, actions):
    for action in actions:
        reachable(page, action)
    assert page.locator(dialog).evaluate('(el) => el.scrollWidth <= el.clientWidth'), 'Horizontal dialog overflow'
    assert page.locator(dialog).evaluate("""el => {
      const body=el.querySelector('.ai-dialog-body').getBoundingClientRect();
      const footer=el.querySelector('.ai-dialog-footer').getBoundingClientRect();
      return body.height>40 && body.bottom<=footer.top+1;
    }"""), 'Footer obscures the scroll area'


def tab_to(page, selector):
    return keyboard_tab_to(page, selector, reachable)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=BROWSERS, default='chromium')
    args = parser.parse_args()
    expect.set_options(timeout=15000)
    artifacts = Path('.test-artifacts').resolve()
    root = init_repo(artifacts / ('component-dialogs-' + str(time.time_ns())))
    server = VitaTreeServer(('127.0.0.1', 0), root, 'main.tex', log_dir=root/'.git/test-logs')
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    errors = []
    cases = [('desktop', 1280, 800, 1), ('narrow-tall', 390, 844, 1),
             ('short', 390, 480, 1), ('narrow-short', 320, 400, 1),
             ('zoom-200', 1280, 720, 2)]
    try:
        with sync_playwright() as p:
            browser = launch_browser(p,args.browser)
            page = browser.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.get_by_role('button', name='Open master', exact=True).click()
            for theme in ('light', 'dark'):
                for name, width, height, zoom in cases:
                    print('Component case:', args.browser, theme, name, flush=True)
                    page.evaluate('document.documentElement.style.zoom=""')
                    page.set_viewport_size({'width': width, 'height': height})
                    set_theme(page, theme)
                    # CSS zoom also exercises enlarged controls; narrow cases
                    # separately cover the reduced layout viewport at browser zoom.
                    page.evaluate('(zoom) => document.documentElement.style.zoom=zoom', str(zoom))
                    page.locator('.dag-node[data-step=extract]').click()
                    page.locator('#step-ai-custom').check()
                    page.locator('#popup-provider').select_option('openai')
                    page.locator('#popup-model').fill('fixture-dialog-model')
                    body = page.locator('#step-ai-dialog .ai-dialog-body')
                    body.evaluate('(el) => el.scrollTop=0')
                    layout(page, '#step-ai-dialog', ['#step-ai-cancel', '#step-ai-apply'])
                    page.screenshot(path=str(artifacts/f'component-{theme}-{name}.png'))
                    # Native scrolling keys differ; Firefox's form controls can
                    # consume wheel events, while WebKit handles wheel scrolling.
                    bounds = body.bounding_box()
                    page.mouse.move(bounds['x']+4,bounds['y']+bounds['height']/2)
                    if args.browser=='firefox':
                        page.locator('#close-step-ai').focus();page.keyboard.press('ControlOrMeta+End')
                    else:
                        page.mouse.wheel(0,2500)
                    expect(page.locator('#step-ai-save-hint')).to_be_in_viewport()
                    page.locator('#step-ai-save-hint').scroll_into_view_if_needed()
                    reachable(page, '#step-ai-save-hint')
                    layout(page, '#step-ai-dialog', ['#step-ai-cancel', '#step-ai-apply'])
                    if args.browser=='firefox':page.keyboard.press('ControlOrMeta+Home')
                    else:page.mouse.wheel(0,-2500)
                    expect(page.locator('#step-ai-title')).to_be_in_viewport(ratio=1)
                    page.locator('#popup-model').fill('invalid model id')
                    page.locator('#step-ai-apply').click()
                    expect(page.locator('#step-ai-error')).to_contain_text('without spaces')
                    reachable(page, '#step-ai-error')
                    layout(page, '#step-ai-dialog', ['#step-ai-cancel', '#step-ai-apply'])
                    page.screenshot(path=str(artifacts/f'component-error-{theme}-{name}.png'))
                    page.locator('#popup-model').fill('fixture-dialog-model')
                    # Tab moves the actual focus, not just programmatic focus.
                    tab_to(page, '#step-ai-apply')
                    page.keyboard.press('Shift+Tab')
                    expect(page.locator('#step-ai-cancel')).to_be_focused()
                    reachable(page, '#step-ai-cancel')
                    page.locator('#step-ai-fields [data-add-key]').click()
                    expect(page.locator('#connection-dialog')).to_be_visible()
                    layout(page, '#connection-dialog', ['#cancel-connection', '#add-connection'])
                    page.locator('#connection-name').fill('Cancelled fixture')
                    page.locator('#connection-key').fill('synthetic-dialog-key')
                    page.keyboard.press('Escape')
                    expect(page.locator('#connection-dialog')).not_to_be_visible()
                    expect(page.locator('#step-ai-dialog')).to_be_visible()
                    expect(page.locator('#popup-model')).to_have_value('fixture-dialog-model')
                    assert page.locator('#step-ai-dialog').evaluate('el=>el.contains(document.activeElement)'), 'Focus left parent settings'
                    page.locator('#step-ai-fields [data-add-key]').click()
                    expect(page.locator('#connection-key')).to_be_empty()
                    # Native required-field validation scrolls the focused input
                    # into the body rather than behind the fixed action area.
                    page.locator('#add-connection').click()
                    expect(page.locator('#connection-key')).to_be_focused()
                    reachable(page, '#connection-key')
                    page.screenshot(path=str(artifacts/f'component-connection-{theme}-{name}.png'))
                    page.locator('#cancel-connection').click()
                    expect(page.locator('#popup-model')).to_have_value('fixture-dialog-model')
                    page.locator('#step-ai-cancel').click()
                    expect(page.locator('.dag-node[data-step=extract]')).to_be_focused()
                    page.keyboard.press('Enter')
                    expect(page.locator('#step-ai-shared')).to_be_checked()
                    page.keyboard.press('Escape')

            # Nested server validation, successful key addition, and actual Apply
            # persistence. No external API requests or generation are made.
            page.evaluate('document.documentElement.style.zoom=""')
            page.set_viewport_size({'width': 390, 'height': 480})
            page.locator('.dag-node[data-step=extract]').click()
            page.locator('#step-ai-custom').check()
            page.locator('#popup-provider').select_option('openai')
            page.locator('#popup-model').fill('persisted-dialog-model')
            page.locator('#step-ai-fields [data-add-key]').click()
            page.locator('#connection-name').fill('Fixture account')
            page.locator('#connection-key').fill('synthetic-dialog-key')
            page.route('**/api/connections', lambda route: route.fulfill(
                status=400, json={'error': 'Fixture validation: choose another connection name.'}), times=1)
            page.locator('#add-connection').click()
            expect(page.locator('#connection-error')).to_contain_text('Fixture validation')
            reachable(page, '#connection-error')
            layout(page, '#connection-dialog', ['#cancel-connection', '#add-connection'])
            page.screenshot(path=str(artifacts/'component-connection-error-dark-short.png'))
            page.locator('#add-connection').click()
            expect(page.locator('#connection-dialog')).not_to_be_visible()
            expect(page.locator('#popup-model')).to_have_value('persisted-dialog-model')
            expect(page.locator('#popup-connection option:checked')).to_have_text('Fixture account')
            page.locator('#step-ai-fields [data-check-generation]').click()
            layout(page, '#generation-check-dialog', ['#cancel-generation-check', '#confirm-generation-check'])
            page.screenshot(path=str(artifacts/'component-generation-dark-short.png'))
            page.keyboard.press('Escape')
            expect(page.locator('#popup-model')).to_have_value('persisted-dialog-model')
            page.route('**/api/ai-settings', lambda route: route.fulfill(
                status=400, json={'error': 'Fixture validation: setup could not be saved. Try again.'}), times=1)
            page.locator('#step-ai-apply').click()
            expect(page.locator('#step-ai-error')).to_contain_text('setup could not be saved')
            reachable(page, '#step-ai-error')
            expect(page.locator('#step-ai-apply')).to_be_enabled()
            expect(page.locator('#popup-model')).to_have_value('persisted-dialog-model')
            page.screenshot(path=str(artifacts/'component-apply-error-dark-short.png'))
            print('After save error:',page.evaluate('''()=>({focused:document.activeElement.id||document.activeElement.tagName,
              hasFocus:document.hasFocus(),dialogs:[...document.querySelectorAll('dialog[open]')].map(el=>el.id)})'''),flush=True)
            tab_to(page, '#step-ai-apply')
            page.keyboard.press('Enter')
            expect(page.locator('#step-ai-dialog')).not_to_be_visible()
            page.reload()
            page.locator('.dag-node[data-step=extract]').click()
            expect(page.locator('#popup-model')).to_have_value('persisted-dialog-model')
            expect(page.locator('#popup-connection option:checked')).to_have_text('Fixture account')
            # Escape and Cancel discard changes, including the inheritance mode.
            page.locator('#step-ai-shared').check()
            page.keyboard.press('Escape')
            page.locator('.dag-node[data-step=extract]').click()
            expect(page.locator('#step-ai-custom')).to_be_checked()
            page.locator('#popup-model').fill('discard-this')
            page.locator('#step-ai-cancel').click()
            page.locator('.dag-node[data-step=extract]').click()
            expect(page.locator('#popup-model')).to_have_value('persisted-dialog-model')
            page.locator('#step-ai-shared').check()
            page.locator('#step-ai-apply').click()
            page.locator('.dag-node[data-step=extract]').click()
            expect(page.locator('#step-ai-shared')).to_be_checked()
            expect(page.locator('#popup-model')).to_be_disabled()
            page.locator('#step-ai-cancel').click()
            page.get_by_role('tab', name='Job details & AI', exact=False).click()
            page.locator('#model').fill('shared-dialog-model')
            page.locator('#model').press('Tab')
            page.locator('.dag-node[data-step=extract]').click()
            expect(page.locator('#popup-model')).to_have_value('shared-dialog-model')
            page.keyboard.press('Escape')
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
    print('PASS: both themes, narrow/tall/short viewports, 200% CSS zoom, visible actions and errors, scrolling, keyboard focus, nested connection validation, Apply persistence, Cancel/Escape and shared inheritance; no AI calls.')


if __name__ == '__main__':
    main()
