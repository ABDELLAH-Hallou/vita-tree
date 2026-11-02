import "./compat/feature-styles.css";
import "./styles/tokens.css";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./api/client";
import { ApplicationShell } from "./components/ApplicationShell";

const host = document.getElementById("react-root");
if (!host) throw new Error("Vita Tree could not find its application root.");
flushSync(() =>
  createRoot(host).render(
    <QueryClientProvider client={queryClient}>
      <ApplicationShell />
    </QueryClientProvider>,
  ),
);
// Preserve the tested edit/review/publication services while moving their view
// ownership to React. Editors and PDF.js retain their own DOM/lifecycle boundary.
try {
  await import("./compat/app.js");
  host.dataset.ready = "true";
} catch (error) {
  const message = document.createElement("p");
  message.setAttribute("role", "alert");
  message.textContent =
    error instanceof Error
      ? error.message
      : "The application could not start. Reload to try again.";
  host.prepend(message);
  throw error;
}
