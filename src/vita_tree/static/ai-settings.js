const steps = [['extract','Identify job requirements'],['analyze','Check CV match'],['adapt','Tailor CV'],['review','Review CV with AI'],['cover','Cover letter']];
const effortNames = {none:'None',minimal:'Minimal',low:'Low · faster',medium:'Medium · balanced',high:'High · more thinking',xhigh:'Extra high',max:'Maximum',ultra:'Ultra'};
const copy = value => structuredClone(value);

export function createAIConfiguration(container, {api, onChange}) {
  const drafts = new Map();
  let branch, catalog, connections=[], settings, disabled=true, saving=false, dirty=false, connectionTarget=null, stepEditor=null, checkTarget=null, checking=false;
  const dialogs=document.createElement('div');dialogs.className='ai-dialogs';document.body.append(dialogs);
  const $ = selector => container.querySelector(selector)||dialogs.querySelector(selector);
  container.innerHTML=`
    <section class="ai-shared" aria-labelledby="shared-ai-title">
      <div class="ai-setup-heading"><div><h3 id="shared-ai-title">Shared AI setup</h3><p class="helper">Set up once. Every step uses this unless you customize it below.</p></div><span class="pill accent">Default for all steps</span></div>
      <div id="shared-ai-fields"></div>
    </section>
    <details id="ai-advanced" class="ai-advanced"><summary><span>Advanced · customize individual steps</span><span id="override-count" class="pill">All use shared setup</span></summary>
      <p class="helper">Use a faster model for job requirements and a different model for writing, for example. Custom steps keep their own setup when the shared setup changes.</p>
      <div id="ai-step-settings"></div><button id="reset-ai-steps" class="quiet" type="button">Use shared setup for every step</button>
    </details>
    <div class="ai-save-bar"><button id="save-ai-setup" type="button">Save AI setup</button><span id="ai-setup-status" class="helper" role="status">Choices are saved locally. API keys last for this server session.</span></div>
    <p id="ai-setup-error" class="ai-setup-error" role="alert" hidden></p>
    <dialog id="step-ai-dialog" class="ai-settings-dialog" aria-labelledby="step-ai-title" aria-describedby="step-ai-description"><form id="step-ai-form">
      <div class="ai-dialog-body">
      <div class="dialog-heading"><div><span id="step-ai-context" class="pill accent"></span><h2 id="step-ai-title"></h2><button id="step-requirements" type="button" hidden>View job requirements</button><button id="inspect-step-dialog" type="button" hidden>Inspect this step’s execution</button></div><button id="close-step-ai" class="quiet" type="button" aria-label="Close step settings">×</button></div>
      <p id="step-ai-description" class="helper"></p>
      <fieldset id="step-ai-mode" class="step-ai-mode"><legend>AI setup for this step</legend>
        <label><input type="radio" name="step-ai-mode" id="step-ai-shared" value="shared"><span><strong>Use shared setup</strong><small>Follow the shared provider, model, reasoning, and connection.</small></span></label>
        <label><input type="radio" name="step-ai-mode" id="step-ai-custom" value="custom"><span><strong>Customize this step</strong><small>Choose a separate setup for this component.</small></span></label>
      </fieldset>
      <div id="step-ai-fields"></div>
      <p id="step-ai-save-hint" class="helper">Apply saves your current AI setup on this computer. Only this step’s override is changed. API keys last for this server session.</p>
      </div>
      <div class="ai-dialog-footer">
      <p id="step-ai-error" role="alert" class="ai-setup-error" hidden></p>
      <div class="dialog-footer"><button id="step-ai-cancel" type="button">Cancel</button><button id="step-ai-next" type="button" hidden>Configure next run</button><button id="step-ai-apply" class="primary" type="submit">Apply to step</button></div>
      </div>
    </form></dialog>
    <dialog id="generation-check-dialog" class="ai-settings-dialog" aria-labelledby="generation-check-title"><form id="generation-check-form">
      <div class="ai-dialog-body">
      <div class="dialog-heading"><h2 id="generation-check-title">Check model generation</h2><button id="close-generation-check" class="quiet" type="button" aria-label="Close generation check">×</button></div>
      <p id="generation-check-route" class="helper"></p>
      <p>This sends a small synthetic prompt to the selected provider and model and <strong>may consume paid usage</strong>, including provider retries. It sends no CV or job description. A successful model listing does not prove generation access.</p>
      <p class="helper">This checks the setup shown here without applying or saving edits. Success confirms generation access at this time, not CV quality.</p>
      <p id="generation-check-result" class="provider-failure" role="status" aria-live="polite"></p>
      </div>
      <div class="ai-dialog-footer">
      <div class="dialog-footer"><button id="cancel-generation-check" type="button">Cancel</button><button id="confirm-generation-check" class="primary" type="submit">Run generation check · may use credits</button></div>
      </div>
    </form></dialog>
    <dialog id="connection-dialog" class="ai-settings-dialog" aria-labelledby="connection-title"><form id="connection-form">
      <div class="ai-dialog-body">
      <div class="dialog-heading"><h2 id="connection-title">Add API connection</h2><button id="close-connection" class="quiet" type="button" aria-label="Close API connection">×</button></div>
      <p id="connection-service" class="helper"></p>
      <label>Connection name<input id="connection-name" maxlength="80" placeholder="e.g. Personal account" autocomplete="off" required></label>
      <label>API key<input id="connection-key" type="password" maxlength="4096" autocomplete="off" spellcheck="false" required></label>
      <label class="show-key"><input id="show-connection-key" type="checkbox">Show API key</label>
      <p class="helper">Get an API key from this provider’s account dashboard. The key stays in this local server’s memory and is never saved in Git, browser storage, or run history. Add it again after restarting the server.</p>
      </div>
      <div class="ai-dialog-footer">
      <p id="connection-error" role="alert" class="ai-setup-error" hidden></p>
      <div class="dialog-footer"><button id="cancel-connection" type="button">Cancel</button><button id="add-connection" class="primary" type="submit">Add connection</button></div>
      </div>
    </form></dialog>`;
  // Keep modal dialogs visible from every workspace tab, including the CV view.
  dialogs.append($('#step-ai-dialog'),$('#connection-dialog'),$('#generation-check-dialog'));

  const routeFor = step => step==='default'?settings.default:settings.steps[step]||settings.default;
  const providerFor = route => catalog?.providers.find(p=>p.id===route.provider);
  function summary(route) {
    if(!route)return '';
    return `${providerFor(route)?.name||route.provider} · ${route.model||'Provider default'} · ${route.reasoning?effortNames[route.reasoning]||route.reasoning:'Automatic reasoning'}`;
  }
  function connectionName(route) {
    if(route.connectionName)return route.connectionName;
    if(!route.connection)return route.provider==='codex'?'Local Codex login':'Existing local credentials';
    return connections.find(c=>c.id===route.connection&&c.provider===route.provider)?.name||'Connection expired · add it again';
  }
  function changed() {
    dirty=true; drafts.set(branch,{settings:copy(settings),dirty});
    $('#ai-setup-status').textContent='Unsaved setup · used immediately for new runs. Save to keep it after reload.';
    $('#ai-setup-error').hidden=true;
    updateSummaries(); onChange();
  }
  function updateSummaries() {
    if(!settings)return;
    const count=Object.keys(settings.steps).length;
    $('#override-count').textContent=count?`${count} custom ${count===1?'step':'steps'}`:'All use shared setup';
    $('#reset-ai-steps').disabled=disabled||!count;
    for(const [step] of steps) {
      const info=$(`[data-ai-summary="${step}"]`);
      if(info)info.textContent=`${settings.steps[step]?'Custom':'Shared'} · ${summary(routeFor(step))}`;
      const badge=document.querySelector(`#step-${step}`)?.closest('label')?.querySelector('.step-ai-summary');
      if(badge)badge.textContent=`${settings.steps[step]?'Custom':'Shared'} · ${routeFor(step).model||providerFor(routeFor(step))?.name||routeFor(step).provider}`;
    }
  }
  function makeFields(step, editor=null) {
    const route=editor?editor.route:routeFor(step), shared=step==='default', prefix=editor?'popup-':shared?'':step+'-';
    const locked=disabled||!!editor?.readOnly||!!editor?.saving||(!!editor&&!editor.custom);
    const notify=()=>editor?updatePopupSummary():changed();
    const repaint=()=>editor?renderPopupFields():replaceFields(step);
    const host=document.createElement('div');host.className='ai-route-fields';
    host.innerHTML=`<div class="ai-controls">
      <label>Provider<select id="${prefix}provider" aria-label="${shared?'Shared':step} provider"></select></label>
      <label>Model ID<input id="${prefix}model" list="${prefix}model-suggestions" maxlength="160" autocomplete="off" spellcheck="false" placeholder="Choose a suggestion or type any model ID" aria-describedby="${prefix}model-help"><datalist id="${prefix}model-suggestions"></datalist></label>
      <label>Reasoning<select id="${prefix}reasoning" aria-describedby="${prefix}reasoning-help"></select></label>
      <label>Connection<select id="${prefix}connection"></select></label>
    </div>
    <p id="${prefix}model-help" class="helper">Choose a suggested model or enter the exact model ID from your provider. Leave empty for its default. Your account must have access.</p>
    <p id="${prefix}reasoning-help" class="helper"></p>
    <div class="connection-actions"><span class="helper" id="${prefix}connection-help"></span><button type="button" data-check-generation>Check generation…</button><button type="button" data-add-key>Add API key…</button><button type="button" data-remove-key class="quiet">Remove connection</button></div>`;
    const field=name=>host.querySelector('#'+prefix+name);
    field('provider').replaceChildren(...catalog.providers.map(p=>new Option(p.name,p.id)));
    field('provider').value=route.provider;
    field('model').value=route.model;
    const suggestions=catalog.options.filter(o=>o.provider===route.provider&&o.supported&&o.model);
    for(const choice of [settings.default,...Object.values(settings.steps)])if(choice.provider===route.provider&&choice.model&&!suggestions.some(o=>o.model===choice.model))suggestions.push({...choice,reasoning:[]});
    field('model-suggestions').replaceChildren(...[...new Set(suggestions.map(o=>o.model))].map(model=>new Option(model,model)));
    const provider=providerFor(route);
    function refreshReasoning(){
      const known=catalog.options.find(o=>o.provider===route.provider&&o.model===route.model);
      const efforts=[...(known?.reasoning?.length?known.reasoning:provider?.reasoning||[])];
      if(editor?.readOnly&&route.reasoning&&!efforts.includes(route.reasoning))efforts.push(route.reasoning);
      if(!efforts.includes(route.reasoning))route.reasoning='';
      field('reasoning').replaceChildren(new Option('Automatic',''),...efforts.map(e=>new Option(effortNames[e]||e,e)));
      field('reasoning').value=route.reasoning;
      field('reasoning').disabled=locked||!efforts.length;
    }
    refreshReasoning();
    field('reasoning-help').textContent=route.provider==='codex'?(catalog.reasoningBridge?'For custom model IDs, check which reasoning levels that model accepts. Higher levels may take longer.':'Custom reasoning needs the Vita CV source connection. Automatic is available.'):'Vita CV currently uses automatic reasoning for this provider.';
    field('connection').replaceChildren(new Option(route.provider==='codex'?'Local Codex login':'Existing local credentials',''),...connections.filter(c=>c.provider===route.provider).map(c=>new Option(c.name,c.id)));
    if(route.connection&&!connections.some(c=>c.id===route.connection&&c.provider===route.provider))field('connection').add(new Option(editor?.readOnly&&route.connectionName?route.connectionName:'Connection expired · add it again',route.connection));
    field('connection').value=route.connection||'';
    field('connection-help').textContent=route.connection?`${connectionName(route)} · session only; key access is checked when a step runs.`:route.provider==='codex'?'Uses the Codex CLI account already signed in on this computer.':`Uses ${provider?.keyVariable||'the provider API key'} from your local environment or .vita/.env. Or add a key here.`;
    host.querySelector('[data-add-key]').hidden=route.provider==='codex'||!!editor?.readOnly;
    host.querySelector('[data-remove-key]').hidden=!!editor||!route.connection||!connections.some(c=>c.id===route.connection);
    for(const element of host.querySelectorAll('input,select,button'))if(locked)element.disabled=true;
    // Checking an inherited route does not edit it or create an override.
    host.querySelector('[data-check-generation]').disabled=disabled||!!editor?.readOnly||!!editor?.saving;
    field('provider').onchange=()=>{
      const p=field('provider').value;
      const suggestion=catalog.options.find(o=>o.provider===p&&o.supported);
      Object.assign(route,{provider:p,model:suggestion?.model||'',reasoning:'',connection:''});
      repaint(); notify();
    };
    field('model').oninput=()=>{route.model=field('model').value;notify();};
    field('model').onchange=()=>{route.model=route.model.trim();field('model').value=route.model;refreshReasoning();notify();};
    field('reasoning').onchange=()=>{route.reasoning=field('reasoning').value;notify();};
    field('connection').onchange=()=>{route.connection=field('connection').value;repaint();notify();};
    host.querySelector('[data-check-generation]').onclick=()=>{
      const issue=routeProblem(route,'Generation check');
      if(issue){if(editor){$('#step-ai-error').textContent=issue;$('#step-ai-error').hidden=false;}else showError(issue);return;}
      const captured=copy(settings);
      if(editor&&!editor.custom)delete captured.steps[step];
      if(step==='default')captured.steps={};else if(!editor||editor.custom)captured.steps[step]=copy(route);
      checkTarget={branch,step:step==='default'?'analyze':step,settings:captured};
      $('#generation-check-route').textContent=`${editor&&!editor.custom||step==='default'||!settings.steps[step]&&!editor?'Shared setup':'Step setup'} · ${summary(route)} · ${connectionName(route)}`;
      $('#generation-check-result').textContent='No request has been sent.';$('#cancel-generation-check').textContent='Cancel';
      $('#confirm-generation-check').disabled=false;$('#cancel-generation-check').disabled=false;
      $('#generation-check-dialog').showModal();
    };
    host.querySelector('[data-add-key]').onclick=()=>{
      connectionTarget={route,step,branch,editor,repaint,notify};$('#connection-service').textContent=`${provider?.name} · reusable by any step with this provider`;
      $('#connection-name').value=`${provider?.name} account`;$('#connection-key').value='';$('#connection-key').type='password';$('#show-connection-key').checked=false;$('#connection-error').hidden=true;$('#connection-dialog').showModal();
    };
    host.querySelector('[data-remove-key]').onclick=async()=>{
      try{connections=(await api('/api/connections/remove',{id:route.connection})).connections;render();changed();}
      catch(error){showError(error.message);}
    };
    return host;
  }
  function replaceFields(step) {
    const host=step==='default'?$('#shared-ai-fields'):$(`[data-ai-fields="${step}"]`);
    host.replaceChildren(makeFields(step));
  }
  function showError(message){$('#ai-setup-error').textContent=message;$('#ai-setup-error').hidden=false;}
  function render() {
    if(!settings)return;
    const expanded=new Set([...container.querySelectorAll('.ai-step-setting[open]')].map(row=>row.querySelector('[data-ai-summary]').dataset.aiSummary));
    replaceFields('default');$('#ai-step-settings').replaceChildren();
    for(const [step,title] of steps) {
      const row=document.createElement('details');row.className='ai-step-setting';
      row.open=expanded.has(step);
      row.innerHTML=`<summary><strong></strong><span data-ai-summary="${step}" class="helper"></span></summary><label class="ai-override-toggle"><input type="checkbox" id="${step}-custom-ai">Use custom AI setup for this step</label><div data-ai-fields="${step}"></div>`;
      row.querySelector('strong').textContent=title;
      const toggle=row.querySelector('input');toggle.checked=!!settings.steps[step];toggle.disabled=disabled;
      const fields=row.querySelector('[data-ai-fields]');fields.hidden=!toggle.checked;
      if(toggle.checked)fields.append(makeFields(step));
      toggle.onchange=()=>{
        if(toggle.checked)settings.steps[step]=copy(settings.default);else delete settings.steps[step];
        fields.hidden=!toggle.checked;fields.replaceChildren();if(toggle.checked)fields.append(makeFields(step));changed();
      };
      $('#ai-step-settings').append(row);
    }
    $('#save-ai-setup').disabled=disabled||saving;
    updateSummaries();
    if(stepEditor)renderPopupFields();
  }
  function routeProblem(route, name) {
    if(!providerFor(route))return `${name}: choose a supported provider.`;
    if(route.model.length>160||(route.model&&!/^[a-zA-Z0-9][a-zA-Z0-9_./:@+-]*$/.test(route.model)))return `${name}: enter an exact model ID without spaces.`;
    if(route.connection&&!connections.some(c=>c.id===route.connection&&c.provider===route.provider))return `${name}: add or select a connection again; the previous session connection expired.`;
    return '';
  }
  function problem(selected=steps.map(([step])=>step)) {
    if(!settings)return 'AI setup is loading.';
    for(const step of selected.filter(id=>id!=='validating')) {
      const route=routeFor(step), name=steps.find(([id])=>id===step)?.[1]||step;
      const issue=routeProblem(route,name);if(issue)return issue;
    }
    return '';
  }
  $('#save-ai-setup').onclick=async()=>{
    const target=branch, captured=copy(settings), issue=problem();if(issue){showError(issue);return;}
    saving=true;$('#save-ai-setup').disabled=true;
    try {
      await api('/api/ai-settings',{branch:target,settings:captured});
      const current=drafts.get(target);
      if(current&&JSON.stringify(current.settings)===JSON.stringify(captured))current.dirty=false;
      if(branch===target&&JSON.stringify(settings)===JSON.stringify(captured)){
        dirty=false;$('#ai-setup-status').textContent='Setup saved on this computer · API keys last until the server stops.';
      }
    }catch(error){if(branch===target)showError(error.message);}
    finally{saving=false;$('#save-ai-setup').disabled=disabled;}
  };
  $('#reset-ai-steps').onclick=()=>{settings.steps={};render();changed();};
  function updatePopupSummary(){
    if(!stepEditor)return;
    $('#step-ai-error').hidden=true;
    $('#step-ai-context').textContent=stepEditor.readOnly?(stepEditor.history?'Recorded run · view only':'View only'):stepEditor.custom?'Custom setup for this step':'Following shared setup';
  }
  function renderPopupFields(){
    const editor=stepEditor;if(!editor)return;
    $('#step-ai-fields').replaceChildren();
    if(editor.route)$('#step-ai-fields').append(makeFields(editor.step,editor));
    $('#step-ai-shared').checked=!editor.custom;$('#step-ai-custom').checked=editor.custom;
    $('#step-ai-mode').hidden=editor.readOnly;
    $('#step-ai-mode').disabled=disabled||editor.readOnly||!!editor.saving;
    $('#step-ai-apply').hidden=editor.readOnly;
    $('#step-ai-apply').disabled=disabled||!!editor.saving;
    $('#step-ai-apply').textContent=editor.saving?'Applying…':'Apply to step';
    $('#step-ai-cancel').textContent=editor.readOnly?'Close':'Cancel';
    $('#step-ai-next').hidden=!editor.readOnly||!editor.allowNext;
    $('#step-ai-next').disabled=disabled;
    $('#step-ai-save-hint').hidden=editor.readOnly;
    $('#close-step-ai').disabled=!!editor.saving;$('#step-ai-cancel').disabled=!!editor.saving;
    updatePopupSummary();
  }
  function openStep(step, options={}){
    const title=steps.find(([id])=>id===step)?.[1];if(!settings||!title)return;
    const history=!!options.history, readOnly=history||disabled||!!options.readOnly;
    const route=history?options.recorded:routeFor(step);
    stepEditor={step,branch,route:route?copy(route):null,custom:!!settings.steps[step],readOnly,history,allowNext:!!options.allowNext,saving:false};
    $('#step-requirements').hidden=step!=='extract';
    $('#step-ai-title').textContent=title;
    $('#step-ai-description').textContent=readOnly?(route?'These are the settings captured for this run. Editing the next run does not change these results.':'This older run did not record an AI setup. Configure the next run to choose its settings.'):'Choose the AI for this component. Changes are applied only after you select Apply to step.';
    renderPopupFields();
    if(!$('#step-ai-dialog').open)$('#step-ai-dialog').showModal();
  }
  function closeStep(){
    if(stepEditor?.saving)return;
    const step=stepEditor?.step;$('#step-ai-dialog').close();stepEditor=null;
    queueMicrotask(()=>document.querySelector(`.dag-node[data-step="${step}"]`)?.focus({preventScroll:true}));
  }
  $('#close-step-ai').onclick=closeStep;$('#step-ai-cancel').onclick=closeStep;
  $('#step-ai-dialog').addEventListener('cancel',event=>{event.preventDefault();closeStep();});
  $('#step-ai-next').onclick=()=>openStep(stepEditor.step);
  for(const mode of ['shared','custom'])$('#step-ai-'+mode).onchange=()=>{
    if(!stepEditor||stepEditor.readOnly||disabled)return;
    if(mode==='shared'&&stepEditor.custom)stepEditor.customDraft=copy(stepEditor.route);
    stepEditor.custom=mode==='custom';
    stepEditor.route=copy(mode==='custom'?(stepEditor.customDraft||routeFor(stepEditor.step)):settings.default);
    renderPopupFields();
  };
  $('#step-ai-form').onsubmit=async event=>{
    event.preventDefault();const editor=stepEditor;
    if(!editor||editor.readOnly||editor.saving||disabled)return;
    const route=editor.custom?editor.route:settings.default;
    const issue=routeProblem(route,'This step');
    if(issue){$('#step-ai-error').textContent=issue;$('#step-ai-error').hidden=false;return;}
    const captured=copy(settings), target=branch;
    if(editor.custom)captured.steps[editor.step]=copy(editor.route);else delete captured.steps[editor.step];
    editor.saving=true;renderPopupFields();
    try{
      await api('/api/ai-settings',{branch:target,settings:captured});
      if(branch!==target||stepEditor!==editor)return;
      settings=captured;dirty=false;drafts.set(branch,{settings:copy(settings),dirty});
      $('#ai-setup-status').textContent='Setup saved on this computer · API keys last until the server stops.';
      editor.saving=false;closeStep();render();onChange();
    }catch(error){if(stepEditor===editor){editor.saving=false;renderPopupFields();$('#step-ai-error').textContent=error.message;$('#step-ai-error').hidden=false;}}
  };
  function closeCheck(){if(checking)return;$('#generation-check-dialog').close();checkTarget=null;}
  $('#close-generation-check').onclick=closeCheck;$('#cancel-generation-check').onclick=closeCheck;
  $('#generation-check-dialog').addEventListener('cancel',event=>{event.preventDefault();closeCheck();});
  $('#generation-check-form').onsubmit=async event=>{
    event.preventDefault();if(checking||!checkTarget)return;
    const target=checkTarget;checking=true;
    for(const id of ['confirm-generation-check','cancel-generation-check','close-generation-check'])$('#'+id).disabled=true;
    $('#generation-check-result').textContent='Checking generation access… The provider may retry temporary failures.';
    try{
      const result=await api('/api/generation-check',{branch:target.branch,step:target.step,aiConfig:target.settings,confirmed:true});
      const route=`${result.provider||'Effective provider unreported'} / ${result.model||'effective model unreported'}`;
      const failure=result.failure;
      $('#generation-check-result').textContent=result.generationVerified
        ? `Generation succeeded · ${route} · ${result.attempts??'unknown'} provider attempts. This does not evaluate CV quality.`
        : `${failure?.title||'Generation was not verified'}${failure?.category?' ('+failure.category.replaceAll('_',' ')+')':''} · ${route} · ${result.attempts??'unknown'} provider attempts. ${failure?.retryable===true?'Retryable. ':failure?.retryable===false?'Needs attention before retry. ':''}${failure?.action||'Inspect the Vita CV connection.'}`;
    }catch(error){$('#generation-check-result').textContent=error.message;}
    finally{checking=false;for(const id of ['confirm-generation-check','cancel-generation-check','close-generation-check'])$('#'+id).disabled=false;$('#cancel-generation-check').textContent='Close';}
  };
  function closeConnection(){if($('#add-connection').disabled)return;$('#connection-dialog').close();$('#connection-key').value='';$('#connection-key').type='password';}
  $('#cancel-connection').onclick=closeConnection;$('#close-connection').onclick=closeConnection;
  $('#connection-dialog').addEventListener('cancel',event=>{event.preventDefault();closeConnection();});
  $('#show-connection-key').onchange=()=>{$('#connection-key').type=$('#show-connection-key').checked?'text':'password';};
  $('#connection-form').onsubmit=async event=>{
    event.preventDefault();if(disabled)return;
    const selection=connectionTarget, route=selection.route, target=selection.branch;
    const payload={name:$('#connection-name').value,provider:route.provider,apiKey:$('#connection-key').value};
    $('#add-connection').disabled=true;$('#connection-error').hidden=true;
    try {
      const connection=await api('/api/connections',payload);connections.push(connection);
      if(branch===target&&(selection.editor?selection.editor===stepEditor:route===routeFor(selection.step))){route.connection=connection.id;selection.repaint();selection.notify();}
      $('#connection-dialog').close();$('#connection-key').value='';$('#connection-key').type='password';
    } catch(error){$('#connection-error').textContent=error.message;$('#connection-error').hidden=false;}
    finally{payload.apiKey='';$('#add-connection').disabled=false;}
  };
  return {
    load(name, nextCatalog, saved, available) {
      if(stepEditor){$('#step-ai-dialog').close();stepEditor=null;}
      branch=name;catalog=nextCatalog;connections=available.connections;
      const draft=drafts.get(name);settings=copy(draft?.settings||saved);dirty=!!draft?.dirty;
      drafts.set(name,{settings:copy(settings),dirty});disabled=false;render();
      $('#ai-setup-status').textContent=dirty?'Unsaved AI setup · save to keep it after reload.':'Choices are saved locally. API keys last for this server session.';
      $('#ai-setup-error').hidden=true;
    },
    setDisabled(value){if(value!==disabled){disabled=value;render();}},
    value(){return copy(settings);},
    route(step){return routeFor(step);},
    summary, connectionName, problem,
    refresh(){updateSummaries();},
    openStep,
  };
}
