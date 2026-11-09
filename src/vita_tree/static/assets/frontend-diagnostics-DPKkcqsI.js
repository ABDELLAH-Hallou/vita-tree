import { t as e } from "./frontend-execution-inspector-DgNGl95a.js";
// frontend/src/compat/diagnostics.js
function t({ api: t, retry: n }) {
	let r = e({
		api: t,
		retry: n
	}), i = (e) => document.querySelector(e), a = i("#diagnostics-dialog"), o = !1, s = null, c = (e, t) => {
		let n = document.createElement("td");
		n.textContent = t ?? "—", e.append(n);
	}, l = {
		server_started: "Vita Tree started",
		server_stopped: "Vita Tree stopped",
		request_failed: "An action could not finish",
		history_write_failed: "Couldn’t save preparation history",
		history_load_failed: "Couldn’t read earlier preparation history",
		run_started: "Application preparation started",
		run_error: "Preparation needs attention",
		run_finished: "Application preparation finished",
		step_started: "A preparation step started",
		step_finished: "A preparation step finished",
		review_saved: "Review saved",
		provider_failed: "AI service could not finish",
		pdf_compiled: "PDF preview created",
		pdf_saved: "PDF saved",
		pdf_failed: "PDF could not be created",
		logging_failed: "Support logging is unavailable"
	};
	function u() {
		let e = i("#activity-summary");
		e.replaceChildren();
		for (let t of (s?.events || []).filter((e) => l[e.event]).slice(0, 12)) {
			let n = document.createElement("li"), r = document.createElement("time");
			r.textContent = new Date(t.time).toLocaleTimeString();
			let i = document.createElement("span");
			i.textContent = l[t.event], n.dataset.level = t.level, n.append(r, i), e.append(n);
		}
		if (!e.children.length) {
			let t = document.createElement("li");
			t.textContent = "No recent activity yet.", e.append(t);
		}
		let t = i("#diagnostics-search").value.trim().toLowerCase(), n = i("#diagnostics-events");
		n.replaceChildren();
		for (let e of s?.events || []) {
			if (t && !JSON.stringify(e).toLowerCase().includes(t)) continue;
			let r = document.createElement("tr");
			r.dataset.level = e.level, c(r, new Date(e.time).toLocaleTimeString()), c(r, e.event.replaceAll("_", " ")), c(r, e.step || e.operation || e.route || ""), c(r, [e.status, e.duration_ms == null ? "" : `${e.duration_ms}ms`].filter((e) => e !== void 0 && e !== "").join(" · ")), c(r, [
				e.error_type,
				e.exit_code == null ? "" : `exit ${e.exit_code}`,
				e.errno == null ? "" : `errno ${e.errno}`,
				e.winerror == null ? "" : `Windows ${e.winerror}`,
				e.location
			].filter(Boolean).join(" · ")), c(r, [e.request_id ? `request ${e.request_id}` : "", e.run_id ? `run ${e.run_id}` : ""].filter(Boolean).join(" · ")), n.append(r);
		}
		if (!n.children.length) {
			let e = document.createElement("tr"), t = document.createElement("td");
			t.colSpan = 6, t.textContent = "No matching events.", e.append(t), n.append(e);
		}
	}
	async function d() {
		if (!o) {
			o = !0, i("#refresh-diagnostics").disabled = !0;
			try {
				s = await t("/api/diagnostics"), i("#diagnostics-error").textContent = "";
				for (let [e, t] of Object.entries({
					active: s.history.running,
					completed: s.history.succeeded,
					failed: s.history.failed,
					requests: s.requests.total,
					errors: s.requests.failed,
					latency: s.requests.meanMs
				})) i("#metric-" + e).textContent = t;
				i("#diagnostics-location").textContent = s.logging.path || "Available for this session only", i("#diagnostics-logging").textContent = s.logging.error || "Older support log files are replaced automatically.", i("#diagnostics-uptime").textContent = `Vita Tree has been running for ${Math.floor(s.uptimeSeconds)} seconds. Performance counts reset when it restarts; preparation history is kept.`, u();
			} catch (e) {
				i("#diagnostics-error").textContent = e.message;
			} finally {
				o = !1, i("#refresh-diagnostics").disabled = !1;
			}
		}
	}
	for (let e of document.querySelectorAll("[data-open-diagnostics]")) e.onclick = () => {
		r.open(), d();
	};
	return i("#refresh-diagnostics").onclick = d, i("#diagnostics-search").oninput = u, i("#download-diagnostics").onclick = () => {
		if (!s) return;
		let e = {
			...s,
			logging: {
				enabled: s.logging.enabled,
				error: s.logging.error
			}
		}, t = URL.createObjectURL(new Blob([JSON.stringify(e, null, 2)], { type: "application/json" })), n = document.createElement("a");
		n.href = t, n.download = "vita-tree-support-report.json", n.click(), setTimeout(() => URL.revokeObjectURL(t), 1e3);
	}, setInterval(() => {
		a.open && d();
	}, 3e3), r;
}
export { t };
