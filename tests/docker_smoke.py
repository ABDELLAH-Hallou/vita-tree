"""Exercise a built runtime image with synthetic files, real Git/PDF and browser.

Requires Docker, Playwright Chromium and pypdf on the test host. No live AI calls.
Only this script's uniquely named containers and volume are removed.
"""
import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError
import uuid


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--image',default='abdellahhallou/vita-tree:local')
    parser.add_argument('--context')
    parser.add_argument('--host-codex', action='store_true', help='Test image-to-host transport using a fake native Codex executable')
    parser.add_argument('--artifacts',type=Path,default=Path('.test-artifacts/docker-smoke'))
    args=parser.parse_args(); args.artifacts.mkdir(parents=True,exist_ok=True)
    prefix=['docker',*(['--context',args.context] if args.context else [])]
    def docker(*command):
        result=subprocess.run([*prefix,*command],capture_output=True,text=True,encoding='utf-8',timeout=180)
        if result.returncode: raise RuntimeError(result.stderr)
        return result.stdout.strip()
    name='vita-smoke-'+uuid.uuid4().hex[:10]; volume=name+'-data'
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}';opener=build_opener(ProxyHandler({}));token=None
    def api(path,data=None):
        req=Request(url+path,data=json.dumps(data).encode() if data is not None else None,
                    headers={'Content-Type':'application/json',**({'X-Vita-Token':token} if token else {})})
        try:
            with opener.open(req,timeout=120) as response:return json.load(response)
        except HTTPError as error:
            raise RuntimeError(f'{path}: HTTP {error.code}: {error.read(12000).decode(errors="replace")}') from error
    def ready():
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            try:return api('/api/session')['token']
            except OSError:time.sleep(.5)
        raise RuntimeError('Container did not become ready: '+docker('logs',name))
    def execute(code):return docker('exec',name,'python','-c',code)
    docker('volume','create',volume)
    host=None; host_options=[]
    if args.host_codex:
        from test_codex_bridge import HostTransportTests
        os.environ['VITA_TEST_HOST_BIND']='0.0.0.0'
        host=HostTransportTests();host.setUp()
        host_options=['--add-host','host.docker.internal:host-gateway',
                      '--mount',f'type=bind,source={host.auth.resolve()},target=/run/secrets/codex_auth,readonly',
                      '-e',f'VITA_CODEX_HOST_URL=http://host.docker.internal:{host.server.server_port}',
                      '-e','VITA_CODEX_HOST_AUTH_FILE=/run/secrets/codex_auth']
    try:
        docker('run','-d','--name',name,'-p',f'127.0.0.1:{port}:8765',
               '-e',f'VITA_TREE_PUBLIC_PORT={port}','--mount',f'type=volume,source={volume},target=/workspace',*host_options,args.image)
        token=ready()
        assert execute('import os;print(os.getuid())')!='0','Runtime unexpectedly root'
        assert 'build' in docker('exec',name,'vita','--help')
        docker('exec',name,'vita','build')
        assert execute('from pathlib import Path;print(Path("out/cv-Your_Name.pdf").is_file())')=='True'
        original=api('/api/workspace?branch=main')
        created=api('/api/create',{'base':'main','name':'synthetic-role','job':'Synthetic role description',
                                   'revision':original['revision'],'projectRevision':original['projectRevision']})
        content=created['content'].replace('Replace this starter with your own CV.','Synthetic reviewed result.')
        content=content.replace(r'\end{document}',r'\input{sections/details}\end{document}')
        execute('from pathlib import Path;p=Path('+repr(created['worktree'])+')/"sections";p.mkdir();(p/"details.tex").write_text("Nested included paragraph.")')
        api('/api/save',{'branch':'synthetic-role','path':'main.tex','revision':created['revision'],
                         'projectRevision':created['projectRevision'],'content':content})
        assert api('/api/workspace?branch=main')['content']==original['content'],'Cross-branch contamination'
        if host:
            assert 'ready' in docker('exec',name,'vita-codex-client','--check')
            native=subprocess.run([*prefix,'exec','-i','-w',created['worktree'],name,
                'vita-codex-client','exec','--sandbox','read-only','--model','synthetic-model',
                '-c','model_reasoning_effort="high"','--output-last-message','.vita/tmp/host-reply.txt','-'],
                input='Synthetic prompt from actual image',text=True,capture_output=True,timeout=45)
            assert native.returncode==0,native.stderr
            output=json.loads(docker('exec','-w',created['worktree'],name,'python','-c',
                'from pathlib import Path;print(Path(".vita/tmp/host-reply.txt").read_text())'))
            assert output['source']==content and output['prompt']=='Synthetic prompt from actual image'
            assert 'sections/details.tex' in output['inputFiles']
            assert 'synthetic-model' in output['args'] and 'model_reasoning_effort="high"' in output['args']
            # Exercise the bundled backend itself, not only the transport shim.
            native_code='''import json
from vita.helpers.llm import _call_codex_cli
value=json.loads(_call_codex_cli('Synthetic system','Synthetic native provider call','synthetic-model',response_schema={'type':'object'},reasoning_effort='high'))
assert value['schema']=={'type':'object'}
assert 'Synthetic native provider call' in value['prompt']
assert 'model_reasoning_effort="high"' in value['args']
print('Native Vita CV schema/host transport verified')
'''
            assert 'verified' in docker('exec','-w',created['worktree'],name,'python','-c',native_code)
        for engine in ('pdflatex','xelatex','lualatex'):
            preview=api('/api/pdf',{'branch':'synthetic-role','engine':engine,'side':'current'})
            with opener.open(url+preview['url']) as response: pdf=response.read()
            from pypdf import PdfReader
            reader=PdfReader(BytesIO(pdf));assert len(reader.pages)==1
            assert 'Synthetic reviewed result.' in reader.pages[0].extract_text()
            assert 'Nested included paragraph.' in reader.pages[0].extract_text()
            (args.artifacts/(engine+'.pdf')).write_bytes(pdf)
        saved=api('/api/pdf-save',{'branch':'synthetic-role','id':preview['id']})
        assert saved['saved']
        assert execute('from pathlib import Path;print(any(Path(".git/vita-tree/worktrees").rglob("*.pdf")))')=='True'
        execute('from pathlib import Path; p=Path('+repr(created['worktree'])+'); (p/"cover-letter.tex").write_text(r"\\documentclass{article}\\begin{document}Synthetic cover letter.\\end{document}")')
        cover=api('/api/pdf',{'branch':'synthetic-role','engine':'pdflatex','side':'current','document':'cover'})
        with opener.open(url+cover['url']) as response:cover_bytes=response.read()
        (args.artifacts/'cover.pdf').write_bytes(cover_bytes)
        assert 'Synthetic cover letter.' in PdfReader(BytesIO(cover_bytes)).pages[0].extract_text()
        assert api('/api/pdf-save',{'branch':'synthetic-role','id':cover['id']})['saved']
        from playwright.sync_api import sync_playwright,expect
        with sync_playwright() as pw:
            browser=pw.chromium.launch();page=browser.new_page();errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(url+'/?branch=synthetic-role')
            expect(page.locator('#branch-title')).to_have_text('synthetic-role',timeout=60000)
            expect(page.locator('#current-document')).to_contain_text('Synthetic reviewed result.',timeout=60000)
            expect(page.locator('#workflow-graph .dag-node')).to_have_count(6)
            for theme in ('light','dark'):
                if page.locator('html').get_attribute('data-theme')!=theme:
                    page.get_by_role('button',name=f'Switch to {theme} mode',exact=True).click()
                page.screenshot(path=str(args.artifacts/(theme+'.png')),full_page=True,animations='disabled')
            page.get_by_role('tab',name='PDF preview',exact=True).click()
            page.get_by_role('button',name='Create PDF previews',exact=True).click()
            expect(page.locator('#current-pdf .textLayer')).to_contain_text('Synthetic reviewed result.',timeout=180000)
            page.screenshot(path=str(args.artifacts/'pdf.png'),full_page=True)
            assert not errors,errors
            browser.close()
        docker('restart',name);token=ready()
        assert api('/api/workspace?branch=synthetic-role')['content']==content,'Draft lost after restart'
        # Actual selected-branch commit and push to a local bare remote.
        execute('''import subprocess
def git(*a):subprocess.run(['git',*a],check=True,stdout=subprocess.DEVNULL)
git('init','--bare','/tmp/synthetic-remote.git')
git('remote','add','origin','/tmp/synthetic-remote.git')
git('config','user.name','Synthetic User');git('config','user.email','tests@example.invalid')
''')
        review=api('/api/commit-preview',{'branch':'synthetic-role'})
        result=api('/api/commit-push',{'branch':'synthetic-role','review':review['review'],'message':'Save synthetic application'})
        assert result['pushed']
        refs=execute("import subprocess;print(subprocess.check_output(['git','--git-dir=/tmp/synthetic-remote.git','for-each-ref','--format=%(refname)'],text=True).strip())")
        assert refs=='refs/heads/synthetic-role',refs
        deadline=time.monotonic()+60
        health=docker('inspect',name,'--format','{{.State.Health.Status}}')
        while health!='healthy' and time.monotonic()<deadline:
            time.sleep(1)
            health=docker('inspect',name,'--format','{{.State.Health.Status}}')
        assert health=='healthy','Container health did not become healthy'
        docker('stop',name)
        # Refuse incompatible worktrees without pruning or rewriting pointers.
        docker('run','--rm','--mount',f'type=volume,source={volume},target=/workspace',args.image,
               'python','-c',"from pathlib import Path;p=Path('.git/worktrees/native');p.mkdir(parents=True);(p/'gitdir').write_text('Z:/synthetic-missing-project/.git')")
        rejected=subprocess.run([*prefix,'run','--rm','--mount',f'type=volume,source={volume},target=/workspace',args.image],
                                capture_output=True,text=True,timeout=30)
        assert rejected.returncode!=0 and 'separate container-owned clone' in rejected.stderr,rejected.stderr
        pointer=docker('run','--rm','--mount',f'type=volume,source={volume},target=/workspace',args.image,
                       'python','-c',"from pathlib import Path;print(Path('.git/worktrees/native/gitdir').read_text())")
        assert pointer=='Z:/synthetic-missing-project/.git'
        metadata={'image':args.image,'id':docker('image','inspect',args.image,'--format','{{.Id}}'),
                  'engines':['pdflatex','xelatex','lualatex'],'nativeArchitecture':docker('image','inspect',args.image,'--format','{{.Architecture}}'),
                  'checks':['nonroot','vita-cli','native-vita-build','create','save','branch-isolation','three-pdf-engines','pdf-export',
                            'nested-includes','cover-pdf-export','browser-themes','pdf-selectable-text','restart-persistence',
                            'selected-branch-local-push','incompatible-worktree-preserved','docker-health']}
        if host:metadata['checks'].append('actual-image-to-native-host-codex-fixture')
        (args.artifacts/'result.json').write_text(json.dumps(metadata,indent=2))
        print('PASS: actual image runtime, browser, Git, PDF and restart checks')
    finally:
        subprocess.run([*prefix,'rm','-f',name],capture_output=True)
        subprocess.run([*prefix,'volume','rm',volume],capture_output=True)
        if host:host.tearDown()


if __name__=='__main__':main()
