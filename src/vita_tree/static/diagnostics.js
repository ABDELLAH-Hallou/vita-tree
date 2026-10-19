// Local diagnostics contain controlled events rather than document/provider payloads.
export function initDiagnostics({api}) {
  const $=selector=>document.querySelector(selector), dialog=$('#diagnostics-dialog');
  let pending=false, snapshot=null;
  const cell=(row,text)=>{const td=document.createElement('td');td.textContent=text ?? '—';row.append(td);};
  function renderEvents(){
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
      $('#diagnostics-location').textContent=snapshot.logging.path||'Memory only';
      $('#diagnostics-logging').textContent=snapshot.logging.error||'Rotating JSON logs · Up to 6 MB per server session.';
      $('#diagnostics-uptime').textContent=`Server uptime: ${Math.floor(snapshot.uptimeSeconds)}s. Request metrics reset on restart; saved run history persists.`;
      renderEvents();
    }catch(error){$('#diagnostics-error').textContent=error.message;}
    finally{pending=false;$('#refresh-diagnostics').disabled=false;}
  }
  for(const button of document.querySelectorAll('[data-open-diagnostics]'))button.onclick=()=>{dialog.showModal();refresh();};
  $('#refresh-diagnostics').onclick=refresh;$('#diagnostics-search').oninput=renderEvents;
  $('#download-diagnostics').onclick=()=>{
    if(!snapshot)return;
    const clean={...snapshot,logging:{enabled:snapshot.logging.enabled,error:snapshot.logging.error}};
    const url=URL.createObjectURL(new Blob([JSON.stringify(clean,null,2)],{type:'application/json'}));
    const link=document.createElement('a');link.href=url;link.download='vita-tree-diagnostics.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  setInterval(()=>{if(dialog.open)refresh();},3000);
}
