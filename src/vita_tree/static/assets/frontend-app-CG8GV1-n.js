import { a as e, n as t, o as n, r, t as i } from "./frontend-workflow-DqtU3Lxp.js";
import { t as a } from "./frontend-client-Cqgf6Pc4.js";
import { i as o, n as s, r as c, t as l } from "./frontend-runs-DVF8sgEZ.js";
import { r as u, t as d } from "./frontend-reports-CzIybQiE.js";
import { t as f } from "./frontend-diagnostics-DPKkcqsI.js";
import { t as p } from "./frontend-ai-settings-R078Tb1d.js";
import { n as m, t as h } from "./frontend-provider-failures-uMyQIdg2.js";
import { t as g } from "./frontend-factual-review-C1JvgUhX.js";
import { t as ee } from "./frontend-jobenu-D3uI5jg7.js";
import { t as te } from "./frontend-requirements-CEEL9r4B.js";
import { t as ne } from "./frontend-preflight-CXA8w4x8.js";
import { createLatexEditor as re } from "/vendor/editor.mjs";
// frontend/src/compat/app.js
var _ = (e) => document.querySelector(e), v = {
	branches: [],
	session: null,
	snapshot: null,
	view: "structure",
	generation: 0,
	pdfs: {},
	pdfGeneration: 0,
	dirty: !1,
	jobDirty: !1,
	leaf: null,
	publishing: !1,
	commitReview: null
}, ie;
async function ae() {
	ie ||= M("/api/session").then((e) => {
		v.session = e;
	}), await ie;
}
var y = ne({
	api: M,
	getState: () => v,
	getBranches: () => v.branches,
	getSteps: () => K().steps
}), b = te({
	api: M,
	getState: () => v,
	changed: () => D.refresh(),
	continued: Ce,
	notice: N
}), x = g({
	api: M,
	getState: () => v,
	changed: () => D.refresh(),
	continued: Ce,
	notice: N
});
v.filter = "all", v.syncedCommits = /* @__PURE__ */ new Map();
var S = (e) => v.branches.find((t) => t.name === e)?.displayName || (v.snapshot?.branch === e ? v.snapshot.displayName : null) || e;
v.workflowChoices = /* @__PURE__ */ new Map();
var C = [
	"extract",
	"analyze",
	"adapt",
	"review",
	"cover"
], oe = ee({
	api: M,
	branches: () => v.branches,
	openBranch: R,
	ready: ae
}), w = (e) => ![
	"extract",
	"review",
	"cover"
].includes(e) || !!v.session?.workflow?.[e];
v.pdfDocument = "cv", v.runs = [], v.reviewSelection = /* @__PURE__ */ new Set(), v.reviewing = !1;
var T = [], E = (e) => v.runs.filter((t) => t.branch === e && !s(t) && !t.reviewed);
function se() {
	let e = v.runs.filter((e) => v.reviewSelection.has(e.branch) && !s(e) && !e.reviewed).length;
	_("#bulk-review").disabled = v.reviewing || !e, _("#bulk-review").textContent = v.reviewing ? "Saving review…" : "Mark selected as reviewed", _("#bulk-review-count").textContent = e ? `${e} ${e === 1 ? "result" : "results"} selected` : "";
	let t = T.filter((e) => v.reviewSelection.has(e)).length, n = _("#select-review-visible");
	n.checked = !!t && t === T.length, n.indeterminate = !!t && t < T.length, n.disabled = v.reviewing || !T.length;
}
_("#select-review-visible").onchange = (e) => {
	for (let t of T) e.target.checked ? v.reviewSelection.add(t) : v.reviewSelection.delete(t);
	F();
}, _("#bulk-review").onclick = async () => {
	let e = v.runs.filter((e) => v.reviewSelection.has(e.branch) && !s(e) && !e.reviewed).map((e) => e.id);
	if (v.reviewing || !e.length) return;
	if (e.length > 500) {
		_("#bulk-review-status").hidden = !1, _("#bulk-review-status").textContent = "Select fewer applications: up to 500 results can be reviewed at once.";
		return;
	}
	v.reviewing = !0, F();
	let t = _("#bulk-review-status");
	t.hidden = !1, t.textContent = `Marking ${e.length} results as reviewed…`;
	try {
		let n = await M("/api/jobs-reviewed", { ids: e }), r = new Set(n.reviewed);
		for (let e of v.runs) r.has(e.id) && (e.reviewed = !0);
		t.textContent = `${n.reviewed.length} ${n.reviewed.length === 1 ? "result" : "results"} marked as reviewed.` + (n.failed.length ? ` ${n.failed.length} could not be saved and remain selected. ${n.failed[0].error} Reference: ${n.requestId}` : ""), await D.refresh();
	} catch (e) {
		t.textContent = e.message;
	} finally {
		v.reviewing = !1, F();
	}
};
var D, ce = /* @__PURE__ */ new Map();
function le() {
	let e = v.snapshot?.branch;
	if (!e || !v.catalog) return;
	let t = _("#language"), n = v.snapshot.running?.language || ce.get(e) || "en", r = [...v.catalog.languages || [{
		code: "en",
		name: "English"
	}]];
	r.some((e) => e.code === n) || r.push({
		code: n,
		name: n
	});
	let i = JSON.stringify([e, r]);
	t.dataset.languages !== i && (t.replaceChildren(...r.map((e) => new Option(e.name, e.code))), t.dataset.languages = i), t.value = n;
}
_("#language").onchange = () => {
	v.snapshot && ce.set(v.snapshot.branch, _("#language").value);
};
var O = Object.fromEntries(["original", "current"].map((e) => [e, re(_(`#${e}-source`), {
	label: e === "original" ? "Before · CV source" : "Current CV source",
	readOnly: !0,
	onChange: (t) => {
		e === "current" && v.snapshot && (v.dirty = t !== z().content, B());
	},
	lint: async (e, t) => a("/api/lint", { content: e }, v.session.token, { signal: t })
})])), k = (e) => String(e ?? "").replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]), A = p(_("#ai-configuration"), {
	api: M,
	onChange: () => {
		v.snapshot && (v.displayedRun?.resumeAvailable || (v.graphRunId = "draft"), q(), J());
	}
});
function j() {
	le(), A.setDisabled(!!v.snapshot?.running || !!v.launching || !v.snapshot?.editable), _("#language").disabled = !!v.snapshot?.running || !!v.launching || !v.snapshot?.editable, _("#model-details").textContent = "Model suggestions come from repository settings and your local Codex catalog. You can enter any model ID your provider accepts.\n\nSetup: install vita-tree[ai] or start with --vita-source pointing to vita-cv. Custom reasoning currently uses the Codex connection.";
}
async function M(e, t) {
	return a(e, t, v.session?.token || "", { fresh: e.startsWith("/api/workspace?") });
}
function N(e = "", t = !1) {
	let n = t && e.includes("\n") || /Cannot parse this LaTeX|Environment .+:|Math is shown as text|use PDF for exact rendering/.test(e);
	_("#message-details").hidden = !n, _("#message-technical").textContent = n ? e : "", _("#notice").textContent = n ? t ? e.startsWith("Cannot parse this LaTeX") ? "The CV has a formatting problem. Open Technical details." : e.split("\n")[0] : "Some formatting may look different here. Use PDF preview to check the final layout." : e, _("#notice").hidden = !e, _("#notice").classList.toggle("error", t);
}
function P(e) {
	_("#toast").textContent = e, _("#toast").hidden = !1, clearTimeout(v.toast), v.toast = setTimeout(() => _("#toast").hidden = !0, 4e3);
}
function ue(e) {
	let t = Math.max(0, Date.now() / 1e3 - e);
	for (let [e, n] of [
		[31536e3, "y"],
		[2592e3, "mo"],
		[86400, "d"],
		[3600, "h"],
		[60, "m"]
	]) if (t >= e) return `${Math.floor(t / e)}${n} ago`;
	return "Just now";
}
function F() {
	let e = _("#search").value.toLowerCase(), t = (e, t) => {
		let n = v.runs.filter((t) => t.branch === e.name), r = n[0];
		return t === "all" || t === "running" && n.some(s) || t === "review" && n.some((e) => e.status === "succeeded" && !e.reviewed) || t === "failed" && r && !U(r) && ["failed", "interrupted"].includes(r.status);
	};
	for (let e of [
		"all",
		"running",
		"review",
		"failed"
	]) _("#filter-" + e).textContent = v.branches.filter((n) => t(n, e)).length;
	let r = v.branches.filter((n) => t(n, v.filter) && `${n.displayName || n.name} ${n.name} ${n.subject} ${n.author}`.toLowerCase().includes(e));
	for (let e of v.reviewSelection) E(e).length || v.reviewSelection.delete(e);
	T = r.filter((e) => E(e.name).length).map((e) => e.name);
	let i = document.activeElement, a = i.closest(".branch-entry")?.dataset.branch, o = i.matches(".select-branch-review"), l = r.map((e) => {
		let t = v.runs.filter((t) => t.branch === e.name), n = t.find(s) || t.find((e) => !e.reviewed) || t[0], r = n && (s(n) || !n.reviewed || ["failed", "interrupted"].includes(n.status));
		return {
			branch: e,
			selected: v.reviewSelection.has(e.name),
			selectable: !v.reviewing && !!E(e.name).length,
			status: r ? U(n) ? "review" : n.status : void 0,
			label: r ? c(n) + (!s(n) && !n.reviewed ? " · To review" : "") : void 0,
			failure: r && !U(n) ? m(n) : void 0
		};
	});
	if (n(_("#branch-list"), {
		rows: l,
		relative: ue,
		empty: v.filter === "review" && !e ? "No completed preparations need review." : "No applications found. Try another filter or create a new application.",
		onOpen: (e) => {
			let t = v.filter === "review" && v.runs.find((t) => t.branch === e && t.status === "succeeded" && !t.reviewed);
			t ? G(t).catch((e) => N(e.message, !0)) : R(e);
		},
		onSelect: (e, t) => {
			t ? v.reviewSelection.add(e) : v.reviewSelection.delete(e), F();
		}
	}), a && !_("#board").hidden && !i.isConnected) {
		let e = [..._("#branch-list").children].find((e) => e.dataset.branch === a)?.querySelector(o ? ".select-branch-review" : ".branch-row");
		(e && !e.disabled ? e : _("#search")).focus({ preventScroll: !0 });
	}
	_("#result-count").textContent = `${r.length} ${r.length === 1 ? "application" : "applications"}`, _("#total-count").textContent = v.branches.length, se();
}
async function I() {
	_("#refresh").disabled = !0, _("#new-branch").disabled = !0;
	try {
		let e = await M("/api/branches");
		v.branches = e.branches, _("#repository").textContent = e.repository, F();
	} catch (e) {
		_("#branch-list").innerHTML = `<p class="empty">${k(e.message)}</p>`;
	} finally {
		_("#refresh").disabled = !1, _("#new-branch").disabled = !v.branches.length;
	}
}
function L() {
	return !(v.dirty || v.jobDirty) || window.confirm("Discard your unsaved editor changes?");
}
async function de(e) {
	try {
		let t = await M("/api/release-worktree", { branch: e });
		t.released ? P("Application closed. You can reopen it at any time.") : t.reason === "locked" && P("Some files are still in use. Your application files are safe.");
	} catch (t) {
		P(`Couldn’t close the application folder for ${S(e)}: ${t.message}`);
	}
}
async function R(t, n = !1) {
	if (!n && !L()) return;
	x.reset(), b.reset();
	let r = v.snapshot?.branch;
	r && r !== t && (v.filePath = null);
	let i = ++v.generation;
	_("#workspace").setAttribute("aria-busy", "true");
	for (let e of document.querySelectorAll("[data-view]")) e.disabled = !0;
	v.pdfGeneration++, v.snapshot = null, v.displayedRun = null, v.graphRunId = null, v.selectedTask = null, _("#task-inspector").hidden = !0, _("#cv-file").disabled = !0, e(_("#workflow-graph")), _("#selected-run").hidden = !0, _("#attempt-history").replaceChildren(), A.setDisabled(!0);
	for (let e of C.map((e) => "step-" + e)) _("#" + e).checked = !1;
	for (let e of [
		"save-source",
		"save-job",
		"run-adapt",
		"run-all",
		"task-run",
		"branch-from",
		"compile",
		"commit-push",
		"view-run",
		"mark-run-reviewed",
		"requirements-current-open",
		"requirements-captured",
		"task-requirements",
		"step-requirements"
	]) _("#" + e).disabled = !0;
	O.current.setReadOnly(!0), _("#job-description").readOnly = !0, _("#board").hidden = !0, _("#workspace").hidden = !1, document.body.classList.add("in-workspace"), _("#branch-title").textContent = S(t), N("Loading the application…");
	try {
		if (r && r !== t && await de(r), i !== v.generation) return;
		let [e, n, a, o] = await Promise.all([
			M("/api/workspace?branch=" + encodeURIComponent(t)),
			M("/api/providers?branch=" + encodeURIComponent(t)),
			M("/api/ai-settings?branch=" + encodeURIComponent(t)),
			M("/api/connections")
		]);
		return i === v.generation ? (v.snapshot = e, v.catalog = n, v.dirty = !1, v.jobDirty = !1, v.pdfs = {}, v.pdfDocument = "cv", _("#pdf-document").value = "cv", v.pdfGeneration++, _("#review-policy").value = e.running?.reviewPolicy || "manual", A.load(t, n, a, o), j(), history.replaceState(null, "", "?branch=" + encodeURIComponent(t)), fe(), V(v.view), v.view !== "structure" && N(), e) : void 0;
	} catch (e) {
		i === v.generation && N(e.message, !0);
	} finally {
		if (i === v.generation) {
			_("#workspace").removeAttribute("aria-busy");
			for (let e of document.querySelectorAll("[data-view]")) e.disabled = !v.snapshot;
		}
	}
}
function fe() {
	let e = v.snapshot, t = z();
	if (pe(), _("#branch-title").textContent = e.displayName || e.branch, _("#workspace-caption").textContent = e.editable ? "Review your CV and results, then save your application." : "This CV is view only. Use it to create a new application before editing.", _("#original-label").textContent = t.originalExists === !1 ? "File absent before" : t.path === e.path ? "" : t.path, _("#current-label").textContent = t.exists === !1 ? "Not in current CV" : t.path === e.path ? e.displayName || e.branch : t.path, _("#version-label").textContent = e.editable && t.exists !== !1 ? "Editable" : "View only", O.original.setDocument(t.original, e.branch + ":" + t.path), O.current.setDocument(t.content, e.branch + ":" + t.path), O.current.setReadOnly(!e.editable || !!e.running || t.exists === !1), he("original", t.originalDocument), he("current", t.document), _("#job-description").value = e.job, _("#job-description").readOnly = !e.editable || !!e.running, _("#job-state").textContent = e.job ? "Saved on this computer" : "No job description yet", _("#save-job").disabled = !e.editable || !!e.running, _("#branch-from").disabled = !!e.running, _("#compile").disabled = !1, _("#ai-dot").textContent = Object.keys(e.artifacts).length ? "•" : "", _("#ai-capability").textContent = v.session.vita ? "Prepare everything or start only the steps you choose. Your existing edits are checked before results are applied. Save any draft edits first." : "The Vita CV connection is not available. Open AI connection details for setup instructions.", _("#run-adapt").disabled = !v.session.vita || !e.editable || !!e.running || !!A.problem(K().steps), _("#ai-status").textContent = e.running?.message || (e.job ? "Ready to prepare this application." : "Add and save a job description first."), _("#application-id").textContent = e.branch, _("#worktree-path").textContent = e.worktree || "An application folder will be created when you save your first draft.", _("#diff").replaceChildren(), !t.diff) _("#diff").textContent = "No changes from the original in this file.";
	else for (let e of t.diff.split("\n")) {
		let t = document.createElement("span");
		t.textContent = e + "\n", e.startsWith("+") && !e.startsWith("+++") ? t.className = "added" : e.startsWith("-") && !e.startsWith("---") && (t.className = "removed"), _("#diff").append(t);
	}
	let n = (e.files || [e]).map((e) => e.diff).join("\n"), r = n.split("\n").filter((e) => e.startsWith("+") && !e.startsWith("+++")).length, i = n.split("\n").filter((e) => e.startsWith("-") && !e.startsWith("---")).length;
	_("#change-count").textContent = r || i ? `+${r} −${i}` : "", _("#artifacts").replaceChildren(), Object.keys(e.artifacts).length || (_("#artifacts").innerHTML = "<p class=\"helper\">No results yet. Choose the steps you want to prepare your application.</p>");
	for (let [t, n] of Object.entries(e.artifacts)) _("#artifacts").append(u(n.path, n.content, { open: t === "analyze" }));
	if (q(), J(), e.cover) {
		let e = document.createElement("button");
		e.id = "open-cover-pdf", e.textContent = "Open cover-letter PDF", e.onclick = () => Ae(), _("#artifacts").prepend(e);
	}
	B();
}
function z() {
	let e = v.snapshot;
	return e ? e.files?.find((e) => e.path === v.filePath) || e.files?.find((t) => t.path === e.path) || e : null;
}
function pe() {
	let e = v.snapshot, t = z();
	v.filePath = t.path, _("#cv-file").disabled = !1, _("#cv-file").replaceChildren(...(e.files || [e]).map((e) => {
		let t = document.createElement("option");
		return t.value = e.path, t.textContent = e.path + (e.exists === !1 ? " · unavailable" : "") + (e.diff ? " · changed" : ""), t;
	})), _("#cv-file").value = t.path, _("#include-problems").hidden = !e.includeDiagnostics?.length, _("#include-diagnostics").replaceChildren(...(e.includeDiagnostics || []).map((t) => {
		let n = document.createElement("li");
		n.textContent = t.message;
		let r = t.sourcePath || t.path;
		if (e.files.some((e) => e.path === r)) {
			let e = document.createElement("button");
			e.className = "quiet", e.textContent = "Open " + r, e.onclick = () => me(r, "source"), n.append(" ", e);
		}
		return n;
	}));
}
function me(e, t = v.view) {
	v.snapshot && (L() ? (v.filePath = e, v.dirty = !1, v.jobDirty = !1, fe(), V(t)) : _("#cv-file").value = v.filePath);
}
_("#cv-file").onchange = (e) => me(e.target.value);
function he(e, t) {
	let n = _(`#${e}-document .cv-document`);
	n.innerHTML = t.error ? `<p class="empty">Structure cannot preview this template. Use Source or PDF preview to view it.</p><details class="technical-details"><summary>Structure details</summary><pre>${k(t.error)}</pre></details>` : t.html;
}
function B() {
	y.summary(v.displayedRun);
	let e = v.snapshot;
	_("#save-state").textContent = v.dirty || v.jobDirty ? "Unsaved changes" : e?.saveState?.draft ? "Draft saved on this computer" : e && v.syncedCommits.get(e.branch) === e.commit ? "Saved and synced" : e?.saveState?.ahead === 0 ? "Saved" : "Saved on this computer · sync pending", _("#save-source").disabled = !v.dirty || !v.snapshot?.editable || !!v.snapshot?.running || z()?.exists === !1, _("#commit-push").disabled = !v.snapshot?.editable || !!v.snapshot?.running || v.publishing;
}
function V(e) {
	v.view = e, _("#file-navigation").hidden = ![
		"structure",
		"source",
		"changes"
	].includes(e), document.querySelectorAll("[data-view]").forEach((t) => {
		t.setAttribute("aria-selected", String(t.dataset.view === e)), t.tabIndex = t.dataset.view === e ? 0 : -1;
	}), v.snapshot && history.replaceState(null, "", "?" + new URLSearchParams({
		branch: v.snapshot.branch,
		view: e
	})), _("#comparison").hidden = ![
		"structure",
		"source",
		"pdf"
	].includes(e) || e === "pdf" && v.pdfDocument === "cover", _("#cover-pdf-pane").hidden = e !== "pdf" || v.pdfDocument !== "cover", _("#compile").textContent = v.pdfDocument === "cover" ? "Create cover-letter PDF" : "Create PDF previews", _("#structure-hint").hidden = e !== "structure", _("#pdf-toolbar").hidden = e !== "pdf", _("#changes-panel").hidden = e !== "changes", _("#ai-panel").hidden = e !== "ai", _("#document-actions").hidden = !1, _("#save-source").hidden = ["ai", "pdf"].includes(e);
	for (let t of ["original", "current"]) _(`#${t}-document`).hidden = e !== "structure", _(`#${t}-source`).hidden = e !== "source", _(`#${t}-pdf`).hidden = e !== "pdf";
	if (e === "source") for (let e of Object.values(O)) e.refresh();
	if (!v.snapshot) return;
	let t = z(), n = v.snapshot;
	if (_("#original-label").textContent = e === "pdf" || t.path === n.path ? "" : t.path, _("#current-label").textContent = e === "pdf" || t.path === n.path ? n.displayName || n.branch : t.path, _("#version-label").textContent = e !== "pdf" && n.editable && t.exists !== !1 ? "Editable" : "View only", e === "structure") {
		let e = z(), t = [.../* @__PURE__ */ new Set([...e.document.warnings, ...e.originalDocument.warnings])];
		N(v.dirty ? "The reading view shows the saved version. Save your draft to update this view." : t.join("\n"));
	} else if (e === "pdf") {
		N(v.dirty ? "PDF previews use your saved draft. Save your changes first." : "");
		for (let e of v.pdfDocument === "cover" ? ["cover"] : ["original", "current"]) v.pdfs[e] || (_(`#${e}-pdf`).innerHTML = "<p class=\"pdf-message\">Create a PDF preview to see the final layout.<br>Text will remain selectable.</p>");
	} else N();
}
async function H() {
	if (!v.dirty || !v.snapshot) return;
	if (v.jobDirty) {
		N("Save the job description draft first.", !0);
		return;
	}
	let e = v.snapshot, t = z(), n = O.current.value;
	_("#save-source").disabled = !0, O.current.setReadOnly(!0), _("#job-description").readOnly = !0, _("#save-job").disabled = !0;
	try {
		await M("/api/save", {
			branch: e.branch,
			path: t.path,
			revision: t.revision,
			projectRevision: e.projectRevision,
			content: n
		}), await R(e.branch, !0), P("CV draft saved on this computer");
	} catch (t) {
		N(t.message, !0), O.current.setReadOnly(!e.editable || z()?.exists === !1), _("#job-description").readOnly = !1, _("#save-job").disabled = !1, B();
	}
}
async function ge() {
	if (!v.snapshot) return;
	let e = v.snapshot;
	_("#save-job").disabled = !0;
	try {
		let t = await M("/api/save", {
			branch: e.branch,
			path: "job.md",
			revision: e.jobRevision,
			content: _("#job-description").value
		});
		e.job = t.content, e.jobRevision = t.revision, v.jobDirty = !1, _("#job-state").textContent = "Saved on this computer", e.saveState = t.saveState || {
			...e.saveState,
			draft: !0
		}, B(), P("Job description draft saved");
	} catch (e) {
		N(e.message, !0);
	} finally {
		_("#save-job").disabled = !e.editable;
	}
}
function _e() {
	let e = v.snapshot, t = {
		branch: e.branch,
		sourceRevision: e.revision,
		jobRevision: e.jobRevision
	};
	return v.dirty && (t.sourceContent = O.current.value), v.jobDirty && (t.jobContent = _("#job-description").value), t;
}
function ve(e, { retry: t = !1 } = {}) {
	v.commitReview = e, _("#commit-branch").textContent = S(e.branch), _("#commit-destination").textContent = e.destinationLabel || (e.remote ? "Connected destination" : "No sync destination connected"), _("#sync-details").textContent = e.destination || "Not connected", _("#commit-files").replaceChildren(...e.files.map((e) => {
		let t = document.createElement("li");
		return t.innerHTML = `<div>${k(d(e.path))}<details class="technical-details"><summary>File details</summary><code>${k(e.path)}</code></details></div><span class="commit-file-status">${{
			Added: "New",
			Modified: "Updated",
			Deleted: "Removed",
			Untracked: "New"
		}[e.status] || e.status}</span>`, t;
	})), _("#commit-files").hidden = !e.files.length, _("#commit-empty").hidden = !!e.files.length, _("#commit-empty").textContent = e.ahead > 0 ? `${e.ahead} saved ${e.ahead === 1 ? "version" : "versions"} will be synced.` : e.ahead === 0 ? "No new edits or versions are waiting to sync. Save will check the connection." : "No new edits. This application will be synced to the connected destination.", _("#commit-excluded").hidden = !e.excludedChanges, _("#commit-excluded").textContent = e.excludedChanges ? `${e.excludedChanges} other ${e.excludedChanges === 1 ? "file will" : "files will"} remain unchanged.` : "", _("#commit-message").disabled = !e.files.length, _("#commit-message").required = !!e.files.length, e.files.length && !_("#commit-message").value && (_("#commit-message").value = `Update CV for ${S(e.branch)}`), _("#confirm-commit").textContent = t ? "Retry sync" : "Save", _("#confirm-commit").disabled = !e.remote, e.remote || (_("#commit-error").textContent = "No sync destination is connected. Check your connection setup before saving.");
}
async function ye(e = {}) {
	let t = await M("/api/commit-preview", _e());
	return ve(t, e), t;
}
async function be() {
	if (v.snapshot && !v.snapshot.running) {
		if (v.dirty && z().path !== v.snapshot.path) {
			if (v.jobDirty) {
				N("Save your CV and job description drafts first.", !0);
				return;
			}
			if (await H(), v.dirty) return;
		}
		_("#commit-push").disabled = !0, _("#commit-error").textContent = "", _("#commit-progress").textContent = "Checking your changes…", _("#commit-message").value = "";
		try {
			await ye(), _("#commit-progress").textContent = "Review these changes before saving and syncing.", _("#commit-dialog").showModal(), v.commitReview.files.length && _("#commit-message").focus();
		} catch (e) {
			N(e.message, !0);
		} finally {
			B();
		}
	}
}
_("#commit-form").onsubmit = async (e) => {
	if (e.preventDefault(), v.publishing) return;
	v.publishing = !0;
	let t = e.submitter || _("#confirm-commit");
	t.disabled = !0, _("#commit-error").textContent = "", _("#commit-progress").textContent = v.commitReview.files.length ? "Saving and syncing…" : "Syncing saved versions…", document.querySelectorAll("#commit-dialog .close-dialog").forEach((e) => e.disabled = !0), B();
	try {
		let e = await M("/api/commit-push", {
			..._e(),
			message: _("#commit-message").value,
			review: v.commitReview.review
		});
		v.syncedCommits.set(e.branch, e.commit), _("#commit-dialog").close(), v.dirty = !1, v.jobDirty = !1, await R(e.branch, !0), await I(), P("Application saved and synced.");
	} catch (e) {
		if (_("#commit-error").textContent = (e.commitCreated && e.commit ? "Your changes were saved on this computer. " : "") + e.message, e.canRetry) try {
			await R(v.snapshot.branch, !0), await ye({ retry: !0 }), _("#commit-progress").textContent = "Your saved version is safe. Check the connection and retry syncing.";
		} catch (e) {
			_("#commit-error").textContent += "\n" + e.message;
		}
		else _("#commit-progress").textContent = "Nothing was synced.";
	} finally {
		v.publishing = !1, document.querySelectorAll("#commit-dialog .close-dialog").forEach((e) => e.disabled = !1), t.disabled = !v.commitReview?.remote, B();
	}
}, _("#commit-dialog").addEventListener("cancel", (e) => {
	v.publishing && e.preventDefault();
});
async function xe() {
	L() && (v.branches.length ? (_("#base-branch").innerHTML = v.branches.map((e) => `<option value="${k(e.name)}">${k(e.displayName || e.name)}</option>`).join(""), _("#base-branch").value = v.snapshot?.branch || v.branches.find((e) => e.current)?.name || v.branches[0]?.name || "", _("#create-error").textContent = "", _("#create-dialog").showModal(), _("#branch-name").focus()) : P("Wait for your saved CVs to load, then try again."));
}
_("#create-form").onsubmit = async (e) => {
	e.preventDefault();
	let t = e.submitter;
	t.disabled = !0;
	try {
		let e = _("#base-branch").value, t = await M("/api/workspace?branch=" + encodeURIComponent(e)), n = await M("/api/create", {
			base: e,
			applicationName: _("#branch-name").value.trim(),
			job: _("#new-job").value,
			revision: t.revision,
			projectRevision: t.projectRevision
		});
		_("#create-dialog").close(), v.dirty = !1, v.jobDirty = !1, await I(), v.view = "structure", await R(n.branch, !0), P("Application created with your CV and job description"), _("#create-form").reset();
	} catch (e) {
		_("#create-error").textContent = e.message;
	} finally {
		t.disabled = !1;
	}
}, _("#current-document").ondblclick = (e) => {
	let t = e.target.closest("[data-leaf]");
	if (!t || !v.snapshot?.editable) return;
	if (v.dirty || v.jobDirty) {
		N("Save your CV and job description drafts before editing this view.", !0);
		return;
	}
	if (v.snapshot.running) {
		N("Wait for this preparation to finish before editing.", !0);
		return;
	}
	if (z().exists === !1) return;
	v.leaf = t.dataset.leaf;
	let n = z().document.leaves[v.leaf];
	v.editOrigin = {
		path: n.path,
		revision: z().revision,
		projectRevision: v.snapshot.projectRevision
	}, _("#edit-origin").textContent = `${n.path} · characters ${n.start}–${n.end}`, _("#edit-text").value = n.text, _("#edit-error").textContent = "", _("#edit-dialog").showModal(), _("#edit-text").focus();
}, _("#edit-form").onsubmit = async (e) => {
	e.preventDefault(), e.submitter.disabled = !0;
	let t = v.snapshot;
	try {
		await M("/api/save", {
			branch: t.branch,
			...v.editOrigin,
			leaf: v.leaf,
			text: _("#edit-text").value
		}), _("#edit-dialog").close(), await R(t.branch, !0), P("CV draft updated on this computer");
	} catch (e) {
		_("#edit-error").textContent = e.message;
	} finally {
		e.submitter.disabled = !1;
	}
};
var U = (e) => !!(e?.requirementsApprovalNeeded || e?.factualReview?.state === "pending");
async function Se(e, t) {
	if (v.snapshot !== t) return e;
	if (t.running = e, v.graphRunId = e.id, await D.refresh(), v.snapshot === t) {
		let t = v.runs.find((t) => t.id === e.id) || e;
		s(t) || await we(v.runs.some((t) => t.id === e.id) ? v.runs : [e, ...v.runs]);
	}
	return v.snapshot && (J(), q(), B()), v.runs.find((t) => t.id === e.id) || e;
}
async function Ce(e, t = v.snapshot?.branch) {
	let n = v.snapshot;
	if (!n || n.branch !== t || v.dirty || v.jobDirty) throw Error("Approval saved. Reopen this application with saved drafts to continue.");
	let r = e ? v.runs.find((t) => t.id === e) : v.runs.find((e) => e.branch === t && e.requirementsDraft && !s(e));
	if (!e && !r) {
		await D.refresh();
		return;
	}
	let i = await Se(await M("/api/review-continue", {
		id: e || r.id,
		revision: n.revision,
		jobRevision: n.jobRevision
	}), n);
	v.snapshot?.branch === t && N(s(i) ? "Approved. Continuing preparation…" : i.message);
}
async function W(e = K().steps) {
	if (!v.snapshot || v.snapshot.running || v.launching) return;
	if (!e.length) {
		N("Select at least one step.", !0);
		return;
	}
	if (v.dirty || v.jobDirty) {
		N("Save your CV and job description before starting AI.", !0);
		return;
	}
	v.launching = !0, _("#run-adapt").disabled = !0, _("#run-all").disabled = !0, _("#task-run").disabled = !0, O.current.setReadOnly(!0), _("#job-description").readOnly = !0, _("#save-job").disabled = !0, _("#branch-from").disabled = !0;
	let t = v.snapshot;
	j();
	for (let e of C.map((e) => "step-" + e)) _("#" + e).disabled = !0;
	try {
		let n = A.problem(e);
		if (n) throw Error(n);
		let r = await M("/api/adapt", {
			branch: t.branch,
			revision: t.revision,
			jobRevision: t.jobRevision,
			aiConfig: A.value(),
			language: _("#language").value,
			workflow: { steps: e },
			engine: y.engine(),
			reviewPolicy: _("#review-policy").value
		});
		t.running = r, v.snapshot === t && (v.graphRunId = r.id, j(), q(), J(), B(), _("#ai-status").textContent = r.message), await D.refresh();
	} catch (e) {
		v.snapshot === t && (N(e.message, !0), q(), O.current.setReadOnly(!t.editable || z()?.exists === !1), _("#job-description").readOnly = !t.editable, _("#save-job").disabled = !t.editable, _("#branch-from").disabled = !1);
	} finally {
		v.launching = !1, v.snapshot && (j(), q(), J());
	}
}
async function we(e) {
	v.runs = e, F();
	let t = v.snapshot;
	if (!t) return;
	J();
	let n = e.find((e) => e.branch === t.branch && s(e));
	if (n) {
		t.running = n, _("#ai-status").textContent = n.message, O.current.setReadOnly(!0), _("#job-description").readOnly = !0;
		for (let e of [
			"save-job",
			"run-adapt",
			"run-all",
			"task-run",
			"branch-from"
		]) _("#" + e).disabled = !0;
		j(), q(), J(), B();
	} else if (t.running) {
		let n = e.find((e) => e.id === t.running.id);
		t.running = null, !v.dirty && !v.jobDirty && !v.publishing ? await R(t.branch, !0) && n && (_("#ai-status").textContent = n.message, N(n.message, n.status !== "succeeded" && !U(n))) : (O.current.setReadOnly(!t.editable || z()?.exists === !1), _("#job-description").readOnly = !t.editable, _("#save-job").disabled = !t.editable, _("#branch-from").disabled = !1, j(), B(), q(), N("The preparation finished. Your unsaved edits are safe; refresh to review the results.", !0));
	}
}
async function G(e) {
	if (!L()) return;
	let t = v.snapshot, n = t?.branch === e.branch && !t.running && !v.dirty && !v.jobDirty ? t : await R(e.branch, !0);
	if (n) {
		if (v.graphRunId = e.id, J(), V("ai"), _("#ai-status").textContent = e.message, e.source === "jobenu") _("#selected-run").hidden = !0, N("Showing the application’s current reports. Jobenu component history is recorded separately; use Import details for logs and continuation."), _("#ai-panel").scrollIntoView({ block: "start" });
		else {
			if (!s(e)) {
				let t = await M("/api/job-result?id=" + encodeURIComponent(e.id));
				if (v.snapshot !== n) return;
				let r = [e.provider ? A.summary(e) : "", [..._("#language").options].find((t) => t.value === e.language)?.textContent || e.language].filter(Boolean).join(" · ");
				_("#selected-run").hidden = !1, _("#selected-run-info").textContent = `${o(e)} · ${c(e)} · ${(/* @__PURE__ */ new Date(e.createdAt * 1e3)).toLocaleString()} · ${e.provider ? r : "Local checks; no AI used"} · ${Math.round(e.elapsedSeconds || 0)}s. Results from this preparation. Your application may contain newer edits.`, De(t), _("#selected-run-files").replaceChildren();
				for (let [e, n] of Object.entries(t.files)) _("#selected-run-files").append(u(e, n, {
					open: /analy(sis|ze)\.md$/.test(e),
					label: t.inputs?.includes(e) ? `Starting material · ${d(e)}` : d(e)
				}));
				if (Object.keys(t.files).length || (_("#selected-run-files").textContent = "This preparation did not produce any results."), t.coverPdf) {
					let e = document.createElement("button");
					e.id = "open-run-cover-pdf", e.textContent = "Open generated cover-letter PDF", e.onclick = () => Ae(t.coverPdf.runId), _("#selected-run-files").prepend(e);
				}
			}
			_("#ai-panel").scrollIntoView({ block: "start" });
		}
	}
}
function K() {
	return { steps: C.filter((e) => _("#step-" + e).checked) };
}
function q() {
	let e = v.snapshot, t = v.session.workflow || {}, n = e.running?.stages?.length ? e.running.stages.filter((e) => e.status !== "skipped").map((e) => e.id) : v.workflowChoices.get(e.branch)?.steps || [
		"analyze",
		"adapt",
		...t.review ? ["review"] : []
	];
	for (let t of C) {
		let r = _("#step-" + t);
		r.checked = n.includes(t) && w(t), r.disabled = !w(t) || !!e.running || !!v.launching || !e.editable, w(t) || (_("#hint-" + t).textContent = "Update Vita CV to use this step.");
	}
	let r = A.problem(K().steps), i = !v.session.vita || !e.editable || !!e.running || !!v.launching || !!r;
	_("#ai-config-validation").textContent = r, _("#ai-config-validation").hidden = !r, _("#run-adapt").textContent = "Start selected steps", _("#run-adapt").disabled = i || !K().steps.length, _("#run-all").disabled = i || !!A.problem(C.filter(w)), A.refresh();
}
function J() {
	if (!v.snapshot) return;
	let e = [...v.runs.filter((e) => e.branch === v.snapshot.branch), ...v.snapshot.nativeRuns || []].sort((e, t) => t.createdAt - e.createdAt), n = v.graphRunId || v.snapshot.running?.id || e[0]?.id || "draft", r = _("#workflow-run");
	r.replaceChildren(new Option("New preparation", "draft"), ...e.map((e) => new Option(`${e.attempt ? "Attempt " + e.attempt + " · " : ""}${(/* @__PURE__ */ new Date(e.createdAt * 1e3)).toLocaleString()} — ${o(e)} · ${c(e)}${e.source === "jobenu" || s(e) ? "" : e.reviewed ? " · Reviewed" : " · Needs review"}`, e.id)));
	let i = e.find((e) => e.id === n) || (v.snapshot.running?.id === n ? v.snapshot.running : null);
	i && !e.some((e) => e.id === i.id) && r.add(new Option("Current preparation", i.id)), r.value = i ? i.id : "draft", v.displayedRun = i, y.summary(i);
	let a = i && !s(i);
	for (let e of [
		"requirements-current-open",
		"requirements-captured",
		"task-requirements",
		"step-requirements"
	]) _("#" + e).disabled = !1;
	_("#requirements-captured").hidden = !i?.requirementsRevision && !i?.requirementsDraft, _("#requirements-captured").textContent = i?.requirementsRevision ? "Requirements used · " + i.requirementsRevision.slice(0, 12) + (i.requirementsStatus && i.requirementsStatus !== "current" ? " · needs update" : "") : "Review job requirements", _("#review-facts").hidden = !a || !i?.factualReview, _("#review-facts").disabled = !!v.snapshot.running || !!v.launching || !!v.openingRunId, _("#review-facts").textContent = i?.factualReview?.state === "resolved" ? "View factual decisions" : "Review factual changes", _("#inspect-run").hidden = !i, _("#inspect-step").hidden = !i, _("#inspect-step-dialog").hidden = !i, i?.source === "jobenu" ? (_("#inspect-run").textContent = "Import details", _("#inspect-step").hidden = !0, _("#inspect-step-dialog").hidden = !0) : _("#inspect-run").textContent = "Execution details", _("#resume-run").hidden = !i?.resumeAvailable, _("#resume-run").disabled = !!v.snapshot.running || !!v.launching || !!v.retryPlanning || !v.snapshot.editable, _("#view-run").hidden = !a, _("#view-run").disabled = !!v.openingRunId, _("#view-run").textContent = v.openingRunId ? "Opening results…" : "View results";
	let l = _("#mark-run-reviewed");
	l.hidden = !a || i?.source === "jobenu", l.disabled = !!i?.reviewed || !!v.reviewingRunId, l.textContent = i?.reviewed ? "Reviewed" : v.reviewingRunId === i?.id ? "Saving review…" : "Mark as reviewed", _("#workflow-summary").textContent = i ? i.factualReview ? i.message : m(i) || i.message : "Choose the steps for your next preparation. Only selected AI steps will use your AI service.", i?.reviewPolicy === "automatic" && (_("#workflow-summary").textContent += " Automatic approvals selected for this preparation."), t(_("#workflow-graph"), {
		run: i,
		history: e,
		options: K(),
		available: v.session.workflow,
		selected: v.selectedTask,
		select: Ee,
		config: i?.stepConfig || Object.fromEntries(C.map((e) => [e, A.route(e)]))
	});
	let u = _("#workflow-next");
	u.disabled = !!v.snapshot.running || !!v.launching, u.textContent = i?.requirementsApprovalNeeded ? "Review job requirements" : i?.factualReview?.state === "pending" ? "Review CV changes" : i?.resumeAvailable ? "Continue preparation" : a && i.status === "succeeded" ? "Preview your PDF" : "Prepare application", _("#workflow-action").dataset.state = U(i) ? "review" : i?.status === "failed" ? "failed" : "ready", _("#workflow-next-help").textContent = U(i) ? "One review, then the remaining steps continue automatically." : i?.status === "failed" ? m(i) || i.message : a && i.status === "succeeded" ? "Your application is updated. Check the final layout before saving." : "Prepare everything, or choose individual steps in Job details & AI.", i?.source === "jobenu" && (u.textContent = "Open import activity", _("#workflow-next-help").textContent = i.message), _("#review-policy").disabled = !!v.snapshot.running || !!v.launching, v.selectedTask && Te();
}
function Te() {
	let e = i(v.displayedRun, K(), v.session.workflow).find((e) => e.id === v.selectedTask);
	if (!e) return;
	_("#task-inspector").hidden = !1, _("#task-title").textContent = e.title;
	let t = v.displayedRun?.stepConfig?.[e.id] || (!v.displayedRun && e.id !== "validating" ? A.route(e.id) : null);
	_("#task-description").textContent = e.detail + (t ? " AI setup: " + A.summary(t) + ". Connection: " + A.connectionName(t) + "." : e.id === "validating" ? " This step runs locally without an AI model." : ""), _("#task-status").textContent = `${r[e.status] || e.status} · ${e.output}`, _("#task-output").textContent = e.id === "validating" ? "Compare current CVs" : e.id === "adapt" ? "View CV source" : "View results", _("#task-run").textContent = e.id === "validating" ? "Check current changes" : "Start this step", _("#task-requirements").hidden = e.id !== "extract", _("#task-configure").hidden = e.id === "validating", _("#task-configure").textContent = v.displayedRun ? "Configure next run" : "Configure AI", _("#task-configure").disabled = !!v.snapshot.running || !!v.launching || !v.snapshot.editable, _("#task-run").disabled = !v.snapshot.editable || !!v.snapshot.running || !!v.launching || !w(e.id) || e.id !== "validating" && (!v.session.vita || !!A.problem([e.id])), _("#task-output").disabled = s(v.displayedRun) || !["succeeded", "unknown"].includes(e.status), h(v.displayedRun, e.id) && (_("#task-status").textContent = h(v.displayedRun, e.id)), s(v.displayedRun) && (_("#task-status").textContent += " · Results open after the preparation finishes.");
}
function Ee(e) {
	v.snapshot && (v.selectedTask = e.id, J(), C.includes(e.id) && A.openStep(e.id, {
		history: !!v.displayedRun,
		recorded: v.displayedRun?.stepConfig?.[e.id],
		readOnly: !!v.snapshot.running || !!v.launching || !v.snapshot.editable,
		allowNext: !v.snapshot.running && !v.launching && v.snapshot.editable
	}));
}
_("#workflow-next").onclick = () => {
	let e = v.displayedRun;
	if (e?.source === "jobenu") return oe.open();
	if (e?.requirementsApprovalNeeded) return b.open().catch((e) => N(e.message, !0));
	if (e?.factualReview?.state === "pending") return x.open(e).catch((e) => N(e.message, !0));
	if (e?.resumeAvailable) return v.resumeCaptured = !0, _("#resume-current-config").checked = !1, X();
	if (e?.status === "succeeded") {
		V("pdf");
		return;
	}
	let t = C.filter(w);
	if (A.problem(t) || !v.snapshot.job.trim()) V("ai"), _("#ai-panel").scrollIntoView({ block: "start" }), N("Add the job description and choose your AI setup, then prepare the application.");
	else return W(t);
}, _("#view-run").onclick = async () => {
	let e = v.displayedRun;
	if (!(!e || s(e) || v.openingRunId)) {
		v.openingRunId = e.id, J();
		try {
			await G(e);
		} catch (e) {
			N(e.message, !0);
		} finally {
			v.openingRunId = null, J();
		}
	}
};
function Y(e) {
	return i(null, {}, {}).find((t) => t.id === e)?.title || e;
}
for (let e of [
	"task-requirements",
	"step-requirements",
	"requirements-current-open"
]) _("#" + e).onclick = () => b.open().catch((e) => N(e.message, !0));
_("#requirements-captured").onclick = () => b.open(v.displayedRun?.requirementsRevision ? v.displayedRun : null).catch((e) => N(e.message, !0)), _("#review-facts").onclick = () => {
	v.displayedRun && x.open(v.displayedRun).catch((e) => N(e.message, !0));
};
function De(e) {
	let t = _("#attempt-history");
	t.replaceChildren();
	let n = document.createElement("h3");
	n.textContent = "Attempt history", t.append(n);
	let r = document.createElement("p");
	r.className = "helper", r.textContent = e.run.checkpointSteps?.length ? "Verified results retained: " + e.run.checkpointSteps.map(Y).join(", ") + "." : "No verified checkpoints retained. A retry will run every selected step again.", t.append(r);
	for (let n of e.attemptHistory || [e.run]) {
		let r = document.createElement("div");
		r.className = "attempt-row";
		let i = document.createElement("button");
		if (i.type = "button", i.className = "quiet", i.textContent = `Attempt ${n.attempt || 1} · ${c(n)}${n.id === e.run.id ? " · Viewing" : ""}`, i.disabled = n.id === e.run.id, i.onclick = () => G(n).catch((e) => N(e.message, !0)), r.append(i), n.requirementsRevision || n.requirementsDraft) {
			let e = document.createElement("button");
			e.textContent = "Requirements " + (n.requirementsRevision || n.requirementsDraft) + (n.requirementsStatus && n.requirementsStatus !== "current" ? " · needs update" : ""), e.onclick = () => b.open(n).catch((e) => N(e.message, !0)), r.append(e);
		}
		if (n.factualReview) {
			let e = document.createElement("button");
			e.type = "button", e.textContent = n.factualReview.state === "resolved" ? "View factual decisions" : "Review factual changes", e.onclick = () => x.open(n).catch((e) => N(e.message, !0)), r.append(e);
		}
		if (n.parentRunId) {
			let t = document.createElement("span");
			t.className = "helper", t.textContent = "Continues attempt " + ((e.attemptHistory || []).find((e) => e.id === n.parentRunId)?.attempt || "unknown") + " · " + (n.configurationChanged ? "Changed setup" : "Captured setup preserved"), r.append(t);
		}
		for (let [e, t] of Object.entries(n.outcomes || {})) {
			let i = document.createElement("p");
			i.className = "helper", i.textContent = Y(e) + ": " + (t.status === "success" ? "Completed" : "Could not finish") + (t.backend?.attempts?.length ? " · AI attempts: " + t.backend.attempts.map((e) => `${e.number}: ${e.category.replaceAll("_", " ")}`).join("; ") : ""), r.append(i);
			let a = h(n, e);
			if (a) {
				let e = document.createElement("p");
				e.className = "provider-failure", e.textContent = a, r.append(e);
			}
		}
		t.append(r);
	}
}
async function X() {
	let e = v.displayedRun, t = v.snapshot;
	if (!(!e?.resumeAvailable || v.retryPlanning || v.launching)) {
		if (v.dirty || v.jobDirty) N("Save your CV and job description drafts before retrying.", !0);
		else {
			v.retryPlanning = !0, _("#confirm-resume").disabled = !0, _("#resume-current-config").disabled = !0, J();
			try {
				let n = v.resumeCaptured && !_("#resume-current-config").checked, r = {
					id: e.id,
					revision: t.revision,
					jobRevision: t.jobRevision,
					...n ? {} : {
						aiConfig: A.value(),
						language: _("#language").value
					}
				}, i = await M("/api/resume-preview", r);
				if (v.snapshot !== t) return;
				v.resumeReview = {
					request: r,
					plan: i,
					snapshot: t
				}, _("#resume-summary").textContent = `Attempt ${i.attempt}, continuing attempt ${e.attempt || 1}. Output language: ${[..._("#language").options].find((t) => t.value === (n ? e.language : _("#language").value))?.textContent || e.language}. Captured TeX engine: ${e.compileEngine || "auto"}. ${n ? "Preserves the AI setup and language captured for this preparation." : "Uses the AI setup currently shown for this application."}`, _("#resume-config-choice").hidden = !v.resumeCaptured, _("#resume-reuse").textContent = i.reuse.length ? i.reuse.map(Y).join(", ") : "None. Start again with the current inputs and setup.", _("#resume-rerun").textContent = [...i.rerun.map(Y), "Final checks"].join(", "), _("#resume-adapted").hidden = !i.reuse.includes("adapt"), _("#resume-error").textContent = "", _("#confirm-resume").disabled = !1, _("#resume-dialog").open || _("#resume-dialog").showModal();
			} catch (e) {
				v.resumeReview = null, _("#confirm-resume").disabled = !0, _("#resume-error").textContent = e.message, N(e.message, !0), v.resumeCaptured && (_("#resume-config-choice").hidden = !1, _("#resume-summary").textContent = "The captured setup could not be checked. Reconnect the account in this application, then explicitly choose its current setup, or cancel and review the error.", _("#resume-reuse").textContent = "Not verified. A valid retry plan is required before starting.", _("#resume-rerun").textContent = "Not planned yet.", _("#resume-adapted").hidden = !0, _("#resume-dialog").open || _("#resume-dialog").showModal());
			} finally {
				v.retryPlanning = !1, _("#resume-current-config").disabled = !1, J();
			}
		}
	}
}
_("#resume-run").onclick = () => {
	v.resumeCaptured = !0, _("#resume-current-config").checked = !1, X();
}, _("#resume-current-config").onchange = () => X(), _("#resume-form").onsubmit = async (e) => {
	e.preventDefault();
	let t = v.resumeReview;
	if (t && !v.launching) {
		v.launching = !0, _("#confirm-resume").disabled = !0, J(), q();
		try {
			let e = await M("/api/resume", {
				...t.request,
				token: t.plan.token
			});
			_("#resume-dialog").close(), _("#selected-run").hidden = !0, await Se(e, t.snapshot);
		} catch (e) {
			_("#resume-error").textContent = e.message;
		} finally {
			v.launching = !1, _("#confirm-resume").disabled = !1, q(), J();
		}
	}
}, _("#resume-dialog").onclose = () => {
	v.launching || (v.resumeReview = null);
}, _("#cleanup-checkpoints").onclick = async () => {
	let e = _("#cleanup-checkpoints");
	e.disabled = !0;
	try {
		let e = await M("/api/checkpoints-cleanup", {});
		_("#cleanup-checkpoints-status").textContent = `Removed checkpoints for ${e.removed.length} preparations. ${e.retainedRuns} retained. Your drafts and review results are unchanged.`, await D.refresh(), J();
	} catch (e) {
		_("#cleanup-checkpoints-status").textContent = e.message;
	} finally {
		e.disabled = !1;
	}
}, _("#mark-run-reviewed").onclick = async () => {
	let e = v.displayedRun;
	if (!(!e || s(e) || e.reviewed || v.reviewingRunId)) {
		v.graphRunId = e.id, v.reviewingRunId = e.id, J(), N();
		try {
			let t = await M("/api/job-reviewed", { id: e.id });
			v.runs = v.runs.map((e) => e.id === t.id ? t : e), F(), J(), P("Run marked as reviewed."), await D.refresh();
		} catch (e) {
			N(e.message, !0);
		} finally {
			v.reviewingRunId = null, J();
		}
	}
}, _("#workflow-run").onchange = () => {
	v.graphRunId = _("#workflow-run").value, J();
};
for (let e of C) _("#step-" + e).onchange = () => {
	v.workflowChoices.set(v.snapshot.branch, K()), v.graphRunId = "draft", q(), J();
};
_("#task-run").onclick = () => W([v.selectedTask]), _("#task-configure").onclick = () => A.openStep(v.selectedTask), _("#run-all").onclick = () => W(C.filter(w)), _("#toggle-workflow").onclick = () => {
	let e = _("#workflow-body");
	e.hidden = !e.hidden, _("#toggle-workflow").textContent = e.hidden ? "Show steps" : "Hide steps", _("#toggle-workflow").setAttribute("aria-expanded", String(!e.hidden));
}, _("#task-output").onclick = async () => {
	let e = v.selectedTask, t = v.displayedRun;
	if (e === "validating") V("structure"), _("#comparison").scrollIntoView({ block: "start" });
	else try {
		if (e === "cover" && t && t.source !== "jobenu" && !s(t) && (await M("/api/job-result?id=" + encodeURIComponent(t.id))).coverPdf) {
			await Ae(t.id);
			return;
		}
		t && !s(t) ? await G(t) : V("ai");
		let n = {
			extract: "job.json",
			analyze: "analy",
			review: "review.",
			cover: "cover",
			adapt: "main.tex"
		}[e], r = [...(t && t.source !== "jobenu" && !s(t) ? _("#selected-run-files") : _("#artifacts")).querySelectorAll("details[data-path]")].find((e) => e.dataset.path.includes(n));
		r ? (r.open = !0, r.scrollIntoView({ block: "center" }), r.querySelector("summary").focus()) : N("This step has no saved results. Check the preparation status.");
	} catch (e) {
		N(e.message, !0);
	}
};
var Z;
async function Oe() {
	return Z || (Z = await import("/vendor/pdf.mjs"), Z.GlobalWorkerOptions.workerSrc = "/vendor/pdf.worker.mjs"), Z;
}
async function ke(e, t, n) {
	let r = v.snapshot;
	if (r) {
		if (e === "current" && v.dirty) N("Save your CV draft and recreate the preview before saving the PDF.", !0);
		else {
			n.disabled = !0;
			try {
				let e;
				try {
					e = await M("/api/pdf-save", {
						id: t.id,
						branch: r.branch
					});
				} catch (n) {
					if (!n.existingRevision || !window.confirm(`${n.filename} already exists in this application folder. Replace it with this preview?`)) {
						if (!n.existingRevision) throw n;
						return;
					}
					e = await M("/api/pdf-save", {
						id: t.id,
						branch: r.branch,
						existingRevision: n.existingRevision
					});
				}
				v.snapshot === r && N(`Saved ${e.filename} in this application’s folder.`);
			} catch (e) {
				v.snapshot === r && N(e.message, !0);
			} finally {
				n.disabled = !1;
			}
		}
	}
}
async function Q(e, t, n) {
	let r = await Oe(), i = _(`#${e}-pdf`), a = r.getDocument({
		url: t.url,
		cMapUrl: "/vendor/cmaps/",
		cMapPacked: !0,
		standardFontDataUrl: "/vendor/standard_fonts/",
		wasmUrl: "/vendor/wasm/"
	}), o = await a.promise;
	if (n !== v.pdfGeneration) {
		await a.destroy();
		return;
	}
	i.replaceChildren();
	let s = document.createElement("div");
	s.className = "pdf-actions";
	let c = document.createElement("a");
	c.className = "pdf-download", c.href = t.url, c.tabIndex = 0, c.target = "_blank", c.rel = "noopener", c.textContent = "Open PDF ↗";
	let l = document.createElement("button");
	l.className = "save-pdf", l.textContent = "Save PDF to application folder", l.title = t.filename || "Save this PDF", l.disabled = !v.snapshot?.editable, l.onclick = () => ke(e, t, l), s.append(c, l), i.append(s);
	for (let e = 1; e <= o.numPages; e++) {
		let t = await o.getPage(e);
		if (n !== v.pdfGeneration) {
			await a.destroy();
			return;
		}
		let s = t.getViewport({ scale: 1 }), c = Math.max(200, i.clientWidth - 30), l = _("#zoom").value, u = l === "fit" ? c / s.width : Number(l), d = t.getViewport({ scale: u }), f = document.createElement("div");
		f.className = "pdf-page", f.style.width = d.width + "px", f.style.height = d.height + "px", f.style.setProperty("--scale-factor", u), f.style.setProperty("--total-scale-factor", u), f.style.setProperty("--user-unit", "1");
		let p = document.createElement("canvas"), m = Math.min(window.devicePixelRatio || 1, 2);
		p.width = Math.floor(d.width * m), p.height = Math.floor(d.height * m), p.style.width = d.width + "px", p.style.height = d.height + "px", f.append(p), i.append(f), await t.render({
			canvasContext: p.getContext("2d"),
			viewport: d,
			transform: m === 1 ? null : [
				m,
				0,
				0,
				m,
				0,
				0
			]
		}).promise;
		let h = document.createElement("div");
		h.className = "textLayer", f.append(h), await new r.TextLayer({
			textContentSource: await t.getTextContent(),
			container: h,
			viewport: d
		}).render();
		let g = document.createElement("div");
		g.className = "pdf-page-label", g.textContent = `Page ${e} of ${o.numPages}`, i.append(g);
	}
	await a.destroy();
}
async function Ae(e = null) {
	v.pdfDocument = "cover", _("#pdf-document").value = "cover", V("pdf"), await je(e);
}
_("#pdf-document").onchange = async () => {
	v.pdfDocument = _("#pdf-document").value;
	let e = ++v.pdfGeneration;
	V("pdf");
	try {
		for (let t of v.pdfDocument === "cover" ? ["cover"] : ["original", "current"]) v.pdfs[t] && await Q(t, v.pdfs[t], e);
	} catch (e) {
		N(e.message, !0);
	}
};
async function je(e = null) {
	if (v.dirty && v.pdfDocument === "cv") {
		N("Save your CV draft before creating PDF previews.", !0);
		return;
	}
	if (!v.snapshot) return;
	let t = v.pdfDocument, n = ++v.pdfGeneration, r = v.snapshot.branch;
	_("#compile").disabled = !0, N("Creating your PDF preview…");
	try {
		let i = await Promise.allSettled((t === "cover" ? ["cover"] : ["original", "current"]).map(async (i) => {
			delete v.pdfs[i], _(`#${i}-pdf`).innerHTML = "<p class=\"pdf-message\">Creating PDF preview…</p>";
			try {
				let a = await M("/api/pdf", {
					branch: r,
					side: i === "cover" ? "current" : i,
					engine: _("#engine").value,
					document: t,
					runId: t === "cover" ? e : null
				});
				return n === v.pdfGeneration ? (v.pdfs[i] = a, i === "cover" && (_("#cover-pdf-label").textContent = e ? "PDF from this preparation" : S(r)), await Q(i, a, n), a) : void 0;
			} catch (e) {
				throw n === v.pdfGeneration && (_(`#${i}-pdf`).innerHTML = `<p class="pdf-message">${k(e.message)}</p>`), e;
			}
		}));
		if (n !== v.pdfGeneration) return;
		let a = i.flatMap((e) => e.status === "fulfilled" ? e.value?.warnings || [] : [e.reason.message]);
		N(a.length ? a.join("\n") : t === "cover" ? "Cover-letter PDF ready. Text is selectable." : "PDF previews are ready. Select and copy text from either page.", i.some((e) => e.status === "rejected"));
	} finally {
		_("#compile").disabled = !v.snapshot;
	}
}
_("#zoom").onchange = async () => {
	let e = ++v.pdfGeneration;
	try {
		for (let t of v.pdfDocument === "cover" ? ["cover"] : ["original", "current"]) v.pdfs[t] && await Q(t, v.pdfs[t], e);
	} catch (e) {
		N(e.message, !0);
	}
}, document.querySelectorAll("[data-filter]").forEach((e) => e.onclick = () => {
	v.filter = e.dataset.filter, document.querySelectorAll("[data-filter]").forEach((t) => t.setAttribute("aria-pressed", String(t === e))), F();
}), _("#search").oninput = F, _("#refresh").onclick = I, _("#new-branch").onclick = xe, _("#branch-from").onclick = xe, _("#back").onclick = () => {
	if (!L()) return;
	let e = v.snapshot?.branch;
	v.generation++, v.pdfGeneration++, v.snapshot = null, v.dirty = !1, v.jobDirty = !1, _("#workspace").hidden = !0, _("#board").hidden = !1, document.body.classList.remove("in-workspace"), history.replaceState(null, "", "/"), _("#search").focus(), e && de(e), I();
}, _("#reload").onclick = () => R(v.snapshot?.branch || _("#branch-title").textContent), document.querySelectorAll("[data-view]").forEach((e) => e.onclick = () => V(e.dataset.view)), _(".tabs").addEventListener("focusin", (e) => requestAnimationFrame(() => {
	document.activeElement === e.target && e.target.scrollIntoView({
		block: "nearest",
		inline: "nearest"
	});
})), _(".tabs").onkeydown = (e) => {
	if (![
		"ArrowLeft",
		"ArrowRight",
		"Home",
		"End"
	].includes(e.key)) return;
	let t = [...document.querySelectorAll("[data-view]")], n = t.indexOf(e.target);
	if (n < 0) return;
	let r = e.key === "Home" ? 0 : e.key === "End" ? t.length - 1 : (n + (e.key === "ArrowRight" ? 1 : -1) + t.length) % t.length;
	e.preventDefault(), V(t[r].dataset.view), t[r].focus();
}, document.querySelectorAll(".close-dialog").forEach((e) => e.onclick = () => e.closest("dialog").close()), _("#job-description").oninput = () => {
	v.jobDirty = _("#job-description").value !== v.snapshot.job, _("#job-state").textContent = v.jobDirty ? "Unsaved changes" : "Saved on this computer", B();
}, _("#save-source").onclick = H, _("#save-job").onclick = ge, _("#commit-push").onclick = be, _("#run-adapt").onclick = () => W(), _("#compile").onclick = () => je(), window.addEventListener("beforeunload", (e) => {
	(v.dirty || v.jobDirty) && (e.preventDefault(), e.returnValue = "");
}), window.addEventListener("pagehide", () => {
	v.snapshot && v.session && fetch("/api/release-worktree", {
		method: "POST",
		keepalive: !0,
		headers: {
			"Content-Type": "application/json",
			"X-Vita-Token": v.session.token
		},
		body: JSON.stringify({ branch: v.snapshot.branch })
	}).catch(() => {});
}), document.addEventListener("keydown", (e) => {
	e.key === "/" && !e.target.closest("input,textarea,select,[contenteditable]") && !_("#board").hidden && (e.preventDefault(), _("#search").focus()), (e.ctrlKey || e.metaKey) && e.key === "s" && v.snapshot && (e.preventDefault(), v.view === "ai" ? ge() : H());
});
var Me = f({
	api: M,
	retry: async (e, t) => {
		if (v.dirty || v.jobDirty) throw Error("Save your CV and job description drafts before retrying.");
		let n = await M("/api/job?id=" + encodeURIComponent(e));
		if (t(), await G(n), v.snapshot?.branch !== n.branch) throw Error("Open this application before retrying.");
		v.resumeCaptured = !0, _("#resume-current-config").checked = !1, await X();
	}
});
_("#inspect-run").onclick = () => v.displayedRun?.source === "jobenu" ? oe.open() : Me.open(v.displayedRun?.id), _("#inspect-step").onclick = () => Me.open(v.displayedRun?.id, v.selectedTask), _("#inspect-step-dialog").onclick = () => {
	_("#step-ai-dialog").close(), Me.open(v.displayedRun?.id, v.selectedTask);
};
try {
	await ae(), await I();
	let e = new URLSearchParams(location.search), t = e.get("branch");
	[
		"structure",
		"source",
		"pdf",
		"changes",
		"ai"
	].includes(e.get("view")) && (v.view = e.get("view")), t && await R(t), D = l({
		api: M,
		changed: we
	}), D.start();
} catch (e) {
	_("#branch-list").innerHTML = `<p class="empty">${k(e.message)}</p>`;
}
setInterval(() => {
	document.querySelectorAll(".dag-time[data-started-at]").forEach((e) => {
		e.textContent = `${Math.max(0, Math.floor(Date.now() / 1e3 - Number(e.dataset.startedAt)))}s`;
	});
}, 1e3);
var $ = !1;
setInterval(async () => {
	let e = v.snapshot;
	if (!(!e || _("#workspace").hidden || $)) {
		$ = !0;
		try {
			let { runs: t } = await M("/api/jobenu/history?branch=" + encodeURIComponent(e.branch));
			if (v.snapshot !== e) return;
			JSON.stringify(t) !== JSON.stringify(e.nativeRuns || []) && (e.nativeRuns = t, J());
		} catch {
			_("#ai-status").textContent = "Import history could not refresh. Reload to reconnect.";
		} finally {
			$ = !1;
		}
	}
}, 2500);
