const $ = selector => document.querySelector(selector);
const state = {branches: [], session: null, snapshot: null, view: 'structure', generation: 0, pdfs: {}, pdfGeneration: 0, dirty: false, jobDirty: false, leaf: null, publishing: false, commitReview: null};
import {createLatexEditor} from './vendor/editor.mjs';
import {createRunMonitor, isActiveRun, runLabel, runSteps} from './runs.js';
import {renderGraph, graphStages, statusNames} from './workflow.js';
import {reportDetails} from './reports.js';
state.filter='all';
state.workflowChoices=new Map();
const aiSteps=['extract','analyze','adapt','review','cover'];
const stepAvailable=id=>!['extract','review','cover'].includes(id)||!!state.session?.workflow?.[id];
state.runs = [];
let runMonitor;
const editors = Object.fromEntries(['original', 'current'].map(side => [side, createLatexEditor($(`#${side}-source`), {
  label: side === 'original' ? 'Original LaTeX' : 'New version LaTeX', readOnly: true,
  onChange: value => {if(side === 'current' && state.snapshot) {state.dirty = value !== state.snapshot.content; updateSaveState();}},
  lint: async (content, signal) => {
    const response = await fetch('/api/lint', {method:'POST', signal, headers:{'Content-Type':'application/json','X-Vita-Token':state.session.token}, body:JSON.stringify({content})});
    const result = await response.json();
    if(!response.ok) throw new Error(result.error || 'Syntax check failed');
    return result;
  },
})]));
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const aiChoices = new Map();
const providerNames = {codex:'Codex',gemini:'Gemini',google:'Google Gemini',openai:'OpenAI',anthropic:'Anthropic'};
const effortNames = {none:'None',minimal:'Minimal',low:'Low',medium:'Medium',high:'High',xhigh:'Extra high',max:'Maximum',ultra:'Ultra'};
function selectedModel() {return state.catalog?.options.find(o=>o.provider===$('#provider').value && o.model===$('#model').value);}
function rememberAI() {
  if(state.snapshot) aiChoices.set(state.snapshot.branch,{provider:$('#provider').value,model:$('#model').value,reasoning:$('#reasoning').value});
}
function renderReasoning(preferred='') {
  const option=selectedModel(), efforts=option?.reasoning || [];
  $('#reasoning').replaceChildren(new Option('Provider default',''),...efforts.map(e=>new Option(effortNames[e]||e,e)));
  $('#reasoning').value=efforts.includes(preferred)?preferred:'';
  $('#reasoning').disabled=!efforts.length || !!state.snapshot?.running;
  $('#reasoning-hint').textContent=efforts.length?'Reasoning applies to all AI steps. Higher levels can take longer.':
    option?.provider==='codex'?(state.catalog.reasoningBridge?'Select a model with reasoning levels in your local Codex catalog.':'Reasoning requires the AI integration. Install vita-tree[ai] or use --vita-source.'):
    'This provider/model uses its default reasoning; the current VITA integration has no effort control for it.';
  $('#provider-hint').textContent=`Models from your repository and local settings. Your provider account determines access.`;
  $('#model').title=option?`Found in:\n${option.sources.join('\n')}`:'';
}
function renderModels(preferred,reasoning='') {
  const options=state.catalog.options.filter(o=>o.provider===$('#provider').value);
  $('#model').replaceChildren(...options.map(o=>new Option(o.model||'CLI / provider default',o.model)));
  if(options.some(o=>o.model===preferred)) $('#model').value=preferred;
  else if($('#provider').value===state.catalog.default.provider) $('#model').value=state.catalog.default.model;
  $('#model').disabled=!!state.snapshot?.running;
  renderReasoning(reasoning);
}
function renderProviders() {
  const choice=aiChoices.get(state.snapshot.branch)||state.catalog.default;
  const names=[...new Set(state.catalog.options.filter(o=>o.supported).map(o=>o.provider))];
  $('#provider').replaceChildren(...names.map(p=>new Option(providerNames[p]||p,p)));
  if(names.includes(choice.provider)) $('#provider').value=choice.provider;
  $('#provider').disabled=!!state.snapshot.running;
  renderModels(choice.model,choice.reasoning);
}
$('#provider').onchange=()=>{renderModels();rememberAI();configureWorkflow();renderWorkflow();};
$('#model').onchange=()=>{renderReasoning();rememberAI();configureWorkflow();renderWorkflow();};
$('#reasoning').onchange=rememberAI;
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {cache: 'no-store'} : {method:'POST', headers:{'Content-Type':'application/json','X-Vita-Token':state.session.token}, body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw Object.assign(new Error(result.error || `Request failed (${response.status})`), result);
  return result;
}
function notice(text = '', error = false) { $('#notice').textContent = text; $('#notice').hidden = !text; $('#notice').classList.toggle('error', error); }
function toast(text) { $('#toast').textContent = text; $('#toast').hidden = false; clearTimeout(state.toast); state.toast = setTimeout(() => $('#toast').hidden = true, 4000); }
function relative(timestamp) {
  const age = Math.max(0, Date.now()/1000-timestamp);
  for (const [seconds, unit] of [[31536000,'y'],[2592000,'mo'],[86400,'d'],[3600,'h'],[60,'m']]) if(age>=seconds) return `${Math.floor(age/seconds)}${unit} ago`;
  return 'Just now';
}
function renderBranches() {
  const query = $('#search').value.toLowerCase();
  const matchesFilter = (b, filter) => {
    const runs=state.runs.filter(run=>run.branch===b.name), latest=runs[0];
    return filter==='all' || (filter==='running' && runs.some(isActiveRun)) ||
      (filter==='review' && runs.some(run=>run.status==='succeeded'&&!run.reviewed)) ||
      (filter==='failed' && latest && ['failed','interrupted'].includes(latest.status));
  };
  for(const filter of ['all','running','review','failed']) $('#filter-'+filter).textContent=state.branches.filter(b=>matchesFilter(b,filter)).length;
  const branches = state.branches.filter(b => matchesFilter(b,state.filter) && `${b.name} ${b.subject} ${b.author}`.toLowerCase().includes(query));
  $('#branch-list').replaceChildren();
  for (const b of branches) {
    const row = document.createElement('button'); row.className='branch-row'; row.setAttribute('aria-label', `Open ${b.name}`);
    row.innerHTML=`<span class="branch-cell"><span class="branch-icon" aria-hidden="true">⑂</span><span class="branch-info"><span class="branch-name">${esc(b.name)}</span><span class="branch-detail">${b.current?'Current branch':b.local?'Local branch':`Remote · ${esc(b.remote)}`}</span></span></span><span class="commit-cell"><span class="commit-subject">${esc(b.subject)}</span><span class="commit-meta">${esc(b.commit)} · ${esc(b.author)}</span></span><time class="branch-date" datetime="${esc(b.modifiedAt)}" title="${esc(new Date(b.modifiedAt).toLocaleString())}">${relative(b.timestamp)}</time>`;
    row.onclick=() => {
      const pending=state.filter==='review'&&state.runs.find(run=>run.branch===b.name&&run.status==='succeeded'&&!run.reviewed);
      if(pending)openRun(pending).catch(error=>notice(error.message,true));else openBranch(b.name);
    }; $('#branch-list').append(row);
    const branchRuns=state.runs.filter(run=>run.branch===b.name);
    const run=branchRuns.find(isActiveRun)||branchRuns.find(item=>!item.reviewed)||branchRuns[0];
    if(run&&(isActiveRun(run)||!run.reviewed||['failed','interrupted'].includes(run.status))){
      const badge=document.createElement('span');badge.className='branch-run';badge.dataset.status=run.status;
      badge.textContent=runLabel(run)+(!isActiveRun(run)&&!run.reviewed?' · To review':'');row.querySelector('.branch-info').append(badge);
    }
  }
  if(!branches.length) $('#branch-list').innerHTML=state.filter==='review'&&!query ? '<p class="empty">No completed runs need review.</p>' : '<p class="empty">No branches here. Try another filter or create a branch for your next application.</p>';
  $('#result-count').textContent=`${branches.length} ${branches.length===1?'branch':'branches'}`;
  $('#total-count').textContent=state.branches.length;
}
async function loadBranches() {
  $('#refresh').disabled=true;
  try {const result=await api('/api/branches');state.branches=result.branches;$('#repository').textContent=result.repository;renderBranches();}
  catch(error) {$('#branch-list').innerHTML=`<p class="empty">${esc(error.message)}</p>`;}
  finally {$('#refresh').disabled=false;}
}
function canLeave() {return !(state.dirty || state.jobDirty) || window.confirm('Discard your unsaved editor changes?');}
async function releaseBranch(name){
  try{
    const result=await api('/api/release-worktree',{branch:name});
    if(result.released||['dirty','locked'].includes(result.reason))toast(`${name}: ${result.message}`);
  }catch(error){toast(`Could not release ${name}: ${error.message}`);}
}
async function openBranch(name, force=false) {
  if(!force && !canLeave()) return;
  const previous=state.snapshot?.branch;
  const generation=++state.generation;
  state.snapshot=null;state.displayedRun=null;state.graphRunId=null;state.selectedTask=null;$('#task-inspector').hidden=true;
  $('#selected-run').hidden=true;
  for(const id of ['provider','model','reasoning',...aiSteps.map(id=>'step-'+id)]) $('#'+id).disabled=true;
  for(const id of aiSteps.map(id=>'step-'+id))$('#'+id).checked=false;
  for(const id of ['save-source','save-job','run-adapt','run-all','task-run','branch-from','compile','commit-push','view-run','mark-run-reviewed']) $('#'+id).disabled=true;
  editors.current.setReadOnly(true);$('#job-description').readOnly=true;
  $('#board').hidden=true;$('#workspace').hidden=false;document.body.classList.add('in-workspace');
  $('#branch-title').textContent=name; notice('Loading the branch…');
  try {
    if(previous&&previous!==name)await releaseBranch(previous);
    if(generation!==state.generation)return;
    const [data,catalog]=await Promise.all([api('/api/workspace?branch='+encodeURIComponent(name)),api('/api/providers?branch='+encodeURIComponent(name))]);
    if(generation!==state.generation) return;
    state.snapshot=data; state.catalog=catalog; state.dirty=false; state.jobDirty=false; state.pdfs={};state.pdfGeneration++;
    renderProviders();
    history.replaceState(null,'','?branch='+encodeURIComponent(name));
    updateSnapshot(); setView(state.view);
    if(state.view!=='structure')notice();
    return data;
  } catch(error) { if(generation===state.generation) notice(error.message,true); }
}
function updateSnapshot() {
  const s=state.snapshot;
  $('#branch-title').textContent=s.branch;$('#workspace-caption').textContent=s.editable?'Changes stay on this branch. Compare the result, then commit when you’re ready.':'Remote branch. Create a local branch to edit or run AI.';
  $('#original-label').textContent=s.baseBranch;$('#current-label').textContent=s.branch;
  $('#version-label').textContent=s.editable?'Editable':'Remote';
  editors.original.setDocument(s.original,s.branch);editors.current.setDocument(s.content,s.branch);editors.current.setReadOnly(!s.editable||!!s.running);
  renderDocument('original',s.originalDocument);renderDocument('current',s.document);
  $('#job-description').value=s.job;$('#job-description').readOnly=!s.editable||!!s.running;$('#job-state').textContent=s.job?'Saved as job.md':'No job description yet';
  $('#save-job').disabled=!s.editable||!!s.running;$('#branch-from').disabled=!!s.running;$('#compile').disabled=false;$('#ai-dot').textContent=Object.keys(s.artifacts).length?'•':'';
  $('#ai-capability').textContent=state.session.vita?'Run only what you select, or Run all available steps. Validation always checks results before applying them. Save editor changes first.': 'VITA CLI is unavailable. Install vita-tree[ai] or restart with --vita-source pointing to vita-cv.';
  $('#run-adapt').disabled=!state.session.vita || !s.editable || !!s.running || !selectedModel()?.supported;
  $('#ai-status').textContent=s.running?.message || (s.job?'Ready to run on this branch.':'Add and save a job description first.');
  $('#worktree-path').textContent=s.worktree || 'A separate worktree will be created on first save.';
  $('#diff').replaceChildren();
  if(!s.diff) $('#diff').textContent='No changes from the original.';
  else for(const line of s.diff.split('\n')) {const item=document.createElement('span');item.textContent=line+'\n';if(line.startsWith('+')&&!line.startsWith('+++'))item.className='added';else if(line.startsWith('-')&&!line.startsWith('---'))item.className='removed';$('#diff').append(item);}
  const added=s.diff.split('\n').filter(x=>x.startsWith('+')&&!x.startsWith('+++')).length;
  const removed=s.diff.split('\n').filter(x=>x.startsWith('-')&&!x.startsWith('---')).length;
  $('#change-count').textContent=added||removed?`+${added} −${removed}`:'';
  $('#artifacts').replaceChildren();
  if(!Object.keys(s.artifacts).length) $('#artifacts').innerHTML='<p class="helper">No reports yet. Run the workflow to see the job analysis and proposed changes here.</p>';
  for(const [key,artifact] of Object.entries(s.artifacts)) $('#artifacts').append(reportDetails(artifact.path,artifact.content,{open:key==='analyze'}));
  configureWorkflow();renderWorkflow();
  updateSaveState();
}
function renderDocument(side, data) {
  const target=$(`#${side}-document .cv-document`);
  // HTML is produced by the source-mapped renderer; every source string is escaped there.
  target.innerHTML=data.error?`<p class="empty">${esc(data.error)}<br>Use LaTeX to repair the source.</p>`:data.html;
}
function updateSaveState(){
  $('#save-state').textContent=state.dirty?'Unsaved edits':state.snapshot?.dirty?'Saved locally · uncommitted':'Saved';
  $('#save-source').disabled=!state.dirty || !state.snapshot?.editable || !!state.snapshot?.running;
  $('#commit-push').disabled=!state.snapshot?.editable || !!state.snapshot?.running || state.publishing;
}
function setView(view){
  state.view=view;
  document.querySelectorAll('[data-view]').forEach(b=>{b.setAttribute('aria-selected',String(b.dataset.view===view));b.tabIndex=b.dataset.view===view?0:-1;});
  if(state.snapshot)history.replaceState(null,'','?'+new URLSearchParams({branch:state.snapshot.branch,view}));
  $('#comparison').hidden=!['structure','source','pdf'].includes(view);$('#structure-hint').hidden=view!=='structure';$('#pdf-toolbar').hidden=view!=='pdf';$('#changes-panel').hidden=view!=='changes';$('#ai-panel').hidden=view!=='ai';$('#document-actions').hidden=false;$('#save-source').hidden=['ai','pdf'].includes(view);
  for(const side of ['original','current']) {$(`#${side}-document`).hidden=view!=='structure';$(`#${side}-source`).hidden=view!=='source';$(`#${side}-pdf`).hidden=view!=='pdf';}
  if(view==='source') for(const editor of Object.values(editors)) editor.refresh();
  if(!state.snapshot)return;
  if(view==='structure'){
    const warnings=[...new Set([...state.snapshot.document.warnings,...state.snapshot.originalDocument.warnings])];
    notice(state.dirty?'The reading view shows the saved version. Save your LaTeX edits to update it.':warnings.join('\n'));
  } else if(view==='pdf') {
    notice(state.dirty?'PDF preview uses the saved version. Save your LaTeX changes first.':'');
    for(const side of ['original','current']) if(!state.pdfs[side]) $(`#${side}-pdf`).innerHTML='<p class="pdf-message">Compile to see the exact PDF layout.<br>Text will remain selectable.</p>';
  } else notice();
}
async function saveSource(){
  if(!state.dirty||!state.snapshot)return;
  if(state.jobDirty){notice('Save job.md before saving your LaTeX edits.',true);return;}
  const s=state.snapshot, value=editors.current.value;$('#save-source').disabled=true;editors.current.setReadOnly(true);$('#job-description').readOnly=true;$('#save-job').disabled=true;
  try {await api('/api/save',{branch:s.branch,path:s.path,revision:s.revision,content:value});await openBranch(s.branch,true);toast('Saved to '+s.path);}
  catch(error){notice(error.message,true);editors.current.setReadOnly(!s.editable);$('#job-description').readOnly=false;$('#save-job').disabled=false;updateSaveState();}
}
async function saveJob(){
  if(!state.snapshot)return;
  const s=state.snapshot;$('#save-job').disabled=true;
  try{const result=await api('/api/save',{branch:s.branch,path:'job.md',revision:s.jobRevision,content:$('#job-description').value});s.job=result.content;s.jobRevision=result.revision;state.jobDirty=false;$('#job-state').textContent='Saved as job.md';toast('Job description saved');}
  catch(error){notice(error.message,true);}finally{$('#save-job').disabled=!s.editable;}
}
function commitPayload(){
  const s=state.snapshot;
  const data={branch:s.branch,sourceRevision:s.revision,jobRevision:s.jobRevision};
  if(state.dirty)data.sourceContent=editors.current.value;
  if(state.jobDirty)data.jobContent=$('#job-description').value;
  return data;
}
function renderCommitReview(review,{retry=false}={}){
  state.commitReview=review;
  $('#commit-branch').textContent=review.branch;
  $('#commit-destination').textContent=review.destination||'No remote configured';
  $('#commit-files').replaceChildren(...review.files.map(file=>{
    const item=document.createElement('li');
    item.innerHTML=`<span>${esc(file.path)}</span><span class="commit-file-status">${esc(file.status)}</span>`;
    return item;
  }));
  $('#commit-files').hidden=!review.files.length;$('#commit-empty').hidden=!!review.files.length;
  $('#commit-empty').textContent=review.ahead>0?`${review.ahead} existing local ${review.ahead===1?'commit':'commits'} will be pushed.`:
    review.ahead===0?'No file changes or unpushed commits were found. Push will verify the selected branch.':
    'No new file changes. The selected branch will be published and its upstream configured.';
  $('#commit-excluded').hidden=!review.excludedChanges;
  $('#commit-excluded').textContent=review.excludedChanges?`${review.excludedChanges} unrelated ${review.excludedChanges===1?'change is':'changes are'} excluded from this commit.`:'';
  $('#commit-message').disabled=!review.files.length;$('#commit-message').required=!!review.files.length;
  if(review.files.length&&!$('#commit-message').value)$('#commit-message').value=`Update CV for ${review.branch}`;
  $('#confirm-commit').textContent=retry?'Retry push':review.files.length?'Commit & push':'Push branch';
  $('#confirm-commit').disabled=!review.remote;
  if(!review.remote)$('#commit-error').textContent='No Git remote is configured. Add a remote, then review again.';
}
async function refreshCommitReview(options={}){
  const review=await api('/api/commit-preview',commitPayload());renderCommitReview(review,options);return review;
}
async function showCommit(){
  if(!state.snapshot||state.snapshot.running)return;
  $('#commit-push').disabled=true;$('#commit-error').textContent='';$('#commit-progress').textContent='Reviewing the branch…';$('#commit-message').value='';
  try{
    await refreshCommitReview();$('#commit-progress').textContent='Review these files before publishing.';$('#commit-dialog').showModal();
    if(state.commitReview.files.length)$('#commit-message').focus();
  }catch(error){notice(error.message,true);}finally{updateSaveState();}
}
$('#commit-form').onsubmit=async event=>{
  event.preventDefault();if(state.publishing)return;
  state.publishing=true;const button=event.submitter||$('#confirm-commit');button.disabled=true;$('#commit-error').textContent='';
  $('#commit-progress').textContent=state.commitReview.files.length?'Saving, committing, and pushing…':'Pushing existing commits…';
  document.querySelectorAll('#commit-dialog .close-dialog').forEach(item=>item.disabled=true);updateSaveState();
  try{
    const result=await api('/api/commit-push',{...commitPayload(),message:$('#commit-message').value,review:state.commitReview.review});
    $('#commit-dialog').close();state.dirty=false;state.jobDirty=false;await openBranch(result.branch,true);await loadBranches();
    toast(`${result.commitCreated?'Committed and pushed':'Pushed'} to ${result.destination}`);
  }catch(error){
    $('#commit-error').textContent=(error.commitCreated&&error.commit?`Commit ${String(error.commit).slice(0,7)} was created locally. `:'')+error.message;
    if(error.canRetry){
      try{
        await openBranch(state.snapshot.branch,true);await refreshCommitReview({retry:true});
        $('#commit-progress').textContent='The local commit is safe. Fix the push problem, then retry.';
      }catch(refreshError){$('#commit-error').textContent+='\n'+refreshError.message;}
    }else $('#commit-progress').textContent='Nothing was pushed.';
  }finally{
    state.publishing=false;document.querySelectorAll('#commit-dialog .close-dialog').forEach(item=>item.disabled=false);
    button.disabled=!state.commitReview?.remote;updateSaveState();
  }
};
$('#commit-dialog').addEventListener('cancel',event=>{if(state.publishing)event.preventDefault();});
async function showCreate(){
  if(!canLeave())return;
  $('#base-branch').innerHTML=state.branches.map(b=>`<option value="${esc(b.name)}">${esc(b.name)}</option>`).join('');
  $('#base-branch').value=state.snapshot?.branch||state.branches.find(b=>b.current)?.name||state.branches[0]?.name||'';
  $('#create-error').textContent='';$('#create-dialog').showModal();$('#branch-name').focus();
}
$('#create-form').onsubmit=async event=>{
  event.preventDefault();const button=event.submitter;button.disabled=true;
  try{const base=$('#base-branch').value;const original=await api('/api/workspace?branch='+encodeURIComponent(base));const s=await api('/api/create',{base,name:$('#branch-name').value.trim(),job:$('#new-job').value,revision:original.revision});$('#create-dialog').close();state.dirty=false;state.jobDirty=false;await loadBranches();state.view='structure';await openBranch(s.branch,true);toast('Branch created with main.tex and job.md');$('#create-form').reset();}
  catch(error){$('#create-error').textContent=error.message;}finally{button.disabled=false;}
};
$('#current-document').ondblclick=event=>{
  const leaf=event.target.closest('[data-leaf]');if(!leaf||!state.snapshot?.editable)return;
  if(state.dirty||state.jobDirty){notice('Save your LaTeX and job edits before editing the reading view.',true);return;}
  if(state.snapshot.running){notice('Wait for the AI run to finish before editing.',true);return;}
  state.leaf=leaf.dataset.leaf;$('#edit-text').value=state.snapshot.document.leaves[state.leaf].text;$('#edit-error').textContent='';$('#edit-dialog').showModal();$('#edit-text').focus();
};
$('#edit-form').onsubmit=async event=>{
  event.preventDefault();event.submitter.disabled=true;const s=state.snapshot;
  try{await api('/api/save',{branch:s.branch,path:s.path,revision:s.revision,leaf:state.leaf,text:$('#edit-text').value});$('#edit-dialog').close();await openBranch(s.branch,true);toast('Text updated in '+s.path);}
  catch(error){$('#edit-error').textContent=error.message;}finally{event.submitter.disabled=false;}
};
async function runAdapt(steps=workflowOptions().steps){
  if(!state.snapshot||state.snapshot.running||state.launching)return;
  if(!steps.length){notice('Select at least one step.',true);return;}
  if(state.dirty||state.jobDirty){notice('Save your CV and job description before starting AI.',true);return;}
  state.launching=true;$('#run-adapt').disabled=true;$('#run-all').disabled=true;$('#task-run').disabled=true;editors.current.setReadOnly(true);$('#job-description').readOnly=true;$('#save-job').disabled=true;$('#branch-from').disabled=true;const s=state.snapshot;
  rememberAI();
  for(const id of aiSteps.map(id=>'step-'+id))$('#'+id).disabled=true;
  try{const job=await api('/api/adapt',{branch:s.branch,revision:s.revision,jobRevision:s.jobRevision,provider:$('#provider').value,model:$('#model').value,reasoning:$('#reasoning').value,language:$('#language').value,workflow:{steps}});s.running=job;if(state.snapshot===s){state.graphRunId=job.id;renderProviders();configureWorkflow();renderWorkflow();updateSaveState();$('#ai-status').textContent=job.message;}await runMonitor.refresh();}
  catch(error){if(state.snapshot===s){notice(error.message,true);configureWorkflow();$('#run-adapt').disabled=false;editors.current.setReadOnly(!s.editable);$('#job-description').readOnly=!s.editable;$('#save-job').disabled=!s.editable;$('#branch-from').disabled=false;}}
  finally{state.launching=false;if(state.snapshot){configureWorkflow();renderWorkflow();}}
}
async function runsChanged(runs){
  state.runs=runs;renderBranches();
  const s=state.snapshot;if(!s)return;
  renderWorkflow();
  const active=runs.find(run=>run.branch===s.branch&&isActiveRun(run));
  if(active){
    s.running=active;$('#ai-status').textContent=active.message;editors.current.setReadOnly(true);$('#job-description').readOnly=true;
    for(const id of ['save-job','run-adapt','run-all','task-run','branch-from'])$('#'+id).disabled=true;
    renderProviders();configureWorkflow();renderWorkflow();updateSaveState();
  }else if(s.running){
    const finished=runs.find(run=>run.id===s.running.id);s.running=null;
    if(!state.dirty&&!state.jobDirty&&!state.publishing){
      const loaded=await openBranch(s.branch,true);
      if(loaded&&finished){$('#ai-status').textContent=finished.message;notice(finished.message,finished.status!=='succeeded');}
    }else{
      editors.current.setReadOnly(!s.editable);$('#job-description').readOnly=!s.editable;
      $('#save-job').disabled=!s.editable;$('#branch-from').disabled=false;
      renderProviders();updateSaveState();
      $('#run-adapt').disabled=!state.session.vita||!s.editable||!selectedModel()?.supported;
      notice('The AI run finished. Your unsaved edits are preserved; reload to review the result.',true);
    }
  }
}
async function openRun(run){
  if(!canLeave())return;
  const loaded=await openBranch(run.branch,true);if(!loaded)return;
  state.graphRunId=run.id;renderWorkflow();
  setView('ai');$('#ai-status').textContent=run.message;
  if(!isActiveRun(run)){
    const detail=await api('/api/job-result?id='+encodeURIComponent(run.id));
    if(state.snapshot!==loaded)return;
    const settings=[run.provider,run.model,run.reasoning,run.language].filter(Boolean).join(' · ');
    $('#selected-run').hidden=false;$('#selected-run-info').textContent=`${runSteps(run)} · ${runLabel(run)} · ${new Date(run.createdAt*1000).toLocaleString()} · ${run.provider?settings:'Local checks; no AI calls'} · ${Math.round(run.elapsedSeconds || 0)}s. Retained files for this run. The branch above may contain newer edits.`;
    $('#selected-run-files').replaceChildren();
    for(const [path,content] of Object.entries(detail.files)){
      $('#selected-run-files').append(reportDetails(path,content,{open:/analy(sis|ze)\.md$/.test(path),label:detail.inputs?.includes(path)?`Input · ${path}`:path}));
    }
    if(!Object.keys(detail.files).length)$('#selected-run-files').textContent='No result files were produced by this run.';
  }
  $('#ai-panel').scrollIntoView({block:'start'});
}
function workflowOptions(){return {steps:aiSteps.filter(id=>$('#step-'+id).checked)};}
function configureWorkflow(){
  const s=state.snapshot, available=state.session.workflow || {};
  const selected=s.running?.stages?.length ? s.running.stages.filter(stage=>stage.status!=='skipped').map(stage=>stage.id) : state.workflowChoices.get(s.branch)?.steps || ['analyze','adapt',...(available.review?['review']:[])];
  for(const id of aiSteps){
    const input=$('#step-'+id);input.checked=selected.includes(id)&&stepAvailable(id);input.disabled=!stepAvailable(id)||!!s.running||!!state.launching||!s.editable;
    if(!stepAvailable(id)) $('#hint-'+id).textContent='Unavailable in the connected Vita CV. Upgrade to enable.';
  }
  const blocked=!state.session.vita||!s.editable||!!s.running||!!state.launching||!selectedModel()?.supported;
  $('#run-adapt').textContent='Run selected';
  $('#run-adapt').disabled=blocked||!workflowOptions().steps.length;
  $('#run-all').disabled=blocked;
}
function renderWorkflow(){
  if(!state.snapshot)return;
  const runs=state.runs.filter(run=>run.branch===state.snapshot.branch);
  const selected=state.graphRunId || state.snapshot.running?.id || runs[0]?.id || 'draft';
  const select=$('#workflow-run');
  select.replaceChildren(new Option('Next run','draft'),...runs.map(run=>new Option(`${new Date(run.createdAt*1000).toLocaleString()} — ${runSteps(run)} · ${runLabel(run)}${isActiveRun(run)?'':run.reviewed?' · Reviewed':' · Unreviewed'}`,run.id)));
  const run=runs.find(run=>run.id===selected) || (state.snapshot.running?.id===selected?state.snapshot.running:null);
  if(run&&!runs.some(item=>item.id===run.id))select.add(new Option('Current run',run.id));
  select.value=run?run.id:'draft';state.displayedRun=run;
  const finished=run&&!isActiveRun(run);
  $('#view-run').hidden=!finished;$('#view-run').disabled=!!state.openingRunId;
  const reviewButton=$('#mark-run-reviewed');reviewButton.hidden=!finished;
  reviewButton.disabled=!!run?.reviewed||!!state.reviewingRunId;
  reviewButton.textContent=run?.reviewed?'Reviewed':state.reviewingRunId===run?.id?'Marking…':'Mark as reviewed';
  $('#workflow-summary').textContent=run ? run.message : 'Plan your next run. Skipped steps make no AI calls.';
  renderGraph($('#workflow-graph'),{run,options:workflowOptions(),available:state.session.workflow,selected:state.selectedTask,select:selectTask});
  if(state.selectedTask)updateInspector();
}
function updateInspector(){
  const task=graphStages(state.displayedRun,workflowOptions(),state.session.workflow).find(t=>t.id===state.selectedTask);
  if(!task)return;
  $('#task-inspector').hidden=false;$('#task-title').textContent=task.title;
  $('#task-description').textContent=task.detail+' Run actions use the current saved branch files and settings in Job & AI.';
  $('#task-status').textContent=`${statusNames[task.status] || task.status} · ${task.output}`;
  $('#task-output').textContent=task.id==='validating'?'Compare current CVs':task.id==='adapt'?'Open run source':'Open report';
  $('#task-run').textContent=task.id==='validating'?'Validate current CV':`Run ${task.title} only`;
  $('#task-run').disabled=!state.snapshot.editable||!!state.snapshot.running||!!state.launching||!stepAvailable(task.id)||(task.id!=='validating'&&(!state.session.vita||!selectedModel()?.supported));
  $('#task-output').disabled=isActiveRun(state.displayedRun)||!['succeeded','unknown'].includes(task.status);
  if(isActiveRun(state.displayedRun))$('#task-status').textContent+=' · Outputs open after the run finishes.';
}
function selectTask(task){state.selectedTask=task.id;renderWorkflow();}
$('#view-run').onclick=async()=>{
  const run=state.displayedRun;if(!run||isActiveRun(run)||state.openingRunId)return;
  state.openingRunId=run.id;renderWorkflow();
  try{await openRun(run);}catch(error){notice(error.message,true);}
  finally{state.openingRunId=null;renderWorkflow();}
};
$('#mark-run-reviewed').onclick=async()=>{
  const run=state.displayedRun;if(!run||isActiveRun(run)||run.reviewed||state.reviewingRunId)return;
  state.graphRunId=run.id;state.reviewingRunId=run.id;renderWorkflow();notice();
  try{
    const reviewed=await api('/api/job-reviewed',{id:run.id});
    state.runs=state.runs.map(item=>item.id===reviewed.id?reviewed:item);
    renderBranches();renderWorkflow();toast('Run marked as reviewed.');
    await runMonitor.refresh();
  }catch(error){notice(error.message,true);}
  finally{state.reviewingRunId=null;renderWorkflow();}
};
$('#workflow-run').onchange=()=>{state.graphRunId=$('#workflow-run').value;renderWorkflow();};
for(const id of aiSteps)$('#step-'+id).onchange=()=>{
  state.workflowChoices.set(state.snapshot.branch,workflowOptions());state.graphRunId='draft';configureWorkflow();renderWorkflow();
};
$('#task-run').onclick=()=>runAdapt([state.selectedTask]);
$('#run-all').onclick=()=>runAdapt(aiSteps.filter(stepAvailable));
$('#toggle-workflow').onclick=()=>{
  const body=$('#workflow-body');body.hidden=!body.hidden;
  $('#toggle-workflow').textContent=body.hidden?'Show graph':'Collapse graph';
  $('#toggle-workflow').setAttribute('aria-expanded',String(!body.hidden));
};
$('#task-output').onclick=async()=>{
  const task=state.selectedTask, run=state.displayedRun;
  if(task==='validating'){setView('structure');$('#comparison').scrollIntoView({block:'start'});return;}
  try{
    if(run&&!isActiveRun(run))await openRun(run);else setView('ai');
    const match={extract:'job.json',analyze:'analy',review:'review.',cover:'cover',adapt:'main.tex'}[task];
    const area=run&&!isActiveRun(run)?$('#selected-run-files'):$('#artifacts');
    const item=[...area.querySelectorAll('details')].find(el=>el.dataset.path.includes(match));
    if(item){item.open=true;item.scrollIntoView({block:'center'});item.querySelector('summary').focus();}
    else notice('This run has no saved output for that task. Check the run status.');
  }catch(error){notice(error.message,true);}
};
let pdfjs;
async function pdfLibrary(){if(!pdfjs){pdfjs=await import('./vendor/pdf.mjs');pdfjs.GlobalWorkerOptions.workerSrc='/vendor/pdf.worker.mjs';}return pdfjs;}
async function renderPDF(side, info, generation){
  const library=await pdfLibrary();const container=$(`#${side}-pdf`);
  const loadingTask=library.getDocument({url:info.url,cMapUrl:'/vendor/cmaps/',cMapPacked:true,standardFontDataUrl:'/vendor/standard_fonts/',wasmUrl:'/vendor/wasm/'});
  const pdf=await loadingTask.promise;
  if(generation!==state.pdfGeneration){await loadingTask.destroy();return;}
  container.replaceChildren();const link=document.createElement('a');link.className='pdf-download';link.href=info.url;link.target='_blank';link.rel='noopener';link.textContent='Open PDF ↗';container.append(link);
  for(let pageNumber=1;pageNumber<=pdf.numPages;pageNumber++){
    const page=await pdf.getPage(pageNumber);if(generation!==state.pdfGeneration){await loadingTask.destroy();return;}
    const natural=page.getViewport({scale:1});const available=Math.max(200,container.clientWidth-30);const zoom=$('#zoom').value;const scale=zoom==='fit'?available/natural.width:Number(zoom);const viewport=page.getViewport({scale});
    const wrapper=document.createElement('div');wrapper.className='pdf-page';wrapper.style.width=viewport.width+'px';wrapper.style.height=viewport.height+'px';wrapper.style.setProperty('--scale-factor',scale);wrapper.style.setProperty('--total-scale-factor',scale);wrapper.style.setProperty('--user-unit','1');
    const canvas=document.createElement('canvas');const ratio=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.floor(viewport.width*ratio);canvas.height=Math.floor(viewport.height*ratio);canvas.style.width=viewport.width+'px';canvas.style.height=viewport.height+'px';wrapper.append(canvas);container.append(wrapper);
    await page.render({canvasContext:canvas.getContext('2d'),viewport,transform:ratio===1?null:[ratio,0,0,ratio,0,0]}).promise;
    const layer=document.createElement('div');layer.className='textLayer';wrapper.append(layer);await new library.TextLayer({textContentSource:await page.getTextContent(),container:layer,viewport}).render();
    const label=document.createElement('div');label.className='pdf-page-label';label.textContent=`Page ${pageNumber} of ${pdf.numPages}`;container.append(label);
  }
  await loadingTask.destroy();
}
async function compilePDFs(){
  if(state.dirty){notice('Save your LaTeX edits before compiling.',true);return;}
  const generation=++state.pdfGeneration, branch=state.snapshot.branch;$('#compile').disabled=true;notice('Compiling the saved versions with the real TeX engine…');
  try{
    const results=await Promise.allSettled(['original','current'].map(async side=>{
      $(`#${side}-pdf`).innerHTML='<p class="pdf-message">Compiling PDF…</p>';
      try{const result=await api('/api/pdf',{branch,side,engine:$('#engine').value});if(generation!==state.pdfGeneration)return;state.pdfs[side]=result;await renderPDF(side,result,generation);return result;}
      catch(error){if(generation===state.pdfGeneration)$(`#${side}-pdf`).innerHTML=`<p class="pdf-message">${esc(error.message)}</p>`;throw error;}
    }));
    if(generation!==state.pdfGeneration)return;
    const warnings=results.flatMap(r=>r.status==='fulfilled'?r.value?.warnings||[]:[r.reason.message]);notice(warnings.length?warnings.join('\n'):'Both PDFs compiled. Select text directly on either page.',results.some(r=>r.status==='rejected'));
  }finally{$('#compile').disabled=false;}
}
$('#zoom').onchange=async()=>{const generation=++state.pdfGeneration;try{for(const side of ['original','current'])if(state.pdfs[side])await renderPDF(side,state.pdfs[side],generation);}catch(error){notice(error.message,true);}};
document.querySelectorAll('[data-filter]').forEach(button=>button.onclick=()=>{state.filter=button.dataset.filter;document.querySelectorAll('[data-filter]').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));renderBranches();});
$('#search').oninput=renderBranches;$('#refresh').onclick=loadBranches;$('#new-branch').onclick=showCreate;$('#branch-from').onclick=showCreate;
$('#back').onclick=()=>{if(!canLeave())return;const previous=state.snapshot?.branch;state.generation++;state.pdfGeneration++;state.snapshot=null;state.dirty=false;state.jobDirty=false;$('#workspace').hidden=true;$('#board').hidden=false;document.body.classList.remove('in-workspace');history.replaceState(null,'','/');if(previous)releaseBranch(previous);loadBranches();};
$('#reload').onclick=()=>openBranch(state.snapshot?.branch||$('#branch-title').textContent);
document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>setView(button.dataset.view));
$('.tabs').onkeydown=event=>{
  if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
  const tabs=[...document.querySelectorAll('[data-view]')], index=tabs.indexOf(event.target);if(index<0)return;
  const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
  event.preventDefault();setView(tabs[next].dataset.view);tabs[next].focus();
};
document.querySelectorAll('.close-dialog').forEach(button=>button.onclick=()=>button.closest('dialog').close());
$('#job-description').oninput=()=>{state.jobDirty=$('#job-description').value!==state.snapshot.job;$('#job-state').textContent=state.jobDirty?'Unsaved changes':'Saved as job.md';};
$('#save-source').onclick=saveSource;$('#save-job').onclick=saveJob;$('#commit-push').onclick=showCommit;$('#run-adapt').onclick=()=>runAdapt();$('#compile').onclick=compilePDFs;
window.addEventListener('beforeunload',event=>{if(state.dirty||state.jobDirty){event.preventDefault();event.returnValue='';}});
window.addEventListener('pagehide',()=>{
  if(state.snapshot&&state.session)fetch('/api/release-worktree',{method:'POST',keepalive:true,
    headers:{'Content-Type':'application/json','X-Vita-Token':state.session.token},
    body:JSON.stringify({branch:state.snapshot.branch})}).catch(()=>{});
});
document.addEventListener('keydown',event=>{if(event.key==='/'&&!event.target.closest('input,textarea,select,[contenteditable]')&&!$('#board').hidden){event.preventDefault();$('#search').focus();}if((event.ctrlKey||event.metaKey)&&event.key==='s'&&state.snapshot){event.preventDefault();state.view==='ai'?saveJob():saveSource();}});
try{state.session=await api('/api/session');await loadBranches();const params=new URLSearchParams(location.search), branch=params.get('branch');if(['structure','source','pdf','changes','ai'].includes(params.get('view')))state.view=params.get('view');if(branch)await openBranch(branch);runMonitor=createRunMonitor({api,changed:runsChanged});runMonitor.start();}catch(error){$('#branch-list').innerHTML=`<p class="empty">${esc(error.message)}</p>`;}

setInterval(()=>{document.querySelectorAll(".dag-time[data-started-at]").forEach(el=>{el.textContent=`${Math.max(0,Math.floor(Date.now()/1000-Number(el.dataset.startedAt)))}s`;});},1000);
