// frontend/src/compat/requirements.js
var e = (e) => document.querySelector(e), t = (e, t) => {
	let n = document.createElement(e);
	return n.textContent = t, n;
}, n = [
	"hard_skills",
	"soft_skills",
	"experience",
	"responsibilities",
	"employment_condition"
];
function r({ api: r, getState: i, changed: a, continued: o, notice: s }) {
	let c = document.createElement("dialog");
	c.id = "requirements-dialog", c.setAttribute("aria-labelledby", "requirements-title"), c.innerHTML = "<div class=\"dialog-heading\"><h2 id=\"requirements-title\">Job requirements</h2><button id=\"requirements-close\" aria-label=\"Close job requirements\">×</button></div>\n    <div class=\"review-scroll\"><p id=\"requirements-status\" role=\"status\"></p><p class=\"helper\">One shared definition for this job description. Required, preferred, and unclear capabilities are assessed separately from employment conditions. Explicit source wording determines classification; conflicting headings stay unclear.</p>\n    <details><summary>Exact revision and origin</summary><p id=\"requirements-origin\"></p><code id=\"requirements-revision\"></code><p id=\"requirements-current\"></p></details>\n    <div class=\"requirements-layout\"><section aria-label=\"Requirements definition\"><div id=\"requirements-items\"></div><button id=\"requirement-add\">Add requirement</button></section><section class=\"requirements-source\" tabindex=\"0\" aria-labelledby=\"requirements-source-title\"><h3 id=\"requirements-source-title\">Job description source</h3><div id=\"requirements-source\" role=\"group\" aria-label=\"Line-numbered job description\"></div></section></div>\n    </div><div class=\"review-controls\"><p id=\"requirements-error\" role=\"alert\" class=\"error\"></p><label id=\"requirements-confirm-label\"><input type=\"checkbox\" id=\"requirements-confirm\"> I reviewed this exact revision, its sources, and unclear classifications.</label>\n    <div class=\"dialog-footer\"><button id=\"requirements-current-button\" hidden>Open current definition</button><button id=\"requirements-cancel\">Close without changes</button><button id=\"requirements-save\">Save new draft revision</button><button id=\"requirements-approve\" class=\"primary\">Approve & continue</button></div></div>", document.body.append(c);
	let l, u, d = [], f = !1, p = !1, m = 0, h = (t) => e("#requirements-error").textContent = t;
	function g() {
		p = !0, e("#requirements-confirm").checked = !1, e("#requirements-approve").disabled = !0, e("#requirements-status").textContent = "Unsaved corrections. Save a new draft revision before approving.";
	}
	function _() {
		f || (m++, c.close(), l = null);
	}
	e("#requirements-close").onclick = _, e("#requirements-cancel").onclick = _, c.oncancel = (e) => {
		e.preventDefault(), _();
	};
	function v(e, n, r, i, a) {
		let o = t("label", n), s = document.createElement(a ? "select" : "textarea");
		if (s.setAttribute("aria-label", n), a) for (let e of a) s.add(new Option(e.replaceAll("_", " "), e));
		return s.value = r, s.disabled = l.readOnly, s.oninput = () => {
			i(s.value), g();
		}, o.append(s), e.append(o), s;
	}
	function y(t) {
		for (let n of e("#requirements-source").children) n.classList.toggle("source-selected", Number(n.dataset.line) >= t.line_start && Number(n.dataset.line) <= t.line_end);
		let n = e(`#requirements-source [data-line="${t.line_start}"]`);
		n?.scrollIntoView({ block: "center" }), n?.focus({ preventScroll: !0 });
	}
	function b() {
		let r = e("#requirements-items");
		r.replaceChildren();
		for (let [e, i] of [["capabilities", "Capabilities"], ["conditions", "Employment conditions · not scored"]]) {
			r.append(t("h3", i));
			for (let i of d.filter((t) => t.category === "employment_condition" == (e === "conditions"))) {
				let e = document.createElement("fieldset");
				e.className = "requirement-card", e.append(t("legend", `Requirement ${d.indexOf(i) + 1}`)), v(e, "Criterion", i.criterion, (e) => i.criterion = e), i.id || v(e, "Job ID", i.job_id, (e) => i.job_id = e), v(e, "Classification", i.classification, (e) => i.classification = e, [
					"required",
					"preferred",
					"unclear"
				]);
				let a = document.createElement("details");
				a.className = "requirement-advanced", a.append(t("summary", "More details & corrections")), e.append(a), v(a, "Category", i.category, (e) => {
					i.category = e, b();
				}, n).setAttribute("aria-label", "Requirement category"), v(a, "Unresolved meaning / ambiguity", i.ambiguity, (e) => i.ambiguity = e), a.append(t("p", `Job: ${i.job_id} · Revision weight: ${i.weight ?? "assigned by Vita CV on save"}`));
				for (let [n, r] of i.source_refs.entries()) {
					let o = t("button", `View source · ${r.job_id} · lines ${r.line_start}–${r.line_end}`);
					o.type = "button", o.onclick = () => y(r), e.append(o);
					let s = document.createElement("details");
					s.append(t("summary", "Correct source reference")), v(s, "Source job ID", r.job_id, (e) => r.job_id = e);
					for (let [e, t] of [["line_start", "First line"], ["line_end", "Last line"]]) {
						let n = v(s, t, String(r[e]), (t) => r[e] = Number(t));
						n.rows = 1;
					}
					if (v(s, "Exact source quote", r.quote, (e) => r.quote = e), !l.readOnly && i.source_refs.length > 1) {
						let e = t("button", "Remove reference");
						e.onclick = () => {
							i.source_refs.splice(n, 1), g(), b();
						}, s.append(e);
					}
					a.append(s);
				}
				if (!l.readOnly) {
					let e = t("button", "Add source reference");
					e.onclick = () => {
						i.source_refs.push({
							job_id: i.job_id,
							line_start: 1,
							line_end: 1,
							quote: ""
						}), g(), b();
					};
					let n = t("button", "Remove requirement");
					n.onclick = () => {
						d.splice(d.indexOf(i), 1), g(), b();
					}, a.append(e, n);
				}
				r.append(e);
			}
		}
	}
	function x(n) {
		l = n, p = !1, d = structuredClone([...n.definition?.requirements || [], ...n.definition?.employment_conditions || []]), e("#requirements-confirm").checked = !1, h(""), e("#requirements-status").textContent = n.readOnly ? "Captured definition for this run · view only" : n.available === !1 ? "Connect Vita CV 2.8 or later to review canonical job requirements." : n.state === "approved" ? "Approved definition · edits create a new revision and invalidate dependent assessments." : n.definition ? "Review required · dependent steps are paused." : "No canonical definition yet. Run Extract to create one.", e("#requirements-revision").textContent = n.definition?.revision || "Not recorded", e("#requirements-origin").textContent = n.originBranch ? `Shared from application ${n.originBranch}${n.parentRevision ? " · previous revision " + n.parentRevision : ""}` : "Shared Vita CV definition", e("#requirements-current").textContent = n.approvedRevision ? `Current approved revision: ${n.approvedRevision}${n.readOnly && n.definition?.revision !== n.approvedRevision ? " · This run used an older definition." : ""}` : "No approved revision.", n.readOnly && n.state === "pending" && (e("#requirements-current").textContent += " A corrected definition is awaiting approval. Earlier assessments need to be rerun."), e("#requirements-source").replaceChildren(...(n.definition?.source_text || n.source || "").split("\n").map((e, n) => {
			let r = t("p", `${n + 1}  ${e}`);
			return r.dataset.line = n + 1, r.tabIndex = -1, r;
		}));
		for (let t of [
			"requirements-save",
			"requirement-add",
			"requirements-confirm-label",
			"requirements-approve"
		]) e("#" + t).hidden = n.readOnly || !n.definition;
		e("#requirements-approve").disabled = n.state === "approved", e("#requirements-current-button").hidden = !n.readOnly, b();
	}
	async function S(e = null) {
		let t = i();
		if (!t.snapshot) return;
		if (t.dirty || t.jobDirty) {
			s("Save your CV and job description drafts before reviewing requirements.", !0);
			return;
		}
		u = t.snapshot.branch;
		let n = ++m, a = await r("/api/requirements?branch=" + encodeURIComponent(u) + (e ? "&runId=" + encodeURIComponent(e.id) : ""));
		n === m && i().snapshot?.branch === u && (a.readOnly = a.readOnly || !!t.snapshot.running || !t.snapshot.editable, x(a), c.open || c.showModal());
	}
	e("#requirement-add").onclick = () => {
		d.push({
			job_id: d[0]?.job_id || "job-1",
			criterion: "",
			category: "hard_skills",
			classification: "unclear",
			ambiguity: "",
			source_refs: [{
				job_id: d[0]?.job_id || "job-1",
				line_start: 1,
				line_end: 1,
				quote: ""
			}]
		}), g(), b();
	}, e("#requirements-current-button").onclick = () => S().catch((e) => h(e.message));
	async function C(t) {
		if (!(f || !l || l.readOnly)) {
			if (t && (p || !e("#requirements-confirm").checked)) h("Save corrections, then confirm that you reviewed this revision.");
			else {
				f = !0, h(""), c.setAttribute("aria-busy", "true");
				for (let e of c.querySelectorAll("button,input,textarea,select")) e.disabled = !0;
				try {
					x(await r("/api/requirements/" + (t ? "approve" : "draft"), {
						branch: u,
						token: l.token,
						revision: l.definition.revision,
						...t ? { confirmed: !0 } : { items: d }
					})), t ? (await o(null, u), f = !1, _()) : await a();
				} catch (e) {
					h(e.message);
				} finally {
					f = !1, c.removeAttribute("aria-busy");
					for (let e of c.querySelectorAll("button,input,textarea,select")) e.disabled = !1;
					e("#requirements-approve").disabled = p || l?.state === "approved";
				}
			}
		}
	}
	return e("#requirements-save").onclick = () => C(!1), e("#requirements-approve").onclick = () => C(!0), {
		open: S,
		reset: _
	};
}
export { r as t };
