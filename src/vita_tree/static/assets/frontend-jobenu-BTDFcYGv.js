import { renderLatexSnippet as e } from "/vendor/editor.mjs";
// frontend/src/compat/jobenu.js
function t({ api: t, branches: n, openBranch: r, ready: i }) {
	let a = (e) => document.querySelector(e), o = (e, t) => {
		let n = document.createElement(e);
		return n.textContent = t, n;
	}, s = (e) => ({
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
	})[e] || e || "", c = o("button", "Import jobs");
	c.id = "open-jobenu", c.className = "quiet", a(".board-nav").append(c);
	let l = document.createElement("section");
	l.id = "jobenu-import", l.hidden = !0, l.innerHTML = "<button id=\"jobenu-back\" class=\"back\">← All applications</button><div class=\"page-heading\"><div><h1>Import jobs</h1><p class=\"subtitle\">Bring opportunities from Jobenu into this CV collection.</p></div></div>\n <div role=\"tablist\" aria-label=\"Import source\" class=\"jobenu-tabs\"><button role=\"tab\" aria-selected=\"true\">Jobenu</button></div>\n <p class=\"helper\">Your export stays unchanged. Each selected application gets its own CV workspace. Importing never submits an application or pushes to Git.</p>\n <p id=\"jobenu-error\" role=\"alert\" class=\"form-error\"></p><p id=\"jobenu-feedback\" role=\"status\"></p>\n <details id=\"jobenu-install\"><summary>Vita installation</summary><label>Compatible Vita CV source folder<input id=\"jobenu-source\" placeholder=\"Folder containing vita/__main__.py\"></label><button id=\"jobenu-check\">Check installation</button><p id=\"jobenu-capability\" role=\"status\"></p></details>\n <label id=\"jobenu-drop\" class=\"jobenu-drop\">Choose or drop a Jobenu JSON export<input id=\"jobenu-file\" type=\"file\" accept=\".json,application/json\"></label><p id=\"jobenu-file-info\" role=\"status\"></p>\n <div id=\"jobenu-date-filters\" hidden><div class=\"jobenu-date-toolbar\"><label>Date<select id=\"jobenu-date-field\"><option value=\"createdAt\">Added</option><option value=\"updatedAt\">Updated</option><option value=\"appliedAt\">Applied</option><option value=\"deadlineAt\">Deadline</option><option value=\"nextActionAt\">Next action</option></select></label><label>From<input id=\"jobenu-date-from\" type=\"date\" aria-describedby=\"jobenu-date-help jobenu-date-error\"></label><label>To<input id=\"jobenu-date-to\" type=\"date\" aria-describedby=\"jobenu-date-help jobenu-date-error\"></label><div class=\"actions\"><button id=\"jobenu-today\">Today</button><button id=\"jobenu-all-dates\">All dates</button></div></div><p id=\"jobenu-date-help\" class=\"helper\">Dates follow the calendar day in your export. Today uses your device's date.</p><p id=\"jobenu-date-error\" role=\"alert\" class=\"form-error\"></p><p id=\"jobenu-selection-summary\" role=\"status\"></p></div>\n <div class=\"jobenu-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Applications to import\"><table id=\"jobenu-selection\"><caption>Select applications</caption><thead><tr><th><input id=\"jobenu-select-all\" type=\"checkbox\" aria-label=\"Select all matching jobs\"></th><th>Company</th><th>Position</th><th>Status</th><th id=\"jobenu-date-heading\">Added</th></tr></thead><tbody></tbody></table></div>\n <div class=\"jobenu-settings\"><label>Starting CV<input id=\"jobenu-base\" type=\"search\" list=\"jobenu-bases\" autocomplete=\"off\" placeholder=\"Search local branches\"><datalist id=\"jobenu-bases\"></datalist></label><label>Approval mode<select id=\"jobenu-approval\"><option value=\"human\">Review changes before applying</option><option value=\"auto\">Apply verified changes automatically</option></select></label></div>\n <label><input id=\"jobenu-run\" type=\"checkbox\" checked> Run the AI workflow</label><p class=\"helper\">Automatic mode can still pause for factual or canonical-requirement confirmation. Complete means the configured AI stages finished; PDFs and submission are separate.</p>\n <details><summary>Advanced</summary><div class=\"jobenu-settings\"><label>Language override<input id=\"jobenu-language\" placeholder=\"Use saved language\"></label><label>Provider override<input id=\"jobenu-provider\" placeholder=\"Use saved AI settings\"></label><label>Status filters<input id=\"jobenu-statuses\" value=\"SAVED\" aria-describedby=\"jobenu-status-help\"></label></div><p id=\"jobenu-status-help\" class=\"helper\">Comma-separated statuses, or ALL. Uses saved stage providers/models and native Vita reasoning preferences. Tree-only reasoning overrides are not forwarded by this batch CLI.</p><label><input id=\"jobenu-demo\" type=\"checkbox\"> Include demo applications</label><label><input id=\"jobenu-revision\" type=\"checkbox\"> Create a new source revision when records changed</label><label><input id=\"jobenu-rerun\" type=\"checkbox\"> Reassess completed stages (additional AI calls)</label></details>\n <div class=\"actions\"><button id=\"jobenu-preview\" disabled>Preview branches</button><button id=\"jobenu-start\" class=\"primary\" disabled>Create branches</button></div>\n <div class=\"jobenu-scroll\" tabindex=\"0\" role=\"region\" aria-label=\"Application preview\"><table id=\"jobenu-plan\"><caption>Branch preview</caption><thead><tr><th>Company</th><th>Position</th><th>Branch</th><th>Action</th></tr></thead><tbody></tbody></table></div><section id=\"jobenu-aliases\" hidden aria-labelledby=\"jobenu-alias-title\"></section>\n <h2>Batch activity</h2><p class=\"helper\">You can leave this view while work continues. Retained sources stay private until you forget the batch; imported workspaces are preserved.</p><div id=\"jobenu-history\"></div>\n <dialog id=\"jobenu-review\" aria-labelledby=\"jobenu-review-title\"><div class=\"dialog-heading\"><h2 id=\"jobenu-review-title\">Review imported application</h2><button id=\"jobenu-review-close\" aria-label=\"Close import review\">×</button></div><div id=\"jobenu-review-content\" class=\"review-scroll\"></div><p id=\"jobenu-review-error\" role=\"alert\" class=\"form-error\"></p><footer class=\"dialog-footer\"><button id=\"jobenu-reject\">Reject changes</button><button id=\"jobenu-approve\" class=\"primary\">Approve exact revision</button></footer></dialog>", a("#main-content").append(l);
	let u = null, d = null, f = !1, p = !1, m = null, h = !1, g = 0, _ = 0, v = "", y = /* @__PURE__ */ new Set(), b = !1, x = /* @__PURE__ */ new Map(), S = (e) => a("#jobenu-error").textContent = e?.message || e || "";
	function C() {
		g++, d = null, a("#jobenu-start").disabled = !0, a("#jobenu-plan tbody").replaceChildren(), a("#jobenu-aliases").replaceChildren(), a("#jobenu-aliases").hidden = !0;
	}
	function w() {
		return {
			dateField: a("#jobenu-date-field").value,
			dateFrom: a("#jobenu-date-from").value,
			dateTo: a("#jobenu-date-to").value
		};
	}
	function T() {
		let { dateField: e, dateFrom: t, dateTo: n } = w();
		return (u?.applications || []).filter((r) => {
			let i = r.dates?.[e];
			return !t && !n || i && (!t || i >= t) && (!n || i <= n);
		});
	}
	function E() {
		let e = T(), t = e.filter((e) => y.has(e.id)).length, { dateField: n, dateFrom: r, dateTo: i } = w(), o = !!(r && i && r > i);
		a("#jobenu-date-error").textContent = o ? "The end date must be on or after the start date." : "";
		for (let e of ["from", "to"]) a("#jobenu-date-" + e).setAttribute("aria-invalid", String(o));
		let s = (u?.applications || []).filter((e) => !e.dates?.[n]).length;
		a("#jobenu-selection-summary").textContent = `${e.length ? `${t} selected · ${e.length} matching` : "No jobs match these dates"} · ${u?.applications?.length || 0} in export${s ? ` · ${s} without a date${r || i ? " (excluded)" : ""}` : ""}`, a("#jobenu-select-all").checked = t > 0 && t === e.length, a("#jobenu-select-all").indeterminate = t > 0 && t < e.length, a("#jobenu-select-all").disabled = !e.length || o, a("#jobenu-preview").disabled = !f || p || b || o || !t;
	}
	function D() {
		a("#jobenu-date-filters").hidden = !u, a("#jobenu-date-heading").textContent = a("#jobenu-date-field").selectedOptions[0].textContent;
		let e = a("#jobenu-selection tbody");
		e.replaceChildren();
		for (let t of T()) {
			let n = document.createElement("tr"), r = document.createElement("td"), i = document.createElement("input");
			i.type = "checkbox", i.value = t.id, i.checked = y.has(t.id), i.setAttribute("aria-label", `Select ${t.company} · ${t.position}`), i.onchange = () => {
				i.checked ? y.add(t.id) : y.delete(t.id), C(), E();
			}, r.append(i);
			let s = o("td", t.dates?.[a("#jobenu-date-field").value] || "—");
			s.dataset.label = a("#jobenu-date-heading").textContent, n.append(r, ...[
				"company",
				"position",
				"status"
			].map((e) => o("td", t[e])), s), e.append(n);
		}
		E();
	}
	for (let e of [
		"field",
		"from",
		"to"
	]) a("#jobenu-date-" + e).addEventListener("input", () => {
		C(), D();
	});
	a("#jobenu-select-all").onchange = (e) => {
		for (let t of T()) e.target.checked ? y.add(t.id) : y.delete(t.id);
		C(), D();
	}, a("#jobenu-today").onclick = () => {
		let e = /* @__PURE__ */ new Date(), t = `${e.getFullYear()}-${String(e.getMonth() + 1).padStart(2, "0")}-${String(e.getDate()).padStart(2, "0")}`;
		a("#jobenu-date-from").value = a("#jobenu-date-to").value = t, C(), D();
	}, a("#jobenu-all-dates").onclick = () => {
		a("#jobenu-date-from").value = a("#jobenu-date-to").value = "", C(), D();
	};
	function O() {
		return {
			id: u.id,
			ids: T().filter((e) => y.has(e.id)).map((e) => e.id),
			...w(),
			base: a("#jobenu-base").value,
			approval: a("#jobenu-approval").value,
			run: a("#jobenu-run").checked,
			source: a("#jobenu-source").value,
			language: a("#jobenu-language").value,
			provider: a("#jobenu-provider").value,
			statuses: a("#jobenu-statuses").value.split(",").map((e) => e.trim().toUpperCase()).filter(Boolean),
			includeDemo: a("#jobenu-demo").checked,
			newRevision: a("#jobenu-revision").checked,
			rerun: a("#jobenu-rerun").checked
		};
	}
	async function k() {
		await i(), f = !1, a("#jobenu-preview").disabled = !0, C();
		let e = await t("/api/jobenu/capability", { source: a("#jobenu-source").value });
		f = e.available, a("#jobenu-capability").textContent = e.message || "Jobenu batch import is available.", a("#jobenu-install").open = !f, a("#jobenu-base").value || (a("#jobenu-base").value = e.base), E();
	}
	async function A() {
		l.hidden = !1, a("#board").hidden = !0, a("#workspace").hidden = !0, a("#jobenu-bases").replaceChildren(...n().filter((e) => e.local).map((e) => {
			let t = document.createElement("option");
			return t.value = e.name, t;
		}));
		try {
			await i(), await k(), await I();
		} catch (e) {
			S(e);
		}
		a("#jobenu-file").focus();
	}
	c.onclick = A, a("#jobenu-back").onclick = () => {
		l.hidden = !0, a("#board").hidden = !1;
	}, a("#jobenu-check").onclick = () => k().catch(S);
	async function j(e) {
		if (!e) return;
		let n = ++_;
		if (u = null, y.clear(), x.clear(), C(), D(), a("#jobenu-file-info").textContent = "Reading export…", S(""), e.size > 10485760) S("Choose a JSON export smaller than 10 MiB.");
		else try {
			await i();
			let r = await t("/api/jobenu/upload", {
				filename: e.name,
				content: await e.text()
			});
			if (n !== _) return;
			u = r, a("#jobenu-date-field").value = "createdAt", a("#jobenu-date-from").value = a("#jobenu-date-to").value = "", y = new Set(u.applications.filter((e) => e.status === "SAVED" && !e.isDemo).map((e) => e.id)), a("#jobenu-file-info").textContent = `${u.filename} · ${u.applications.length} applications`, D();
		} catch (e) {
			S(e);
		}
	}
	a("#jobenu-file").onchange = (e) => j(e.target.files[0]), a("#jobenu-drop").ondragover = (e) => e.preventDefault(), a("#jobenu-drop").ondrop = (e) => {
		e.preventDefault(), j(e.dataTransfer.files[0]);
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
	]) a("#jobenu-" + e).addEventListener("input", C);
	async function M() {
		if (p || b || !u || !f || !O().ids.length) return;
		p = !0, C();
		let e = g;
		S(""), a("#jobenu-preview").disabled = !0;
		try {
			let n = await t("/api/jobenu/preview", O());
			if (g !== e) return;
			d = n.plan, d.error && S(d.error);
			let r = a("#jobenu-plan tbody");
			r.replaceChildren();
			for (let e of d.entries) {
				let t = document.createElement("tr");
				t.append(...[
					"company",
					"position",
					"branch",
					"action"
				].map((t) => {
					let n = o("td", e[t]);
					return n.dataset.label = t === "branch" ? "Application" : t, n;
				})), r.append(t);
			}
			N(d.entries);
			let i = d.entries.filter((e) => e.action === "create").length;
			a("#jobenu-start").textContent = i ? `Create ${i} branches${a("#jobenu-run").checked ? " and run" : ""}` : `Continue ${d.entries.length} application${d.entries.length === 1 ? "" : "s"}`, a("#jobenu-start").disabled = d.entries.some((e) => !["create", "existing"].includes(e.action)) || n.status !== "planned" || !d.entries.length;
		} catch (e) {
			S(e);
		} finally {
			p = !1, E();
		}
	}
	function N(e) {
		let n = [...new Set(e.filter((e) => e.role_resolution === "slug_fallback").map((e) => e.position))], r = a("#jobenu-aliases");
		if (r.replaceChildren(), r.hidden = !n.length, !n.length) return;
		let i = o("h2", "Short role names"), s = o("p", "Optional: give these roles shorter names for your application branches. Save all names together.");
		i.id = "jobenu-alias-title", s.className = "helper";
		let c = document.createElement("form"), l = document.createElement("fieldset"), u = document.createElement("div");
		u.className = "jobenu-alias-fields";
		let f = n.map((e) => {
			let t = o("label", e), n = document.createElement("input");
			return n.value = x.get(e) || "", n.placeholder = "e.g. ml-engineer", n.pattern = "[a-z0-9][a-z0-9-]{0,63}", n.maxLength = 64, n.setAttribute("aria-describedby", "jobenu-alias-help"), n.oninput = () => {
				x.set(e, n.value), _.disabled = !f.some((e) => e.value.trim());
			}, t.append(n), u.append(t), n;
		}), m = o("p", "Lowercase letters, numbers and hyphens, up to 64 characters. Leave any role blank to keep its current name."), h = o("p", ""), _ = o("button", "Save aliases & update preview");
		m.id = "jobenu-alias-help", m.className = "helper", h.id = "jobenu-alias-error", h.className = "form-error", h.setAttribute("role", "alert"), _.type = "submit", _.disabled = !f.some((e) => e.value.trim()), l.append(u, m, h, _), c.append(l), c.onsubmit = async (e) => {
			if (e.preventDefault(), p || b) return;
			let r = n.map((e, t) => ({
				title: e,
				alias: f[t].value.trim()
			})).filter((e) => e.alias);
			if (r.length) {
				b = !0, l.disabled = !0, _.textContent = "Saving aliases…", h.textContent = "", g++, d = null, a("#jobenu-start").disabled = !0, E();
				try {
					await t("/api/jobenu/aliases", { aliases: r });
					for (let { title: e } of r) x.delete(e);
					a("#jobenu-feedback").textContent = `${r.length} role alias${r.length === 1 ? "" : "es"} saved. Updating preview…`, b = !1, await M(), a("#jobenu-preview").focus();
				} catch (e) {
					h.textContent = e.message, h.isConnected || S(e);
				} finally {
					b = !1, l.disabled = !1, _.textContent = "Save aliases & update preview", E();
				}
			}
		}, r.append(i, s, c);
	}
	a("#jobenu-preview").onclick = M, a("#jobenu-start").onclick = async () => {
		if (p || !d) return;
		p = !0, E();
		let e = d.plan_id;
		a("#jobenu-start").disabled = !0, S("");
		try {
			await t("/api/jobenu/start", {
				id: u.id,
				planId: e
			}), C(), await I();
		} catch (e) {
			S(e);
		} finally {
			p = !1, E();
		}
	};
	async function P(n, r) {
		m = {
			batch: n,
			entry: r,
			...await t("/api/jobenu/review", {
				id: n.id,
				key: r.key
			})
		};
		let i = a("#jobenu-review-content");
		i.replaceChildren(), a("#jobenu-review-error").textContent = "", a("#jobenu-reject").hidden = m.kind !== "facts";
		let s = m.kind === "facts" && [
			"approved",
			"applied",
			"rejected"
		].includes(m.report.status);
		if (a("#jobenu-approve").disabled = s, a("#jobenu-reject").disabled = s, a("#jobenu-approve").textContent = m.needsDraft ? "Generate requirement draft" : "Approve exact revision", m.kind === "facts") {
			let t = m.report;
			i.append(o("p", `Revision ${t.revision}`));
			for (let n of t.changes) {
				let t = document.createElement("article");
				t.className = "factual-change", t.append(o("h3", "Confirm the meaning of this change"), o("h4", "Original wording"), o("pre", n.original), o("h4", "Proposed wording"), o("pre", n.proposed));
				let r = t.querySelectorAll("pre");
				for (let [t, i] of [...r].entries()) i.className = t ? "wording-after" : "wording-before", e(i, t ? n.proposed : n.original, 0, (t ? n.proposed : n.original).length);
				let a = o("p", `Category: ${n.kind || n.reason} · ${n.verification || "Requires review"} · Source facts: ${(n.source_fact_ids || []).join(", ")}`);
				t.append(a);
				for (let e of n.source_fact_ids || []) {
					let n = m.report.source_facts?.find((t) => t.id === e)?.source_ref;
					if (!n) continue;
					let r = m.report.candidate_sources?.sources?.find((e) => e.id === n.source_id)?.path || "Captured source", i = document.createElement("details");
					i.append(o("summary", `${r} · lines ${n.line_start}–${n.line_end}`), o("pre", n.quote)), t.append(i);
				}
				i.append(t);
			}
			i.append(o("p", "Approve only after checking every factual interpretation against the captured sources."));
		} else if (m.needsDraft) i.append(o("p", "Canonical requirements need a separate draft and explicit approval. Generating a draft uses your configured AI provider."));
		else {
			i.append(o("p", "Review the immutable requirement definition, classifications and source references before approval."), o("p", `Revision ${m.report.revision.revision}`));
			let e = m.report.revision;
			for (let [t, n] of [["requirements", "Requirements"], ["employment_conditions", "Employment conditions"]]) {
				i.append(o("h3", n));
				for (let n of e[t] || []) {
					let e = document.createElement("article");
					e.className = "factual-change", e.append(o("h4", n.criterion || n.text || n.label || n.key), o("p", `${n.classification || n.kind || ""} · ${n.category || ""}`));
					let t = document.createElement("details");
					t.append(o("summary", "Source references and definition"), o("pre", JSON.stringify(n, null, 2))), e.append(t), i.append(e);
				}
			}
		}
		a("#jobenu-review").open || a("#jobenu-review").showModal();
	}
	a("#jobenu-review-close").onclick = () => a("#jobenu-review").close();
	async function F(e) {
		let n = a("#jobenu-approve");
		n.disabled = !0, a("#jobenu-reject").disabled = !0;
		try {
			let n = m.kind === "facts" ? m.report.revision : m.report?.revision?.revision;
			await t("/api/jobenu/decide", {
				id: m.batch.id,
				key: m.entry.key,
				action: m.needsDraft ? "draft" : e,
				revision: n
			}), m.needsDraft ? await P(m.batch, m.entry) : (a("#jobenu-review").close(), a("#jobenu-feedback").textContent = "Decision saved. Use Preview resume to review the remaining work before continuing.", await I());
		} catch (e) {
			a("#jobenu-review-error").textContent = e.message;
		} finally {
			n.disabled = !1, a("#jobenu-reject").disabled = !1;
		}
	}
	a("#jobenu-approve").onclick = () => F("approve"), a("#jobenu-reject").onclick = () => F("reject");
	async function I() {
		if (!h) {
			h = !0;
			try {
				let { batches: e } = await t("/api/jobenu"), n = JSON.stringify(e);
				if (n === v) return;
				v = n;
				let i = a("#jobenu-history");
				i.replaceChildren();
				for (let n of e) {
					let e = document.createElement("section");
					e.className = "jobenu-batch", e.append(o("h3", n.filename), o("p", n.status === "complete" ? "AI stages complete · PDF generation and submission are separate" : s(n.status))), n.error && e.append(o("p", n.error));
					let c = document.createElement("table"), d = document.createElement("thead"), f = document.createElement("tr");
					for (let e of [
						"Company",
						"Position",
						"Progress",
						"Actions"
					]) f.append(o("th", e));
					d.append(f), c.append(d);
					for (let i of n.entries) {
						let a = document.createElement("tr");
						a.append(o("td", i.company), o("td", i.position), o("td", [
							s(i.status || i.action),
							s(i.current_step),
							(i.completed_steps || []).map(s).join(" → ")
						].filter(Boolean).join(" · "))), i.error && a.lastElementChild.append(o("p", i.error));
						let u = document.createElement("td");
						if (i.workspace) {
							let e = o("button", "Open workspace");
							e.onclick = async () => {
								l.hidden = !0, await r(i.branch);
							}, u.append(e);
						}
						if (i.execution_log) {
							let r = o("button", "Application log");
							r.onclick = async () => {
								try {
									let r = await t("/api/jobenu/log", {
										id: n.id,
										key: i.key
									});
									e.append(o("pre", r.text));
								} catch (e) {
									S(e);
								}
							}, u.append(r);
						}
						if (i.pending || i.status === "awaiting_requirements_approval") {
							let e = o("button", i.pending ? "Review changes" : "Review requirements");
							e.onclick = () => P(n, i).catch(S), u.append(e);
						}
						a.append(u), c.append(a);
					}
					let p = document.createElement("div");
					p.className = "jobenu-scroll", p.tabIndex = 0, p.setAttribute("role", "region"), p.setAttribute("aria-label", `Applications from ${n.filename}`), p.append(c), e.append(p);
					let m = o("button", "View logs");
					if (m.onclick = async () => {
						try {
							let r = await t("/api/jobenu/log", { id: n.id }), i = o("pre", r.text);
							e.append(i);
						} catch (e) {
							S(e);
						}
					}, e.append(m), n.status !== "running") {
						let r = o("button", "Preview resume");
						r.onclick = async () => {
							C(), u = { id: n.id };
							let e = n.options || {};
							a("#jobenu-base").value = e.base || "", a("#jobenu-source").value = e.source || "", a("#jobenu-approval").value = e.approval || "human", a("#jobenu-run").checked = e.run !== !1;
							for (let t of ["language", "provider"]) a("#jobenu-" + t).value = e[t] || "";
							a("#jobenu-statuses").value = (e.statuses || ["SAVED"]).join(","), a("#jobenu-demo").checked = !!e.includeDemo, a("#jobenu-revision").checked = !!e.newRevision, a("#jobenu-rerun").checked = !1;
							let r = await t("/api/jobenu/selection", { id: n.id });
							u.applications = r.applications, y = new Set(e.ids || []), x.clear(), a("#jobenu-date-field").value = e.dateField || "createdAt", a("#jobenu-date-from").value = e.dateFrom || "", a("#jobenu-date-to").value = e.dateTo || "", a("#jobenu-file-info").textContent = `${n.filename} · ${r.applications.length} applications`, D(), await k(), await M();
						}, e.append(r);
						let i = o("button", "Forget batch");
						i.onclick = async () => {
							confirm("Forget this private export and batch history? Imported CV workspaces are kept.") && (await t("/api/jobenu/discard", { id: n.id }), await I());
						}, e.append(i);
					}
					i.append(e);
				}
			} catch (e) {
				S(e);
			} finally {
				h = !1;
			}
		}
	}
	return setInterval(() => {
		l.hidden || I();
	}, 1800), { open: A };
}
export { t };
