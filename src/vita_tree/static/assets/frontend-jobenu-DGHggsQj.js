import { n as e, r as t, t as n } from "./frontend-jobenu-history-DAQVDk9-.js";
import { renderLatexSnippet as r } from "/vendor/editor.mjs";
// frontend/src/compat/jobenu.js
function i({ api: i, branches: a, openBranch: o, ready: s }) {
	let c = (e) => document.querySelector(e), l = (e, t) => {
		let n = document.createElement(e);
		return n.textContent = t, n;
	}, u = (e) => ({
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
	})[e] || e || "", d = l("button", "Import jobs");
	d.id = "open-jobenu", d.className = "quiet", c(".board-nav").append(d);
	let f = document.createElement("section");
	f.id = "jobenu-import", f.hidden = !0, f.innerHTML = "<button id=\"jobenu-back\" class=\"back\">← All applications</button><div class=\"page-heading\"><div><h1>Import jobs</h1><p class=\"subtitle\">Bring opportunities from Jobenu into this CV collection.</p></div></div>\n <div role=\"tablist\" aria-label=\"Import source\" class=\"jobenu-tabs\"><button role=\"tab\" aria-selected=\"true\">Jobenu</button></div>\n <p class=\"helper\">Your export stays unchanged. Each selected application gets its own CV workspace. Importing never submits an application or pushes to Git.</p>\n <p id=\"jobenu-error\" role=\"alert\" class=\"form-error\"></p><p id=\"jobenu-feedback\" role=\"status\"></p>\n <details id=\"jobenu-install\"><summary>Vita installation</summary><label>Compatible Vita CV source folder<input id=\"jobenu-source\" placeholder=\"Folder containing vita/__main__.py\"></label><button id=\"jobenu-check\">Check installation</button><p id=\"jobenu-capability\" role=\"status\"></p></details>\n <label id=\"jobenu-drop\" class=\"jobenu-drop\">Choose or drop a Jobenu JSON export<input id=\"jobenu-file\" type=\"file\" accept=\".json,application/json\"></label><p id=\"jobenu-file-info\" role=\"status\"></p>\n <div id=\"jobenu-date-filters\" hidden><div class=\"jobenu-date-toolbar\"><label>Date<select id=\"jobenu-date-field\"><option value=\"createdAt\">Added</option><option value=\"updatedAt\">Updated</option><option value=\"appliedAt\">Applied</option><option value=\"deadlineAt\">Deadline</option><option value=\"nextActionAt\">Next action</option></select></label><label>From<input id=\"jobenu-date-from\" type=\"date\" aria-describedby=\"jobenu-date-help jobenu-date-error\"></label><label>To<input id=\"jobenu-date-to\" type=\"date\" aria-describedby=\"jobenu-date-help jobenu-date-error\"></label><div class=\"actions\"><button id=\"jobenu-today\">Today</button><button id=\"jobenu-all-dates\">All dates</button></div></div><p id=\"jobenu-date-help\" class=\"helper\">Dates follow the calendar day in your export. Today uses your device's date.</p><p id=\"jobenu-date-error\" role=\"alert\" class=\"form-error\"></p><p id=\"jobenu-selection-summary\" role=\"status\"></p></div>\n <div class=\"jobenu-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Applications to import\"><table id=\"jobenu-selection\"><caption>Select applications</caption><thead><tr><th><input id=\"jobenu-select-all\" type=\"checkbox\" aria-label=\"Select all matching jobs\"></th><th>Company</th><th>Position</th><th>Status</th><th id=\"jobenu-date-heading\">Added</th></tr></thead><tbody></tbody></table></div>\n <div class=\"jobenu-settings\"><label>Starting CV<input id=\"jobenu-base\" type=\"search\" list=\"jobenu-bases\" autocomplete=\"off\" placeholder=\"Search local branches\"><datalist id=\"jobenu-bases\"></datalist></label><label>Approval mode<select id=\"jobenu-approval\" aria-describedby=\"jobenu-approval-help\"><option value=\"human\">Review changes before applying</option><option value=\"auto\">Apply verified changes automatically</option><option value=\"unattended\" disabled>Run without manual reviews</option></select></label></div>\n <p id=\"jobenu-approval-help\" class=\"helper\" role=\"status\"></p><div id=\"jobenu-approval-change\" hidden></div>\n <label><input id=\"jobenu-run\" type=\"checkbox\" checked> Run the AI workflow</label><p class=\"helper\">Complete means the configured AI stages finished; PDFs and submission are separate.</p>\n <details id=\"jobenu-advanced\"><summary>Advanced</summary><div class=\"jobenu-settings\"><label>Language override<input id=\"jobenu-language\" placeholder=\"Use saved language\"></label><label>Provider override<input id=\"jobenu-provider\" placeholder=\"Use saved AI settings\"></label><label>Status filters<input id=\"jobenu-statuses\" value=\"SAVED\" aria-describedby=\"jobenu-status-help\"></label></div><p id=\"jobenu-status-help\" class=\"helper\">Comma-separated statuses, or ALL. Uses saved stage providers/models and native Vita reasoning preferences. Tree-only reasoning overrides are not forwarded by this batch CLI.</p><label><input id=\"jobenu-demo\" type=\"checkbox\"> Include demo applications</label><label><input id=\"jobenu-revision\" type=\"checkbox\"> Create a new source revision when records changed</label><label id=\"jobenu-rerun-choice\"><input id=\"jobenu-rerun\" type=\"checkbox\"> Rerun completed steps (uses AI credits)</label></details>\n <div class=\"actions\"><button id=\"jobenu-preview\" disabled>Preview branches</button><button id=\"jobenu-start\" class=\"primary\" disabled>Create branches</button></div>\n <div class=\"jobenu-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Application preview\"><table id=\"jobenu-plan\"><caption>Branch preview</caption><thead><tr><th>Company</th><th>Position</th><th>Branch</th><th>Action</th></tr></thead><tbody></tbody></table></div><section id=\"jobenu-aliases\" hidden aria-labelledby=\"jobenu-alias-title\"></section>\n <h2>Batch activity</h2><p class=\"helper\">You can leave this view while work continues. Retained sources stay private until you forget the batch; imported workspaces are preserved.</p><div id=\"jobenu-history\" tabindex=\"-1\" role=\"region\" aria-label=\"Batch activity\"></div>\n <dialog id=\"jobenu-retry\" aria-labelledby=\"jobenu-retry-title\"><div class=\"dialog-heading\"><h2 id=\"jobenu-retry-title\">Retry failed jobs</h2></div><div class=\"review-scroll\"><p>Use the original AI settings. Keep valid completed steps and continue from the failure. Retrying makes AI requests and may use provider credits.</p><p id=\"jobenu-retry-progress\" role=\"status\"></p><div class=\"jobenu-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Jobs to retry\"><table><thead><tr><th>Company</th><th>Position</th><th>Continue from</th></tr></thead><tbody id=\"jobenu-retry-jobs\"></tbody></table></div><p id=\"jobenu-retry-error\" role=\"alert\" class=\"form-error\"></p></div><footer class=\"dialog-footer\"><button id=\"jobenu-retry-cancel\">Cancel</button><button id=\"jobenu-retry-confirm\" class=\"primary\" disabled>Retry jobs</button></footer></dialog>\n <dialog id=\"jobenu-review\" aria-labelledby=\"jobenu-review-title\"><div class=\"dialog-heading\"><h2 id=\"jobenu-review-title\">Review imported application</h2><button id=\"jobenu-review-close\" aria-label=\"Close import review\">×</button></div><div id=\"jobenu-review-content\" class=\"review-scroll\"></div><p id=\"jobenu-review-error\" role=\"alert\" class=\"form-error\"></p><footer class=\"dialog-footer\"><button id=\"jobenu-reject\">Reject changes</button><button id=\"jobenu-approve\" class=\"primary\">Approve exact revision</button></footer></dialog>", c("#main-content").append(f);
	let p = null, m = null, h = !1, g = !1, _ = null, v = !1, y = null, b = !1, x = 0, S = 0, C = "", w = /* @__PURE__ */ new Set(), T = !1, E = /* @__PURE__ */ new Map(), D = !1, O = !1, k = null, A = 0, j = null, M = (e) => ({
		extract: "Identify job requirements",
		analyze: "Check CV match",
		adapt: "Tailor CV",
		review: "Review CV",
		cover: "Cover letter"
	})[e] || e || "Last unfinished step";
	function N() {
		for (let e of f.querySelectorAll(".jobenu-retry-action")) e.disabled = D || e.dataset.blocked === "true";
	}
	async function P(e) {
		e && await i("/api/jobenu/discard", { id: e.id });
	}
	async function F() {
		if (O) return;
		A++;
		let e = k;
		k = null, D = !1, c("#jobenu-retry").close(), N(), ([...f.querySelectorAll(".jobenu-retry-action")].find((e) => e.dataset.batch === j?.batch && e.dataset.key === j?.key) || c("#jobenu-history")).focus();
		try {
			await P(e);
		} catch (e) {
			L(e);
		}
	}
	c("#jobenu-retry-cancel").onclick = F, c("#jobenu-retry").oncancel = (e) => {
		e.preventDefault(), F();
	};
	async function I(e, t) {
		if (D) return;
		D = !0, j = {
			batch: e.id,
			key: t?.[0] || ""
		};
		let n = ++A;
		N(), c("#jobenu-retry-error").textContent = "", c("#jobenu-retry-progress").textContent = "Checking saved steps and settings…", c("#jobenu-retry-jobs").replaceChildren(), c("#jobenu-retry-confirm").disabled = !0, c("#jobenu-retry").showModal();
		try {
			let r = await i("/api/jobenu/retry-preview", {
				id: e.id,
				...t ? { keys: t } : {}
			});
			if (n !== A) {
				await P(r);
				return;
			}
			k = r;
			for (let e of r.entries) {
				let t = document.createElement("tr"), n = e.current_step, i = r.capturedRoutes?.[n], a = l("td", M(n));
				a.append(l("p", i?.provider ? `${i.provider}${i.model ? " / " + i.model : ""}` : "Saved Vita CV settings")), a.lastElementChild.className = "helper", t.append(l("td", e.company), l("td", e.position), a), c("#jobenu-retry-jobs").append(t);
			}
			c("#jobenu-retry-progress").textContent = `${r.entries.length} failed job${r.entries.length === 1 ? "" : "s"} ready to retry.`, c("#jobenu-retry-confirm").textContent = `Retry ${r.entries.length} job${r.entries.length === 1 ? "" : "s"}`, c("#jobenu-retry-confirm").disabled = !1;
		} catch (e) {
			n === A && (c("#jobenu-retry-progress").textContent = "", c("#jobenu-retry-error").textContent = e.message);
		}
	}
	c("#jobenu-retry-confirm").onclick = async () => {
		if (k && !O) {
			O = !0, c("#jobenu-retry-confirm").disabled = !0, c("#jobenu-retry-cancel").disabled = !0, c("#jobenu-retry-error").textContent = "", c("#jobenu-retry-progress").textContent = "Starting retry…";
			try {
				await i("/api/jobenu/start", {
					id: k.id,
					planId: k.plan.plan_id
				}), k = null, c("#jobenu-retry").close(), c("#jobenu-feedback").textContent = "Retry started. Follow progress in Batch activity.", C = "", await Q(), c("#jobenu-history").focus();
			} catch (e) {
				c("#jobenu-retry-error").textContent = e.message;
			} finally {
				O = !1, D = c("#jobenu-retry").open, c("#jobenu-retry-cancel").disabled = !1, c("#jobenu-retry-confirm").disabled = !k, N();
			}
		}
	};
	let L = (e) => c("#jobenu-error").textContent = e?.message || e || "";
	function R() {
		x++, m = null, c("#jobenu-start").disabled = !0, c("#jobenu-plan tbody").replaceChildren(), c("#jobenu-aliases").replaceChildren(), c("#jobenu-aliases").hidden = !0, H();
	}
	function z() {
		let e = c("#jobenu-approval").value, t = _ && _ !== e && [_, e].includes("unattended"), n = c(t ? "#jobenu-approval-change" : "#jobenu-advanced"), r = c("#jobenu-rerun-choice");
		r.parentElement !== n && n.append(r), c("#jobenu-approval-change").hidden = !t;
		let i = e === "unattended" && !g, a = i ? "Update Vita CV and check the installation to run without manual reviews." : ({
			human: "Review changes and job requirements before continuing.",
			auto: "Only verified changes apply automatically. Other changes and job requirements can still need review.",
			unattended: "AI changes and job requirements are approved without review. AI wording can be inaccurate. Validation and file-conflict checks still run."
		}[e] || "") + (t ? c("#jobenu-rerun").checked ? " Completed steps will run again and use AI credits." : " To switch this saved batch, select Rerun completed steps (uses AI credits)." : "") + (h && !g ? " Update Vita CV to enable running without manual reviews." : ""), o = c("#jobenu-approval-help");
		return o.textContent !== a && (o.textContent = a), i || !(!t || c("#jobenu-rerun").checked);
	}
	function B() {
		return {
			dateField: c("#jobenu-date-field").value,
			dateFrom: c("#jobenu-date-from").value,
			dateTo: c("#jobenu-date-to").value
		};
	}
	function V() {
		let { dateField: e, dateFrom: t, dateTo: n } = B();
		return (p?.applications || []).filter((r) => {
			let i = r.dates?.[e];
			return !t && !n || i && (!t || i >= t) && (!n || i <= n);
		});
	}
	function H() {
		let e = z(), t = V(), n = t.filter((e) => w.has(e.id)).length, { dateField: r, dateFrom: i, dateTo: a } = B(), o = !!(i && a && i > a);
		c("#jobenu-date-error").textContent = o ? "The end date must be on or after the start date." : "";
		for (let e of ["from", "to"]) c("#jobenu-date-" + e).setAttribute("aria-invalid", String(o));
		let s = (p?.applications || []).filter((e) => !e.dates?.[r]).length;
		c("#jobenu-selection-summary").textContent = `${t.length ? `${n} selected · ${t.length} matching` : "No jobs match these dates"} · ${p?.applications?.length || 0} in export${s ? ` · ${s} without a date${i || a ? " (excluded)" : ""}` : ""}`, c("#jobenu-select-all").checked = n > 0 && n === t.length, c("#jobenu-select-all").indeterminate = n > 0 && n < t.length, c("#jobenu-select-all").disabled = !t.length || o, c("#jobenu-preview").disabled = !h || v || T || o || !n || e;
	}
	function U() {
		c("#jobenu-date-filters").hidden = !p, c("#jobenu-date-heading").textContent = c("#jobenu-date-field").selectedOptions[0].textContent;
		let e = c("#jobenu-selection tbody");
		e.replaceChildren();
		for (let t of V()) {
			let n = document.createElement("tr"), r = document.createElement("td"), i = document.createElement("input");
			i.type = "checkbox", i.value = t.id, i.checked = w.has(t.id), i.setAttribute("aria-label", `Select ${t.company} · ${t.position}`), i.onchange = () => {
				i.checked ? w.add(t.id) : w.delete(t.id), R(), H();
			}, r.append(i);
			let a = l("td", t.dates?.[c("#jobenu-date-field").value] || "—");
			a.dataset.label = c("#jobenu-date-heading").textContent, n.append(r, ...[
				"company",
				"position",
				"status"
			].map((e) => l("td", t[e])), a), e.append(n);
		}
		H();
	}
	for (let e of [
		"field",
		"from",
		"to"
	]) c("#jobenu-date-" + e).addEventListener("input", () => {
		R(), U();
	});
	c("#jobenu-select-all").onchange = (e) => {
		for (let t of V()) e.target.checked ? w.add(t.id) : w.delete(t.id);
		R(), U();
	}, c("#jobenu-today").onclick = () => {
		let e = /* @__PURE__ */ new Date(), t = `${e.getFullYear()}-${String(e.getMonth() + 1).padStart(2, "0")}-${String(e.getDate()).padStart(2, "0")}`;
		c("#jobenu-date-from").value = c("#jobenu-date-to").value = t, R(), U();
	}, c("#jobenu-all-dates").onclick = () => {
		c("#jobenu-date-from").value = c("#jobenu-date-to").value = "", R(), U();
	};
	function W() {
		return {
			id: p.id,
			ids: V().filter((e) => w.has(e.id)).map((e) => e.id),
			...B(),
			base: c("#jobenu-base").value,
			approval: c("#jobenu-approval").value,
			run: c("#jobenu-run").checked,
			source: c("#jobenu-source").value,
			language: c("#jobenu-language").value,
			provider: c("#jobenu-provider").value,
			statuses: c("#jobenu-statuses").value.split(",").map((e) => e.trim().toUpperCase()).filter(Boolean),
			includeDemo: c("#jobenu-demo").checked,
			newRevision: c("#jobenu-revision").checked,
			rerun: c("#jobenu-rerun").checked
		};
	}
	async function G() {
		await s(), h = !1, c("#jobenu-preview").disabled = !0, R();
		let e = await i("/api/jobenu/capability", { source: c("#jobenu-source").value });
		h = e.available, g = e.unattended === !0, c("#jobenu-approval option[value=unattended]").disabled = !g, c("#jobenu-capability").textContent = e.message || "Jobenu batch import is available.", c("#jobenu-install").open = !h, c("#jobenu-base").value || (c("#jobenu-base").value = e.base), H();
	}
	async function K() {
		f.hidden = !1, c("#board").hidden = !0, c("#workspace").hidden = !0, c("#jobenu-bases").replaceChildren(...a().filter((e) => e.local).map((e) => {
			let t = document.createElement("option");
			return t.value = e.name, t;
		}));
		try {
			await s(), await G(), await Q();
		} catch (e) {
			L(e);
		}
		c("#jobenu-file").focus();
	}
	d.onclick = K, c("#jobenu-back").onclick = () => {
		f.hidden = !0, c("#board").hidden = !1;
	}, c("#jobenu-check").onclick = () => G().catch(L);
	async function q(e) {
		if (!e) return;
		let t = ++S;
		if (p = null, _ = null, c("#jobenu-rerun").checked = !1, w.clear(), E.clear(), R(), U(), c("#jobenu-file-info").textContent = "Reading export…", L(""), e.size > 10485760) L("Choose a JSON export smaller than 10 MiB.");
		else try {
			await s();
			let n = await i("/api/jobenu/upload", {
				filename: e.name,
				content: await e.text()
			});
			if (t !== S) return;
			p = n, c("#jobenu-date-field").value = "createdAt", c("#jobenu-date-from").value = c("#jobenu-date-to").value = "", w = new Set(p.applications.filter((e) => e.status === "SAVED" && !e.isDemo).map((e) => e.id)), c("#jobenu-file-info").textContent = `${p.filename} · ${p.applications.length} applications`, U();
		} catch (e) {
			L(e);
		}
	}
	c("#jobenu-file").onchange = (e) => q(e.target.files[0]), c("#jobenu-drop").ondragover = (e) => e.preventDefault(), c("#jobenu-drop").ondrop = (e) => {
		e.preventDefault(), q(e.dataTransfer.files[0]);
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
	]) c("#jobenu-" + e).addEventListener("input", R);
	async function J() {
		if (v || T || !p || !h || !W().ids.length) return;
		v = !0, R();
		let e = x;
		L(""), c("#jobenu-preview").disabled = !0;
		try {
			let t = await i("/api/jobenu/preview", W());
			if (x !== e) return;
			m = t.plan, m.error && L(m.error);
			let n = c("#jobenu-plan tbody");
			n.replaceChildren();
			for (let e of m.entries) {
				let t = document.createElement("tr");
				t.append(...[
					"company",
					"position",
					"branch",
					"action"
				].map((t) => {
					let n = l("td", e[t]);
					return n.dataset.label = t === "branch" ? "Application" : t, n;
				})), n.append(t);
			}
			Y(m.entries);
			let r = m.entries.filter((e) => e.action === "create").length;
			c("#jobenu-start").textContent = r ? `Create ${r} branches${c("#jobenu-run").checked ? " and run" : ""}` : `Continue ${m.entries.length} application${m.entries.length === 1 ? "" : "s"}`, c("#jobenu-start").disabled = m.entries.some((e) => !["create", "existing"].includes(e.action)) || t.status !== "planned" || !m.entries.length;
		} catch (e) {
			L(e);
		} finally {
			v = !1, H();
		}
	}
	function Y(e) {
		let t = [...new Set(e.filter((e) => e.role_resolution === "slug_fallback").map((e) => e.position))], n = c("#jobenu-aliases");
		if (n.replaceChildren(), n.hidden = !t.length, !t.length) return;
		let r = l("h2", "Short role names"), a = l("p", "Optional: give these roles shorter names for your application branches. Save all names together.");
		r.id = "jobenu-alias-title", a.className = "helper";
		let o = document.createElement("form"), s = document.createElement("fieldset"), u = document.createElement("div");
		u.className = "jobenu-alias-fields";
		let d = t.map((e) => {
			let t = l("label", e), n = document.createElement("input");
			return n.value = E.get(e) || "", n.placeholder = "e.g. ml-engineer", n.pattern = "[a-z0-9][a-z0-9-]{0,63}", n.maxLength = 64, n.setAttribute("aria-describedby", "jobenu-alias-help"), n.oninput = () => {
				E.set(e, n.value), h.disabled = !d.some((e) => e.value.trim());
			}, t.append(n), u.append(t), n;
		}), f = l("p", "Lowercase letters, numbers and hyphens, up to 64 characters. Leave any role blank to keep its current name."), p = l("p", ""), h = l("button", "Save aliases & update preview");
		f.id = "jobenu-alias-help", f.className = "helper", p.id = "jobenu-alias-error", p.className = "form-error", p.setAttribute("role", "alert"), h.type = "submit", h.disabled = !d.some((e) => e.value.trim()), s.append(u, f, p, h), o.append(s), o.onsubmit = async (e) => {
			if (e.preventDefault(), v || T) return;
			let n = t.map((e, t) => ({
				title: e,
				alias: d[t].value.trim()
			})).filter((e) => e.alias);
			if (n.length) {
				T = !0, s.disabled = !0, h.textContent = "Saving aliases…", p.textContent = "", x++, m = null, c("#jobenu-start").disabled = !0, H();
				try {
					await i("/api/jobenu/aliases", { aliases: n });
					for (let { title: e } of n) E.delete(e);
					c("#jobenu-feedback").textContent = `${n.length} role alias${n.length === 1 ? "" : "es"} saved. Updating preview…`, T = !1, await J(), c("#jobenu-preview").focus();
				} catch (e) {
					p.textContent = e.message, p.isConnected || L(e);
				} finally {
					T = !1, s.disabled = !1, h.textContent = "Save aliases & update preview", H();
				}
			}
		}, n.append(r, a, o);
	}
	c("#jobenu-preview").onclick = J, c("#jobenu-start").onclick = async () => {
		if (v || !m) return;
		v = !0, H();
		let e = m.plan_id;
		c("#jobenu-start").disabled = !0, L("");
		try {
			await i("/api/jobenu/start", {
				id: p.id,
				planId: e
			}), R(), await Q();
		} catch (e) {
			L(e);
		} finally {
			v = !1, H();
		}
	};
	async function X(e, t) {
		y = {
			batch: e,
			entry: t,
			...await i("/api/jobenu/review", {
				id: e.id,
				key: t.key
			})
		};
		let n = c("#jobenu-review-content");
		n.replaceChildren(), c("#jobenu-review-error").textContent = "", c("#jobenu-reject").hidden = y.kind !== "facts";
		let a = y.kind === "facts" && [
			"approved",
			"applied",
			"rejected"
		].includes(y.report.status);
		if (c("#jobenu-approve").disabled = a, c("#jobenu-reject").disabled = a, c("#jobenu-approve").textContent = y.needsDraft ? "Generate requirement draft" : "Approve exact revision", y.kind === "facts") {
			let e = y.report;
			n.append(l("p", `Revision ${e.revision}`));
			for (let t of e.changes) {
				let e = document.createElement("article");
				e.className = "factual-change", e.append(l("h3", "Confirm the meaning of this change"), l("h4", "Original wording"), l("pre", t.original), l("h4", "Proposed wording"), l("pre", t.proposed));
				let i = e.querySelectorAll("pre");
				for (let [e, n] of [...i].entries()) n.className = e ? "wording-after" : "wording-before", r(n, e ? t.proposed : t.original, 0, (e ? t.proposed : t.original).length);
				let a = l("p", `Category: ${t.kind || t.reason} · ${t.verification || "Requires review"} · Source facts: ${(t.source_fact_ids || []).join(", ")}`);
				e.append(a);
				for (let n of t.source_fact_ids || []) {
					let t = y.report.source_facts?.find((e) => e.id === n)?.source_ref;
					if (!t) continue;
					let r = y.report.candidate_sources?.sources?.find((e) => e.id === t.source_id)?.path || "Captured source", i = document.createElement("details");
					i.append(l("summary", `${r} · lines ${t.line_start}–${t.line_end}`), l("pre", t.quote)), e.append(i);
				}
				n.append(e);
			}
			n.append(l("p", "Approve only after checking every factual interpretation against the captured sources."));
		} else if (y.needsDraft) n.append(l("p", "Canonical requirements need a separate draft and explicit approval. Generating a draft uses your configured AI provider."));
		else {
			n.append(l("p", "Review the immutable requirement definition, classifications and source references before approval."), l("p", `Revision ${y.report.revision.revision}`));
			let e = y.report.revision;
			for (let [t, r] of [["requirements", "Requirements"], ["employment_conditions", "Employment conditions"]]) {
				n.append(l("h3", r));
				for (let r of e[t] || []) {
					let e = document.createElement("article");
					e.className = "factual-change", e.append(l("h4", r.criterion || r.text || r.label || r.key), l("p", `${r.classification || r.kind || ""} · ${r.category || ""}`));
					let t = document.createElement("details");
					t.append(l("summary", "Source references and definition"), l("pre", JSON.stringify(r, null, 2))), e.append(t), n.append(e);
				}
			}
		}
		c("#jobenu-review").open || c("#jobenu-review").showModal();
	}
	c("#jobenu-review-close").onclick = () => c("#jobenu-review").close();
	async function Z(e) {
		let t = c("#jobenu-approve");
		t.disabled = !0, c("#jobenu-reject").disabled = !0;
		try {
			let t = y.kind === "facts" ? y.report.revision : y.report?.revision?.revision;
			await i("/api/jobenu/decide", {
				id: y.batch.id,
				key: y.entry.key,
				action: y.needsDraft ? "draft" : e,
				revision: t
			}), y.needsDraft ? await X(y.batch, y.entry) : (c("#jobenu-review").close(), c("#jobenu-feedback").textContent = "Decision saved. Use Preview resume to review the remaining work before continuing.", await Q());
		} catch (e) {
			c("#jobenu-review-error").textContent = e.message;
		} finally {
			t.disabled = !1, c("#jobenu-reject").disabled = !1;
		}
	}
	c("#jobenu-approve").onclick = () => Z("approve"), c("#jobenu-reject").onclick = () => Z("reject");
	async function Q() {
		if (!b) {
			b = !0;
			try {
				let { batches: r } = await i("/api/jobenu"), a = n(r), s = JSON.stringify(a);
				if (s === C) return;
				C = s;
				let d = c("#jobenu-history");
				d.replaceChildren();
				let m = r.some((e) => e.status === "running");
				for (let n of a) {
					let r = n.batch, a = document.createElement("section");
					a.className = "jobenu-batch";
					let s = document.createElement("div");
					s.append(l("h3", r.filename), l("p", e(n, u)));
					let h = document.createElement("div");
					if (h.className = "jobenu-batch-heading", h.append(s), n.entries.some(t) || n.attempts.some((e) => e.parentBatchId && e.status === "running")) {
						let e = l("button", "Retry failed jobs");
						e.className = "jobenu-retry-action", e.dataset.batch = r.id, e.dataset.key = "", e.dataset.blocked = String(m), e.onclick = () => I(r), h.append(e);
					}
					a.append(h);
					let g = n.attempts.at(-1);
					g.error && a.append(l("p", g.error));
					let v = document.createElement("table"), y = document.createElement("thead"), b = document.createElement("tr");
					for (let e of [
						"Company",
						"Position",
						"Progress",
						"Actions"
					]) b.append(l("th", e));
					y.append(b), v.append(y);
					for (let e of n.entries) {
						let n = document.createElement("tr");
						n.className = "jobenu-application-row", n.append(l("td", e.company), l("td", e.position), l("td", [
							u(e.status || e.action),
							u(e.current_step),
							(e.completed_steps || []).map(u).join(" → ")
						].filter(Boolean).join(" · "))), e.error && n.lastElementChild.append(l("p", e.error));
						let s = document.createElement("td");
						if (t(e)) {
							let t = l("button", "Retry");
							t.className = "jobenu-retry-action", t.dataset.batch = r.id, t.dataset.key = e.key, t.setAttribute("aria-label", `Retry ${e.company}`), t.dataset.blocked = String(m), t.onclick = () => I(r, [e.key]), s.append(t);
						}
						if (e.workspace) {
							let t = l("button", "Open workspace");
							t.onclick = async () => {
								f.hidden = !0, await o(e.branch);
							}, s.append(t);
						}
						if (e.execution_log) {
							let t = l("button", "Application log");
							t.onclick = async () => {
								try {
									let t = await i("/api/jobenu/log", {
										id: r.id,
										key: e.key
									});
									a.append(l("pre", t.text));
								} catch (e) {
									L(e);
								}
							}, s.append(t);
						}
						if (e.pending || e.status === "awaiting_requirements_approval") {
							let t = l("button", e.pending ? "Review changes" : "Review requirements");
							t.onclick = () => X(r, e).catch(L), s.append(t);
						}
						n.append(s), v.append(n);
					}
					let x = document.createElement("div");
					if (x.className = "jobenu-scroll", x.tabIndex = 0, x.setAttribute("role", "region"), x.setAttribute("aria-label", `Applications from ${r.filename}`), x.append(v), a.append(x), n.attempts.length > 1) {
						let e = document.createElement("details");
						e.className = "jobenu-attempts", e.append(l("summary", `Attempts (${n.attempts.length})`));
						for (let [t, r] of n.attempts.entries()) e.append(l("p", `${t ? "Retry" : "Original run"} · ${(/* @__PURE__ */ new Date((r.startedAt || r.createdAt) * 1e3)).toLocaleString()} · ${u(r.status)}`));
						a.append(e);
					}
					let S = l("button", "View logs");
					if (S.onclick = async () => {
						try {
							let e = await i("/api/jobenu/log", { id: r.id }), t = l("pre", e.text);
							a.append(t);
						} catch (e) {
							L(e);
						}
					}, a.append(S), !m) {
						let e = l("button", "Preview resume");
						e.onclick = async () => {
							R(), p = { id: r.id };
							let e = r.options || {};
							_ = r.startedAt && e.run ? e.approval || "human" : null, c("#jobenu-base").value = e.base || "", c("#jobenu-source").value = e.source || "", c("#jobenu-approval").value = e.approval || "human", c("#jobenu-run").checked = e.run !== !1;
							for (let t of ["language", "provider"]) c("#jobenu-" + t).value = e[t] || "";
							c("#jobenu-statuses").value = (e.statuses || ["SAVED"]).join(","), c("#jobenu-demo").checked = !!e.includeDemo, c("#jobenu-revision").checked = !!e.newRevision, c("#jobenu-rerun").checked = !1;
							let t = await i("/api/jobenu/selection", { id: r.id });
							p.applications = t.applications, w = new Set(e.ids || []), E.clear(), c("#jobenu-date-field").value = e.dateField || "createdAt", c("#jobenu-date-from").value = e.dateFrom || "", c("#jobenu-date-to").value = e.dateTo || "", c("#jobenu-file-info").textContent = `${r.filename} · ${t.applications.length} applications`, U(), await G(), await J();
						}, a.append(e);
						let t = l("button", "Forget batch");
						t.onclick = async () => {
							confirm("Forget this private export and batch history? Imported CV workspaces are kept.") && (await i("/api/jobenu/discard", { id: r.id }), await Q());
						}, a.append(t);
					}
					d.append(a);
				}
				N();
			} catch (e) {
				L(e);
			} finally {
				b = !1;
			}
		}
	}
	return setInterval(() => {
		f.hidden || Q();
	}, 1800), { open: K };
}
export { i as t };
