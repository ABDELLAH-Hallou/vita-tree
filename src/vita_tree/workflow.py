"""The CLI workflow contract and its small, public progress record."""
from pathlib import Path
import time

REPORTS = {
    'extract': ('job.json', 'job.toon'),
    'analyze': ('analysis.md', 'analysis.json', 'analyze.md'),
    'adapt': ('adapt.md',),
    'review': ('review.md', 'review.json', 'delta.md', 'delta.json'),
    'cover': ('cover.md',),
}
STEPS = ('extract', 'analyze', 'adapt', 'review', 'cover', 'validating')
MESSAGES = {
    'extract': 'Extracting the job requirements…',
    'analyze': 'Evaluating the original CV against the role…',
    'adapt': 'Adapting the CV…',
    'review': 'Reviewing the adapted CV against the same requirements…',
    'cover': 'Writing the cover letter…',
    'validating': 'Checking the generated files and branch conflicts…',
}


def capabilities(source):
    """Inspect the connected installation, not a version promised by the UI."""
    root = Path(source) / 'vita' if source else None
    return {step: bool(root and (root / 'assets' / 'prompts' / f'{step}.md').is_file())
            for step in ('extract', 'review', 'cover')}


def plan(options, available):
    if options is None:
        options = {}  # Old API callers retain the two-step workflow.
    if not isinstance(options, dict):
        raise ValueError('Unknown workflow options')
    if 'steps' in options:
        selected = options['steps']
        if (set(options) != {'steps'} or not isinstance(selected, list) or not selected
                or any(not isinstance(step, str) or step not in STEPS for step in selected)
                or len(set(selected)) != len(selected)):
            raise ValueError('Select one or more distinct workflow steps')
        selected = set(selected)
    else:
        if set(options) - {'extract', 'review', 'cover'}:
            raise ValueError('Unknown workflow options')
        if any(type(enabled) is not bool for enabled in options.values()):
            raise ValueError('Workflow options must be true or false')
        selected = {'analyze', 'adapt'} | {step for step, enabled in options.items() if enabled}
    for step in selected & {'extract', 'review', 'cover'}:
        if not available.get(step):
            raise ValueError(f'VITA {step} is unavailable. Upgrade vita-cv or check --vita-source.')
    return [{'id': step, 'status': 'pending' if step == 'validating' or step in selected else 'skipped',
             'startedAt': None, 'finishedAt': None} for step in STEPS]


def reusable_reports(reports, job_hash):
    """Carry only job-matching context into a new isolated run.

    Vita CV validates extraction/evaluation schemas and criteria itself. Markdown
    without provenance is excluded so Adapt cannot use a different job's advice.
    """
    import json
    result = {}
    for step, name, key in (('extract', 'job.json', 'source_sha256'),
                            ('analyze', 'analysis.json', 'job_sha256')):
        try:
            data = json.loads(reports.get('.vita/results/' + name, ''))
            metadata = data if step == 'extract' else data.get('metadata', {})
            if metadata.get(key) != job_hash:
                continue
        except (ValueError, AttributeError):
            continue
        for filename in REPORTS[step]:
            path = '.vita/results/' + filename
            if path in reports:
                result[path] = reports[path]
    return result


def transition(stages, step=None, terminal=None):
    """Copy on update so API responses cannot observe partially changed stages."""
    now = time.time()
    result = [dict(stage) for stage in stages or []]
    for stage in result:
        if stage['status'] == 'running':
            stage.update(status=terminal or 'succeeded', finishedAt=now)
        elif terminal in ('failed', 'interrupted') and stage['status'] == 'pending':
            stage['status'] = 'blocked'
        if stage['id'] == step and not terminal:
            stage.update(status='running', startedAt=now)
    return result


def clean_stages(stages):
    """Read old histories safely, exposing only the documented progress fields."""
    if stages is None:
        return []
    if not isinstance(stages, list) or len(stages) > len(STEPS):
        raise ValueError('Invalid workflow history')
    result, seen = [], set()
    for stage in stages:
        if (not isinstance(stage, dict) or stage.get('id') not in STEPS
                or stage['id'] in seen or stage.get('status') not in
                {'pending', 'running', 'succeeded', 'failed', 'blocked', 'interrupted', 'skipped'}):
            raise ValueError('Invalid workflow stage')
        seen.add(stage['id'])
        value = {key: stage.get(key) for key in ('id', 'status', 'startedAt', 'finishedAt')}
        if any(t is not None and (type(t) not in (int, float) or not 0 <= t < 1e12)
               for t in (value['startedAt'], value['finishedAt'])):
            raise ValueError('Invalid workflow time')
        result.append(value)
    return result
