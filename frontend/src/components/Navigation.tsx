import { useEffect, useRef, useState } from "react";
import { Dialog, DropdownMenu } from "radix-ui";
import styles from "../styles/Workspace.module.css";

const actions = [
  { name: "New application", target: "#new-branch" },
  { name: "All applications", target: '[data-filter="all"]' },
  { name: "In progress", target: '[data-filter="running"]' },
  { name: "Needs review", target: '[data-filter="review"]' },
  { name: "Needs attention", target: '[data-filter="failed"]' },
  { name: "Import jobs", target: "#open-jobenu" },
  { name: "Activity & support", target: "#show-activity" },
];
let navigationVersion = 0;
let cancelPendingNavigation: (() => void) | undefined;
function perform(target: string) {
  cancelPendingNavigation?.();
  const version = ++navigationVersion;
  const apply = () => {
    if (target.startsWith("[data-filter") || target === "#open-jobenu") {
      const workspace = document.querySelector<HTMLElement>("#workspace");
      if (workspace && !workspace.hidden) {
        document.querySelector<HTMLButtonElement>("#back")?.click();
        // The existing controller owns the unsaved-draft confirmation. A
        // cancelled confirmation must cancel navigation as well.
        if (!workspace.hidden) return;
      }
      const imports = document.querySelector<HTMLElement>("#jobenu-import");
      if (imports && !imports.hidden && target !== "#open-jobenu")
        document.querySelector<HTMLButtonElement>("#jobenu-back")?.click();
    }
    const button = document.querySelector<HTMLButtonElement>(target);
    if (button && !button.disabled) button.click();
  };
  requestAnimationFrame(() => {
    if (version !== navigationVersion) return;
    if (document.querySelector(target)) return apply();
    // The React menu is ready before the feature controllers finish loading.
    // Keep this one user action until its control exists; a newer choice cancels it.
    const observer = new MutationObserver(() => {
      if (!document.querySelector(target)) return;
      cleanup();
      if (version === navigationVersion) apply();
    });
    const cleanup = () => {
      observer.disconnect();
      window.clearTimeout(timeout);
      if (cancelPendingNavigation === cleanup)
        cancelPendingNavigation = undefined;
    };
    const timeout = window.setTimeout(cleanup, 10000);
    cancelPendingNavigation = cleanup;
    observer.observe(document.body, { childList: true, subtree: true });
  });
}
export function ThemeButton() {
  const [theme, setTheme] = useState(
    document.documentElement.dataset.theme || "light",
  );
  useEffect(() => {
    const media = matchMedia("(prefers-color-scheme: dark)");
    const change = () => {
      let saved = null;
      try {
        saved = localStorage.getItem("vita-tree-theme");
      } catch {}
      if (!saved || saved === "system")
        setTheme(media.matches ? "dark" : "light");
    };
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  const label = `Switch to ${theme === "dark" ? "light" : "dark"} mode`;
  return (
    <button
      id="theme"
      type="button"
      className="theme-toggle"
      aria-label={label}
      title={label}
      onClick={() => {
        const value = theme === "dark" ? "light" : "dark";
        try {
          localStorage.setItem("vita-tree-theme", value);
        } catch {}
        setTheme(value);
      }}
    >
      <svg
        className={theme === "dark" ? "theme-moon" : "theme-sun"}
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        {theme === "dark" ? (
          <path d="M20.8 13A9 9 0 0 1 11 3.2 9 9 0 1 0 20.8 13Z" />
        ) : (
          <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" />
          </>
        )}
      </svg>
    </button>
  );
}
export function QuickActions() {
  const [open, setOpen] = useState(false),
    [search, setSearch] = useState("");
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const key = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "k")
        return;
      if (document.querySelector("dialog[open]")) return;
      const target = event.target;
      if (
        target instanceof Element &&
        target.closest('input,textarea,[contenteditable="true"],.cm-editor')
      )
        return;
      event.preventDefault();
      setOpen((value) => !value);
      setSearch("");
    };
    addEventListener("keydown", key);
    return () => removeEventListener("keydown", key);
  }, []);
  return (
    <Dialog.Root
      open={open}
      onOpenChange={(value) => {
        setOpen(value);
        if (value) setSearch("");
      }}
    >
      <Dialog.Trigger asChild>
        <button
          type="button"
          className={styles.quickTrigger}
          aria-label="Quick actions"
        >
          <span>Quick actions</span>
          <kbd>Ctrl K</kbd>
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className={styles.overlay} />
        <Dialog.Content
          className={styles.command}
          onOpenAutoFocus={(event) => {
            event.preventDefault();
            input.current?.focus();
          }}
        >
          <div className={styles.commandHeading}>
            <Dialog.Title>Quick actions</Dialog.Title>
            <Dialog.Close aria-label="Close quick actions">Close</Dialog.Close>
          </div>
          <Dialog.Description className={styles.commandDescription}>
            Jump to an application task.
          </Dialog.Description>
          <label className={styles.commandSearch}>
            Find an action
            <input
              ref={input}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search actions…"
            />
          </label>
          <div className={styles.commandItems}>
            {actions
              .filter((action) =>
                action.name.toLowerCase().includes(search.toLowerCase()),
              )
              .map((action) => (
                <button
                  key={action.target}
                  type="button"
                  onClick={() => {
                    setOpen(false);
                    perform(action.target);
                  }}
                >
                  {action.name}
                  <span aria-hidden="true">→</span>
                </button>
              ))}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
export function NavigationMenu() {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          className={styles.navigationTrigger}
          aria-label="Navigation"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
          <span>Menu</span>
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className={styles.menu}
          align="end"
          sideOffset={8}
          aria-label="Application navigation"
        >
          {actions.map((action) => (
            <DropdownMenu.Item
              key={action.target}
              className={styles.menuItem}
              onSelect={() => perform(action.target)}
            >
              {action.name}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
