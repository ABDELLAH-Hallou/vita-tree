import {renderWorkflowGraph} from '../components/renderers';
export const tasks = [
  {id:'extract', title:'Identify job requirements', detail:'Identify the skills and experience the employer wants.', output:'Job requirements'},
  {id:'analyze', title:'Check CV match', detail:'Compare your CV with the job requirements.', output:'CV match analysis'},
  {id:'adapt', title:'Tailor CV', detail:'Tailor the CV to the role and selected language.', output:'Tailored CV and summary'},
  {id:'review', title:'Review CV with AI', detail:'Get feedback on your current CV. When an earlier matching analysis is available, compare the scores.', output:'Feedback and score comparison'},
  {id:'cover', title:'Cover letter', detail:'Write a letter using the current CV and job context. Compiles a PDF before finishing. Adaptation is not required.', output:'Cover letter and PDF'},
  {id:'validating', title:'Final checks', detail:'Check the document files and protect your existing edits. CV PDF previews are created separately.', output:'Application files'},
];
export const statusNames = {pending:'Not started', running:'In progress', succeeded:'Done', failed:'Couldn’t finish', blocked:'Waiting for an earlier step', interrupted:'Stopped before finishing', skipped:'Skipped', unavailable:'Not available', unknown:'No earlier details',review:'Needs your review',previous:'Earlier run only'};
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
  renderWorkflowGraph(container,{stages,run,selected,select,config,statusNames});
  if(focused) container.querySelector(`[data-step="${focused}"]`)?.focus({preventScroll:true});
}
