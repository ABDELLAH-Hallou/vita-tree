"""Private factual-review payloads. Never send these to diagnostic exports."""
import difflib
import re

VERSION = 'factual-changes/1'
STEPS = {'adapt', 'cover'}
REASONS = {
    'ambiguous_acronym': 'The acronym’s intended meaning is not verified.',
    'date_interpretation': 'The intended date or date range is not verified.',
    'credential_status': 'The qualification or its current status is not verified.',
    'metric_or_unit': 'The quantity, currency, or unit is not verified.',
    'unverified_semantic_change': 'The source does not establish that the new wording has the same meaning.',
    'formatting_semantics_unverified': 'Formatting inside LaTeX may change the meaning.',
    'whitespace_only': 'Only outer whitespace changed.',
}


def validate(report):
    if (not isinstance(report, dict) or report.get('contract_version') != VERSION
            or report.get('step') not in STEPS
            or not re.fullmatch(r'fc-[a-f0-9]{64}', str(report.get('revision', '')))
            or report.get('status') not in {'ready', 'confirmation_required', 'applied', 'approved', 'rejected'}
            or report.get('application_status') not in {'applied', 'not_applied'}):
        raise ValueError('Unsupported factual-change contract. Update Vita CV and regenerate.')
    if not isinstance(report.get('document'), str) or len(report['document'].encode()) > 2_000_000:
        raise ValueError('Invalid factual-change document')
    changes, facts = report.get('changes'), report.get('source_facts')
    if not isinstance(changes, list) or len(changes) > 500 or not isinstance(facts, list):
        raise ValueError('Invalid factual-change items')
    ids = set()
    for item in changes:
        if (not isinstance(item, dict) or not re.fullmatch(r'change-[a-f0-9]{64}', str(item.get('id', '')))
                or item['id'] in ids or item.get('operation') not in {'replace', 'insert', 'delete'}
                or item.get('kind') not in {'wording', 'semantic_or_factual'}
                or item.get('reason') not in REASONS
                or item.get('verification') not in {'host_verified', 'confirmation_required'}
                or any(not isinstance(item.get(k), str) for k in ('original', 'proposed'))):
            raise ValueError('Invalid factual-change item')
        ids.add(item['id'])
    return report


def original(report):
    return (report['target_before'] or '') if report['step'] == 'adapt' else '\n'.join(
        s['content'] for s in report['candidate_sources']['sources'] if s['kind'] == 'cv')


def resolve_document(report, decisions):
    """Apply every explicit decision to the host diff, never search/replace prose."""
    validate(report)
    if not isinstance(decisions, list) or len(decisions) != len(report['changes']):
        raise ValueError('Choose accept, reject, or edit for every change.')
    by_id = {}
    for value in decisions:
        if (not isinstance(value, dict) or set(value) - {'id', 'action', 'text'}
                or not isinstance(value.get('id'), str) or value['id'] in by_id
                or not isinstance(value.get('action'), str) or value['action'] not in {'accept', 'reject', 'edit'}
                or (value['action'] == 'edit' and (not isinstance(value.get('text'), str) or len(value['text'].encode()) > 2_000_000))):
            raise ValueError('Invalid factual-review decision.')
        by_id[value.get('id')] = value
    if set(by_id) != {item['id'] for item in report['changes']}:
        raise ValueError('The factual-review items changed. Reload this review.')
    # A fully rejected letter preserves the previous target, rather than turning
    # CV source lines into a letter. There may be no previous letter at all.
    if report['step'] == 'cover' and all(v['action'] == 'reject' for v in decisions):
        return report['target_before'], True
    if all(v['action'] == 'accept' for v in decisions):
        return report['document'], False
    old = original(report).removesuffix('\n').split('\n')
    new = report['document'].removesuffix('\n').split('\n')
    chunks, index = [], 0
    for tag, start, end, out_start, out_end in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag == 'equal':
            chunks.extend(old[start:end])
            continue
        item = report['changes'][index]; index += 1
        if (item['operation'], item['original'], item['proposed']) != (tag, '\n'.join(old[start:end]), '\n'.join(new[out_start:out_end])):
            raise ValueError('The host diff changed. Regenerate this proposal.')
        choice = by_id[item['id']]
        if choice['action'] == 'accept':
            chunks.extend(new[out_start:out_end])
        elif choice['action'] == 'reject':
            chunks.extend(old[start:end])
        elif choice['text']:
            chunks.extend(choice['text'].split('\n'))
    if index != len(report['changes']):
        raise ValueError('The host diff changed. Regenerate this proposal.')
    # Retain the source's terminal newline when rejecting the entire CV diff.
    if all(v['action'] == 'reject' for v in decisions):
        return report['target_before'], False
    return '\n'.join(chunks) + ('\n' if report['document'].endswith('\n') else ''), False
