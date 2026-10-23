# Inspecting a preparation

Open **Activity & support**, choose a preparation, and select a step. The same
inspector is available from **Execution details** in preparation history and
**Inspect this step's execution** in a recorded graph component.

Overview names the recorded phase and known category, then suggests an action.
Timeline shows Tree phases, backend spans, provider attempts, retry delays, and
resume lineage. Request separates requested routing from backend-reported
effective routing and configuration origins. A requested value is not evidence
that a provider used it. Shared settings and step overrides are labelled.
Input, configuration, criteria, and backend fingerprints identify the captured
revision without copying personal documents.

Response shows capture state separately from whether a model response was
observed. No response, an HTTP provider error, rejected generation, disabled
capture, privacy suppression, truncation, and missing historical artifacts have
different labels. Unknown response existence stays unknown. Error contains
allowlisted provider metadata, HTTP status, retryability, validation locations,
and module/line frames; it never parses stderr to guess a provider failure.

**Retry preparation** in the inspector opens the existing verified-checkpoint
review. It preserves the captured route and language by default. Explicitly
select **Use the current application setup** to change them. Reuse still requires
matching inputs, dependencies, criteria, credentials, and effective setup.
Changed-routing attempts are labelled. Each attempt has a new execution ID and
its own backend processes; related attempts share their root trace ID.
Unsaved editor drafts must be saved first. Starting a retry does not publish
partial results or bypass conflict checks and atomic publication.

## Trace location

The application project owns `.vita/logs/traces/<trace-id>/` by default. Tree
passes the absolute project root, traceparent, and traces destination into
every AI subprocess, so diagnostics survive disposal of staging workspaces,
checkpoint cleanup, failed runs, and server restarts.

Set `VITA_DIAGNOSTICS_DIR` to an absolute alternative traces directory in the
server environment or the project's `.vita/.env` before starting Tree. It names
the store, not one trace folder. Tree and Vita CV use the same destination.
Relative alternatives and linked/junction destinations are rejected. Storage
failure is shown separately and never replaces the original preparation result.
Memory-only evidence can be lost on restart; the UI does not claim it was saved.
The resolved location is shown under **Where execution details are stored**;
**Copy trace folder location** lets you locate it in your file manager without
accepting arbitrary filesystem-open requests.

Tree adds a local Git exclusion for an in-project trace directory in the shared
Git info/exclude file. It does not change application commits. This exclusion
does not remove files already tracked by Git. Avoid committing diagnostics:
technical model identifiers and hashes can still be identifying.

Vita CV owns `manifest.json`, `process-*.json`, `events-*.jsonl` and `artifacts/`.
Tree writes separate `tree-<execution-id>.json` records and never rewrites backend
streams. Server JSON logs remain at the existing `--log-dir` destination; workflow
and phase events include run and trace IDs so the two stores can be correlated.

## Capture and compatibility

Tree consumes Vita CV's **diagnostics v1** contract. Compatibility fixtures and
schema snapshots are in `tests/fixtures/diagnostics`. This contract was inspected
in Vita CV's local diagnostics implementation; upgrading to a version without
that implementation will show **limited diagnostics**, even if its version
number is newer than the existing outcome API. Unsupported schema versions and
unreadable contracts are explicitly unavailable. Missing completion records are
incomplete/possibly running, never proof of success.

Capture defaults to `off`. Technical metadata, prompt section labels/sizes, safe
instruction summaries, and value-free schema structure can still be recorded.
Explicit `VITA_DIAGNOSTIC_CONTENT=sanitized` allows additional response/error
**structure**, with source values removed. It does not enable raw content capture,
restore discarded prose, or reveal hidden reasoning. Tree does not override
providers or make diagnostic model calls.

Every artifact is read lazily through its execution/artifact IDs. Both reading
and export reapply type, vocabulary, size, identity, path, and symlink checks.
Artifact views render text. A manually edited file cannot introduce executable
HTML or authorize arbitrary file access. Sanitization is not a guarantee of
anonymization; inspect technical identifiers before sharing.

## Retention and support exports

Completed traces are eligible for cleanup after **7 days**, at **100 traces**, or
under the shared **50 MiB** store budget. Tree uses Vita CV's storage-lock
protocol and accounts for its active process reservations. Active traces,
incomplete backend processes, and crash reservations are protected. When they
exhaust the budget, diagnostics report a storage problem rather than deleting
them. Resolve incomplete/crashed traces deliberately with the server stopped.
Trace cleanup does not delete preparation history, CV drafts, checkpoints,
reports, or generated PDFs. A history entry can therefore outlive its evidence.
Vita CV also enforces its own bounded event rotation and 16 KiB artifact limit.
Tree retains at most 512 phase records per execution; the reader limits large
or malformed trace stores and reports unavailable evidence honestly.

In **Artifacts**, **Review support export** shows included and omitted information
before download. The ZIP contains only revalidated technical `diagnostics.json`
and an explanatory README. It excludes artifact bodies, CV/job documents, exact
prompts, model prose, credentials, environment objects, local paths, application
names, and raw subprocess output. **Copy execution diagnostics** similarly omits
the resolved storage location. Normal activity counts and server metrics remain
available in the existing technical details.
