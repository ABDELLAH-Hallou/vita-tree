"""Workflow graph, report reader, filters and history; no real AI/network calls."""
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
from vita_tree.workspace import digest
from support import init_repo, SOURCE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=('chrome', 'chromium'), default='chromium')
    args = parser.parse_args()
    expect.set_options(timeout=30000)
    artifacts = Path('.test-artifacts').resolve()
    root = init_repo(artifacts / ('workflow-ui-' + str(time.time_ns())))
    control = root / '.git/control'; control.mkdir()
    config = root / '.vita'; config.mkdir()
    (config / 'extensions.json').write_text(json.dumps({'llm_providers': {'openai': {'model': 'fixture-model'}}}))
    source = root / '.git/fake-vita'
    prompts = source / 'vita/assets/prompts'; prompts.mkdir(parents=True)
    for step in ('extract', 'review', 'cover'):
        (prompts / (step + '.md')).write_text('Fixture task')
    server = VitaTreeServer(('127.0.0.1', 0), root, 'main.tex', source)
    server.workspace.create('master', 'platform-engineer', json.dumps({'label': 'platform-engineer', 'pipeline': True, 'extraction': True, 'hold': 'review'}), digest(SOURCE))
    server.workspace.create('master', 'research-engineer', json.dumps({'label': 'research-engineer', 'pipeline': True, 'fail': 'extract'}), digest(SOURCE))
    server.workspace.create('master', 'independent-steps', json.dumps({'label': 'independent-steps', 'pipeline': True}), digest(SOURCE))
    (control / 'independent-steps.release').touch()
    (control / 'platform-engineer.release').touch()
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    command = [sys.executable, str(Path(__file__).with_name('fake_ai_process.py').resolve())]
    errors = []
    try:
        with patch.object(server.workspace, 'vita_command', return_value=command), patch.dict(os.environ, {'VITA_TEST_CONTROL': str(control)}), sync_playwright() as p:
            browser = p.chromium.launch(**({'channel': 'chrome'} if args.browser == 'chrome' else {}))
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            page.on('pageerror', lambda error: errors.append(str(error)))
            url = f'http://127.0.0.1:{server.server_port}'
            page.goto(url)
            expect(page.get_by_role('button', name='Open platform-engineer', exact=True)).to_be_visible()
            page.screenshot(path=str(artifacts / 'workbench-light.png'), full_page=True)
            page.get_by_role('button', name='Open platform-engineer', exact=True).click()
            expect(page.locator('.dag-node')).to_have_count(6)
            page.get_by_role('tab', name='Job & AI', exact=False).click()
            page.locator('#step-extract').check(); page.locator('#step-cover').check()
            expect(page.locator('#step-review')).to_be_checked()
            page.locator('#step-review').uncheck()  # Run all overrides the subset.
            page.locator('#provider').select_option('openai');page.locator('#model').select_option('fixture-model')
            page.locator('#run-all').click()
            review = page.locator('.dag-node[data-step=review]')
            expect(review).to_have_attribute('data-status', 'running')
            expect(page.locator('.dag-node[data-step=extract]')).to_have_attribute('data-status', 'succeeded')
            expect(page.locator('.dag-node[data-step=cover]')).to_have_attribute('data-status', 'pending')
            expect(page.locator('#step-cover')).to_be_disabled()
            review.focus();page.keyboard.press('Enter')
            expect(page.locator('#task-inspector')).to_contain_text('Running')
            expect(page.locator('#task-output')).to_be_disabled()
            expect(page.locator('#task-run')).to_be_disabled()
            expect(page.locator('#run-all')).to_be_disabled()
            expect(page.locator('#run-adapt')).to_be_disabled()
            page.locator('#workflow-title').scroll_into_view_if_needed()
            page.screenshot(path=str(artifacts / 'workflow-running.png'), full_page=True)
            page.locator('#back').click()
            page.locator('[data-filter=running]').click()
            expect(page.locator('#branch-list .branch-row')).to_have_count(1)
            page.locator('[data-filter=all]').click()
            page.get_by_role('button', name='Open research-engineer', exact=True).click()
            expect(page.locator('#current-label')).to_have_text('research-engineer')
            page.get_by_role('tab', name='Job & AI', exact=False).click()
            page.locator('#step-extract').check()
            page.locator('#provider').select_option('openai');page.locator('#model').select_option('fixture-model')
            expect(page.locator('#step-extract')).to_be_checked()
            page.locator('#run-adapt').click()
            expect(page.locator('.dag-node[data-step=extract]')).to_have_attribute('data-status', 'failed')
            expect(page.locator('.dag-node[data-step=adapt]')).to_have_attribute('data-status', 'blocked')
            page.locator('#theme').select_option('dark')
            page.screenshot(path=str(artifacts / 'workflow-failed-dark.png'), full_page=True)
            (control / 'platform-engineer.review.release').touch()
            expect(page.locator('#run-notifications')).to_contain_text('Completed: platform-engineer')
            page.locator('#run-notifications').get_by_role('button', name='Completed: platform-engineer — Review', exact=True).click()
            expect(page.locator('.dag-node[data-status=succeeded]')).to_have_count(6)
            expect(page.locator('#selected-run-files .report-prose table').first).to_be_visible()
            expect(page.locator('#selected-run-files .report-prose h3').first).to_contain_text('Initial analysis')
            expect(page.locator('#selected-run-files')).to_contain_text('cover-letter.tex')
            completed_id = page.locator('#workflow-run').input_value()
            page.locator('.dag-node[data-step=review]').click();page.locator('#task-output').click()
            expect(page.locator('#selected-run-files details[data-path=".vita/results/review.md"]')).to_have_attribute('open', '')
            page.locator('#theme').select_option('light')
            page.get_by_role('tab', name='Structure', exact=True).click()
            expect(page.locator('#toast')).to_be_hidden()
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(artifacts / 'workflow-complete-light.png'), full_page=True)
            page.locator('#theme').select_option('dark')
            page.screenshot(path=str(artifacts / 'workflow-complete-dark.png'), full_page=True)
            for theme in ('light','dark'):
                page.locator('#theme').select_option(theme)
                contrasts=page.evaluate('''() => {
                  const style=getComputedStyle(document.documentElement);
                  const lum=name=>{
                    let hex=style.getPropertyValue(name).trim().slice(1);if(hex.length===3)hex=[...hex].map(c=>c+c).join('');
                    const rgb=[0,2,4].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
                    return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;
                  };
                  return [['--ink','--panel'],['--muted','--bg'],['--accent','--accent-light'],['--positive','--positive-bg'],['--negative','--negative-bg']].map(([a,b])=>(Math.max(lum(a),lum(b))+.05)/(Math.min(lum(a),lum(b))+.05));
                }''')
                assert all(ratio >= 4.5 for ratio in contrasts), (theme, contrasts)
            page.get_by_role('tab', name='Structure', exact=True).focus();page.keyboard.press('ArrowRight')
            expect(page.get_by_role('tab',name='LaTeX',exact=True)).to_have_attribute('aria-selected','true')
            assert 'view=source' in page.url
            page.keyboard.press('Home')
            expect(page.get_by_role('tab',name='Structure',exact=True)).to_be_focused()
            page.reload()
            expect(page.locator('#workflow-run')).to_have_value(completed_id)
            expect(page.locator('.dag-node[data-status=succeeded]')).to_have_count(6)
            page.locator('#workflow-run').select_option('draft')
            expect(page.locator('.dag-node[data-status=succeeded]')).to_have_count(0)
            page.locator('#workflow-run').select_option(completed_id)
            # Hostile Markdown remains inert text; only HTTP(S) links are active.
            safe = page.evaluate('''async () => {
              const {markdown}=await import('/reports.js');
              const el=markdown('# Report\\n<script>window.reportXSS=1</script>\\n[unsafe](javascript:alert(1))\\n[safe](https://example.invalid)\\n\\n| Skill | Score |\\n|---|---:|\\n| Python | 80 |');
              document.body.append(el);
              const result={scripts:el.querySelectorAll('script').length, links:[...el.querySelectorAll('a')].map(a=>a.protocol), tables:el.querySelectorAll('table').length, xss:window.reportXSS};
              el.remove();return result;
            }''')
            assert safe == {'scripts': 0, 'links': ['https:'], 'tables': 1, 'xss': None}, safe
            # Old histories must not invent successful stages.
            legacy = page.evaluate('''async () => {
              const {graphStages}=await import('/workflow.js');
              return graphStages({status:'failed',step:'failed'}).map(s=>s.status);
            }''')
            assert set(legacy) == {'unknown'}
            # Every node can run independently, including validation without AI.
            page.locator('#back').click()
            page.get_by_role('button', name='Open independent-steps', exact=True).click()
            page.get_by_role('tab', name='Job & AI', exact=False).click()
            page.locator('#provider').select_option('openai');page.locator('#model').select_option('fixture-model')
            for step in ('extract', 'analyze', 'adapt', 'review', 'cover', 'validating'):
                node = page.locator(f'.dag-node[data-step={step}]')
                node.click()
                expect(page.locator('#task-run')).to_be_enabled()
                with page.expect_response(lambda response: response.url.endswith('/api/adapt') and response.request.method == 'POST') as pending:
                    page.locator('#task-run').click()
                record = pending.value.json()
                expect(page.locator('#workflow-run')).to_have_value(record['id'])
                expect(node).to_have_attribute('data-status', 'succeeded')
                expect(page.locator('.dag-node[data-status=succeeded]')).to_have_count(1 if step == 'validating' else 2)
                expect(page.locator('.dag-node[data-status=skipped]')).to_have_count(5 if step == 'validating' else 4)
                assert server.workspace.get_job(record['id'])['status'] == 'succeeded'
                if step in ('extract','analyze'):
                    assert server.workspace.read('independent-steps', 'main.tex') == SOURCE
            # Arbitrary selection: no implicit analysis or adaptation.
            page.get_by_role('tab', name='Job & AI', exact=False).click()
            for step in ('extract','analyze','adapt','review','cover'):
                page.locator('#step-' + step).uncheck()
            expect(page.locator('#run-adapt')).to_be_disabled()
            page.locator('#step-review').check();page.locator('#step-cover').check()
            with page.expect_response(lambda response: response.url.endswith('/api/adapt') and response.request.method == 'POST') as pending:
                page.locator('#run-adapt').click()
            record = pending.value.json()
            expect(page.locator('#workflow-run')).to_have_value(record['id'])
            expect(page.locator('.dag-node[data-status=succeeded]')).to_have_count(3)
            assert {t['id'] for t in server.workspace.get_job(record['id'])['stages'] if t['status']=='succeeded'} == {'review','cover','validating'}
            # Unsaved job edits stop individual launch without losing the edits.
            page.locator('#job-description').fill('Unsaved job text')
            page.locator('.dag-node[data-step=review]').click();page.locator('#task-run').click()
            expect(page.locator('#notice')).to_contain_text('Save your CV and job description')
            expect(page.locator('#job-description')).to_have_value('Unsaved job text')
            page.screenshot(path=str(artifacts / 'workflow-independent.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.emulate_media(reduced_motion='reduce')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Page overflows mobile'
            graph = page.locator('#workflow-graph')
            assert graph.evaluate('el=>el.scrollWidth>el.clientWidth'), 'Graph should scroll within its container'
            page.locator('.dag-node[data-step=validating]').focus();page.keyboard.press('Enter')
            expect(page.locator('#task-title')).to_have_text('Validate')
            page.screenshot(path=str(artifacts / 'workflow-mobile.png'), full_page=True)
            page.locator('#toggle-workflow').click()
            expect(page.locator('#workflow-body')).to_be_hidden()
            expect(page.locator('#toggle-workflow')).to_have_attribute('aria-expanded', 'false')
            assert not errors, errors
            browser.close()
        print('PASS: full pipeline, independent tasks, arbitrary subsets, unsaved-edit guard, failures, task inspector, run history, branch filters, report Markdown, XSS protection, keyboard, mobile and themes.')
    finally:
        (control / 'platform-engineer.review.release').touch()
        server.shutdown();server.server_close();worker.join()
        for thread in list(server.workspace._ai_threads):thread.join(timeout=15)


if __name__ == '__main__':
    main()
