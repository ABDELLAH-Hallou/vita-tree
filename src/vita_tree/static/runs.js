import {tasks} from './workflow.js';
// Global background run monitor. Polling is independent of branch navigation.
export const isActiveRun = run => run && ['queued', 'running'].includes(run.status);
export const runLabel = run => ({queued:'Queued', preparing:'Preparing', extract:'Extracting', review:'Reviewing', cover:'Writing cover letter', analyze:'Analyzing', adapt:'Adapting',
  validating:'Validating', completed:'Completed', failed:'Failed', interrupted:'Interrupted'}[run.step] || run.status);
export const runSteps = run => {
  const selected=(run.stages || []).filter(stage=>stage.status!=='skipped'&&stage.id!=='validating');
  return selected.map(stage=>tasks.find(task=>task.id===stage.id)?.title).join(' → ') || (run.stages?.length?'Validation':'Workflow');
};

export function createRunMonitor({api, changed}) {
  const $ = selector => document.querySelector(selector);
  let signature = '', pending = false;
  async function refresh() {
    if(pending) return;
    pending = true;
    try {
      const result = await api('/api/jobs');
      const runs = result.runs;
      const next = JSON.stringify(runs.map(({elapsedSeconds, ...run}) => run));
      $('#runs-error').textContent = '';
      if(next !== signature) {signature = next; await changed(runs);}
    } catch(error) {$('#runs-error').textContent = 'Run status is unavailable. Reconnecting…';}
    finally {pending = false;}
  }
  async function poll() {await refresh(); setTimeout(poll, 1500);}
  return {start: poll, refresh};
}
