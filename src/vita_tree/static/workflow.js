export const tasks = [
  {id:'extract', title:'Extract', detail:'Turn the job description into reusable requirements.', output:'job.json + job.toon'},
  {id:'analyze', title:'Analyze', detail:'Find the evidence and gaps in your original CV.', output:'analysis.md'},
  {id:'adapt', title:'Adapt', detail:'Tailor the CV to the role and selected language.', output:'main.tex + adapt.md'},
  {id:'review', title:'AI review', detail:'Evaluate the current CV. A matching analysis enables a before/after score comparison; otherwise this is a standalone evaluation.', output:'review.md · delta when comparable'},
  {id:'cover', title:'Cover letter', detail:'Write a letter using the current CV and job context. Compiles a PDF before finishing. Adaptation is not required.', output:'cover-letter.tex + PDF'},
  {id:'validating', title:'Validate', detail:'Check LaTeX structure and file conflicts before applying results. PDF compilation is separate.', output:'Branch files'},
];
export const statusNames = {pending:'Not started', running:'Running', succeeded:'Done', failed:'Failed', blocked:'Blocked', interrupted:'Interrupted', skipped:'Skipped', unavailable:'Unavailable', unknown:'Not recorded'};
const symbols = {pending:'○', running:'◉', succeeded:'✓', failed:'!', blocked:'−', interrupted:'!', skipped:'−', unavailable:'−', unknown:'?'};
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
export function renderGraph(container, {run, options, available, selected, select}) {
  const stages = graphStages(run, options, available);
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
    button.setAttribute('aria-label',`${task.title}: ${statusNames[task.status] || task.status}. ${task.detail}`);
    const icon=document.createElement('span'); icon.className='dag-symbol'; icon.textContent=symbols[task.status] || '?'; icon.setAttribute('aria-hidden','true');
    const title=document.createElement('strong'); title.textContent=task.title;
    const state=document.createElement('span'); state.className='dag-status'; state.textContent=statusNames[task.status] || task.status;
    const time=document.createElement('span'); time.className='dag-time';
    if(task.startedAt&&!task.finishedAt&&task.status==='running')time.dataset.startedAt=task.startedAt;
    time.textContent=task.startedAt ? `${Math.max(0,Math.floor((task.finishedAt || Date.now()/1000)-task.startedAt))}s` : task.output;
    button.append(icon,title,state,time); button.onclick=()=>select(task); container.append(button);
  }
  if(focused) container.querySelector(`[data-step="${focused}"]`)?.focus({preventScroll:true});
}
