"""Guided setup, real restricted TeX diagnostics, and synthetic AI gating."""
import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from playwright.sync_api import sync_playwright,expect
from support import init_repo,SOURCE,set_theme
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest
from vita_tree.pdf import compile_document,CompilationError

LIMITED=r'''\documentclass{article}
\begin{document}
\iffalse { \fi
Synthetic CV with valid conditional TeX.
\end{document}
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=('chrome','chromium'),default='chromium');args=parser.parse_args()
    artifacts=ROOT/'.test-artifacts';root=init_repo(artifacts/('preflight-ui-'+str(time.time_ns())))
    config=root/'.vita';config.mkdir();(config/'extensions.json').write_text(json.dumps({'llm_providers':{'openai':{'model':'fixture-model'}}}))
    backend=root/'.git/fake-vita';(backend/'vita').mkdir(parents=True)
    control=root/'.git/control';control.mkdir()
    server=VitaTreeServer(('127.0.0.1',0),root,'main.tex',backend,log_dir=root/'.git/test-logs')
    for label in ('valid','limited','missing-package','missing-entry','invalid-settings','conflict'):
        branch=server.workspace.create('master',label,json.dumps({'label':label,'pipeline':True}),digest(SOURCE))
        location=Path(branch['worktree']);(control/(label+'.release')).touch()
        if label=='limited':(location/'main.tex').write_text(LIMITED,encoding='utf-8')
        if label=='missing-package':(location/'main.tex').write_text(SOURCE.replace(r'\begin{document}',r'\usepackage{vita-tree-synthetic-missing-42}\begin{document}'),encoding='utf-8')
        if label=='missing-entry':(location/'main.tex').unlink()
        if label=='invalid-settings':
            (location/'.vita').mkdir(exist_ok=True);(location/'.vita/config.json').write_text('{')
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    origin=f'http://127.0.0.1:{server.server_port}';errors=[]
    command=[sys.executable,str(ROOT/'tests/fake_ai_process.py')]
    try:
        with patch.object(server.workspace,'vita_command',return_value=command),patch.dict(os.environ,{'VITA_TEST_CONTROL':str(control)}),sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome' if args.browser=='chrome' else None)
            page=browser.new_page(viewport={'width':1440,'height':1050});page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:d.accept())
            expect.set_options(timeout=45000)
            page.goto(origin);page.locator('.input-guide summary').click()
            expect(page.locator('.input-guide')).to_contain_text('PDF, Word and scanned-CV import are not available')
            page.get_by_role('button',name='Check input & setup',exact=True).click()
            dialog=page.locator('#setup-dialog');expect(dialog).to_be_visible()
            page.locator('#setup-branch').select_option('missing-entry');page.locator('#check-setup').click()
            expect(page.locator('#setup-results')).to_contain_text('entry file is missing')
            assert not (server.workspace.location('missing-entry')/'main.tex').exists()
            page.locator('#setup-branch').select_option('invalid-settings');page.locator('#check-setup').click()
            expect(page.locator('#setup-results')).to_contain_text('Project settings could not be read')
            expect(page.locator('#setup-results')).to_contain_text('config.json')
            page.locator('#setup-branch').select_option('valid')
            with patch('vita_tree.pdf.engine_executable',side_effect=ValueError('synthetic unavailable engine')):
                page.locator('#check-setup').click();expect(page.locator('#setup-results')).to_contain_text('TeX engine is unavailable')
                expect(page.locator('#setup-results')).to_contain_text('Install that engine')
            page.locator('#setup-branch').select_option('missing-package');page.locator('#check-setup').click()
            expect(page.locator('#setup-results')).to_contain_text('vita-tree-synthetic-missing-42.sty')
            expect(page.locator('#setup-results')).to_contain_text('install its package explicitly')
            page.keyboard.press('Escape');page.goto(origin+'/?branch=limited')
            expect(page.locator('#current-document')).to_contain_text('Structure cannot preview this template')
            page.get_by_role('button',name='Check setup',exact=True).click();page.locator('#check-setup').click()
            expect(page.locator('#setup-result-heading')).to_have_text('Ready for the checked steps')
            expect(page.locator('#setup-results')).to_contain_text('Structure is an approximate preview')
            expect(page.locator('#setup-results')).to_contain_text('compiled successfully')
            page.screenshot(path=str(artifacts/'preflight-light.png'),full_page=True)
            page.keyboard.press('Escape');set_theme(page,'dark');page.get_by_role('button',name='Check setup',exact=True).click()
            page.screenshot(path=str(artifacts/'preflight-dark.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(artifacts/'preflight-mobile.png'),full_page=True)
            page.keyboard.press('Escape');page.set_viewport_size({'width':1440,'height':1050})
            # Unsaved editor text must never be labelled as a checked revision.
            page.get_by_role('tab',name='Source · Advanced',exact=True).click();page.locator('#current-source .cm-content').click();page.keyboard.press('Control+End');page.keyboard.press('Enter');page.keyboard.type('% unsaved synthetic draft')
            page.get_by_role('button',name='Check setup',exact=True).click();page.locator('#check-setup').click()
            expect(page.locator('#setup-progress')).to_contain_text('Save your CV and job-description drafts')
            page.keyboard.press('Escape');page.locator('#reload').click()
            expect(page.locator('#save-state')).not_to_have_text('Unsaved changes')
            # A saved draft changed externally during compilation must conflict.
            page.goto(origin+'/?branch=conflict');page.get_by_role('button',name='Check setup',exact=True).click()
            location=server.workspace.location('conflict')
            def edited(folder,entry,**options):
                result=compile_document(folder,entry,**options)
                (location/'main.tex').write_text(SOURCE+'\n% synthetic external change',encoding='utf-8')
                return result
            with patch('vita_tree.pdf.compile_document',side_effect=edited):
                page.locator('#check-setup').click();expect(page.locator('#setup-progress')).to_contain_text('project changed during setup checks')
            assert 'external change' in (location/'main.tex').read_text(encoding='utf-8')
            page.keyboard.press('Escape')
            # Automatic preflight gates model work even without a manual check.
            page.goto(origin+'/?branch=missing-package');page.get_by_role('tab',name='Job details & AI',exact=False).click()
            page.locator('#step-adapt').uncheck();page.locator('#run-adapt').click()
            expect(page.locator('#workflow-summary')).to_contain_text('No AI was called')
            assert not (control/'missing-package.analyze.calls').exists()
            page.goto(origin+'/?branch=limited');page.get_by_role('tab',name='Job details & AI',exact=False).click()
            page.locator('#step-adapt').uncheck();page.locator('#run-adapt').click()
            expect(page.locator('.dag-node[data-step=analyze]')).to_have_attribute('data-status','succeeded')
            expect(page.locator('#setup-summary')).to_contain_text('Setup check passed')
            assert (control/'limited.analyze.calls').exists()
            assert server.workspace.read('limited','main.tex')==LIMITED
            assert page.request.post(origin+'/api/preflight',data={'branch':'valid'}).status==403
            assert not errors,errors
            browser.close()
        print('PASS: truthful input guidance, missing entry/config/engine/package diagnostics, real valid TeX with limited Structure, changed/unsaved drafts, automatic pre-AI gating, independent fake execution, CSRF, themes/mobile, and project preservation; no real providers.')
    finally:
        server.shutdown();server.server_close();worker.join();server.workspace.close()
        for thread in list(server.workspace._ai_threads):thread.join(timeout=15)


if __name__=='__main__':main()
