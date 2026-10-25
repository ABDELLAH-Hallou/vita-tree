import {EditorState, Compartment} from '@codemirror/state';
import {EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter, drawSelection} from '@codemirror/view';
import {defaultKeymap, history, historyKeymap, redo} from '@codemirror/commands';
import {StreamLanguage, syntaxHighlighting, HighlightStyle, bracketMatching, syntaxTree} from '@codemirror/language';
import {stex} from '@codemirror/legacy-modes/mode/stex';
import {searchKeymap, highlightSelectionMatches} from '@codemirror/search';
import {linter, lintGutter, lintKeymap, openLintPanel} from '@codemirror/lint';
import {tags, highlightTree} from '@lezer/highlight';

const highlighting = HighlightStyle.define([
  {tag: [tags.tagName, tags.keyword, tags.standard(tags.variableName)], class: 'tex-command'},
  {tag: [tags.atom, tags.string], class: 'tex-argument'},
  {tag: tags.comment, class: 'tex-comment'},
  {tag: [tags.bracket, tags.punctuation], class: 'tex-bracket'},
  {tag: [tags.number, tags.operator], class: 'tex-math'},
]);

// Static snippets share the editor's real TeX tokenizer, without one editor per change.
export function renderLatexSnippet(host, value, changedFrom=0, changedTo=0) {
  const state=EditorState.create({doc:value,extensions:[StreamLanguage.define(stex)]});
  const tokens=[];highlightTree(syntaxTree(state),highlighting,(from,to,classes)=>tokens.push({from,to,classes}));
  const cuts=[...new Set([0,value.length,changedFrom,changedTo,...tokens.flatMap(t=>[t.from,t.to])])].sort((a,b)=>a-b);
  host.replaceChildren();
  for(let i=0;i<cuts.length-1;i++){
    const from=cuts[i],to=cuts[i+1];if(from===to)continue;
    const span=document.createElement(from>=changedFrom&&to<=changedTo?'mark':'span');
    span.textContent=value.slice(from,to);span.className=tokens.find(t=>t.from<=from&&t.to>=to)?.classes||'';host.append(span);
  }
}

export function createLatexEditor(host, {label, readOnly = false, onChange, lint}) {
  const mount = document.createElement('div');
  mount.className = 'code-mount';
  const footer = document.createElement('div');
  footer.className = 'code-footer';
  const status = document.createElement('button');
  status.type = 'button'; status.className = 'lint-status'; status.disabled = true;
  status.textContent = 'Syntax check pending';
  const position = document.createElement('span');
  footer.append(status, position); host.replaceChildren(mount, footer);
  const access = new Compartment();
  let locked = readOnly, branchKey, request, epoch = 0;
  function setStatus(message, issues = false) {
    status.textContent = message; status.disabled = !issues;
    status.classList.toggle('has-issues', issues);
  }
  const extensions = () => [
    lineNumbers(), history(), drawSelection(), bracketMatching(),
    highlightActiveLine(), highlightActiveLineGutter(), highlightSelectionMatches(),
    StreamLanguage.define(stex), syntaxHighlighting(highlighting),
    keymap.of([{key: 'Mod-Shift-z', run: redo, preventDefault: true}, ...defaultKeymap, ...historyKeymap, ...searchKeymap, ...lintKeymap]),
    access.of([EditorState.readOnly.of(locked), EditorView.contentAttributes.of({'aria-readonly': String(locked)})]),
    EditorView.contentAttributes.of({'aria-label': label, spellcheck: 'false'}),
    EditorView.theme({
      '&': {height: '100%', color: 'var(--ink)', backgroundColor: 'var(--panel)'},
      '.cm-scroller': {overflow: 'auto', fontFamily: 'var(--mono)', fontSize: '12px', lineHeight: '1.8'},
      '.cm-content': {padding: '16px 0', caretColor: 'var(--ink)'},
      '.cm-line': {padding: '0 12px'},
      '.cm-gutters': {backgroundColor: 'var(--bg)', color: 'var(--muted)', borderColor: 'var(--line)'},
      '.cm-activeLine, .cm-activeLineGutter': {backgroundColor: 'var(--surface)'},
      '.cm-cursor': {borderLeftColor: 'var(--ink)'},
      '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': {backgroundColor: 'var(--code-selection)'},
      '.cm-matchingBracket': {backgroundColor: 'var(--accent-light)', outline: '1px solid var(--accent)'},
      '.cm-panels, .cm-tooltip': {backgroundColor: 'var(--panel)', color: 'var(--ink)', borderColor: 'var(--border)'},
      '.cm-textfield, .cm-button': {background: 'var(--surface)', color: 'var(--ink)', border: '1px solid var(--border)'},
      '.cm-panel.cm-panel-lint ul [aria-selected]': {backgroundColor: 'var(--accent-light)'},
      '.cm-panel.cm-panel-lint ul:focus [aria-selected]': {backgroundColor: 'var(--accent-light)', color: 'var(--ink)'},
    }),
    lintGutter(),
    linter(async editor => {
      request?.abort(); request = new AbortController();
      const controller = request, doc = editor.state.doc, generation = epoch;
      setStatus('Checking syntax…');
      try {
        const result = await lint(doc.toString(), controller.signal);
        if (controller.signal.aborted || epoch !== generation || editor.state.doc !== doc) return [];
        const diagnostics = result.diagnostics;
        setStatus(diagnostics.length ? 'Syntax issue · show details' : 'No syntax issues', diagnostics.length > 0);
        status.title = 'Syntax only. Compile the PDF to check packages, macros, and layout.';
        return diagnostics;
      } catch (error) {
        if (!controller.signal.aborted && epoch === generation && editor.state.doc === doc) {
          setStatus('Syntax check unavailable'); status.title = error.message;
        }
        return [];
      }
    }, {delay: 500}),
    EditorView.updateListener.of(update => {
      const cursor = update.state.selection.main.head, line = update.state.doc.lineAt(cursor);
      position.textContent = `Ln ${line.number}, Col ${cursor - line.from + 1}`;
      if (update.docChanged) {setStatus('Syntax check pending'); onChange?.(update.state.doc.toString());}
    }),
  ];
  const view = new EditorView({parent: mount, state: EditorState.create({extensions: extensions()})});
  status.onclick = () => openLintPanel(view);
  position.textContent = 'Ln 1, Col 1';
  return {
    get value() {return view.state.doc.toString();},
    setDocument(text, key) {
      if (key === branchKey && text === this.value) return;
      branchKey = key; epoch++; request?.abort();
      view.setState(EditorState.create({doc: text, extensions: extensions()}));
      position.textContent = 'Ln 1, Col 1'; setStatus('Syntax check pending');
    },
    setReadOnly(value) {
      locked = value;
      view.dispatch({effects: access.reconfigure([EditorState.readOnly.of(value), EditorView.contentAttributes.of({'aria-readonly': String(value)})])});
    },
    refresh() {view.requestMeasure();},
    destroy() {request?.abort();view.destroy();},
  };
}
