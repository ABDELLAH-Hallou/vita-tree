"""Production migration contract: real local UI, synthetic CVs, no AI calls."""
import sys
import threading
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from playwright.sync_api import sync_playwright, expect
expect.set_options(timeout=30000)
from support import init_repo, set_theme
from vita_tree.server import VitaTreeServer

def main():
    repo=init_repo(ROOT/'.test-artifacts'/('migration-ui-'+str(time.time_ns())))
    server=VitaTreeServer(('127.0.0.1',0),repo,'main.tex',log_dir=repo/'.git/test-logs')
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch()
            page=browser.new_page(viewport={'width':1440,'height':900})
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            expect(page.locator('#react-root')).to_have_attribute('data-ready','true')
            expect(page.get_by_role('button',name='Open master',exact=True)).to_be_visible()
            page.keyboard.press('Control+k')
            expect(page.get_by_role('dialog',name='Quick actions',exact=True)).to_be_visible()
            page.get_by_role('button',name='New application',exact=True).click()
            expect(page.locator('#create-dialog')).to_be_visible()
            page.keyboard.press('Escape')
            expect(page.locator('#create-dialog')).not_to_be_visible()
            for theme in ('dark','light'):
                set_theme(page,theme)
                for width in (1440,768,390):
                    page.set_viewport_size({'width':width,'height':900})
                    expect(page.get_by_role('button',name='Open master',exact=True)).to_be_visible()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    page.screenshot(path=str(ROOT/f'.test-artifacts/migration-{theme}-{width}.png'),full_page=True,animations='disabled')
            page.get_by_role('button',name='Open master',exact=True).click()
            expect(page.locator('#workspace')).to_be_visible()
            try:
                expect(page.locator('.dag-node')).to_have_count(6)
            except AssertionError:
                print('Workspace failure:',page.locator('#notice').inner_text(),errors)
                page.screenshot(path=str(ROOT/'.test-artifacts/migration/workspace-failure.png'),full_page=True)
                raise
            page.get_by_role('tab',name='Source · Advanced',exact=True).click()
            expect(page.locator('#current-source .cm-editor')).to_be_visible()
            page.locator('#reload').click()
            expect(page.locator('.dag-node[data-step=adapt]')).to_be_enabled()
            for width in (1440,768,390):
                page.set_viewport_size({'width':width,'height':900})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.screenshot(path=str(ROOT/f'.test-artifacts/migration-workspace-{width}.png'),full_page=True,animations='disabled')
            editor=page.locator('#current-source .cm-content')
            editor.click();page.keyboard.press('Control+End');page.keyboard.insert_text('\n% unsaved migration check')
            expect(page.locator('#save-source')).to_be_enabled()
            page.set_viewport_size({'width':390,'height':740})
            page.get_by_role('button',name='Navigation',exact=True).click()
            page.once('dialog',lambda dialog:dialog.dismiss())
            page.get_by_role('menuitem',name='All applications',exact=True).click()
            expect(page.locator('#workspace')).to_be_visible()
            expect(editor).to_contain_text('% unsaved migration check')
            page.get_by_role('button',name='Navigation',exact=True).click()
            page.once('dialog',lambda dialog:dialog.accept())
            page.get_by_role('menuitem',name='All applications',exact=True).click()
            expect(page.locator('#board')).to_be_visible()
            expect(page.locator('#workspace')).not_to_be_visible()
            page.get_by_role('button',name='Navigation',exact=True).click()
            page.get_by_role('menuitem',name='Import jobs',exact=True).click()
            expect(page.locator('#jobenu-import')).to_be_visible()
            page.get_by_role('button',name='Navigation',exact=True).click()
            page.get_by_role('menuitem',name='All applications',exact=True).click()
            expect(page.locator('#board')).to_be_visible()
            expect(page.locator('#jobenu-import')).not_to_be_visible()
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown();server.server_close();worker.join(5)
    print('PASS: compiled React UI, keyboard actions, existing workflows, editor, themes and responsive viewports')

if __name__=='__main__':main()
