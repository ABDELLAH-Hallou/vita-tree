"""Backend-owned validation and explicit human decisions; never calls an AI."""
import json
from pathlib import Path
import sys

try:
    from .factual_contract import resolve_document
except ImportError:
    from factual_contract import resolve_document


def capture(step, execution_id):
    path = Path('.vita/results') / (step + '.facts.json')
    if step not in {'adapt', 'cover'} or not path.exists():
        return
    from vita.helpers import factual_changes as facts
    report = facts.load(step)  # Full backend schema, source and host-diff integrity.
    if report['status'] == 'confirmation_required':
        facts._current(report)
    output = path.with_name('tree-' + step + '.facts.json')
    output.write_text(json.dumps({'schemaVersion': 1, 'executionId': execution_id, 'report': report}), encoding='utf-8')


def decide(request):
    from vita.helpers import factual_changes as facts
    step = request['step']
    report = facts.load(step)
    if report['revision'] != request['revision'] or report['status'] != 'confirmation_required':
        raise ValueError('The unresolved revision changed')
    facts._current(report)
    document, omitted = resolve_document(report, request['decisions'])
    # The original revision remains archived, with an explicit rejection if any
    # part was changed. A new revision is reviewed as the complete chosen text.
    if document == report['document']:
        resolved = facts.decide(step, report['revision'], True)
    else:
        facts.decide(step, report['revision'], False)
        if omitted or document == report['target_before']:
            resolved = facts.load(step)
        else:
            context = {k: report[k] for k in ('contract_version', 'step', 'target', 'candidate_sources', 'job_sha256', 'target_before')}
            amended = facts.propose(context, document)
            facts._current(amended)
            facts.save(amended)
            resolved = facts.decide(step, amended['revision'], True)
    return {'revision': resolved['revision'], 'omitted': omitted, 'report': resolved}


def main():
    # Private, typed IPC; stdout/stderr are not read as business evidence.
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    result = decide(request)
    Path(sys.argv[2]).write_text(json.dumps(result), encoding='utf-8')


if __name__ == '__main__':
    main()
