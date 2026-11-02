// frontend/src/compat/preflight.js
function e({ api: e, getState: t, getBranches: n, getSteps: r }) {
	let i = (e) => document.querySelector(e), a = i("#setup-dialog"), o = !1, s = 0, c = /* @__PURE__ */ new Map();
	function l(e) {
		i("#setup-results").replaceChildren(), i("#setup-result-heading").hidden = !e, i("#setup-result-heading").textContent = e ? e.ready ? "Ready for your selected steps" : "Something needs fixing" : "", i("#setup-revision").textContent = e ? `Saved CV revision ${e.revision?.slice(0, 12) || "unavailable"} · Engine: ${e.engine}. New or unsaved edits need another check.` : "";
		for (let t of e?.checks || []) {
			let e = document.createElement("li");
			e.dataset.severity = t.severity;
			let n = document.createElement("strong");
			n.textContent = t.message + (t.target ? " (" + t.target + ")" : "");
			let r = document.createElement("p");
			r.textContent = t.action, e.append(n, r), i("#setup-results").append(e);
		}
	}
	function u(e) {
		let n = t().snapshot, r = e?.preflight;
		r && n && c.set(n.branch, r);
		let a = r || n && c.get(n.branch), o = a?.checks.some((e) => e.code === "extract_only");
		i("#setup-summary").textContent = e?.step === "preflight" ? "Checking CV files and PDF tools…" : a ? `${a.ready ? o ? "Job details checked" : "CV files checked" : "Some files need attention"}. ${a.revision === n?.revision ? "" : "Your CV has changed since this check. "}${t().dirty || t().jobDirty ? "Save your draft to check your latest changes. " : ""}${a.checks.find((e) => e.severity === "error")?.message || "Files are checked again before preparation."}` : "CV files are checked automatically before preparation.";
	}
	async function d() {
		let r = t().snapshot?.branch || new URL(location.href).searchParams.get("branch"), u = ++s;
		a.showModal(), i("#check-setup").disabled = !0, i("#setup-progress").textContent = "Loading applications…";
		try {
			let t = n().length ? n() : (await e("/api/branches")).branches;
			if (u !== s || !a.open) return;
			i("#setup-branch").replaceChildren(...t.map((e) => new Option(e.displayName || e.name, e.name))), t.some((e) => e.name === r) && (i("#setup-branch").value = r), l(c.get(i("#setup-branch").value)), i("#setup-progress").textContent = t.length ? "" : "No CVs are available to check.", i("#check-setup").disabled = o || !t.length, i("#setup-branch").focus();
		} catch (e) {
			u === s && (i("#setup-progress").textContent = e.message);
		}
	}
	for (let e of document.querySelectorAll("[data-open-setup]")) e.onclick = d;
	return i("#setup-branch").onchange = () => {
		s++, l(c.get(i("#setup-branch").value)), i("#setup-progress").textContent = "";
	}, i("#setup-engine").onchange = () => {
		i("#engine").value = i("#setup-engine").value;
	}, i("#engine").addEventListener("change", () => {
		i("#setup-engine").value = i("#engine").value;
	}), i("#check-setup").onclick = async () => {
		if (o) return;
		let n = t(), a = i("#setup-branch").value, d = n.snapshot;
		if (!a) return;
		if (!n.session) {
			i("#setup-progress").textContent = "Wait for your applications to load, then try again.";
			return;
		}
		if (d?.branch === a && (n.dirty || n.jobDirty)) {
			i("#setup-progress").textContent = "Save your CV and job-description drafts before checking.";
			return;
		}
		let f = ++s;
		o = !0, i("#check-setup").disabled = !0, i("#setup-branch").disabled = !0, i("#setup-engine").disabled = !0, c.delete(a), l(null), u(), i("#setup-progress").textContent = "Checking CV files…";
		try {
			let t = await e("/api/preflight", {
				branch: a,
				engine: i("#setup-engine").value,
				workflow: { steps: d?.branch === a ? r() : ["analyze", "adapt"] },
				...d?.branch === a ? {
					revision: d.revision,
					jobRevision: d.jobRevision
				} : {}
			});
			if (c.set(a, t), f !== s) return;
			l(t), i("#setup-progress").textContent = "Check complete.", i("#setup-result-heading").focus(), u();
		} catch (e) {
			f === s && (l(null), i("#setup-progress").textContent = e.message);
		} finally {
			o = !1, i("#check-setup").disabled = !1, i("#setup-branch").disabled = !1, i("#setup-engine").disabled = !1;
		}
	}, a.addEventListener("close", () => {
		s++;
	}), {
		summary: u,
		engine: () => i("#setup-engine").value
	};
}
export { e as t };
