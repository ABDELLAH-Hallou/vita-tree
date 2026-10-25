# Application workspace

Vita Tree is an operating surface for preparing documents. Use a quiet paper-like content layer and a compact translucent control layer. The application workflow is the identifying element: a readable sequence with an adjacent next action, not a wall of controls.

## Tokens and layout

Light: paper #ffffff, canvas #f5f6f8, text #182b3c, action #245dc1, review #805500. Dark: paper #1c2835, canvas #151e28, text #e5edf4, action #9ac0ff, review #ffd580. Use existing system text and code fonts; document content determines its own typography. Body text remains at least 14px, primary actions at least 44px high. Text on paper has at least 4.5:1 contrast.

Desktop: application title → next action → workflow → document tabs and comparison. Review opens a focused sheet with a fixed heading and footer around independently scrolling changes. Narrow screens stack the before/after wording and keep Close and Continue reachable.

Use amber for a decision waiting on the user, green for completed work, blue for the current action, and red only for actual errors or removed wording. Add/remove labels complement color. Technical provenance and AI configuration remain accessible through secondary controls.

Glass is confined to floating headers and review footers, with solid fallbacks for reduced transparency. Avoid decorative motion and preserve reduced-motion preferences.

## Design references

- [Apple: Principles of great design](https://developer.apple.com/videos/play/wwdc2026/250/): purpose, agency, clarity and simplicity.
- [Apple HIG reference skill](https://github.com/doclegg05/apple-human-interface-guidelines) and [Apple design skill](https://github.com/dickwu/apple-design-skill): clear action hierarchy, accessible controls, content/control separation.
- [Liquid Glass for Tailwind](https://github.com/Tontoon7/liquidglass-tailwind): adapt its translucent control patterns to the existing CSS; no Tailwind migration is needed.
- [Impeccable](https://impeccable.style/): task-oriented composition, concrete labels, restrained operational UI.
