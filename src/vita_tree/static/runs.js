import {tasks} from './workflow.js';
// Global background run monitor. Polling is independent of branch navigation.
export const isActiveRun = run => run && ['queued', 'running'].includes(run.status);
export const runLabel = run => run.factualReview?({pending:'Needs factual review',resolved:'Ready to continue',unavailable:'Review unavailable'}[run.factualReview.state]||'Review unavailable'):({queued:'Queued', preparing:'Preparing', extract:'Identifying requirements', review:'Reviewing CV', cover:'Writing cover letter', analyze:'Checking CV match', adapt:'Tailoring CV',
  preflight:'Checking setup', validating:'Checking results', completed:'Completed', failed:'Couldn’t finish', interrupted:'Stopped before finishing'}[run.step] || run.status);
export const runSteps = run => {
  const selected=(run.stages || []).filter(stage=>stage.status!=='skipped'&&stage.id!=='validating');
  return selected.map(stage=>tasks.find(task=>task.id===stage.id)?.title).join(' → ') || (run.stages?.length?'Final checks':'Preparation');
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
    } catch(error) {$('#runs-error').textContent = 'Preparation updates are unavailable. Reconnecting…';}
    finally {pending = false;}
  }
  async function poll() {await refresh(); setTimeout(poll, 1500);}
  return {start: poll, refresh};
}
