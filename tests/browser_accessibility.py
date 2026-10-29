"""Scoped automated evidence, not screen-reader or human usability certification."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from playwright.sync_api import expect, sync_playwright
from browser_support import BROWSERS, launch_browser
from support import SOURCE, init_repo
from requirements_fixtures import JD, seed
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest


def keyboard_to(page, selector):
    target = page.locator(selector)
    expect(target).to_be_visible()
    history = []
    for attempt in range(240):
        history.append(page.evaluate('''() => {const e=document.activeElement;return e.id || e.tagName+':'+(e.getAttribute('aria-label')||e.textContent||'').slice(0,45);}'''))
        if target.evaluate('el => el===document.activeElement'):
            bounds = target.bounding_box()
            # A viewport resize does not itself move focus or scroll. Complete
            # a real Tab cycle before evaluating focus visibility in that case.
            if attempt == 0 and bounds and (bounds['y'] < -1 or bounds['y']+bounds['height'] > page.viewport_size['height']+1):
                page.keyboard.press('Tab')
                continue
            page.wait_for_function('''selector=>{const r=document.querySelector(selector)?.getBoundingClientRect();
              return r&&r.top>=-1&&r.bottom<=innerHeight+1;}''',arg=selector,timeout=5000)
            bounds = target.bounding_box()
            assert bounds and bounds['y'] >= -1 and bounds['y']+bounds['height'] <= page.viewport_size['height']+1, ('Clipped keyboard focus', selector, bounds)
            assert target.evaluate('''el=>{const s=getComputedStyle(el);return parseFloat(s.outlineWidth)>=1 && s.outlineStyle!=='none' && s.outlineColor!=='transparent';}'''), ('Missing keyboard focus indicator',selector)
            return target
        # Do not depend on wrapping through browser chrome (Firefox keeps the
        # last DOM activeElement while focus moves into its own toolbar).
        backwards = target.evaluate('el=>!!(document.activeElement.compareDocumentPosition(el)&Node.DOCUMENT_POSITION_PRECEDING)')
        page.keyboard.press('Shift+Tab' if backwards else 'Tab')
    context = page.evaluate('''() => ({hasFocus:document.hasFocus(),dialogs:[...document.querySelectorAll('dialog[open]')].map(el=>el.id),
        boardHidden:document.querySelector('#board').hidden, workspaceHidden:document.querySelector('#workspace').hidden})''')
    raise AssertionError('Keyboard could not reach ' + selector + '; context: ' + str(context) + '; focus cycle: ' + str(history[-8:]))


def activate(page, selector):
    keyboard_to(page, selector)
    page.keyboard.press('Enter')


def type_text(page, selector, value):
    keyboard_to(page, selector)
    page.keyboard.press('ControlOrMeta+A')
    page.keyboard.insert_text(value)
    page.keyboard.press('Tab')


def scan(page, report, output, name, scope=None):
    if not page.evaluate('!!window.axe'):
        # Serve the pinned test tool through a Playwright-only same-origin route.
        # Keep the real application's CSP intact; no production test endpoint.
        page.add_script_tag(url='/__fixture_axe.js')
    data = page.evaluate("""async scope => {
      const r=await axe.run(scope || document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}});
      const summarize = list => list.map(v=>({id:v.id,impact:v.impact,help:v.help,helpUrl:v.helpUrl,
        nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary || '',checks:[...n.any,...n.all,...n.none].map(c=>c.id)}))}));
      return {axeVersion:r.testEngine.version,violations:summarize(r.violations),incomplete:summarize(r.incomplete),passes:r.passes.length};
    }""", scope)
    report['scans'].append(dict(state=name, scope=scope or 'document', **data))
    theme = page.locator('html').get_attribute('data-theme')
    if theme not in report['tokenContrast']:
        pairs = page.evaluate('''() => {const s=getComputedStyle(document.documentElement);
          return Object.fromEntries(['ink','muted','accent','negative','positive','panel'].map(k=>[k,s.getPropertyValue('--'+k).trim()]));}''')
        def luminance(value):
            raw = value.lstrip('#')
            if len(raw)==3: raw=''.join(c*2 for c in raw)
            channels = [int(raw[i:i+2],16)/255 for i in (0,2,4)]
            linear = [c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in channels]
            return sum(c*w for c,w in zip(linear,(.2126,.7152,.0722)))
        background = luminance(pairs['panel'])
        report['tokenContrast'][theme] = {key:round((max(luminance(value),background)+.05)/(min(luminance(value),background)+.05),3)
                                        for key,value in pairs.items() if key!='panel'}
        assert all(ratio>=4.5 for ratio in report['tokenContrast'][theme].values()), report['tokenContrast'][theme]
    page.screenshot(path=str(output/(name+'.png')))
    print('Audit:', report['browser'], name, 'violations='+str(len(data['violations'])), flush=True)


def review_matrix(page, report, output, name, dialog, action):
    original_theme = page.locator('html').get_attribute('data-theme')
    for theme in ('light','dark'):
        # Appearance fixture only: the workflow itself toggles the real control.
        page.locator('html').evaluate('(el,theme)=>el.dataset.theme=theme',theme)
        for label,width,height,zoom in [('desktop',1280,900,1),('narrow',320,640,1),('zoom-200',1280,720,2)]:
            page.set_viewport_size({'width':width,'height':height})
            page.evaluate('z=>document.documentElement.style.zoom=z',str(zoom))
            scan(page,report,output,name+'-'+label+'-'+theme,dialog)
            keyboard_to(page,action)
            assert page.locator(dialog+' .review-scroll').evaluate('el=>el.clientHeight>40'), 'Review content lost its scroll area'
    page.evaluate('document.documentElement.style.zoom=""')
    page.set_viewport_size({'width':1280,'height':900})
    page.locator('html').evaluate('(el,theme)=>el.dataset.theme=theme',original_theme)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=BROWSERS, default='chromium')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import vita
    expect.set_options(timeout=45000)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = dict(schemaVersion=1, browser=args.browser, platform=platform.platform(),
                  playwright=importlib.metadata.version('playwright'), backend=importlib.metadata.version('vita-cv'),
                  treeCommit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  sourceHashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
                      'src/vita_tree/static/app.js','src/vita_tree/static/ai-settings.js','src/vita_tree/static/requirements.js',
                      'src/vita_tree/static/factual-review.js','src/vita_tree/static/styles.css','src/vita_tree/static/index.html','src/vita_tree/static/workflow.js',
                      'tests/browser_accessibility.py','tests/browser_support.py','package-lock.json')},
                  fixtureHashes=dict(source=hashlib.sha256(SOURCE.encode()).hexdigest(),job=hashlib.sha256(JD.encode()).hexdigest()),
                  tokenContrast={},scans=[], tasks=[], limitations=['No screen reader, physical mobile device or representative participant used.',
                  '200% CSS zoom and reduced layout viewports; native browser chrome zoom is not measured.',
                  'Axe scans and DOM live-region assertions cannot prove spoken announcements or PDF reading order.'])
    root = init_repo(output/('fixture-'+str(time.time_ns())))
    server = VitaTreeServer(('127.0.0.1',0),root,'main.tex',Path(vita.__file__).resolve().parent.parent,log_dir=root/'.git/test-logs')
    branch = server.workspace.create('master','accessibility',JD,digest(SOURCE))
    seed(server.workspace,'accessibility',False)
    facts = server.workspace.create('master','facts',json.dumps({'label':'facts','pipeline':True}),digest(SOURCE))
    seed(server.workspace,'facts')
    for application in (branch,facts):
        result_dir = Path(application['worktree'])/'.vita/results'
        result_dir.mkdir(parents=True,exist_ok=True)
        (result_dir/'analyze.md').write_text('# Match analysis\n\nSynthetic reviewed report.\n\n| Criterion | Result |\n| --- | --- |\n| Python | Supported |\n',encoding='utf-8')
    worker = threading.Thread(target=server.serve_forever,daemon=True)
    worker.start()
    errors = []
    command = [sys.executable,str(ROOT/'tests/smoke/factual_ai.py')]
    try:
        with patch.object(server.workspace,'vita_command',return_value=command), patch.dict(os.environ,{'VITA_TEST_CANONICAL':'1'}), sync_playwright() as pw:
            browser = launch_browser(pw,args.browser)
            report['browserVersion'] = browser.version
            page = browser.new_page(viewport={'width':1280,'height':900},reduced_motion='reduce')
            page.route('**/__fixture_axe.js',lambda route: route.fulfill(
                path=str(ROOT/'node_modules/axe-core/axe.min.js'),content_type='application/javascript'))
            page.on('pageerror',lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            activate(page,'button[aria-label="Open accessibility"]')
            # Roving tabs: move through all tabs with the documented keys.
            keyboard_to(page,'.tabs [role=tab][aria-selected=true]')
            page.keyboard.press('End')
            expect(page.locator('[data-view=ai]')).to_be_focused()
            expect(page.locator('[data-view=ai]')).to_have_attribute('aria-selected','true')
            expect(page.locator('#provider')).to_have_value('openai')
            type_text(page,'#model','shared-fixture-model')
            activate(page,'#save-ai-setup')
            expect(page.locator('#ai-setup-status')).to_contain_text('Setup saved')
            report['tasks'].append('keyboard shared setup and roving tabs')
            for theme in ('light','dark'):
                if page.locator('html').get_attribute('data-theme') != theme:
                    activate(page,'#theme')
                scan(page,report,output,'shared-'+theme)
            activate(page,'.dag-node[data-step=extract]')
            expect(page.get_by_role('dialog',name='Identify job requirements',exact=True)).to_be_visible()
            keyboard_to(page,'#step-ai-shared')
            page.keyboard.press('ArrowDown')
            expect(page.locator('#step-ai-custom')).to_be_checked()
            type_text(page,'#popup-model','invalid model id')
            activate(page,'#step-ai-apply')
            expect(page.locator('#step-ai-error')).to_contain_text('without spaces')
            expect(page.locator('#step-ai-error')).to_have_attribute('role','alert')
            scan(page,report,output,'extract-validation','#step-ai-dialog')
            type_text(page,'#popup-model','extract-fixture-model')
            activate(page,'#step-ai-fields [data-add-key]')
            expect(page.get_by_role('dialog',name='Add API connection',exact=True)).to_be_visible()
            type_text(page,'#connection-name','Cancelled fixture account')
            type_text(page,'#connection-key','synthetic-key-do-not-use')
            page.keyboard.press('Escape')
            expect(page.locator('#step-ai-fields [data-add-key]')).to_be_focused()
            expect(page.locator('#popup-model')).to_have_value('extract-fixture-model')
            activate(page,'#step-ai-fields [data-add-key]')
            expect(page.locator('#connection-key')).to_be_empty()
            type_text(page,'#connection-name','Session fixture account')
            type_text(page,'#connection-key','synthetic-key-do-not-use')
            activate(page,'#add-connection')
            expect(page.locator('#connection-dialog')).not_to_be_visible()
            expect(page.locator('#popup-connection option:checked')).to_have_text('Session fixture account')
            # Completion must leave focus in the parent modal after fields repaint.
            assert page.locator('#step-ai-dialog').evaluate('el=>el.contains(document.activeElement)'), 'Nested connection completion lost focus'
            activate(page,'#step-ai-apply')
            expect(page.locator('.dag-node[data-step=extract]')).to_be_focused()
            activate(page,'.dag-node[data-step=extract]')
            expect(page.locator('#popup-model')).to_have_value('extract-fixture-model')
            keyboard_to(page,'#step-ai-custom')
            page.keyboard.press('ArrowUp')
            expect(page.locator('#step-ai-shared')).to_be_checked()
            activate(page,'#step-ai-cancel')
            activate(page,'.dag-node[data-step=extract]')
            expect(page.locator('#step-ai-custom')).to_be_checked()
            report['tasks'].append('keyboard Extract override, invalid model, nested key, Apply and Cancel')

            activate(page,'#step-requirements')
            expect(page.get_by_role('dialog',name='Job requirements',exact=True)).to_be_visible()
            expect(page.locator('.requirement-card')).to_have_count(4)
            review_matrix(page,report,output,'requirements','#requirements-dialog','#requirements-cancel')
            # Names distinguish source navigation from AI setup. Do not click.
            activate(page,'.requirement-card:first-of-type > button[type=button]')
            expect(page.locator('#requirements-source [data-line="3"]')).to_be_focused()
            activate(page,'#requirements-cancel')
            expect(page.locator('#step-requirements')).to_be_focused()
            activate(page,'#step-requirements')
            activate(page,'#requirements-approve')
            expect(page.locator('#requirements-error')).to_contain_text('confirm')
            expect(page.locator('#requirements-error')).to_have_attribute('role','alert')
            scan(page,report,output,'requirements-error','#requirements-dialog')
            keyboard_to(page,'#requirements-confirm')
            page.keyboard.press('Space')
            activate(page,'#requirements-approve')
            expect(page.locator('#requirements-dialog')).not_to_be_visible()
            activate(page,'#step-ai-cancel')
            report['tasks'].append('keyboard requirement source, cancellation, validation and immutable approval')

            # The component-sheet resize matrix checks reflow and focus in both
            # themes; the separate component suite exercises the full form.
            for theme in ('light','dark'):
                if page.locator('html').get_attribute('data-theme') != theme:
                    activate(page,'#theme')
                for label,width,height,zoom in [('narrow',320,640,1),('zoom-200',1280,720,2)]:
                    page.set_viewport_size({'width':width,'height':height})
                    page.evaluate('z=>document.documentElement.style.zoom=z',str(zoom))
                    activate(page,'.dag-node[data-step=extract]')
                    expect(page.locator('#popup-model')).to_have_value('extract-fixture-model')
                    scan(page,report,output,label+'-'+theme,'#step-ai-dialog')
                    keyboard_to(page,'#step-ai-cancel')
                    page.keyboard.press('Escape')
                    page.evaluate('document.documentElement.style.zoom=""')
                page.set_viewport_size({'width':1280,'height':900})

            activate(page,'#back')
            expect(page.locator('#search')).to_be_focused()
            keyboard_to(page,'button[aria-label="Open facts"]')
            # Fixture-driven asynchronous refresh while a user is poised to
            # activate a row. It must not destroy the user's keyboard position.
            with page.expect_response('**/api/branches'):
                page.locator('#refresh').evaluate('el=>el.click()')
            expect(page.locator('#refresh')).to_be_enabled()
            expect(page.get_by_role('button',name='Open facts',exact=True)).to_be_focused()
            page.keyboard.press('Enter')
            expect(page.locator('#branch-title')).to_have_text('facts')
            run = server.workspace.start_ai('facts',facts['revision'],facts['jobRevision'],provider='codex',workflow={'steps':['adapt']})
            expect(page.locator('#workflow-next')).to_have_text('Review CV changes',timeout=90000)
            activate(page,'#workflow-next')
            expect(page.get_by_role('dialog',name='Review factual changes',exact=True)).to_be_visible()
            expect(page.locator('.factual-change')).to_have_count(3)
            review_matrix(page,report,output,'factual','#factual-review-panel','#cancel-factual-review')
            # Individual keyboard decisions, including the edit focus transfer.
            keyboard_to(page,'.factual-change:nth-child(1) input[value=accept]')
            page.keyboard.press('Space')
            keyboard_to(page,'.factual-change:nth-child(2) input[value=accept]')
            page.keyboard.press('ArrowDown')
            expect(page.locator('.factual-change:nth-child(2) input[value=reject]')).to_be_checked()
            keyboard_to(page,'.factual-change:nth-child(3) input[value=accept]')
            page.keyboard.press('Space')
            page.keyboard.press('ArrowDown')
            page.keyboard.press('ArrowDown')
            expect(page.locator('#fact-edit-2')).to_be_focused()
            page.keyboard.press('ControlOrMeta+A')
            page.keyboard.insert_text(r'Languages & Python, SQL, TypeScript \\')
            keyboard_to(page,'#confirm-factual-meaning')
            page.keyboard.press('Space')
            activate(page,'#apply-factual-review')
            expect(page.locator('#factual-review-panel')).not_to_be_visible()
            expect(page.locator('.dag-node[data-step=validating]')).to_have_attribute('data-status','succeeded',timeout=90000)
            assert 'TypeScript' in server.workspace.read('facts','main.tex')
            assert 'Built OOP services' not in server.workspace.read('facts','main.tex')
            activate(page,'.dag-node[data-step=adapt]')
            expect(page.locator('#step-ai-context')).to_have_text('Recorded run · view only')
            expect(page.locator('#step-ai-apply')).to_be_hidden()
            expect(page.locator('#popup-model')).to_be_disabled()
            scan(page,report,output,'recorded-setup-dark','#step-ai-dialog')
            page.keyboard.press('Escape')
            report['tasks'].append('keyboard mixed factual decisions and resumed validation')

            # Final report and actual restricted-compiler PDF, not a placeholder.
            keyboard_to(page,'.tabs [role=tab][aria-selected=true]')
            page.keyboard.press('End')
            expect(page.locator('#artifacts')).to_be_visible()
            expect(page.locator('#artifacts')).to_contain_text('Synthetic reviewed report')
            scan(page,report,output,'final-report-dark')
            keyboard_to(page,'.tabs [role=tab][aria-selected=true]')
            page.keyboard.press('Home')
            page.keyboard.press('ArrowRight')
            page.keyboard.press('ArrowRight')
            expect(page.locator('[data-view=pdf]')).to_be_focused()
            activate(page,'#compile')
            expect(page.locator('#current-pdf .textLayer').first).to_be_visible(timeout=180000)
            expect(page.locator('#current-pdf .textLayer').first).to_contain_text('Jordan')
            for theme in ('light','dark'):
                if page.locator('html').get_attribute('data-theme') != theme:
                    activate(page,'#theme')
                scan(page,report,output,'pdf-'+theme)
            keyboard_to(page,'#current-pdf .pdf-download')
            expect(page.locator('#current-pdf .pdf-download')).to_have_accessible_name('Open PDF \u2197')
            report['tasks'].append('keyboard final report and real selectable PDF access')
            report['pageErrors'] = errors
            assert not errors, errors
            browser.close()
        report['tasksPassed'] = True
    except Exception as error:
        report['tasksPassed'] = False
        report['failure'] = dict(category=type(error).__name__,message=str(error)[:2000])
        print(type(error).__name__, str(error), flush=True)
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        report['passed'] = report.get('tasksPassed',False) and not any(s['violations'] for s in report['scans'])
        (output/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=report['passed'],tasks=report['tasks'],violations=[(s['state'],[v['id'] for v in s['violations']]) for s in report['scans'] if s['violations']]),indent=2))
    raise SystemExit(not report['passed'])


if __name__ == '__main__':
    main()
