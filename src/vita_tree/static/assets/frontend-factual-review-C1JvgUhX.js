import { createLatexEditor as e, renderLatexSnippet as t } from "/vendor/editor.mjs";
// frontend/src/compat/factual-review.js
var n = (e) => document.querySelector(e), r = {
	ambiguous_acronym: "Check this abbreviation",
	date_interpretation: "Check these dates",
	credential_status: "Check this qualification",
	metric_or_unit: "Check this number",
	unverified_semantic_change: "Check the meaning",
	formatting_semantics_unverified: "Check the formatting",
	whitespace_only: "Spacing update"
}, i = (e, t, n) => {
	let r = document.createElement(e);
	return r.textContent = t, n && (r.className = n), r;
};
function a({ api: a, getState: o, changed: s, continued: c, notice: l }) {
	let u = n("#factual-review-panel"), d = n("#factual-review-form"), f = n("#factual-review-items"), p = null, m = !1, h = 0, g = null;
	function _(e) {
		for (let t of u.querySelectorAll("button,input,textarea")) t.disabled = e;
	}
	function v() {
		m || (h++, p = null, g?.destroy(), g = null, f.replaceChildren(), d.reset(), u.close(), u.hidden = !0, n("#review-facts").focus({ preventScroll: !0 }));
	}
	n("#cancel-factual-review").onclick = v, n("#close-factual-review").onclick = v, u.oncancel = (e) => {
		e.preventDefault(), v();
	};
	function y() {
		let e = f.querySelectorAll("input:checked").length;
		n("#factual-choice-count").textContent = `${e} of ${p?.items.length || 0} decisions ready`;
	}
	for (let [e, t] of [["accept-all-facts", "accept"], ["reject-all-facts", "reject"]]) n("#" + e).onclick = () => {
		if (!m) {
			for (let e of f.querySelectorAll(`input[value=${t}]`)) e.checked = !0, e.dispatchEvent(new Event("change"));
			y();
		}
	};
	async function b(s) {
		let c = o();
		if (c.dirty || c.jobDirty) {
			l("Save your CV and job description drafts before reviewing factual changes.", !0);
			return;
		}
		let m = c.snapshot, _ = ++h, v = await a("/api/factual-review?id=" + encodeURIComponent(s.id));
		if (o().snapshot !== m || _ !== h) return;
		p = v, f.replaceChildren(), d.reset(), n("#factual-review-error").textContent = "";
		let b = v.state === "resolved";
		n("#factual-review-title").textContent = b ? "Your factual decisions" : "Review factual changes", n("#factual-review-summary").textContent = `${v.step === "adapt" ? "Tailored CV" : "Cover letter"} · ${v.items.length} changes · ${v.target}. ` + (b ? "Your approved wording is shown below. It is retained safely; the application is updated after the remaining steps and final checks succeed." : "Your application is unchanged. Check each interpretation against your source, then accept, reject, or edit it."), n("#factual-review-revision").textContent = v.revision, n("#factual-review-confirmation").hidden = b, n("#confirm-factual-meaning").required = !b, n("#apply-factual-review").hidden = !1, n("#apply-factual-review").textContent = b ? "Continue preparation" : "Approve & continue", n("#factual-bulk").hidden = b;
		for (let [e, n] of v.items.entries()) {
			let a = document.createElement("fieldset");
			a.className = "factual-change", a.dataset.changeId = n.id, a.append(i("legend", `${e + 1}. ${r[n.reason] || "Check this change"}`));
			let o = document.createElement("details");
			o.append(i("summary", "Change details"), i("p", `${n.kind.replaceAll("_", " ")} · ${n.verification.replaceAll("_", " ")}`, "helper")), a.append(o), a.append(i("p", n.output_span ? `Proposed location: ${v.target} · lines ${n.output_span.line_start}–${n.output_span.line_end}` : "Deletion from the source locations below.", "helper")), a.append(i("p", n.unresolvedMeaning, "factual-meaning"));
			let s = document.createElement("div");
			s.className = "factual-sources", n.sources.length || s.append(i("p", "No supporting source location. This is an unsupported insertion."));
			for (let e of n.sources) {
				let t = document.createElement("details");
				t.append(i("summary", `${e.path} · lines ${e.line_start}–${e.line_end}`), i("pre", e.quote)), s.append(t);
			}
			a.append(s);
			let c = document.createElement("div");
			c.className = "factual-wording";
			for (let [e, r] of [["Original wording", n.original], ["Proposed wording", n.proposed]]) {
				let a = document.createElement("div");
				a.className = e.startsWith("Original") ? "wording-before" : "wording-after";
				let o = i("pre", ""), s = 0, l = 0, u = n.original || "", d = n.proposed || "";
				for (; s < Math.min(u.length, d.length) && u[s] === d[s];) s++;
				for (; l < Math.min(u.length, d.length) - s && u[u.length - 1 - l] === d[d.length - 1 - l];) l++;
				t(o, r || "(no text)", s, Math.max(s, (r || "").length - l)), a.append(i("h3", e), o), c.append(a);
			}
			if (a.append(c), b) {
				let e = v.provenance?.decisions.find((e) => e.id === n.id);
				a.append(i("p", `Decision: ${e?.action || "unknown"}`)), e?.action === "edit" && a.append(i("pre", e.text));
			} else {
				let t = document.createElement("div");
				t.className = "factual-options";
				let r = document.createElement("textarea");
				r.id = "fact-edit-" + e, r.value = n.proposed, r.hidden = !0, r.setAttribute("aria-label", `Edited wording for change ${e + 1}`);
				for (let [n, i] of [
					["accept", "Accept proposed wording"],
					["reject", "Reject; keep original wording"],
					["edit", "Edit wording"]
				]) {
					let a = document.createElement("label"), o = document.createElement("input");
					o.type = "radio", o.name = "fact-" + e, o.value = n, o.required = !0, o.onchange = () => {
						r.hidden = o.value !== "edit", o.value === "edit" && r.focus(), y();
					}, a.append(o, document.createTextNode(i)), t.append(a);
				}
				a.append(t, r);
			}
			f.append(a);
		}
		let x = n("#factual-provenance");
		x.hidden = !b, b && (x.textContent = `${v.provenance.method === "automatic_run_policy" ? "Automatic approval · selected for this run" : "Explicit local-user review"} · ${(/* @__PURE__ */ new Date(v.provenance.decidedAt * 1e3)).toLocaleString()} · resulting revision ${v.provenance.resolvedRevision}. Original source and proposal retained.`);
		let S = n("#factual-source-preview"), C = S.closest("details");
		C.querySelector("summary").textContent = b ? "Approved LaTeX · your decisions applied" : "Full proposed LaTeX · syntax check", C.open = b, g?.destroy(), g = e(S, {
			label: b ? "Approved LaTeX" : "Full proposed LaTeX",
			readOnly: !0,
			lint: (e) => a("/api/lint", { content: e })
		}), g.setDocument((b ? v.reviewed : v.proposed) || "", v.revision), y(), u.hidden = !1, u.open || u.showModal(), n("#factual-review-title").focus({ preventScroll: !0 });
	}
	return d.onsubmit = async (e) => {
		if (e.preventDefault(), m || !p) return;
		let t = o();
		if (t.dirty || t.jobDirty) {
			n("#factual-review-error").textContent = "Save your local editor drafts before applying decisions.";
			return;
		}
		let r = p.state === "resolved" ? [] : p.items.map((e, t) => {
			let r = d.elements["fact-" + t].value;
			return {
				id: e.id,
				action: r,
				...r === "edit" ? { text: n("#fact-edit-" + t).value } : {}
			};
		});
		m = !0, _(!0), n("#factual-review-error").textContent = "", u.setAttribute("aria-busy", "true"), n("#factual-review-progress").textContent = "Validating your decisions and saving the reviewed draft…";
		try {
			p.state !== "resolved" && await a("/api/factual-review/apply", {
				id: p.runId,
				revision: p.revision,
				token: p.token,
				decisions: r,
				confirmed: n("#confirm-factual-meaning").checked
			}), p.state = "resolved", n("#confirm-factual-meaning").required = !1, n("#apply-factual-review").textContent = "Continue preparation", await c(p.runId, t.snapshot.branch), m = !1, v();
		} catch (e) {
			if (p?.state === "resolved") try {
				await b({ id: p.runId });
			} catch {}
			n("#factual-review-error").textContent = e.message;
		} finally {
			m = !1, _(!1), u.removeAttribute("aria-busy"), n("#factual-review-progress").textContent = "";
		}
	}, {
		open: b,
		reset() {
			m || (h++, p = null, g?.destroy(), g = null, u.close(), u.hidden = !0, f.replaceChildren());
		}
	};
}
export { a as t };
