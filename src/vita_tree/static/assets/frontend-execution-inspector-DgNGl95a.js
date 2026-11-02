import { n as e } from "./frontend-provider-failures-uMyQIdg2.js";
// frontend/src/compat/execution-inspector.js
function t({ api: t, retry: n }) {
	let r = (e) => document.querySelector(e), i = r("#execution-inspector"), a = r("#diagnostics-dialog"), o = {
		extract: "Identify job requirements",
		analyze: "Check CV match",
		adapt: "Tailor CV",
		review: "Review CV with AI",
		cover: "Cover letter",
		validating: "Final checks",
		preparing: "Prepare workspace"
	}, s = [
		"overview",
		"timeline",
		"request",
		"response",
		"error",
		"artifacts"
	];
	i.innerHTML = `
    <div class="inspector-heading"><div><h3>Preparation history</h3><p class="helper">Choose a preparation to see what happened and what to do next.</p></div><button id="refresh-executions">Refresh preparations</button></div>
    <div class="inspector-filters"><label>Find a preparation<input id="execution-search" type="search" placeholder="Application, model, or trace ID"></label><label>Status<select id="execution-status"><option value="">All preparations</option><option value="running">In progress</option><option value="failed">Needs attention</option><option value="interrupted">Interrupted</option><option value="succeeded">Completed</option></select></label></div>
    <p id="execution-error" class="form-error" role="status"></p><div id="execution-list" class="execution-list" aria-label="Preparations"></div>
    <div class="inspector-pagination"><button id="execution-prev">Previous preparations</button><span id="execution-count" role="status"></span><button id="execution-next">More preparations</button></div>
    <section id="execution-detail" hidden aria-labelledby="execution-detail-title">
      <div class="inspector-heading"><div><h3 id="execution-detail-title" tabindex="-1">Execution details</h3><p id="execution-reference" class="helper"></p></div><div class="actions"><button id="execution-copy-trace">Copy trace ID</button><button id="execution-retry" hidden>Retry preparation</button></div></div>
      <label>Preparation step<select id="execution-step"><option value="">All steps</option>${Object.entries(o).filter(([e]) => e !== "preparing").map(([e, t]) => "<option value=\"" + e + "\">" + t + "</option>").join("")}</select></label>
      <p id="execution-contract" role="status"></p><p id="execution-warnings" class="form-error"></p>
      <div class="inspector-tabs" role="tablist" aria-label="Execution evidence">${s.map((e, t) => "<button role=\"tab\" id=\"inspector-tab-" + e + "\" aria-controls=\"inspector-panel-" + e + "\" aria-selected=\"" + (t === 0) + "\" tabindex=\"" + (t === 0 ? 0 : -1) + "\">" + e[0].toUpperCase() + e.slice(1) + "</button>").join("")}</div>
      ${s.map((e, t) => "<div id=\"inspector-panel-" + e + "\" role=\"tabpanel\" aria-labelledby=\"inspector-tab-" + e + "\"" + (t ? " hidden" : "") + "></div>").join("")}
      <p id="inspector-feedback" role="status"></p>
    </section>
    <details class="technical-details"><summary>Where execution details are stored</summary><p>Trace folder: <code id="execution-location"></code></p><button id="execution-copy-location">Copy trace folder location</button><p id="execution-storage-error" class="form-error"></p><p id="execution-policy" class="helper"></p><p id="execution-retention" class="helper"></p><p class="helper">Paste the copied location into your file manager. Technical structure is not an exact prompt or model response. Sanitization does not guarantee anonymization.</p></details>`;
	let c = 0, l = null, u = null, d = 0, f, p = null, m = 0, h = 0, g = !1, _ = (e, t, n) => {
		let r = document.createElement(e);
		return r.textContent = t ?? "", n && (r.className = n), r;
	}, v = (e, t) => e.append(_("p", t));
	function y(e, t, n) {
		let r = document.createElement("details");
		r.className = "inspector-evidence", r.append(_("summary", t));
		let i = _("pre", JSON.stringify(n, null, 2));
		i.tabIndex = 0, r.append(i), e.append(r);
	}
	function b(e, t, n) {
		let r = _("button", t);
		return r.type = "button", r.onclick = n, e.append(r), r;
	}
	async function x(e) {
		try {
			await navigator.clipboard.writeText(e), r("#inspector-feedback").textContent = "Copied.";
		} catch {
			r("#inspector-feedback").textContent = "Clipboard access is unavailable. Select and copy the displayed text.";
		}
	}
	function S(e) {
		r("#execution-location").textContent = e.path, r("#execution-storage-error").textContent = e.error || "", r("#execution-policy").textContent = e.policy + " Additional content capture for new preparations: " + e.capture + ".", r("#execution-retention").textContent = e.retention;
	}
	async function C() {
		let n = ++h;
		r("#refresh-executions").disabled = !0;
		try {
			let i = await t("/api/executions?" + new URLSearchParams({
				offset: c,
				q: r("#execution-search").value,
				status: r("#execution-status").value
			}));
			if (n !== h) return;
			S(i.storage), r("#execution-error").textContent = "";
			let a = r("#execution-list");
			a.replaceChildren();
			for (let t of i.runs) {
				let n = document.createElement("div");
				n.className = "execution-row";
				let r = b(n, `${t.branch} · ${t.status === "succeeded" ? "Completed" : t.status === "running" ? "In progress" : t.status === "interrupted" ? "Interrupted" : "Needs attention"} · Attempt ${t.attempt || "—"}`, () => A(t.id));
				r.dataset.run = t.id, r.setAttribute("aria-pressed", String(l === t.id));
				let i = [
					t.failedStep ? `Stopped at ${o[t.failedStep] || t.failedStep}` : "",
					t.provider,
					t.model,
					`${Math.floor(t.elapsedSeconds)}s`,
					(/* @__PURE__ */ new Date(t.createdAt * 1e3)).toLocaleString(),
					t.traceId ? `Trace ${t.traceId}` : "Limited historical diagnostics"
				].filter(Boolean).join(" · ");
				n.append(_("span", i, "helper")), e(t) && n.append(_("p", e(t), "provider-failure")), t.parentRunId && n.append(_("span", `Continues ${t.parentRunId} · ${t.configurationChanged ? "Changed setup" : "Captured setup preserved"}`, "helper")), t.failedStep && b(n, "Inspect failed step", () => A(t.id, t.failedStep)), a.append(n);
			}
			i.runs.length || v(a, "No matching preparations."), r("#execution-count").textContent = i.total ? `${c + 1}–${c + i.runs.length} of ${i.total}` : "0 preparations", r("#execution-prev").disabled = c === 0, r("#execution-next").disabled = c + 20 >= i.total;
		} catch (e) {
			r("#execution-error").textContent = e.message;
		} finally {
			n === h && (r("#refresh-executions").disabled = !1);
		}
	}
	function w(e, t = !1) {
		for (let t of s) {
			let n = r("#inspector-tab-" + t);
			n.setAttribute("aria-selected", String(t === e)), n.tabIndex = t === e ? 0 : -1, r("#inspector-panel-" + t).hidden = t !== e;
		}
		t && r("#inspector-tab-" + e).focus();
	}
	for (let [e, t] of s.entries()) {
		let n = r("#inspector-tab-" + t);
		n.onclick = () => w(t), n.onkeydown = (t) => {
			let n = t.key === "ArrowRight" ? s[(e + 1) % s.length] : t.key === "ArrowLeft" ? s[(e + s.length - 1) % s.length] : t.key === "Home" ? s[0] : t.key === "End" ? s.at(-1) : null;
			n && (t.preventDefault(), w(n, !0));
		};
	}
	function T(e) {
		return e.kind === "provider_error" ? e.content_exists === !1 ? "Provider error reported · no error response body received" : e.content_exists === null ? "Provider error details · response body not observed" : "Provider error response · " + e.capture_status : e.content_exists === !1 ? e.kind === "http_response" ? "No HTTP response received" : "No model response produced (generation rejected or stopped before output)" : e.content_exists === null ? "No response observed · whether content exists is unknown" : {
			disabled: "Response exists · content capture disabled",
			suppressed: "Response exists · privacy suppression",
			truncated: "Response structure truncated",
			unavailable: "Response artifact unavailable",
			redacted: "Response exists · source values removed",
			captured: "Sanitized diagnostic summary available"
		}[e.capture_status];
	}
	async function E(e, n, i) {
		i.disabled = !0;
		let a = l;
		try {
			let r = await t("/api/execution-artifact?" + new URLSearchParams({
				id: a,
				artifact: e
			}));
			if (a !== l) return;
			n.querySelector("[data-artifact-content]")?.remove();
			let i = _("pre", r.content ? JSON.stringify(r.content, null, 2) : r.message || `No body is available: ${r.state}.`);
			i.dataset.artifactContent = "", i.tabIndex = 0, n.append(i);
		} catch (e) {
			r("#inspector-feedback").textContent = e.message;
		} finally {
			i.disabled = !1;
		}
	}
	function D(e, t) {
		if (!t.length) v(e, "No capture references were recorded for this selection. Response content must not be assumed to exist.");
		else for (let n of t) {
			let t = document.createElement("div");
			if (t.className = "inspector-capture", t.append(_("strong", [
				"response",
				"provider_error",
				"http_response"
			].includes(n.kind) ? T(n) : `${n.kind} · ${n.capture_status}`)), v(t, `Capture reason: ${n.reason.replaceAll("_", " ")} · ${n.bytes} bytes · Artifact ${n.id}`), n.bytes && [
				"captured",
				"redacted",
				"truncated"
			].includes(n.capture_status)) {
				let e = b(t, "Inspect sanitized structure", () => E(n.id, t, e));
				e.dataset.artifact = n.id;
			}
			e.append(t);
		}
	}
	function O() {
		let { run: e, tree: n, backend: i, overview: a, lineage: c } = u;
		r("#execution-detail").hidden = !1, r("#execution-detail-title").textContent = `Attempt ${e.attempt || "—"} · ${e.status}`, r("#execution-reference").textContent = e.traceId ? `Trace ${e.traceId} · Execution ${e.id}` : `Execution ${e.id} · Historical trace unavailable`, r("#execution-copy-trace").disabled = !e.traceId, r("#execution-contract").textContent = i.message, r("#execution-warnings").textContent = i.warnings.join(" "), r("#execution-retry").hidden = !u.resumeAvailable, S(u.storage);
		for (let e of s) r("#inspector-panel-" + e).replaceChildren();
		let d = r("#inspector-panel-overview");
		v(d, a.phase ? `Stopped during ${a.phase.replaceAll("_", " ")}${a.category ? ` · ${a.category.replaceAll("_", " ")}` : ""}.` : e.status === "succeeded" ? "Preparation completed." : "No failure phase was recorded; the cause is unknown."), v(d, a.nextAction), n.configurationChanged && v(d, "Changed configuration: this attempt uses different captured routing than its parent."), e.parentRunId && v(d, `Continues execution ${e.parentRunId}. Root execution ${e.rootRunId}.`);
		let f = r("#inspector-panel-timeline"), p = document.createElement("div");
		p.className = "inspector-lineage";
		for (let e of c) b(p, `Attempt ${e.attempt || "—"} · ${e.status}`, () => A(e.id));
		f.append(p);
		for (let e of n.events || []) v(f, `Tree · ${o[e.step] || "Preparation"} · ${e.phase} · ${e.status}${e.duration_ms == null ? "" : ` · ${e.duration_ms}ms`}${e.reusedFrom ? ` · verified result from ${e.reusedFrom}` : ""}`);
		for (let e of i.events) {
			let t = document.createElement("details");
			t.className = "inspector-evidence", t.append(_("summary", `${o[e.step] || e.step || "Backend"} · ${e.phase} · ${e.event} · ${e.status}${e.details.attempt ? ` · attempt ${e.details.attempt}` : ""}${e.details.duration_ms == null ? "" : ` · ${e.details.duration_ms}ms`}${e.details.delay_seconds == null ? "" : ` · retry delay ${e.details.delay_seconds}s`}`));
			let n = _("pre", JSON.stringify(e, null, 2));
			n.tabIndex = 0, t.append(n), f.append(t);
		}
		if (i.totalEvents > 100) {
			v(f, `Backend events ${i.offset + 1}–${Math.min(i.offset + 100, i.totalEvents)} of ${i.totalEvents}.`);
			let e = b(f, "Earlier events", () => {
				m = Math.max(0, m - 100), k(!1);
			});
			e.disabled = m === 0;
			let t = b(f, "More events", () => {
				m += 100, k(!1);
			});
			t.disabled = m + 100 >= i.totalEvents;
		}
		let h = r("#inspector-panel-request");
		for (let e of i.processes) v(h, `${o[e.step] || e.step} · Additional structure capture ${e.capture_enabled ? "enabled" : "disabled"} (reported by backend) · Logging ${e.logging_complete ? "complete" : "incomplete"}`);
		for (let [e, t] of Object.entries(n.configuration || {})) r("#execution-step").value && r("#execution-step").value !== e || (v(h, `${o[e] || e} · ${t.origin === "step_override" ? "Per-step override" : t.origin === "shared" ? "Shared settings" : "Captured settings"}`), y(h, "Requested route", t.requested));
		let g = i.routes || i.events.filter((e) => e.event === "route");
		if (g.length) for (let e of g) y(h, "Backend-reported effective route and origins", e.details);
		else v(h, "Effective provider, model, reasoning, and their origins were not reported by the backend. Requested values are not proof of the effective route.");
		y(h, "Captured input and configuration fingerprints", n.inputs || {}), y(h, "Source and dependency fingerprints at each step", n.stepInputs || {}), D(h, i.artifacts.filter((e) => [
			"request",
			"schema",
			"instructions"
		].includes(e.kind))), D(r("#inspector-panel-response"), i.artifacts.filter((e) => [
			"response",
			"http_response",
			"provider_error"
		].includes(e.kind)));
		let C = r("#inspector-panel-error"), w = i.processes.filter((e) => e.failure);
		if (w.length) for (let e of w) y(C, `${o[e.step] || e.step} · ${e.failure.phase}`, e.failure);
		else v(C, "No structured backend error was recorded. A missing capture does not mean there was an empty or successful response.");
		for (let e of n.events || []) e.status === "error" && y(C, `Tree · ${e.phase}`, e);
		let T = r("#inspector-panel-artifacts");
		D(T, i.artifacts), b(T, "Copy execution diagnostics", () => x(JSON.stringify({
			...u,
			storage: void 0
		}, null, 2))), b(T, "Review support export", async () => {
			try {
				let e = await t("/api/execution-export?" + new URLSearchParams({
					id: l,
					preview: "1"
				}));
				T.querySelector("[data-export-review]")?.remove();
				let n = document.createElement("div");
				n.dataset.exportReview = "", n.className = "inspector-capture", v(n, e.notice), y(n, "Included information", e.included), y(n, "Omitted information", e.omitted);
				let r = _("a", "Download inspected support bundle");
				r.href = "/api/execution-export?" + new URLSearchParams({ id: l }), r.download = "vita-tree-technical-support.zip", n.append(r), T.append(n);
			} catch (e) {
				r("#inspector-feedback").textContent = e.message;
			}
		});
	}
	async function k(e = !0) {
		let n = ++d, i = l;
		r("#execution-error").textContent = "", r("#inspector-feedback").textContent = "";
		try {
			let a = await t("/api/execution?" + new URLSearchParams({
				id: i,
				step: r("#execution-step").value,
				offset: m
			}));
			if (n !== d) return;
			u = a, O(), e && (r("#execution-detail-title").focus({ preventScroll: !0 }), r("#execution-detail").scrollIntoView({ block: "start" }));
		} catch (e) {
			n === d && (r("#execution-error").textContent = e.message);
		}
	}
	async function A(e, t = "") {
		l = e, m = 0, r("#execution-step").value = t, await k();
		for (let t of i.querySelectorAll("[data-run]")) t.setAttribute("aria-pressed", String(t.dataset.run === e));
	}
	async function j(e = null, t = "") {
		p = document.activeElement, a.open || a.showModal(), await C(), e && await A(e, t);
	}
	return r("#execution-copy-trace").onclick = () => x(u?.run.traceId || ""), r("#execution-copy-location").onclick = () => x(r("#execution-location").textContent), r("#execution-retry").onclick = async () => {
		if (!g && l) {
			g = !0, r("#execution-retry").disabled = !0;
			try {
				await n(l, () => a.close());
			} catch (e) {
				r("#execution-error").textContent = e.message;
			} finally {
				g = !1, r("#execution-retry").disabled = !1;
			}
		}
	}, r("#refresh-executions").onclick = async () => {
		await C(), l && await k(!1);
	}, r("#execution-search").oninput = () => {
		clearTimeout(f), f = setTimeout(() => {
			c = 0, C();
		}, 250);
	}, r("#execution-status").onchange = () => {
		c = 0, C();
	}, r("#execution-step").onchange = () => {
		m = 0, k(!1);
	}, r("#execution-prev").onclick = () => {
		c = Math.max(0, c - 20), C();
	}, r("#execution-next").onclick = () => {
		c += 20, C();
	}, a.addEventListener("close", () => {
		p?.isConnected && p.focus();
	}), {
		open: j,
		refresh: C
	};
}
export { t };
