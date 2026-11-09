"""Local setup checks on disposable copies; never invoke an AI or installer."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .security import snapshot_excluded, redact

ENGINES = {'auto','pdflatex','xelatex','lualatex'}
MESSAGES = {
    'entry_missing': ('error','The CV entry file is missing or empty.','Place the complete CV project in this Git collection with main.tex at its root, alongside its local classes, styles, images and includes.'),
    'input_encoding': ('error','A source or project settings file is not UTF-8 text.','Save the entry, job description and JSON settings as UTF-8 in your editor, then check again. No file was converted.'),
    'entry_contract': ('error','AI preparation requires main.tex at the collection root.','Use main.tex and set tex_entry to main.tex in .vita/config.json. Other --file entries remain available for direct viewing and PDF previews.'),
    'cover_contract': ('error','The cover-letter entry setting is incompatible.','Set cover_tex_entry to cover-letter.tex in .vita/config.json.'),
    'configuration_invalid': ('error','Project settings could not be read.','Correct the JSON object and supported field types in the indicated .vita settings file. No settings were rewritten.'),
    'configuration_default': ('info','No project config.json was found; supported defaults will be used.','main.tex and cover-letter.tex are the default entry files. Existing direct LaTeX projects do not need to be reinitialized.'),
    'engine_missing': ('error','The selected TeX engine is unavailable.','Install that engine with MiKTeX or TeX Live, or choose another compatible installed engine. Restart Vita Tree after changing PATH, then check again. Vita Tree will not install it.'),
    'missing_package': ('error','A required TeX package or document class is unavailable.','Restore the project-local template file if it belongs to the template; otherwise install its package explicitly with your TeX distribution manager, then check again.'),
    'missing_file': ('error','A required project input is unavailable to the compiler.','Restore the include, image or other asset beside the template and ensure Git does not ignore it. Recheck the filename and letter case.'),
    'missing_font': ('error','A required font could not be loaded.','Install the template’s font explicitly or select a font already installed on this computer, then check again.'),
    'engine_mismatch': ('error','This template needs a different TeX engine.','Choose XeLaTeX or LuaLaTeX for fontspec/unicode-math templates, then check again.'),
    'compile_timeout': ('error','The restricted compilation exceeded its time limit.','Check the template for loops or expensive macros and verify the local TeX installation. No AI was called.'),
    'compile_failed': ('error','The captured LaTeX project could not produce a PDF.','Open the LaTeX source or PDF tools to investigate the template and installation. Structure limitations alone do not mean the TeX is invalid.'),
    'structure_limited': ('warning','Structure is an approximate preview of this template.','The compiler determines PDF validity. Use LaTeX editing and the PDF view for macros or included files that Structure cannot display.'),
    'compiled': ('info','The captured project compiled successfully.','Dependencies used by this compilation are available. This does not predict dependencies introduced by future AI output.'),
    'extract_only': ('info','Job requirements can run independently of CV compilation.','This step uses the job description. Check the CV setup before running steps that use the CV.'),
    'draft_changed': ('error','Project inputs changed or became unavailable during setup checks.','Reload the saved CV, job description and includes, resolve any file-access problem, then check again. Your edits were preserved and no AI was called.'),
}


def item(code, target=None, secrets=()):
    result = {'code':code}
    if isinstance(target,str) and re.fullmatch(r'[A-Za-z0-9_.+-]{1,100}',target) and redact(target,secrets)==target:
        result['target']=target
    return result


def public_result(value, secrets=()):
    """Do not expose compiler logs, arbitrary history fields, paths or source text."""
    if not isinstance(value,dict):return None
    checks=[]
    raw=value.get('checks')
    if not isinstance(raw,list):return None
    for entry in raw[:30]:
        if not isinstance(entry,dict) or entry.get('code') not in MESSAGES:continue
        clean=item(entry['code'],entry.get('target'),secrets)
        severity,message,action=MESSAGES[clean['code']]
        checks.append({**clean,'severity':severity,'message':message,'action':action})
    result={'ready':any(c['code'] in {'compiled','extract_only'} for c in checks) and not any(c['severity']=='error' for c in checks),'checks':checks}
    result['engine']=value.get('engine') if isinstance(value.get('engine'),str) and value['engine'] in ENGINES else 'auto'
    for key in ('revision','jobRevision'):
        v=value.get(key)
        result[key]=v if isinstance(v,str) and re.fullmatch('[a-f0-9]{64}',v) else None
    return result


def configuration(configs, entry='main.tex', selected=()):
    checks=[]
    values={}
    for name in ('config.json','extensions.json'):
        try:
            data=json.loads(configs.get(name,'{}'))
            if not isinstance(data,dict):raise ValueError()
            if name=='config.json':
                for key in ('tex_entry','cover_tex_entry','build_mode'):
                    if key in data and not isinstance(data[key],str):raise ValueError()
            else:
                routes=data.get('llm_providers',{})
                if not isinstance(routes,dict) or any(not isinstance(route,dict) or ('model' in route and not isinstance(route['model'],str)) for route in routes.values()):raise ValueError()
            values[name]=data
        except (ValueError,TypeError,RecursionError):checks.append(item('configuration_invalid',name))
    config=values.get('config.json',{})
    if entry!='main.tex' or config.get('tex_entry','main.tex')!='main.tex':checks.append(item('entry_contract'))
    if 'cover' in selected and config.get('cover_tex_entry','cover-letter.tex')!='cover-letter.tex':checks.append(item('cover_contract'))
    if 'config.json' not in configs:checks.append(item('configuration_default'))
    return checks


def compile_failure(error, secrets=()):
    """Interpret bounded compiler diagnostics, never AI provider stdout."""
    from .pdf import CompilationError
    if isinstance(error,subprocess.TimeoutExpired):return item('compile_timeout')
    if isinstance(error,CompilationError) and error.category in {'engine_missing','compile_timeout'}:
        return item(error.category)
    log=str(error)
    if re.search(r'(?:requires (?:either )?(?:XeTeX|XeLaTeX|LuaTeX|LuaLaTeX)|cannot-use-pdftex)',log,re.I):return item('engine_mismatch')
    missing=re.search(r"(?:File\s+[`'\"]|find file\s+[`'\"])([^\r\n`'\"]{1,200})[`'\"](?:\s+not found)?",log,re.I)
    if missing:
        name=missing[1].replace('\\','/').split('/')[-1]
        return item('missing_package' if name.lower().endswith(('.sty','.cls','.def','.fd','.clo')) else 'missing_file',name,secrets)
    if re.search(r'font.*(?:cannot be found|not found|not loadable)',log,re.I):return item('missing_font')
    return item('compile_failed')


def copy_project(origin, target):
    from .workspace import safe_path
    import os
    total=count=0
    copied={}
    for base,dirs,files in os.walk(origin,followlinks=False):
        relative=Path(base).relative_to(origin)
        dirs[:]=[name for name in dirs if not snapshot_excluded((relative/name).as_posix())]
        for name in dirs: safe_path(origin,(relative/name).as_posix())
        for name in files:
            rel=(relative/name).as_posix()
            if snapshot_excluded(rel):continue
            source=safe_path(origin,rel)
            total+=source.stat().st_size;count+=1
            if total>200_000_000 or count>10000:raise ValueError('The project exceeds the preflight snapshot limits')
            destination=safe_path(target,rel);destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,destination)
            copied[rel]=hashlib.sha256(destination.read_bytes()).hexdigest()
    return copied


def check_project(folder, configs, engine='auto', entry='main.tex', selected=(), revision=None, job_revision=None, scratch=None, secrets=(), expected_assets=None):
    from .pdf import compile_document
    from .workspace import read_text,safe_path
    from .latex import parse_document
    if not isinstance(engine,str) or engine not in ENGINES:raise ValueError('Choose Automatic, pdflatex, xelatex or lualatex for setup checks.')
    checks=configuration(configs,entry,selected)
    if scratch is not None:Path(scratch).mkdir(parents=True,exist_ok=True)
    if 'extract' in selected and not set(selected)-{'extract','validating'}:
        return public_result(dict(checks=[*checks,item('extract_only')],engine=engine,revision=revision,jobRevision=job_revision),secrets)
    source=read_text(safe_path(folder,entry))
    if not source.strip():checks.append(item('entry_missing'))
    else:
        preview=parse_document(source)
        if preview['warnings'] or preview['error']:checks.append(item('structure_limited'))
    chosen=engine if engine!='auto' else ('xelatex' if any(x in source for x in ('fontspec','polyglossia','unicode-math')) else 'pdflatex')
    if not any(MESSAGES[c['code']][0]=='error' and not (c['code']=='entry_contract' and entry!='main.tex') for c in checks):
        with tempfile.TemporaryDirectory(prefix='check-',dir=scratch) as tmp:
            root=Path(tmp);target=root/'project';target.mkdir()
            copied=copy_project(folder,target)
            from .workspace import ConflictError,digest
            assets=lambda data:{k:v for k,v in data.items() if k not in {'main.tex','job.md','cover-letter.tex'}}
            if (revision and digest(read_text(safe_path(target,entry)))!=revision) or (expected_assets is not None and assets(copied)!=assets(expected_assets)):
                raise ConflictError('The project changed while its setup snapshot was captured. Check the new draft again.')
            try:
                compile_document(target,entry,engine=chosen,output=root/'output')
                checks.append(item('compiled'))
            except (ValueError,OSError,subprocess.SubprocessError) as error:
                checks.append(compile_failure(error,secrets))
    return public_result(dict(checks=checks,engine=chosen,revision=revision,jobRevision=job_revision),secrets)


def project_state(workspace, name):
    from .workspace import digest,read_text,safe_path
    from .server import run_git
    location=workspace.location(name)
    commit=workspace.head(name)
    configs={}
    for origin in (workspace.repository,location):
        if origin:
            for filename in ('config.json','extensions.json'):
                path=safe_path(origin,'.vita/'+filename)
                if path.is_file():configs[filename]=read_text(path)
    if location is None:
        for filename in ('config.json','extensions.json'):
            content=workspace.committed(commit,'.vita/'+filename)
            if content:configs[filename]=content
    assets={};total=0
    if location:
        names=set(run_git(location,'ls-files','-z','--cached','--others','--exclude-standard',strip=False).split('\0'))-{''}
        if len(names)>10000:raise ValueError('The project exceeds the preflight file limit')
        for name_in_repo in sorted(names):
            if snapshot_excluded(name_in_repo):continue
            path=safe_path(location,name_in_repo)
            if path.is_file():
                total+=path.stat().st_size
                if total>200_000_000:raise ValueError('The project exceeds the preflight snapshot limit')
                assets[name_in_repo]=hashlib.sha256(path.read_bytes()).hexdigest()
    source=read_text(safe_path(location,workspace.document_path)) if location else workspace.committed(commit,workspace.document_path)
    job=read_text(safe_path(location,'job.md')) if location else workspace.committed(commit,'job.md')
    return dict(commit=commit,source=digest(source),job=digest(job),assets=assets,configs=configs),location


def check_workspace(workspace,name,revision=None,job_revision=None,engine='auto',selected=()):
    from .workspace import ConflictError
    from .pdf import export_snapshot
    from .security import credential_name
    import os
    with workspace.lock:
        workspace.busy(name)
        if not isinstance(engine,str) or engine not in ENGINES:raise ValueError('Choose a supported TeX engine for setup checks.')
        if name in workspace._setup_checks:raise ConflictError('Setup checks are already running for this application.')
        try:captured,location=project_state(workspace,name)
        except UnicodeError:
            return public_result(dict(checks=[item('input_encoding')],engine=engine))
        if (revision is not None and revision!=captured['source']) or (job_revision is not None and job_revision!=captured['job']):
            raise ConflictError('The saved draft changed. Reload before checking setup.')
        workspace._setup_checks.add(name)
        workspace._previewing[name]=workspace._previewing.get(name,0)+1
        secrets=[v for k,v in os.environ.items() if credential_name(k)]+[v['key'] for v in workspace.connections.items.values()]+list(workspace.inspector.secrets)
    try:
        scratch=workspace.root/'preflight';scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='snapshot-',dir=scratch) as tmp:
            folder=Path(tmp);export_snapshot(workspace.repository,captured['commit'],folder,location)
            result=check_project(folder,captured['configs'],engine,workspace.document_path,selected,captured['source'],captured['job'],scratch,secrets,captured['assets'] if location else None)
        with workspace.lock:
            fresh,_=project_state(workspace,name)
            if fresh!=captured:raise ConflictError('The project changed during setup checks. Your edits were preserved; check the new draft again.')
        return result
    finally:
        with workspace.lock:
            workspace._setup_checks.discard(name)
            count=workspace._previewing[name]-1
            if count:workspace._previewing[name]=count
            else:
                workspace._previewing.pop(name)
                if name in workspace._release_requested:workspace.release_worktree(name)
