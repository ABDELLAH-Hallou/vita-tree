import { i as e, n as t, r as n, t as r } from "./frontend-jobenu-history-lKunSV0p.js";
import { renderLatexSnippet as i } from "/vendor/editor.mjs";
// frontend/src/compat/jobenu.js
function a({ api: a, branches: o, openBranch: s, ready: c }) {
	let l = (e) => document.querySelector(e), u = (e, t) => {
		let n = document.createElement(e);
		return n.textContent = t, n;
	}, d = (e) => ({
		selecting: "Choose applications",
		planned: "Ready to start",
		running: "In progress",
		imported: "Branches created",
		awaiting_approval: "Waiting for review",
		awaiting_requirements_approval: "Review job requirements",
		failed: "Needs attention",
		rejected: "Changes rejected",
		interrupted: "Interrupted · preview to resume",
		complete: "AI stages complete",
		preparing: "Preparing workspace",
		extract: "Extract",
		analyze: "Analyze",
		adapt: "Adapt",
		review: "Review",
		cover: "Cover"
	})[e] || e || "", f = u("button", "Import jobs");
	f.id = "open-jobenu", f.className = "quiet", l(".board-nav").append(f);
	let p = document.createElement("section");
	p.id = "jobenu-import", p.hidden = !0, p.innerHTML = "<button id=\"jobenu-back\" class=\"back\">← All applications</button><div class=\"page-heading\"><div><h1>Import jobs</h1><p class=\"subtitle\">Bring opportunities from Jobenu into this CV collection.</p></div></div>\n <div role=\"tablist\" aria-label=\"Import source\" class=\"jobenu-tabs\"><button role=\"tab\" aria-selected=\"true\">Jobenu</button></div>\n <p class=\"helper\">Your export stays unchanged. Each selected application gets its own CV workspace. Importing never submits an application or pushes to Git.</p>\n <p id=\"jobenu-error\" role=\"alert\" class=\"form-error\"></p><p id=\"jobenu-feedback\" role=\"status\"></p><p id=\"jobenu-limitations\" class=\"helper\"></p><p id=\"jobenu-settings-limitations\" role=\"status\"></p>\n <details id=\"jobenu-install\"><summary>Vita installation</summary><label>Compatible Vita CV source folder<input id=\"jobenu-source\" placeholder=\"Folder containing vita/__main__.py\"></label><button id=\"jobenu-check\">Check installation</button><p id=\"jobenu-capability\" role=\"status\"></p></details>\n <label id=\"jobenu-drop\" class=\"jobenu-drop\">Choose or drop a Jobenu JSON export<input id=\"jobenu-file\" type=\"file\" accept=\".json,application/json\"></label><p id=\"jobenu-file-info\" role=\"status\"></p>\n <div id=\"jobenu-date-filters\" hidden><div class=\"jobenu-date-toolbar\"><label>Date<select id=\"jobenu-date-field\"><option value=\"createdAt\">Added</option><option value=\"updatedAt\">Updated</option><option value=\"appliedAt\">Applied</option><option value=\"deadlineAt\">Deadline</option><option value=\"nextActionAt\">Next action</option></select></label><label>From<input id=\"jobenu-date-from\" type=\"date\" aria-describedby=\"jobenu-date-help jobenu-date-error\"></label><label>To<input id=\"jobenu-date-to\" type=\"date\" aria-describedby=\"jobenu-date-help jobenu-date-error\"></label><div class=\"actions\"><button id=\"jobenu-today\">Today</button><button id=\"jobenu-all-dates\">All dates</button></div></div><p id=\"jobenu-date-help\" class=\"helper\">Dates follow the calendar day in your export. Today uses your device's date.</p><p id=\"jobenu-date-error\" role=\"alert\" class=\"form-error\"></p><p id=\"jobenu-selection-summary\" role=\"status\"></p></div>\n <div class=\"jobenu-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Applications to import\"><table id=\"jobenu-selection\"><caption>Select applications</caption><thead><tr><th><input id=\"jobenu-select-all\" type=\"checkbox\" aria-label=\"Select all matching jobs\"></th><th>Company</th><th>Position</th><th>Status</th><th id=\"jobenu-date-heading\">Added</th></tr></thead><tbody></tbody></table></div>\n <div class=\"jobenu-settings\"><label>Starting CV<input id=\"jobenu-base\" type=\"search\" list=\"jobenu-bases\" autocomplete=\"off\" placeholder=\"Search local branches\"><datalist id=\"jobenu-bases\"></datalist></label><label>Approval mode<select id=\"jobenu-approval\" aria-describedby=\"jobenu-approval-help\"><option value=\"human\">Review changes before applying</option><option value=\"auto\">Apply verified changes automatically</option><option value=\"unattended\" disabled>Run without manual reviews</option></select></label></div>\n <p id=\"jobenu-approval-help\" class=\"helper\" role=\"status\"></p><div id=\"jobenu-approval-change\" hidden></div>\n <label><input id=\"jobenu-run\" type=\"checkbox\" checked> Run the AI workflow</label><p class=\"helper\">Complete means the configured AI stages finished; PDFs and submission are separate.</p>\n <details id=\"jobenu-advanced\"><summary>Advanced</summary><div class=\"jobenu-settings\"><label>Language override<input id=\"jobenu-language\" placeholder=\"Use saved language\"></label><label>Provider override<input id=\"jobenu-provider\" placeholder=\"Use saved AI settings\"></label><label>Status filters<input id=\"jobenu-statuses\" value=\"SAVED\" aria-describedby=\"jobenu-status-help\"></label></div><p id=\"jobenu-status-help\" class=\"helper\">Comma-separated statuses, or ALL. Uses saved stage providers/models and native Vita reasoning preferences. Tree-only reasoning overrides are not forwarded by this batch CLI.</p><label><input id=\"jobenu-demo\" type=\"checkbox\"> Include demo applications</label><label><input id=\"jobenu-revision\" type=\"checkbox\"> Create a new source revision when records changed</label><label id=\"jobenu-rerun-choice\"><input id=\"jobenu-rerun\" type=\"checkbox\"> Rerun completed steps (uses AI credits)</label></details>\n <div class=\"actions\"><button id=\"jobenu-preview\" disabled>Preview branches</button><button id=\"jobenu-start\" class=\"primary\" disabled>Create branches</button></div>\n <div class=\"jobenu-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Application preview\"><table id=\"jobenu-plan\"><caption>Branch preview</caption><thead><tr><th>Company</th><th>Position</th><th>Branch</th><th>Action</th></tr></thead><tbody></tbody></table></div><section id=\"jobenu-aliases\" hidden aria-labelledby=\"jobenu-alias-title\"></section>\n <h2>Batch activity</h2><p class=\"helper\">You can leave this view while work continues. Retained sources stay private until you forget the batch; imported workspaces are preserved.</p><div id=\"jobenu-history\" tabindex=\"-1\" role=\"region\" aria-label=\"Batch activity\"></div>\n <dialog id=\"jobenu-retry\" aria-labelledby=\"jobenu-retry-title\"><div class=\"dialog-heading\"><h2 id=\"jobenu-retry-title\">Retry failed jobs</h2></div><div class=\"review-scroll\"><p>Use the original AI settings. Keep valid completed steps and continue from the failure. Retrying makes AI requests and may use provider credits.</p><p id=\"jobenu-retry-progress\" role=\"status\"></p><div class=\"jobenu-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Jobs to retry\"><table><thead><tr><th>Company</th><th>Position</th><th>Continue from</th></tr></thead><tbody id=\"jobenu-retry-jobs\"></tbody></table></div><p id=\"jobenu-retry-error\" role=\"alert\" class=\"form-error\"></p></div><footer class=\"dialog-footer\"><button id=\"jobenu-retry-cancel\">Cancel</button><button id=\"jobenu-retry-confirm\" class=\"primary\" disabled>Retry jobs</button></footer></dialog>\n <dialog id=\"jobenu-review\" aria-labelledby=\"jobenu-review-title\"><div class=\"dialog-heading\"><h2 id=\"jobenu-review-title\">Review imported application</h2><button id=\"jobenu-review-close\" aria-label=\"Close import review\">×</button></div><div id=\"jobenu-review-content\" class=\"review-scroll\"></div><p id=\"jobenu-review-error\" role=\"alert\" class=\"form-error\"></p><footer class=\"dialog-footer\"><button id=\"jobenu-reject\">Reject changes</button><button id=\"jobenu-approve\" class=\"primary\">Approve exact revision</button></footer></dialog>", l("#main-content").append(p), document.body.append(l("#jobenu-review"));
	let m = null, h = null, g = !1, _ = !1, v = null, y = !1, b = null, x = !1, S = 0, C = 0, w = "", T = /* @__PURE__ */ new Set(), E = !1, D = /* @__PURE__ */ new Map(), O = !1, k = !1, A = null, j = 0, M = null, N = (e) => ({
		extract: "Identify job requirements",
		analyze: "Check CV match",
		adapt: "Tailor CV",
		review: "Review CV",
		cover: "Cover letter"
	})[e] || e || "Last unfinished step";
	function P() {
		for (let e of p.querySelectorAll(".jobenu-retry-action")) e.disabled = O || e.dataset.blocked === "true";
	}
	async function F(e) {
		e && await a("/api/jobenu/discard", { id: e.id });
	}
	async function I() {
		if (k) return;
		j++;
		let e = A;
		A = null, O = !1, l("#jobenu-retry").close(), P(), ([...p.querySelectorAll(".jobenu-retry-action")].find((e) => e.dataset.batch === M?.batch && e.dataset.key === M?.key) || l("#jobenu-history")).focus();
		try {
			await F(e);
		} catch (e) {
			R(e);
		}
	}
	l("#jobenu-retry-cancel").onclick = I, l("#jobenu-retry").oncancel = (e) => {
		e.preventDefault(), I();
	};
	async function L(e, t) {
		if (O) return;
		O = !0, M = {
			batch: e.id,
			key: t?.[0] || ""
		};
		let n = ++j;
		P(), l("#jobenu-retry-error").textContent = "", l("#jobenu-retry-progress").textContent = "Checking saved steps and settings…", l("#jobenu-retry-jobs").replaceChildren(), l("#jobenu-retry-confirm").disabled = !0, l("#jobenu-retry").showModal();
		try {
			let r = await a("/api/jobenu/retry-preview", {
				id: e.id,
				...t ? { keys: t } : {}
			});
			if (n !== j) {
				await F(r);
				return;
			}
			A = r;
			for (let e of r.entries) {
				let t = document.createElement("tr"), n = e.current_step, i = r.capturedRoutes?.[n], a = u("td", N(n));
				a.append(u("p", i?.provider ? `${i.provider}${i.model ? " / " + i.model : ""}` : "Saved Vita CV settings")), a.lastElementChild.className = "helper", t.append(u("td", e.company), u("td", e.position), a), l("#jobenu-retry-jobs").append(t);
			}
			l("#jobenu-retry-progress").textContent = `${r.entries.length} failed job${r.entries.length === 1 ? "" : "s"} ready to retry.`, l("#jobenu-retry-confirm").textContent = `Retry ${r.entries.length} job${r.entries.length === 1 ? "" : "s"}`, l("#jobenu-retry-confirm").disabled = !1;
		} catch (e) {
			n === j && (l("#jobenu-retry-progress").textContent = "", l("#jobenu-retry-error").textContent = e.message);
		}
	}
	l("#jobenu-retry-confirm").onclick = async () => {
		if (A && !k) {
			k = !0, l("#jobenu-retry-confirm").disabled = !0, l("#jobenu-retry-cancel").disabled = !0, l("#jobenu-retry-error").textContent = "", l("#jobenu-retry-progress").textContent = "Starting retry…";
			try {
				await a("/api/jobenu/start", {
					id: A.id,
					planId: A.plan.plan_id
				}), A = null, l("#jobenu-retry").close(), l("#jobenu-feedback").textContent = "Retry started. Follow progress in Batch activity.", w = "", await $(), l("#jobenu-history").focus();
			} catch (e) {
				l("#jobenu-retry-error").textContent = e.message;
			} finally {
				k = !1, O = l("#jobenu-retry").open, l("#jobenu-retry-cancel").disabled = !1, l("#jobenu-retry-confirm").disabled = !A, P();
			}
		}
	};
	let R = (e) => l("#jobenu-error").textContent = e?.message || e || "";
	function z() {
		S++, h = null, l("#jobenu-start").disabled = !0, l("#jobenu-plan tbody").replaceChildren(), l("#jobenu-aliases").replaceChildren(), l("#jobenu-aliases").hidden = !0, U();
	}
	function B() {
		let e = l("#jobenu-approval").value, t = v && v !== e && [v, e].includes("unattended"), n = l(t ? "#jobenu-approval-change" : "#jobenu-advanced"), r = l("#jobenu-rerun-choice");
		r.parentElement !== n && n.append(r), l("#jobenu-approval-change").hidden = !t;
		let i = e === "unattended" && !_, a = i ? "Update Vita CV and check the installation to run without manual reviews." : ({
			human: "Review changes and job requirements before continuing.",
			auto: "Only verified changes apply automatically. Other changes and job requirements can still need review.",
			unattended: "AI changes and job requirements are approved without review. AI wording can be inaccurate. Validation and file-conflict checks still run."
		}[e] || "") + (t ? l("#jobenu-rerun").checked ? " Completed steps will run again and use AI credits." : " To switch this saved batch, select Rerun completed steps (uses AI credits)." : "") + (g && !_ ? " Update Vita CV to enable running without manual reviews." : ""), o = l("#jobenu-approval-help");
		return o.textContent !== a && (o.textContent = a), i || !(!t || l("#jobenu-rerun").checked);
	}
	function V() {
		return {
			dateField: l("#jobenu-date-field").value,
			dateFrom: l("#jobenu-date-from").value,
			dateTo: l("#jobenu-date-to").value
		};
	}
	function H() {
		let { dateField: e, dateFrom: t, dateTo: n } = V();
		return (m?.applications || []).filter((r) => {
			let i = r.dates?.[e];
			return !t && !n || i && (!t || i >= t) && (!n || i <= n);
		});
	}
	function U() {
		let e = B(), t = H(), n = t.filter((e) => T.has(e.id)).length, { dateField: r, dateFrom: i, dateTo: a } = V(), o = !!(i && a && i > a);
		l("#jobenu-date-error").textContent = o ? "The end date must be on or after the start date." : "";
		for (let e of ["from", "to"]) l("#jobenu-date-" + e).setAttribute("aria-invalid", String(o));
		let s = (m?.applications || []).filter((e) => !e.dates?.[r]).length;
		l("#jobenu-selection-summary").textContent = `${t.length ? `${n} selected · ${t.length} matching` : "No jobs match these dates"} · ${m?.applications?.length || 0} in export${s ? ` · ${s} without a date${i || a ? " (excluded)" : ""}` : ""}`, l("#jobenu-select-all").checked = n > 0 && n === t.length, l("#jobenu-select-all").indeterminate = n > 0 && n < t.length, l("#jobenu-select-all").disabled = !t.length || o, l("#jobenu-preview").disabled = !g || y || E || o || !n || e;
	}
	function W() {
		l("#jobenu-date-filters").hidden = !m, l("#jobenu-date-heading").textContent = l("#jobenu-date-field").selectedOptions[0].textContent;
		let e = l("#jobenu-selection tbody");
		e.replaceChildren();
		for (let t of H()) {
			let n = document.createElement("tr"), r = document.createElement("td"), i = document.createElement("input");
			i.type = "checkbox", i.value = t.id, i.checked = T.has(t.id), i.setAttribute("aria-label", `Select ${t.company} · ${t.position}`), i.onchange = () => {
				i.checked ? T.add(t.id) : T.delete(t.id), z(), U();
			}, r.append(i);
			let a = u("td", t.dates?.[l("#jobenu-date-field").value] || "—");
			a.dataset.label = l("#jobenu-date-heading").textContent, n.append(r, ...[
				"company",
				"position",
				"status"
			].map((e) => u("td", t[e])), a), e.append(n);
		}
		U();
	}
	for (let e of [
		"field",
		"from",
		"to"
	]) l("#jobenu-date-" + e).addEventListener("input", () => {
		z(), W();
	});
	l("#jobenu-select-all").onchange = (e) => {
		for (let t of H()) e.target.checked ? T.add(t.id) : T.delete(t.id);
		z(), W();
	}, l("#jobenu-today").onclick = () => {
		let e = /* @__PURE__ */ new Date(), t = `${e.getFullYear()}-${String(e.getMonth() + 1).padStart(2, "0")}-${String(e.getDate()).padStart(2, "0")}`;
		l("#jobenu-date-from").value = l("#jobenu-date-to").value = t, z(), W();
	}, l("#jobenu-all-dates").onclick = () => {
		l("#jobenu-date-from").value = l("#jobenu-date-to").value = "", z(), W();
	};
	function G() {
		return {
			id: m.id,
			ids: H().filter((e) => T.has(e.id)).map((e) => e.id),
			...V(),
			base: l("#jobenu-base").value,
			approval: l("#jobenu-approval").value,
			run: l("#jobenu-run").checked,
			source: l("#jobenu-source").value,
			language: l("#jobenu-language").value,
			provider: l("#jobenu-provider").value,
			statuses: l("#jobenu-statuses").value.split(",").map((e) => e.trim().toUpperCase()).filter(Boolean),
			includeDemo: l("#jobenu-demo").checked,
			newRevision: l("#jobenu-revision").checked,
			rerun: l("#jobenu-rerun").checked
		};
	}
	async function K() {
		await c(), g = !1, l("#jobenu-preview").disabled = !0, z();
		let e = await a("/api/jobenu/capability", { source: l("#jobenu-source").value });
		g = e.available, l("#jobenu-limitations").textContent = (e.limitations || []).join(" "), _ = e.unattended === !0, l("#jobenu-approval option[value=unattended]").disabled = !_, l("#jobenu-capability").textContent = e.message || "Jobenu batch import is available.", l("#jobenu-install").open = !g, l("#jobenu-base").value || (l("#jobenu-base").value = e.base), U();
	}
	async function q() {
		p.hidden = !1, l("#board").hidden = !0, l("#workspace").hidden = !0, l("#jobenu-bases").replaceChildren(...o().filter((e) => e.local).map((e) => {
			let t = document.createElement("option");
			return t.value = e.name, t;
		}));
		try {
			await c(), await K(), await $();
		} catch (e) {
			R(e);
		}
		l("#jobenu-file").focus();
	}
	f.onclick = q, l("#jobenu-back").onclick = () => {
		p.hidden = !0, l("#board").hidden = !1;
	}, l("#jobenu-check").onclick = () => K().catch(R);
	async function J(e) {
		if (!e) return;
		let t = ++C;
		if (m = null, v = null, l("#jobenu-rerun").checked = !1, T.clear(), D.clear(), z(), W(), l("#jobenu-file-info").textContent = "Reading export…", R(""), e.size > 10485760) R("Choose a JSON export smaller than 10 MiB.");
		else try {
			await c();
			let n = await a("/api/jobenu/upload", {
				filename: e.name,
				content: await e.text()
			});
			if (t !== C) return;
			m = n, l("#jobenu-date-field").value = "createdAt", l("#jobenu-date-from").value = l("#jobenu-date-to").value = "", T = new Set(m.applications.filter((e) => e.status === "SAVED" && !e.isDemo).map((e) => e.id)), l("#jobenu-file-info").textContent = `${m.filename} · ${m.applications.length} applications`, W();
		} catch (e) {
			R(e);
		}
	}
	l("#jobenu-file").onchange = (e) => J(e.target.files[0]), l("#jobenu-drop").ondragover = (e) => e.preventDefault(), l("#jobenu-drop").ondrop = (e) => {
		e.preventDefault(), J(e.dataTransfer.files[0]);
	};
	for (let e of [
		"base",
		"approval",
		"run",
		"source",
		"language",
		"provider",
		"statuses",
		"demo",
		"revision",
		"rerun"
	]) l("#jobenu-" + e).addEventListener("input", z);
	async function Y() {
		if (y || E || !m || !g || !G().ids.length) return;
		y = !0, z();
		let e = S;
		R(""), l("#jobenu-preview").disabled = !0;
		try {
			let t = await a("/api/jobenu/preview", G());
			if (S !== e) return;
			h = t.plan, l("#jobenu-settings-limitations").textContent = (t.settingsLimitations || []).join(" "), h.error && R(h.error);
			let n = l("#jobenu-plan tbody");
			n.replaceChildren();
			for (let e of h.entries) {
				let t = document.createElement("tr");
				t.append(...[
					"company",
					"position",
					"branch",
					"action"
				].map((t) => {
					let n = u("td", e[t]);
					return n.dataset.label = t === "branch" ? "Application" : t, n;
				})), n.append(t);
			}
			X(h.entries);
			let r = h.entries.filter((e) => e.action === "create").length;
			l("#jobenu-start").textContent = r ? `Create ${r} branches${l("#jobenu-run").checked ? " and run" : ""}` : `Continue ${h.entries.length} application${h.entries.length === 1 ? "" : "s"}`, l("#jobenu-start").disabled = h.entries.some((e) => !["create", "existing"].includes(e.action)) || t.status !== "planned" || !h.entries.length;
		} catch (e) {
			R(e);
		} finally {
			y = !1, U();
		}
	}
	function X(e) {
		let t = [...new Set(e.filter((e) => e.role_resolution === "slug_fallback").map((e) => e.position))], n = l("#jobenu-aliases");
		if (n.replaceChildren(), n.hidden = !t.length, !t.length) return;
		let r = u("h2", "Short role names"), i = u("p", "Optional: give these roles shorter names for your application branches. Save all names together.");
		r.id = "jobenu-alias-title", i.className = "helper";
		let o = document.createElement("form"), s = document.createElement("fieldset"), c = document.createElement("div");
		c.className = "jobenu-alias-fields";
		let d = t.map((e) => {
			let t = u("label", e), n = document.createElement("input");
			return n.value = D.get(e) || "", n.placeholder = "e.g. ml-engineer", n.pattern = "[a-z0-9][a-z0-9-]{0,63}", n.maxLength = 64, n.setAttribute("aria-describedby", "jobenu-alias-help"), n.oninput = () => {
				D.set(e, n.value), m.disabled = !d.some((e) => e.value.trim());
			}, t.append(n), c.append(t), n;
		}), f = u("p", "Lowercase letters, numbers and hyphens, up to 64 characters. Leave any role blank to keep its current name."), p = u("p", ""), m = u("button", "Save aliases & update preview");
		f.id = "jobenu-alias-help", f.className = "helper", p.id = "jobenu-alias-error", p.className = "form-error", p.setAttribute("role", "alert"), m.type = "submit", m.disabled = !d.some((e) => e.value.trim()), s.append(c, f, p, m), o.append(s), o.onsubmit = async (e) => {
			if (e.preventDefault(), y || E) return;
			let n = t.map((e, t) => ({
				title: e,
				alias: d[t].value.trim()
			})).filter((e) => e.alias);
			if (n.length) {
				E = !0, s.disabled = !0, m.textContent = "Saving aliases…", p.textContent = "", S++, h = null, l("#jobenu-start").disabled = !0, U();
				try {
					await a("/api/jobenu/aliases", { aliases: n });
					for (let { title: e } of n) D.delete(e);
					l("#jobenu-feedback").textContent = `${n.length} role alias${n.length === 1 ? "" : "es"} saved. Updating preview…`, E = !1, await Y(), l("#jobenu-preview").focus();
				} catch (e) {
					p.textContent = e.message, p.isConnected || R(e);
				} finally {
					E = !1, s.disabled = !1, m.textContent = "Save aliases & update preview", U();
				}
			}
		}, n.append(r, i, o);
	}
	l("#jobenu-preview").onclick = Y, l("#jobenu-start").onclick = async () => {
		if (y || !h) return;
		y = !0, U();
		let e = h.plan_id;
		l("#jobenu-start").disabled = !0, R("");
		try {
			await a("/api/jobenu/start", {
				id: m.id,
				planId: e
			}), z(), await $();
		} catch (e) {
			R(e);
		} finally {
			y = !1, U();
		}
	};
	async function Z(e, t) {
		b = {
			batch: e,
			entry: t,
			...await a("/api/jobenu/review", {
				id: e.id,
				key: t.key
			})
		};
		let n = l("#jobenu-review-content");
		n.replaceChildren(), l("#jobenu-review-error").textContent = "", l("#jobenu-reject").hidden = b.kind !== "facts";
		let r = b.kind === "facts" && [
			"approved",
			"applied",
			"rejected"
		].includes(b.report.status);
		if (l("#jobenu-approve").disabled = r, l("#jobenu-reject").disabled = r, l("#jobenu-approve").textContent = b.needsDraft ? "Generate requirement draft" : "Approve exact revision", b.kind === "facts") {
			let e = b.report;
			n.append(u("p", `Revision ${e.revision}`));
			for (let t of e.changes) {
				let e = document.createElement("article");
				e.className = "factual-change", e.append(u("h3", "Confirm the meaning of this change"), u("h4", "Original wording"), u("pre", t.original), u("h4", "Proposed wording"), u("pre", t.proposed));
				let r = e.querySelectorAll("pre");
				for (let [e, n] of [...r].entries()) n.className = e ? "wording-after" : "wording-before", i(n, e ? t.proposed : t.original, 0, (e ? t.proposed : t.original).length);
				let a = u("p", `Category: ${t.kind || t.reason} · ${t.verification || "Requires review"} · Source facts: ${(t.source_fact_ids || []).join(", ")}`);
				e.append(a);
				for (let n of t.source_fact_ids || []) {
					let t = b.report.source_facts?.find((e) => e.id === n)?.source_ref;
					if (!t) continue;
					let r = b.report.candidate_sources?.sources?.find((e) => e.id === t.source_id)?.path || "Captured source", i = document.createElement("details");
					i.append(u("summary", `${r} · lines ${t.line_start}–${t.line_end}`), u("pre", t.quote)), e.append(i);
				}
				n.append(e);
			}
			n.append(u("p", "Approve only after checking every factual interpretation against the captured sources."));
		} else if (b.needsDraft) n.append(u("p", "Canonical requirements need a separate draft and explicit approval. Generating a draft uses your configured AI provider."));
		else {
			n.append(u("p", "Review the immutable requirement definition, classifications and source references before approval."), u("p", `Revision ${b.report.revision.revision}`));
			let e = b.report.revision;
			for (let [t, r] of [["requirements", "Requirements"], ["employment_conditions", "Employment conditions"]]) {
				n.append(u("h3", r));
				for (let r of e[t] || []) {
					let e = document.createElement("article");
					e.className = "factual-change", e.append(u("h4", r.criterion || r.text || r.label || r.key), u("p", `${r.classification || r.kind || ""} · ${r.category || ""}`));
					let t = document.createElement("details");
					t.append(u("summary", "Source references and definition"), u("pre", JSON.stringify(r, null, 2))), e.append(t), n.append(e);
				}
			}
		}
		l("#jobenu-review").open || l("#jobenu-review").showModal();
	}
	l("#jobenu-review-close").onclick = () => l("#jobenu-review").close();
	async function Q(e) {
		let t = l("#jobenu-approve");
		t.disabled = !0, l("#jobenu-reject").disabled = !0;
		try {
			let t = b.kind === "facts" ? b.report.revision : b.report?.revision?.revision;
			await a("/api/jobenu/decide", {
				id: b.batch.id,
				key: b.entry.key,
				action: b.needsDraft ? "draft" : e,
				revision: t
			}), b.needsDraft ? await Z(b.batch, b.entry) : (l("#jobenu-review").close(), l("#jobenu-feedback").textContent = "Decision saved. Use Preview resume to review the remaining work before continuing.", await $());
		} catch (e) {
			l("#jobenu-review-error").textContent = e.message;
		} finally {
			t.disabled = !1, l("#jobenu-reject").disabled = !1;
		}
	}
	l("#jobenu-approve").onclick = () => Q("approve"), l("#jobenu-reject").onclick = () => Q("reject");
	async function $() {
		if (!x) {
			x = !0;
			try {
				let { batches: i } = await a("/api/jobenu"), o = r(i), c = JSON.stringify(o);
				if (c === w) return;
				w = c;
				let f = l("#jobenu-history");
				f.replaceChildren();
				for (let r of o) {
					let i = r.batch, o = n(r), c = document.createElement("section");
					c.className = "jobenu-batch";
					let h = document.createElement("div");
					h.append(u("h3", i.filename), u("p", t(r, d)));
					let g = document.createElement("div");
					if (g.className = "jobenu-batch-heading", g.append(h), r.entries.some(e) || r.attempts.some((e) => e.parentBatchId && e.status === "running")) {
						let e = u("button", "Retry failed jobs");
						e.className = "jobenu-retry-action", e.dataset.batch = i.id, e.dataset.key = "", e.dataset.blocked = String(o), e.onclick = () => L(i), g.append(e);
					}
					c.append(g);
					let _ = r.attempts.at(-1);
					_.error && c.append(u("p", _.error));
					let y = document.createElement("table"), b = document.createElement("thead"), x = document.createElement("tr");
					for (let e of [
						"Company",
						"Position",
						"Progress",
						"Actions"
					]) x.append(u("th", e));
					b.append(x), y.append(b);
					for (let t of r.entries) {
						let n = document.createElement("tr");
						n.className = "jobenu-application-row", n.append(u("td", t.company), u("td", t.position), u("td", [
							d(t.status || t.action),
							d(t.current_step),
							(t.completed_steps || []).map(d).join(" → ")
						].filter(Boolean).join(" · "))), t.error && n.lastElementChild.append(u("p", t.error));
						let r = document.createElement("td");
						if (e(t)) {
							let e = u("button", "Retry");
							e.className = "jobenu-retry-action", e.dataset.batch = i.id, e.dataset.key = t.key, e.setAttribute("aria-label", `Retry ${t.company}`), e.dataset.blocked = String(o), e.onclick = () => L(i, [t.key]), r.append(e);
						}
						if (t.workspace) {
							let e = u("button", "Open workspace");
							e.onclick = async () => {
								p.hidden = !0, await s(t.branch);
							}, r.append(e);
						}
						if (t.execution_log) {
							let e = u("button", "Application log");
							e.onclick = async () => {
								try {
									let e = await a("/api/jobenu/log", {
										id: i.id,
										key: t.key
									});
									c.append(u("pre", e.text));
								} catch (e) {
									R(e);
								}
							}, r.append(e);
						}
						if (t.pending || t.status === "awaiting_requirements_approval") {
							let e = u("button", t.pending ? "Review changes" : "Review requirements");
							e.onclick = () => Z(i, t).catch(R), r.append(e);
						}
						n.append(r), y.append(n);
					}
					let S = document.createElement("div");
					if (S.className = "jobenu-scroll", S.tabIndex = 0, S.setAttribute("role", "region"), S.setAttribute("aria-label", `Applications from ${i.filename}`), S.append(y), c.append(S), r.attempts.length > 1) {
						let e = document.createElement("details");
						e.className = "jobenu-attempts", e.append(u("summary", `Attempts (${r.attempts.length})`));
						for (let [t, n] of r.attempts.entries()) e.append(u("p", `${t ? "Retry" : "Original run"} · ${(/* @__PURE__ */ new Date((n.startedAt || n.createdAt) * 1e3)).toLocaleString()} · ${d(n.status)}`));
						c.append(e);
					}
					let C = u("button", "View logs");
					if (C.onclick = async () => {
						try {
							let e = await a("/api/jobenu/log", { id: i.id }), t = u("pre", e.text);
							c.append(t);
						} catch (e) {
							R(e);
						}
					}, c.append(C), !o) {
						let e = u("button", "Preview resume");
						e.onclick = async () => {
							z(), m = { id: i.id };
							let e = i.options || {};
							v = i.startedAt && e.run ? e.approval || "human" : null, l("#jobenu-base").value = e.base || "", l("#jobenu-source").value = e.source || "", l("#jobenu-approval").value = e.approval || "human", l("#jobenu-run").checked = e.run !== !1;
							for (let t of ["language", "provider"]) l("#jobenu-" + t).value = e[t] || "";
							l("#jobenu-statuses").value = (e.statuses || ["SAVED"]).join(","), l("#jobenu-demo").checked = !!e.includeDemo, l("#jobenu-revision").checked = !!e.newRevision, l("#jobenu-rerun").checked = !1;
							let t = await a("/api/jobenu/selection", { id: i.id });
							m.applications = t.applications, T = new Set(e.ids || []), D.clear(), l("#jobenu-date-field").value = e.dateField || "createdAt", l("#jobenu-date-from").value = e.dateFrom || "", l("#jobenu-date-to").value = e.dateTo || "", l("#jobenu-file-info").textContent = `${i.filename} · ${t.applications.length} applications`, W(), await K(), await Y();
						}, c.append(e);
						let t = u("button", "Forget batch");
						t.onclick = async () => {
							confirm("Forget this private export and batch history? Imported CV workspaces are kept.") && (await a("/api/jobenu/discard", { id: i.id }), await $());
						}, c.append(t);
					}
					f.append(c);
				}
				P();
			} catch (e) {
				R(e);
			} finally {
				x = !1;
			}
		}
	}
	setInterval(() => {
		p.hidden || $();
	}, 1800);
	async function ee(e) {
		let { batches: t } = await a("/api/jobenu"), n = t.find((t) => t.id === e.nativeBatchId), r = n?.entries?.find((t) => t.key === e.nativeKey && t.branch === e.branch);
		if (!r || e.pendingRevision && r.pending?.revision !== e.pendingRevision) throw Error("This pending review changed. Refresh the application before reviewing.");
		l("#jobenu-review-error").textContent = "", await Z(n, r);
	}
	return {
		open: q,
		reviewRun: ee
	};
}
export { a as t };
