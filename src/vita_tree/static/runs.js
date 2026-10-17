import {tasks} from './workflow.js';
// Global background run monitor. Polling is independent of branch navigation.
export const isActiveRun = run => run && ['queued', 'running'].includes(run.status);
export const runLabel = run => ({queued:'Queued', preparing:'Preparing', extract:'Extracting', review:'Reviewing', cover:'Writing cover letter', analyze:'Analyzing', adapt:'Adapting',
  validating:'Validating', completed:'Completed', failed:'Failed', interrupted:'Interrupted'}[run.step] || run.status);
export const runSteps = run => {
  const selected=(run.stages || []).filter(stage=>stage.status!=='skipped'&&stage.id!=='validating');
  return selected.map(stage=>tasks.find(task=>task.id===stage.id)?.title).join(' → ') || (run.stages?.length?'Validation':'Workflow');
};

export function createRunMonitor({api, openRun, changed}) {
  const $ = selector => document.querySelector(selector);
  let runs = [], signature = '', pending = false, expanded = false;
  const text = (tag, content, className) => {
    const element = document.createElement(tag); element.textContent = content;
    if(className) element.className = className;
    return element;
  };
  async function select(run, button) {
    button.disabled = true;
    try {await openRun(run); await refresh();}
    catch(error) {$('#runs-error').textContent = error.message;}
    finally {button.disabled = false;}
  }
  function render() {
    const unread = runs.filter(run => !isActiveRun(run) && !run.reviewed);
    $('#run-notifications').replaceChildren();
    for(const run of unread.slice(0, expanded ? unread.length : 3)) {
      const button = text('button', `${runLabel(run)}: ${run.branch} — Review`, 'run-notification');
      button.type = 'button'; button.dataset.runId = run.id; button.onclick = () => select(run, button);
      $('#run-notifications').append(button);
    }
    if(unread.length > 3) {
      const more = text('button', expanded ? 'Show fewer results' : `View all ${unread.length} results`, 'quiet');
      more.type = 'button';more.setAttribute('aria-expanded', String(expanded));
      more.onclick = () => {expanded = !expanded;render();$('#run-notifications .quiet')?.focus();};
      $('#run-notifications').append(more);
    }
    $('#run-notifications').hidden = !unread.length;
  }
  async function refresh() {
    if(pending) return;
    pending = true;
    try {
      const result = await api('/api/jobs');
      runs = result.runs;
      const next = JSON.stringify(runs.map(({elapsedSeconds, ...run}) => run));
      $('#runs-error').textContent = '';
      if(next !== signature) {signature = next; render(); await changed(runs);}
    } catch(error) {$('#runs-error').textContent = 'Run status is unavailable. Reconnecting…';}
    finally {pending = false;}
  }
  async function poll() {await refresh(); setTimeout(poll, 1500);}
  return {start: poll, refresh};
}
