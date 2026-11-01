import { memo } from "react";
export const ApplicationWorkspace = memo(function ApplicationWorkspace() {
  return (
    <section id="workspace" hidden={true}>
      <div className="workspace-heading">
        <div>
          <button id="back" className="back">
            ← All applications
          </button>
          <h1 id="branch-title"></h1>
          <p id="workspace-caption" className="subtitle"></p>
        </div>
        <div className="actions">
          <button id="reload">↻ Reload</button>
          <button id="branch-from">＋ Use this CV for a new application</button>
        </div>
      </div>
      <div className="setup-bar">
        <p id="setup-summary" role="status">
          Check your saved project before preparing it.
        </p>
        <button data-open-setup="" type="button">
          Check setup
        </button>
      </div>
      <section className="workflow-panel" aria-labelledby="workflow-title">
        <header className="workflow-heading">
          <div>
            <h2 id="workflow-title">Prepare your application</h2>
            <p id="workflow-summary" role="status">
              Choose how to prepare this application.
            </p>
          </div>
          <div className="actions">
            <label className="run-picker">
              <span className="sr-only">Preparation history</span>
              <select id="workflow-run" aria-label="Preparation history">
                <option value="draft">New preparation</option>
              </select>
            </label>
            <button id="inspect-run" className="quiet" hidden={true}>
              Execution details
            </button>
            <button id="view-run" className="quiet" hidden={true}>
              View results
            </button>
            <button id="requirements-current-open">Job requirements</button>
            <button id="requirements-captured" hidden={true}></button>
            <button id="review-facts" hidden={true}>
              Review factual changes
            </button>
            <button id="resume-run" hidden={true}>
              Retry preparation
            </button>
            <button id="mark-run-reviewed" hidden={true}>
              Mark as reviewed
            </button>
            <button
              id="toggle-workflow"
              className="quiet"
              aria-expanded="true"
              aria-controls="workflow-body"
            >
              Hide steps
            </button>
          </div>
        </header>
        <div id="workflow-action" className="workflow-action">
          <div>
            <strong>Your next step</strong>
            <p id="workflow-next-help"></p>
          </div>
          <button id="workflow-next" className="primary">
            Prepare application
          </button>
        </div>
        <div id="workflow-body">
          <div
            id="workflow-graph"
            className="dag"
            role="group"
            aria-label="Application preparation steps"
          ></div>
          <footer className="workflow-footer">
            <span>
              Click an AI step to configure it. Prepare everything, choose a few
              steps, or start one step on its own.
            </span>
            <span>
              <i className="status-dot running"></i>In progress{" "}
              <i className="status-dot succeeded"></i>Done{" "}
              <i className="status-dot failed"></i>Couldn’t finish
            </span>
          </footer>
          <div id="task-inspector" className="task-inspector" hidden={true}>
            <div>
              <strong id="task-title"></strong>
              <p id="task-description"></p>
              <span id="task-status" className="helper"></span>
            </div>
            <div className="actions">
              <button id="task-requirements" hidden={true}>
                Review job requirements
              </button>
              <button id="task-configure">Configure AI</button>
              <button id="inspect-step" className="quiet" hidden={true}>
                Inspect execution
              </button>
              <button id="task-output">View results</button>
              <button id="task-run" className="primary">
                Start this step
              </button>
            </div>
          </div>
        </div>
      </section>
      <dialog
        id="factual-review-panel"
        className="factual-review"
        aria-labelledby="factual-review-title"
        hidden={true}
      >
        <div className="review-heading">
          <h2 id="factual-sheet-title">Check your changes</h2>
          <button
            id="close-factual-review"
            type="button"
            aria-label="Close factual review"
          >
            Close
          </button>
        </div>
        <div className="review-scroll">
          <h2 id="factual-review-title" tabIndex={-1}>
            Review factual changes
          </h2>
          <p id="factual-review-summary"></p>
          <p className="helper">
            Check that the proposed wording is accurate. Reject keeps your
            original wording. Keeping all originals for a cover letter preserves
            the previous letter, if any.
          </p>
          <details className="technical-details">
            <summary>Captured revision</summary>
            <code id="factual-review-revision"></code>
          </details>
          <form id="factual-review-form">
            <div id="factual-bulk" className="review-bulk">
              <span id="factual-choice-count" role="status"></span>
              <button id="accept-all-facts" type="button">
                Accept all
              </button>
              <button id="reject-all-facts" type="button">
                Keep all originals
              </button>
            </div>
            <div id="factual-review-items"></div>
            <details>
              <summary>Full proposed LaTeX · syntax check</summary>
              <div
                id="factual-source-preview"
                className="review-source-preview"
              ></div>
            </details>
            <p id="factual-provenance" className="helper" hidden={true}></p>
          </form>
        </div>
        <div className="review-controls">
          <label id="factual-review-confirmation" className="factual-confirm">
            <input
              id="confirm-factual-meaning"
              form="factual-review-form"
              type="checkbox"
              required={true}
            />{" "}
            I reviewed every change and confirm the factual meaning of my
            accepted and edited wording.
          </label>
          <p id="factual-review-error" className="error" role="alert"></p>
          <p id="factual-review-progress" role="status"></p>
          <div className="panel-footer">
            <span>
              Your application updates after the remaining steps and final
              checks succeed.
            </span>
            <div className="actions">
              <button id="cancel-factual-review" type="button">
                Close without changes
              </button>
              <button
                id="apply-factual-review"
                form="factual-review-form"
                className="primary"
                type="submit"
              >
                Approve &amp; continue
              </button>
            </div>
          </div>
        </div>
      </dialog>
      <div className="workspace-toolbar">
        <div className="tabs" role="tablist" aria-label="Application view">
          <button role="tab" data-view="structure" aria-selected="true">
            Edit CV
          </button>
          <button role="tab" data-view="source" aria-selected="false">
            Source · Advanced
          </button>
          <button role="tab" data-view="pdf" aria-selected="false">
            PDF preview
          </button>
          <button role="tab" data-view="changes" aria-selected="false">
            Changes <span id="change-count"></span>
          </button>
          <button role="tab" data-view="ai" aria-selected="false">
            Job details &amp; AI <span id="ai-dot"></span>
          </button>
        </div>
        <div id="document-actions" className="actions">
          <span id="save-state">Saved</span>
          <button id="save-source" disabled={true}>
            Save draft
          </button>
          <button id="commit-push" className="primary" disabled={true}>
            Save
          </button>
        </div>
      </div>
      <div id="notice" className="notice" role="status" hidden={true}></div>
      <details id="message-details" className="technical-details" hidden={true}>
        <summary>Technical details</summary>
        <pre id="message-technical"></pre>
      </details>
      <div id="structure-hint" className="view-hint">
        <span>Double-click text in your current CV to edit it.</span>
        <span>PDF shows the exact layout.</span>
      </div>
      <section
        id="file-navigation"
        className="file-navigation"
        aria-label="CV files"
      >
        <label htmlFor="cv-file">CV file</label>
        <select id="cv-file"></select>
        <p id="file-help" className="helper">
          Each file is edited separately. PDF assembles the complete CV;
          Structure approximates each file without executing macros or
          conditional includes.
        </p>
        <details id="include-problems" hidden={true}>
          <summary>Include files need attention</summary>
          <ul id="include-diagnostics"></ul>
        </details>
      </section>
      <div id="pdf-toolbar" className="view-hint" hidden={true}>
        <div className="actions">
          <label>
            Document{" "}
            <select id="pdf-document">
              <option value="cv">CV comparison</option>
              <option value="cover">Cover letter</option>
            </select>
          </label>
          <details className="pdf-settings">
            <summary>Advanced PDF settings</summary>
            <label>
              PDF engine{" "}
              <select id="engine">
                <option value="auto">Automatic</option>
                <option>pdflatex</option>
                <option>xelatex</option>
                <option>lualatex</option>
              </select>
            </label>
          </details>
          <button id="compile">Create PDF previews</button>
        </div>
        <div className="actions">
          <label>
            Zoom{" "}
            <select id="zoom">
              <option value="fit">Fit width</option>
              <option value="1">100%</option>
              <option value="1.25">125%</option>
              <option value="1.5">150%</option>
            </select>
          </label>
          <span>Select and copy text directly from the PDF</span>
        </div>
      </div>
      <div id="comparison" className="comparison">
        <section className="pane">
          <header className="pane-heading">
            <div>
              <span className="pane-dot"></span>
              <strong>Before</strong>
              <span id="original-label"></span>
            </div>
            <span className="pill">View only</span>
          </header>
          <div id="original-document" className="document-scroll">
            <article className="cv-document"></article>
          </div>
          <div
            id="original-source"
            className="source-editor"
            hidden={true}
          ></div>
          <div id="original-pdf" className="pdf-scroll" hidden={true}></div>
        </section>
        <section className="pane">
          <header className="pane-heading">
            <div>
              <span className="pane-dot purple"></span>
              <strong>Current CV</strong>
              <span id="current-label"></span>
            </div>
            <span id="version-label" className="pill accent">
              Editable
            </span>
          </header>
          <div id="current-document" className="document-scroll">
            <article className="cv-document"></article>
          </div>
          <div
            id="current-source"
            className="source-editor"
            hidden={true}
          ></div>
          <div id="current-pdf" className="pdf-scroll" hidden={true}></div>
        </section>
      </div>
      <section
        id="cover-pdf-pane"
        className="pane cover-pdf-pane"
        hidden={true}
      >
        <header className="pane-heading">
          <strong>Cover letter</strong>
          <span id="cover-pdf-label" className="helper"></span>
        </header>
        <div id="cover-pdf" className="pdf-scroll"></div>
      </section>
      <section id="changes-panel" className="content-panel" hidden={true}>
        <div className="panel-heading">
          <h2>What changed</h2>
          <p>Compared with the original shown on the left.</p>
        </div>
        <pre id="diff" className="diff"></pre>
      </section>
      <section id="ai-panel" className="ai-grid" hidden={true}>
        <div className="content-panel">
          <div className="panel-heading">
            <h2>Job description</h2>
            <p>
              Keep the role, company, and requirements with this application.
            </p>
          </div>
          <textarea
            id="job-description"
            aria-label="Job description"
            placeholder="Paste the role, company, requirements, and full job description…"
          ></textarea>
          <div className="panel-footer">
            <span id="job-state"></span>
            <button id="save-job">Save job description</button>
          </div>
        </div>
        <div className="content-panel">
          <div className="panel-heading">
            <h2>Prepare with AI</h2>
            <p>
              Connect your AI, choose the steps, and prepare your application.
              Customize a step whenever it needs a different model.
            </p>
          </div>
          <div id="ai-configuration"></div>
          <div className="ai-language">
            <label>
              Output language
              <select id="language" disabled={true}>
                <option value="en">English</option>
              </select>
            </label>
          </div>
          <label className="review-policy">
            Review mode
            <select id="review-policy">
              <option value="manual">Review before continuing</option>
              <option value="automatic">Automatic · accept AI proposals</option>
            </select>
            <small>
              Automatic mode accepts requirements and factual changes for this
              run. Validation still runs. It does not save to Git or push.
            </small>
          </label>
          <fieldset className="workflow-options">
            <legend>Choose your steps</legend>
            <label>
              <input id="step-extract" type="checkbox" />
              <span>
                Identify job requirements
                <small id="hint-extract">
                  Understand what the employer is looking for.
                </small>
                <small className="step-ai-summary"></small>
              </span>
            </label>
            <label>
              <input id="step-analyze" type="checkbox" />
              <span>
                Check CV match<small>See how your CV matches the job.</small>
                <small className="step-ai-summary"></small>
              </span>
            </label>
            <label>
              <input id="step-adapt" type="checkbox" />
              <span>
                Tailor CV<small>Adjust your CV for this opportunity.</small>
                <small className="step-ai-summary"></small>
              </span>
            </label>
            <label>
              <input id="step-review" type="checkbox" />
              <span>
                Review CV with AI
                <small id="hint-review">Get feedback on your current CV.</small>
                <small className="step-ai-summary"></small>
              </span>
            </label>
            <label>
              <input id="step-cover" type="checkbox" />
              <span>
                Cover letter
                <small id="hint-cover">
                  Write the cover letter and create its PDF.
                </small>
                <small className="step-ai-summary"></small>
              </span>
            </label>
          </fieldset>
          <p
            id="ai-config-validation"
            className="ai-setup-error"
            role="alert"
            hidden={true}
          ></p>
          <details className="technical-details">
            <summary>AI connection details</summary>
            <pre id="model-details"></pre>
          </details>
          <p id="ai-capability" className="helper"></p>
          <div className="panel-footer">
            <span id="ai-status" role="status">
              Save a job description to get started
            </span>
            <div className="actions">
              <button id="run-all">Prepare application</button>
              <button id="run-adapt" className="primary">
                Start selected steps
              </button>
            </div>
          </div>
          <p className="helper privacy">
            Uses your configured AI provider and sends it the CV and job
            context.
          </p>
        </div>
        <div className="content-panel artifacts">
          <div className="panel-heading">
            <h2>AI results</h2>
            <p>Read the feedback and suggested changes for this application.</p>
          </div>
          <div id="artifacts"></div>
        </div>
        <div
          id="selected-run"
          className="content-panel artifacts"
          hidden={true}
        >
          <div className="panel-heading">
            <h2>Results from this preparation</h2>
            <p id="selected-run-info"></p>
          </div>
          <div id="attempt-history" className="attempt-history"></div>
          <div id="selected-run-files"></div>
        </div>
      </section>
      <footer className="workspace-footer">
        <details className="technical-details">
          <summary>Application details</summary>
          <p>
            Internal identifier: <code id="application-id"></code>
          </p>
          <p>
            Application folder: <code id="worktree-path"></code>
          </p>
          <p>
            CV source: <code>main.tex</code> · Job description:{" "}
            <code>job.md</code>
          </p>
        </details>
        <div className="actions">
          <span>
            Save draft keeps your edits on this computer. Save records a version
            and syncs it.
          </span>
          <button className="quiet" data-open-diagnostics="">
            Activity &amp; support
          </button>
        </div>
      </footer>
    </section>
  );
});
