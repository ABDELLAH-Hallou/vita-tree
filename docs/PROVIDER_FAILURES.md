# AI failures and generation checks

A failed workflow component and its preparation history show a category, the
backend-reported provider/model, retryability, provider attempt count, and the
next action. Temporary overload and request limits call for waiting; rejected
credentials, unavailable models, permissions, and exhausted quota call for
repairing the relevant setup. Invalid output is reported separately. Unknown
historical evidence stays unknown; the captured request is labelled separately
when the backend did not report an effective route. No vendor is switched
silently. Advice comes from Tree’s allowlisted categories, never provider prose.

**Retry preparation** opens the verified checkpoint plan. It preserves the
failed attempt’s captured setup and language, even if you have since edited the
shared setup. Select **Use the current application setup** explicitly to change
it, review which steps can be reused, then confirm. Cancelling starts nothing.
Expired session credentials require reconnecting and explicitly selecting the
repaired setup. Each retry creates a new attempt linked to its parent; history
shows whether the configuration changed. Verified dependency matching, atomic
publication, and unsaved-draft protection still apply.

**Check generation…**, beside a shared or individual AI setup, opens a usage
confirmation. **Run generation check · may use credits** sends a small synthetic
prompt through Vita CV’s `providers check --generate` contract. Provider retries
can also consume usage. It sends no CV, job description, project instructions,
or saved reports. It runs in a system temporary workspace outside the CV project;
Codex receives its own empty Git repository. With credentials in memory, it
uses the selected provider/model/reasoning and connection and deletes the check
workspace afterward. The server limits each check to 180 seconds and rejects
duplicate submissions for the same application/step. A timeout does not prove
that the provider did no work or incurred no usage.

A model appearing in suggestions is catalog evidence, not generation access.
A successful generation check proves access only at that time, not output
quality or compatibility with every workflow schema. Results distinguish the
requested route from backend evidence. Opening or cancelling the confirmation
sends no request. Checking a step-settings draft does not apply or save it;
**Apply**, **Cancel**, and Escape retain their existing behavior. The check is
separate from workflow execution/history and never publishes application files.

Tree consumes provider-error v1, outcome v1, and provider-check v1 artifacts.
Older Vita CV installations without provider-check evidence show an update
message; Tree never guesses success from stdout, model discovery, or exit code.
Raw stdout/stderr, error prose, environment objects, API keys, and generated
check content are not returned to the UI or support export. Stored outcomes and
history are revalidated when read; only allowlisted technical fields survive.

Tests use temporary Git repositories and local fake AI processes. An optional
`tests/smoke/run_provider_contract.py --vita-source <checkout>` checks the actual
Vita CV producer and Tree adapter with synthetic responses and networking blocked.
