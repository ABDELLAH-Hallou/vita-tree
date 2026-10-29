"""Issue 82: custom language UI and captured command delivery; no live AI."""
import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parent)]
from playwright.sync_api import expect, sync_playwright
from browser_support import BROWSERS, launch_browser
from support import SOURCE, init_repo, set_theme
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest


def write(folder, mapping):
    path=folder/'.vita/extensions.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({'language_map':mapping,'llm_providers':{'codex':{'model':'fixture-model'}}}),encoding='utf-8')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=BROWSERS,default='chromium')
    args=parser.parse_args();expect.set_options(timeout=40000)
    artifacts=Path('.test-artifacts').resolve();root=init_repo(artifacts/('language-ui-'+str(time.time_ns())))
    write(root,{'sv':'Shared Swedish'})
    control=root/'.git/control';control.mkdir()
    source=root/'.git/fake-vita';prompts=source/'vita/assets/prompts';prompts.mkdir(parents=True)
    for step in ('extract','review','cover'):(prompts/(step+'.md')).write_text('Synthetic fixture')
    server=VitaTreeServer(('127.0.0.1',0),root,'main.tex',source,log_dir=root/'.git/test-logs')
    swedish=server.workspace.create('master','swedish',json.dumps({'label':'swedish','pipeline':True,'record_language':True}),digest(SOURCE))
    danish=server.workspace.create('master','danish',json.dumps({'label':'danish','pipeline':True}),digest(SOURCE))
    location=Path(swedish['worktree'])
    mapping={'SV':'Swedish','en':'English override','pt-BR':'Portuguese (Brazil)','zz':'<img src=x onerror=alert(1)>','_comment':'ignore'}
    write(location,mapping);write(Path(danish['worktree']),{'da':'Danish'})
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();errors=[]
    command=[sys.executable,str(Path(__file__).with_name('fake_ai_process.py').resolve())]

    def compile_fixture(folder,entry,engine='auto',output=None):
        output=output or folder/'__vt_output';output.mkdir(parents=True,exist_ok=True)
        pdf=output/(Path(entry).stem+'.pdf');pdf.write_bytes(b'%PDF-1.7\nsynthetic language delivery fixture')
        return dict(pdf=pdf,engine='pdflatex',warnings=[])

    try:
        with patch.object(server.workspace,'vita_command',return_value=command),patch.dict(os.environ,{'VITA_TEST_CONTROL':str(control)}),patch('vita_tree.pdf.compile_document',side_effect=compile_fixture),sync_playwright() as pw:
            browser=launch_browser(pw,args.browser);page=browser.new_page(viewport={'width':1280,'height':900})
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.get_by_role('button',name='Open swedish',exact=True).click()
            page.get_by_role('tab',name='Job details & AI',exact=False).click()
            expect(page.locator('#language option[value=sv]')).to_have_text('Swedish')
            expect(page.locator('#language option[value=en]')).to_have_text('English override')
            expect(page.locator('#language option[value="pt-br"]')).to_have_text('Portuguese (Brazil)')
            expect(page.locator('#language option[value=zz]')).to_have_text(mapping['zz'])
            assert page.locator('#language img').count()==0
            assert page.locator('#language option[value="_comment"]').count()==0
            # Real keyboard selection via the native language combobox.
            page.locator('#language').focus();page.keyboard.press('End');page.keyboard.press('ArrowUp');page.keyboard.press('ArrowUp')
            # Default built-ins retain their order; custom SV follows them.
            expect(page.locator('#language')).to_have_value('sv')
            page.locator('#reload').click();expect(page.locator('#language')).to_have_value('sv')
            page.locator('#back').click();page.get_by_role('button',name='Open danish',exact=True).click()
            expect(page.locator('#language option[value=sv]')).to_have_count(0)
            expect(page.locator('#language option[value=da]')).to_have_text('Danish')
            page.locator('#language').select_option('fr')
            page.locator('#back').click();page.get_by_role('button',name='Open swedish',exact=True).click()
            expect(page.locator('#language')).to_have_value('sv')
            # A changed mapping refreshes labels. Removing a selected mapping
            # retains the code instead of silently selecting English.
            write(location,{'sv':'Svenska'})
            page.locator('#reload').click();expect(page.locator('#language option[value=sv]')).to_have_text('Svenska')
            write(location,{})
            page.locator('#reload').click();expect(page.locator('#language')).to_have_value('sv')
            write(location,{'sv':'Swedish'})
            page.reload();expect(page.locator('#language option[value=sv]')).to_have_text('Swedish')
            page.locator('#language').select_option('sv')
            page.locator('#language').scroll_into_view_if_needed()
            page.screenshot(path=str(artifacts/'language-map-light.png'))
            set_theme(page,'dark');page.locator('#language').scroll_into_view_if_needed();page.screenshot(path=str(artifacts/'language-map-dark.png'))
            page.set_viewport_size({'width':390,'height':844})
            page.locator('#language').scroll_into_view_if_needed()
            assert page.locator('#language').evaluate('el=>el.getBoundingClientRect().right<=innerWidth')
            page.screenshot(path=str(artifacts/'language-map-narrow.png'))
            page.set_viewport_size({'width':1280,'height':900})
            for step in ('extract','analyze','adapt','review','cover'):page.locator('#step-'+step).set_checked(step in ('adapt','cover'))
            (control/'swedish.cover.fail').touch()
            page.locator('#run-adapt').click();expect(page.locator('#language')).to_be_disabled()
            (control/'swedish.release').touch()
            expect(page.locator('.dag-node[data-step=cover]')).to_have_attribute('data-status','failed',timeout=90000)
            for step in ('adapt','cover'):
                assert (control/f'swedish.{step}.language').read_text()=='sv'
                assert json.loads((control/f'swedish.{step}.languages.json').read_text())=={'sv':'Swedish'}
            # Retry retains the captured Swedish choice even if the next-run
            # dropdown draft has changed to English.
            page.locator('#language').select_option('en')
            (control/'swedish.cover.fail').unlink()
            page.locator('#resume-run').click()
            expect(page.locator('#resume-summary')).to_contain_text('Swedish')
            expect(page.locator('#resume-reuse')).to_contain_text('Tailor CV')
            page.locator('#confirm-resume').click()
            expect(page.locator('.dag-node[data-step=validating]')).to_have_attribute('data-status','succeeded',timeout=90000)
            runs=server.workspace.list_jobs()['runs']
            assert runs[0]['language']=='sv' and runs[0]['attempt']==2
            assert (control/'swedish.cover.language').read_text()=='sv'
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown();server.server_close();worker.join(timeout=5)
    print('PASS: branch-scoped language maps, built-ins/overrides, safe labels, reload/switch retention, keyboard selection, Swedish Adapt/Cover delivery and captured retry; both themes/narrow; no live AI.')


if __name__=='__main__':main()
