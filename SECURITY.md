# Security boundaries

Vita Tree is a local application running with its owner's OS permissions. It can read a CV collection, create Git worktrees, invoke Vita CV and TeX, and save selected application files. Its loopback HTTP token protects browser mutations from other origins. It is **not authentication against other local programs**, a multi-user service, or a sandbox for hostile TeX or AI agents.

The scoped review and reproducible synthetic tests are described in [Security review](docs/SECURITY_REVIEW.md). Passing them is not security certification, penetration-testing coverage of every feature, or a guarantee that a template, provider, or dependency is safe.

## Threat model

Protected assets include session API keys, CV/job content, application drafts, Git refs, local files outside an application, and private execution history. Inputs treated as untrusted include CV/job text, included template assets, generated wording/reports, provider failures, diagnostic records, and public HTTP request data.

The assumed adversary can supply such text or assets, induce a user to open a report, or operate a separate website. The tested adversary does not control the OS account, installed programs, browser extensions, Git configuration, or the trusted Vita CV installation. Repository configuration such as `.vita/.env`, project skills, provider endpoints, and Git filters/hooks must be reviewed and trusted separately. Opening an arbitrary configured repository is not equivalent to opening an inert CV file.

The implementation is intended to prevent source/model text becoming HTML or host task authority, ordinary application path escapes, accidental credential forwarding/persistence, and browser cross-origin mutations. Kernel isolation, malicious local programs, model obedience, and semantic truth of evidence are outside that guarantee.

## Boundary policies

| Boundary | Policy | Limit |
| --- | --- | --- |
| HTTP | Loopback-only construction; exact local Host; matching Origin when present; reject cross-site/same-site Fetch Metadata; constant-time mutation token check; JSON-only writes. GET and HEAD use the same origin guard. | Local clients can obtain a session token. A token is not a separate user's authorization. Older clients without Fetch Metadata rely on the browser's same-origin policy and mutation token. |
| Requests and documents | Request bodies up to 3 MB; source documents up to 2 MB, including immutable Git blobs checked before reading; incomplete/deeply invalid bodies fail; idle socket deadline. | No global connection, rate, memory, or disk quota. Idle deadlines are not total request-duration limits. |
| Application paths | Repository-relative paths; reject traversal, absolute/drive/alternate-stream paths, symlinks, and available junction detection; validate ZIP targets and reject ZIP symlink entries. | Path checks are not a kernel sandbox or protection from a hostile same-account process racing filesystem changes. Hard-link attacks and privileged mount manipulation are not certified. |
| Snapshots | Omit known credential/control filenames, including case variants; spool Git archives to temporary disk; expanded/archive/file-count budgets; local includes remain available. | This is a filename policy, not general secret discovery. Temporary/native-tool disk use still needs OS quotas. |
| Compilation | Installed executables outside the CV repository; cleaned environment; shell escape disabled; first-line option parsing disabled; MiKTeX installer/write18 disabled; engine-specific input/output settings; bounded retained diagnostics and PDF size. | TeX runs with the user's OS permissions. Engine primitives, Lua, native libraries, dependencies, fonts and generated PDF features are not comprehensively isolated. |
| Session credentials | Named keys remain in memory; forward only supported authentication variables for the selected provider; an explicit connection replaces inherited aliases; compiler children receive no provider keys. | Selected AI providers necessarily receive their own key. CLI login files, proxy configuration, custom secret names and local filesystem access are separate trust boundaries. In-memory secrets are not securely erased. |
| Generated outputs | Detect known literal and URL-encoded credentials in retained business outputs before review, checkpointing, or publication; withhold the run and redact detected copies. Discard outer AI stdout/stderr. | This is not DLP, arbitrary encoding detection, PII removal, or protection against a malicious provider. A backend may have its own storage outside Tree's inspected outputs. |
| Reports and PDFs | Escape Structure text; reports use text nodes and HTTP(S)-only links with `noopener noreferrer`; preview character/line/formatting limits; CSP restricts execution and framing. | Link destinations and claims are still untrusted. Exported PDFs are not sanitized active-content containers; another PDF reader has its own security model. |
| History, checkpoints and support exports | Revalidate typed outcomes, identities, hashes, allowlisted paths and diagnostic contracts; support ZIPs contain revalidated technical metadata, not document/prompt bodies. | Hashes establish matching content, not authorship, factual accuracy or approval by a trusted third party. Someone controlling the local store can forge it. Metadata can remain identifying. |

The Structure parser displays `\input`/`\include` references without opening those files. Snapshot copying applies the path checks above; actual TeX include resolution belongs to the compiler and has the engine-dependent limits described below.

Checkpoint cleanup targets 20 run collections, a 256 MiB budget, and a seven-day age policy, protecting active runs and their retry parents even when those protections prevent meeting the cleanup targets. Individual checkpoints have a 32 MiB budget. Cleanup expires checkpoint copies; application drafts, run inputs, reviews, and history have separate lifecycles and are not thereby erased. These stores remain private user data.

## Source instructions and Vita CV

CVs, job descriptions and generated reports are data. Tree does not execute their shell fragments, interpret their prose as workflow actions, or change the captured provider/model because a report asks it to. Structured outcomes, revision checks and explicit review actions determine publication and retries.

Vita CV owns provider adapters, prompt construction, factual evidence validation and internal diagnostic capture. The review checked these interfaces against its structured contracts and synthetic responses; it did not adversarially evaluate a live model. Prompt injection can still influence model wording, evidence or agent tool use. A read-only agent mode does not establish that it cannot read local credentials or contact another process. Review output meaning and use external OS isolation for hostile inputs.

## Compilation expectations

Use templates and TeX installations you trust. For hostile templates, use an OS sandbox/container with restricted files, no credential/home mounts, no network and explicit resource limits. Tree's process flags do not create that isolation.

MiKTeX has its own input/output policy; Kpathsea environment variables alone are insufficient. TeX Live 2026 release notes also document that `openin_any` no longer restricts input filenames. The native probes therefore record observed behavior per engine rather than declaring all TeX versions contained. See the review's references and results.

## Reporting a concern

Do not post credentials, real CVs, raw provider captures, machine-specific paths or sensitive exploit chains in public issues. Use the repository's private vulnerability-reporting channel when available; otherwise ask maintainers for a private channel before sharing details. A public report should identify the affected boundary and use a minimized synthetic reproduction.
