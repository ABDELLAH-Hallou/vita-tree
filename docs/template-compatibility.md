# Template compatibility evidence

The [versioned synthetic corpus](../tests/fixtures/template_matrix/README.md)
tests Structure, file-aware source mapping and restricted PDF compilation against
the **same captured files**. It is a regression suite, not a claim that arbitrary
LaTeX templates reproduce their PDF layout in Structure.

## Recorded baseline

The [hash-bound baseline](../tests/fixtures/template_matrix/baseline.json) records
the tested source snapshots, engine/package versions, outcomes and every inspected
page image hash. The successful Linux run is linked there with its downloadable
CI evidence (14-day retention).

| Environment | Saved edits / leaf sweep | PDFs / pages visually inspected | Expected diagnostic controls | Missing dependency outcomes |
| --- | --- | --- | --- | --- |
| Ubuntu 24.04, TeX Live 2023/Debian: pdfTeX 1.40.25, XeTeX 0.999995, LuaHBTeX 1.17.0 | 15 / 306 | 48 / 102 | 12 | 0 |
| Windows, MiKTeX 24.4: pdfTeX 4.19, XeTeX 4.11 | 15 / 306 | 30 / 66 | 8 | 22 |

The Windows LuaLaTeX executable exists but its `lualatex.fmt` is missing; Amiri is
also unavailable. Those 22 original/edited outcomes are explicitly unverified,
including controls that could not reach compilation. They are not passing PDFs.
No dependencies were installed to repair that machine. The Linux browser run
also passed all 11 fixtures, all 15 named edits, the delayed-refresh regression,
and both eight-page selectable previews.

Every rendered baseline page was inspected by Codex for apparent clipping,
overlap, omissions and heading/entry association. This is agent visual inspection,
not human sign-off or typography certification. Arabic painted output is complete
in the inspected fixture; its extraction limitation below remains unresolved.

## Reproduce

From the repository root, install the explicit test extra in a virtual environment:

```sh
python -m pip install -e '.[test]'
python -m unittest discover -s tests -p test_template_matrix.py -v
python tests/run_template_matrix.py --output .test-artifacts/matrix-run
python -m playwright install --only-shell chromium
python tests/browser_template_matrix.py --browser chromium --output .test-artifacts/matrix-browser
python tests/review_template_matrix.py .test-artifacts/matrix-run/results.json
```

Use fresh output directories. `--engines pdflatex xelatex` or `--fixtures unicode`
limits a diagnostic run; do not present that run as full engine coverage.
`--require-dependencies` fails the run if an expected engine, package, font or
inspection tool is unavailable. Without it, absent dependencies remain explicit
in the report and are not counted as verified PDFs.

Install TeX and Poppler yourself. The dedicated Ubuntu 24.04 CI job explicitly
provisions `texlive-latex-extra`, `texlive-fonts-recommended`, `texlive-xetex`, `texlive-luatex`,
`texlive-lang-arabic`, `fonts-hosny-amiri` and `poppler-utils`. This is test-machine
setup, not product behavior. Vita Tree never installs a missing package or
enables shell escape to make these tests pass. Windows/MiKTeX installations need
equivalent packages, Latin Modern Roman and Amiri to exercise the same cases.

## What the checks establish

1. The manifest verifies fixture hashes before parsing. Required/absent Structure
   text and include diagnostics are independent fixture expectations.
2. Every exposed leaf is replaced independently with escaped punctuation. Exact
   span replacement must preserve all surrounding syntax and still parse.
3. Named edits use the real Workspace revision checks and file identities. Their
   independent literal replacement oracle compares **every source file's bytes**.
   External changes must cause a stale-save conflict.
4. Both the original and edited snapshots compile with each contracted engine.
   The harness verifies restricted flags and unchanged source hashes even if
   compilation fails. No AI service is called.
5. Poppler checks every PDF page for bounds, substantial word-box overlap, missing
   markers, unexpected page count and separated heading/entry associations. It
   renders every page as a PNG. The browser test separately exercises every named
   Structure edit and both eight-page PDF previews, including unchanged original
   versus edited page four.

`results.json` records fixture/input hashes, adapter and harness hashes, engine
and Poppler versions, LaTeX's `listfiles` package versions, embedded font names
and subset hashes, compiler restrictions, PDF/page hashes and failures. Font
subset hashes identify what was embedded; they are not upstream font versions.
The dated engine/package records make the installed dependency set explicit;
OS package mirrors can change, so this is not a bit-for-bit PDF reproducibility
promise. PDF timestamps also vary.

## Classify failures honestly

| Result | Meaning |
| --- | --- |
| `parser_defect` | Valid fixture cannot be parsed |
| `rendering_defect` | A supported visible marker disappeared from Structure |
| `source_map_defect` | Wrong span/file, changed untouched bytes or failed save oracle |
| `layout_defect` | PDF bounds/overlap/content/page assertion needs investigation |
| `dependency_missing` | Engine, package, font, installed MiKTeX format or file missing on this machine |
| `inspection_dependency_missing` | Poppler unavailable; visual checks did not run |
| `expected_diagnostic` | Deliberately invalid/missing-package control rejected correctly |
| `not_in_fixture_contract` | Engine deliberately excluded; not a passing test |
| `verified_automatically` | Automated checks passed; visual review still separate |

`approximate` and `unsupported` describe fixture **Structure support**, independently
of PDF compilation success. Arbitrary macro expansion, computed includes, exact
table/column geometry and bidi layout remain limited. The Unicode case covers
accented Latin text; it does not establish emoji, CJK or all writing-system support.

In the Arabic/Amiri fixture, the PDF paints the complete Arabic phrases but Poppler
extracts fragmented presentation glyphs. Those phrases are explicit
`visualOnlyMarkers`, displayed in the review gallery and ledger. Their omission
checks require visual inspection; selection, search and reading order are **not**
verified for this case. Joined Arabic glyph bounds intentionally overlap, so this
fixture explicitly permits Arabic-to-Arabic box joins. Latin overlaps and page
bounds remain checked. This is a recorded compatibility limit, not a parser fix.

Word boxes are font metrics, not painted pixels. For example, bitmap T1 fonts can
have oversized boxes that overlap between clean-looking lines. Investigate the
page and font before calling that a product defect; the escaped-text fixture uses
Latin Modern vector fonts to keep this geometric oracle meaningful. Do not disable
the overlap check to hide a real problem.

## Review every rendered page

The review command creates `review.html` and a pending `visual-review.json`, bound
to the report hash and each PNG hash. Open the gallery and inspect **every page**
of both snapshots at readable resolution for clipping, overlap, omissions and
heading/entry associations. Compare before/after changes; inspect original PNGs
when a thumbnail is insufficient. Record pass/fail and concise observations per
page, set the reviewer, then validate:

```sh
python tests/review_template_matrix.py .test-artifacts/matrix-run/results.json --verify
```

The command cannot approve pages automatically. CI uploads reports, PDFs, PNGs,
gallery and pending review records for 14 days; green automation does not imply a
human visual sign-off. Keep a sanitized reviewed summary with a release or PR;
do not commit generated CVs, PDFs or machine paths into the source tree.

## Confirmed compiler boundary

The matrix exposed MiKTeX LuaLaTeX rejecting `--dont-parse-first-line`. Vita Tree
uses that switch only for engines that implement it; LuaLaTeX rejects `%&`
first-line directives before invoking any process instead. Shell escape stays
disabled, MiKTeX installers stay disabled, and source snapshots are not rewritten.
This is restricted local compilation, not an OS sandbox or security certification.
