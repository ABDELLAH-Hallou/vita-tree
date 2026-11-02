"""Explicit unattended batch approval, using only a synthetic CLI contract."""
import json
from pathlib import Path
import threading
import time
from unittest.mock import patch

from playwright.sync_api import expect, sync_playwright
from support import init_repo, set_theme
from vita_tree.server import VitaTreeServer


def main():
    expect.set_options(timeout=30000)
    artifacts=Path('.test-artifacts/jobenu-approval');artifacts.mkdir(parents=True,exist_ok=True)
    root=init_repo((artifacts/('fixture-'+str(time.time_ns()))).resolve())
    server=VitaTreeServer(('127.0.0.1',0),root,'main.tex',log_dir=root/'.git/test-logs')
    manager=server.workspace.jobenu
    supported=[True];executions=[]
    row=dict(application_id='one',company='North Robotics',position='Research Engineer',
             branch='synthetic-application',key='synthetic-key',fingerprint='synthetic-version',action='create')
    def invoke(command,env,args,**kwargs):
        if '--help' in args:
            return 0,b'--plan-id --approve-plan --json'+(b' unattended' if supported[0] else b''),b''
        if args[0]=='approval-policies':
            if not supported[0]:return 2,b'unknown command',b''
            return 0,json.dumps(dict(schema_version=1,policy_version='approval-policy/1',modes=[{'id':'unattended'}],requires_explicit_selection=['unattended'],generated_prompt_consent=False)).encode(),b''
        assert args[:2]==['import','jobenu']
        mode=args[args.index('--approval')+1]
        if '--dry-run' in args:
            return 0,json.dumps(dict(schema_version=1,status='planned',plan_id='plan-'+mode,
                approval=mode,approval_policy=dict(version='approval-policy/1',mode=mode),entries=[row])).encode(),b''
        executions.append((mode,'--rerun' in args))
        result={**row,'status':'complete','completed_steps':['extract','analyze','adapt','review','cover']}
        if mode=='auto':result.update(status='awaiting_approval',pending={'step':'adapt','revision':'synthetic-proposal'})
        return (2 if mode=='auto' else 0),json.dumps(dict(schema_version=1,status=result['status'],results=[result])).encode(),b''
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    try:
        with patch.object(manager,'command',return_value=(['fixture'],{})),patch.object(manager,'invoke',side_effect=invoke),sync_playwright() as pw:
            browser=pw.chromium.launch();page=browser.new_page(viewport=dict(width=1440,height=1000))
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}')
            page.locator('#open-jobenu').click();expect(page.locator('#jobenu-import')).to_be_visible()
            for width in (1440,768,390):
                path=artifacts/f'before-{width}.png'
                if not path.exists():
                    page.set_viewport_size(dict(width=width,height=1000));page.screenshot(path=str(path),full_page=True)
            assert page.locator('#jobenu-approval option[value=unattended]').count()==1,'Missing fully automatic approval choice'
            page.set_viewport_size(dict(width=1440,height=1000))
            expect(page.locator('#jobenu-approval option[value=unattended]')).to_have_js_property('disabled',False)
            expect(page.locator('#jobenu-approval')).to_have_value('human')
            page.locator('#jobenu-file').set_input_files(dict(name='synthetic.json',mimeType='application/json',buffer=json.dumps(dict(applications=[dict(id='one',company=row['company'],position=row['position'],description='Synthetic opportunity',status='SAVED')])).encode()))
            page.locator('#jobenu-base').fill('master')
            page.locator('#jobenu-approval').select_option('auto')
            expect(page.locator('#jobenu-approval-help')).to_contain_text('can still need review')
            page.locator('#jobenu-preview').click();expect(page.locator('#jobenu-start')).to_be_enabled()
            page.locator('#jobenu-start').click()
            expect(page.get_by_role('button',name='Review changes',exact=True)).to_be_visible()
            page.get_by_role('button',name='Preview resume',exact=True).click()
            expect(page.locator('#jobenu-start')).to_be_enabled()
            page.locator('#jobenu-approval').select_option('unattended')
            expect(page.locator('#jobenu-start')).to_be_disabled()
            expect(page.locator('#jobenu-preview')).to_be_disabled()
            expect(page.locator('#jobenu-approval-help')).to_contain_text('without review')
            expect(page.locator('#jobenu-approval-change #jobenu-rerun')).to_be_visible()
            expect(page.locator('#jobenu-rerun')).not_to_be_checked()
            page.locator('#jobenu-rerun').check()
            for theme in ('light','dark'):
                set_theme(page,theme)
                for width in (1440,768,390):
                    page.set_viewport_size(dict(width=width,height=1000))
                    page.locator('#jobenu-approval').evaluate("el=>el.scrollIntoView({block:'center'})")
                    page.screenshot(path=str(artifacts/f'approval-{theme}-{width}.png'))
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                snapshot=page.evaluate("""() => {
                    const doc=document.documentElement.cloneNode(true),originals=document.querySelectorAll('input,select,textarea');
                    doc.querySelectorAll('input,select,textarea').forEach((el,i)=>{
                        const current=originals[i];
                        if(el.tagName==='SELECT')Array.from(el.options).forEach((option,j)=>option.toggleAttribute('selected',current.options[j].selected));
                        else if(el.tagName==='TEXTAREA')el.textContent=current.value;
                        else if(!['file','password'].includes(el.type)){el.setAttribute('value',current.value);el.toggleAttribute('checked',current.checked);}
                    });
                    doc.querySelectorAll('#board[hidden],#workspace[hidden],script,link[rel=modulepreload]').forEach(el=>el.remove());
                    doc.querySelectorAll('link[href]').forEach(el=>el.setAttribute('href','../../src/vita_tree/static'+new URL(el.getAttribute('href'),location.href).pathname));
                    return '<!doctype html>'+doc.outerHTML;
                }""")
                (artifacts/f'inspect-{theme}.html').write_text(snapshot,encoding='utf-8')
            page.set_viewport_size(dict(width=1440,height=1000))
            page.locator('#jobenu-preview').click();expect(page.locator('#jobenu-start')).to_be_enabled()
            page.locator('#jobenu-start').click()
            expect(page.locator('#jobenu-history')).to_contain_text('AI stages complete')
            expect(page.get_by_role('button',name='Review changes',exact=True)).to_have_count(0)
            assert executions==[('auto',False),('unattended',True)],executions
            page.reload();page.locator('#open-jobenu').click()
            page.get_by_role('button',name='Preview resume',exact=True).click()
            expect(page.locator('#jobenu-approval')).to_have_value('unattended')
            expect(page.locator('#jobenu-start')).to_be_enabled()
            supported[0]=False
            page.locator('#jobenu-install').evaluate('el=>el.open=true')
            page.locator('#jobenu-check').click()
            expect(page.locator('#jobenu-approval option[value=unattended]')).to_have_js_property('disabled',True)
            expect(page.locator('#jobenu-approval')).to_have_value('unattended')
            expect(page.locator('#jobenu-preview')).to_be_disabled()
            expect(page.locator('#jobenu-approval-help')).to_contain_text('Update Vita CV')
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown();server.server_close();worker.join()
    print('PASS: explicit unattended policy reaches the batch command; verified-only mode stays separate; fresh consent, reload, unsupported backend and responsive themes.')


if __name__=='__main__':main()
