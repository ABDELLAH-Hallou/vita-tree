// All diagnostic values are rendered as text, never as HTML.
export function initExecutionInspector({api, retry}) {
  const $=s=>document.querySelector(s), host=$('#execution-inspector'), dialog=$('#diagnostics-dialog');
  const names={extract:'Identify job requirements',analyze:'Check CV match',adapt:'Tailor CV',review:'Review CV with AI',cover:'Cover letter',validating:'Final checks',preparing:'Prepare workspace'};
  const tabs=['overview','timeline','request','response','error','artifacts'];
  host.innerHTML=`
    <div class="inspector-heading"><div><h3>Preparation history</h3><p class="helper">Choose a preparation to see what happened and what to do next.</p></div><button id="refresh-executions">Refresh preparations</button></div>
    <div class="inspector-filters"><label>Find a preparation<input id="execution-search" type="search" placeholder="Application, model, or trace ID"></label><label>Status<select id="execution-status"><option value="">All preparations</option><option value="running">In progress</option><option value="failed">Needs attention</option><option value="interrupted">Interrupted</option><option value="succeeded">Completed</option></select></label></div>
    <p id="execution-error" class="form-error" role="status"></p><div id="execution-list" class="execution-list" aria-label="Preparations"></div>
    <div class="inspector-pagination"><button id="execution-prev">Previous preparations</button><span id="execution-count" role="status"></span><button id="execution-next">More preparations</button></div>
    <section id="execution-detail" hidden aria-labelledby="execution-detail-title">
      <div class="inspector-heading"><div><h3 id="execution-detail-title" tabindex="-1">Execution details</h3><p id="execution-reference" class="helper"></p></div><div class="actions"><button id="execution-copy-trace">Copy trace ID</button><button id="execution-retry" hidden>Retry preparation</button></div></div>
      <label>Preparation step<select id="execution-step"><option value="">All steps</option>${Object.entries(names).filter(([id])=>id!=='preparing').map(([id,name])=>'<option value="'+id+'">'+name+'</option>').join('')}</select></label>
      <p id="execution-contract" role="status"></p><p id="execution-warnings" class="form-error"></p>
      <div class="inspector-tabs" role="tablist" aria-label="Execution evidence">${tabs.map((id,i)=>'<button role="tab" id="inspector-tab-'+id+'" aria-controls="inspector-panel-'+id+'" aria-selected="'+(i===0)+'" tabindex="'+(i===0?0:-1)+'">'+id[0].toUpperCase()+id.slice(1)+'</button>').join('')}</div>
      ${tabs.map((id,i)=>'<div id="inspector-panel-'+id+'" role="tabpanel" aria-labelledby="inspector-tab-'+id+'"'+(i?' hidden':'')+'></div>').join('')}
      <p id="inspector-feedback" role="status"></p>
    </section>
    <details class="technical-details"><summary>Where execution details are stored</summary><p>Trace folder: <code id="execution-location"></code></p><button id="execution-copy-location">Copy trace folder location</button><p id="execution-storage-error" class="form-error"></p><p id="execution-policy" class="helper"></p><p id="execution-retention" class="helper"></p><p class="helper">Paste the copied location into your file manager. Technical structure is not an exact prompt or model response. Sanitization does not guarantee anonymization.</p></details>`;
  let offset=0, selected=null, detail=null, generation=0, searchTimer, lastFocus=null;
  let eventOffset=0, listingVersion=0, busy=false;
  const element=(tag,text,className)=>{const el=document.createElement(tag);el.textContent=text??'';if(className)el.className=className;return el;};
  const paragraph=(parent,text)=>parent.append(element('p',text));
  function evidence(parent,label,data) {
    const item=document.createElement('details');item.className='inspector-evidence';item.append(element('summary',label));
    const pre=element('pre',JSON.stringify(data,null,2));pre.tabIndex=0;item.append(pre);parent.append(item);
  }
  function action(parent,label,handler) {const el=element('button',label);el.type='button';el.onclick=handler;parent.append(el);return el;}
  async function copy(text) {
    try{await navigator.clipboard.writeText(text);$('#inspector-feedback').textContent='Copied.';}
    catch{$('#inspector-feedback').textContent='Clipboard access is unavailable. Select and copy the displayed text.';}
  }
  function storage(value) {
    $('#execution-location').textContent=value.path;
    $('#execution-storage-error').textContent=value.error||'';
    $('#execution-policy').textContent=value.policy+' Additional content capture for new preparations: '+value.capture+'.';
    $('#execution-retention').textContent=value.retention;
  }
  async function list() {
    const version=++listingVersion;$('#refresh-executions').disabled=true;
    try{
      const data=await api('/api/executions?'+new URLSearchParams({offset,q:$('#execution-search').value,status:$('#execution-status').value}));
      if(version!==listingVersion)return;
      storage(data.storage);$('#execution-error').textContent='';
      const list=$('#execution-list');list.replaceChildren();
      for(const run of data.runs) {
        const row=document.createElement('div');row.className='execution-row';
        const button=action(row,`${run.branch} · ${run.status==='succeeded'?'Completed':run.status==='running'?'In progress':run.status==='interrupted'?'Interrupted':'Needs attention'} · Attempt ${run.attempt||'—'}`,()=>select(run.id));
        button.dataset.run=run.id;button.setAttribute('aria-pressed',String(selected===run.id));
        const info=[run.failedStep?`Stopped at ${names[run.failedStep]||run.failedStep}`:'',run.provider,run.model,`${Math.floor(run.elapsedSeconds)}s`,new Date(run.createdAt*1000).toLocaleString(),run.traceId?`Trace ${run.traceId}`:'Limited historical diagnostics'].filter(Boolean).join(' · ');
        row.append(element('span',info,'helper'));
        if(run.failedStep)action(row,'Inspect failed step',()=>select(run.id,run.failedStep));
        list.append(row);
      }
      if(!data.runs.length)paragraph(list,'No matching preparations.');
      $('#execution-count').textContent=data.total?`${offset+1}–${offset+data.runs.length} of ${data.total}`:'0 preparations';
      $('#execution-prev').disabled=offset===0;$('#execution-next').disabled=offset+20>=data.total;
    }catch(error){$('#execution-error').textContent=error.message;}
    finally{if(version===listingVersion)$('#refresh-executions').disabled=false;}
  }
  function tab(id,focus=false) {
    for(const key of tabs){const button=$('#inspector-tab-'+key);button.setAttribute('aria-selected',String(key===id));button.tabIndex=key===id?0:-1;$('#inspector-panel-'+key).hidden=key!==id;}
    if(focus)$('#inspector-tab-'+id).focus();
  }
  for(const [index,id] of tabs.entries()) {
    const button=$('#inspector-tab-'+id);button.onclick=()=>tab(id);
    button.onkeydown=event=>{
      const next=event.key==='ArrowRight'?tabs[(index+1)%tabs.length]:event.key==='ArrowLeft'?tabs[(index+tabs.length-1)%tabs.length]:event.key==='Home'?tabs[0]:event.key==='End'?tabs.at(-1):null;
      if(next){event.preventDefault();tab(next,true);}
    };
  }
  function responseLabel(ref) {
    if(ref.kind==='provider_error')return ref.content_exists===false?'Provider error reported · no error response body received':ref.content_exists===null?'Provider error details · response body not observed':'Provider error response · '+ref.capture_status;
    if(ref.content_exists===false)return ref.kind==='http_response'?'No HTTP response received':'No model response produced (generation rejected or stopped before output)';
    if(ref.content_exists===null)return 'No response observed · whether content exists is unknown';
    return {disabled:'Response exists · content capture disabled',suppressed:'Response exists · privacy suppression',truncated:'Response structure truncated',unavailable:'Response artifact unavailable',redacted:'Response exists · source values removed',captured:'Sanitized diagnostic summary available'}[ref.capture_status];
  }
  async function inspectArtifact(id,area,button) {
    button.disabled=true;const run=selected;
    try{
      const result=await api('/api/execution-artifact?'+new URLSearchParams({id:run,artifact:id}));
      if(run!==selected)return;
      area.querySelector('[data-artifact-content]')?.remove();
      const content=element('pre',result.content?JSON.stringify(result.content,null,2):result.message||`No body is available: ${result.state}.`);
      content.dataset.artifactContent='';content.tabIndex=0;area.append(content);
    }catch(error){$('#inspector-feedback').textContent=error.message;}
    finally{button.disabled=false;}
  }
  function captures(parent,refs) {
    if(!refs.length){paragraph(parent,'No capture references were recorded for this selection. Response content must not be assumed to exist.');return;}
    for(const ref of refs) {
      const area=document.createElement('div');area.className='inspector-capture';
      area.append(element('strong',['response','provider_error','http_response'].includes(ref.kind)?responseLabel(ref):`${ref.kind} · ${ref.capture_status}`));
      paragraph(area,`Capture reason: ${ref.reason.replaceAll('_',' ')} · ${ref.bytes} bytes · Artifact ${ref.id}`);
      if(ref.bytes&&['captured','redacted','truncated'].includes(ref.capture_status)) {
        const button=action(area,'Inspect sanitized structure',()=>inspectArtifact(ref.id,area,button));button.dataset.artifact=ref.id;
      }
      parent.append(area);
    }
  }
  function render() {
    const {run,tree,backend,overview,lineage}=detail;
    $('#execution-detail').hidden=false;
    $('#execution-detail-title').textContent=`Attempt ${run.attempt||'—'} · ${run.status}`;
    $('#execution-reference').textContent=run.traceId?`Trace ${run.traceId} · Execution ${run.id}`:`Execution ${run.id} · Historical trace unavailable`;
    $('#execution-copy-trace').disabled=!run.traceId;
    $('#execution-contract').textContent=backend.message;$('#execution-warnings').textContent=backend.warnings.join(' ');
    $('#execution-retry').hidden=!detail.resumeAvailable;storage(detail.storage);
    for(const id of tabs)$('#inspector-panel-'+id).replaceChildren();
    const overviewPanel=$('#inspector-panel-overview');
    paragraph(overviewPanel,overview.phase?`Stopped during ${overview.phase.replaceAll('_',' ')}${overview.category?` · ${overview.category.replaceAll('_',' ')}`:''}.`:run.status==='succeeded'?'Preparation completed.':'No failure phase was recorded; the cause is unknown.');
    paragraph(overviewPanel,overview.nextAction);
    if(tree.configurationChanged)paragraph(overviewPanel,'Changed configuration: this attempt uses different captured routing than its parent.');
    if(run.parentRunId)paragraph(overviewPanel,`Continues execution ${run.parentRunId}. Root execution ${run.rootRunId}.`);
    const timeline=$('#inspector-panel-timeline'), history=document.createElement('div');history.className='inspector-lineage';
    for(const item of lineage)action(history,`Attempt ${item.attempt||'—'} · ${item.status}`,()=>select(item.id));
    timeline.append(history);
    for(const item of tree.events||[])paragraph(timeline,`Tree · ${names[item.step]||'Preparation'} · ${item.phase} · ${item.status}${item.duration_ms!=null?` · ${item.duration_ms}ms`:''}${item.reusedFrom?` · verified result from ${item.reusedFrom}`:''}`);
    for(const item of backend.events) {
      const entry=document.createElement('details');entry.className='inspector-evidence';
      entry.append(element('summary',`${names[item.step]||item.step||'Backend'} · ${item.phase} · ${item.event} · ${item.status}${item.details.attempt?` · attempt ${item.details.attempt}`:''}${item.details.duration_ms!=null?` · ${item.details.duration_ms}ms`:''}${item.details.delay_seconds!=null?` · retry delay ${item.details.delay_seconds}s`:''}`));
      const pre=element('pre',JSON.stringify(item,null,2));pre.tabIndex=0;entry.append(pre);timeline.append(entry);
    }
    if(backend.totalEvents>100) {
      paragraph(timeline,`Backend events ${backend.offset+1}–${Math.min(backend.offset+100,backend.totalEvents)} of ${backend.totalEvents}.`);
      const prev=action(timeline,'Earlier events',()=>{eventOffset=Math.max(0,eventOffset-100);load(false);});prev.disabled=eventOffset===0;
      const next=action(timeline,'More events',()=>{eventOffset+=100;load(false);});next.disabled=eventOffset+100>=backend.totalEvents;
    }
    const request=$('#inspector-panel-request');
    for(const process of backend.processes)paragraph(request,`${names[process.step]||process.step} · Additional structure capture ${process.capture_enabled?'enabled':'disabled'} (reported by backend) · Logging ${process.logging_complete?'complete':'incomplete'}`);
    for(const [step,config] of Object.entries(tree.configuration||{})) {
      if($('#execution-step').value&&$('#execution-step').value!==step)continue;
      paragraph(request,`${names[step]||step} · ${config.origin==='step_override'?'Per-step override':config.origin==='shared'?'Shared settings':'Captured settings'}`);
      evidence(request,'Requested route',config.requested);
    }
    const routes=backend.routes||backend.events.filter(e=>e.event==='route');
    if(routes.length)for(const route of routes)evidence(request,'Backend-reported effective route and origins',route.details);
    else paragraph(request,'Effective provider, model, reasoning, and their origins were not reported by the backend. Requested values are not proof of the effective route.');
    evidence(request,'Captured input and configuration fingerprints',tree.inputs||{});
    evidence(request,'Source and dependency fingerprints at each step',tree.stepInputs||{});
    captures(request,backend.artifacts.filter(r=>['request','schema','instructions'].includes(r.kind)));
    captures($('#inspector-panel-response'),backend.artifacts.filter(r=>['response','http_response','provider_error'].includes(r.kind)));
    const errors=$('#inspector-panel-error'), failures=backend.processes.filter(p=>p.failure);
    if(failures.length)for(const proc of failures)evidence(errors,`${names[proc.step]||proc.step} · ${proc.failure.phase}`,proc.failure);
    else paragraph(errors,'No structured backend error was recorded. A missing capture does not mean there was an empty or successful response.');
    for(const item of tree.events||[])if(item.status==='error')evidence(errors,`Tree · ${item.phase}`,item);
    const artifacts=$('#inspector-panel-artifacts');captures(artifacts,backend.artifacts);
    action(artifacts,'Copy execution diagnostics',()=>copy(JSON.stringify({...detail,storage:undefined},null,2)));
    action(artifacts,'Review support export',async()=>{
      try{
        const summary=await api('/api/execution-export?'+new URLSearchParams({id:selected,preview:'1'}));
        artifacts.querySelector('[data-export-review]')?.remove();
        const review=document.createElement('div');review.dataset.exportReview='';review.className='inspector-capture';
        paragraph(review,summary.notice);evidence(review,'Included information',summary.included);evidence(review,'Omitted information',summary.omitted);
        const link=element('a','Download inspected support bundle');link.href='/api/execution-export?'+new URLSearchParams({id:selected});link.download='vita-tree-technical-support.zip';review.append(link);artifacts.append(review);
      }catch(error){$('#inspector-feedback').textContent=error.message;}
    });
  }
  async function load(focus=true) {
    const version=++generation, run=selected;$('#execution-error').textContent='';$('#inspector-feedback').textContent='';
    try{
      const value=await api('/api/execution?'+new URLSearchParams({id:run,step:$('#execution-step').value,offset:eventOffset}));
      if(version!==generation)return;detail=value;render();
      if(focus){$('#execution-detail-title').focus({preventScroll:true});$('#execution-detail').scrollIntoView({block:'start'});}
    }catch(error){if(version===generation)$('#execution-error').textContent=error.message;}
  }
  async function select(id,step='') {
    selected=id;eventOffset=0;$('#execution-step').value=step;await load();
    for(const button of host.querySelectorAll('[data-run]'))button.setAttribute('aria-pressed',String(button.dataset.run===id));
  }
  async function open(id=null,step='') {
    lastFocus=document.activeElement;if(!dialog.open)dialog.showModal();await list();if(id)await select(id,step);
  }
  $('#execution-copy-trace').onclick=()=>copy(detail?.run.traceId||'');
  $('#execution-copy-location').onclick=()=>copy($('#execution-location').textContent);
  $('#execution-retry').onclick=async()=>{
    if(busy||!selected)return;busy=true;$('#execution-retry').disabled=true;
    try{await retry(selected,()=>dialog.close());}catch(error){$('#execution-error').textContent=error.message;}
    finally{busy=false;$('#execution-retry').disabled=false;}
  };
  $('#refresh-executions').onclick=async()=>{await list();if(selected)await load(false);};
  $('#execution-search').oninput=()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{offset=0;list();},250);};
  $('#execution-status').onchange=()=>{offset=0;list();};
  $('#execution-step').onchange=()=>{eventOffset=0;load(false);};
  $('#execution-prev').onclick=()=>{offset=Math.max(0,offset-20);list();};
  $('#execution-next').onclick=()=>{offset+=20;list();};
  dialog.addEventListener('close',()=>{lastFocus?.isConnected&&lastFocus.focus();});
  return {open,refresh:list};
}
