"""Harmless native TeX canaries. Never read real host files or run external commands."""
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from pypdf import PdfReader
from vita_tree.pdf import compile_document
from vita_tree.security import compiler_environment,engine_executable


def main():
    artifacts=ROOT/'.test-artifacts';artifacts.mkdir(exist_ok=True)
    results=[]
    with tempfile.TemporaryDirectory(dir=artifacts,prefix='tex-security-') as name:
        root=Path(name);stage=root/'stage';stage.mkdir();outside=root/'canary.tex';outside.write_text('SYNTHETICEXTERNALCANARY',encoding='utf-8')
        def build(source,engine='pdflatex'):
            (stage/'main.tex').write_text(source,encoding='utf-8')
            output=stage/('output-'+engine)
            built=compile_document(stage,'main.tex',engine=engine,output=output)
            return ''.join(page.extract_text() or '' for page in PdfReader(built['pdf']).pages),built
        ordinary=r'\documentclass{article}\begin{document}Synthetic readable PDF.\end{document}'
        text,normal=build(ordinary);assert 'Synthetic readable PDF.' in text
        shutil.copyfile(normal['pdf'],artifacts/'security-clean.pdf')
        results.append({'boundary':'normal_selectable_pdf','result':'passed','engine':normal['engine']})
        # The command is a synthetic name which cannot invoke an installed program.
        # A forged first line asks for shell escape; the engine must ignore it.
        source='%&pdflatex --shell-escape\n'+ordinary.replace(r'\begin{document}',r'\begin{document}\immediate\write18{vita_tree_synthetic_command_never_installed}')
        text,_=build(source);assert 'Synthetic readable PDF.' in text
        log=(stage/'output-pdflatex/main.log').read_text(encoding='utf-8',errors='replace')
        assert 'runsystem(vita_tree_synthetic_command_never_installed)...disabled' in log.replace('\n','') or 'disabled' in log.lower()
        results.append({'boundary':'shell_and_first_line_flags','result':'passed'})
        source=ordinary.replace('Synthetic readable PDF.',r'\input{'+outside.as_posix()+'}')
        try:text,_=build(source);read='SYNTHETICEXTERNALCANARY' in text
        except ValueError:read=False
        # TeX Live 2026 explicitly removed Kpathsea openin_any enforcement. The
        # result is evidence, not an assertion that TeX is an OS file sandbox.
        environment=compiler_environment(stage,stage/'output-pdflatex')
        import subprocess
        version=subprocess.run([engine_executable('pdflatex',stage,environment),'--version'],env=environment,capture_output=True,timeout=10).stdout.decode(errors='replace').splitlines()[0]
        if 'MiKTeX' in version:assert not read
        results.append({'boundary':'native_external_file_read','result':'not_contained' if read else 'blocked_in_this_probe','engineVersion':version})
        write_marker=root/'outside-write-canary.txt'
        source=ordinary.replace('Synthetic readable PDF.',r'\newwrite\auditout\immediate\openout\auditout='+write_marker.as_posix()+r' \immediate\write\auditout{SYNTHETICWRITE}\immediate\closeout\auditout')
        try:build(source)
        except ValueError:pass
        assert not write_marker.exists()
        results.append({'boundary':'native_external_file_write','result':'blocked_in_this_probe'})
        # Local includes remain usable under restrictions.
        (stage/'included.tex').write_text('SYNTHETICLOCALINCLUDE',encoding='utf-8')
        text,_=build(ordinary.replace('Synthetic readable PDF.',r'\input{included.tex}'));assert 'SYNTHETICLOCALINCLUDE' in text
        results.append({'boundary':'local_include','result':'passed'})
        # A missing/unusable Lua installation is reported, never called a passed
        # Lua security probe. Environment filtering is tested independently.
        try:
            text,_=build(ordinary,engine='lualatex')
        except ValueError:
            results.append({'boundary':'lua_native_checks','result':'unavailable_benign_compile_failed'})
        else:
            from unittest.mock import patch
            import os
            with patch.dict(os.environ,{'VITA_TEST_COMPILER_CREDENTIAL':'SYNTHETICLUACREDENTIAL'}):
                text,_=build(ordinary.replace('Synthetic readable PDF.',r'\directlua{tex.sprint(os.getenv("VITA_TEST_COMPILER_CREDENTIAL") or "ABSENT")}'),engine='lualatex')
            assert 'SYNTHETICLUACREDENTIAL' not in text
            results.append({'boundary':'lua_environment_credential','result':'passed'})
    (artifacts/'security-tex-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    for item in results:print(item['boundary']+': '+item['result'])


if __name__=='__main__':main()
