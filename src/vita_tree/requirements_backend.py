"""Typed adapter to Vita CV's canonical schema. Review operations never call AI."""
import json
import os
from pathlib import Path
import sys


def contract(request):
    from vita.helpers import env
    original = env.load_env
    env.load_env = lambda: {**original(), **os.environ}
    from vita.helpers import requirements as r
    data = request['definition']
    r.validate_revision(data)
    if data['source_text'] != request['source']:
        raise ValueError('The definition belongs to a different job description.')
    if request.get('approval') is not None:
        r.validate(request['approval'], r.APPROVAL_SCHEMA)
        if (request['approval']['source_sha256'] != r.digest(request['source']) or request['approval']['revision'] != data['revision']):
            raise ValueError('The approval does not match the definition.')
        r.save_revision(data)
        pointer = r.store_dir()/'approved'/(r.digest(request['source'])+'.json')
        pointer.parent.mkdir(parents=True, exist_ok=True)
        pointer.write_text(json.dumps(request['approval']), encoding='utf-8')
        r.approved_revision(request['source'])
    if request['action'] == 'edit':
        existing = {item['id']: item for item in data['requirements'] + data['employment_conditions']}
        units, conditions = [], []
        if not isinstance(request['items'], list) or len(request['items']) > 500:
            raise ValueError('Use at most 500 requirements.')
        for item in request['items']:
            # Existing identity is immutable; added concepts receive backend IDs.
            old = existing.get(item.get('id'))
            job_id = old['job_id'] if old else item['job_id']
            key = old['key'] if old else r.concept_key(item['criterion'])
            classification = item['classification']
            condition = item['category'] == 'employment_condition'
            unit = dict(id='req-' + r.digest(job_id + '\n' + key), job_id=job_id,
                        key=key, criterion=item['criterion'].strip(), category=item['category'],
                        classification=classification, importance=r.IMPORTANCE[classification],
                        weight=0 if condition else r.WEIGHTS[classification],
                        ambiguity=item['ambiguity'], source_refs=item['source_refs'])
            (conditions if condition else units).append(unit)
        data = r._revision(request['source'], units, conditions, 'draft')
        r.validate_revision(data)
    if request['action'] == 'approve':
        r.save_revision(data)
        r.approve_revision(data['revision'], request['source'])
    return data


def main():
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    try:
        result = {'definition': contract(request)}
    except (ValueError, KeyError, TypeError, IndexError):
        # Schema errors can include entire source objects; do not echo them.
        result = {'error': 'Invalid definition. Check unique nonempty criteria, job IDs, exact source quotes and line ranges, categories, and classifications. Explicit Required/Preferred wording cannot be contradicted; choose Unclear or clarify the job description.'}
    Path(sys.argv[2]).write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
