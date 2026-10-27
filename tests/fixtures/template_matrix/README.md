# Template matrix 1.0.0

All source and expected content in this directory was written for Vita Tree,
is synthetic, and is licensed under the repository's [MIT license](../../../LICENSE).
No real CV, third-party template, bundled font, or third-party PDF is included.
Names and URLs are fictional test data. Installed TeX packages and fonts retain
their own licenses; they are test prerequisites, not redistributed assets.

`manifest.json` is the contract: corpus/fixture versions, exact UTF-8 LF file
hashes, engine expectations, visible markers, page counts, include diagnostics,
mapped edits, and declared compatibility limits. `.fixture` files are copied to
their manifest filenames in isolated temporary repositories. They are inert test
assets in Git, not user CVs. They ship in the source archive for reproducibility,
not in the installed runtime wheel.

| Fixture | Coverage | Engines | Structure limit |
| --- | --- | --- | --- |
| native-environments | Local class, nested custom environment definitions | pdfTeX, XeTeX, LuaTeX | Body text; approximate layout |
| macro-arguments | Multi-argument resume commands, nested formatting, optional arguments, link labels | All three | Arbitrary macro expansion omitted |
| escaped-text | Escaped punctuation, braces, backslash, tilde, caret, decoded-leaf replacement | All three | TeX spacing is approximate |
| tables-columns | `tabularx`, two `minipage` columns, cell/body edits | All three | Column geometry/reading order approximate |
| nested-includes | `input`, `include`, nested includes, duplicate text in different files | All three | Individual file views; no expanded page layout |
| unicode | Accents, German text, non-BMP character before edit offsets | XeTeX, LuaTeX | Emoji is in a comment, not a glyph test |
| rtl-arabic | Arabic body, English editable argument, polyglossia/Amiri | XeTeX | Logical text only; no Structure bidi-layout claim |
| long-document | Eight pages, 96 numbered entries, middle-page edit | All three | Explicit page breaks; no arbitrary-pagination claim |
| dynamic-include | Computed include path that TeX can resolve | All three | Unsupported include explicitly reported |
| missing-dependency | Deliberately absent synthetic package | All three | Expected missing-package diagnostic |
| invalid-source | Unclosed group | All three | Expected syntax/compilation failure |

The portable tests sweep every exposed source leaf independently, including
decoded escapes. A separate set of manifest edits is saved through the real
Workspace API, checked against independent literal replacements, and compiled.
The sweep does **not** claim every possible user edit is valid TeX. Every untouched
prefix, suffix, section and fixture file must remain byte-identical.

Change a fixture's version and SHA-256 references when changing its source or
expectations after release. Increment the corpus version when its contract or
membership changes; update the loader's supported version and recorded baseline
together. Never regenerate hashes to make an unexplained failure disappear.

See [running and interpreting the matrix](../../../docs/template-compatibility.md)
for commands, evidence, manual page review and actual limits.
