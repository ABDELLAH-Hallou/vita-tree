# Scoped local security review — issue 48

Reviewed baseline: merge `9e69332` on 24 October 2026. Changes and tests are on `codex/local-security-boundaries`. This is a source review plus bounded synthetic regression testing, not security certification or a comprehensive penetration test. The [threat model](../SECURITY.md) states the operating assumptions and remaining limits.

No real CV, job corpus, credential, provider request, or unrelated external target is used by these tests. Browser attacks use two disposable loopback servers; outbound requests from the report test page are intercepted. Native TeX probes use temporary, non-sensitive canary files. Raw compiler/provider captures and installation paths are not published as findings.

## Confirmed findings and changes

| Finding at the baseline | Change and focused verification |
| --- | --- |
| GET accepted metadata-marked cross-origin requests without Origin; inherited HEAD handling skipped the Host/Origin guard. This was an inconsistent browser boundary, not proof that a website could read the token through CORS. | Share the guard with HEAD; reject cross-site and same-site Fetch Metadata. Test raw HTTP and actual Chromium fetch/image requests from another loopback port. Constructor also rejects non-loopback exposure. |
| AI child environments included unselected providers' ambient credentials. Compiler environments included the server's full environment. | Scope supported AI authentication to the selected route; replace Google/Gemini aliases when a named key is chosen. Give compiler/version processes a small OS/font environment, excluding provider credentials and inherited TeX configuration overrides. Exercise distinct named keys in concurrent real child processes. |
| Compiler lookup could select a program from the working directory or repository PATH. | Use absolute candidates from cleaned installed PATH entries; reject repository-contained executables. Test that a synthetic repository executable is never selected. This does not verify signatures or integrity of installed tools. |
| The installed MiKTeX engine read a harmless external canary under the old Kpathsea-only input settings. | Set per-process MiKTeX application input/output and shell-command policy as well as existing restrictions. The same native read probe is blocked after the change, while a local include and clean selectable PDF still work. |
| Committed sources bypassed the local file-size check; archive bytes and compiler/outer AI output were buffered before useful bounds. | Size-check immutable Git blobs; spool archives and compiler diagnostics; discard unused outer AI output; enforce documented snapshot, diagnostic and PDF budgets. Test declared oversize requests/ZIP entries and oversized committed/local files. This does not provide hard disk or aggregate resource quotas. |
| Known credential filenames could enter snapshots. Known credential values in an error or generated report could reach an API/report/checkpoint. | Exclude known credential/control paths case-insensitively; redact known error values and HTTP userinfo; withhold/redact detected credential-bearing business outputs before checkpoints/publication. Test synthetic echoed credentials, failed-process stdout, private stores and support ZIP contents. Unknown or encoded secrets beyond the tested representations are not ruled out. |
| Large Markdown reports could create excessive preview work. | Bound preview characters, lines, inline formatting and table width, with a shortened-preview notice. Raw HTML remains text; executable URL schemes never become links. Test an oversized synthetic report and HTML/URL payloads in Chromium. |

## Reproducible checks

Run from an isolated checkout with the test extras and Git installed:

```text
python -m unittest discover -s tests -v
python tests/browser_security.py --browser chromium
python tests/smoke/run_security_tex.py
```

The native probe requires installed `pdflatex` and `pypdf` (in the test extra). It writes only synthetic PDF/results under ignored `.test-artifacts/`. It does not enable shell escape or an installer. A missing/unusable Lua installation is recorded as unavailable, not a passed Lua test. A TeX engine which permits the external read probe is reported as `not_contained`; it is not silently labelled safe.

Additional regression coverage uses the existing browser editing, AI settings, checkpoint retry, factual-review/PDF and canonical-requirement tests. Vita CV contract tests use the published 2.8.0 minimum backend with synthetic responses. Source interface review also covered the local 2.9 implementation of provider routing, diagnostics, Codex read-only invocation, and canonical/factual outcomes. This does not establish behavior of every installed provider or backend version.

## Observations on the local test platform

- Windows, Python 3.12 and Chromium were exercised locally.
- MiKTeX-pdfTeX 4.19 / MiKTeX 24.4 produced a readable/selectable clean PDF and a permitted local include. The shell/first-line probe did not enable command execution. External canary input was readable before the change and blocked afterward; the external output probe is also blocked afterward.
- A benign LuaLaTeX compile failed on this installation. Native Lua credential/file behavior is **not verified** here. Environment construction and command flags are tested separately.
- HTML/report probes exercised DOM structure as well as execution markers, so CSP alone was not treated as proof that escaping works. Cross-origin rejection was verified at the server, not inferred merely from a browser CORS error.
- Worker tests exercise separate named connections concurrently, source instructions as inert host data, raw failed-process output, an intentionally echoed synthetic credential, checkpoint non-publication and technical support exports. They make no live-model prompt-injection claim.

Local verification completed as follows:

- The full Python suite passed 193 tests. The final focused security run passed 19 tests, including encoded credential copies and linked snapshot roots. After a final HEAD response-body correction, 17 HTTP/server tests passed.
- Chromium security, normal editing/PDF, AI settings and factual-review browser checks passed. The native PDF probe passed the boundaries recorded above; a rendered clean page was also visually inspected.
- The canonical-requirements suite passed 10 tests against Vita CV 2.8.0. The factual-change suite passed all 10 tests with private subprocess diagnostic capture. **Two earlier ordinary factual-suite runs each failed during canonical backend setup in different tests.** Those cases passed individually, and 30 isolated approvals with ordinary handles plus 30 with diagnostic capture passed. The intermittent setup failure's cause remains unconfirmed; the diagnostic pass does not establish that it was fixed. No production contract or approval check was weakened to get a pass.
- Local distributions passed strict metadata/package checks and the project's history/distribution privacy check. A secret scan of tracked and non-ignored publication candidates found no leaks. Ignored local research artifacts and installed dependency trees are not publication candidates or part of that clean-scan claim.

CI runs Python boundary regressions on its existing platform/version matrix and the browser/native-TeX probes in the browser job. CI and additional platforms must supply their own results; a local pass is not a claimed remote CI pass.

## Unresolved and excluded boundaries

1. **No OS sandbox.** Engine/library vulnerabilities, Lua native I/O, arbitrary TeX input computation, subprocess descendants, native font helpers and malicious installed tools are not contained by these checks. TeX Live 2026 no longer enforces `openin_any`; behavior of that version was researched but not natively tested here. Hostile templates need separate OS/file/network isolation. No shell-escape or installer fallback was introduced.
2. **No model-level prompt-injection result.** A live model can still follow misleading source instructions or produce fabricated evidence. Tree's tests establish that prose does not override host workflow/configuration or approval contracts. Vita CV owns prompt/adaptor/evidence semantics; further adversarial model/agent testing belongs there and must use synthetic data and private handling where needed.
3. **Single OS account.** Other local programs can access loopback APIs and user files. Repository `.git` configuration, project skills, endpoints, installed CLIs, login files and browser extensions are trusted. Same-account filesystem races, hard-link manipulation and process memory inspection are not excluded by path checks.
4. **Bounded redaction.** Known current/captured credential literals and URL-encoded forms are checked in the tested outputs. Arbitrary encodings, short coincidences, unfamiliar secret variables, personal data, backend-side storage, remote retention and deliberate exfiltration are not covered by that scan. Saved source documents and ordinary private application outputs are intentionally retained and may contain personal data.
5. **Resource and export limits.** No global rate/concurrency/disk/memory quota or complete process-tree deadline is provided. Native tools can write their own logs before checks finish; temporary archive spooling is not a disk quota. Support metadata is not anonymous, and exported PDFs may contain features handled differently by another reader. Dependency CVE coverage, binary/font fuzzing, browser-extension attacks and network penetration testing were not performed.

Further findings should be handled privately under the reporting guidance. These exclusions are not assertions that an exploit exists, or that it has been prevented.

## Primary references

- [MDN: Fetch Metadata and Sec-Fetch-Site](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Sec-Fetch-Site) — browser-supplied origin relationship and rejection policy.
- [MiKTeX configuration reference](https://docs.miktex.org/manual/miktex.ini.html), [MiKTeX pdfTeX options](https://docs.miktex.org/manual/miktex-pdftex.html), and [MiKTeX configuration lookup source](https://github.com/MiKTeX/miktex/blob/master/Libraries/MiKTeX/Core/Session/config.cpp) — separate input/output policy and application-scoped overrides; disabled installer/write18/first-line options.
- [TeX Live security considerations](https://tug.org/texlive/doc/texlive-en/texlive-en.html#x1-110001.4) and [TeX Live 2026 changes](https://tug.org/texlive/bugs.html) — untrusted input precautions and the changed `openin_any` behavior.
