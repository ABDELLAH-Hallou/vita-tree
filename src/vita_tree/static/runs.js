// Global background run monitor. Polling is independent of branch navigation.
export const isActiveRun = run => run && ['queued', 'running'].includes(run.status);
export const runLabel = run => ({queued:'Queued', preparing:'Preparing', analyze:'Analyzing', adapt:'Adapting',
  validating:'Validating', completed:'Completed', failed:'Failed', interrupted:'Interrupted'}[run.step] || run.status);

export function createRunMonitor({api, openRun, changed}) {
  const $ = selector => document.querySelector(selector);
  let runs = [], signature = '', pending = false;
  const text = (tag, content, className) => {
    const element = document.createElement(tag); element.textContent = content;
    if(className) element.className = className;
    return element;
  };
  const timestamp = value => value ? new Date(value * 1000).toLocaleString() : '—';
  const duration = value => value < 60 ? `${Math.floor(value)}s` : `${Math.floor(value / 60)}m ${Math.floor(value % 60)}s`;
  function elapsed() {
    document.querySelectorAll('[data-run-time]').forEach(element => {
      const run = runs.find(item => item.id === element.dataset.runTime);
      const seconds = run?.startedAt ? Math.max(0, (run.finishedAt || Date.now()/1000) - run.startedAt) : 0;
      element.textContent = run?.startedAt ? `Elapsed ${duration(seconds)}` : 'Waiting for a slot';
    });
  }
  async function select(run, button) {
    button.disabled = true;
    try {await openRun(run); await refresh();}
    catch(error) {$('#runs-error').textContent = error.message; $('#ai-runs').hidden = false;}
    finally {button.disabled = false;}
  }
  function render() {
    const active = runs.filter(isActiveRun), unread = runs.filter(run => !isActiveRun(run) && !run.reviewed);
    $('#runs-count').textContent = active.length || unread.length || '';
    $('#runs-summary').textContent = `${active.length} running · ${unread.length} to review · Independent sessions`;
    $('#runs-list').replaceChildren();
    if(!runs.length) $('#runs-list').append(text('p', 'No AI runs yet. Start Analyze & adapt from a branch.', 'helper'));
    for(const run of runs) {
      const card = document.createElement('article'); card.className = 'run-card'; card.dataset.runId = run.id;
      card.dataset.status = run.status;
      const heading = document.createElement('div'); heading.className = 'run-heading';
      heading.append(text('strong', run.opportunity || run.branch), text('span', runLabel(run) + (!isActiveRun(run) && !run.reviewed ? ' · New' : ''), 'run-status'));
      const config = [run.provider || 'Provider default', run.model || 'Default model', run.reasoning || 'Default reasoning', run.language].filter(Boolean).join(' · ');
      const times = text('p', `Submitted ${timestamp(run.createdAt)} · Started ${timestamp(run.startedAt)} · Finished ${timestamp(run.finishedAt)}`, 'run-times');
      const clock = text('span', '', 'run-elapsed'); clock.dataset.runTime = run.id;
      const button = text('button', isActiveRun(run) ? 'Open branch' : 'Review result');
      button.type = 'button'; button.onclick = () => select(run, button);
      const footer = document.createElement('div'); footer.className = 'run-footer'; footer.append(clock, button);
      card.append(heading, text('p', config, 'run-config'), text('p', run.message, 'run-message'), times, footer);
      $('#runs-list').append(card);
    }
    $('#run-notifications').replaceChildren();
    for(const run of unread.slice(0, 3)) {
      const button = text('button', `${runLabel(run)}: ${run.branch} — Review`, 'run-notification');
      button.type = 'button'; button.dataset.runId = run.id; button.onclick = () => select(run, button);
      $('#run-notifications').append(button);
    }
    if(unread.length > 3) {
      const more = text('button', `View all ${unread.length} results`, 'quiet');
      more.onclick = () => {$('#ai-runs').hidden = false; $('#ai-runs').scrollIntoView({block:'start'});};
      $('#run-notifications').append(more);
    }
    $('#run-notifications').hidden = !unread.length;
    elapsed();
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
      else elapsed();
    } catch(error) {$('#runs-error').textContent = 'Run status is unavailable. Reconnecting…';}
    finally {pending = false;}
  }
  async function poll() {await refresh(); setTimeout(poll, 1500);}
  $('#show-runs').onclick = () => {$('#ai-runs').hidden = !$('#ai-runs').hidden; $('#show-runs').setAttribute('aria-expanded', String(!$('#ai-runs').hidden));};
  $('#hide-runs').onclick = () => {$('#ai-runs').hidden = true; $('#show-runs').setAttribute('aria-expanded', 'false');};
  return {start: poll, refresh};
}
