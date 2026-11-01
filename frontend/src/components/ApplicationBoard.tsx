import { memo } from "react";
export const ApplicationBoard = memo(function ApplicationBoard() {
  return (
    <section id="board">
      <div className="board-layout">
        <aside className="board-nav" aria-label="Application filters">
          <p className="nav-label">Applications</p>
          <button data-filter="all" aria-pressed="true">
            <span>All applications</span>
            <span id="filter-all">0</span>
          </button>
          <button data-filter="running" aria-pressed="false">
            <span>
              <i className="status-dot running"></i>In progress
            </span>
            <span id="filter-running">0</span>
          </button>
          <button data-filter="review" aria-pressed="false">
            <span>
              <i className="status-dot succeeded"></i>Needs review
            </span>
            <span id="filter-review">0</span>
          </button>
          <button data-filter="failed" aria-pressed="false">
            <span>
              <i className="status-dot failed"></i>Needs attention
            </span>
            <span id="filter-failed">0</span>
          </button>
          <button id="show-activity" data-open-diagnostics="">
            Activity &amp; support
          </button>
          <div className="workspace-note">
            <strong>A tailored CV for every opportunity</strong>
            <p>
              Choose a starting CV, add the job description, and prepare your
              application. Review the results before saving.
            </p>
            <span>Powered by Vita CV</span>
          </div>
        </aside>
        <div className="branch-table">
          <div className="page-heading">
            <div>
              <h1>
                Applications{" "}
                <span id="total-count" className="count">
                  0
                </span>
              </h1>
              <p className="subtitle">
                A tailored CV and cover letter for every opportunity.
              </p>
            </div>
            <button id="new-branch" className="primary" disabled={true}>
              ＋ New application
            </button>
          </div>
          <div className="list-toolbar">
            <label className="search">
              <span aria-hidden="true">⌕</span>
              <input
                id="search"
                type="search"
                placeholder="Search applications…"
                aria-label="Search applications"
              />
              <kbd>/</kbd>
            </label>
            <button id="refresh" className="quiet">
              ↻ Refresh
            </button>
          </div>
          <div className="bulk-review-toolbar">
            <label>
              <input id="select-review-visible" type="checkbox" /> Select
              visible applications with unreviewed results
            </label>
            <button id="bulk-review" disabled={true}>
              Mark selected as reviewed
            </button>
            <span id="bulk-review-count" className="helper"></span>
          </div>
          <p
            id="bulk-review-status"
            className="bulk-review-status"
            role="status"
            hidden={true}
          ></p>
          <div className="list-head">
            <span>Application</span>
            <span>Last saved update</span>
            <span>Updated</span>
          </div>
          <div id="branch-list" aria-live="polite">
            <p className="empty">Loading applications…</p>
          </div>
          <footer className="list-footer">
            <span id="result-count"></span>
            <span>Latest activity first</span>
          </footer>
        </div>
      </div>
    </section>
  );
});
