"""Restricted, snapshot-bound template compatibility evidence; no AI calls."""
import argparse
import datetime
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from template_matrix import (CORPUS, ENGINES, after_expectations, apply_edits, hashes,
                             load_corpus, make_repository, normalized, sha, sources, structure, sweep_leaves)
from vita_tree.pdf import compile_document
from vita_tree.preflight import compile_failure, public_result
from vita_tree.security import compiler_environment, engine_executable
from vita_tree.observability import Diagnostics
from vita_tree.workspace import Workspace

DEPENDENCIES = {'engine_missing', 'missing_package', 'missing_file', 'missing_font', 'engine_mismatch'}


def command_version(command, flag='--version'):
    if not command:
        return None
    result = subprocess.run([str(command), flag], capture_output=True, timeout=15, stdin=subprocess.DEVNULL)
    lines = (result.stdout + result.stderr).decode('utf-8', errors='replace').splitlines()
    return next((line for line in lines if 'version' in line.lower() or 'TeX' in line), lines[0] if lines else None)


def missing_miktex_format(engine, folder, env):
    """Inspect installed formats; never build one or permit a package installer."""
    try:
        probe = engine_executable('kpsewhich', folder, env)
    except ValueError:
        return False  # No evidence: let the compiler report its actual failure.
    engine_name = {'pdflatex': 'pdftex', 'xelatex': 'xetex', 'lualatex': 'luahbtex'}[engine]
    result = subprocess.run([probe, '--engine='+engine_name, '--format=fmt', engine+'.fmt'], cwd=folder, env=env,
                            stdin=subprocess.DEVNULL, capture_output=True, timeout=15)
    return result.returncode == 1 and not result.stdout.strip()


def package_versions(log):
    """Read LaTeX's own listfiles block; never publish arbitrary compiler prose."""
    lines = log.split('*File List*')[-1].split('***********')[0].splitlines() if '*File List*' in log else []
    return [line.strip() for line in lines if re.fullmatch(r'\s*[A-Za-z0-9_.+-]+\.(?:cls|sty|clo|def|fd|ldf|cfg|fontspec)\s+\d{4}[/.-]\d{2}[/.-]\d{2}[A-Za-z0-9_ .,():+\[\]-]*', line)]


def embedded_fonts(pdf):
    from pypdf import PdfReader
    result = {}
    for page in PdfReader(pdf).pages:
        resources = page.get('/Resources')
        fonts = resources.get_object().get('/Font') if resources else None
        for value in (fonts.get_object().values() if fonts else ()):
            font = value.get_object()
            descendants = font.get('/DescendantFonts') or [font]
            for child in descendants:
                child = child.get_object()
                descriptor = (child.get('/FontDescriptor') or {}).get_object() if child.get('/FontDescriptor') else {}
                blob = next((descriptor[key].get_object().get_data() for key in ('/FontFile', '/FontFile2', '/FontFile3') if key in descriptor), None)
                name = str(child.get('/BaseFont', font.get('/BaseFont', 'unknown')))
                result[name] = {'name': name, 'embeddedSubsetSha256': sha(blob) if blob else None}
    return list(result.values())


def inspect_boxes(xml, expectation):
    """Check every page, content anchors, same-page associations and word bounds.

    Bounding boxes detect gross layout faults, not all visual/semantic defects.
    Contact sheets and original-resolution page PNGs remain a required review.
    """
    root = ET.fromstring(xml)
    pages = []
    problems = []
    for number, page in enumerate(root.findall('.//{*}page'), 1):
        width, height = float(page.attrib['width']), float(page.attrib['height'])
        words = []
        for word in page.findall('.//{*}word'):
            box = [float(word.attrib[key]) for key in ('xMin', 'yMin', 'xMax', 'yMax')]
            value = ''.join(word.itertext())
            words.append((box, value))
            if box[0] < -.5 or box[1] < -.5 or box[2] > width+.5 or box[3] > height+.5:
                problems.append({'kind': 'clipping', 'page': number, 'text': value})
        # A sweep over y-sorted words avoids a quadratic all-document comparison.
        ordered = sorted(words, key=lambda word: word[0][1])
        for index, (a, text) in enumerate(ordered):
            for b, other in ordered[index+1:]:
                if b[1] >= a[3]:
                    break
                dx, dy = min(a[2], b[2])-max(a[0], b[0]), min(a[3], b[3])-max(a[1], b[1])
                area = min((a[2]-a[0])*(a[3]-a[1]), (b[2]-b[0])*(b[3]-b[1]))
                if dx > 2 and dy > 2 and dx*dy > .2*area:
                    problems.append({'kind': 'overlap', 'page': number, 'text': text, 'other': other})
        content = normalized(' '.join(value for _, value in words))
        if not words:
            problems.append({'kind': 'empty_page', 'page': number})
        for marker in expectation.get('perPage', {}).get(str(number), []):
            if normalized(marker) not in content:
                problems.append({'kind': 'page_omission', 'page': number, 'text': marker})
        pages.append({'number': number, 'width': width, 'height': height, 'words': len(words), 'text': content})
    whole = ' '.join(page['text'] for page in pages)
    for marker in expectation['required']:
        if normalized(marker) not in whole:
            problems.append({'kind': 'omission', 'text': marker})
    for association in expectation.get('associations', []):
        if not any(all(normalized(text) in page['text'] for text in association) for page in pages):
            problems.append({'kind': 'orphaned_association', 'texts': association})
    return pages, problems


def compile_case(output, fixture, files, engine, snapshot, tools):
    folder = output/fixture['id']/engine/snapshot
    inputs = folder/'input'
    inputs.mkdir(parents=True)
    for name, value in files.items():
        target = inputs/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value.encode('utf-8'))
    captured = hashes(files)
    result = {'snapshot': snapshot, 'inputHashes': captured, 'restrictions': [], 'pages': []}
    run = subprocess.run

    def checked_run(args, **kwargs):
        if '-interaction=nonstopmode' in args:
            assert '-no-shell-escape' in args and not kwargs.get('shell')
            assert not any(arg in {'-shell-escape', '--enable-installer', '--enable-write18'} for arg in args)
            if result.get('engineVersion') and 'MiKTeX' in result['engineVersion']:
                assert '--disable-installer' in args and '--disable-write18' in args
            result['restrictions'] = [arg for arg in args[1:] if not arg.startswith('-output-directory=')]
        return run(args, **kwargs)

    try:
        env = compiler_environment(inputs, folder/'pdf')
        try:
            executable = engine_executable(engine, inputs, env)
            result['engineVersion'] = command_version(executable)
            if 'MiKTeX' in (result['engineVersion'] or '') and missing_miktex_format(engine, inputs, env):
                result.update(status='dependency_missing', category='format_missing', diagnostic={
                    'code': 'format_missing', 'severity': 'error', 'title': 'Installed TeX format is missing',
                    'message': engine+'.fmt is not available in this MiKTeX installation.',
                    'action': 'Use MiKTeX Console to inspect and explicitly build the installed engine format, then rerun. Vita Tree did not install or generate it.'})
                return result
        except ValueError:
            pass  # compile_document returns the typed, actionable engine error.
        with patch('vita_tree.pdf.subprocess.run', side_effect=checked_run):
            compiled = compile_document(inputs, fixture['entry'], engine, folder/'pdf')
        result.update(status='compiled', category='compiled', pdf=compiled['pdf'].relative_to(output).as_posix(),
                      pdfSha256=sha(compiled['pdf'].read_bytes()), warnings=compiled['warnings'])
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        diagnostic = compile_failure(error)
        result.update(status='dependency_missing' if diagnostic['code'] in DEPENDENCIES else 'compile_failed',
                      category=diagnostic['code'], diagnostic=public_result({'checks': [diagnostic], 'engine': engine})['checks'][0])
        return result
    finally:
        actual = {name: sha((inputs/name).read_bytes()) for name in files}
        assert actual == captured, 'Compilation modified captured source files'
        result['sourcePreserved'] = True
    log = (folder/'pdf'/Path(fixture['entry']).with_suffix('.log')).read_text(encoding='utf-8', errors='replace')
    result['packages'] = package_versions(log)
    assert result['packages'], 'Fixture listfiles did not record package versions'
    result['fonts'] = embedded_fonts(compiled['pdf'])
    if not tools['pdftotext'] or not tools['pdftoppm']:
        result.update(status='inspection_dependency_missing', category='poppler_missing')
        return result
    xml = folder/'pages.xml'
    subprocess.run([tools['pdftotext'], '-bbox-layout', '-enc', 'UTF-8', str(compiled['pdf']), str(xml)],
                   check=True, capture_output=True, timeout=30)
    pages, problems = inspect_boxes(xml.read_bytes(), fixture['pdf'])
    if len(pages) != fixture['engines'][engine]['pages']:
        problems.append({'kind': 'page_count', 'expected': fixture['engines'][engine]['pages'], 'actual': len(pages)})
    for warning in compiled['warnings']:
        if 'Overfull' in warning or 'Missing character' in warning:
            problems.append({'kind': 'compiler_layout_warning', 'text': warning})
    images = folder/'pages'
    images.mkdir()
    subprocess.run([tools['pdftoppm'], '-png', '-r', '96', str(compiled['pdf']), str(images/'page')],
                   check=True, capture_output=True, timeout=90)
    pngs = sorted(images.glob('page-*.png'), key=lambda path: int(path.stem.rsplit('-', 1)[1]))
    assert len(pngs) == len(pages), 'Not every PDF page was rendered'
    for page, path in zip(pages, pngs):
        page.pop('text')  # Sources/markers are synthetic, but reports need no document body.
        page.update(image=path.relative_to(output).as_posix(), imageSha256=sha(path.read_bytes()), visualReview='pending')
    result.update(pages=pages, problems=problems, status='layout_defect' if problems else 'verified_automatically')
    return result


def run_matrix(output, engines, selected=None, require_dependencies=False):
    corpus = load_corpus()
    assert not selected or set(selected) <= {fixture['id'] for fixture in corpus['fixtures']}, 'Unknown fixture'
    assert not output.exists(), 'Use a new output directory; never overwrite captured evidence'
    output.mkdir(parents=True)
    tools = {name: shutil.which(name) for name in ('pdftotext', 'pdftoppm')}
    report = {'schemaVersion': 1, 'corpusVersion': corpus['corpusVersion'], 'corpusSha256': sha((CORPUS/'manifest.json').read_bytes()),
              'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'python': platform.python_version(), 'platform': platform.system(),
              'treeCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'adapterHashes': {name: sha((ROOT/'src/vita_tree'/name).read_bytes()) for name in ('latex.py', 'includes.py', 'pdf.py', 'workspace.py', 'security.py', 'static/app.js')},
              'harnessHashes': {name: sha((ROOT/'tests'/name).read_bytes()) for name in ('run_template_matrix.py', 'template_matrix.py')},
              'toolVersions': {name: command_version(path, '-v') for name, path in tools.items()}, 'results': [],
              'limits': ['Synthetic layouts only; no third-party original-PDF design fidelity claim.',
                         'Word boxes and markers do not prove full semantic reading order or typography fidelity.',
                         'Every page is rasterized. Human visual review is separately recorded against page hashes.']}
    failed = False
    for fixture in corpus['fixtures']:
        if selected and fixture['id'] not in selected:
            continue
        entry = {'id': fixture['id'], 'fixtureVersion': fixture['version'], 'structure': fixture['structure']['status'],
                 'limits': fixture['limits'], 'before': hashes(sources(fixture)), 'engines': {}}
        report['results'].append(entry)
        phase = 'structure'
        try:
            original = sources(fixture)
            documents, graph = structure(fixture, original)
            entry.update(sweep_leaves(documents, original), includeDiagnostics=graph['diagnostics'])
            phase = 'source_map'
            repo = make_repository(output/fixture['id']/'repository', fixture)
            workspace = Workspace(repo, diagnostics=Diagnostics(repo/'.git/test-logs'))
            try:
                current, edits = apply_edits(workspace, fixture)
                entry.update(after=hashes(current), edits=edits)
            finally:
                workspace.close()
                workspace.diagnostics.close()
            structure(after_expectations(fixture), current)
            phase = 'compiler_or_inspection'
            for engine in engines:
                if engine not in fixture['engines']:
                    entry['engines'][engine] = {'status': 'not_in_fixture_contract'}
                    continue
                outcomes = []
                for name, files, expected in (('before', original, fixture), ('after', current, after_expectations(fixture))):
                    result = compile_case(output, expected, files, engine, name, tools)
                    outcomes.append(result)
                    wanted = fixture['engines'][engine]['status']
                    if wanted != 'success' and result['category'] == wanted:
                        result['status'] = 'expected_diagnostic'
                    elif result['status'] in {'dependency_missing', 'inspection_dependency_missing'}:
                        failed |= require_dependencies
                    elif result['status'] != 'verified_automatically':
                        failed = True
                entry['engines'][engine] = outcomes
                print(f"{fixture['id']} / {engine}: " + ', '.join(item['status'] for item in outcomes), flush=True)
        except Exception as error:
            failed = True
            # Fixed category, no arbitrary local exception/source text in evidence.
            entry.update(status='product_or_matrix_defect', category=getattr(error, 'category', phase+'_defect'), errorType=type(error).__name__)
            print(f"FAIL: {fixture['id']}: {error}", file=sys.stderr, flush=True)
        (output/'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    report['automatedChecksPassed'] = not failed
    (output/'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--engines', nargs='+', choices=ENGINES, default=list(ENGINES))
    parser.add_argument('--fixtures', nargs='+')
    parser.add_argument('--require-dependencies', action='store_true')
    args = parser.parse_args()
    report = run_matrix(args.output.resolve(), args.engines, args.fixtures, args.require_dependencies)
    raise SystemExit(not report['automatedChecksPassed'])


if __name__ == '__main__':
    main()
