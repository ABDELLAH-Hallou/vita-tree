const $ = selector => document.querySelector(selector);
const text = (tag, value, className) => {const el=document.createElement(tag);el.textContent=value;if(className)el.className=className;return el;};

export function createFactualReview({api, getState, changed, notice}) {
  const panel=$('#factual-review-panel'), form=$('#factual-review-form'), items=$('#factual-review-items');
  let review=null, submitting=false, generation=0;
  function close(){if(submitting)return;generation++;review=null;items.replaceChildren();form.reset();panel.hidden=true;$('#review-facts').focus({preventScroll:true});}
  $('#cancel-factual-review').onclick=close;
  async function open(run){
    const state=getState();
    if(state.dirty||state.jobDirty){notice('Save your CV and job description drafts before reviewing factual changes.',true);return;}
    const snapshot=state.snapshot;
    const request=++generation;
    const result=await api('/api/factual-review?id='+encodeURIComponent(run.id));
    if(getState().snapshot!==snapshot||request!==generation)return;
    review=result;items.replaceChildren();form.reset();$('#factual-review-error').textContent='';
    const resolved=result.state==='resolved';
    $('#factual-review-title').textContent=resolved?'Your factual decisions':'Review factual changes';
    $('#factual-review-summary').textContent=`${result.step==='adapt'?'Tailored CV':'Cover letter'} · ${result.items.length} changes · ${result.target}. `+(resolved?'Decisions are saved in the preparation draft. Retry with matching inputs to continue.':'Your application is unchanged. Check each interpretation against your source, then accept, reject, or edit it.');
    $('#factual-review-revision').textContent=result.revision;
    $('#factual-review-confirmation').hidden=resolved;$('#apply-factual-review').hidden=resolved;
    for(const [index,item] of result.items.entries()){
      const card=document.createElement('fieldset');card.className='factual-change';card.dataset.changeId=item.id;
      card.append(text('legend',`${index+1}. ${item.reason.replaceAll('_',' ')}`));
      card.append(text('p',`${item.kind.replaceAll('_',' ')} · ${item.verification.replaceAll('_',' ')}`,'helper'));
      card.append(text('p',item.output_span?`Proposed location: ${result.target} · lines ${item.output_span.line_start}–${item.output_span.line_end}`:'Deletion from the source locations below.','helper'));
      card.append(text('p',item.unresolvedMeaning,'factual-meaning'));
      const location=document.createElement('div');location.className='factual-sources';
      if(!item.sources.length)location.append(text('p','No supporting source location. This is an unsupported insertion.'));
      for(const source of item.sources){
        const details=document.createElement('details');details.append(text('summary',`${source.path} · lines ${source.line_start}–${source.line_end}`),text('pre',source.quote));location.append(details);
      }
      card.append(location);
      const wording=document.createElement('div');wording.className='factual-wording';
      for(const [label,value] of [['Original wording',item.original],['Proposed wording',item.proposed]]){
        const section=document.createElement('div');section.append(text('h3',label),text('pre',value||'(no text)'));wording.append(section);
      }
      card.append(wording);
      if(resolved){
        const decision=result.provenance?.decisions.find(choice=>choice.id===item.id);
        card.append(text('p',`Decision: ${decision?.action||'unknown'}`));
        if(decision?.action==='edit')card.append(text('pre',decision.text));
      }else{
        const options=document.createElement('div');options.className='factual-options';
        const edit=document.createElement('textarea');edit.id='fact-edit-'+index;edit.value=item.proposed;edit.hidden=true;edit.setAttribute('aria-label',`Edited wording for change ${index+1}`);
        for(const [value,label] of [['accept','Accept proposed wording'],['reject','Reject; keep original wording'],['edit','Edit wording']]){
          const wrapper=document.createElement('label'),input=document.createElement('input');input.type='radio';input.name='fact-'+index;input.value=value;input.required=true;
          input.onchange=()=>{edit.hidden=input.value!=='edit';if(input.value==='edit')edit.focus();};wrapper.append(input,document.createTextNode(label));options.append(wrapper);
        }
        card.append(options,edit);
      }
      items.append(card);
    }
    const provenance=$('#factual-provenance');provenance.hidden=!resolved;
    if(resolved)provenance.textContent=`Explicit local-user review · ${new Date(result.provenance.decidedAt*1000).toLocaleString()} · resulting revision ${result.provenance.resolvedRevision}. Original source and proposal retained.`;
    panel.hidden=false;panel.scrollIntoView({block:'start'});$('#factual-review-title').focus({preventScroll:true});
  }
  form.onsubmit=async event=>{
    event.preventDefault();if(submitting||!review)return;
    const state=getState();
    if(state.dirty||state.jobDirty){$('#factual-review-error').textContent='Save your local editor drafts before applying decisions.';return;}
    const decisions=review.items.map((item,index)=>{const action=form.elements['fact-'+index].value;return {id:item.id,action,...(action==='edit'?{text:$('#fact-edit-'+index).value}:{})};});
    submitting=true;$('#apply-factual-review').disabled=true;$('#cancel-factual-review').disabled=true;$('#factual-review-error').textContent='';
    panel.setAttribute('aria-busy','true');$('#factual-review-progress').textContent='Validating your decisions and saving the reviewed draft…';
    try{
      await api('/api/factual-review/apply',{id:review.runId,revision:review.revision,token:review.token,decisions,confirmed:$('#confirm-factual-meaning').checked});
      const runId=review.runId;await changed();await open({id:runId});notice('Decisions saved in the preparation draft. Retry preparation to continue; your application will update after final checks.');
    }catch(error){$('#factual-review-error').textContent=error.message;}
    finally{submitting=false;$('#apply-factual-review').disabled=false;$('#cancel-factual-review').disabled=false;panel.removeAttribute('aria-busy');$('#factual-review-progress').textContent='';}
  };
  return {open,reset(){if(!submitting){generation++;review=null;panel.hidden=true;items.replaceChildren();}}};
}
