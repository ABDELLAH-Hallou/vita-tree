"""Verify Tree's snapshot retains Vita CV's real nested include context contract."""
import argparse
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from test_includes import MAIN,EXPERIENCE,EDUCATION,DETAILS
from support import init_repo,git,cleanup_repo
from vita_tree.workspace import Workspace,digest
from vita_tree.pdf import export_snapshot


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--vita-source',type=Path);args=parser.parse_args()
    if args.vita_source:sys.path.insert(0,str(args.vita_source.resolve()))
    from vita.helpers.context_builder import cv_source_files,cv_source_context
    temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=ROOT)
    previous=Path.cwd()
    try:
        root=init_repo(Path(temp.name));(root/'sections').mkdir()
        for path,value in {'main.tex':MAIN,'sections/experience.tex':EXPERIENCE,'education.tex':EDUCATION,'sections/details.tex':DETAILS}.items():
            (root/path).write_text(value,encoding='utf-8')
        git(root,'add','.');git(root,'commit','-m','Synthetic includes')
        workspace=Workspace(root);snapshot=workspace.create('master','nested','Synthetic job',digest(MAIN))
        location=Path(snapshot['worktree'])
        changed='Unique synthetic nested context.\n'
        (location/'sections/details.tex').write_text(changed,encoding='utf-8')
        graph=workspace.snapshot('nested');file=next(item for item in graph['files'] if item['path']=='sections/details.tex')
        assert file['content']==changed
        stage=root/'.git/contract-snapshot'
        export_snapshot(root,workspace.head('nested'),stage,location)
        os.chdir(stage)
        files=cv_source_files('main.tex')
        assert set(files)=={file['path'] for file in graph['files']},files
        assert files['sections/details.tex'].strip()==changed.strip(),files
        assert r'\input{sections/experience}' in files['main.tex'],'Tree flattened an include'
        context=cv_source_context('main.tex')
        assert 'Unique synthetic nested context.' in context
        assert '==== FILE: sections/details.tex ====' in context
        print('PASS: real Vita CV resolver receives unchanged include commands and matching nested draft files from Tree snapshots; no provider called.')
    finally:
        os.chdir(previous);cleanup_repo(temp)


if __name__=='__main__':main()
