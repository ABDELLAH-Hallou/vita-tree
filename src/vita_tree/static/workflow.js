export const tasks = [
  {id:'extract', title:'Identify job requirements', detail:'Identify the skills and experience the employer wants.', output:'Job requirements'},
  {id:'analyze', title:'Check CV match', detail:'Compare your CV with the job requirements.', output:'CV match analysis'},
  {id:'adapt', title:'Tailor CV', detail:'Tailor the CV to the role and selected language.', output:'Tailored CV and summary'},
  {id:'review', title:'Review CV with AI', detail:'Get feedback on your current CV. When an earlier matching analysis is available, compare the scores.', output:'Feedback and score comparison'},
  {id:'cover', title:'Cover letter', detail:'Write a letter using the current CV and job context. Compiles a PDF before finishing. Adaptation is not required.', output:'Cover letter and PDF'},
  {id:'validating', title:'Final checks', detail:'Check the document files and protect your existing edits. CV PDF previews are created separately.', output:'Application files'},
];
export const statusNames = {pending:'Not started', running:'In progress', succeeded:'Done', failed:'Couldn’t finish', blocked:'Waiting for an earlier step', interrupted:'Stopped before finishing', skipped:'Skipped', unavailable:'Not available', unknown:'No earlier details',review:'Needs your review',previous:'Done earlier'};
export function graphStages(run, options={}, available={}) {
  return tasks.map(task => {
    let stage = run?.stages?.find(item => item.id === task.id);
    if(!stage && run) {
      // Older history has no per-stage evidence. Never invent successful tasks.
      stage = {status: run.step === task.id && run.status === 'running' ? 'running' : 'unknown'};
    }
    if(!stage) stage = {status: ['extract','review','cover'].includes(task.id) && !available[task.id]
      ? 'unavailable' : task.id === 'validating' || options.steps?.includes(task.id) ? 'pending' : 'skipped'};
    return {...task, ...stage};
  });
}
export function renderGraph(container, {run, options, available, selected, select, history=[], config={}}) {
  const stages = graphStages(run, options, available).map(task=>{
    if(run?.factualReview?.state==='pending'&&run.factualReview.step===task.id||task.id==='extract'&&run?.requirementsApprovalNeeded)return {...task,status:'review'};
    if(task.status==='skipped'){
      const prior=history.find(item=>item.id!==run?.id&&(!run||item.createdAt<run.createdAt)&&item.stages?.some(stage=>stage.id===task.id&&stage.status==='succeeded'));
      if(prior)return {...task,status:'previous',previousRun:prior.id};
    }
    return task;
  });
  // Keep keyboard focus stable while a poll updates status text.
  const focused = container.contains(document.activeElement) ? document.activeElement.dataset.step : null;
  container.replaceChildren();
  for(const [index, task] of stages.entries()) {
    if(index) {
      const edge = document.createElement('span'); edge.className='dag-edge'; edge.setAttribute('aria-hidden','true');
      edge.dataset.status=stages[index-1].status; edge.textContent='→'; container.append(edge);
    }
    const button = document.createElement('button'); button.type='button'; button.className='dag-node';
    button.dataset.step=task.id; button.dataset.status=task.status;
    button.setAttribute('aria-pressed',String(selected === task.id));
    if(task.id!=='validating'){
      button.setAttribute('aria-haspopup','dialog');
      button.title=run?'View the AI settings captured for this step':'Configure the AI for this step';
    }
    button.setAttribute('aria-label',`${task.title}: ${statusNames[task.status] || task.status}. ${task.detail}`);
    const icon=document.createElementNS('http://www.w3.org/2000/svg','svg');icon.classList.add('dag-symbol');icon.setAttribute('viewBox','0 0 24 24');icon.setAttribute('aria-hidden','true');
    const shape=document.createElementNS('http://www.w3.org/2000/svg','path');
    shape.setAttribute('d',['succeeded','previous'].includes(task.status)?'m5 12 4 4L19 6':['failed','interrupted'].includes(task.status)?'M12 5v9m0 4v.1':['skipped','unavailable','blocked'].includes(task.status)?'M6 12h12':'M21 12a9 9 0 1 1-9-9 9 9 0 0 1 9 9');icon.append(shape);
    const title=document.createElement('strong'); title.textContent=task.title;
    const state=document.createElement('span'); state.className='dag-status'; state.textContent=(statusNames[task.status] || task.status)+(task.reusedFrom?' · reused':'');
    if(run?.factualReview?.step===task.id)state.textContent=({pending:'Needs factual review',resolved:'Factual decisions saved',unavailable:'Review unavailable'}[run.factualReview.state]||'Review unavailable');
    if(task.id==='extract'&&run?.requirementsApprovalNeeded)state.textContent='Needs requirements review';
    if(['analyze','adapt','review','cover'].includes(task.id)&&task.status==='succeeded'&&run?.requirementsStatus&&run.requirementsStatus!=='current')state.textContent+=' · requirements changed';
    const time=document.createElement('span'); time.className='dag-time';
    if(task.startedAt&&!task.finishedAt&&task.status==='running')time.dataset.startedAt=task.startedAt;
    time.textContent=task.startedAt ? `${Math.max(0,Math.floor((task.finishedAt || Date.now()/1000)-task.startedAt))}s` : task.output;
    if(task.previousRun){time.textContent='Earlier preparation · not rerun';button.title='Completed in an earlier preparation. This is history, not a claim that its artifacts match current inputs.';}button.append(icon,title,state,time); button.onclick=()=>select(task); container.append(button);
    if(run?.requirementsRevision&&task.id!=='validating'){
      const revision=document.createElement('span');revision.className='dag-requirements';revision.textContent='Requirements '+run.requirementsRevision.slice(0,12);revision.title=run.requirementsRevision;button.append(revision);
    }
    if(config[task.id]) {
      const route=config[task.id], model=document.createElement('span');model.className='dag-model';
      model.textContent=route.model||route.provider+' default';model.title=`${route.provider} · ${route.reasoning||'Automatic reasoning'}`;button.append(model);
    }
  }
  if(focused) container.querySelector(`[data-step="${focused}"]`)?.focus({preventScroll:true});
}
