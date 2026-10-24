"""Real browser/TeX coverage for file-specific Structure and Source editing."""
import argparse
from pathlib import Path
import threading
import time
from urllib.parse import parse_qs, urlsplit

import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader
from support import init_repo, git, set_theme
from test_includes import MAIN, EXPERIENCE, EDUCATION, DETAILS
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browser',choices=('chrome','chromium'),default='chromium');args=parser.parse_args()
    artifacts=ROOT/'.test-artifacts';root=init_repo(artifacts/('includes-ui-'+str(time.time_ns())))
    (root/'sections').mkdir()
    for path,value in {'main.tex':MAIN,'sections/experience.tex':EXPERIENCE,'education.tex':EDUCATION,'sections/details.tex':DETAILS}.items():
        (root/path).write_text(value,encoding='utf-8')
    git(root,'add','.');git(root,'commit','-m','Synthetic nested includes')
    server=VitaTreeServer(('127.0.0.1',0),root,'main.tex',None,log_dir=root/'.git/test-logs')
    branch=server.workspace.create('master','application','Synthetic job',digest(MAIN));location=Path(branch['worktree'])
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();errors=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome' if args.browser=='chrome' else None)
            page=browser.new_page(viewport={'width':1440,'height':1050});page.on('pageerror',lambda error:errors.append(str(error)))
            expect.set_options(timeout=45000)
            page.goto(f'http://127.0.0.1:{server.server_port}/?branch=application')
            expect(page.locator('#cv-file option')).to_have_count(4)
            page.locator('#cv-file').select_option('sections/experience.tex')
            expect(page.locator('#current-document')).to_contain_text('Identical employer')
            expect(page.locator('#file-help')).to_contain_text('without executing macros')
            page.locator('#current-document [data-leaf]').filter(has_text='Identical employer').dblclick()
            expect(page.locator('#edit-origin')).to_contain_text('sections/experience.tex')
            page.locator('#edit-text').fill('Updated & verified employer.\n')
            page.locator('#edit-form button[type=submit]').click()
            expect(page.locator('#edit-dialog')).not_to_be_visible()
            expect(page.locator('#current-document')).to_contain_text('Updated & verified employer')
            assert (location/'education.tex').read_text()==EDUCATION
            assert (location/'main.tex').read_text()==MAIN
            assert r'Updated \& verified employer.' in (location/'sections/experience.tex').read_text()
            page.locator('#cv-file').select_option('sections/details.tex')
            page.get_by_role('tab',name='Source · Advanced',exact=True).click()
            editor=page.get_by_role('textbox',name='Current CV source',exact=True)
            editor.fill('Edited nested achievement.\n')
            # Cancelling file navigation retains the unsaved text and selection.
            page.once('dialog',lambda dialog:dialog.dismiss())
            page.locator('#cv-file').select_option('education.tex')
            expect(page.locator('#cv-file')).to_have_value('sections/details.tex')
            expect(editor).to_contain_text('Edited nested achievement')
            page.get_by_role('button',name='Save draft',exact=True).click()
            expect(page.locator('#save-state')).not_to_have_text('Unsaved changes')
            assert (location/'sections/details.tex').read_text()=='Edited nested achievement.\n'
            page.get_by_role('tab',name='Changes',exact=False).click()
            expect(page.locator('#diff')).to_contain_text('+Edited nested achievement')
            page.get_by_role('tab',name='Edit CV',exact=True).click()
            page.locator('#current-document [data-leaf]').filter(has_text='Edited nested achievement').dblclick()
            (location/'education.tex').write_text(EDUCATION+'\n% concurrent edit',encoding='utf-8')
            page.locator('#edit-text').fill('Must remain pending')
            page.locator('#edit-form button[type=submit]').click()
            expect(page.locator('#edit-error')).to_contain_text('include dependencies changed')
            assert (location/'sections/details.tex').read_text()=='Edited nested achievement.\n'
            page.keyboard.press('Escape');page.locator('#reload').click()
            expect(page.locator('#notice')).not_to_contain_text('Loading the application')
            set_theme(page,'light');page.screenshot(path=str(artifacts/'includes-light.png'),full_page=True)
            set_theme(page,'dark');page.screenshot(path=str(artifacts/'includes-dark.png'),full_page=True)
            page.get_by_role('tab',name='PDF preview',exact=True).click()
            expect(page.locator('#file-navigation')).not_to_be_visible()
            page.get_by_role('button',name='Create PDF previews',exact=True).click()
            expect(page.locator('#current-pdf .textLayer').first).to_be_visible(timeout=180000)
            expect(page.locator('#compile')).to_be_enabled(timeout=180000)
            pdf_id=parse_qs(urlsplit(page.locator('#current-pdf .pdf-download').get_attribute('href')).query)['id'][0]
            pdf=server.compiler.results[pdf_id]
            text='\n'.join(item.extract_text() for item in PdfReader(pdf).pages)
            assert 'Edited nested achievement' in text and 'Updated & verified employer' in text,text
            assert 'Education' in text and 'Root text' in text,text
            assert len(PdfReader(pdf).pages)==1
            page.screenshot(path=str(artifacts/'includes-pdf.png'),full_page=True)
            # Unlike input, include writes a nested auxiliary file and adds
            # page boundaries. Exercise the real engine, including Linux CI.
            (location/'main.tex').write_text(MAIN.replace(r'\input{sections/experience}',r'\include{sections/experience}'),encoding='utf-8')
            page.locator('#reload').click()
            expect(page.locator('#notice')).not_to_contain_text('Loading the application')
            page.get_by_role('button',name='Create PDF previews',exact=True).click()
            expect(page.locator('#current-pdf .textLayer')).to_have_count(3,timeout=180000)
            expect(page.locator('#compile')).to_be_enabled(timeout=180000)
            pdf_id=parse_qs(urlsplit(page.locator('#current-pdf .pdf-download').get_attribute('href')).query)['id'][0]
            included=PdfReader(server.compiler.results[pdf_id])
            assert len(included.pages)==3
            assert 'Edited nested achievement' in '\n'.join(item.extract_text() for item in included.pages)
            page.get_by_role('tab',name='Edit CV',exact=True).click()
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(artifacts/'includes-mobile.png'),full_page=True)
            (location/'main.tex').write_text(MAIN.replace(r'\input{sections/experience}',''),encoding='utf-8')
            page.locator('#reload').click()
            expect(page.locator('#cv-file option:checked')).to_contain_text('unavailable')
            page.get_by_role('tab',name='Source · Advanced',exact=True).click()
            expect(page.locator('#version-label')).to_have_text('View only')
            expect(page.get_by_role('textbox',name='Current CV source',exact=True)).to_have_attribute('aria-readonly','true')
            assert not errors,errors
            browser.close()
        print('PASS: nested file selection, mapped edits, duplicate text isolation, Source drafts, cancelled navigation, concurrent dependency conflict, per-file diff, light/dark/mobile layout and selectable real PDF.')
    finally:
        server.shutdown();server.server_close();thread.join()


if __name__=='__main__':main()
