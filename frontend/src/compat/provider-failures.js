// Safe public summaries are produced from typed backend evidence by the server.
export function failureText(run, step) {
  const entry=run?.failures?.[step];
  if(!entry)return '';
  const requested=run.stepConfig?.[step];
  const route=entry.routeEvidence==='backend'
    ? `Effective: ${entry.provider||'provider unreported'} / ${entry.model||'model unreported'}`
    : `Effective route unreported${requested?`; captured request: ${requested.provider} / ${requested.model||'provider default'}`:''}`;
  const retry=entry.retryable===true?'Retryable':entry.retryable===false?'Needs attention before retry':'Retryability unknown';
  return `${entry.title} (${entry.category.replaceAll('_',' ')})${entry.httpStatus?` · HTTP ${entry.httpStatus}`:''}. ${route}. ${retry}; ${entry.attempts??'unknown'} provider attempts${entry.exhausted?' · retry budget exhausted':''}. ${entry.retryAfterSeconds!=null?`Provider asks to wait ${entry.retryAfterSeconds}s. `:''}${entry.action}`;
}
export function runFailureText(run) {
  return Object.keys(run?.failures||{}).map(step=>`${step}: ${failureText(run,step)}`).join(' ');
}
