# Vita CV diagnostics v1 fixtures

The JSON schemas and success/failure fixtures in this folder are copied without
modification from Vita CV's diagnostics implementation, inspected on 2026-10-23.
They describe the separate diagnostics contract, not CV outputs or outcome v1.
The fixtures contain synthetic identifiers and no provider output.

The upstream working tree was based on 0f3e34b (2.6.3); its diagnostics work was
not yet committed. Source snapshots used for compatibility:

- vita/helpers/diagnostics_contract.py: SHA-256 56c62560df2d1a3d6e1f9a68d5f7594c22cd063dc097a3769a491e76befebc05
- vita/helpers/diagnostics.py: SHA-256 77dced699b5d8e9b580570ccf9eed63f5e617f0b6fe659d790a7576f62b038a4

The diagnostic_fixtures.py helper derives deterministic scenario variants using
this vocabulary and shape. It never calls a model. Refresh these snapshots
deliberately when the shared contract changes; unsupported major versions remain
unavailable.
