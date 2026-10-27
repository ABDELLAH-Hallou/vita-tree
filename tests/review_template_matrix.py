"""Prepare a static all-page gallery or verify explicit page-by-page review."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path


def sha(value):
    return hashlib.sha256(value).hexdigest()


def captured_pages(report):
    result = []
    for fixture in report['results']:
        for engine, runs in fixture['engines'].items():
            if not isinstance(runs, list):
                continue
            for run in runs:
                for page in run['pages']:
                    result.append(dict(id=f"{fixture['id']}/{engine}/{run['snapshot']}/{page['number']}",
                                       image=page['image'], imageSha256=page['imageSha256'],
                                       status='pending', notes=''))
    return result


def review_report(path, verify=False):
    root = path.resolve().parent
    raw = path.read_bytes()
    report = json.loads(raw)
    pages = captured_pages(report)
    ledger = root/'visual-review.json'
    for page in pages:
        image = root/page['image']
        assert image.resolve().is_relative_to(root) and not image.is_symlink(), 'Unsafe page path'
        assert sha(image.read_bytes()) == page['imageSha256'], 'Rendered page changed'
    if verify:
        review = json.loads(ledger.read_text(encoding='utf-8'))
        assert review['reportSha256'] == sha(raw), 'Review belongs to a different report'
        assert review['reviewer'].strip(), 'Set the reviewer'
        assert len(review['pages']) == len(pages) > 0, 'Review must cover every rendered page'
        for expected, actual in zip(pages, review['pages']):
            assert all(actual[key] == expected[key] for key in ('id', 'image', 'imageSha256')), 'Page identity changed'
            assert actual['status'] == 'pass', f"Page not approved: {expected['id']}"
            assert actual['notes'].strip(), 'Record observations, not just a pass flag'
        return len(pages)
    assert not ledger.exists(), 'Never overwrite an existing visual review'
    ledger.write_text(json.dumps(dict(schemaVersion=1, reportSha256=sha(raw), reviewer='',
                                     checks=['clipping', 'overlap', 'omissions', 'heading/entry associations'],
                                     pages=pages), indent=2)+'\n', encoding='utf-8')
    cards = []
    for page in pages:
        cards.append(f'<figure><figcaption>{escape(page["id"])}</figcaption>'
                     f'<a href="{escape(page["image"], quote=True)}"><img loading="lazy" '
                     f'src="{escape(page["image"], quote=True)}" alt="{escape(page["id"], quote=True)}"></a></figure>')
    (root/'review.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
        '<title>Template matrix page review</title><style>body{font:16px system-ui;background:#e8e8e8;color:#111;margin:24px}'
        'main{display:grid;grid-template-columns:repeat(auto-fit,minmax(600px,1fr));gap:24px}'
        'figure{margin:0}figcaption{padding:12px;background:white;font-weight:600}img{width:100%;display:block}'
        '@media(max-width:650px){main{display:block}figure{margin-bottom:24px}}</style>'
        '<h1>Review every page of both snapshots</h1><p>Open each image at readable resolution. '
        'Record observations in visual-review.json; this gallery does not approve pages.</p><main>'
        + ''.join(cards) + '</main></html>', encoding='utf-8')
    return len(pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    count = review_report(args.results, args.verify)
    print(f'{count} pages: ' + ('explicit review verified' if args.verify else 'gallery and pending review created'))


if __name__ == '__main__':
    main()
