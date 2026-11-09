import { createRoot, type Root } from "react-dom/client";
import { flushSync } from "react-dom";
import { ApplicationList, type ApplicationListProps } from "./ApplicationList";
import { WorkflowGraph, type WorkflowGraphProps } from "./WorkflowGraph";
const roots = new WeakMap<HTMLElement, Root>();
const graphViews = new WeakMap<HTMLElement, WorkflowGraphProps>();
function rootFor(container: HTMLElement) {
  let root = roots.get(container);
  if (!root) {
    root = createRoot(container);
    roots.set(container, root);
  }
  return root;
}
export function renderApplicationList(
  container: HTMLElement,
  props: ApplicationListProps,
) {
  flushSync(() => rootFor(container).render(<ApplicationList {...props} />));
}
export function renderWorkflowGraph(
  container: HTMLElement,
  props: WorkflowGraphProps,
) {
  graphViews.set(container, props);
  flushSync(() => rootFor(container).render(<WorkflowGraph {...props} />));
}

export function disableWorkflowGraph(container: HTMLElement) {
  const props = graphViews.get(container);
  if (props) renderWorkflowGraph(container, { ...props, disabled: true });
}
