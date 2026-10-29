# Browser and accessibility verification

Vita Tree targets current desktop Chrome/Edge, Firefox and Safari for preparing
applications. We test Chromium, Firefox and WebKit engines with Playwright.
An engine result does not qualify every branded browser, operating system or
assistive-technology combination. In particular, Playwright WebKit is not
shipping Safari, and a narrow viewport is not a physical phone test.

The UI target is the relevant WCAG 2.2 AA behavior: keyboard operation without a
trap; understandable names, roles and instructions; visible, unobscured focus;
identified errors and status updates; text contrast; and usable enlarged/reflowed
controls. This is an engineering target, **not a WCAG conformance statement**.
No complete WCAG audit, screen-reader qualification or human task study has been
completed by this change.

## Reproduce the automated coverage

Use Python 3.12, Node 22.13+ or 24+, Git and an installed TeX engine. Compilation
remains restricted; these tests do not enable shell escape, install TeX packages
on behalf of the application or contact an AI provider.

```sh
python -m pip install '.[test]' 'vita-cv==2.8.0' 'playwright==1.63.0'
npm ci --ignore-scripts
python -m playwright install --with-deps chromium firefox webkit
python tests/browser_accessibility.py --browser chromium --output .test-artifacts/a11y-chromium
python tests/browser_accessibility.py --browser firefox --output .test-artifacts/a11y-firefox
python tests/browser_accessibility.py --browser webkit --output .test-artifacts/a11y-webkit
```

On Windows omit `--with-deps`; install the declared test dependencies yourself.
The new accessibility workflow installs TeX explicitly on its disposable Linux
runner. It runs the keyboard/axe walkthrough and the existing AI settings,
component-dialog, requirements, provider-recovery and factual-review scenarios
separately in each engine. Failures are not silently skipped when an engine or
dependency is missing. Use a separate output directory per walkthrough run.

The walkthrough uses only Tab, Shift+Tab, arrow keys, Space, Enter, Escape and
text input for task actions. Fixture setup, viewport resizing, appearance
seeding for modal screenshots, axe injection and source assertions are test
instrumentation, not claimed as user actions. axe-core is pinned in the npm
lockfile and runs through a same-origin Playwright route; the production CSP
and server routes are unchanged.

`results.json` records the code revision, OS, backend, Playwright, browser and
axe versions, completed tasks, violations and incomplete checks. Screenshots
cover both themes, desktop and 320-pixel layouts, enlarged component/review
sheets, errors and final PDF access. 200% **CSS zoom** checks enlarged controls;
the reduced layout cases also check reflow. Native browser-chrome zoom, OS text
scaling, pinch gestures and touch operation require separate manual testing.

## What the checks establish

| Task | Automated evidence | Still requires human/AT evidence |
| --- | --- | --- |
| Shared AI setup and Extract override | Keyboard changes, exact model IDs, inherited/custom states, Apply persistence and Cancel/Escape discard | Whether first-time users understand effective configuration and model IDs |
| Session credentials | Named nested dialog, masked key entry, cancel clears key, successful return to parent focus | Spoken explanation of session-only storage, comprehension and real authentication UX |
| Requirements | Source navigation, focusable source scroller, validation alert, confirmation and immutable approval | Screen-reader reading order, classifications and ambiguity comprehension |
| Provider failure and retry | Typed failure categories, explicit retry, captured configuration and lineage in fixture scenarios | Whether guidance is understandable and announcements are timely in actual AT |
| Factual decisions | Keyboard accept/reject/edit, edit focus, confirmation, resume and preserved rejected wording | Correct interpretation by representative users, screen-reader comparison usability |
| Reports and PDF | Named report controls, real restricted compilation, rendered/selectable text and keyboard PDF-link access | PDF tagging, logical reading order, accessible exported content and external viewer behavior |

DOM `role=alert`/`role=status` assertions and axe scans do not prove that an actual
screen reader speaks an update. The PDF text layer is not a tagged PDF structure
or a guarantee of correct reading order for arbitrary templates. Canvas pixels,
transparent text layers, native controls, focus indicators and other axe
incomplete results need manual review. axe does not cover all WCAG criteria.

The proposed representative-user sessions and recording sheet are in
[the task-study protocol](usability-study.md). No simulated participant results
or automated success rate should be substituted for those sessions.

## Results and limitations

The recorded engine results and demonstrated fixes are updated with this PR's
verification evidence. CI retains sanitized JSON/screenshots for 14 days. The
synthetic fixture worktrees, session credentials and raw provider output are
excluded from uploaded evidence. Run the commands again after artifact expiry;
the checked-in fixtures and dependency locks define the reproducible setup.

Physical iOS/Android devices, branded Edge, shipping Safari, NVDA, JAWS,
VoiceOver, TalkBack, Windows High Contrast/forced colors and representative-user
sessions are not qualified by this automation. A failure on one of these targets
remains actionable; absence of that evidence is not a pass.

Primary references: [WCAG 2.2](https://www.w3.org/TR/WCAG22/),
[focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html),
[contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html),
[status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html),
and [Playwright browser coverage](https://playwright.dev/python/docs/browsers).
