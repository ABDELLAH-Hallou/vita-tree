"""Checkpoint retries and attempt lineage, using controlled local AI and real TeX."""
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
from support import SOURCE, init_repo, set_theme


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=('chrome','chromium'), default='chromium')
    args = parser.parse_args()
    expect.set_options(timeout=30000)
    artifacts = Path('.test-artifacts').resolve()
    root = init_repo(artifacts/('resume-ui-'+str(time.time_ns())))
    control = root/'.git/control';control.mkdir()
    config = root/'.vita';config.mkdir()
    (config/'extensions.json').write_text(json.dumps({'llm_providers':{'openai':{'model':'fixture-model'}}}))
    source = root/'.git/fake-vita'
    prompts = source/'vita/assets/prompts';prompts.mkdir(parents=True)
    for step in ('extract','review','cover'):(prompts/(step+'.md')).write_text('Fixture task')
    server = VitaTreeServer(('127.0.0.1',0), root, 'main.tex', source, log_dir=root/'.git/test-logs')
    branch = server.workspace.create('master','checkpoint-retry',json.dumps({'label':'checkpoint-retry','pipeline':True,'extraction':True}),digest(SOURCE))
    fail = control/'checkpoint-retry.cover.fail';fail.touch()
    (control/'checkpoint-retry.release').touch()
    worker = threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    command = [sys.executable,str(Path(__file__).with_name('fake_ai_process.py').resolve())]
    errors=[]
    try:
        with patch.object(server.workspace,'vita_command',return_value=command),patch.dict(os.environ,{'VITA_TEST_CONTROL':str(control)}),sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome' if args.browser=='chrome' else None)
            page=browser.new_page(viewport={'width':1440,'height':1000})
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.get_by_role('button',name='Open checkpoint-retry',exact=True).click()
            page.get_by_role('tab',name='Job details & AI',exact=False).click()
            page.locator('#provider').select_option('openai')
            page.locator('#model').fill('fixture-model');page.locator('#model').press('Tab')
            page.locator('#run-all').click()
            expect(page.locator('.dag-node[data-step=cover]')).to_have_attribute('data-status','failed')
            page.locator('#view-run').click()
            expect(page.locator('#attempt-history')).to_contain_text('Attempt 1')
            assert (Path(branch['worktree'])/'main.tex').read_text()==SOURCE
            page.locator('#resume-run').click()
            expect(page.locator('#resume-dialog')).to_be_visible()
            expect(page.locator('#resume-reuse')).to_contain_text('Tailor CV')
            expect(page.locator('#resume-rerun')).to_have_text('Cover letter, Final checks')
            expect(page.locator('#resume-adapted')).to_be_visible()
            page.screenshot(path=str(artifacts/'resume-review-light.png'),full_page=True)
            # Preview and cancellation must not launch a backend call.
            before=len((control/'checkpoint-retry.cover.calls').read_text().splitlines())
            page.locator('#resume-dialog .close-dialog').last.click()
            assert len((control/'checkpoint-retry.cover.calls').read_text().splitlines())==before
            page.locator('#resume-run').click();page.locator('#confirm-resume').click()
            expect(page.locator('.dag-node[data-step=cover]')).to_have_attribute('data-status','failed')
            expect(page.locator('#workflow-run')).to_contain_text('Attempt 2')
            page.locator('#view-run').click()
            expect(page.locator('#attempt-history .attempt-row')).to_have_count(2)
            expect(page.locator('#attempt-history')).to_contain_text('Continues attempt 1')
            assert (Path(branch['worktree'])/'main.tex').read_text()==SOURCE
            page.reload()
            expect(page.locator('#resume-run')).to_be_visible()
            # A changed effective setup cannot reuse the prior prefix.
            page.get_by_role('tab',name='Job details & AI',exact=False).click()
            page.locator('#model').fill('different-model');page.locator('#model').press('Tab')
            page.locator('#resume-run').click()
            expect(page.locator('#resume-reuse')).to_contain_text('Tailor CV')
            page.locator('#resume-current-config').check()
            expect(page.locator('#resume-reuse')).to_contain_text('None. Start again')
            page.locator('#resume-dialog .close-dialog').last.click()
            page.locator('#model').fill('fixture-model');page.locator('#model').press('Tab')
            fail.unlink()
            page.locator('#resume-run').click();page.locator('#confirm-resume').click()
            expect(page.locator('.dag-node[data-step=validating]')).to_have_attribute('data-status','succeeded',timeout=180000)
            expect(page.locator('.dag-node[data-step=adapt] .dag-status')).to_have_text('Done · reused')
            page.locator('#view-run').click()
            expect(page.locator('#attempt-history .attempt-row')).to_have_count(3)
            expect(page.locator('#attempt-history')).to_contain_text('Continues attempt 2')
            assert len((control/'checkpoint-retry.adapt.calls').read_text().splitlines())==1
            assert 'checkpoint-retry systems' in (Path(branch['worktree'])/'main.tex').read_text()
            page.locator('#open-run-cover-pdf').click()
            expect(page.locator('#cover-pdf .textLayer')).to_contain_text('Dear hiring team')
            set_theme(page,'dark');page.screenshot(path=str(artifacts/'resume-complete-dark.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            page.locator('#zoom').select_option('fit')
            page.wait_for_function("()=>{const page=document.querySelector('#cover-pdf .pdf-page');const pane=document.querySelector('#cover-pdf');return page&&page.clientWidth<=pane.clientWidth}")
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(artifacts/'resume-mobile.png'),full_page=True)
            assert not errors,errors
            browser.close()
        print('PASS: explicit retry review/cancel, configuration invalidation, repeated failure with draft preservation, refreshed attempt lineage, reused adapted source, successful real cover PDF, themes/mobile, no browser errors.')
    finally:
        server.shutdown();server.server_close();worker.join()
        for thread in list(server.workspace._ai_threads):thread.join(timeout=15)


if __name__=='__main__':main()
