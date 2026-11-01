import { renderLatexSnippet as e } from "/vendor/editor.mjs";
// frontend/src/compat/jobenu.js
function t({ api: t, branches: n, openBranch: r }) {
	let i = (e) => document.querySelector(e), a = (e, t) => {
		let n = document.createElement(e);
		return n.textContent = t, n;
	}, o = (e) => ({
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
	})[e] || e || "", s = a("button", "Import jobs");
	s.id = "open-jobenu", s.className = "quiet", i(".board-nav").append(s);
	let c = document.createElement("section");
	c.id = "jobenu-import", c.hidden = !0, c.innerHTML = "<button id=\"jobenu-back\" class=\"back\">← All applications</button><div class=\"page-heading\"><div><h1>Import jobs</h1><p class=\"subtitle\">Bring opportunities from Jobenu into this CV collection.</p></div></div>\n <div role=\"tablist\" aria-label=\"Import source\" class=\"jobenu-tabs\"><button role=\"tab\" aria-selected=\"true\">Jobenu</button></div>\n <p class=\"helper\">Your export stays unchanged. Each selected application gets its own CV workspace. Importing never submits an application or pushes to Git.</p>\n <p id=\"jobenu-error\" role=\"alert\" class=\"form-error\"></p><p id=\"jobenu-feedback\" role=\"status\"></p>\n <details id=\"jobenu-install\"><summary>Vita installation</summary><label>Compatible Vita CV source folder<input id=\"jobenu-source\" placeholder=\"Folder containing vita/__main__.py\"></label><button id=\"jobenu-check\">Check installation</button><p id=\"jobenu-capability\" role=\"status\"></p></details>\n <label id=\"jobenu-drop\" class=\"jobenu-drop\">Choose or drop a Jobenu JSON export<input id=\"jobenu-file\" type=\"file\" accept=\".json,application/json\"></label><p id=\"jobenu-file-info\" role=\"status\"></p>\n <div class=\"jobenu-scroll\"><table id=\"jobenu-selection\"><caption>Select applications</caption><thead><tr><th>Select</th><th>Company</th><th>Position</th><th>Status</th></tr></thead><tbody></tbody></table></div>\n <div class=\"jobenu-settings\"><label>Starting CV<input id=\"jobenu-base\" type=\"search\" list=\"jobenu-bases\" autocomplete=\"off\" placeholder=\"Search local branches\"><datalist id=\"jobenu-bases\"></datalist></label><label>Approval mode<select id=\"jobenu-approval\"><option value=\"human\">Review changes before applying</option><option value=\"auto\">Apply verified changes automatically</option></select></label></div>\n <label><input id=\"jobenu-run\" type=\"checkbox\" checked> Run the AI workflow</label><p class=\"helper\">Automatic mode can still pause for factual or canonical-requirement confirmation. Complete means the configured AI stages finished; PDFs and submission are separate.</p>\n <details><summary>Advanced</summary><div class=\"jobenu-settings\"><label>Language override<input id=\"jobenu-language\" placeholder=\"Use saved language\"></label><label>Provider override<input id=\"jobenu-provider\" placeholder=\"Use saved AI settings\"></label><label>Status filters<input id=\"jobenu-statuses\" value=\"SAVED\" aria-describedby=\"jobenu-status-help\"></label></div><p id=\"jobenu-status-help\" class=\"helper\">Comma-separated statuses, or ALL. Uses saved stage providers/models and native Vita reasoning preferences. Tree-only reasoning overrides are not forwarded by this batch CLI.</p><label><input id=\"jobenu-demo\" type=\"checkbox\"> Include demo applications</label><label><input id=\"jobenu-revision\" type=\"checkbox\"> Create a new source revision when records changed</label><label><input id=\"jobenu-rerun\" type=\"checkbox\"> Reassess completed stages (additional AI calls)</label></details>\n <div class=\"actions\"><button id=\"jobenu-preview\" disabled>Preview branches</button><button id=\"jobenu-start\" class=\"primary\" disabled>Create branches</button></div>\n <div class=\"jobenu-scroll\"><table id=\"jobenu-plan\"><caption>Branch preview</caption><thead><tr><th>Company</th><th>Position</th><th>Branch</th><th>Action</th></tr></thead><tbody></tbody></table></div><div id=\"jobenu-aliases\"></div>\n <h2>Batch activity</h2><p class=\"helper\">You can leave this view while work continues. Retained sources stay private until you forget the batch; imported workspaces are preserved.</p><div id=\"jobenu-history\"></div>\n <dialog id=\"jobenu-review\" aria-labelledby=\"jobenu-review-title\"><div class=\"dialog-heading\"><h2 id=\"jobenu-review-title\">Review imported application</h2><button id=\"jobenu-review-close\" aria-label=\"Close import review\">×</button></div><div id=\"jobenu-review-content\" class=\"review-scroll\"></div><p id=\"jobenu-review-error\" role=\"alert\" class=\"form-error\"></p><footer class=\"dialog-footer\"><button id=\"jobenu-reject\">Reject changes</button><button id=\"jobenu-approve\" class=\"primary\">Approve exact revision</button></footer></dialog>", i("#main-content").append(c);
	let l = null, u = null, d = !1, f = !1, p = null, m = !1, h = 0, g = 0, _ = "", v = (e) => i("#jobenu-error").textContent = e?.message || e || "";
	function y() {
		h++, u = null, i("#jobenu-start").disabled = !0, i("#jobenu-plan tbody").replaceChildren(), i("#jobenu-aliases").replaceChildren();
	}
	function b() {
		return {
			id: l.id,
			ids: [...i("#jobenu-selection").querySelectorAll("input:checked")].map((e) => e.value),
			base: i("#jobenu-base").value,
			approval: i("#jobenu-approval").value,
			run: i("#jobenu-run").checked,
			source: i("#jobenu-source").value,
			language: i("#jobenu-language").value,
			provider: i("#jobenu-provider").value,
			statuses: i("#jobenu-statuses").value.split(",").map((e) => e.trim().toUpperCase()).filter(Boolean),
			includeDemo: i("#jobenu-demo").checked,
			newRevision: i("#jobenu-revision").checked,
			rerun: i("#jobenu-rerun").checked
		};
	}
	async function x() {
		d = !1, i("#jobenu-preview").disabled = !0, y();
		let e = await t("/api/jobenu/capability", { source: i("#jobenu-source").value });
		d = e.available, i("#jobenu-capability").textContent = e.message || "Jobenu batch import is available.", i("#jobenu-install").open = !d, i("#jobenu-base").value || (i("#jobenu-base").value = e.base), i("#jobenu-preview").disabled = !d;
	}
	async function S() {
		c.hidden = !1, i("#board").hidden = !0, i("#workspace").hidden = !0, i("#jobenu-bases").replaceChildren(...n().filter((e) => e.local).map((e) => {
			let t = document.createElement("option");
			return t.value = e.name, t;
		}));
		try {
			await x(), await D();
		} catch (e) {
			v(e);
		}
		i("#jobenu-file").focus();
	}
	s.onclick = S, i("#jobenu-back").onclick = () => {
		c.hidden = !0, i("#board").hidden = !1;
	}, i("#jobenu-check").onclick = () => x().catch(v);
	async function C(e) {
		if (!e) return;
		let n = ++g;
		if (l = null, y(), i("#jobenu-selection tbody").replaceChildren(), i("#jobenu-file-info").textContent = "Reading export…", v(""), e.size > 10485760) v("Choose a JSON export smaller than 10 MiB.");
		else try {
			let r = await t("/api/jobenu/upload", {
				filename: e.name,
				content: await e.text()
			});
			if (n !== g) return;
			l = r, i("#jobenu-file-info").textContent = `${l.filename} · ${l.applications.length} applications`;
			let o = i("#jobenu-selection tbody");
			o.replaceChildren();
			for (let e of l.applications) {
				let t = document.createElement("tr"), n = document.createElement("td"), r = document.createElement("input");
				r.type = "checkbox", r.value = e.id, r.checked = e.status === "SAVED" && !e.isDemo, r.setAttribute("aria-label", `Select ${e.company} · ${e.position}`), r.onchange = y, n.append(r), t.append(n, ...[
					"company",
					"position",
					"status"
				].map((t) => a("td", e[t]))), o.append(t);
			}
		} catch (e) {
			v(e);
		}
	}
	i("#jobenu-file").onchange = (e) => C(e.target.files[0]), i("#jobenu-drop").ondragover = (e) => e.preventDefault(), i("#jobenu-drop").ondrop = (e) => {
		e.preventDefault(), C(e.dataTransfer.files[0]);
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
	]) i("#jobenu-" + e).addEventListener("input", y);
	async function w() {
		if (f || !l || !d) return;
		f = !0, y();
		let e = h;
		v(""), i("#jobenu-preview").disabled = !0;
		try {
			let n = await t("/api/jobenu/preview", b());
			if (h !== e) return;
			u = n.plan, u.error && v(u.error);
			let r = i("#jobenu-plan tbody");
			r.replaceChildren();
			for (let e of u.entries) {
				let n = document.createElement("tr");
				if (n.append(...[
					"company",
					"position",
					"branch",
					"action"
				].map((t) => a("td", e[t]))), r.append(n), e.role_resolution === "slug_fallback") {
					let n = a("label", `Short role for ${e.position}`), r = document.createElement("input"), o = a("button", "Save role alias");
					n.append(r), o.onclick = async () => {
						try {
							await t("/api/jobenu/alias", {
								title: e.position,
								alias: r.value
							}), y(), await w();
						} catch (e) {
							v(e);
						}
					}, i("#jobenu-aliases").append(n, o);
				}
			}
			let o = u.entries.filter((e) => e.action === "create").length;
			i("#jobenu-start").textContent = o ? `Create ${o} branches${i("#jobenu-run").checked ? " and run" : ""}` : `Continue ${u.entries.length} application${u.entries.length === 1 ? "" : "s"}`, i("#jobenu-start").disabled = u.entries.some((e) => !["create", "existing"].includes(e.action)) || n.status !== "planned" || !u.entries.length;
		} catch (e) {
			v(e);
		} finally {
			f = !1, i("#jobenu-preview").disabled = !d;
		}
	}
	i("#jobenu-preview").onclick = w, i("#jobenu-start").onclick = async () => {
		if (f || !u) return;
		f = !0;
		let e = u.plan_id;
		i("#jobenu-start").disabled = !0, v("");
		try {
			await t("/api/jobenu/start", {
				id: l.id,
				planId: e
			}), y(), await D();
		} catch (e) {
			v(e);
		} finally {
			f = !1;
		}
	};
	async function T(n, r) {
		p = {
			batch: n,
			entry: r,
			...await t("/api/jobenu/review", {
				id: n.id,
				key: r.key
			})
		};
		let o = i("#jobenu-review-content");
		o.replaceChildren(), i("#jobenu-review-error").textContent = "", i("#jobenu-reject").hidden = p.kind !== "facts";
		let s = p.kind === "facts" && [
			"approved",
			"applied",
			"rejected"
		].includes(p.report.status);
		if (i("#jobenu-approve").disabled = s, i("#jobenu-reject").disabled = s, i("#jobenu-approve").textContent = p.needsDraft ? "Generate requirement draft" : "Approve exact revision", p.kind === "facts") {
			let t = p.report;
			o.append(a("p", `Revision ${t.revision}`));
			for (let n of t.changes) {
				let t = document.createElement("article");
				t.className = "factual-change", t.append(a("h3", "Confirm the meaning of this change"), a("h4", "Original wording"), a("pre", n.original), a("h4", "Proposed wording"), a("pre", n.proposed));
				let r = t.querySelectorAll("pre");
				for (let [t, i] of [...r].entries()) i.className = t ? "wording-after" : "wording-before", e(i, t ? n.proposed : n.original, 0, (t ? n.proposed : n.original).length);
				let i = a("p", `Category: ${n.kind || n.reason} · ${n.verification || "Requires review"} · Source facts: ${(n.source_fact_ids || []).join(", ")}`);
				t.append(i);
				for (let e of n.source_fact_ids || []) {
					let n = p.report.source_facts?.find((t) => t.id === e)?.source_ref;
					if (!n) continue;
					let r = p.report.candidate_sources?.sources?.find((e) => e.id === n.source_id)?.path || "Captured source", i = document.createElement("details");
					i.append(a("summary", `${r} · lines ${n.line_start}–${n.line_end}`), a("pre", n.quote)), t.append(i);
				}
				o.append(t);
			}
			o.append(a("p", "Approve only after checking every factual interpretation against the captured sources."));
		} else if (p.needsDraft) o.append(a("p", "Canonical requirements need a separate draft and explicit approval. Generating a draft uses your configured AI provider."));
		else {
			o.append(a("p", "Review the immutable requirement definition, classifications and source references before approval."), a("p", `Revision ${p.report.revision.revision}`));
			let e = p.report.revision;
			for (let [t, n] of [["requirements", "Requirements"], ["employment_conditions", "Employment conditions"]]) {
				o.append(a("h3", n));
				for (let n of e[t] || []) {
					let e = document.createElement("article");
					e.className = "factual-change", e.append(a("h4", n.criterion || n.text || n.label || n.key), a("p", `${n.classification || n.kind || ""} · ${n.category || ""}`));
					let t = document.createElement("details");
					t.append(a("summary", "Source references and definition"), a("pre", JSON.stringify(n, null, 2))), e.append(t), o.append(e);
				}
			}
		}
		i("#jobenu-review").open || i("#jobenu-review").showModal();
	}
	i("#jobenu-review-close").onclick = () => i("#jobenu-review").close();
	async function E(e) {
		let n = i("#jobenu-approve");
		n.disabled = !0, i("#jobenu-reject").disabled = !0;
		try {
			let n = p.kind === "facts" ? p.report.revision : p.report?.revision?.revision;
			await t("/api/jobenu/decide", {
				id: p.batch.id,
				key: p.entry.key,
				action: p.needsDraft ? "draft" : e,
				revision: n
			}), p.needsDraft ? await T(p.batch, p.entry) : (i("#jobenu-review").close(), i("#jobenu-feedback").textContent = "Decision saved. Use Preview resume to review the remaining work before continuing.", await D());
		} catch (e) {
			i("#jobenu-review-error").textContent = e.message;
		} finally {
			n.disabled = !1, i("#jobenu-reject").disabled = !1;
		}
	}
	i("#jobenu-approve").onclick = () => E("approve"), i("#jobenu-reject").onclick = () => E("reject");
	async function D() {
		if (!m) {
			m = !0;
			try {
				let { batches: e } = await t("/api/jobenu"), n = JSON.stringify(e);
				if (n === _) return;
				_ = n;
				let s = i("#jobenu-history");
				s.replaceChildren();
				for (let n of e) {
					let e = document.createElement("section");
					e.className = "jobenu-batch", e.append(a("h3", n.filename), a("p", n.status === "complete" ? "AI stages complete · PDF generation and submission are separate" : o(n.status))), n.error && e.append(a("p", n.error));
					let u = document.createElement("table"), d = document.createElement("thead"), f = document.createElement("tr");
					for (let e of [
						"Company",
						"Position",
						"Progress",
						"Actions"
					]) f.append(a("th", e));
					d.append(f), u.append(d);
					for (let i of n.entries) {
						let s = document.createElement("tr");
						s.append(a("td", i.company), a("td", i.position), a("td", [
							o(i.status || i.action),
							o(i.current_step),
							(i.completed_steps || []).map(o).join(" → ")
						].filter(Boolean).join(" · "))), i.error && s.lastElementChild.append(a("p", i.error));
						let l = document.createElement("td");
						if (i.workspace) {
							let e = a("button", "Open workspace");
							e.onclick = async () => {
								c.hidden = !0, await r(i.branch);
							}, l.append(e);
						}
						if (i.execution_log) {
							let r = a("button", "Application log");
							r.onclick = async () => {
								try {
									let r = await t("/api/jobenu/log", {
										id: n.id,
										key: i.key
									});
									e.append(a("pre", r.text));
								} catch (e) {
									v(e);
								}
							}, l.append(r);
						}
						if (i.pending || i.status === "awaiting_requirements_approval") {
							let e = a("button", i.pending ? "Review changes" : "Review requirements");
							e.onclick = () => T(n, i).catch(v), l.append(e);
						}
						s.append(l), u.append(s);
					}
					let p = document.createElement("div");
					p.className = "jobenu-scroll", p.append(u), e.append(p);
					let m = a("button", "View logs");
					if (m.onclick = async () => {
						try {
							let r = await t("/api/jobenu/log", { id: n.id }), i = a("pre", r.text);
							e.append(i);
						} catch (e) {
							v(e);
						}
					}, e.append(m), n.status !== "running") {
						let r = a("button", "Preview resume");
						r.onclick = async () => {
							y(), l = { id: n.id };
							let e = n.options || {};
							i("#jobenu-base").value = e.base || "", i("#jobenu-source").value = e.source || "", i("#jobenu-approval").value = e.approval || "human", i("#jobenu-run").checked = e.run !== !1;
							for (let t of ["language", "provider"]) i("#jobenu-" + t).value = e[t] || "";
							i("#jobenu-statuses").value = (e.statuses || ["SAVED"]).join(","), i("#jobenu-demo").checked = !!e.includeDemo, i("#jobenu-revision").checked = !!e.newRevision, i("#jobenu-rerun").checked = !1;
							let r = await t("/api/jobenu/selection", { id: n.id });
							l.applications = r.applications, i("#jobenu-file-info").textContent = `${n.filename} · ${r.applications.length} applications`, i("#jobenu-selection tbody").replaceChildren();
							for (let t of r.applications) {
								let n = document.createElement("tr"), r = document.createElement("td"), o = document.createElement("input");
								o.type = "checkbox", o.value = t.id, o.checked = e.ids?.includes(t.id), o.setAttribute("aria-label", `Select ${t.company} · ${t.position}`), o.onchange = y, r.append(o), n.append(r, a("td", t.company), a("td", t.position), a("td", t.status)), i("#jobenu-selection tbody").append(n);
							}
							await x(), await w();
						}, e.append(r);
						let o = a("button", "Forget batch");
						o.onclick = async () => {
							confirm("Forget this private export and batch history? Imported CV workspaces are kept.") && (await t("/api/jobenu/discard", { id: n.id }), await D());
						}, e.append(o);
					}
					s.append(e);
				}
			} catch (e) {
				v(e);
			} finally {
				m = !1;
			}
		}
	}
	return setInterval(() => {
		c.hidden || D();
	}, 1800), { open: S };
}
export { t };
