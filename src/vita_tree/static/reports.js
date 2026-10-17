// A deliberately small Markdown reader. All untrusted content becomes text;
// raw HTML, images, and executable URLs are never inserted into the document.
function inline(parent, value) {
  const tokens = /(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^\s)]+\))/g;
  let end=0;
  for(const match of value.matchAll(tokens)) {
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
  const lines=content.replace(/\r\n/g,'\n').split('\n');
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
      const row=(text,tag)=>{const tr=document.createElement('tr'); for(const value of cells(text)){const cell=document.createElement(tag);if(tag==='th')cell.scope='col';inline(cell,value.trim());tr.append(cell);}return tr;};
      const head=document.createElement('thead');head.append(row(line,'th'));table.append(head);i++;
      const body=document.createElement('tbody');
      while(i+1<lines.length && lines[i+1].includes('|') && lines[i+1].trim()) body.append(row(lines[++i],'td'));
      table.append(body);wrapper.append(table);article.append(wrapper);continue;
    }
    const heading=line.match(/^(#{1,6})\s+(.+)/);
    if(heading) {const h=document.createElement('h'+Math.min(heading[1].length+2,6));inline(h,heading[2]);article.append(h);continue;}
    if(/^\s*([-*]|\d+\.)\s+/.test(line)) {
      const ordered=/^\s*\d+\./.test(line), list=document.createElement(ordered?'ol':'ul');
      do {const li=document.createElement('li');inline(li,lines[i].replace(/^\s*([-*]|\d+\.)\s+/,''));list.append(li);i++;}
      while(i<lines.length && (ordered?/^\s*\d+\.\s+/:/^\s*[-*]\s+/).test(lines[i]));
      i--;article.append(list);continue;
    }
    if(/^\s*([-*_])\1{2,}\s*$/.test(line)){article.append(document.createElement('hr'));continue;}
    const paragraph=document.createElement(line.startsWith('> ')?'blockquote':'p');inline(paragraph,line.replace(/^> /,''));article.append(paragraph);
  }
  return article;
}
export function reportDetails(path,content,{open=false,label=path}={}) {
  const item=document.createElement('details');item.open=open;item.dataset.path=path;
  const summary=document.createElement('summary');summary.textContent=label;
  item.append(summary);
  if(path.endsWith('.md')) item.append(markdown(content));
  else {const pre=document.createElement('pre');pre.textContent=content;item.append(pre);}
  return item;
}
