import {initExecutionInspector} from './execution-inspector.js';
// Local diagnostics contain controlled events rather than document/provider payloads.
export function initDiagnostics({api, retry}) {
  const inspector=initExecutionInspector({api,retry});
  const $=selector=>document.querySelector(selector), dialog=$('#diagnostics-dialog');
  let pending=false, snapshot=null;
  const cell=(row,text)=>{const td=document.createElement('td');td.textContent=text ?? '—';row.append(td);};
  const labels={server_started:'Vita Tree started',server_stopped:'Vita Tree stopped',request_failed:'An action could not finish',history_write_failed:'Couldn’t save preparation history',history_load_failed:'Couldn’t read earlier preparation history',run_started:'Application preparation started',run_error:'Preparation needs attention',run_finished:'Application preparation finished',step_started:'A preparation step started',step_finished:'A preparation step finished',review_saved:'Review saved',provider_failed:'AI service could not finish',pdf_compiled:'PDF preview created',pdf_saved:'PDF saved',pdf_failed:'PDF could not be created',logging_failed:'Support logging is unavailable'};
  function renderEvents(){
    const summary=$('#activity-summary');summary.replaceChildren();
    for(const event of (snapshot?.events||[]).filter(item=>labels[item.event]).slice(0,12)){
      const item=document.createElement('li');const time=document.createElement('time');time.textContent=new Date(event.time).toLocaleTimeString();
      const label=document.createElement('span');label.textContent=labels[event.event];item.dataset.level=event.level;item.append(time,label);summary.append(item);
    }
    if(!summary.children.length){const item=document.createElement('li');item.textContent='No recent activity yet.';summary.append(item);}

    const query=$('#diagnostics-search').value.trim().toLowerCase();
    const body=$('#diagnostics-events');body.replaceChildren();
    for(const event of snapshot?.events || []){
      if(query&&!JSON.stringify(event).toLowerCase().includes(query))continue;
      const row=document.createElement('tr');row.dataset.level=event.level;
      cell(row,new Date(event.time).toLocaleTimeString());cell(row,event.event.replaceAll('_',' '));
      cell(row,event.step||event.operation||event.route||'');
      cell(row,[event.status,event.duration_ms!=null?`${event.duration_ms}ms`:''].filter(v=>v!==undefined&&v!=='').join(' · '));
      cell(row,[event.error_type,event.exit_code!=null?`exit ${event.exit_code}`:'',event.errno!=null?`errno ${event.errno}`:'',event.winerror!=null?`Windows ${event.winerror}`:'',event.location].filter(Boolean).join(' · '));
      cell(row,[event.request_id?`request ${event.request_id}`:'',event.run_id?`run ${event.run_id}`:''].filter(Boolean).join(' · '));body.append(row);
    }
    if(!body.children.length){const row=document.createElement('tr');const td=document.createElement('td');td.colSpan=6;td.textContent='No matching events.';row.append(td);body.append(row);}
  }
  async function refresh(){
    if(pending)return;pending=true;$('#refresh-diagnostics').disabled=true;
    try{
      snapshot=await api('/api/diagnostics');
      $('#diagnostics-error').textContent='';
      for(const [id,value] of Object.entries({active:snapshot.history.running,completed:snapshot.history.succeeded,failed:snapshot.history.failed,
        requests:snapshot.requests.total,errors:snapshot.requests.failed,latency:snapshot.requests.meanMs}))$('#metric-'+id).textContent=value;
      $('#diagnostics-location').textContent=snapshot.logging.path||'Available for this session only';
      $('#diagnostics-logging').textContent=snapshot.logging.error||'Older support log files are replaced automatically.';
      $('#diagnostics-uptime').textContent=`Vita Tree has been running for ${Math.floor(snapshot.uptimeSeconds)} seconds. Performance counts reset when it restarts; preparation history is kept.`;
      renderEvents();
    }catch(error){$('#diagnostics-error').textContent=error.message;}
    finally{pending=false;$('#refresh-diagnostics').disabled=false;}
  }
  for(const button of document.querySelectorAll('[data-open-diagnostics]'))button.onclick=()=>{inspector.open();refresh();};
  $('#refresh-diagnostics').onclick=refresh;$('#diagnostics-search').oninput=renderEvents;
  $('#download-diagnostics').onclick=()=>{
    if(!snapshot)return;
    const clean={...snapshot,logging:{enabled:snapshot.logging.enabled,error:snapshot.logging.error}};
    const url=URL.createObjectURL(new Blob([JSON.stringify(clean,null,2)],{type:'application/json'}));
    const link=document.createElement('a');link.href=url;link.download='vita-tree-support-report.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  setInterval(()=>{if(dialog.open)refresh();},3000);
  return inspector;
}
