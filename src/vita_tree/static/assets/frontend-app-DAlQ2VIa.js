import { a as e, c as t, i as n, l as r, n as i, r as a, s as o, t as s } from "./frontend-workflow-DzZcoqia.js";
import { t as c } from "./frontend-client-Cqgf6Pc4.js";
import { i as l, n as u, r as d, t as f } from "./frontend-runs-hCqe5cjr.js";
import { i as p, n as m, t as h } from "./frontend-reports-DfIid_Jq.js";
import { t as g } from "./frontend-diagnostics-DPKkcqsI.js";
import { t as ee } from "./frontend-ai-settings-Dr2u_7AL.js";
import { n as _, t as v } from "./frontend-provider-failures-uMyQIdg2.js";
import { t as te } from "./frontend-factual-review-C1JvgUhX.js";
import { t as ne } from "./frontend-jobenu-S9Z8cF7V.js";
import { t as re } from "./frontend-requirements-CEEL9r4B.js";
import { t as ie } from "./frontend-preflight-CXA8w4x8.js";
import { createLatexEditor as ae } from "/vendor/editor.mjs";
// frontend/src/compat/app.js
var y = (e) => document.querySelector(e), b = {
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
}, oe;
async function se() {
	oe ||= P("/api/session").then((e) => {
		b.session = e;
	}), await oe;
}
var x = ie({
	api: P,
	getState: () => b,
	getBranches: () => b.branches,
	getSteps: () => q().steps
}), S = re({
	api: P,
	getState: () => b,
	changed: () => k.refresh(),
	continued: Ee,
	notice: F
}), C = te({
	api: P,
	getState: () => b,
	changed: () => k.refresh(),
	continued: Ee,
	notice: F
});
b.filter = "all", b.syncedCommits = /* @__PURE__ */ new Map();
var w = (e) => b.branches.find((t) => t.name === e)?.displayName || (b.snapshot?.branch === e ? b.snapshot.displayName : null) || e;
b.workflowChoices = /* @__PURE__ */ new Map();
var T = [
	"extract",
	"analyze",
	"adapt",
	"review",
	"cover"
], E = ne({
	api: P,
	branches: () => b.branches,
	openBranch: B,
	ready: se
}), D = (e) => ![
	"extract",
	"review",
	"cover"
].includes(e) || !!b.session?.workflow?.[e];
b.pdfDocument = "cv", b.runs = [], b.reviewSelection = /* @__PURE__ */ new Set(), b.reviewing = !1;
var O = [], ce = (e) => b.runs.filter((t) => t.branch === e && !u(t) && !t.reviewed);
function le() {
	let e = b.runs.filter((e) => b.reviewSelection.has(e.branch) && !u(e) && !e.reviewed).length;
	y("#bulk-review").disabled = b.reviewing || !e, y("#bulk-review").textContent = b.reviewing ? "Saving review…" : "Mark selected as reviewed", y("#bulk-review-count").textContent = e ? `${e} ${e === 1 ? "result" : "results"} selected` : "";
	let t = O.filter((e) => b.reviewSelection.has(e)).length, n = y("#select-review-visible");
	n.checked = !!t && t === O.length, n.indeterminate = !!t && t < O.length, n.disabled = b.reviewing || !O.length;
}
y("#select-review-visible").onchange = (e) => {
	for (let t of O) e.target.checked ? b.reviewSelection.add(t) : b.reviewSelection.delete(t);
	L();
}, y("#bulk-review").onclick = async () => {
	let e = b.runs.filter((e) => b.reviewSelection.has(e.branch) && !u(e) && !e.reviewed).map((e) => e.id);
	if (b.reviewing || !e.length) return;
	if (e.length > 500) {
		y("#bulk-review-status").hidden = !1, y("#bulk-review-status").textContent = "Select fewer applications: up to 500 results can be reviewed at once.";
		return;
	}
	b.reviewing = !0, L();
	let t = y("#bulk-review-status");
	t.hidden = !1, t.textContent = `Marking ${e.length} results as reviewed…`;
	try {
		let n = await P("/api/jobs-reviewed", { ids: e }), r = new Set(n.reviewed);
		for (let e of b.runs) r.has(e.id) && (e.reviewed = !0);
		t.textContent = `${n.reviewed.length} ${n.reviewed.length === 1 ? "result" : "results"} marked as reviewed.` + (n.failed.length ? ` ${n.failed.length} could not be saved and remain selected. ${n.failed[0].error} Reference: ${n.requestId}` : ""), await k.refresh();
	} catch (e) {
		t.textContent = e.message;
	} finally {
		b.reviewing = !1, L();
	}
};
var k, ue = /* @__PURE__ */ new Map();
function de() {
	let e = b.snapshot?.branch;
	if (!e || !b.catalog) return;
	let t = y("#language"), n = b.snapshot.running?.language || ue.get(e) || "en", r = [...b.catalog.languages || [{
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
y("#language").onchange = () => {
	b.snapshot && ue.set(b.snapshot.branch, y("#language").value);
};
var A = Object.fromEntries(["original", "current"].map((e) => [e, ae(y(`#${e}-source`), {
	label: e === "original" ? "Before · CV source" : "Current CV source",
	readOnly: !0,
	onChange: (t) => {
		e === "current" && b.snapshot && (b.dirty = t !== V().content, H());
	},
	lint: async (e, t) => c("/api/lint", { content: e }, b.session.token, { signal: t })
})])), j = (e) => String(e ?? "").replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]), M = ee(y("#ai-configuration"), {
	api: P,
	onChange: () => {
		b.snapshot && (b.displayedRun?.resumeAvailable || (b.graphRunId = "draft", b.historyRunId = null), J(), Y());
	}
});
function N() {
	de(), M.setDisabled(!!b.snapshot?.running || !!b.launching || !b.snapshot?.editable), y("#language").disabled = !!b.snapshot?.running || !!b.launching || !b.snapshot?.editable, y("#model-details").textContent = "Model suggestions come from repository settings and your local Codex catalog. You can enter any model ID your provider accepts.\n\nSetup: install vita-tree[ai] or start with --vita-source pointing to vita-cv. Custom reasoning currently uses the Codex connection.";
}
async function P(e, t) {
	return c(e, t, b.session?.token || "", { fresh: e.startsWith("/api/workspace?") });
}
function F(e = "", t = !1) {
	let n = t && e.includes("\n") || /Cannot parse this LaTeX|Environment .+:|Math is shown as text|use PDF for exact rendering/.test(e);
	y("#message-details").hidden = !n, y("#message-technical").textContent = n ? e : "", y("#notice").textContent = n ? t ? e.startsWith("Cannot parse this LaTeX") ? "The CV has a formatting problem. Open Technical details." : e.split("\n")[0] : "Some formatting may look different here. Use PDF preview to check the final layout." : e, y("#notice").hidden = !e, y("#notice").classList.toggle("error", t);
}
function I(e) {
	y("#toast").textContent = e, y("#toast").hidden = !1, clearTimeout(b.toast), b.toast = setTimeout(() => y("#toast").hidden = !0, 4e3);
}
function fe(e) {
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
function L() {
	let e = y("#search").value.toLowerCase(), n = (e, t) => {
		let n = b.runs.filter((t) => t.branch === e.name), r = n[0];
		return t === "all" || t === "running" && n.some(u) || t === "review" && n.some((e) => i(e) || e.status === "succeeded" && !e.reviewed) || t === "failed" && r && !i(r) && ["failed", "interrupted"].includes(r.status);
	};
	for (let e of [
		"all",
		"running",
		"review",
		"failed"
	]) y("#filter-" + e).textContent = b.branches.filter((t) => n(t, e)).length;
	let r = b.branches.filter((t) => n(t, b.filter) && `${t.displayName || t.name} ${t.name} ${t.subject} ${t.author}`.toLowerCase().includes(e));
	for (let e of b.reviewSelection) ce(e).length || b.reviewSelection.delete(e);
	O = r.filter((e) => ce(e.name).length).map((e) => e.name);
	let a = document.activeElement, o = a.closest(".branch-entry")?.dataset.branch, s = a.matches(".select-branch-review"), c = r.map((e) => {
		let t = b.runs.filter((t) => t.branch === e.name), n = t.find(u) || t.find(i) || t.find((e) => !e.reviewed) || t[0], r = n && (u(n) || i(n) || !n.reviewed || ["failed", "interrupted"].includes(n.status));
		return {
			branch: e,
			selected: b.reviewSelection.has(e.name),
			selectable: !b.reviewing && !!ce(e.name).length,
			status: r ? i(n) ? "review" : n.status : void 0,
			label: r ? d(n) + (!u(n) && !n.reviewed ? " · To review" : "") : void 0,
			failure: r && !i(n) ? _(n) : void 0
		};
	});
	if (t(y("#branch-list"), {
		rows: c,
		relative: fe,
		empty: b.filter === "review" && !e ? "No completed preparations need review." : "No applications found. Try another filter or create a new application.",
		onOpen: (e) => {
			let t = b.filter === "review" && b.runs.find((t) => t.branch === e && (i(t) || t.status === "succeeded" && !t.reviewed));
			t ? (async () => {
				await K(t), i(t) && await W(t);
			})().catch((e) => F(e.message, !0)) : B(e);
		},
		onSelect: (e, t) => {
			t ? b.reviewSelection.add(e) : b.reviewSelection.delete(e), L();
		}
	}), o && !y("#board").hidden && !a.isConnected) {
		let e = [...y("#branch-list").children].find((e) => e.dataset.branch === o)?.querySelector(s ? ".select-branch-review" : ".branch-row");
		(e && !e.disabled ? e : y("#search")).focus({ preventScroll: !0 });
	}
	y("#result-count").textContent = `${r.length} ${r.length === 1 ? "application" : "applications"}`, y("#total-count").textContent = b.branches.length, le();
}
async function R() {
	y("#refresh").disabled = !0, y("#new-branch").disabled = !0;
	try {
		let e = await P("/api/branches");
		b.branches = e.branches, y("#repository").textContent = e.repository, L();
	} catch (e) {
		y("#branch-list").innerHTML = `<p class="empty">${j(e.message)}</p>`;
	} finally {
		y("#refresh").disabled = !1, y("#new-branch").disabled = !b.branches.length;
	}
}
function z() {
	return !(b.dirty || b.jobDirty) || window.confirm("Discard your unsaved editor changes?");
}
async function pe(e) {
	try {
		let t = await P("/api/release-worktree", { branch: e });
		t.released ? I("Application closed. You can reopen it at any time.") : [
			"locked",
			"dirty",
			"external"
		].includes(t.reason) && (F(t.message), I(t.message));
	} catch (t) {
		I(`Couldn’t close the application folder for ${w(e)}: ${t.message}`);
	}
}
async function B(e, t = !1) {
	if (!t && !z()) return;
	C.reset(), S.reset();
	let n = b.snapshot?.branch, r = n === e ? b.historyRunId : null;
	n && n !== e && (b.filePath = null);
	let i = ++b.generation;
	y("#workspace").setAttribute("aria-busy", "true");
	for (let e of document.querySelectorAll("[data-view]")) e.disabled = !0;
	b.pdfGeneration++, b.snapshot = null, b.displayedRun = null, b.graphRunId = r, b.historyRunId = r, b.selectedTask = null, y("#task-inspector").hidden = !0, y("#cv-file").disabled = !0, y("#workflow-run").disabled = !0, o(y("#workflow-graph")), y("#selected-run").hidden = !0, y("#attempt-history").replaceChildren(), M.setDisabled(!0);
	for (let e of T.map((e) => "step-" + e)) y("#" + e).checked = !1;
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
		"review-facts",
		"mark-run-reviewed",
		"requirements-current-open",
		"requirements-captured",
		"task-requirements",
		"step-requirements"
	]) y("#" + e).disabled = !0;
	A.current.setReadOnly(!0), y("#job-description").readOnly = !0, y("#board").hidden = !0, y("#workspace").hidden = !1, document.body.classList.add("in-workspace"), y("#branch-title").textContent = w(e), F("Loading the application…");
	try {
		if (n && n !== e && await pe(n), i !== b.generation) return;
		let [t, r, a, o] = await Promise.all([
			P("/api/workspace?branch=" + encodeURIComponent(e)),
			P("/api/providers?branch=" + encodeURIComponent(e)),
			P("/api/ai-settings?branch=" + encodeURIComponent(e)),
			P("/api/connections")
		]);
		return i === b.generation ? (b.snapshot = t, b.catalog = r, b.dirty = !1, b.jobDirty = !1, b.pdfs = {}, b.pdfDocument = "cv", y("#pdf-document").value = "cv", b.pdfGeneration++, y("#review-policy").value = t.running?.reviewPolicy || "manual", M.load(e, r, a, o), N(), history.replaceState(null, "", "?branch=" + encodeURIComponent(e)), me(), U(b.view), b.view !== "structure" && F(), t) : void 0;
	} catch (e) {
		i === b.generation && F(e.message, !0);
	} finally {
		if (i === b.generation) {
			y("#workspace").removeAttribute("aria-busy"), y("#workflow-run").disabled = !b.snapshot;
			for (let e of document.querySelectorAll("[data-view]")) e.disabled = !b.snapshot;
		}
	}
}
function me() {
	let e = b.snapshot, t = V();
	if (he(), y("#branch-title").textContent = e.displayName || e.branch, y("#workspace-caption").textContent = e.editable ? "Review your CV and results, then save your application." : "This CV is view only. Use it to create a new application before editing.", y("#original-label").textContent = t.originalExists === !1 ? "File absent before" : t.path === e.path ? "" : t.path, y("#current-label").textContent = t.exists === !1 ? "Not in current CV" : t.path === e.path ? e.displayName || e.branch : t.path, y("#version-label").textContent = e.editable && t.exists !== !1 ? "Editable" : "View only", A.original.setDocument(t.original, e.branch + ":" + t.path), A.current.setDocument(t.content, e.branch + ":" + t.path), A.current.setReadOnly(!e.editable || !!e.running || t.exists === !1), _e("original", t.originalDocument), _e("current", t.document), y("#job-description").value = e.job, y("#job-description").readOnly = !e.editable || !!e.running, y("#job-state").textContent = e.job ? "Saved on this computer" : "No job description yet", y("#save-job").disabled = !e.editable || !!e.running, y("#branch-from").disabled = !!e.running, y("#compile").disabled = !1, y("#ai-dot").textContent = Object.keys(e.artifacts).length ? "•" : "", y("#ai-capability").textContent = b.session.vita ? "Prepare everything or start only the steps you choose. Your existing edits are checked before results are applied. Save any draft edits first." : "The Vita CV connection is not available. Open AI connection details for setup instructions.", y("#run-adapt").disabled = !b.session.vita || !e.editable || !!e.running || !!M.problem(q().steps), y("#ai-status").textContent = e.running?.message || (e.job ? "Ready to prepare this application." : "Add and save a job description first."), y("#application-id").textContent = e.branch, y("#worktree-path").textContent = e.worktree || "An application folder will be created when you save your first draft.", y("#diff").replaceChildren(), !t.diff) y("#diff").textContent = "No changes from the original in this file.";
	else for (let e of t.diff.split("\n")) {
		let t = document.createElement("span");
		t.textContent = e + "\n", e.startsWith("+") && !e.startsWith("+++") ? t.className = "added" : e.startsWith("-") && !e.startsWith("---") && (t.className = "removed"), y("#diff").append(t);
	}
	let n = (e.files || [e]).map((e) => e.diff).join("\n"), r = n.split("\n").filter((e) => e.startsWith("+") && !e.startsWith("+++")).length, i = n.split("\n").filter((e) => e.startsWith("-") && !e.startsWith("---")).length;
	y("#change-count").textContent = r || i ? `+${r} −${i}` : "", y("#artifacts").replaceChildren(), Object.keys(e.artifacts).length || (y("#artifacts").innerHTML = "<p class=\"helper\">No results yet. Choose the steps you want to prepare your application.</p>");
	for (let [t, n] of Object.entries(e.artifacts)) y("#artifacts").append(p(n.path, n.content, { open: t === "analyze" }));
	if (e.coverOutputs && y("#artifacts").append(h(e.coverOutputs)), J(), Y(), e.cover) {
		let e = document.createElement("button");
		e.id = "open-cover-pdf", e.textContent = "Open cover-letter PDF", e.onclick = () => Pe(), y("#artifacts").prepend(e);
	}
	H();
}
function V() {
	let e = b.snapshot;
	return e ? e.files?.find((e) => e.path === b.filePath) || e.files?.find((t) => t.path === e.path) || e : null;
}
function he() {
	let e = b.snapshot, t = V();
	b.filePath = t.path, y("#cv-file").disabled = !1, y("#cv-file").replaceChildren(...(e.files || [e]).map((e) => {
		let t = document.createElement("option");
		return t.value = e.path, t.textContent = e.path + (e.exists === !1 ? " · unavailable" : "") + (e.diff ? " · changed" : ""), t;
	})), y("#cv-file").value = t.path, y("#include-problems").hidden = !e.includeDiagnostics?.length, y("#include-diagnostics").replaceChildren(...(e.includeDiagnostics || []).map((t) => {
		let n = document.createElement("li");
		n.textContent = t.message;
		let r = t.sourcePath || t.path;
		if (e.files.some((e) => e.path === r)) {
			let e = document.createElement("button");
			e.className = "quiet", e.textContent = "Open " + r, e.onclick = () => ge(r, "source"), n.append(" ", e);
		}
		return n;
	}));
}
function ge(e, t = b.view) {
	b.snapshot && (z() ? (b.filePath = e, b.dirty = !1, b.jobDirty = !1, me(), U(t)) : y("#cv-file").value = b.filePath);
}
y("#cv-file").onchange = (e) => ge(e.target.value);
function _e(e, t) {
	let n = y(`#${e}-document .cv-document`);
	n.innerHTML = t.error ? `<p class="empty">Structure cannot preview this template. Use Source or PDF preview to view it.</p><details class="technical-details"><summary>Structure details</summary><pre>${j(t.error)}</pre></details>` : t.html;
}
function H() {
	x.summary(b.displayedRun);
	let e = b.snapshot;
	y("#save-state").textContent = b.dirty || b.jobDirty ? "Unsaved changes" : e?.saveState?.draft ? "Draft saved on this computer" : e && b.syncedCommits.get(e.branch) === e.commit ? "Saved and synced" : e?.saveState?.ahead === 0 ? "Saved" : "Saved on this computer · sync pending", y("#save-source").disabled = !b.dirty || !b.snapshot?.editable || !!b.snapshot?.running || V()?.exists === !1, y("#commit-push").disabled = !b.snapshot?.editable || !!b.snapshot?.running || b.publishing;
}
function U(e) {
	b.view = e, y("#file-navigation").hidden = ![
		"structure",
		"source",
		"changes"
	].includes(e), document.querySelectorAll("[data-view]").forEach((t) => {
		t.setAttribute("aria-selected", String(t.dataset.view === e)), t.tabIndex = t.dataset.view === e ? 0 : -1;
	}), b.snapshot && history.replaceState(null, "", "?" + new URLSearchParams({
		branch: b.snapshot.branch,
		view: e
	})), y("#comparison").hidden = ![
		"structure",
		"source",
		"pdf"
	].includes(e) || e === "pdf" && b.pdfDocument === "cover", y("#cover-pdf-pane").hidden = e !== "pdf" || b.pdfDocument !== "cover", y("#compile").textContent = b.pdfDocument === "cover" ? "Create cover-letter PDF" : "Create PDF previews", y("#structure-hint").hidden = e !== "structure", y("#pdf-toolbar").hidden = e !== "pdf", y("#changes-panel").hidden = e !== "changes", y("#ai-panel").hidden = e !== "ai", y("#document-actions").hidden = !1, y("#save-source").hidden = ["ai", "pdf"].includes(e);
	for (let t of ["original", "current"]) y(`#${t}-document`).hidden = e !== "structure", y(`#${t}-source`).hidden = e !== "source", y(`#${t}-pdf`).hidden = e !== "pdf";
	if (e === "source") for (let e of Object.values(A)) e.refresh();
	if (!b.snapshot) return;
	let t = V(), n = b.snapshot;
	if (y("#original-label").textContent = e === "pdf" || t.path === n.path ? "" : t.path, y("#current-label").textContent = e === "pdf" || t.path === n.path ? n.displayName || n.branch : t.path, y("#version-label").textContent = e !== "pdf" && n.editable && t.exists !== !1 ? "Editable" : "View only", e === "structure") {
		let e = V(), t = [.../* @__PURE__ */ new Set([...e.document.warnings, ...e.originalDocument.warnings])];
		F(b.dirty ? "The reading view shows the saved version. Save your draft to update this view." : t.join("\n"));
	} else if (e === "pdf") {
		F(b.dirty ? "PDF previews use your saved draft. Save your changes first." : "");
		for (let e of b.pdfDocument === "cover" ? ["cover"] : ["original", "current"]) b.pdfs[e] || (y(`#${e}-pdf`).innerHTML = "<p class=\"pdf-message\">Create a PDF preview to see the final layout.<br>Text will remain selectable.</p>");
	} else F();
}
async function ve() {
	if (!b.dirty || !b.snapshot) return;
	if (b.jobDirty) {
		F("Save the job description draft first.", !0);
		return;
	}
	let e = b.snapshot, t = V(), n = A.current.value;
	y("#save-source").disabled = !0, A.current.setReadOnly(!0), y("#job-description").readOnly = !0, y("#save-job").disabled = !0;
	try {
		await P("/api/save", {
			branch: e.branch,
			path: t.path,
			revision: t.revision,
			projectRevision: e.projectRevision,
			content: n
		}), await B(e.branch, !0), I("CV draft saved on this computer");
	} catch (t) {
		F(t.message, !0), A.current.setReadOnly(!e.editable || V()?.exists === !1), y("#job-description").readOnly = !1, y("#save-job").disabled = !1, H();
	}
}
async function ye() {
	if (!b.snapshot) return;
	let e = b.snapshot;
	y("#save-job").disabled = !0;
	try {
		let t = await P("/api/save", {
			branch: e.branch,
			path: "job.md",
			revision: e.jobRevision,
			content: y("#job-description").value
		});
		e.job = t.content, e.jobRevision = t.revision, b.jobDirty = !1, y("#job-state").textContent = "Saved on this computer", e.saveState = t.saveState || {
			...e.saveState,
			draft: !0
		}, H(), I("Job description draft saved");
	} catch (e) {
		F(e.message, !0);
	} finally {
		y("#save-job").disabled = !e.editable;
	}
}
function be() {
	let e = b.snapshot, t = {
		branch: e.branch,
		sourceRevision: e.revision,
		jobRevision: e.jobRevision
	};
	return b.dirty && (t.sourceContent = A.current.value), b.jobDirty && (t.jobContent = y("#job-description").value), t;
}
function xe(e, { retry: t = !1 } = {}) {
	b.commitReview = e, y("#commit-branch").textContent = w(e.branch), y("#commit-destination").textContent = e.destinationLabel || (e.remote ? "Connected destination" : "No sync destination connected"), y("#sync-details").textContent = e.destination || "Not connected", y("#commit-files").replaceChildren(...e.files.map((e) => {
		let t = document.createElement("li");
		return t.innerHTML = `<div>${j(m(e.path))}<details class="technical-details"><summary>File details</summary><code>${j(e.path)}</code></details></div><span class="commit-file-status">${{
			Added: "New",
			Modified: "Updated",
			Deleted: "Removed",
			Untracked: "New"
		}[e.status] || e.status}</span>`, t;
	})), y("#commit-files").hidden = !e.files.length, y("#commit-empty").hidden = !!e.files.length, y("#commit-empty").textContent = e.ahead > 0 ? `${e.ahead} saved ${e.ahead === 1 ? "version" : "versions"} will be synced.` : e.ahead === 0 ? "No new edits or versions are waiting to sync. Save will check the connection." : "No new edits. This application will be synced to the connected destination.", y("#commit-excluded").hidden = !e.excludedChanges, y("#commit-excluded").textContent = e.excludedChanges ? `${e.excludedChanges} other ${e.excludedChanges === 1 ? "file will" : "files will"} remain unchanged.` : "", y("#commit-message").disabled = !e.files.length, y("#commit-message").required = !!e.files.length, e.files.length && !y("#commit-message").value && (y("#commit-message").value = `Update CV for ${w(e.branch)}`), y("#confirm-commit").textContent = t ? "Retry sync" : "Save", y("#confirm-commit").disabled = !e.remote, e.remote || (y("#commit-error").textContent = "No sync destination is connected. Check your connection setup before saving.");
}
async function Se(e = {}) {
	let t = await P("/api/commit-preview", be());
	return xe(t, e), t;
}
async function Ce() {
	if (b.snapshot && !b.snapshot.running) {
		if (b.dirty && V().path !== b.snapshot.path) {
			if (b.jobDirty) {
				F("Save your CV and job description drafts first.", !0);
				return;
			}
			if (await ve(), b.dirty) return;
		}
		y("#commit-push").disabled = !0, y("#commit-error").textContent = "", y("#commit-progress").textContent = "Checking your changes…", y("#commit-message").value = "";
		try {
			await Se(), y("#commit-progress").textContent = "Review these changes before saving and syncing.", y("#commit-dialog").showModal(), b.commitReview.files.length && y("#commit-message").focus();
		} catch (e) {
			F(e.message, !0);
		} finally {
			H();
		}
	}
}
y("#commit-form").onsubmit = async (e) => {
	if (e.preventDefault(), b.publishing) return;
	b.publishing = !0;
	let t = e.submitter || y("#confirm-commit");
	t.disabled = !0, y("#commit-error").textContent = "", y("#commit-progress").textContent = b.commitReview.files.length ? "Saving and syncing…" : "Syncing saved versions…", document.querySelectorAll("#commit-dialog .close-dialog").forEach((e) => e.disabled = !0), H();
	try {
		let e = await P("/api/commit-push", {
			...be(),
			message: y("#commit-message").value,
			review: b.commitReview.review
		});
		b.syncedCommits.set(e.branch, e.commit), y("#commit-dialog").close(), b.dirty = !1, b.jobDirty = !1, await B(e.branch, !0), await R(), I("Application saved and synced.");
	} catch (e) {
		if (y("#commit-error").textContent = (e.commitCreated && e.commit ? "Your changes were saved on this computer. " : "") + e.message, e.canRetry) try {
			await B(b.snapshot.branch, !0), await Se({ retry: !0 }), y("#commit-progress").textContent = "Your saved version is safe. Check the connection and retry syncing.";
		} catch (e) {
			y("#commit-error").textContent += "\n" + e.message;
		}
		else y("#commit-progress").textContent = "Nothing was synced.";
	} finally {
		b.publishing = !1, document.querySelectorAll("#commit-dialog .close-dialog").forEach((e) => e.disabled = !1), t.disabled = !b.commitReview?.remote, H();
	}
}, y("#commit-dialog").addEventListener("cancel", (e) => {
	b.publishing && e.preventDefault();
});
async function we() {
	z() && (b.branches.length ? (y("#base-branch").innerHTML = b.branches.map((e) => `<option value="${j(e.name)}">${j(e.displayName || e.name)}</option>`).join(""), y("#base-branch").value = b.snapshot?.branch || b.branches.find((e) => e.current)?.name || b.branches[0]?.name || "", y("#create-error").textContent = "", y("#create-dialog").showModal(), y("#branch-name").focus()) : I("Wait for your saved CVs to load, then try again."));
}
y("#create-form").onsubmit = async (e) => {
	e.preventDefault();
	let t = e.submitter;
	t.disabled = !0;
	try {
		let e = y("#base-branch").value, t = await P("/api/workspace?branch=" + encodeURIComponent(e)), n = await P("/api/create", {
			base: e,
			applicationName: y("#branch-name").value.trim(),
			job: y("#new-job").value,
			revision: t.revision,
			projectRevision: t.projectRevision
		});
		y("#create-dialog").close(), b.dirty = !1, b.jobDirty = !1, await R(), b.view = "structure", await B(n.branch, !0), I("Application created with your CV and job description"), y("#create-form").reset();
	} catch (e) {
		y("#create-error").textContent = e.message;
	} finally {
		t.disabled = !1;
	}
}, y("#current-document").ondblclick = (e) => {
	let t = e.target.closest("[data-leaf]");
	if (!t || !b.snapshot?.editable) return;
	if (b.dirty || b.jobDirty) {
		F("Save your CV and job description drafts before editing this view.", !0);
		return;
	}
	if (b.snapshot.running) {
		F("Wait for this preparation to finish before editing.", !0);
		return;
	}
	if (V().exists === !1) return;
	b.leaf = t.dataset.leaf;
	let n = V().document.leaves[b.leaf];
	b.editOrigin = {
		path: n.path,
		revision: V().revision,
		projectRevision: b.snapshot.projectRevision
	}, y("#edit-origin").textContent = `${n.path} · characters ${n.start}–${n.end}`, y("#edit-text").value = n.text, y("#edit-error").textContent = "", y("#edit-dialog").showModal(), y("#edit-text").focus();
}, y("#edit-form").onsubmit = async (e) => {
	e.preventDefault(), e.submitter.disabled = !0;
	let t = b.snapshot;
	try {
		await P("/api/save", {
			branch: t.branch,
			...b.editOrigin,
			leaf: b.leaf,
			text: y("#edit-text").value
		}), y("#edit-dialog").close(), await B(t.branch, !0), I("CV draft updated on this computer");
	} catch (e) {
		y("#edit-error").textContent = e.message;
	} finally {
		e.submitter.disabled = !1;
	}
};
async function W(e) {
	if (e && !b.openingRunId) {
		b.openingRunId = e.id, Y();
		try {
			e.source === "jobenu" ? await E.reviewRun(e) : e.requirementsApprovalNeeded ? await S.open() : e.factualReview?.state === "pending" && await C.open(e);
		} finally {
			b.openingRunId = null, Y();
		}
	}
}
async function Te(e, t) {
	if (b.snapshot !== t) return e;
	if (t.running = e, b.graphRunId = e.id, b.historyRunId = null, await k.refresh(), b.snapshot === t) {
		let t = b.runs.find((t) => t.id === e.id) || e;
		u(t) || await De(b.runs.some((t) => t.id === e.id) ? b.runs : [e, ...b.runs]);
	}
	return b.snapshot && (Y(), J(), H()), b.runs.find((t) => t.id === e.id) || e;
}
async function Ee(e, t = b.snapshot?.branch) {
	let n = b.snapshot;
	if (!n || n.branch !== t || b.dirty || b.jobDirty) throw Error("Approval saved. Reopen this application with saved drafts to continue.");
	let r = e ? b.runs.find((t) => t.id === e) : b.runs.find((e) => e.branch === t && e.requirementsDraft && !u(e));
	if (!e && !r) {
		await k.refresh();
		return;
	}
	let i = await Te(await P("/api/review-continue", {
		id: e || r.id,
		revision: n.revision,
		jobRevision: n.jobRevision
	}), n);
	b.snapshot?.branch === t && F(u(i) ? "Approved. Continuing preparation…" : i.message);
}
async function G(e = q().steps) {
	if (!b.snapshot || b.snapshot.running || b.launching) return;
	if (!e.length) {
		F("Select at least one step.", !0);
		return;
	}
	if (b.dirty || b.jobDirty) {
		F("Save your CV and job description before starting AI.", !0);
		return;
	}
	b.launching = !0, y("#run-adapt").disabled = !0, y("#run-all").disabled = !0, y("#task-run").disabled = !0, A.current.setReadOnly(!0), y("#job-description").readOnly = !0, y("#save-job").disabled = !0, y("#branch-from").disabled = !0;
	let t = b.snapshot;
	N();
	for (let e of T.map((e) => "step-" + e)) y("#" + e).disabled = !0;
	try {
		let n = M.problem(e);
		if (n) throw Error(n);
		let r = await P("/api/adapt", {
			branch: t.branch,
			revision: t.revision,
			jobRevision: t.jobRevision,
			aiConfig: M.value(),
			language: y("#language").value,
			workflow: { steps: e },
			engine: x.engine(),
			reviewPolicy: y("#review-policy").value
		});
		t.running = r, b.snapshot === t && (b.graphRunId = r.id, b.historyRunId = null, N(), J(), Y(), H(), y("#ai-status").textContent = r.message), await k.refresh();
	} catch (e) {
		b.snapshot === t && (F(e.message, !0), J(), A.current.setReadOnly(!t.editable || V()?.exists === !1), y("#job-description").readOnly = !t.editable, y("#save-job").disabled = !t.editable, y("#branch-from").disabled = !1);
	} finally {
		b.launching = !1, b.snapshot && (N(), J(), Y());
	}
}
async function De(e) {
	let t = e.filter((e) => !u(e) && b.runs.some((t) => t.id === e.id && u(t)));
	t.length && I(`${w(t[0].branch)}: ${d(t[0])}${t.length > 1 ? ` · ${t.length - 1} more updates` : ""}`), b.runs = e, L();
	let n = b.snapshot;
	if (!n) return;
	n.nativeRuns = e.filter((e) => e.source === "jobenu" && e.branch === n.branch), Y();
	let r = e.find((e) => e.branch === n.branch && u(e));
	if (r) {
		n.running = r, y("#ai-status").textContent = r.message, A.current.setReadOnly(!0), y("#job-description").readOnly = !0;
		for (let e of [
			"save-job",
			"run-adapt",
			"run-all",
			"task-run",
			"branch-from"
		]) y("#" + e).disabled = !0;
		N(), J(), Y(), H();
	} else if (n.running) {
		let t = e.find((e) => e.id === n.running.id);
		n.running = null, !b.dirty && !b.jobDirty && !b.publishing ? await B(n.branch, !0) && t && (y("#ai-status").textContent = t.message, F(t.message, t.status !== "succeeded" && !i(t))) : (A.current.setReadOnly(!n.editable || V()?.exists === !1), y("#job-description").readOnly = !n.editable, y("#save-job").disabled = !n.editable, y("#branch-from").disabled = !1, N(), H(), J(), F("The preparation finished. Your unsaved edits are safe; refresh to review the results.", !0));
	}
}
async function K(e) {
	if (!z()) return;
	let t = b.snapshot, n = t?.branch === e.branch && !t.running && !b.dirty && !b.jobDirty ? t : await B(e.branch, !0);
	if (n) {
		if (b.graphRunId = e.id, b.historyRunId = e.id, Y(), U("ai"), y("#ai-status").textContent = e.message, e.source === "jobenu") y("#selected-run").hidden = !0, F("Showing the application’s current reports. Jobenu component history is recorded separately; use Import details for logs and continuation."), y("#ai-panel").scrollIntoView({ block: "start" });
		else {
			if (!u(e)) {
				let t = await P("/api/job-result?id=" + encodeURIComponent(e.id));
				if (b.snapshot !== n) return;
				let r = [e.provider ? M.summary(e) : "", [...y("#language").options].find((t) => t.value === e.language)?.textContent || e.language].filter(Boolean).join(" · ");
				y("#selected-run").hidden = !1, y("#selected-run-info").textContent = `${l(e)} · ${d(e)} · ${(/* @__PURE__ */ new Date(e.createdAt * 1e3)).toLocaleString()} · ${e.provider ? r : "Local checks; no AI used"} · ${Math.round(e.elapsedSeconds || 0)}s. Results from this preparation. Your application may contain newer edits.`, Ae(t), y("#selected-run-files").replaceChildren();
				for (let [e, n] of Object.entries(t.files)) y("#selected-run-files").append(p(e, n, {
					open: /analy(sis|ze)\.md$/.test(e),
					label: t.inputs?.includes(e) ? `Starting material · ${m(e)}` : m(e)
				}));
				if (Object.keys(t.files).length || (y("#selected-run-files").textContent = "This preparation did not produce any results."), t.coverPdf) {
					let e = document.createElement("button");
					e.id = "open-run-cover-pdf", e.textContent = "Open generated cover-letter PDF", e.onclick = () => Pe(t.coverPdf.runId), y("#selected-run-files").prepend(e);
				}
				t.coverOutputs && y("#selected-run-files").append(h(t.coverOutputs));
			}
			y("#ai-panel").scrollIntoView({ block: "start" });
		}
	}
}
function q() {
	return { steps: T.filter((e) => y("#step-" + e).checked) };
}
function J() {
	let e = b.snapshot, t = b.session.workflow || {}, n = e.running?.stages?.length ? e.running.stages.filter((e) => e.status !== "skipped").map((e) => e.id) : b.workflowChoices.get(e.branch)?.steps || [
		"analyze",
		"adapt",
		...t.review ? ["review"] : []
	];
	for (let t of T) {
		let r = y("#step-" + t);
		r.checked = n.includes(t) && D(t), r.disabled = !D(t) || !!e.running || !!b.launching || !e.editable, D(t) || (y("#hint-" + t).textContent = "Update Vita CV to use this step.");
	}
	let r = M.problem(q().steps), i = !b.session.vita || !e.editable || !!e.running || !!b.launching || !!r;
	y("#ai-config-validation").textContent = r, y("#ai-config-validation").hidden = !r, y("#run-adapt").textContent = "Start selected steps", y("#run-adapt").disabled = i || !q().steps.length, y("#run-all").disabled = i || !!M.problem(T.filter(D)), M.refresh();
}
function Y() {
	if (!b.snapshot) return;
	let e = [...new Map([...b.snapshot.nativeRuns || [], ...b.runs.filter((e) => e.branch === b.snapshot.branch)].map((e) => [e.id, e])).values()].sort((e, t) => t.createdAt - e.createdAt), t = b.graphRunId || b.snapshot.running?.id || e[0]?.id || "draft", n = y("#workflow-run");
	n.replaceChildren(new Option("New preparation", "draft"), ...e.map((e) => new Option(`${e.attempt ? "Attempt " + e.attempt + " · " : ""}${(/* @__PURE__ */ new Date(e.createdAt * 1e3)).toLocaleString()} — ${l(e)} · ${d(e)}${e.source === "jobenu" || u(e) ? "" : e.reviewed ? " · Reviewed" : " · Needs review"}`, e.id)));
	let r = e.find((e) => e.id === t) || (b.snapshot.running?.id === t ? b.snapshot.running : null);
	r && !e.some((e) => e.id === r.id) && n.add(new Option("Current preparation", r.id)), n.value = r ? r.id : "draft", b.displayedRun = r, x.summary(r);
	let o = r && !u(r);
	for (let e of [
		"requirements-current-open",
		"requirements-captured",
		"task-requirements",
		"step-requirements"
	]) y("#" + e).disabled = !1;
	y("#requirements-captured").hidden = !r?.requirementsRevision && !r?.requirementsDraft, y("#requirements-captured").textContent = r?.requirementsRevision ? "Requirements used · " + r.requirementsRevision.slice(0, 12) + (r.requirementsStatus && r.requirementsStatus !== "current" ? " · needs update" : "") : "Review job requirements", y("#review-facts").hidden = !o || !r?.factualReview, y("#review-facts").disabled = !!b.snapshot.running || !!b.launching || !!b.openingRunId, y("#review-facts").textContent = r?.factualReview?.state === "resolved" ? "View factual decisions" : "Review factual changes", y("#inspect-run").hidden = !r, y("#inspect-step").hidden = !r, y("#inspect-step-dialog").hidden = !r, r?.source === "jobenu" ? (y("#inspect-run").textContent = "Import details", y("#inspect-step").hidden = !0, y("#inspect-step-dialog").hidden = !0) : y("#inspect-run").textContent = "Execution details", y("#resume-run").hidden = !r?.resumeAvailable, y("#resume-run").disabled = !!b.snapshot.running || !!b.launching || !!b.retryPlanning || !b.snapshot.editable, y("#view-run").hidden = !o, y("#view-run").disabled = !!b.openingRunId, y("#view-run").textContent = b.openingRunId ? "Opening results…" : "View results";
	let s = y("#mark-run-reviewed");
	s.hidden = !o || r?.source === "jobenu", s.disabled = !!r?.reviewed || !!b.reviewingRunId, s.textContent = r?.reviewed ? "Reviewed" : b.reviewingRunId === r?.id ? "Saving review…" : "Mark as reviewed", y("#workflow-summary").textContent = r ? r.factualReview ? r.message : _(r) || r.message : "Choose the steps for your next preparation. Only selected AI steps will use your AI service.", r?.reviewPolicy === "automatic" && (y("#workflow-summary").textContent += " Automatic approvals selected for this preparation."), r?.contextInvalidated && (y("#workflow-summary").textContent += " Earlier analysis did not match the captured inputs and was excluded. Select Check CV match to refresh it."), a(y("#workflow-graph"), {
		run: r,
		history: e,
		options: q(),
		available: b.session.workflow,
		selected: b.selectedTask,
		select: ke,
		config: r?.stepConfig || Object.fromEntries(T.map((e) => [e, M.route(e)]))
	});
	let c = !!b.snapshot.running || !!b.launching || !!b.openingRunId, f = y("#workflow-next");
	f.disabled = c || !r && y("#run-adapt").disabled, y("#workflow-run-one").disabled = c || !b.snapshot.editable, f.textContent = r?.requirementsApprovalNeeded ? "Review job requirements" : r?.factualReview?.state === "pending" ? "Review CV changes" : r?.resumeAvailable ? "Continue preparation" : o && r.status === "succeeded" ? "Preview your PDF" : "Start selected steps", y("#workflow-action").dataset.state = i(r) ? "review" : r?.status === "failed" ? "failed" : "ready", y("#workflow-next-help").textContent = i(r) ? "One review, then the remaining steps continue automatically." : r?.status === "failed" ? _(r) || r.message : o && r.status === "succeeded" ? "Your application is updated. Check the final layout before saving." : "If AI review and cover letter are both selected, review runs first.", r?.source === "jobenu" && (f.textContent = i(r) ? r.pendingStep === "extract" ? "Review requirements" : "Review changes" : r.status === "failed" ? "Start selected steps" : "Open import activity", y("#workflow-next-help").textContent = r.status === "failed" ? "Start a new preparation with your current AI setup. The imported attempt keeps its captured settings." : r.message), b.openingRunId && (f.textContent = "Opening review…"), y("#review-policy").disabled = !!b.snapshot.running || !!b.launching, b.selectedTask && Oe();
}
function Oe() {
	let t = s(b.displayedRun, q(), b.session.workflow).find((e) => e.id === b.selectedTask);
	if (!t) return;
	y("#task-inspector").hidden = !1, y("#task-title").textContent = t.title;
	let r = b.displayedRun?.stepConfig?.[t.id] || (!b.displayedRun && t.id !== "validating" ? M.route(t.id) : null);
	y("#task-description").textContent = t.detail + (r ? " AI setup: " + M.summary(r) + ". Connection: " + M.connectionName(r) + "." : t.id === "validating" ? " This step runs locally without an AI model." : ""), y("#task-status").textContent = `${n[t.status] || t.status} · ${t.output}`, y("#task-output").textContent = t.id === "validating" ? "Compare current CVs" : t.id === "adapt" ? "View CV source" : "View results";
	let i = e(b.displayedRun, t.id);
	y("#task-run").textContent = i ? t.id === "extract" ? "Review requirements" : "Review changes" : t.id === "validating" ? "Check current changes" : "Start this step", y("#task-requirements").hidden = t.id !== "extract", y("#task-configure").hidden = t.id === "validating", y("#task-configure").textContent = b.displayedRun ? "Configure next run" : "Configure AI", y("#task-configure").disabled = !!b.snapshot.running || !!b.launching || !b.snapshot.editable, y("#task-run").disabled = i ? !!b.snapshot.running || !!b.launching || !!b.openingRunId : !b.snapshot.editable || !!b.snapshot.running || !!b.launching || !D(t.id) || t.id !== "validating" && (!b.session.vita || !!M.problem([t.id])), y("#task-output").disabled = u(b.displayedRun) || !["succeeded", "unknown"].includes(t.status), v(b.displayedRun, t.id) && (y("#task-status").textContent = v(b.displayedRun, t.id)), u(b.displayedRun) && (y("#task-status").textContent += " · Results open after the preparation finishes.");
}
function ke(t) {
	if (b.snapshot) {
		if (b.selectedTask = t.id, Y(), e(b.displayedRun, t.id)) return W(b.displayedRun).catch((e) => F(e.message, !0));
		T.includes(t.id) && M.openStep(t.id, {
			history: !!b.displayedRun,
			recorded: b.displayedRun?.stepConfig?.[t.id],
			readOnly: !!b.snapshot.running || !!b.launching || !b.snapshot.editable,
			allowNext: !b.snapshot.running && !b.launching && b.snapshot.editable
		});
	}
}
y("#workflow-next").onclick = () => {
	let e = b.displayedRun;
	if (i(e)) return W(e).catch((e) => F(e.message, !0));
	if (e?.source === "jobenu") return e.status === "failed" ? G(q().steps) : E.open();
	if (e?.requirementsApprovalNeeded) return S.open().catch((e) => F(e.message, !0));
	if (e?.factualReview?.state === "pending") return C.open(e).catch((e) => F(e.message, !0));
	if (e?.resumeAvailable) return b.resumeCaptured = !0, y("#resume-current-config").checked = !1, Z();
	if (e?.status === "succeeded") {
		U("pdf");
		return;
	}
	let t = q().steps;
	if (M.problem(t) || !b.snapshot.job.trim()) U("ai"), y("#ai-panel").scrollIntoView({ block: "start" }), F("Add the job description and choose your AI setup, then prepare the application.");
	else return G(t);
}, y("#workflow-run-one").onclick = () => {
	let e = y("#workflow-step-picker");
	y("#workflow-step-choice").replaceChildren(...s(null, q(), b.session.workflow).filter((e) => D(e.id)).map((e) => new Option(e.title, e.id))), e.returnValue = "", e.showModal();
}, y("#workflow-step-picker").onclose = (e) => {
	e.currentTarget.returnValue === "run" && G([y("#workflow-step-choice").value]);
}, y("#view-run").onclick = async () => {
	let e = b.displayedRun;
	if (!(!e || u(e) || b.openingRunId)) {
		b.openingRunId = e.id, Y();
		try {
			await K(e);
		} catch (e) {
			F(e.message, !0);
		} finally {
			b.openingRunId = null, Y();
		}
	}
};
function X(e) {
	return s(null, {}, {}).find((t) => t.id === e)?.title || e;
}
for (let e of [
	"task-requirements",
	"step-requirements",
	"requirements-current-open"
]) y("#" + e).onclick = () => S.open().catch((e) => F(e.message, !0));
y("#requirements-captured").onclick = () => S.open(b.displayedRun?.requirementsRevision ? b.displayedRun : null).catch((e) => F(e.message, !0)), y("#review-facts").onclick = () => {
	b.displayedRun && C.open(b.displayedRun).catch((e) => F(e.message, !0));
};
function Ae(e) {
	let t = y("#attempt-history");
	t.replaceChildren();
	let n = document.createElement("h3");
	n.textContent = "Attempt history", t.append(n);
	let r = document.createElement("p");
	r.className = "helper", r.textContent = e.run.checkpointSteps?.length ? "Verified results retained: " + e.run.checkpointSteps.map(X).join(", ") + "." : "No verified checkpoints retained. A retry will run every selected step again.", t.append(r);
	for (let n of e.attemptHistory || [e.run]) {
		let r = document.createElement("div");
		r.className = "attempt-row";
		let i = document.createElement("button");
		if (i.type = "button", i.className = "quiet", i.textContent = `Attempt ${n.attempt || 1} · ${d(n)}${n.id === e.run.id ? " · Viewing" : ""}`, i.disabled = n.id === e.run.id, i.onclick = () => K(n).catch((e) => F(e.message, !0)), r.append(i), n.requirementsRevision || n.requirementsDraft) {
			let e = document.createElement("button");
			e.textContent = "Requirements " + (n.requirementsRevision || n.requirementsDraft) + (n.requirementsStatus && n.requirementsStatus !== "current" ? " · needs update" : ""), e.onclick = () => S.open(n).catch((e) => F(e.message, !0)), r.append(e);
		}
		if (n.factualReview) {
			let e = document.createElement("button");
			e.type = "button", e.textContent = n.factualReview.state === "resolved" ? "View factual decisions" : "Review factual changes", e.onclick = () => C.open(n).catch((e) => F(e.message, !0)), r.append(e);
		}
		if (n.parentRunId) {
			let t = document.createElement("span");
			t.className = "helper", t.textContent = "Continues attempt " + ((e.attemptHistory || []).find((e) => e.id === n.parentRunId)?.attempt || "unknown") + " · " + (n.configurationChanged ? "Changed setup" : "Captured setup preserved"), r.append(t);
		}
		for (let [e, t] of Object.entries(n.outcomes || {})) {
			let i = document.createElement("p");
			i.className = "helper", i.textContent = X(e) + ": " + (t.status === "success" ? "Completed" : "Could not finish") + (t.backend?.attempts?.length ? " · AI attempts: " + t.backend.attempts.map((e) => `${e.number}: ${e.category.replaceAll("_", " ")}`).join("; ") : ""), r.append(i);
			let a = v(n, e);
			if (a) {
				let e = document.createElement("p");
				e.className = "provider-failure", e.textContent = a, r.append(e);
			}
		}
		t.append(r);
	}
}
async function Z() {
	let e = b.displayedRun, t = b.snapshot;
	if (!(!e?.resumeAvailable || b.retryPlanning || b.launching)) {
		if (b.dirty || b.jobDirty) F("Save your CV and job description drafts before retrying.", !0);
		else {
			b.retryPlanning = !0, y("#confirm-resume").disabled = !0, y("#resume-current-config").disabled = !0, Y();
			try {
				let n = b.resumeCaptured && !y("#resume-current-config").checked, r = {
					id: e.id,
					revision: t.revision,
					jobRevision: t.jobRevision,
					...n ? {} : {
						aiConfig: M.value(),
						language: y("#language").value
					}
				}, i = await P("/api/resume-preview", r);
				if (b.snapshot !== t) return;
				b.resumeReview = {
					request: r,
					plan: i,
					snapshot: t
				}, y("#resume-summary").textContent = `Attempt ${i.attempt}, continuing attempt ${e.attempt || 1}. Output language: ${[...y("#language").options].find((t) => t.value === (n ? e.language : y("#language").value))?.textContent || e.language}. Captured TeX engine: ${e.compileEngine || "auto"}. ${n ? "Preserves the AI setup and language captured for this preparation." : "Uses the AI setup currently shown for this application."}`, y("#resume-config-choice").hidden = !b.resumeCaptured, y("#resume-reuse").textContent = i.reuse.length ? i.reuse.map(X).join(", ") : "None. Start again with the current inputs and setup.", y("#resume-rerun").textContent = [...i.rerun.map(X), "Final checks"].join(", "), y("#resume-adapted").hidden = !i.reuse.includes("adapt"), y("#resume-error").textContent = "", y("#confirm-resume").disabled = !1, y("#resume-dialog").open || y("#resume-dialog").showModal();
			} catch (e) {
				b.resumeReview = null, y("#confirm-resume").disabled = !0, y("#resume-error").textContent = e.message, F(e.message, !0), b.resumeCaptured && (y("#resume-config-choice").hidden = !1, y("#resume-summary").textContent = "The captured setup could not be checked. Reconnect the account in this application, then explicitly choose its current setup, or cancel and review the error.", y("#resume-reuse").textContent = "Not verified. A valid retry plan is required before starting.", y("#resume-rerun").textContent = "Not planned yet.", y("#resume-adapted").hidden = !0, y("#resume-dialog").open || y("#resume-dialog").showModal());
			} finally {
				b.retryPlanning = !1, y("#resume-current-config").disabled = !1, Y();
			}
		}
	}
}
y("#resume-run").onclick = () => {
	b.resumeCaptured = !0, y("#resume-current-config").checked = !1, Z();
}, y("#resume-current-config").onchange = () => Z(), y("#resume-form").onsubmit = async (e) => {
	e.preventDefault();
	let t = b.resumeReview;
	if (t && !b.launching) {
		b.launching = !0, y("#confirm-resume").disabled = !0, Y(), J();
		try {
			let e = await P("/api/resume", {
				...t.request,
				token: t.plan.token
			});
			y("#resume-dialog").close(), y("#selected-run").hidden = !0, await Te(e, t.snapshot);
		} catch (e) {
			y("#resume-error").textContent = e.message;
		} finally {
			b.launching = !1, y("#confirm-resume").disabled = !1, J(), Y();
		}
	}
}, y("#resume-dialog").onclose = () => {
	b.launching || (b.resumeReview = null);
}, y("#cleanup-checkpoints").onclick = async () => {
	let e = y("#cleanup-checkpoints");
	e.disabled = !0;
	try {
		let e = await P("/api/checkpoints-cleanup", {});
		y("#cleanup-checkpoints-status").textContent = `Removed checkpoints for ${e.removed.length} preparations. ${e.retainedRuns} retained. Your drafts and review results are unchanged.`, await k.refresh(), Y();
	} catch (e) {
		y("#cleanup-checkpoints-status").textContent = e.message;
	} finally {
		e.disabled = !1;
	}
}, y("#mark-run-reviewed").onclick = async () => {
	let e = b.displayedRun;
	if (!(!e || u(e) || e.reviewed || b.reviewingRunId)) {
		b.graphRunId = e.id, b.reviewingRunId = e.id, Y(), F();
		try {
			let t = await P("/api/job-reviewed", { id: e.id });
			b.runs = b.runs.map((e) => e.id === t.id ? t : e), L(), Y(), I("Run marked as reviewed."), await k.refresh();
		} catch (e) {
			F(e.message, !0);
		} finally {
			b.reviewingRunId = null, Y();
		}
	}
}, y("#workflow-run").onchange = () => {
	b.graphRunId = y("#workflow-run").value, b.historyRunId = b.graphRunId, Y();
};
for (let e of T) y("#step-" + e).onchange = () => {
	b.workflowChoices.set(b.snapshot.branch, q()), b.graphRunId = "draft", b.historyRunId = null, J(), Y();
};
y("#task-run").onclick = () => e(b.displayedRun, b.selectedTask) ? W(b.displayedRun).catch((e) => F(e.message, !0)) : G([b.selectedTask]), y("#task-configure").onclick = () => M.openStep(b.selectedTask), y("#run-all").onclick = () => G(T.filter(D)), y("#toggle-workflow").onclick = () => {
	let e = y("#workflow-body");
	e.hidden = !e.hidden, y("#toggle-workflow").textContent = e.hidden ? "Show steps" : "Hide steps", y("#toggle-workflow").setAttribute("aria-expanded", String(!e.hidden));
}, y("#task-output").onclick = async () => {
	let e = b.selectedTask, t = b.displayedRun;
	if (e === "validating") U("structure"), y("#comparison").scrollIntoView({ block: "start" });
	else try {
		if (e === "cover" && t && t.source !== "jobenu" && !u(t) && (await P("/api/job-result?id=" + encodeURIComponent(t.id))).coverPdf) {
			await Pe(t.id);
			return;
		}
		t && !u(t) ? await K(t) : U("ai");
		let n = {
			extract: "job.json",
			analyze: "analy",
			review: "review.",
			cover: "cover",
			adapt: "main.tex"
		}[e], r = [...(t && t.source !== "jobenu" && !u(t) ? y("#selected-run-files") : y("#artifacts")).querySelectorAll("details[data-path]")].find((e) => e.dataset.path.includes(n));
		r ? (r.open = !0, r.scrollIntoView({ block: "center" }), r.querySelector("summary").focus()) : F("This step has no saved results. Check the preparation status.");
	} catch (e) {
		F(e.message, !0);
	}
};
var Q;
async function je() {
	return Q || (Q = await import("/vendor/pdf.mjs"), Q.GlobalWorkerOptions.workerSrc = "/vendor/pdf.worker.mjs"), Q;
}
async function Me(e, t, n) {
	let r = b.snapshot;
	if (r) {
		if (e === "current" && b.dirty) F("Save your CV draft and recreate the preview before saving the PDF.", !0);
		else {
			n.disabled = !0;
			try {
				let e;
				try {
					e = await P("/api/pdf-save", {
						id: t.id,
						branch: r.branch
					});
				} catch (n) {
					if (!n.existingRevision || !window.confirm(`${n.filename} already exists in this application folder. Replace it with this preview?`)) {
						if (!n.existingRevision) throw n;
						return;
					}
					e = await P("/api/pdf-save", {
						id: t.id,
						branch: r.branch,
						existingRevision: n.existingRevision
					});
				}
				b.snapshot === r && F(`Saved ${e.filename} in this application’s folder.`);
			} catch (e) {
				b.snapshot === r && F(e.message, !0);
			} finally {
				n.disabled = !1;
			}
		}
	}
}
async function Ne(e, t, n) {
	let r = await je(), i = y(`#${e}-pdf`), a = r.getDocument({
		url: t.url,
		cMapUrl: "/vendor/cmaps/",
		cMapPacked: !0,
		standardFontDataUrl: "/vendor/standard_fonts/",
		wasmUrl: "/vendor/wasm/"
	}), o = await a.promise;
	if (n !== b.pdfGeneration) {
		await a.destroy();
		return;
	}
	i.replaceChildren();
	let s = document.createElement("div");
	s.className = "pdf-actions";
	let c = document.createElement("a");
	c.className = "pdf-download", c.href = t.url, c.tabIndex = 0, c.target = "_blank", c.rel = "noopener", c.textContent = "Open PDF ↗";
	let l = document.createElement("button");
	l.className = "save-pdf", l.textContent = "Save PDF to application folder", l.title = t.filename || "Save this PDF", l.disabled = !b.snapshot?.editable, l.onclick = () => Me(e, t, l), s.append(c, l), i.append(s);
	for (let e = 1; e <= o.numPages; e++) {
		let t = await o.getPage(e);
		if (n !== b.pdfGeneration) {
			await a.destroy();
			return;
		}
		let s = t.getViewport({ scale: 1 }), c = Math.max(200, i.clientWidth - 30), l = y("#zoom").value, u = l === "fit" ? c / s.width : Number(l), d = t.getViewport({ scale: u }), f = document.createElement("div");
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
async function Pe(e = null) {
	b.pdfDocument = "cover", y("#pdf-document").value = "cover", U("pdf"), await Fe(e);
}
y("#pdf-document").onchange = async () => {
	b.pdfDocument = y("#pdf-document").value;
	let e = ++b.pdfGeneration;
	U("pdf");
	try {
		for (let t of b.pdfDocument === "cover" ? ["cover"] : ["original", "current"]) b.pdfs[t] && await Ne(t, b.pdfs[t], e);
	} catch (e) {
		F(e.message, !0);
	}
};
async function Fe(e = null) {
	if (b.dirty && b.pdfDocument === "cv") {
		F("Save your CV draft before creating PDF previews.", !0);
		return;
	}
	if (!b.snapshot) return;
	let t = b.pdfDocument, n = ++b.pdfGeneration, r = b.snapshot.branch;
	y("#compile").disabled = !0, F("Creating your PDF preview…");
	try {
		let i = await Promise.allSettled((t === "cover" ? ["cover"] : ["original", "current"]).map(async (i) => {
			delete b.pdfs[i], y(`#${i}-pdf`).innerHTML = "<p class=\"pdf-message\">Creating PDF preview…</p>";
			try {
				let a = await P("/api/pdf", {
					branch: r,
					side: i === "cover" ? "current" : i,
					engine: y("#engine").value,
					document: t,
					runId: t === "cover" ? e : null
				});
				return n === b.pdfGeneration ? (b.pdfs[i] = a, i === "cover" && (y("#cover-pdf-label").textContent = e ? "PDF from this preparation" : w(r)), await Ne(i, a, n), a) : void 0;
			} catch (e) {
				throw n === b.pdfGeneration && (y(`#${i}-pdf`).innerHTML = `<p class="pdf-message">${j(e.message)}</p>`), e;
			}
		}));
		if (n !== b.pdfGeneration) return;
		let a = i.flatMap((e) => e.status === "fulfilled" ? e.value?.warnings || [] : [e.reason.message]);
		F(a.length ? a.join("\n") : t === "cover" ? "Cover-letter PDF ready. Text is selectable." : "PDF previews are ready. Select and copy text from either page.", i.some((e) => e.status === "rejected"));
	} finally {
		y("#compile").disabled = !b.snapshot;
	}
}
y("#zoom").onchange = async () => {
	let e = ++b.pdfGeneration;
	try {
		for (let t of b.pdfDocument === "cover" ? ["cover"] : ["original", "current"]) b.pdfs[t] && await Ne(t, b.pdfs[t], e);
	} catch (e) {
		F(e.message, !0);
	}
}, document.querySelectorAll("[data-filter]").forEach((e) => e.onclick = () => {
	b.filter = e.dataset.filter, document.querySelectorAll("[data-filter]").forEach((t) => t.setAttribute("aria-pressed", String(t === e))), L();
}), y("#search").oninput = L, y("#refresh").onclick = R, y("#new-branch").onclick = we, y("#branch-from").onclick = we, y("#back").onclick = () => {
	if (!z()) return;
	let e = b.snapshot?.branch;
	b.generation++, b.pdfGeneration++, b.snapshot = null, b.dirty = !1, b.jobDirty = !1, y("#workspace").hidden = !0, y("#board").hidden = !1, document.body.classList.remove("in-workspace"), history.replaceState(null, "", "/"), y("#search").focus(), e && pe(e), R();
}, y("#reload").onclick = () => B(b.snapshot?.branch || y("#branch-title").textContent), document.querySelectorAll("[data-view]").forEach((e) => e.onclick = () => U(e.dataset.view)), y(".tabs").addEventListener("focusin", (e) => requestAnimationFrame(() => {
	document.activeElement === e.target && e.target.scrollIntoView({
		block: "nearest",
		inline: "nearest"
	});
})), y(".tabs").onkeydown = (e) => {
	if (![
		"ArrowLeft",
		"ArrowRight",
		"Home",
		"End"
	].includes(e.key)) return;
	let t = [...document.querySelectorAll("[data-view]")], n = t.indexOf(e.target);
	if (n < 0) return;
	let r = e.key === "Home" ? 0 : e.key === "End" ? t.length - 1 : (n + (e.key === "ArrowRight" ? 1 : -1) + t.length) % t.length;
	e.preventDefault(), U(t[r].dataset.view), t[r].focus();
}, document.querySelectorAll(".close-dialog").forEach((e) => e.onclick = () => e.closest("dialog").close()), y("#job-description").oninput = () => {
	b.jobDirty = y("#job-description").value !== b.snapshot.job, y("#job-state").textContent = b.jobDirty ? "Unsaved changes" : "Saved on this computer", H();
}, y("#save-source").onclick = ve, y("#save-job").onclick = ye, y("#commit-push").onclick = Ce, y("#run-adapt").onclick = () => G(), y("#compile").onclick = () => Fe(), window.addEventListener("beforeunload", (e) => {
	(b.dirty || b.jobDirty) && (e.preventDefault(), e.returnValue = "");
}), window.addEventListener("pagehide", () => {
	b.snapshot && b.session && fetch("/api/release-worktree", {
		method: "POST",
		keepalive: !0,
		headers: {
			"Content-Type": "application/json",
			"X-Vita-Token": b.session.token
		},
		body: JSON.stringify({ branch: b.snapshot.branch })
	}).catch(() => {});
}), document.addEventListener("keydown", (e) => {
	e.key === "/" && !e.target.closest("input,textarea,select,[contenteditable]") && !y("#board").hidden && (e.preventDefault(), y("#search").focus()), (e.ctrlKey || e.metaKey) && e.key === "s" && b.snapshot && (e.preventDefault(), b.view === "ai" ? ye() : ve());
});
var $ = g({
	api: P,
	retry: async (e, t) => {
		if (b.dirty || b.jobDirty) throw Error("Save your CV and job description drafts before retrying.");
		let n = await P("/api/job?id=" + encodeURIComponent(e));
		if (t(), await K(n), b.snapshot?.branch !== n.branch) throw Error("Open this application before retrying.");
		b.resumeCaptured = !0, y("#resume-current-config").checked = !1, await Z();
	}
});
y("#inspect-run").onclick = () => b.displayedRun?.source === "jobenu" ? E.open() : $.open(b.displayedRun?.id), y("#inspect-step").onclick = () => $.open(b.displayedRun?.id, b.selectedTask), y("#inspect-step-dialog").onclick = () => {
	y("#step-ai-dialog").close(), $.open(b.displayedRun?.id, b.selectedTask);
};
try {
	await se(), await R();
	let e = new URLSearchParams(location.search), t = e.get("branch");
	[
		"structure",
		"source",
		"pdf",
		"changes",
		"ai"
	].includes(e.get("view")) && (b.view = e.get("view")), t && await B(t), k = f({
		api: P,
		changed: De
	}), k.start();
} catch (e) {
	y("#branch-list").innerHTML = `<p class="empty">${j(e.message)}</p>`;
}
setInterval(() => {
	document.querySelectorAll(".dag-time[data-started-at]").forEach((e) => {
		e.textContent = r(Date.now() / 1e3 - Number(e.dataset.startedAt), e.hasAttribute("data-clock"));
	});
}, 1e3);
