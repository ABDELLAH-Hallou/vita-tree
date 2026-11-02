export function createSetupChecks({api,getState,getBranches,getSteps}) {
  const $=selector=>document.querySelector(selector),dialog=$('#setup-dialog');
  let busy=false,ticket=0;
  const reports=new Map();
  function render(result) {
    $('#setup-results').replaceChildren();
    $('#setup-result-heading').hidden=!result;
    $('#setup-result-heading').textContent=result?(result.ready?'Ready for your selected steps':'Something needs fixing'):'';
    $('#setup-revision').textContent=result?`Saved CV revision ${result.revision?.slice(0,12)||'unavailable'} · Engine: ${result.engine}. New or unsaved edits need another check.`:'';
    for(const check of result?.checks||[]) {
      const row=document.createElement('li');row.dataset.severity=check.severity;
      const title=document.createElement('strong');title.textContent=check.message+(check.target?' ('+check.target+')':'');
      const action=document.createElement('p');action.textContent=check.action;row.append(title,action);$('#setup-results').append(row);
    }
  }
  function summary(run) {
    const s=getState().snapshot,report=run?.preflight;
    if(report&&s)reports.set(s.branch,report);
    const result=report||(s&&reports.get(s.branch));
    const extractionOnly=result?.checks.some(c=>c.code==='extract_only');
    $('#setup-summary').textContent=run?.step==='preflight'?'Checking CV files and PDF tools…':
      result?`${result.ready?(extractionOnly?'Job details checked':'CV files checked'):'Some files need attention'}. ${result.revision!==s?.revision?'Your CV has changed since this check. ':''}${getState().dirty||getState().jobDirty?'Save your draft to check your latest changes. ':''}${result.checks.find(c=>c.severity==='error')?.message||'Files are checked again before preparation.'}`:
      'CV files are checked automatically before preparation.';
  }
  async function open() {
    const s=getState().snapshot,selected=s?.branch||new URL(location.href).searchParams.get('branch');
    const generation=++ticket;
    dialog.showModal();$('#check-setup').disabled=true;$('#setup-progress').textContent='Loading applications…';
    try {
      const branches=getBranches().length?getBranches():(await api('/api/branches')).branches;
      if(generation!==ticket||!dialog.open)return;
      $('#setup-branch').replaceChildren(...branches.map(b=>new Option(b.displayName||b.name,b.name)));
      if(branches.some(b=>b.name===selected))$('#setup-branch').value=selected;
      render(reports.get($('#setup-branch').value));$('#setup-progress').textContent=branches.length?'':'No CVs are available to check.';
      $('#check-setup').disabled=busy||!branches.length;$('#setup-branch').focus();
    } catch(error){if(generation===ticket)$('#setup-progress').textContent=error.message;}
  }
  for(const button of document.querySelectorAll('[data-open-setup]'))button.onclick=open;
  $('#setup-branch').onchange=()=>{ticket++;render(reports.get($('#setup-branch').value));$('#setup-progress').textContent='';};
  $('#setup-engine').onchange=()=>{$('#engine').value=$('#setup-engine').value;};
  $('#engine').addEventListener('change',()=>{$('#setup-engine').value=$('#engine').value;});
  $('#check-setup').onclick=async()=>{
    if(busy)return;
    const state=getState(),branch=$('#setup-branch').value,s=state.snapshot;
    if(!branch)return;
    if(!state.session){$('#setup-progress').textContent='Wait for your applications to load, then try again.';return;}
    if(s?.branch===branch&&(state.dirty||state.jobDirty)){$('#setup-progress').textContent='Save your CV and job-description drafts before checking.';return;}
    const generation=++ticket;busy=true;$('#check-setup').disabled=true;$('#setup-branch').disabled=true;$('#setup-engine').disabled=true;
    reports.delete(branch);render(null);summary();
    $('#setup-progress').textContent='Checking CV files…';
    try {
      const result=await api('/api/preflight',{branch,engine:$('#setup-engine').value,workflow:{steps:s?.branch===branch?getSteps():['analyze','adapt']},
        ...(s?.branch===branch?{revision:s.revision,jobRevision:s.jobRevision}:{})});
      reports.set(branch,result);
      if(generation!==ticket)return;
      render(result);$('#setup-progress').textContent='Check complete.';
      $('#setup-result-heading').focus();summary();
    } catch(error) {if(generation===ticket){render(null);$('#setup-progress').textContent=error.message;}}
    finally{busy=false;$('#check-setup').disabled=false;$('#setup-branch').disabled=false;$('#setup-engine').disabled=false;}
  };
  dialog.addEventListener('close',()=>{ticket++;});
  return {summary,engine:()=>$('#setup-engine').value};
}
