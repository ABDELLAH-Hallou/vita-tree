# Vita Tree setup

Repository-local Codex skill: `design-taste-frontend`.

Source: https://github.com/leonxlnx/taste-skill
Pinned revision: `12af471f627f866411b4bd785b19646d3672784c`.
Installed from `skills/taste-skill`, with the upstream MIT license retained.

Local adjustment: three contact email addresses in the upstream evaluation
examples were replaced with `contact@example.org` to satisfy this repository's
publication privacy policy. The skill instructions, scripts, assets and design
library are otherwise unchanged.

Invoke `$design-taste-frontend` for design work. Vita Tree is an app/editor, so
follow `references/app-screens.md` for its interface. Keep its existing plain
HTML/CSS/JavaScript stack and actual behavior.

Requires Node 22+ and Chrome, Edge or Chromium. Generated working files belong in
`.taste-skill/` (ignored by Git). Image discovery needs network access; no API key
or frontend runtime dependency is installed by this setup.