# Reviewed job requirements

Open **Identify job requirements (Extract) → View job requirements**. This opens a separate review dialog and preserves any unapplied AI settings. The workflow header also has **Job requirements**.

For a new job description, Extract produces a canonical draft using Vita CV's JD-only requirements generator. The candidate CV is not available to that generator. Extract retains its verified checkpoint and pauses the workflow for human review. No downstream AI call starts before approval. The existing extraction report remains available as a separate artifact.

Capabilities show required, preferred, or unclear classifications, source job IDs, line ranges, exact quotes, and canonical weights. Employment conditions are separate and unscored. **View source** focuses and highlights the referenced job-description lines. Conflicting headings remain unclear. Vita CV validates the schema, deduplication, IDs, classifications, weights, and sources; Tree does not infer them from prose.

Correct wording, category, ambiguity, and references; add or remove requirements as needed. **Save new draft revision** validates corrections and retains a new immutable revision. Explicit Required/Preferred source wording cannot be contradicted: use Unclear or correct the job description itself. Review the saved revision, check the confirmation, and choose **Approve revision**. Closing the dialog discards only unsaved corrections; it never approves or rewrites a saved definition.

After approval, use **Retry preparation** to continue with the captured AI setup. Matching Extract checkpoints remain reusable. Changed definitions invalidate downstream checkpoints and old analysis context. New analysis and review reports must identify the exact approved revision. Runs record a private immutable definition snapshot, with a revision link in the graph header and attempt history. Historical views are read only and distinguish the captured revision from the current approval.

Applications sharing identical `job.md` content reuse the shared canonical definition under Git's common `.git/vita/requirements` directory (or the configured `VITA_REQUIREMENTS_DIR`). A changed job description needs its own approval. Saving corrections on one application blocks dependent new work on all applications using that definition. Running work checks the captured definition again before atomic publication; concurrent edits preserve the application and retain results separately.

An unapproved draft created by `vita requirements draft` can also be reviewed directly when its local state points to the current job description. Local **Final checks** remain available without requirement approval.

Canonical revisions, approval provenance, and run snapshots are private local state, retained alongside run history. They are not removed by the seven-day execution-checkpoint cleanup: older assessments must remain inspectable. No job text, requirements, or credentials enter the global runs list. Back up the Git common directory before manually clearing history. Vita CV 2.8 or later is required for this interface's canonical contract; older backends are not labelled as approved.
