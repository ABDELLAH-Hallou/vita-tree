"""Real Chromium UI and TeX smoke tests. Run explicitly, outside unit discovery."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from playwright.sync_api import sync_playwright, expect
expect.set_options(timeout=30000)  # Git/provider refreshes can exceed 5s on Windows CI.
from pypdf import PdfReader
from vita_tree.server import VitaTreeServer
from support import init_repo, git


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sample-cv',type=Path)
    parser.add_argument('--browser',choices=('chrome','chromium'),default='chrome')
    args=parser.parse_args()
    artifacts=Path('.test-artifacts').resolve();artifacts.mkdir(exist_ok=True)
    root=artifacts/('ui-'+str(time.time_ns()));init_repo(root)
    remote=root/'.git/browser-remote.git';git(root,'init','--bare',str(remote));git(root,'remote','add','origin',str(remote))
    config=root/'.vita/extensions.json';config.parent.mkdir(exist_ok=True)
    config.write_text(json.dumps({'llm_providers':{'codex':{'model':'test-codex'},'openai':{'model':'gpt-4-turbo'}}}))
    git(root,'add','-f','.vita/extensions.json');git(root,'commit','-m','Provider fixtures')
    git(root,'branch','provider-history')
    config.write_text(json.dumps({'llm_providers':{'codex':{'model':'test-current'}}}))
    fake_vita=root.parent/(root.name+'-cli')
    (fake_vita/'vita').mkdir(parents=True)
    (fake_vita/'vita/__init__.py').write_text('')
    (fake_vita/'vita/helpers').mkdir()
    (fake_vita/'vita/helpers/__init__.py').write_text('')
    (fake_vita/'vita/helpers/llm.py').write_text("def load_env(): return {}\ndef _find_codex_cli(): return 'codex-fixture'\n")
    (fake_vita/'vita/__main__.py').write_text('''import sys,time,json,subprocess
from pathlib import Path
from unittest.mock import patch
from vita.helpers import llm
step=sys.argv[1]
assert sys.argv[sys.argv.index('--provider')+1]=='codex'
model=json.loads(Path('.vita/extensions.json').read_text())['llm_providers']['codex']['model']
assert model=='test-codex'
def run(command,**kwargs):
 assert command[command.index('-c')+1]=='model_reasoning_effort="high"'
 assert command[command.index('--model')+1]=='test-codex'
 Path(command[command.index('--output-last-message')+1]).write_text('controlled CLI fixture with high reasoning')
 return subprocess.CompletedProcess(command,0)
with patch('subprocess.run',side_effect=run):
 report=llm._call_codex_cli('System','Task',model)
time.sleep(1)
results=Path('.vita/results');results.mkdir(parents=True,exist_ok=True)
(results/(step+'.md')).write_text('# '+step+' report from '+report)
if step=='adapt':
 p=Path('main.tex');p.write_text(p.read_text().replace('careful automated tests','rigorous automated tests'))
''')
    model_patch=patch('vita_tree.providers.codex_efforts',return_value={'test-codex':['low','medium','high'],'test-current':['low','medium','high']})
    model_patch.start()
    server=VitaTreeServer(('127.0.0.1',0),root,'main.tex',fake_vita)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    errors=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(**({'channel':'chrome'} if args.browser=='chrome' else {}),headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto('http://127.0.0.1:'+str(server.server_port));expect(page.get_by_role('button',name='Open master',exact=True)).to_be_visible(timeout=30000)
            page.locator('#theme').select_option('dark')
            expect(page.locator('html')).to_have_attribute('data-theme','dark')
            page.reload();expect(page.locator('#theme')).to_have_value('dark')
            expect(page.locator('html')).to_have_attribute('data-theme','dark')
            page.screenshot(path=str(artifacts/'branches-dark.png'),full_page=True)
            page.locator('#theme').select_option('system');page.emulate_media(color_scheme='light')
            expect(page.locator('html')).to_have_attribute('data-theme','light')
            page.emulate_media(color_scheme='dark');expect(page.locator('html')).to_have_attribute('data-theme','dark')
            page.locator('#theme').select_option('light')
            page.screenshot(path=str(artifacts/'branches.png'),full_page=True)
            page.get_by_role('button',name='Open master',exact=True).click()
            expect(page.locator('#current-document')).to_contain_text('reliable systems')
            page.get_by_role('button',name='＋ Branch from this',exact=True).click()
            page.locator('#branch-name').fill('etp-acme-swe');page.locator('#new-job').fill('Acme seeks a software engineer with Python and SQL experience.')
            page.get_by_role('button',name='Create branch',exact=True).click()
            expect(page.locator('#branch-title')).to_have_text('etp-acme-swe',timeout=30000)
            expect(page.locator('#current-label')).to_have_text('etp-acme-swe')
            worktree=server.workspace.location('etp-acme-swe')
            assert (worktree/'job.md').read_text().startswith('Acme')
            assert git(root,'branch','--show-current')=='master'
            page.locator('#current-document [data-leaf]').filter(has_text='reliable systems').dblclick()
            page.locator('#edit-text').fill('safe & reliable systems')
            page.get_by_role('button',name='Save text',exact=True).click()
            expect(page.locator('#current-document')).to_contain_text('safe & reliable systems')
            assert r'safe \& reliable systems' in (worktree/'main.tex').read_text()
            page.get_by_role('tab',name='LaTeX',exact=True).click()
            editor=page.get_by_role('textbox',name='New version LaTeX',exact=True)
            original_editor=page.get_by_role('textbox',name='Original LaTeX',exact=True)
            source=(worktree/'main.tex').read_text()
            expect(editor).to_have_attribute('aria-readonly','false')
            expect(original_editor).to_have_attribute('aria-readonly','true')
            expect(page.locator('#current-source .tex-command').first).to_be_visible()
            expect(page.locator('#current-source .cm-lineNumbers')).to_be_visible()
            expect(page.locator('#current-source .lint-status')).to_have_text('No syntax issues',timeout=15000)
            original_text=original_editor.inner_text()
            original_editor.click();page.keyboard.press('ControlOrMeta+End');page.keyboard.insert_text('DO NOT WRITE')
            assert original_editor.inner_text()==original_text
            editor.fill(source.replace('automated tests','careful automated tests'))
            expect(page.locator('#save-state')).to_have_text('Unsaved edits')
            editor.press('ControlOrMeta+z');expect(page.locator('#save-source')).to_be_disabled()
            editor.press('ControlOrMeta+Shift+z');expect(page.locator('#save-source')).to_be_enabled()
            valid=source.replace('automated tests','careful automated tests')
            editor.fill(valid+'\n% editor comment\n}')
            expect(page.locator('#current-source .lint-status')).to_contain_text('Syntax issue',timeout=15000)
            expect(page.locator('#current-source .cm-lintRange-error')).to_have_count(1)
            page.locator('#current-source .lint-status').click()
            expect(page.locator('#current-source .cm-panel-lint')).to_contain_text('Unexpected')
            page.locator('#theme').select_option('light')
            page.screenshot(path=str(artifacts/'latex-editor-light.png'),full_page=True)
            command_light=page.locator('#current-source .tex-command').first.evaluate('el => getComputedStyle(el).color')
            page.locator('#theme').select_option('dark')
            assert page.locator('#current-source .tex-command').first.evaluate('el => getComputedStyle(el).color')!=command_light
            page.screenshot(path=str(artifacts/'latex-editor-dark.png'),full_page=True)
            page.locator('#theme').select_option('light')
            editor.fill(valid)
            expect(page.locator('#current-source .lint-status')).to_have_text('No syntax issues',timeout=15000)
            expect(page.locator('#current-source .cm-lintRange-error')).to_have_count(0)
            editor.press('ControlOrMeta+f')
            search=page.locator('#current-source .cm-search input[name="search"]')
            search.fill('careful')
            search.press('Enter')
            expect(page.locator('#current-source .cm-searchMatch').first).to_be_visible()
            search.press('Escape')
            editor.press('ControlOrMeta+Home')
            for _ in range(valid.index('{')+1): editor.press('ArrowRight')
            expect(page.locator('#current-source .cm-matchingBracket')).to_have_count(2)
            page.get_by_role('button',name='Save changes',exact=True).click()
            expect(page.locator('#save-state')).to_have_text('Saved locally · uncommitted',timeout=30000)
            expect(editor).to_contain_text('careful automated tests')
            expect(page.locator('#current-label')).to_have_text('etp-acme-swe')
            assert 'careful automated tests' in (worktree/'main.tex').read_text()
            assert git(worktree,'rev-parse','HEAD')==git(root,'rev-parse','master'),'Save changes created a commit'
            page.get_by_role('tab',name='Changes',exact=False).click();expect(page.locator('#diff')).to_contain_text('careful automated tests')
            page.get_by_role('tab',name='Job & AI',exact=False).click()
            expect(page.locator('#job-description')).to_have_value('Acme seeks a software engineer with Python and SQL experience.')
            page.locator('#job-description').fill('Updated job context');page.get_by_role('button',name='Save job.md',exact=True).click();expect(page.locator('#job-state')).to_have_text('Saved as job.md')
            results=worktree/'.vita/results';results.mkdir(parents=True,exist_ok=True)
            (results/'analyze.md').write_text('# Match analysis\nStrong Python and SQL experience.')
            (results/'adapt.md').write_text('# Changes\nRefined the summary.')
            page.get_by_role('button',name='↻ Reload',exact=True).click();expect(page.locator('#artifacts')).to_contain_text('Strong Python and SQL experience.',timeout=30000)
            expect(page.locator('#provider')).to_have_value('codex')
            page.locator('#provider').select_option('openai');expect(page.locator('#reasoning')).to_be_disabled()
            page.locator('#provider').select_option('codex');page.locator('#model').select_option('test-codex')
            page.locator('#reasoning').select_option('high')
            page.screenshot(path=str(artifacts/'ai-light.png'),full_page=True)
            page.locator('#theme').select_option('dark')
            page.screenshot(path=str(artifacts/'ai-dark.png'),full_page=True)
            page.get_by_role('button',name='Analyze & adapt',exact=True).click()
            expect(page.locator('#job-description')).to_have_attribute('readonly','')
            expect(page.locator('#ai-status')).to_contain_text('ready to review',timeout=60000)
            expect(page.locator('#artifacts')).to_contain_text('controlled CLI fixture')
            expect(page.locator('#artifacts')).to_contain_text('high reasoning')
            expect(page.locator('#reasoning')).to_have_value('high')
            assert json.loads(config.read_text())['llm_providers']['codex']['model']=='test-current'
            assert 'rigorous automated tests' in (worktree/'main.tex').read_text()
            page.get_by_role('tab',name='LaTeX',exact=True).click()
            editor.fill((worktree/'main.tex').read_text()+'\n% publish from UI')
            page.get_by_role('tab',name='Job & AI',exact=False).click()
            page.locator('#job-description').fill('Committed job context')
            page.locator('#commit-push').click()
            expect(page.locator('#commit-dialog')).to_be_visible()
            expect(page.locator('#commit-branch')).to_have_text('etp-acme-swe')
            expect(page.locator('#commit-destination')).to_have_text('origin/etp-acme-swe')
            for expected_file in ('main.tex','job.md','.vita/results/analyze.md','.vita/results/adapt.md'):
                expect(page.locator('#commit-files')).to_contain_text(expected_file)
            page.locator('#commit-message').fill('Tailor CV for Acme')
            page.screenshot(path=str(artifacts/'commit-review.png'),full_page=True)
            missing_remote=root/'.git/missing-browser-remote.git';git(root,'remote','set-url','origin',str(missing_remote))
            page.locator('#confirm-commit').click()
            expect(page.locator('#commit-error')).to_contain_text('created locally',timeout=30000)
            local_commit=git(worktree,'rev-parse','HEAD')
            assert '% publish from UI' in (worktree/'main.tex').read_text()
            assert (worktree/'job.md').read_text()=='Committed job context'
            git(root,'remote','set-url','origin',str(remote))
            page.get_by_role('button',name='Retry push',exact=True).click()
            expect(page.locator('#commit-dialog')).to_be_hidden(timeout=30000)
            assert git(root,'--git-dir',str(remote),'rev-parse','refs/heads/etp-acme-swe')==local_commit
            absent=subprocess.run(['git','--git-dir',str(remote),'rev-parse','--verify','refs/heads/provider-history'],capture_output=True)
            assert absent.returncode!=0,'Commit & push published an unrelated branch'
            assert git(worktree,'rev-list','--count','master..HEAD')=='1','Retry created a duplicate commit'
            page.get_by_role('tab',name='Structure',exact=True).click();page.screenshot(path=str(artifacts/'comparison.png'),full_page=True)
            page.get_by_role('tab',name='PDF',exact=True).click();page.get_by_role('button',name='Compile both PDFs',exact=True).click()
            expect(page.locator('#compile')).to_be_enabled(timeout=180000)
            page.screenshot(path=str(artifacts/'pdf-debug.png'),full_page=True)
            print('PDF status:',page.locator('#notice').inner_text(),flush=True)
            print('Browser errors:',errors,flush=True)
            expect(page.locator('#current-pdf .textLayer')).to_have_count(1,timeout=10000)
            expect(page.locator('#current-pdf .pdf-page')).to_have_css('background-color','rgb(255, 255, 255)')
            expect(page.locator('#original-pdf .textLayer')).to_have_count(1,timeout=180000)
            assert page.locator('#current-pdf .textLayer').inner_text().strip()
            selected=page.locator('#current-pdf .textLayer').evaluate("el => {const range=document.createRange();range.selectNodeContents(el);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);return selection.toString();}")
            assert 'Jordan' in selected and 'Python' in selected,selected
            page.evaluate('window.getSelection().removeAllRanges()')
            name_span=page.locator('#current-pdf .textLayer span').filter(has_text='Jordan Lee').first
            rect=name_span.bounding_box();assert rect
            page.mouse.move(rect['x']+1,rect['y']+rect['height']/2);page.mouse.down()
            page.mouse.move(rect['x']+rect['width'],rect['y']+rect['height']/2,steps=12);page.mouse.up()
            assert 'Jordan' in page.evaluate('window.getSelection().toString()'), 'Mouse selection failed'
            page.evaluate('window.getSelection().removeAllRanges()')
            page.screenshot(path=str(artifacts/'pdf-comparison.png'),full_page=True)
            page.locator('#theme').select_option('light')
            page.screenshot(path=str(artifacts/'pdf-comparison-light.png'),full_page=True)
            page.locator('#zoom').select_option('1.25');expect(page.locator('#current-pdf .pdf-page')).to_have_css('width','765px',timeout=30000)
            expect(page.locator('#current-pdf .textLayer')).to_have_count(1,timeout=30000)
            page.get_by_role('tab',name='LaTeX',exact=True).click();saved=(worktree/'main.tex').read_text();editor.fill(saved+'\n% local edit')
            (worktree/'main.tex').write_text(saved+'\n% external edit')
            page.get_by_role('button',name='Save changes',exact=True).click();expect(page.locator('#notice')).to_contain_text('changed outside the editor')
            assert '% external edit' in (worktree/'main.tex').read_text()
            assert '% local edit' in editor.inner_text()
            page.on('dialog',lambda dialog:dialog.accept())
            page.get_by_role('button',name='↻ Reload',exact=True).click();expect(editor).to_contain_text('% external edit')
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile editor horizontal overflow'
            page.screenshot(path=str(artifacts/'latex-editor-mobile.png'),full_page=True)
            page.get_by_role('tab',name='Structure',exact=True).click()
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile horizontal overflow'
            page.screenshot(path=str(artifacts/'mobile.png'),full_page=True)
            if args.sample_cv:
                # Copy source into the disposable fixture; never mutate the user's repository.
                shutil.copyfile(args.sample_cv/'main.tex',root/'main.tex');shutil.copyfile(args.sample_cv/'resume.cls',root/'resume.cls')
                page.set_viewport_size({'width':1600,'height':1100});page.goto('http://127.0.0.1:'+str(server.server_port)+'/?branch=master')
                expect(page.locator('#current-document')).to_contain_text('Technical Skills')
                assert page.locator('#current-document .cv-table').count()>0
                assert '-5pt' not in page.locator('#current-document').inner_text()
                assert 'mailto:' not in page.locator('#current-document').inner_text()
                page.screenshot(path=str(artifacts/'sample-structure.png'),full_page=True)
                page.get_by_role('tab',name='PDF',exact=True).click();page.get_by_role('button',name='Compile both PDFs',exact=True).click()
                expect(page.locator('#current-pdf .textLayer').first).to_be_visible(timeout=180000)
                expect(page.locator('#compile')).to_be_enabled(timeout=180000)
                count=page.locator('#current-pdf .textLayer').count();assert count>=2
                page.screenshot(path=str(artifacts/'sample-pdf.png'),full_page=True)
                page.locator('#current-pdf').evaluate('el => el.scrollTop=el.scrollHeight')
                page.screenshot(path=str(artifacts/'sample-pdf-last-page.png'),full_page=True)
                actual_pdf=list(server.compiler.results.values())[-1]
                shutil.copyfile(actual_pdf,artifacts/'sample-preview.pdf')
                text='\n'.join(page.extract_text() for page in PdfReader(actual_pdf).pages)
                assert len(text.strip()) > 100, 'Compiled sample CV has no useful text layer'
                print('Sample CV PDF pages:',count)
            assert not errors, errors
            browser.close()
        print('PASS: provider/model discovery, reasoning delivered to both CLI steps, themes, branch creation, edits, reviewed commit/push with safe retry, reports, conflicts, selectable PDFs, zoom, mobile layout, zero browser errors.')
        print('Artifacts:',artifacts)
    finally:
        model_patch.stop()
        server.shutdown();server.server_close();thread.join()

if __name__=='__main__':main()
