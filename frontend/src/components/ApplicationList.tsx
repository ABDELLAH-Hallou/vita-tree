import type { ApplicationRow } from "../model";
export interface ApplicationListProps {
  rows: ApplicationRow[];
  empty: string;
  onOpen: (name: string) => void;
  onSelect: (name: string, selected: boolean) => void;
  relative: (timestamp: number) => string;
}
export function ApplicationList({
  rows,
  empty,
  onOpen,
  onSelect,
  relative,
}: ApplicationListProps) {
  if (!rows.length) return <p className="empty">{empty}</p>;
  return (
    <>
      {rows.map(
        ({ branch: b, selected, selectable, status, label, failure }) => (
          <div key={b.name} className="branch-entry" data-branch={b.name}>
            <input
              type="checkbox"
              className="select-branch-review"
              aria-label={`Select unreviewed results for ${b.displayName || b.name}`}
              disabled={!selectable}
              checked={selected}
              onChange={(event) => onSelect(b.name, event.target.checked)}
            />
            <button
              type="button"
              className="branch-row"
              aria-label={`Open ${b.displayName || b.name}`}
              onClick={() => onOpen(b.name)}
            >
              <span className="branch-cell">
                <svg
                  className="branch-icon"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                  width="18"
                  height="18"
                >
                  <path d="M6 5v11a3 3 0 0 0 3 3h9M6 10h8a4 4 0 0 0 4-4" />
                  <circle cx="6" cy="4" r="2" />
                  <circle cx="18" cy="4" r="2" />
                  <circle cx="18" cy="19" r="2" />
                </svg>
                <span className="branch-info">
                  <span className="branch-name">{b.displayName || b.name}</span>
                  <span className="branch-detail">
                    {b.local ? "Editable CV" : "View only CV"}
                  </span>
                  {label && (
                    <span className="branch-run" data-status={status}>
                      {label}
                    </span>
                  )}
                  {failure && <span className="branch-failure">{failure}</span>}
                </span>
              </span>
              <span className="commit-cell">
                <span className="commit-subject">{b.subject}</span>
                <span className="commit-meta">{b.author}</span>
              </span>
              <time
                className="branch-date"
                dateTime={b.modifiedAt}
                title={new Date(b.modifiedAt).toLocaleString()}
              >
                {relative(b.timestamp)}
              </time>
            </button>
          </div>
        ),
      )}
    </>
  );
}
