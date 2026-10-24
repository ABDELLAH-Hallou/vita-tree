const $=selector=>document.querySelector(selector);
const node=(tag,value)=>{const el=document.createElement(tag);el.textContent=value;return el;};
const categories=['hard_skills','soft_skills','experience','responsibilities','employment_condition'];

export function createRequirements({api,getState,changed,notice}){
  const dialog=document.createElement('dialog');dialog.id='requirements-dialog';dialog.setAttribute('aria-labelledby','requirements-title');
  dialog.innerHTML=`<div class="dialog-heading"><h2 id="requirements-title">Job requirements</h2><button id="requirements-close" aria-label="Close job requirements">×</button></div>
    <p id="requirements-status" role="status"></p><p class="helper">One shared definition for this job description. Required, preferred, and unclear capabilities are assessed separately from employment conditions. Explicit source wording determines classification; conflicting headings stay unclear.</p>
    <details><summary>Exact revision and origin</summary><p id="requirements-origin"></p><code id="requirements-revision"></code><p id="requirements-current"></p></details>
    <div class="requirements-layout"><section aria-label="Requirements definition"><div id="requirements-items"></div><button id="requirement-add">Add requirement</button></section><section class="requirements-source"><h3>Job description source</h3><div id="requirements-source" aria-label="Line-numbered job description"></div></section></div>
    <p id="requirements-error" role="alert" class="error"></p><label id="requirements-confirm-label"><input type="checkbox" id="requirements-confirm"> I reviewed this exact revision, its sources, and unclear classifications.</label>
    <div class="dialog-footer"><button id="requirements-current-button" hidden>Open current definition</button><button id="requirements-cancel">Close without changes</button><button id="requirements-save">Save new draft revision</button><button id="requirements-approve" class="primary">Approve revision</button></div>`;
  document.body.append(dialog);
  let review,branch,rows=[],busy=false,dirty=false,request=0;
  const error=message=>$('#requirements-error').textContent=message;
  function setDirty(){dirty=true;$('#requirements-confirm').checked=false;$('#requirements-approve').disabled=true;$('#requirements-status').textContent='Unsaved corrections. Save a new draft revision before approving.';}
  function close(){if(busy)return;request++;dialog.close();review=null;}
  $('#requirements-close').onclick=close;$('#requirements-cancel').onclick=close;
  dialog.oncancel=event=>{event.preventDefault();close();};
  function field(card,label,value,change,options){
    const wrapper=node('label',label),input=document.createElement(options?'select':'textarea');
    input.setAttribute('aria-label',label);
    if(options)for(const option of options)input.add(new Option(option.replaceAll('_',' '),option));
    input.value=value;input.disabled=review.readOnly;input.oninput=()=>{change(input.value);setDirty();};wrapper.append(input);card.append(wrapper);return input;
  }
  function source(ref){
    for(const el of $('#requirements-source').children)el.classList.toggle('source-selected',Number(el.dataset.line)>=ref.line_start&&Number(el.dataset.line)<=ref.line_end);
    const line=$(`#requirements-source [data-line="${ref.line_start}"]`);line?.scrollIntoView({block:'center'});line?.focus({preventScroll:true});
  }
  function renderRows(){
    const area=$('#requirements-items');area.replaceChildren();
    for(const [key,title] of [['capabilities','Capabilities'],['conditions','Employment conditions · not scored']]){
      area.append(node('h3',title));
      for(const item of rows.filter(item=>(item.category==='employment_condition')===(key==='conditions'))){
        const card=document.createElement('fieldset');card.className='requirement-card';card.append(node('legend',item.id?item.id.slice(0,16):'New capability'));
        field(card,'Criterion',item.criterion,value=>item.criterion=value);
        if(!item.id)field(card,'Job ID',item.job_id,value=>item.job_id=value);
        field(card,'Classification',item.classification,value=>item.classification=value,['required','preferred','unclear']);
        const category=field(card,'Category',item.category,value=>{item.category=value;renderRows();},categories);
        category.setAttribute('aria-label','Requirement category');
        field(card,'Unresolved meaning / ambiguity',item.ambiguity,value=>item.ambiguity=value);
        card.append(node('p',`Job: ${item.job_id} · Revision weight: ${item.weight??'assigned by Vita CV on save'}`));
        for(const [index,ref] of item.source_refs.entries()){
          const button=node('button',`View source · ${ref.job_id} · lines ${ref.line_start}–${ref.line_end}`);button.type='button';button.onclick=()=>source(ref);card.append(button);
          const details=document.createElement('details');details.append(node('summary','Correct source reference'));
          field(details,'Source job ID',ref.job_id,value=>ref.job_id=value);
          for(const [name,label] of [['line_start','First line'],['line_end','Last line']]){
            const input=field(details,label,String(ref[name]),value=>ref[name]=Number(value));input.rows=1;
          }
          field(details,'Exact source quote',ref.quote,value=>ref.quote=value);
          if(!review.readOnly&&item.source_refs.length>1){const remove=node('button','Remove reference');remove.onclick=()=>{item.source_refs.splice(index,1);setDirty();renderRows();};details.append(remove);}
          card.append(details);
        }
        if(!review.readOnly){
          const add=node('button','Add source reference');add.onclick=()=>{item.source_refs.push({job_id:item.job_id,line_start:1,line_end:1,quote:''});setDirty();renderRows();};
          const remove=node('button','Remove requirement');remove.onclick=()=>{rows.splice(rows.indexOf(item),1);setDirty();renderRows();};card.append(add,remove);
        }
        area.append(card);
      }
    }
  }
  function render(data){
    review=data;dirty=false;rows=structuredClone([...(data.definition?.requirements||[]),...(data.definition?.employment_conditions||[])]);
    $('#requirements-confirm').checked=false;error('');
    $('#requirements-status').textContent=data.readOnly?'Captured definition for this run · view only':data.available===false?'Connect Vita CV 2.8 or later to review canonical job requirements.':data.state==='approved'?'Approved definition · edits create a new revision and invalidate dependent assessments.':data.definition?'Review required · dependent steps are paused.':'No canonical definition yet. Run Extract to create one.';
    $('#requirements-revision').textContent=data.definition?.revision||'Not recorded';
    $('#requirements-origin').textContent=data.originBranch?`Shared from application ${data.originBranch}${data.parentRevision?' · previous revision '+data.parentRevision:''}`:'Shared Vita CV definition';
    $('#requirements-current').textContent=data.approvedRevision?`Current approved revision: ${data.approvedRevision}${data.readOnly&&data.definition?.revision!==data.approvedRevision?' · This run used an older definition.':''}`:'No approved revision.';
    if(data.readOnly&&data.state==='pending')$('#requirements-current').textContent+=' A corrected definition is awaiting approval. Earlier assessments need to be rerun.';
    $('#requirements-source').replaceChildren(...(data.definition?.source_text||data.source||'').split('\n').map((line,index)=>{const el=node('p',`${index+1}  ${line}`);el.dataset.line=index+1;el.tabIndex=-1;return el;}));
    for(const id of ['requirements-save','requirement-add','requirements-confirm-label','requirements-approve'])$('#'+id).hidden=data.readOnly||!data.definition;
    $('#requirements-approve').disabled=data.state==='approved';
    $('#requirements-current-button').hidden=!data.readOnly;
    renderRows();
  }
  async function open(run=null){
    const state=getState();if(!state.snapshot)return;
    if(state.dirty||state.jobDirty){notice('Save your CV and job description drafts before reviewing requirements.',true);return;}
    branch=state.snapshot.branch;const generation=++request;
    const data=await api('/api/requirements?branch='+encodeURIComponent(branch)+(run?'&runId='+encodeURIComponent(run.id):''));
    if(generation!==request||getState().snapshot?.branch!==branch)return;
    data.readOnly=data.readOnly||!!state.snapshot.running||!state.snapshot.editable;
    render(data);if(!dialog.open)dialog.showModal();
  }
  $('#requirement-add').onclick=()=>{rows.push({job_id:rows[0]?.job_id||'job-1',criterion:'',category:'hard_skills',classification:'unclear',ambiguity:'',source_refs:[{job_id:rows[0]?.job_id||'job-1',line_start:1,line_end:1,quote:''}]});setDirty();renderRows();};
  $('#requirements-current-button').onclick=()=>open().catch(e=>error(e.message));
  async function submit(approve){
    if(busy||review.readOnly)return;
    if(approve&&(dirty||!$('#requirements-confirm').checked)){error('Save corrections, then confirm that you reviewed this revision.');return;}
    busy=true;error('');dialog.setAttribute('aria-busy','true');
    for(const el of dialog.querySelectorAll('button,input,textarea,select'))el.disabled=true;
    try{
      const data=await api('/api/requirements/'+(approve?'approve':'draft'),{branch,token:review.token,revision:review.definition.revision,...(approve?{confirmed:true}:{items:rows})});
      render(data);await changed();
    }catch(e){error(e.message);}
    finally{busy=false;dialog.removeAttribute('aria-busy');for(const el of dialog.querySelectorAll('button,input,textarea,select'))el.disabled=false;$('#requirements-approve').disabled=dirty||review.state==='approved';}
  }
  $('#requirements-save').onclick=()=>submit(false);$('#requirements-approve').onclick=()=>submit(true);
  return {open,reset:close};
}
