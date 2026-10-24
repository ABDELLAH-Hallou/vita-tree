// A deliberately small Markdown reader. All untrusted content becomes text;
// raw HTML, images, and executable URLs are never inserted into the document.
function inline(parent, value, budget) {
  const tokens = /(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^\s)]+\))/g;
  let end=0;
  for(const match of value.matchAll(tokens)) {
    if(budget.remaining--<=0)break;
    parent.append(document.createTextNode(value.slice(end,match.index)));
    const token=match[0]; let element;
    if(token.startsWith('`')) {element=document.createElement('code');element.textContent=token.slice(1,-1);}
    else if(token.startsWith('**')) {element=document.createElement('strong');element.textContent=token.slice(2,-2);}
    else {
      const [,label,url]=token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      element=document.createElement('span'); element.textContent=label;
      if(/^https?:\/\//i.test(url)) {element=document.createElement('a');element.textContent=label;element.href=url;element.target='_blank';element.rel='noopener noreferrer';}
    }
    parent.append(element);end=match.index+token.length;
  }
  parent.append(document.createTextNode(value.slice(end)));
}
export function markdown(content) {
  const article=document.createElement('article'); article.className='report-prose';
  const all=content.slice(0,200000).replace(/\r\n/g,'\n').split('\n');
  const lines=all.slice(0,2000),budget={remaining:4000};
  if(content.length>200000||all.length>2000){const notice=document.createElement('p');notice.textContent='Preview shortened for readability. Open the saved report file for the full text.';article.append(notice);}
  for(let i=0;i<lines.length;i++) {
    const line=lines[i]; if(!line.trim()) continue;
    if(line.startsWith('```')) {
      const pre=document.createElement('pre'), code=document.createElement('code'), body=[];
      while(++i<lines.length && !lines[i].startsWith('```')) body.push(lines[i]);
      code.textContent=body.join('\n'); pre.append(code); article.append(pre); continue;
    }
    if(line.includes('|') && /^\s*\|?\s*:?-{3,}/.test(lines[i+1] || '')) {
      const wrapper=document.createElement('div');wrapper.className='report-table';wrapper.tabIndex=0;wrapper.setAttribute('role','region');wrapper.setAttribute('aria-label','Report table');
      const table=document.createElement('table');
      const cells=text=>text.trim().replace(/^\||\|$/g,'').split('|');
      const row=(text,tag)=>{const tr=document.createElement('tr'); for(const value of cells(text).slice(0,40)){const cell=document.createElement(tag);if(tag==='th')cell.scope='col';inline(cell,value.trim(),budget);tr.append(cell);}return tr;};
      const head=document.createElement('thead');head.append(row(line,'th'));table.append(head);i++;
      const body=document.createElement('tbody');
      while(i+1<lines.length && lines[i+1].includes('|') && lines[i+1].trim()) body.append(row(lines[++i],'td'));
      table.append(body);wrapper.append(table);article.append(wrapper);continue;
    }
    const heading=line.match(/^(#{1,6})\s+(.+)/);
    if(heading) {const h=document.createElement('h'+Math.min(heading[1].length+2,6));inline(h,heading[2],budget);article.append(h);continue;}
    if(/^\s*([-*]|\d+\.)\s+/.test(line)) {
      const ordered=/^\s*\d+\./.test(line), list=document.createElement(ordered?'ol':'ul');
      do {const li=document.createElement('li');inline(li,lines[i].replace(/^\s*([-*]|\d+\.)\s+/,''),budget);list.append(li);i++;}
      while(i<lines.length && (ordered?/^\s*\d+\.\s+/:/^\s*[-*]\s+/).test(lines[i]));
      i--;article.append(list);continue;
    }
    if(/^\s*([-*_])\1{2,}\s*$/.test(line)){article.append(document.createElement('hr'));continue;}
    const paragraph=document.createElement(line.startsWith('> ')?'blockquote':'p');inline(paragraph,line.replace(/^> /,''),budget);article.append(paragraph);
  }
  return article;
}
export function fileLabel(path){
  const name=path.split('/').pop();
  const labels={'analysis.md':'CV match analysis','analyze.md':'CV match analysis','adapt.md':'Tailoring summary','review.md':'AI review','delta.md':'Changes since the previous review','cover.md':'Cover-letter summary','main.tex':'CV source','cover-letter.tex':'Cover-letter source','job.md':'Job description','job.json':'Job requirements · data','job.toon':'Job requirements · data','analysis.json':'CV match scores · data','review.json':'Review scores · data','delta.json':'Score changes · data'};
  return labels[name]||name;
}
export function reportDetails(path,content,{open=false,label=null}={}) {
  const item=document.createElement('details');item.open=open;item.dataset.path=path;
  const summary=document.createElement('summary');summary.textContent=label||fileLabel(path);
  item.append(summary);const details=document.createElement("details");details.className="technical-details";const caption=document.createElement("summary");caption.textContent="File details";const code=document.createElement("code");code.textContent=path;details.append(caption,code);item.append(details);
  if(path.endsWith('.md')) item.append(markdown(content));
  else {const pre=document.createElement('pre');pre.textContent=content;item.append(pre);}
  return item;
}
