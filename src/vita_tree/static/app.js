const state = { branches: [], query: "", source: "", cleanText: "", view: "clean", deepLinkOpened: false };

const elements = {
  repository: document.querySelector("#repository"),
  total: document.querySelector("#total-count"),
  recent: document.querySelector("#recent-count"),
  search: document.querySelector("#search"),
  refresh: document.querySelector("#refresh"),
  list: document.querySelector("#branch-list"),
  resultCount: document.querySelector("#result-count"),
  template: document.querySelector("#branch-template"),
  modal: document.querySelector("#source-modal"),
  modalBranch: document.querySelector("#modal-branch"),
  modalCommit: document.querySelector("#modal-commit"),
  sourceState: document.querySelector("#source-state"),
  sourceCode: document.querySelector("#source-view code"),
  cleanDocument: document.querySelector(".clean-document"),
  viewOptions: document.querySelectorAll(".view-option"),
  copySource: document.querySelector("#copy-source"),
  closeModal: document.querySelector("#close-modal"),
};

function relativeTime(timestamp) {
  const seconds = Math.max(0, Math.floor(Date.now() / 1000 - timestamp));
  const units = [
    [31536000, "year"], [2592000, "month"], [604800, "week"],
    [86400, "day"], [3600, "hour"], [60, "minute"], [1, "second"],
  ];
  const [divisor, label] = units.find(([value]) => seconds >= value) || units.at(-1);
  const amount = Math.floor(seconds / divisor);
  return `${amount} ${label}${amount === 1 ? "" : "s"} ago`;
}

function absoluteTime(isoDate) {
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric", month: "short", day: "2-digit",
    hour: "2-digit", minute: "2-digit",
  }).format(new Date(isoDate));
}

function badge(text, className = "") {
  const node = document.createElement("span");
  node.className = `badge ${className}`.trim();
  node.textContent = text;
  return node;
}

function commandArguments(source, command) {
  const results = [];
  const token = `\\${command}`;
  let cursor = 0;
  while ((cursor = source.indexOf(token, cursor)) !== -1) {
    let start = cursor + token.length;
    while (/\s/.test(source[start] || "")) start += 1;
    if (source[start] !== "{") { cursor = start; continue; }
    let depth = 0;
    for (let end = start; end < source.length; end += 1) {
      if (source[end] === "{" && source[end - 1] !== "\\") depth += 1;
      if (source[end] === "}" && source[end - 1] !== "\\") depth -= 1;
      if (depth === 0) {
        results.push(source.slice(start + 1, end));
        cursor = end + 1;
        break;
      }
    }
  }
  return results;
}

function stripComment(line) {
  for (let index = 0; index < line.length; index += 1) {
    if (line[index] === "%" && line[index - 1] !== "\\") return line.slice(0, index);
  }
  return line;
}

function cleanInline(value) {
  let text = value;
  const protectedChars = new Map([
    ["\\&", "\uE000"], ["\\%", "\uE001"], ["\\_", "\uE002"],
    ["\\#", "\uE003"], ["\\$", "\uE004"], ["\\{", "\uE005"], ["\\}", "\uE006"],
  ]);
  protectedChars.forEach((placeholder, latex) => { text = text.split(latex).join(placeholder); });
  text = text.replace(/\\href\{[^{}]*\}\{([^{}]*)\}/g, "$1");
  text = text.replace(/\\url\{([^{}]*)\}/g, "$1");
  for (let pass = 0; pass < 5; pass += 1) {
    text = text.replace(/\\(?:textbf|textit|emph|textrm|texttt)\s*\{([^{}]*)\}/g, "$1");
    text = text.replace(/\{\\(?:bf|it|large|small)\s+([^{}]*)\}/g, "$1");
  }
  text = text.replace(/\\hfill/g, "  —  ");
  text = text.replace(/\\\\(?:\[[^\]]*\])?/g, "\n");
  text = text.replace(/\$([^$]*)\$/g, "$1");
  text = text.replace(/\\(?:large|small|bf|it)\b/g, "");
  text = text.replace(/\\[A-Za-z@]+\*?(?:\[[^\]]*\])?/g, "");
  text = text.replace(/[{}]/g, "");
  text = text.replace(/\s*&\s*/g, "  —  ");
  text = text.replace(/~/g, " ");
  const restored = ["&", "%", "_", "#", "$", "{", "}"];
  restored.forEach((char, index) => { text = text.split(String.fromCharCode(0xE000 + index)).join(char); });
  return text.split("\n").map((part) => part.replace(/[ \t]+/g, " ").trim()).filter(Boolean);
}

function cleanLatex(source) {
  const blocks = [];
  const name = commandArguments(source, "name")[0];
  if (name) blocks.push({ type: "name", text: cleanInline(name).join(" ") });
  commandArguments(source, "address").forEach((address) => {
    cleanInline(address).forEach((line) => blocks.push({ type: "contact", text: line }));
  });

  const documentBody = source.split("\\begin{document}")[1]?.split("\\end{document}")[0] || source;
  let centered = false;
  for (const rawLine of documentBody.split(/\r?\n/)) {
    let line = stripComment(rawLine).trim();
    if (!line) continue;
    const section = line.match(/^\\begin\{rSection\}\{(.+)\}$/);
    if (section) {
      blocks.push({ type: "section", text: cleanInline(section[1]).join(" ") });
      continue;
    }
    if (/^\\begin\{center\}/.test(line)) { centered = true; continue; }
    if (/^\\end\{center\}/.test(line)) { centered = false; continue; }
    if (/^\\(?:begin|end)\{/.test(line) || /^\\(?:itemsep|setlength|vspace|pagebreak)/.test(line)) continue;

    const isBullet = /^\\item(?:\s|$)/.test(line);
    line = line.replace(/^\\item\s*/, "");
    const parts = cleanInline(line);
    parts.forEach((text, index) => blocks.push({
      type: isBullet && index === 0 ? "bullet" : (centered ? "lead" : "line"),
      text,
    }));
  }

  const plainText = blocks.map((block) => {
    if (block.type === "section") return `\n${block.text.toUpperCase()}\n`;
    if (block.type === "bullet") return `• ${block.text}`;
    return block.text;
  }).join("\n").replace(/\n{3,}/g, "\n\n").trim();
  return { blocks, plainText };
}

function renderCleanDocument(source) {
  const clean = cleanLatex(source);
  elements.cleanDocument.replaceChildren();
  clean.blocks.forEach((block) => {
    const node = document.createElement(block.type === "section" ? "h3" : block.type === "name" ? "h1" : "p");
    node.className = `clean-${block.type}`;
    node.textContent = block.text;
    elements.cleanDocument.append(node);
  });
  return clean.plainText;
}

function setPreviewView(view) {
  state.view = view;
  elements.modal.dataset.view = view;
  elements.viewOptions.forEach((button) => button.classList.toggle("active", button.dataset.view === view));
}

async function openBranchSource(branch) {
  setPreviewView("clean");
  elements.modal.classList.remove("loaded");
  elements.sourceState.classList.remove("error");
  elements.sourceState.textContent = "READING SOURCE…";
  elements.sourceCode.textContent = "";
  elements.modalBranch.textContent = branch.name;
  elements.modalCommit.textContent = branch.commit;
  elements.copySource.textContent = "COPY";
  elements.modal.showModal();

  try {
    const query = new URLSearchParams({ branch: branch.name });
    const response = await fetch(`/api/branch-content?${query}`, { cache: "no-store" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Unable to read main.tex");
    state.source = data.content;
    state.cleanText = renderCleanDocument(data.content);
    elements.sourceCode.textContent = data.content;
    elements.modalCommit.textContent = `${data.commit} · ${absoluteTime(data.modifiedAt)}`;
    elements.modal.classList.add("loaded");
  } catch (error) {
    elements.sourceState.classList.add("error");
    elements.sourceState.textContent = error.message;
  }
}

function render() {
  const query = state.query.trim().toLocaleLowerCase();
  const visible = state.branches.filter((branch) =>
    `${branch.name} ${branch.subject} ${branch.author}`.toLocaleLowerCase().includes(query),
  );

  elements.list.replaceChildren();
  visible.forEach((branch, index) => {
    const row = elements.template.content.firstElementChild.cloneNode(true);
    row.style.animationDelay = `${Math.min(index * 18, 220)}ms`;
    row.classList.toggle("current", branch.current);
    const branchName = row.querySelector(".branch-name");
    branchName.textContent = branch.name;
    branchName.addEventListener("click", () => openBranchSource(branch));
    row.querySelector(".subject").textContent = branch.subject || "No commit message";
    row.querySelector(".sha").textContent = branch.commit;
    row.querySelector(".author").textContent = branch.author;

    const badges = row.querySelector(".badges");
    if (branch.current) badges.append(badge("CURRENT", "current"));
    if (!branch.local) badges.append(badge(branch.remote || "REMOTE"));

    const time = row.querySelector("time");
    time.dateTime = branch.modifiedAt;
    time.append(document.createTextNode(relativeTime(branch.timestamp)));
    const exact = document.createElement("small");
    exact.textContent = absoluteTime(branch.modifiedAt);
    time.append(exact);
    elements.list.append(row);
  });

  if (!visible.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = state.branches.length ? "NO BRANCHES MATCH YOUR FILTER" : "NO BRANCHES FOUND";
    elements.list.append(empty);
  }

  elements.resultCount.textContent = query
    ? `${visible.length} OF ${state.branches.length} BRANCHES`
    : `${visible.length} BRANCH${visible.length === 1 ? "" : "ES"} SHOWN`;
}

async function loadBranches() {
  elements.refresh.classList.add("loading");
  elements.refresh.disabled = true;
  try {
    const response = await fetch("/api/branches", { cache: "no-store" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Unable to read branches");
    state.branches = data.branches;
    elements.repository.textContent = data.detached
      ? `${data.repository} / DETACHED HEAD`
      : `${data.repository} / ${data.currentBranch}`;
    elements.total.textContent = data.branches.length.toString().padStart(2, "0");
    const weekAgo = Date.now() / 1000 - 7 * 24 * 60 * 60;
    elements.recent.textContent = data.branches.filter((branch) => branch.timestamp >= weekAgo).length.toString().padStart(2, "0");
    render();
    const previewBranch = new URLSearchParams(window.location.search).get("branch");
    if (previewBranch && !state.deepLinkOpened) {
      const branch = state.branches.find((item) => item.name === previewBranch);
      if (branch) {
        state.deepLinkOpened = true;
        openBranchSource(branch);
      }
    }
  } catch (error) {
    elements.list.innerHTML = `<div class="empty error"></div>`;
    elements.list.firstElementChild.textContent = error.message;
    elements.resultCount.textContent = "FAILED TO LOAD";
  } finally {
    elements.refresh.classList.remove("loading");
    elements.refresh.disabled = false;
  }
}

elements.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  render();
});
elements.refresh.addEventListener("click", loadBranches);
elements.closeModal.addEventListener("click", () => elements.modal.close());
elements.viewOptions.forEach((button) => button.addEventListener("click", () => setPreviewView(button.dataset.view)));
elements.modal.addEventListener("click", (event) => {
  if (event.target === elements.modal) elements.modal.close();
});
elements.copySource.addEventListener("click", async () => {
  if (!elements.modal.classList.contains("loaded")) return;
  await navigator.clipboard.writeText(state.view === "clean" ? state.cleanText : state.source);
  elements.copySource.textContent = "COPIED";
  setTimeout(() => { elements.copySource.textContent = "COPY"; }, 1400);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "/" && document.activeElement !== elements.search) {
    event.preventDefault();
    elements.search.focus();
  }
});

loadBranches();
