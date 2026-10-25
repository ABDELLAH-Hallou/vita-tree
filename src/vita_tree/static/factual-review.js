import {createLatexEditor,renderLatexSnippet} from './vendor/editor.mjs';
const $ = selector => document.querySelector(selector);
const reasons={ambiguous_acronym:'Check this abbreviation',date_interpretation:'Check these dates',credential_status:'Check this qualification',metric_or_unit:'Check this number',unverified_semantic_change:'Check the meaning',formatting_semantics_unverified:'Check the formatting',whitespace_only:'Spacing update'};
const text = (tag, value, className) => {const el=document.createElement(tag);el.textContent=value;if(className)el.className=className;return el;};

export function createFactualReview({api, getState, changed, continued, notice}) {
  const panel=$('#factual-review-panel'), form=$('#factual-review-form'), items=$('#factual-review-items');
  let review=null, submitting=false, generation=0, sourceEditor=null;
  function lock(value){for(const element of panel.querySelectorAll('button,input,textarea'))element.disabled=value;}
  function close(){if(submitting)return;generation++;review=null;sourceEditor?.destroy();sourceEditor=null;items.replaceChildren();form.reset();panel.close();panel.hidden=true;$('#review-facts').focus({preventScroll:true});}
  $('#cancel-factual-review').onclick=close;$('#close-factual-review').onclick=close;panel.oncancel=event=>{event.preventDefault();close();};
  function count(){const chosen=items.querySelectorAll('input:checked').length;$('#factual-choice-count').textContent=`${chosen} of ${review?.items.length||0} decisions ready`; }
  for(const [id,action] of [['accept-all-facts','accept'],['reject-all-facts','reject']])$('#'+id).onclick=()=>{if(submitting)return;for(const input of items.querySelectorAll(`input[value=${action}]`)){input.checked=true;input.dispatchEvent(new Event('change'));}count();};
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
    $('#factual-review-summary').textContent=`${result.step==='adapt'?'Tailored CV':'Cover letter'} · ${result.items.length} changes · ${result.target}. `+(resolved?'Decisions are saved. Continue to finish preparing your application.':'Your application is unchanged. Check each interpretation against your source, then accept, reject, or edit it.');
    $('#factual-review-revision').textContent=result.revision;
    $('#factual-review-confirmation').hidden=resolved;$('#confirm-factual-meaning').required=!resolved;$('#apply-factual-review').hidden=false;$('#apply-factual-review').textContent=resolved?'Continue preparation':'Approve & continue';$('#factual-bulk').hidden=resolved;
    for(const [index,item] of result.items.entries()){
      const card=document.createElement('fieldset');card.className='factual-change';card.dataset.changeId=item.id;
      card.append(text('legend',`${index+1}. ${reasons[item.reason]||'Check this change'}`));
      const category=document.createElement('details');category.append(text('summary','Change details'),text('p',`${item.kind.replaceAll('_',' ')} · ${item.verification.replaceAll('_',' ')}`,'helper'));card.append(category);
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
        const section=document.createElement('div');section.className=label.startsWith('Original')?'wording-before':'wording-after';const code=text('pre','');let start=0,end=0;const a=item.original||'',b=item.proposed||'';while(start<Math.min(a.length,b.length)&&a[start]===b[start])start++;while(end<Math.min(a.length,b.length)-start&&a[a.length-1-end]===b[b.length-1-end])end++;renderLatexSnippet(code,value||'(no text)',start,Math.max(start,(value||'').length-end));section.append(text('h3',label),code);wording.append(section);
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
          input.onchange=()=>{edit.hidden=input.value!=='edit';if(input.value==='edit')edit.focus();count();};wrapper.append(input,document.createTextNode(label));options.append(wrapper);
        }
        card.append(options,edit);
      }
      items.append(card);
    }
    const provenance=$('#factual-provenance');provenance.hidden=!resolved;
    if(resolved)provenance.textContent=`${result.provenance.method==='automatic_run_policy'?'Automatic approval · selected for this run':'Explicit local-user review'} · ${new Date(result.provenance.decidedAt*1000).toLocaleString()} · resulting revision ${result.provenance.resolvedRevision}. Original source and proposal retained.`;
    sourceEditor?.destroy();sourceEditor=createLatexEditor($('#factual-source-preview'),{label:'Full proposed LaTeX',readOnly:true,lint:(content)=>api('/api/lint',{content})});sourceEditor.setDocument(result.proposed||'',result.revision);count();panel.hidden=false;if(!panel.open)panel.showModal();$('#factual-review-title').focus({preventScroll:true});
  }
  form.onsubmit=async event=>{
    event.preventDefault();if(submitting||!review)return;
    const state=getState();
    if(state.dirty||state.jobDirty){$('#factual-review-error').textContent='Save your local editor drafts before applying decisions.';return;}
    const decisions=review.state==='resolved'?[]:review.items.map((item,index)=>{const action=form.elements['fact-'+index].value;return {id:item.id,action,...(action==='edit'?{text:$('#fact-edit-'+index).value}:{})};});
    submitting=true;lock(true);$('#factual-review-error').textContent='';
    panel.setAttribute('aria-busy','true');$('#factual-review-progress').textContent='Validating your decisions and saving the reviewed draft…';
    try{
      if(review.state!=='resolved')await api('/api/factual-review/apply',{id:review.runId,revision:review.revision,token:review.token,decisions,confirmed:$('#confirm-factual-meaning').checked});
      review.state='resolved';$('#confirm-factual-meaning').required=false;$('#apply-factual-review').textContent='Continue preparation';await continued(review.runId,state.snapshot.branch);submitting=false;close();
    }catch(error){$('#factual-review-error').textContent=error.message;}
    finally{submitting=false;lock(false);panel.removeAttribute('aria-busy');$('#factual-review-progress').textContent='';}
  };
  return {open,reset(){if(!submitting){generation++;review=null;sourceEditor?.destroy();sourceEditor=null;panel.close();panel.hidden=true;items.replaceChildren();}}};
}
