import { memo } from "react";
import { ApplicationBoard } from "./ApplicationBoard";
import { ApplicationWorkspace } from "./ApplicationWorkspace";
import { ThemeButton, QuickActions, NavigationMenu } from "./Navigation";
import styles from "../styles/Workspace.module.css";
export const ApplicationShell = memo(function ApplicationShell() {
  return (
    <div className={styles.application}>
      <a className="skip-link" href="#main-content">
        Skip to application
      </a>
      <header className="topbar">
        <div className="topbar-inner">
          <a className="brand" href="/" aria-label="Vita Tree home">
            <svg className="brand-mark" viewBox="0 0 32 32" aria-hidden="true">
              <path d="M8 7v13a5 5 0 0 0 5 5h11M8 13h11a5 5 0 0 0 5-5"></path>
              <circle cx="8" cy="7" r="3"></circle>
              <circle cx="24" cy="7" r="3"></circle>
              <circle cx="24" cy="25" r="3"></circle>
            </svg>
            Vita Tree
          </a>
          <span className="divider">/</span>
          <span id="repository">CV collection</span>
          <QuickActions />
          <NavigationMenu />
          <ThemeButton />
        </div>
      </header>
      <main className="shell" id="main-content" tabIndex={-1}>
        <p id="runs-error" className="helper" role="status"></p>
        <ApplicationBoard></ApplicationBoard>
        <ApplicationWorkspace></ApplicationWorkspace>
      </main>
      <dialog id="create-dialog">
        <form id="create-form">
          <div className="dialog-heading">
            <div>
              <h2>Create an application</h2>
            </div>
            <button
              type="button"
              className="close-dialog quiet"
              aria-label="Close create dialog"
            >
              ×
            </button>
          </div>
          <label>
            Starting CV<select id="base-branch" required={true}></select>
          </label>
          <label>
            Application name
            <input
              id="branch-name"
              placeholder="Company — Role"
              required={true}
              maxLength={100}
              autoComplete="off"
            />
          </label>
          <label>
            Job description
            <textarea
              id="new-job"
              placeholder="Paste the full job description…"
              required={true}
            ></textarea>
          </label>
          <p className="helper">
            Creates a separate application using this CV. Your original remains
            unchanged. You can use a saved CV or an earlier application as your
            starting point.
          </p>
          <p id="create-error" className="form-error" role="alert"></p>
          <footer className="dialog-footer">
            <button type="button" className="close-dialog">
              Cancel
            </button>
            <button type="submit" className="primary">
              Create application
            </button>
          </footer>
        </form>
      </dialog>
      <dialog id="edit-dialog">
        <form id="edit-form">
          <div className="dialog-heading">
            <div>
              <h2>Edit CV text</h2>
              <p id="edit-origin" className="helper"></p>
            </div>
            <button
              type="button"
              className="close-dialog quiet"
              aria-label="Close text editor"
            >
              ×
            </button>
          </div>
          <label>
            Text<textarea id="edit-text" required={true}></textarea>
          </label>
          <p className="helper">
            Updates the selected text in its originating file. Formatting is
            handled for you.
          </p>
          <p id="edit-error" className="form-error" role="alert"></p>
          <footer className="dialog-footer">
            <button type="button" className="close-dialog">
              Cancel
            </button>
            <button type="submit" className="primary">
              Save draft
            </button>
          </footer>
        </form>
      </dialog>
      <dialog id="commit-dialog">
        <form id="commit-form">
          <div className="dialog-heading">
            <div>
              <h2>Save</h2>
            </div>
            <button
              type="button"
              className="close-dialog quiet"
              aria-label="Close save review"
            >
              ×
            </button>
          </div>
          <p className="helper">
            Save records a version of these changes and syncs them to the
            destination below. Save draft keeps edits on this computer.
          </p>
          <dl className="commit-summary">
            <div>
              <dt>Application</dt>
              <dd id="commit-branch"></dd>
            </div>
            <div>
              <dt>Sync destination</dt>
              <dd id="commit-destination"></dd>
            </div>
          </dl>
          <details className="technical-details">
            <summary>Connection setup</summary>
            <p>
              Internal destination: <code id="sync-details"></code>
            </p>
            <p>
              For setup, configure the CV collection’s Git destination and your
              save identity.
            </p>
            <pre>
              git remote add origin &lt;destination URL&gt; git config user.name
              "Your name" git config user.email "Your email"
            </pre>
          </details>
          <div className="commit-files">
            <strong>Changes to save</strong>
            <ul id="commit-files"></ul>
            <p id="commit-empty" className="helper" hidden={true}>
              No new edits. Any versions waiting to sync will be included.
            </p>
            <p id="commit-excluded" className="helper" hidden={true}></p>
          </div>
          <label>
            Change note
            <input
              id="commit-message"
              maxLength={200}
              placeholder="Update CV for this opportunity"
              required={true}
              autoComplete="off"
            />
          </label>
          <p id="commit-progress" className="helper" role="status"></p>
          <p id="commit-error" className="form-error" role="alert"></p>
          <footer className="dialog-footer">
            <button type="button" className="close-dialog">
              Cancel
            </button>
            <button id="confirm-commit" type="submit" className="primary">
              Save
            </button>
          </footer>
        </form>
      </dialog>
      <dialog id="resume-dialog" aria-labelledby="resume-title">
        <form id="resume-form">
          <div className="dialog-heading">
            <h2 id="resume-title">Resume preparation</h2>
            <button
              type="button"
              className="close-dialog quiet"
              aria-label="Close resume review"
            >
              ×
            </button>
          </div>
          <p className="helper">
            Continue as a new attempt. Verified results are reused only when the
            captured inputs, requirements, and AI setup match. All other
            selected steps run again.
          </p>
          <p id="resume-summary"></p>
          <label id="resume-config-choice" hidden={true}>
            <input type="checkbox" id="resume-current-config" /> Use the current
            application setup instead of the captured setup
          </label>
          <h3>Reuse verified results</h3>
          <p id="resume-reuse"></p>
          <h3>Run again</h3>
          <p id="resume-rerun"></p>
          <p id="resume-adapted" className="helper" hidden={true}>
            The matching tailored CV from the earlier attempt will be used for
            the remaining steps, including the cover letter. Your current draft
            stays unchanged until the preparation finishes successfully.
          </p>
          <p className="helper">
            A change invalidates that step and all later selected steps. Final
            checks always run. Expired, missing, or unverifiable checkpoints are
            never reused.
          </p>
          <p id="resume-error" className="form-error" role="alert"></p>
          <footer className="dialog-footer">
            <button type="button" className="close-dialog">
              Cancel
            </button>
            <button id="confirm-resume" type="submit" className="primary">
              Start new attempt
            </button>
          </footer>
        </form>
      </dialog>
      <dialog id="diagnostics-dialog" aria-labelledby="diagnostics-title">
        <div className="dialog-heading">
          <div>
            <h2 id="diagnostics-title">Activity &amp; support</h2>
            <p className="helper">
              Preparation progress and help with recent problems.
            </p>
          </div>
          <button
            className="close-dialog quiet"
            aria-label="Close activity and support"
          >
            ×
          </button>
        </div>
        <div className="diagnostics-metrics">
          <div>
            <strong id="metric-active">0</strong>
            <span>In progress</span>
          </div>
          <div>
            <strong id="metric-completed">0</strong>
            <span>Completed preparations</span>
          </div>
          <div>
            <strong id="metric-failed">0</strong>
            <span>Preparations needing attention</span>
          </div>
          <div>
            <strong id="metric-requests">0</strong>
            <span>Requests this session</span>
          </div>
          <div>
            <strong id="metric-errors">0</strong>
            <span>Failed requests</span>
          </div>
          <div>
            <strong id="metric-latency">0</strong>
            <span>Average response time (ms)</span>
          </div>
        </div>
        <section
          id="execution-inspector"
          aria-label="Execution inspector"
        ></section>
        <ul id="activity-summary" className="activity-summary"></ul>
        <details className="technical-details">
          <summary>Retained retry results</summary>
          <p>
            Verified checkpoints are kept for up to 7 days, 20 preparations, and
            256 MB. Active preparations are protected. Cleanup removes only
            retry checkpoints; application drafts, preparation history, and
            review results remain.
          </p>
          <button id="cleanup-checkpoints">Clean expired checkpoints</button>
          <p id="cleanup-checkpoints-status" role="status"></p>
        </details>
        <details className="technical-details">
          <summary>Technical details</summary>
          <p id="diagnostics-uptime" className="helper"></p>
          <p className="helper">
            Log file: <code id="diagnostics-location"></code>
          </p>
          <p id="diagnostics-logging" className="helper"></p>
          <div className="diagnostics-toolbar">
            <label>
              Find an event
              <input
                id="diagnostics-search"
                type="search"
                placeholder="Request ID, step, or error type"
              />
            </label>
            <div className="actions">
              <button id="refresh-diagnostics">Refresh activity</button>
              <button id="download-diagnostics">Download support report</button>
              <a href="/metrics" target="_blank" rel="noopener">
                View performance statistics
              </a>
            </div>
          </div>
          <p id="diagnostics-error" className="form-error" role="status"></p>
          <div className="diagnostics-table">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Event</th>
                  <th>Operation</th>
                  <th>Result</th>
                  <th>Error details</th>
                  <th>Reference</th>
                </tr>
              </thead>
              <tbody id="diagnostics-events"></tbody>
            </table>
          </div>
          <p className="helper">
            Updates every 3 seconds. The last 200 events are shown. Logs exclude
            CV text, prompts, credentials, and raw AI output. Downloaded
            diagnostics also omit local log paths.
          </p>
        </details>
      </dialog>
      <dialog id="setup-dialog" aria-labelledby="setup-title">
        <div className="dialog-heading">
          <h2 id="setup-title">Check CV files</h2>
          <button
            type="button"
            className="close-dialog quiet"
            aria-label="Close setup checks"
          >
            ×
          </button>
        </div>
        <p>Find missing files or PDF tools. Your CV stays unchanged.</p>
        <label>
          CV<select id="setup-branch"></select>
        </label>
        <details id="setup-technical" className="technical-details">
          <summary>Technical details</summary>
          <label>
            PDF tool for checks and new preparations
            <select id="setup-engine">
              <option value="auto">Automatic</option>
              <option value="pdflatex">PDFLaTeX</option>
              <option value="xelatex">XeLaTeX</option>
              <option value="lualatex">LuaLaTeX</option>
            </select>
          </label>
          <p className="helper">
            Automatic uses XeLaTeX when main.tex declares fontspec, polyglossia
            or unicode-math; otherwise PDFLaTeX. Choose explicitly when a class
            or included file requires another engine. Retries preserve their
            captured engine.
          </p>
          <p>
            Use a UTF-8 LaTeX project with <code>main.tex</code> at the project
            root. Include all required classes, styles, fonts, images and
            included files in Git. PDF, Word and scanned-CV import are not
            available. A different <code>vt run --file</code> entry supports
            viewing and PDF previews; AI preparation requires{" "}
            <code>main.tex</code>.
          </p>
          <p className="helper">
            Checks compile a temporary copy with shell escape and automatic
            package installation disabled. No AI service is contacted. Only open
            templates and TeX installations you trust; these restrictions are
            not an OS sandbox.
          </p>
          <p id="setup-revision" className="helper"></p>
        </details>
        <p id="setup-progress" role="status"></p>
        <h3 id="setup-result-heading" tabIndex={-1} hidden={true}></h3>
        <ul id="setup-results"></ul>
        <footer className="dialog-footer">
          <button type="button" className="close-dialog">
            Close
          </button>
          <button type="button" id="check-setup" className="primary">
            Check files
          </button>
        </footer>
      </dialog>
      <div id="toast" className="toast" role="status" hidden={true}></div>
    </div>
  );
});
