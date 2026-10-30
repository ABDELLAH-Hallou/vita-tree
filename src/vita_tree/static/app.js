const $ = selector => document.querySelector(selector);
const state = {branches: [], session: null, snapshot: null, view: 'structure', generation: 0, pdfs: {}, pdfGeneration: 0, dirty: false, jobDirty: false, leaf: null, publishing: false, commitReview: null};
import {createLatexEditor} from './vendor/editor.mjs';
import {createRunMonitor, isActiveRun, runLabel, runSteps} from './runs.js';
import {renderGraph, graphStages, statusNames} from './workflow.js';
import {reportDetails,fileLabel} from './reports.js';
import {initDiagnostics} from './diagnostics.js';
import {createAIConfiguration} from './ai-settings.js';
import {failureText,runFailureText} from './provider-failures.js';
import {createFactualReview} from './factual-review.js';
import {createRequirements} from './requirements.js';
import {createSetupChecks} from './preflight.js';
const setupChecks=createSetupChecks({api,getState:()=>state,getBranches:()=>state.branches,getSteps:()=>workflowOptions().steps});
const requirements=createRequirements({api,getState:()=>state,changed:()=>runMonitor.refresh(),continued:continueApproved,notice});
const factualReview=createFactualReview({api,getState:()=>state,changed:()=>runMonitor.refresh(),continued:continueApproved,notice});
state.filter='all';
state.syncedCommits=new Map();
const applicationName=name=>state.branches.find(item=>item.name===name)?.displayName||(state.snapshot?.branch===name?state.snapshot.displayName:null)||name;
state.workflowChoices=new Map();
const aiSteps=['extract','analyze','adapt','review','cover'];
const stepAvailable=id=>!['extract','review','cover'].includes(id)||!!state.session?.workflow?.[id];
state.pdfDocument='cv';
state.runs = [];
state.reviewSelection = new Set();
state.reviewing = false;
let visibleReviewBranches = [];
const reviewableRuns = branch => state.runs.filter(run=>run.branch===branch&&!isActiveRun(run)&&!run.reviewed);
function updateBulkReview(){
  const count=state.runs.filter(run=>state.reviewSelection.has(run.branch)&&!isActiveRun(run)&&!run.reviewed).length;
  $('#bulk-review').disabled=state.reviewing||!count;
  $('#bulk-review').textContent=state.reviewing?'Saving review…':'Mark selected as reviewed';
  $('#bulk-review-count').textContent=count?`${count} ${count===1?'result':'results'} selected`:'';
  const selected=visibleReviewBranches.filter(branch=>state.reviewSelection.has(branch)).length;
  const all=$('#select-review-visible');all.checked=!!selected&&selected===visibleReviewBranches.length;
  all.indeterminate=!!selected&&selected<visibleReviewBranches.length;all.disabled=state.reviewing||!visibleReviewBranches.length;
}
$('#select-review-visible').onchange=event=>{
  for(const branch of visibleReviewBranches)event.target.checked?state.reviewSelection.add(branch):state.reviewSelection.delete(branch);
  renderBranches();
};
$('#bulk-review').onclick=async()=>{
  const ids=state.runs.filter(run=>state.reviewSelection.has(run.branch)&&!isActiveRun(run)&&!run.reviewed).map(run=>run.id);
  if(state.reviewing||!ids.length)return;
  if(ids.length>500){$('#bulk-review-status').hidden=false;$('#bulk-review-status').textContent='Select fewer applications: up to 500 results can be reviewed at once.';return;}
  state.reviewing=true;renderBranches();const status=$('#bulk-review-status');status.hidden=false;status.textContent=`Marking ${ids.length} results as reviewed…`;
  try{
    const result=await api('/api/jobs-reviewed',{ids});
    const saved=new Set(result.reviewed);
    for(const run of state.runs)if(saved.has(run.id))run.reviewed=true;
    status.textContent=`${result.reviewed.length} ${result.reviewed.length===1?"result":"results"} marked as reviewed.`+(result.failed.length?` ${result.failed.length} could not be saved and remain selected. ${result.failed[0].error} Reference: ${result.requestId}`:'');
    await runMonitor.refresh();
  }catch(error){status.textContent=error.message;}
  finally{state.reviewing=false;renderBranches();}
};
let runMonitor;
const languageDrafts=new Map();
function renderLanguages(){
  const branch=state.snapshot?.branch;
  if(!branch||!state.catalog)return;
  const select=$('#language'), selected=state.snapshot.running?.language||languageDrafts.get(branch)||'en';
  const choices=[...(state.catalog.languages||[{code:'en',name:'English'}])];
  // An in-flight/captured language or a draft selection must not silently turn
  // into English if its mapping is later removed from this application's file.
  if(!choices.some(choice=>choice.code===selected))choices.push({code:selected,name:selected});
  const signature=JSON.stringify([branch,choices]);
  if(select.dataset.languages!==signature){
    select.replaceChildren(...choices.map(choice=>new Option(choice.name,choice.code)));
    select.dataset.languages=signature;
  }
  select.value=selected;
}
$('#language').onchange=()=>{if(state.snapshot)languageDrafts.set(state.snapshot.branch,$('#language').value);};
const editors = Object.fromEntries(['original', 'current'].map(side => [side, createLatexEditor($(`#${side}-source`), {
  label: side === 'original' ? 'Before · CV source' : 'Current CV source', readOnly: true,
  onChange: value => {if(side === 'current' && state.snapshot) {state.dirty = value !== currentFile().content; updateSaveState();}},
  lint: async (content, signal) => {
    const response = await fetch('/api/lint', {method:'POST', signal, headers:{'Content-Type':'application/json','X-Vita-Token':state.session.token}, body:JSON.stringify({content})});
    const result = await response.json();
    if(!response.ok) throw new Error(result.error || 'Couldn’t check the document formatting');
    return result;
  },
})]));
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const aiSetup=createAIConfiguration($('#ai-configuration'),{api,onChange:()=>{if(state.snapshot){if(!state.displayedRun?.resumeAvailable)state.graphRunId='draft';configureWorkflow();renderWorkflow();}}});
function renderProviders() {
  renderLanguages();
  aiSetup.setDisabled(!!state.snapshot?.running||!!state.launching||!state.snapshot?.editable);
  $('#language').disabled=!!state.snapshot?.running||!!state.launching||!state.snapshot?.editable;
  $('#model-details').textContent='Model suggestions come from repository settings and your local Codex catalog. You can enter any model ID your provider accepts.\n\nSetup: install vita-tree[ai] or start with --vita-source pointing to vita-cv. Custom reasoning currently uses the Codex connection.';
}
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {cache: 'no-store'} : {method:'POST', headers:{'Content-Type':'application/json','X-Vita-Token':state.session.token}, body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw Object.assign(new Error(result.error || `Request failed (${response.status})`), result);
  return result;
}
function notice(text = '', error = false) {
  const technical=(error&&text.includes('\n'))||/Cannot parse this LaTeX|Environment .+:|Math is shown as text|use PDF for exact rendering/.test(text);
  $('#message-details').hidden=!technical;$('#message-technical').textContent=technical?text:'';
  $('#notice').textContent=technical?(error?(text.startsWith('Cannot parse this LaTeX')?'The CV has a formatting problem. Open Technical details.':text.split('\n')[0]):'Some formatting may look different here. Use PDF preview to check the final layout.'):text;
  $('#notice').hidden=!text;$('#notice').classList.toggle('error',error);
}
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
      (filter==='failed' && latest && !needsDecision(latest) && ['failed','interrupted'].includes(latest.status));
  };
  for(const filter of ['all','running','review','failed']) $('#filter-'+filter).textContent=state.branches.filter(b=>matchesFilter(b,filter)).length;
  const branches = state.branches.filter(b => matchesFilter(b,state.filter) && `${b.displayName||b.name} ${b.name} ${b.subject} ${b.author}`.toLowerCase().includes(query));
  for(const branch of state.reviewSelection)if(!reviewableRuns(branch).length)state.reviewSelection.delete(branch);
  visibleReviewBranches=branches.filter(branch=>reviewableRuns(branch.name).length).map(branch=>branch.name);
  const focused=document.activeElement, focusedEntry=focused.closest('.branch-entry');
  const focusedBranch=focusedEntry?.dataset.branch, focusedSelection=focused.matches('.select-branch-review');
  $('#branch-list').replaceChildren();
  for (const b of branches) {
    const row = document.createElement('button'); row.className='branch-row'; row.setAttribute('aria-label', `Open ${b.displayName||b.name}`);
    row.innerHTML=`<span class="branch-cell"><span class="branch-icon" aria-hidden="true">⑂</span><span class="branch-info"><span class="branch-name">${esc(b.displayName||b.name)}</span><span class="branch-detail">${b.local?'Editable CV':'View only CV'}</span></span></span><span class="commit-cell"><span class="commit-subject">${esc(b.subject)}</span><span class="commit-meta">${esc(b.author)}</span></span><time class="branch-date" datetime="${esc(b.modifiedAt)}" title="${esc(new Date(b.modifiedAt).toLocaleString())}">${relative(b.timestamp)}</time>`;
    row.onclick=() => {
      const pending=state.filter==='review'&&state.runs.find(run=>run.branch===b.name&&run.status==='succeeded'&&!run.reviewed);
      if(pending)openRun(pending).catch(error=>notice(error.message,true));else openBranch(b.name);
    };
    const entry=document.createElement('div');entry.className='branch-entry';entry.dataset.branch=b.name;
    const select=document.createElement('input');select.type='checkbox';select.className='select-branch-review';
    select.setAttribute('aria-label',`Select unreviewed results for ${b.displayName||b.name}`);select.disabled=state.reviewing||!reviewableRuns(b.name).length;
    select.checked=state.reviewSelection.has(b.name);select.onchange=()=>{select.checked?state.reviewSelection.add(b.name):state.reviewSelection.delete(b.name);updateBulkReview();};
    entry.append(select,row);$('#branch-list').append(entry);
    const branchRuns=state.runs.filter(run=>run.branch===b.name);
    const run=branchRuns.find(isActiveRun)||branchRuns.find(item=>!item.reviewed)||branchRuns[0];
    if(run&&(isActiveRun(run)||!run.reviewed||['failed','interrupted'].includes(run.status))){
      const badge=document.createElement('span');badge.className='branch-run';badge.dataset.status=needsDecision(run)?'review':run.status;
      badge.textContent=runLabel(run)+(!isActiveRun(run)&&!run.reviewed?' · To review':'');row.querySelector('.branch-info').append(badge);
      if(!needsDecision(run)&&runFailureText(run)){const info=document.createElement('span');info.className='branch-failure';info.textContent=runFailureText(run);row.querySelector('.branch-info').append(info);}
    }
  }
  if(!branches.length) $('#branch-list').innerHTML=state.filter==='review'&&!query ? '<p class="empty">No completed preparations need review.</p>' : '<p class="empty">No applications found. Try another filter or create a new application.</p>';
  if(focusedBranch&&!$('#board').hidden&&!focused.isConnected){
    const replacement=[...$('#branch-list').children].find(entry=>entry.dataset.branch===focusedBranch)?.querySelector(focusedSelection?'.select-branch-review':'.branch-row');
    (replacement&&!replacement.disabled?replacement:$('#search')).focus({preventScroll:true});
  }
  $('#result-count').textContent=`${branches.length} ${branches.length===1?'application':'applications'}`;
  $('#total-count').textContent=state.branches.length;
  updateBulkReview();
}
async function loadBranches() {
  $('#refresh').disabled=true;$('#new-branch').disabled=true;
  try {const result=await api('/api/branches');state.branches=result.branches;$('#repository').textContent=result.repository;renderBranches();}
  catch(error) {$('#branch-list').innerHTML=`<p class="empty">${esc(error.message)}</p>`;}
  finally {$('#refresh').disabled=false;$('#new-branch').disabled=!state.branches.length;}
}
function canLeave() {return !(state.dirty || state.jobDirty) || window.confirm('Discard your unsaved editor changes?');}
async function releaseBranch(name){
  try{
    const result=await api('/api/release-worktree',{branch:name});
    if(result.released)toast('Application closed. You can reopen it at any time.');else if(result.reason==='locked')toast('Some files are still in use. Your application files are safe.');
  }catch(error){toast(`Couldn’t close the application folder for ${applicationName(name)}: ${error.message}`);}
}
async function openBranch(name, force=false) {
  if(!force && !canLeave()) return;
  factualReview.reset();requirements.reset();
  const previous=state.snapshot?.branch;
  if(previous&&previous!==name)state.filePath=null;
  const generation=++state.generation;
  $('#workspace').setAttribute('aria-busy','true');
  for(const tab of document.querySelectorAll('[data-view]'))tab.disabled=true;
  state.pdfGeneration++;state.snapshot=null;state.displayedRun=null;state.graphRunId=null;state.selectedTask=null;$('#task-inspector').hidden=true;$('#cv-file').disabled=true;
  for(const node of document.querySelectorAll('.dag-node'))node.disabled=true;
  $('#selected-run').hidden=true;$('#attempt-history').replaceChildren();
  aiSetup.setDisabled(true);
  for(const id of aiSteps.map(id=>'step-'+id))$('#'+id).checked=false;
  for(const id of ['save-source','save-job','run-adapt','run-all','task-run','branch-from','compile','commit-push','view-run','mark-run-reviewed','requirements-current-open','requirements-captured','task-requirements','step-requirements']) $('#'+id).disabled=true;
  editors.current.setReadOnly(true);$('#job-description').readOnly=true;
  $('#board').hidden=true;$('#workspace').hidden=false;document.body.classList.add('in-workspace');
  $('#branch-title').textContent=applicationName(name); notice('Loading the application…');
  try {
    if(previous&&previous!==name)await releaseBranch(previous);
    if(generation!==state.generation)return;
    const [data,catalog,settings,connections]=await Promise.all([api('/api/workspace?branch='+encodeURIComponent(name)),api('/api/providers?branch='+encodeURIComponent(name)),api('/api/ai-settings?branch='+encodeURIComponent(name)),api('/api/connections')]);
    if(generation!==state.generation) return;
    state.snapshot=data; state.catalog=catalog; state.dirty=false; state.jobDirty=false; state.pdfs={};state.pdfDocument='cv';$('#pdf-document').value='cv';state.pdfGeneration++;
    $('#review-policy').value=data.running?.reviewPolicy||'manual';
    aiSetup.load(name,catalog,settings,connections);
    renderProviders();
    history.replaceState(null,'','?branch='+encodeURIComponent(name));
    updateSnapshot(); setView(state.view);
    if(state.view!=='structure')notice();
    return data;
  } catch(error) { if(generation===state.generation) notice(error.message,true); }
  finally {
    if(generation===state.generation){
      $('#workspace').removeAttribute('aria-busy');
      for(const tab of document.querySelectorAll('[data-view]'))tab.disabled=!state.snapshot;
    }
  }
}
function updateSnapshot() {
  const s=state.snapshot;
  const file=currentFile();
  renderFileNavigation();
  $('#branch-title').textContent=s.displayName||s.branch;$('#workspace-caption').textContent=s.editable?'Review your CV and results, then save your application.':'This CV is view only. Use it to create a new application before editing.';
  $('#original-label').textContent=file.originalExists===false?'File absent before':file.path===s.path?'':file.path;$('#current-label').textContent=file.exists===false?'Not in current CV':file.path===s.path?s.displayName||s.branch:file.path;
  $('#version-label').textContent=s.editable&&file.exists!==false?'Editable':'View only';
  editors.original.setDocument(file.original,s.branch+':'+file.path);editors.current.setDocument(file.content,s.branch+':'+file.path);editors.current.setReadOnly(!s.editable||!!s.running||file.exists===false);
  renderDocument('original',file.originalDocument);renderDocument('current',file.document);
  $('#job-description').value=s.job;$('#job-description').readOnly=!s.editable||!!s.running;$('#job-state').textContent=s.job?'Saved on this computer':'No job description yet';
  $('#save-job').disabled=!s.editable||!!s.running;$('#branch-from').disabled=!!s.running;$('#compile').disabled=false;$('#ai-dot').textContent=Object.keys(s.artifacts).length?'•':'';
  $('#ai-capability').textContent=state.session.vita?'Prepare everything or start only the steps you choose. Your existing edits are checked before results are applied. Save any draft edits first.': 'The Vita CV connection is not available. Open AI connection details for setup instructions.';
  $('#run-adapt').disabled=!state.session.vita || !s.editable || !!s.running || !!aiSetup.problem(workflowOptions().steps);
  $('#ai-status').textContent=s.running?.message || (s.job?'Ready to prepare this application.':'Add and save a job description first.');
  $('#application-id').textContent=s.branch;$('#worktree-path').textContent=s.worktree || 'An application folder will be created when you save your first draft.';
  $('#diff').replaceChildren();
  if(!file.diff) $('#diff').textContent='No changes from the original in this file.';
  else for(const line of file.diff.split('\n')) {const item=document.createElement('span');item.textContent=line+'\n';if(line.startsWith('+')&&!line.startsWith('+++'))item.className='added';else if(line.startsWith('-')&&!line.startsWith('---'))item.className='removed';$('#diff').append(item);}
  const allDiff=(s.files||[s]).map(file=>file.diff).join('\n');
  const added=allDiff.split('\n').filter(x=>x.startsWith('+')&&!x.startsWith('+++')).length;
  const removed=allDiff.split('\n').filter(x=>x.startsWith('-')&&!x.startsWith('---')).length;
  $('#change-count').textContent=added||removed?`+${added} −${removed}`:'';
  $('#artifacts').replaceChildren();
  if(!Object.keys(s.artifacts).length) $('#artifacts').innerHTML='<p class="helper">No results yet. Choose the steps you want to prepare your application.</p>';
  for(const [key,artifact] of Object.entries(s.artifacts)) $('#artifacts').append(reportDetails(artifact.path,artifact.content,{open:key==='analyze'}));
  configureWorkflow();renderWorkflow();
  if(s.cover){
    const button=document.createElement('button');button.id='open-cover-pdf';button.textContent='Open cover-letter PDF';
    button.onclick=()=>openCoverPDF();$('#artifacts').prepend(button);
  }
  updateSaveState();
}
function currentFile(){
  const s=state.snapshot;
  if(!s)return null;
  return s.files?.find(file=>file.path===state.filePath)||s.files?.find(file=>file.path===s.path)||s;
}
function renderFileNavigation(){
  const s=state.snapshot,file=currentFile();state.filePath=file.path;
  $('#cv-file').disabled=false;
  $('#cv-file').replaceChildren(...(s.files||[s]).map(item=>{
    const option=document.createElement('option');option.value=item.path;option.textContent=item.path+(item.exists===false?' · unavailable':'')+(item.diff?' · changed':'');return option;
  }));$('#cv-file').value=file.path;
  $('#include-problems').hidden=!s.includeDiagnostics?.length;
  $('#include-diagnostics').replaceChildren(...(s.includeDiagnostics||[]).map(item=>{
    const li=document.createElement('li');li.textContent=item.message;
    const path=item.sourcePath||item.path;
    if(s.files.some(file=>file.path===path)){
      const button=document.createElement('button');button.className='quiet';button.textContent='Open '+path;button.onclick=()=>selectFile(path,'source');li.append(' ',button);
    }return li;
  }));
}
function selectFile(path,view=state.view){
  if(!state.snapshot)return;
  if(!canLeave()){$('#cv-file').value=state.filePath;return;}
  state.filePath=path;state.dirty=false;state.jobDirty=false;updateSnapshot();setView(view);
}
$('#cv-file').onchange=event=>selectFile(event.target.value);
function renderDocument(side, data) {
  const target=$(`#${side}-document .cv-document`);
  // HTML is produced by the source-mapped renderer; every source string is escaped there.
  target.innerHTML=data.error?`<p class="empty">Structure cannot preview this template. Use LaTeX editing and the PDF view; Check setup verifies compilation separately.</p><details class="technical-details"><summary>Structure details</summary><pre>${esc(data.error)}</pre></details>`:data.html;
}
function updateSaveState(){
  setupChecks.summary(state.displayedRun);
  const s=state.snapshot;$('#save-state').textContent=state.dirty||state.jobDirty?'Unsaved changes':s?.saveState?.draft?'Draft saved on this computer':s&&state.syncedCommits.get(s.branch)===s.commit?'Saved and synced':s?.saveState?.ahead!==0?'Saved on this computer · sync pending':'Saved';
  $('#save-source').disabled=!state.dirty || !state.snapshot?.editable || !!state.snapshot?.running || currentFile()?.exists===false;
  $('#commit-push').disabled=!state.snapshot?.editable || !!state.snapshot?.running || state.publishing;
}
function setView(view){
  state.view=view;
  $('#file-navigation').hidden=!['structure','source','changes'].includes(view);
  document.querySelectorAll('[data-view]').forEach(b=>{b.setAttribute('aria-selected',String(b.dataset.view===view));b.tabIndex=b.dataset.view===view?0:-1;});
  if(state.snapshot)history.replaceState(null,'','?'+new URLSearchParams({branch:state.snapshot.branch,view}));
  $('#comparison').hidden=!['structure','source','pdf'].includes(view)||(view==='pdf'&&state.pdfDocument==='cover');$('#cover-pdf-pane').hidden=view!=='pdf'||state.pdfDocument!=='cover';$('#compile').textContent=state.pdfDocument==='cover'?'Create cover-letter PDF':'Create PDF previews';$('#structure-hint').hidden=view!=='structure';$('#pdf-toolbar').hidden=view!=='pdf';$('#changes-panel').hidden=view!=='changes';$('#ai-panel').hidden=view!=='ai';$('#document-actions').hidden=false;$('#save-source').hidden=['ai','pdf'].includes(view);
  for(const side of ['original','current']) {$(`#${side}-document`).hidden=view!=='structure';$(`#${side}-source`).hidden=view!=='source';$(`#${side}-pdf`).hidden=view!=='pdf';}
  if(view==='source') for(const editor of Object.values(editors)) editor.refresh();
  if(!state.snapshot)return;
  const file=currentFile(),s=state.snapshot;
  $('#original-label').textContent=view==='pdf'||file.path===s.path?'':file.path;
  $('#current-label').textContent=view==='pdf'||file.path===s.path?s.displayName||s.branch:file.path;
  $('#version-label').textContent=view!=='pdf'&&s.editable&&file.exists!==false?'Editable':'View only';
  if(view==='structure'){
    const file=currentFile(),warnings=[...new Set([...file.document.warnings,...file.originalDocument.warnings])];
    notice(state.dirty?'The reading view shows the saved version. Save your draft to update this view.':warnings.join('\n'));
  } else if(view==='pdf') {
    notice(state.dirty?'PDF previews use your saved draft. Save your changes first.':'');
    for(const side of state.pdfDocument==='cover'?['cover']:['original','current']) if(!state.pdfs[side]) $(`#${side}-pdf`).innerHTML='<p class="pdf-message">Create a PDF preview to see the final layout.<br>Text will remain selectable.</p>';
  } else notice();
}
async function saveSource(){
  if(!state.dirty||!state.snapshot)return;
  if(state.jobDirty){notice('Save the job description draft first.',true);return;}
  const s=state.snapshot,file=currentFile(), value=editors.current.value;$('#save-source').disabled=true;editors.current.setReadOnly(true);$('#job-description').readOnly=true;$('#save-job').disabled=true;
  try {await api('/api/save',{branch:s.branch,path:file.path,revision:file.revision,projectRevision:s.projectRevision,content:value});await openBranch(s.branch,true);toast('CV draft saved on this computer');}
  catch(error){notice(error.message,true);editors.current.setReadOnly(!s.editable||currentFile()?.exists===false);$('#job-description').readOnly=false;$('#save-job').disabled=false;updateSaveState();}
}
async function saveJob(){
  if(!state.snapshot)return;
  const s=state.snapshot;$('#save-job').disabled=true;
  try{const result=await api('/api/save',{branch:s.branch,path:'job.md',revision:s.jobRevision,content:$('#job-description').value});s.job=result.content;s.jobRevision=result.revision;state.jobDirty=false;$('#job-state').textContent='Saved on this computer';s.saveState=result.saveState||{...s.saveState,draft:true};updateSaveState();toast('Job description draft saved');}
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
  $('#commit-branch').textContent=applicationName(review.branch);
  $('#commit-destination').textContent=review.destinationLabel||(review.remote?'Connected destination':'No sync destination connected');$('#sync-details').textContent=review.destination||'Not connected';
  $('#commit-files').replaceChildren(...review.files.map(file=>{
    const item=document.createElement('li');
    item.innerHTML=`<div>${esc(fileLabel(file.path))}<details class="technical-details"><summary>File details</summary><code>${esc(file.path)}</code></details></div><span class="commit-file-status">${({Added:'New',Modified:'Updated',Deleted:'Removed',Untracked:'New'})[file.status]||file.status}</span>`;
    return item;
  }));
  $('#commit-files').hidden=!review.files.length;$('#commit-empty').hidden=!!review.files.length;
  $('#commit-empty').textContent=review.ahead>0?`${review.ahead} saved ${review.ahead===1?'version':'versions'} will be synced.`:
    review.ahead===0?'No new edits or versions are waiting to sync. Save will check the connection.':
    'No new edits. This application will be synced to the connected destination.';
  $('#commit-excluded').hidden=!review.excludedChanges;
  $('#commit-excluded').textContent=review.excludedChanges?`${review.excludedChanges} other ${review.excludedChanges===1?'file will':'files will'} remain unchanged.`:'';
  $('#commit-message').disabled=!review.files.length;$('#commit-message').required=!!review.files.length;
  if(review.files.length&&!$('#commit-message').value)$('#commit-message').value=`Update CV for ${applicationName(review.branch)}`;
  $('#confirm-commit').textContent=retry?'Retry sync':'Save';
  $('#confirm-commit').disabled=!review.remote;
  if(!review.remote)$('#commit-error').textContent='No sync destination is connected. Check your connection setup before saving.';
}
async function refreshCommitReview(options={}){
  const review=await api('/api/commit-preview',commitPayload());renderCommitReview(review,options);return review;
}
async function showCommit(){
  if(!state.snapshot||state.snapshot.running)return;
  if(state.dirty&&currentFile().path!==state.snapshot.path){
    if(state.jobDirty){notice('Save your CV and job description drafts first.',true);return;}
    await saveSource();if(state.dirty)return;
  }
  $('#commit-push').disabled=true;$('#commit-error').textContent='';$('#commit-progress').textContent='Checking your changes…';$('#commit-message').value='';
  try{
    await refreshCommitReview();$('#commit-progress').textContent='Review these changes before saving and syncing.';$('#commit-dialog').showModal();
    if(state.commitReview.files.length)$('#commit-message').focus();
  }catch(error){notice(error.message,true);}finally{updateSaveState();}
}
$('#commit-form').onsubmit=async event=>{
  event.preventDefault();if(state.publishing)return;
  state.publishing=true;const button=event.submitter||$('#confirm-commit');button.disabled=true;$('#commit-error').textContent='';
  $('#commit-progress').textContent=state.commitReview.files.length?'Saving and syncing…':'Syncing saved versions…';
  document.querySelectorAll('#commit-dialog .close-dialog').forEach(item=>item.disabled=true);updateSaveState();
  try{
    const result=await api('/api/commit-push',{...commitPayload(),message:$('#commit-message').value,review:state.commitReview.review});
    state.syncedCommits.set(result.branch,result.commit);$('#commit-dialog').close();state.dirty=false;state.jobDirty=false;await openBranch(result.branch,true);await loadBranches();
    toast('Application saved and synced.');
  }catch(error){
    $('#commit-error').textContent=(error.commitCreated&&error.commit?`Your changes were saved on this computer. `:'')+error.message;
    if(error.canRetry){
      try{
        await openBranch(state.snapshot.branch,true);await refreshCommitReview({retry:true});
        $('#commit-progress').textContent='Your saved version is safe. Check the connection and retry syncing.';
      }catch(refreshError){$('#commit-error').textContent+='\n'+refreshError.message;}
    }else $('#commit-progress').textContent='Nothing was synced.';
  }finally{
    state.publishing=false;document.querySelectorAll('#commit-dialog .close-dialog').forEach(item=>item.disabled=false);
    button.disabled=!state.commitReview?.remote;updateSaveState();
  }
};
$('#commit-dialog').addEventListener('cancel',event=>{if(state.publishing)event.preventDefault();});
async function showCreate(){
  if(!canLeave())return;
  if(!state.branches.length){toast('Wait for your saved CVs to load, then try again.');return;}
  $('#base-branch').innerHTML=state.branches.map(b=>`<option value="${esc(b.name)}">${esc(b.displayName||b.name)}</option>`).join('');
  $('#base-branch').value=state.snapshot?.branch||state.branches.find(b=>b.current)?.name||state.branches[0]?.name||'';
  $('#create-error').textContent='';$('#create-dialog').showModal();$('#branch-name').focus();
}
$('#create-form').onsubmit=async event=>{
  event.preventDefault();const button=event.submitter;button.disabled=true;
  try{const base=$('#base-branch').value;const original=await api('/api/workspace?branch='+encodeURIComponent(base));const s=await api('/api/create',{base,applicationName:$('#branch-name').value.trim(),job:$('#new-job').value,revision:original.revision,projectRevision:original.projectRevision});$('#create-dialog').close();state.dirty=false;state.jobDirty=false;await loadBranches();state.view='structure';await openBranch(s.branch,true);toast('Application created with your CV and job description');$('#create-form').reset();}
  catch(error){$('#create-error').textContent=error.message;}finally{button.disabled=false;}
};
$('#current-document').ondblclick=event=>{
  const leaf=event.target.closest('[data-leaf]');if(!leaf||!state.snapshot?.editable)return;
  if(state.dirty||state.jobDirty){notice('Save your CV and job description drafts before editing this view.',true);return;}
  if(state.snapshot.running){notice('Wait for this preparation to finish before editing.',true);return;}
  if(currentFile().exists===false)return;
  state.leaf=leaf.dataset.leaf;const mapped=currentFile().document.leaves[state.leaf];
  state.editOrigin={path:mapped.path,revision:currentFile().revision,projectRevision:state.snapshot.projectRevision};
  $('#edit-origin').textContent=`${mapped.path} · characters ${mapped.start}–${mapped.end}`;
  $('#edit-text').value=mapped.text;$('#edit-error').textContent='';$('#edit-dialog').showModal();$('#edit-text').focus();
};
$('#edit-form').onsubmit=async event=>{
  event.preventDefault();event.submitter.disabled=true;const s=state.snapshot;
  try{await api('/api/save',{branch:s.branch,...state.editOrigin,leaf:state.leaf,text:$('#edit-text').value});$('#edit-dialog').close();await openBranch(s.branch,true);toast('CV draft updated on this computer');}
  catch(error){$('#edit-error').textContent=error.message;}finally{event.submitter.disabled=false;}
};
const needsDecision=run=>!!(run?.requirementsApprovalNeeded||run?.factualReview?.state==='pending');
async function followContinuation(job, snapshot){
  if(state.snapshot!==snapshot)return job;
  // Remember even an already-finished response. Polling may have observed it
  // before this request returned, so another monitor change is not guaranteed.
  snapshot.running=job;state.graphRunId=job.id;
  await runMonitor.refresh();
  if(state.snapshot===snapshot){
    const latest=state.runs.find(run=>run.id===job.id)||job;
    if(!isActiveRun(latest))await runsChanged(state.runs.some(run=>run.id===job.id)?state.runs:[job,...state.runs]);
  }
  if(state.snapshot){renderWorkflow();configureWorkflow();updateSaveState();}
  return state.runs.find(run=>run.id===job.id)||job;
}
async function continueApproved(ident, branch=state.snapshot?.branch){
  const s=state.snapshot;
  if(!s||s.branch!==branch||state.dirty||state.jobDirty)throw new Error('Approval saved. Reopen this application with saved drafts to continue.');
  const run=ident?state.runs.find(r=>r.id===ident):state.runs.find(r=>r.branch===branch&&r.requirementsDraft&&!isActiveRun(r));
  if(!ident&&!run){await runMonitor.refresh();return;}
  const job=await api('/api/review-continue',{id:ident||run.id,revision:s.revision,jobRevision:s.jobRevision});
  const latest=await followContinuation(job,s);
  if(state.snapshot?.branch===branch)notice(isActiveRun(latest)?'Approved. Continuing preparation…':latest.message);
}
async function runAdapt(steps=workflowOptions().steps){
  if(!state.snapshot||state.snapshot.running||state.launching)return;
  if(!steps.length){notice('Select at least one step.',true);return;}
  if(state.dirty||state.jobDirty){notice('Save your CV and job description before starting AI.',true);return;}
  state.launching=true;$('#run-adapt').disabled=true;$('#run-all').disabled=true;$('#task-run').disabled=true;editors.current.setReadOnly(true);$('#job-description').readOnly=true;$('#save-job').disabled=true;$('#branch-from').disabled=true;const s=state.snapshot;
  renderProviders();
  for(const id of aiSteps.map(id=>'step-'+id))$('#'+id).disabled=true;
  try{const issue=aiSetup.problem(steps);if(issue)throw new Error(issue);const job=await api('/api/adapt',{branch:s.branch,revision:s.revision,jobRevision:s.jobRevision,aiConfig:aiSetup.value(),language:$('#language').value,workflow:{steps},engine:setupChecks.engine(),reviewPolicy:$('#review-policy').value});s.running=job;if(state.snapshot===s){state.graphRunId=job.id;renderProviders();configureWorkflow();renderWorkflow();updateSaveState();$('#ai-status').textContent=job.message;}await runMonitor.refresh();}
  catch(error){if(state.snapshot===s){notice(error.message,true);configureWorkflow();editors.current.setReadOnly(!s.editable||currentFile()?.exists===false);$('#job-description').readOnly=!s.editable;$('#save-job').disabled=!s.editable;$('#branch-from').disabled=false;}}
  finally{state.launching=false;if(state.snapshot){renderProviders();configureWorkflow();renderWorkflow();}}
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
      if(loaded&&finished){$('#ai-status').textContent=finished.message;notice(finished.message,finished.status!=='succeeded'&&!needsDecision(finished));}
    }else{
      editors.current.setReadOnly(!s.editable||currentFile()?.exists===false);$('#job-description').readOnly=!s.editable;
      $('#save-job').disabled=!s.editable;$('#branch-from').disabled=false;
      renderProviders();updateSaveState();
      configureWorkflow();
      notice('The preparation finished. Your unsaved edits are safe; refresh to review the results.',true);
    }
  }
}
async function openRun(run){
  if(!canLeave())return;
  // Recorded results are immutable; reuse an idle, clean application instead
  // of racing a second full reload against completion polling.
  const current=state.snapshot;
  const loaded=current?.branch===run.branch&&!current.running&&!state.dirty&&!state.jobDirty
    ? current : await openBranch(run.branch,true);if(!loaded)return;
  state.graphRunId=run.id;renderWorkflow();
  setView('ai');$('#ai-status').textContent=run.message;
  if(!isActiveRun(run)){
    const detail=await api('/api/job-result?id='+encodeURIComponent(run.id));
    if(state.snapshot!==loaded)return;
    const settings=[run.provider?aiSetup.summary(run):'', [...$('#language').options].find(option=>option.value===run.language)?.textContent||run.language].filter(Boolean).join(' · ');
    $('#selected-run').hidden=false;$('#selected-run-info').textContent=`${runSteps(run)} · ${runLabel(run)} · ${new Date(run.createdAt*1000).toLocaleString()} · ${run.provider?settings:'Local checks; no AI used'} · ${Math.round(run.elapsedSeconds || 0)}s. Results from this preparation. Your application may contain newer edits.`;
    renderAttemptHistory(detail);
    $('#selected-run-files').replaceChildren();
    for(const [path,content] of Object.entries(detail.files)){
      $('#selected-run-files').append(reportDetails(path,content,{open:/analy(sis|ze)\.md$/.test(path),label:detail.inputs?.includes(path)?`Starting material · ${fileLabel(path)}`:fileLabel(path)}));
    }
    if(!Object.keys(detail.files).length)$('#selected-run-files').textContent='This preparation did not produce any results.';
    if(detail.coverPdf){const button=document.createElement('button');button.id='open-run-cover-pdf';button.textContent='Open generated cover-letter PDF';button.onclick=()=>openCoverPDF(detail.coverPdf.runId);$('#selected-run-files').prepend(button);}

  }
  $('#ai-panel').scrollIntoView({block:'start'});
}
function workflowOptions(){return {steps:aiSteps.filter(id=>$('#step-'+id).checked)};}
function configureWorkflow(){
  const s=state.snapshot, available=state.session.workflow || {};
  const selected=s.running?.stages?.length ? s.running.stages.filter(stage=>stage.status!=='skipped').map(stage=>stage.id) : state.workflowChoices.get(s.branch)?.steps || ['analyze','adapt',...(available.review?['review']:[])];
  for(const id of aiSteps){
    const input=$('#step-'+id);input.checked=selected.includes(id)&&stepAvailable(id);input.disabled=!stepAvailable(id)||!!s.running||!!state.launching||!s.editable;
    if(!stepAvailable(id)) $('#hint-'+id).textContent='Update Vita CV to use this step.';
  }
  const setupProblem=aiSetup.problem(workflowOptions().steps);
  const blocked=!state.session.vita||!s.editable||!!s.running||!!state.launching||!!setupProblem;
  $('#ai-config-validation').textContent=setupProblem;
  $('#ai-config-validation').hidden=!setupProblem;
  $('#run-adapt').textContent='Start selected steps';
  $('#run-adapt').disabled=blocked||!workflowOptions().steps.length;
  $('#run-all').disabled=blocked||!!aiSetup.problem(aiSteps.filter(stepAvailable));
  aiSetup.refresh();
}
function renderWorkflow(){
  if(!state.snapshot)return;
  const runs=state.runs.filter(run=>run.branch===state.snapshot.branch);
  const selected=state.graphRunId || state.snapshot.running?.id || runs[0]?.id || 'draft';
  const select=$('#workflow-run');
  select.replaceChildren(new Option('New preparation','draft'),...runs.map(run=>new Option(`${run.attempt?'Attempt '+run.attempt+' · ':''}${new Date(run.createdAt*1000).toLocaleString()} — ${runSteps(run)} · ${runLabel(run)}${isActiveRun(run)?'':run.reviewed?' · Reviewed':' · Needs review'}`,run.id)));
  const run=runs.find(run=>run.id===selected) || (state.snapshot.running?.id===selected?state.snapshot.running:null);
  if(run&&!runs.some(item=>item.id===run.id))select.add(new Option('Current preparation',run.id));
  select.value=run?run.id:'draft';state.displayedRun=run;
  setupChecks.summary(run);
  const finished=run&&!isActiveRun(run);
  for(const id of ['requirements-current-open','requirements-captured','task-requirements','step-requirements'])$('#'+id).disabled=false;
  $('#requirements-captured').hidden=!run?.requirementsRevision&&!run?.requirementsDraft;
  $('#requirements-captured').textContent=run?.requirementsRevision?'Requirements used · '+run.requirementsRevision.slice(0,12)+(run.requirementsStatus&&run.requirementsStatus!=='current'?' · needs update':''):'Review job requirements';
  $('#review-facts').hidden=!finished||!run?.factualReview;
  $('#review-facts').disabled=!!state.snapshot.running||!!state.launching||!!state.openingRunId;
  $('#review-facts').textContent=run?.factualReview?.state==='resolved'?'View factual decisions':'Review factual changes';
  $('#inspect-run').hidden=!run;$('#inspect-step').hidden=!run;$('#inspect-step-dialog').hidden=!run;
  $('#resume-run').hidden=!run?.resumeAvailable;$('#resume-run').disabled=!!state.snapshot.running||!!state.launching||!!state.retryPlanning||!state.snapshot.editable;
  $('#view-run').hidden=!finished;$('#view-run').disabled=!!state.openingRunId;
  $('#view-run').textContent=state.openingRunId?'Opening results…':'View results';
  const reviewButton=$('#mark-run-reviewed');reviewButton.hidden=!finished;
  reviewButton.disabled=!!run?.reviewed||!!state.reviewingRunId;
  reviewButton.textContent=run?.reviewed?'Reviewed':state.reviewingRunId===run?.id?'Saving review…':'Mark as reviewed';
   $('#workflow-summary').textContent=run ? (run.factualReview?run.message:runFailureText(run)||run.message) : 'Choose the steps for your next preparation. Only selected AI steps will use your AI service.';
  if(run?.reviewPolicy==='automatic')$('#workflow-summary').textContent+=' Automatic approvals selected for this preparation.';
  renderGraph($('#workflow-graph'),{run,history:runs,options:workflowOptions(),available:state.session.workflow,selected:state.selectedTask,select:selectTask,config:run?.stepConfig||Object.fromEntries(aiSteps.map(step=>[step,aiSetup.route(step)]))});
  const next=$('#workflow-next');next.disabled=!!state.snapshot.running||!!state.launching;
  next.textContent=run?.requirementsApprovalNeeded?'Review job requirements':run?.factualReview?.state==='pending'?'Review CV changes':run?.resumeAvailable?'Continue preparation':finished&&run.status==='succeeded'?'Preview your PDF':'Prepare application';
  $('#workflow-action').dataset.state=needsDecision(run)?'review':run?.status==='failed'?'failed':'ready';
  $('#workflow-next-help').textContent=needsDecision(run)?'One review, then the remaining steps continue automatically.':run?.status==='failed'?(runFailureText(run)||run.message):finished&&run.status==='succeeded'?'Your application is updated. Check the final layout before saving.':'Prepare everything, or choose individual steps in Job details & AI.';
  $('#review-policy').disabled=!!state.snapshot.running||!!state.launching;
  if(state.selectedTask)updateInspector();
}
function updateInspector(){
  const task=graphStages(state.displayedRun,workflowOptions(),state.session.workflow).find(t=>t.id===state.selectedTask);
  if(!task)return;
  $('#task-inspector').hidden=false;$('#task-title').textContent=task.title;
  const route=state.displayedRun?.stepConfig?.[task.id]||(!state.displayedRun&&task.id!=='validating'?aiSetup.route(task.id):null);
  $('#task-description').textContent=task.detail+(route?' AI setup: '+aiSetup.summary(route)+'. Connection: '+aiSetup.connectionName(route)+'.':task.id==='validating'?' This step runs locally without an AI model.':'');
  $('#task-status').textContent=`${statusNames[task.status] || task.status} · ${task.output}`;
  $('#task-output').textContent=task.id==='validating'?'Compare current CVs':task.id==='adapt'?'View CV source':'View results';
  $('#task-run').textContent=task.id==='validating'?'Check current changes':'Start this step';
  $('#task-requirements').hidden=task.id!=='extract';
  $('#task-configure').hidden=task.id==='validating';
  $('#task-configure').textContent=state.displayedRun?'Configure next run':'Configure AI';
  $('#task-configure').disabled=!!state.snapshot.running||!!state.launching||!state.snapshot.editable;
  $('#task-run').disabled=!state.snapshot.editable||!!state.snapshot.running||!!state.launching||!stepAvailable(task.id)||(task.id!=='validating'&&(!state.session.vita||!!aiSetup.problem([task.id])));
  $('#task-output').disabled=isActiveRun(state.displayedRun)||!['succeeded','unknown'].includes(task.status);
  if(failureText(state.displayedRun,task.id))$('#task-status').textContent=failureText(state.displayedRun,task.id);
  if(isActiveRun(state.displayedRun))$('#task-status').textContent+=' · Results open after the preparation finishes.';
}
function selectTask(task){
  if(!state.snapshot)return;
  state.selectedTask=task.id;renderWorkflow();
  if(aiSteps.includes(task.id))aiSetup.openStep(task.id,{
    history:!!state.displayedRun,recorded:state.displayedRun?.stepConfig?.[task.id],
    readOnly:!!state.snapshot.running||!!state.launching||!state.snapshot.editable,
    allowNext:!state.snapshot.running&&!state.launching&&state.snapshot.editable,
  });
}
$('#workflow-next').onclick=()=>{
  const run=state.displayedRun;
  if(run?.requirementsApprovalNeeded)return requirements.open().catch(e=>notice(e.message,true));
  if(run?.factualReview?.state==='pending')return factualReview.open(run).catch(e=>notice(e.message,true));
  if(run?.resumeAvailable){state.resumeCaptured=true;$('#resume-current-config').checked=false;return reviewResume();}
  if(run?.status==='succeeded'){setView('pdf');return;}
  const steps=aiSteps.filter(stepAvailable);
  if(aiSetup.problem(steps)||!state.snapshot.job.trim()){setView('ai');$('#ai-panel').scrollIntoView({block:'start'});notice('Add the job description and choose your AI setup, then prepare the application.');return;}
  return runAdapt(steps);
};
$('#view-run').onclick=async()=>{
  const run=state.displayedRun;if(!run||isActiveRun(run)||state.openingRunId)return;
  state.openingRunId=run.id;renderWorkflow();
  try{await openRun(run);}catch(error){notice(error.message,true);}
  finally{state.openingRunId=null;renderWorkflow();}
};
function stepTitle(id){return graphStages(null,{},{}).find(task=>task.id===id)?.title||id;}
for(const id of ['task-requirements','step-requirements','requirements-current-open'])$('#'+id).onclick=()=>requirements.open().catch(e=>notice(e.message,true));
$('#requirements-captured').onclick=()=>requirements.open(state.displayedRun?.requirementsRevision?state.displayedRun:null).catch(e=>notice(e.message,true));
$('#review-facts').onclick=()=>{if(state.displayedRun)factualReview.open(state.displayedRun).catch(error=>notice(error.message,true));};
function renderAttemptHistory(detail){
  const area=$('#attempt-history');area.replaceChildren();
  const heading=document.createElement('h3');heading.textContent='Attempt history';area.append(heading);
  const checkpoints=document.createElement('p');checkpoints.className='helper';
  checkpoints.textContent=detail.run.checkpointSteps?.length?'Verified results retained: '+detail.run.checkpointSteps.map(stepTitle).join(', ')+'.':'No verified checkpoints retained. A retry will run every selected step again.';area.append(checkpoints);
  for(const attempt of detail.attemptHistory||[detail.run]){
    const row=document.createElement('div');row.className='attempt-row';
    const button=document.createElement('button');button.type='button';button.className='quiet';
    button.textContent=`Attempt ${attempt.attempt||1} · ${runLabel(attempt)}${attempt.id===detail.run.id?' · Viewing':''}`;
    button.disabled=attempt.id===detail.run.id;button.onclick=()=>openRun(attempt).catch(error=>notice(error.message,true));row.append(button);
    if(attempt.requirementsRevision||attempt.requirementsDraft){const requirementsButton=document.createElement('button');requirementsButton.textContent='Requirements '+(attempt.requirementsRevision||attempt.requirementsDraft)+(attempt.requirementsStatus&&attempt.requirementsStatus!=='current'?' · needs update':'');requirementsButton.onclick=()=>requirements.open(attempt).catch(e=>notice(e.message,true));row.append(requirementsButton);}
    if(attempt.factualReview){const review=document.createElement('button');review.type='button';review.textContent=attempt.factualReview.state==='resolved'?'View factual decisions':'Review factual changes';review.onclick=()=>factualReview.open(attempt).catch(error=>notice(error.message,true));row.append(review);}
    if(attempt.parentRunId){const parent=document.createElement('span');parent.className='helper';const prior=(detail.attemptHistory||[]).find(item=>item.id===attempt.parentRunId);parent.textContent='Continues attempt '+(prior?.attempt||'unknown')+' · '+(attempt.configurationChanged?'Changed setup':'Captured setup preserved');row.append(parent);}
    for(const [step,outcome] of Object.entries(attempt.outcomes||{})){
      const text=document.createElement('p');text.className='helper';
      text.textContent=stepTitle(step)+': '+(outcome.status==='success'?'Completed':'Could not finish')+(outcome.backend?.attempts?.length?' · AI attempts: '+outcome.backend.attempts.map(item=>`${item.number}: ${item.category.replaceAll('_',' ')}`).join('; '):'');row.append(text);
      const failure=failureText(attempt,step);if(failure){const info=document.createElement('p');info.className='provider-failure';info.textContent=failure;row.append(info);}
    }
    area.append(row);
  }
}
async function reviewResume(){
  const run=state.displayedRun,s=state.snapshot;
  if(!run?.resumeAvailable||state.retryPlanning||state.launching)return;
  if(state.dirty||state.jobDirty){notice('Save your CV and job description drafts before retrying.',true);return;}
  state.retryPlanning=true;$('#confirm-resume').disabled=true;$('#resume-current-config').disabled=true;renderWorkflow();
  try{
    const captured=state.resumeCaptured&&!$('#resume-current-config').checked;
    const request={id:run.id,revision:s.revision,jobRevision:s.jobRevision,...(captured?{}:{aiConfig:aiSetup.value(),language:$('#language').value})};
    const plan=await api('/api/resume-preview',request);
    if(state.snapshot!==s)return;
    state.resumeReview={request,plan,snapshot:s};
    $('#resume-summary').textContent=`Attempt ${plan.attempt}, continuing attempt ${run.attempt||1}. Output language: ${[...$('#language').options].find(item=>item.value===(captured?run.language:$('#language').value))?.textContent||run.language}. Captured TeX engine: ${run.compileEngine||'auto'}. ${captured?'Preserves the AI setup and language captured for this preparation.':'Uses the AI setup currently shown for this application.'}`;
    $('#resume-config-choice').hidden=!state.resumeCaptured;
    $('#resume-reuse').textContent=plan.reuse.length?plan.reuse.map(stepTitle).join(', '):'None. Start again with the current inputs and setup.';
    $('#resume-rerun').textContent=[...plan.rerun.map(stepTitle),'Final checks'].join(', ');
    $('#resume-adapted').hidden=!plan.reuse.includes('adapt');$('#resume-error').textContent='';$('#confirm-resume').disabled=false;
    if(!$('#resume-dialog').open)$('#resume-dialog').showModal();
  }catch(error){
    state.resumeReview=null;$('#confirm-resume').disabled=true;$('#resume-error').textContent=error.message;notice(error.message,true);
    if(state.resumeCaptured){
      $('#resume-config-choice').hidden=false;
      $('#resume-summary').textContent='The captured setup could not be checked. Reconnect the account in this application, then explicitly choose its current setup, or cancel and review the error.';
      $('#resume-reuse').textContent='Not verified. A valid retry plan is required before starting.';
      $('#resume-rerun').textContent='Not planned yet.';$('#resume-adapted').hidden=true;
      if(!$('#resume-dialog').open)$('#resume-dialog').showModal();
    }
  }finally{state.retryPlanning=false;$('#resume-current-config').disabled=false;renderWorkflow();}
}
$('#resume-run').onclick=()=>{state.resumeCaptured=true;$('#resume-current-config').checked=false;reviewResume();};
$('#resume-current-config').onchange=()=>reviewResume();
$('#resume-form').onsubmit=async event=>{
  event.preventDefault();const review=state.resumeReview;if(!review||state.launching)return;
  state.launching=true;$('#confirm-resume').disabled=true;renderWorkflow();configureWorkflow();
  try{
    const job=await api('/api/resume',{...review.request,token:review.plan.token});
    $('#resume-dialog').close();$('#selected-run').hidden=true;
    await followContinuation(job,review.snapshot);
  }catch(error){$('#resume-error').textContent=error.message;}
  finally{state.launching=false;$('#confirm-resume').disabled=false;configureWorkflow();renderWorkflow();}
};
$('#resume-dialog').onclose=()=>{if(!state.launching)state.resumeReview=null;};
$('#cleanup-checkpoints').onclick=async()=>{
  const button=$('#cleanup-checkpoints');button.disabled=true;
  try{const result=await api('/api/checkpoints-cleanup',{});$('#cleanup-checkpoints-status').textContent=`Removed checkpoints for ${result.removed.length} preparations. ${result.retainedRuns} retained. Your drafts and review results are unchanged.`;await runMonitor.refresh();renderWorkflow();}
  catch(error){$('#cleanup-checkpoints-status').textContent=error.message;}finally{button.disabled=false;}
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
$('#task-configure').onclick=()=>aiSetup.openStep(state.selectedTask);
$('#run-all').onclick=()=>runAdapt(aiSteps.filter(stepAvailable));
$('#toggle-workflow').onclick=()=>{
  const body=$('#workflow-body');body.hidden=!body.hidden;
  $('#toggle-workflow').textContent=body.hidden?'Show steps':'Hide steps';
  $('#toggle-workflow').setAttribute('aria-expanded',String(!body.hidden));
};
$('#task-output').onclick=async()=>{
  const task=state.selectedTask, run=state.displayedRun;
  if(task==='validating'){setView('structure');$('#comparison').scrollIntoView({block:'start'});return;}
  try{
    if(task==='cover'&&run&&!isActiveRun(run)){const detail=await api('/api/job-result?id='+encodeURIComponent(run.id));if(detail.coverPdf){await openCoverPDF(run.id);return;}}
    if(run&&!isActiveRun(run))await openRun(run);else setView('ai');
    const match={extract:'job.json',analyze:'analy',review:'review.',cover:'cover',adapt:'main.tex'}[task];
    const area=run&&!isActiveRun(run)?$('#selected-run-files'):$('#artifacts');
    const item=[...area.querySelectorAll('details[data-path]')].find(el=>el.dataset.path.includes(match));
    if(item){item.open=true;item.scrollIntoView({block:'center'});item.querySelector('summary').focus();}
    else notice('This step has no saved results. Check the preparation status.');
  }catch(error){notice(error.message,true);}
};
let pdfjs;
async function pdfLibrary(){if(!pdfjs){pdfjs=await import('./vendor/pdf.mjs');pdfjs.GlobalWorkerOptions.workerSrc='/vendor/pdf.worker.mjs';}return pdfjs;}
async function savePDF(side, info, button){
  const snapshot=state.snapshot;if(!snapshot)return;
  if(side==='current'&&state.dirty){notice('Save your CV draft and recreate the preview before saving the PDF.',true);return;}
  button.disabled=true;
  try{
    let saved;
    try{saved=await api('/api/pdf-save',{id:info.id,branch:snapshot.branch});}
    catch(error){
      if(!error.existingRevision||!window.confirm(`${error.filename} already exists in this application folder. Replace it with this preview?`)){
        if(!error.existingRevision)throw error;return;
      }
      saved=await api('/api/pdf-save',{id:info.id,branch:snapshot.branch,existingRevision:error.existingRevision});
    }
    if(state.snapshot===snapshot)notice(`Saved ${saved.filename} in this application’s folder.`);
  }catch(error){if(state.snapshot===snapshot)notice(error.message,true);}
  finally{button.disabled=false;}
}
async function renderPDF(side, info, generation){
  const library=await pdfLibrary();const container=$(`#${side}-pdf`);
  const loadingTask=library.getDocument({url:info.url,cMapUrl:'/vendor/cmaps/',cMapPacked:true,standardFontDataUrl:'/vendor/standard_fonts/',wasmUrl:'/vendor/wasm/'});
  const pdf=await loadingTask.promise;
  if(generation!==state.pdfGeneration){await loadingTask.destroy();return;}
  container.replaceChildren();const actions=document.createElement('div');actions.className='pdf-actions';const link=document.createElement('a');link.className='pdf-download';link.href=info.url;link.tabIndex=0;link.target='_blank';link.rel='noopener';link.textContent='Open PDF ↗';const save=document.createElement('button');save.className='save-pdf';save.textContent='Save PDF to application folder';save.title=info.filename||'Save this PDF';save.disabled=!state.snapshot?.editable;save.onclick=()=>savePDF(side,info,save);actions.append(link,save);container.append(actions);
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
async function openCoverPDF(runId=null){
  state.pdfDocument='cover';$('#pdf-document').value='cover';setView('pdf');await compilePDFs(runId);
}
$('#pdf-document').onchange=async()=>{
  state.pdfDocument=$('#pdf-document').value;const generation=++state.pdfGeneration;setView('pdf');
  try{for(const side of state.pdfDocument==='cover'?['cover']:['original','current'])if(state.pdfs[side])await renderPDF(side,state.pdfs[side],generation);}catch(error){notice(error.message,true);}
};
async function compilePDFs(runId=null){
  if(state.dirty&&state.pdfDocument==='cv'){notice('Save your CV draft before creating PDF previews.',true);return;}
  if(!state.snapshot)return;
  const document=state.pdfDocument, generation=++state.pdfGeneration, branch=state.snapshot.branch;$('#compile').disabled=true;notice('Creating your PDF preview…');
  try{
    const results=await Promise.allSettled((document==='cover'?['cover']:['original','current']).map(async side=>{
      delete state.pdfs[side];$(`#${side}-pdf`).innerHTML='<p class="pdf-message">Creating PDF preview…</p>';
      try{const result=await api('/api/pdf',{branch,side:side==='cover'?'current':side,engine:$('#engine').value,document,runId:document==='cover'?runId:null});if(generation!==state.pdfGeneration)return;state.pdfs[side]=result;if(side==='cover')$('#cover-pdf-label').textContent=runId?'PDF from this preparation':applicationName(branch);await renderPDF(side,result,generation);return result;}
      catch(error){if(generation===state.pdfGeneration)$(`#${side}-pdf`).innerHTML=`<p class="pdf-message">${esc(error.message)}</p>`;throw error;}
    }));
    if(generation!==state.pdfGeneration)return;
    const warnings=results.flatMap(r=>r.status==='fulfilled'?r.value?.warnings||[]:[r.reason.message]);notice(warnings.length?warnings.join('\n'):(document==='cover'?'Cover-letter PDF ready. Text is selectable.':'PDF previews are ready. Select and copy text from either page.'),results.some(r=>r.status==='rejected'));
  }finally{$('#compile').disabled=!state.snapshot;}
}
$('#zoom').onchange=async()=>{const generation=++state.pdfGeneration;try{for(const side of state.pdfDocument==='cover'?['cover']:['original','current'])if(state.pdfs[side])await renderPDF(side,state.pdfs[side],generation);}catch(error){notice(error.message,true);}};
document.querySelectorAll('[data-filter]').forEach(button=>button.onclick=()=>{state.filter=button.dataset.filter;document.querySelectorAll('[data-filter]').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));renderBranches();});
$('#search').oninput=renderBranches;$('#refresh').onclick=loadBranches;$('#new-branch').onclick=showCreate;$('#branch-from').onclick=showCreate;
$('#back').onclick=()=>{if(!canLeave())return;const previous=state.snapshot?.branch;state.generation++;state.pdfGeneration++;state.snapshot=null;state.dirty=false;state.jobDirty=false;$('#workspace').hidden=true;$('#board').hidden=false;document.body.classList.remove('in-workspace');history.replaceState(null,'','/');$('#search').focus();if(previous)releaseBranch(previous);loadBranches();};
$('#reload').onclick=()=>openBranch(state.snapshot?.branch||$('#branch-title').textContent);
document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>setView(button.dataset.view));
$('.tabs').addEventListener('focusin',event=>requestAnimationFrame(()=>{
  if(document.activeElement===event.target)event.target.scrollIntoView({block:'nearest',inline:'nearest'});
}));
$('.tabs').onkeydown=event=>{
  if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
  const tabs=[...document.querySelectorAll('[data-view]')], index=tabs.indexOf(event.target);if(index<0)return;
  const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
  event.preventDefault();setView(tabs[next].dataset.view);tabs[next].focus();
};
document.querySelectorAll('.close-dialog').forEach(button=>button.onclick=()=>button.closest('dialog').close());
$('#job-description').oninput=()=>{state.jobDirty=$('#job-description').value!==state.snapshot.job;$('#job-state').textContent=state.jobDirty?'Unsaved changes':'Saved on this computer';updateSaveState();};
$('#save-source').onclick=saveSource;$('#save-job').onclick=saveJob;$('#commit-push').onclick=showCommit;$('#run-adapt').onclick=()=>runAdapt();$('#compile').onclick=()=>compilePDFs();
window.addEventListener('beforeunload',event=>{if(state.dirty||state.jobDirty){event.preventDefault();event.returnValue='';}});
window.addEventListener('pagehide',()=>{
  if(state.snapshot&&state.session)fetch('/api/release-worktree',{method:'POST',keepalive:true,
    headers:{'Content-Type':'application/json','X-Vita-Token':state.session.token},
    body:JSON.stringify({branch:state.snapshot.branch})}).catch(()=>{});
});
document.addEventListener('keydown',event=>{if(event.key==='/'&&!event.target.closest('input,textarea,select,[contenteditable]')&&!$('#board').hidden){event.preventDefault();$('#search').focus();}if((event.ctrlKey||event.metaKey)&&event.key==='s'&&state.snapshot){event.preventDefault();state.view==='ai'?saveJob():saveSource();}});
const executionInspector=initDiagnostics({api,retry:async(id,close)=>{
  if(state.dirty||state.jobDirty)throw new Error('Save your CV and job description drafts before retrying.');
  const run=await api('/api/job?id='+encodeURIComponent(id));
  close();await openRun(run);
  if(state.snapshot?.branch!==run.branch)throw new Error('Open this application before retrying.');
  state.resumeCaptured=true;$('#resume-current-config').checked=false;await reviewResume();
}});
$('#inspect-run').onclick=()=>executionInspector.open(state.displayedRun?.id);
$('#inspect-step').onclick=()=>executionInspector.open(state.displayedRun?.id,state.selectedTask);
$('#inspect-step-dialog').onclick=()=>{
  $('#step-ai-dialog').close();executionInspector.open(state.displayedRun?.id,state.selectedTask);
};
try{state.session=await api('/api/session');await loadBranches();const params=new URLSearchParams(location.search), branch=params.get('branch');if(['structure','source','pdf','changes','ai'].includes(params.get('view')))state.view=params.get('view');if(branch)await openBranch(branch);runMonitor=createRunMonitor({api,changed:runsChanged});runMonitor.start();}catch(error){$('#branch-list').innerHTML=`<p class="empty">${esc(error.message)}</p>`;}

setInterval(()=>{document.querySelectorAll(".dag-time[data-started-at]").forEach(el=>{el.textContent=`${Math.max(0,Math.floor(Date.now()/1000-Number(el.dataset.startedAt)))}s`;});},1000);
