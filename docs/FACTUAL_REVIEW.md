# Reviewing factual changes

Vita CV 2.8.0+ produces `factual-changes/1` proposals for Tailor CV and Cover
letter. A proposal is not an approval. When a run needs confirmation, the graph
and history offer **Review factual changes**. Clicking the graph node still opens
its AI settings.

Each change shows the original and proposed wording, its category, the backend's
unresolved interpretation, source file/line references and quotations, and its
location in the proposed document. References establish text presence; they do
not establish truth or semantic equivalence. Unsupported insertions have no
supporting source location and are labelled accordingly.

Choose **Accept**, **Reject**, or **Edit** for every change, then explicitly confirm
that you reviewed the factual meaning. Native radio groups support Tab, arrow
keys and Space. Editing focuses a labelled textarea. Closing the panel discards
unsubmitted choices without touching the application or the retained proposal.
**Mark as reviewed** remains an acknowledgement of a run; it cannot approve facts.

## Drafts and publication

**Apply decisions to draft** updates a retained preparation checkpoint. It does
not overwrite the application. Use **Retry preparation** to review the reuse plan
and continue the remaining steps. The application updates through the existing
recoverable multi-file publication only after all selected steps and final checks
succeed. An unsaved editor draft must be saved before reviewing or applying.

Application source, job, include/assets, criteria, configuration and backend hashes
must still match the capture. The retained draft must also match. Changes cause
a conflict; they are never overwritten. A changed route, skill or dependency on
retry invalidates the affected checkpoints and downstream work. New proposals
require fresh decisions. A Cover retry following Adapt restores the matching
reviewed CV and its factual contract.

Rejection retains the original wording. Rejecting every Cover change keeps the
previous letter, if any; it does not substitute the CV for the letter or create a
new PDF. Mixed edits must form valid LaTeX. Accepted letters are compiled before
their reviewed checkpoint can be reused.

## Contract and provenance

The adapter obtains and validates the backend's host-generated report through
its Python API, with an execution-bound JSON envelope. It does not infer facts,
approval or success from human-readable stdout. Whole-revision approval is the
backend's current contract: for mixed decisions Tree constructs the chosen text,
archives the original revision as rejected, asks Vita CV to create a new revision,
and approves that exact reviewed document. The backend revalidates captured
sources and the host diff before applying it in a disposable copy.

`adapt.decisions.json` and `cover.decisions.json` record the original/resulting
revision, run, timestamp, per-item choices and exact edited wording. The method is
`explicit_ui_review` and the actor is `local_user`: this describes an explicit
action in the local UI, not an independently authenticated person's identity.
The original source, original proposal, host verification finding and revision
archives remain available. Human approval does not turn an unverified
interpretation into host-verified truth.

The reviewed checkpoint is written before a single atomic review manifest commits
the decision. A crash before that marker leaves the review pending and blocks
Retry, including after restart. Subprocess or compilation failures only affect
the disposable copy. The application remains unchanged.

## Privacy and retention

Proposal text, source snapshots and decisions are private business artifacts,
stored under the Git common directory's `vita-tree/factual-reviews/` and in
checkpoints/results. Global run summaries contain state, step, revisions, count
and decision time, never wording. These documents are not diagnostic exports or
provider logs. Normal application Save review lists factual result files before
including them in a CV repository commit.

Checkpoint limits remain 7 days, 20 terminal preparations, 256 MB total and 32 MB
per checkpoint. Expiration forces regeneration and fresh factual review; it never
silently reapproves a proposal. Captured review/provenance records, application
drafts and run history are retained with the existing run artifacts rather than
silently deleted by checkpoint cleanup. Stop the server before explicitly removing
old private run/review caches. Review payloads are capped at 32 MB, documents at
2 MB and 500 changes; disposable review work is removed after each operation.

Legacy backends without this contract do not acquire factual verification. Install
`vita-tree[ai]` to obtain the compatible backend, or update the connected Vita CV
installation. An invalid or incomplete known contract fails closed.

## Verification

`tests/test_factual_contract.py` covers positional mixed decisions, insertions,
deletions, repeated text, exact newlines, rejected letters and malformed choices.
`tests/smoke/run_factual_contract.py` exercises the real Vita CV API using synthetic
documents and no providers, including conflicts, restart, interrupted decision
publication and checkpoint invalidation. CI runs that contract suite on Windows
and Linux against the minimum supported Vita CV 2.8.0.

`tests/browser_factual_reviews.py` covers keyboard decisions, cancellation,
provenance, graph AI settings, refresh, retries, stale drafts, both themes/mobile,
the write-authentication boundary and a real selectable Cover PDF. All test
content is synthetic; no AI provider is called.
