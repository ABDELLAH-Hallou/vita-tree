# Third-party components

Vita Tree's own source code is licensed under the MIT license in `LICENSE`.

The offline PDF viewer bundles files from Mozilla PDF.js (`pdfjs-dist` 6.4.299).
Their original notices are preserved under `vita_tree/static/vendor/` in the
installed package, and also included in the distribution's license metadata:

| Component | License/notice file relative to `static/vendor/` |
| --- | --- |
| PDF.js viewer and worker | `PDFJS-LICENSE` (Apache-2.0) |
| Adobe character maps | `cmaps/LICENSE` |
| Foxit/PDFium standard fonts | `standard_fonts/LICENSE_FOXIT` |
| Liberation fonts | `standard_fonts/LICENSE_LIBERATION` |
| JBIG2 decoder and PDF.js integration | `wasm/LICENSE_JBIG2`, `wasm/LICENSE_PDFJS_JBIG2` |
| OpenJPEG decoder and PDF.js integration | `wasm/LICENSE_OPENJPEG`, `wasm/LICENSE_PDFJS_OPENJPEG` |
| QCMS color management and PDF.js integration | `wasm/LICENSE_QCMS`, `wasm/LICENSE_PDFJS_QCMS` |

The pinned upstream source and refresh command are in `package-lock.json` and
`scripts/vendor-pdf.mjs`. Node is needed only to refresh vendored browser assets.
No upstream license is replaced by the MIT license of Vita Tree.

`pylatexenc` and the optional `vita-cv` integration are installed as Python
dependencies; their source is not copied into Vita Tree. They retain their own
licenses and metadata.

The offline LaTeX editor bundles CodeMirror, Lezer, and their runtime dependencies.
Their original MIT license notices are collected in `static/vendor/EDITOR-LICENSE`.
Pinned versions are in `package-lock.json`; `npm run build:editor` rebuilds the
bundle and notices from `scripts/latex-editor.mjs`.

Accessibility tests use the MIT-licensed `axe-core` development dependency from
Deque Systems, pinned in `package-lock.json`. Its upstream license is included
in the npm package. It is not bundled into Vita Tree's browser assets or wheel.
