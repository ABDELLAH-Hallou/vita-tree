"""Synthetic, explicitly approved canonical jobs; never calls a provider."""
from vita_tree import requirements_review as review

JD = '''# Marketing operations
## Required
- HubSpot experience is required.
## Preferred
- 6sense is a significant plus.
## Must-Have or Strong Plus
- Experience with AI workflows.
## Employment conditions
- If working remotely, reliable internet is required.
'''


def proposal(raw):
    items=[]
    if raw == JD:
        specs=[(3,'hubspot','required','capability'),(5,'6sense','preferred','capability'),
               (7,'ai','required','capability'),(9,'internet','required','employment_condition')]
    else:
        specs=[(1,'engineering','unclear','capability')]
    for line,key,classification,kind in specs:
        quote=raw.splitlines()[line-1]
        items.append(dict(job_id='job-1',key=key,text=quote,kind=kind,category='hard_skills',
                          classification=classification,ambiguity='',source_refs=[dict(job_id='job-1',line_start=line,line_end=line,quote=quote)]))
    return dict(schema_version=1,items=items)


def compile_definition(raw):
    from vita.helpers.requirements import compile_revision
    return compile_revision(proposal(raw),raw)


def seed(workspace, branch, approved=True, raw=None):
    context=review.context_for(workspace,branch)
    data=compile_definition(context['job'] if raw is None else raw)
    store,approval,marker=review.paths(workspace,context)
    review.retain(store,data)
    if approved:
        data=review.backend(workspace,dict(action='approve',definition=data,source=context['job']))
        review.write(approval,dict(schema_version=1,source_sha256=data['source_sha256'],revision=data['revision']))
    else:
        review.write(marker,dict(state='pending',revision=data['revision'],originBranch=branch,parentRevision=None))
    return data
