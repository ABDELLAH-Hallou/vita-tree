// frontend/src/compat/ai-settings.js
var e = [
	["extract", "Identify job requirements"],
	["analyze", "Check CV match"],
	["adapt", "Tailor CV"],
	["review", "Review CV with AI"],
	["cover", "Cover letter"]
], t = {
	none: "None",
	minimal: "Minimal",
	low: "Low · faster",
	medium: "Medium · balanced",
	high: "High · more thinking",
	xhigh: "Extra high",
	max: "Maximum",
	ultra: "Ultra"
}, n = (e) => structuredClone(e);
function r(r, { api: i, onChange: a }) {
	let o = /* @__PURE__ */ new Map(), s, c, l = [], u, d = !0, f = !1, p = !1, m = null, h = null, g = null, _ = !1, v = document.createElement("div");
	v.className = "ai-dialogs", document.body.append(v);
	let y = (e) => r.querySelector(e) || v.querySelector(e);
	r.innerHTML = "\n    <section class=\"ai-shared\" aria-labelledby=\"shared-ai-title\">\n      <div class=\"ai-setup-heading\"><div><h3 id=\"shared-ai-title\">Shared AI setup</h3><p class=\"helper\">Set up once. Every step uses this unless you customize it below.</p></div><span class=\"pill accent\">Default for all steps</span></div>\n      <div id=\"shared-ai-fields\"></div>\n    </section>\n    <details id=\"ai-advanced\" class=\"ai-advanced\"><summary><span>Advanced · customize individual steps</span><span id=\"override-count\" class=\"pill\">All use shared setup</span></summary>\n      <p class=\"helper\">Use a faster model for job requirements and a different model for writing, for example. Custom steps keep their own setup when the shared setup changes.</p>\n      <div id=\"ai-step-settings\"></div><button id=\"reset-ai-steps\" class=\"quiet\" type=\"button\">Use shared setup for every step</button>\n    </details>\n    <div class=\"ai-save-bar\"><button id=\"save-ai-setup\" type=\"button\">Save AI setup</button><span id=\"ai-setup-status\" class=\"helper\" role=\"status\">Choices are saved locally. API keys last for this server session.</span></div>\n    <p id=\"ai-setup-error\" class=\"ai-setup-error\" role=\"alert\" hidden></p>\n    <dialog id=\"step-ai-dialog\" class=\"ai-settings-dialog\" aria-labelledby=\"step-ai-title\" aria-describedby=\"step-ai-description\"><form id=\"step-ai-form\">\n      <div class=\"ai-dialog-body\">\n      <div class=\"dialog-heading\"><div><span id=\"step-ai-context\" class=\"pill accent\"></span><h2 id=\"step-ai-title\"></h2><button id=\"step-requirements\" type=\"button\" hidden>View job requirements</button><button id=\"inspect-step-dialog\" type=\"button\" hidden>Inspect this step’s execution</button></div><button id=\"close-step-ai\" class=\"quiet\" type=\"button\" aria-label=\"Close step settings\">×</button></div>\n      <p id=\"step-ai-description\" class=\"helper\"></p>\n      <fieldset id=\"step-ai-mode\" class=\"step-ai-mode\"><legend>AI setup for this step</legend>\n        <label><input type=\"radio\" name=\"step-ai-mode\" id=\"step-ai-shared\" value=\"shared\"><span><strong>Use shared setup</strong><small>Follow the shared provider, model, reasoning, and connection.</small></span></label>\n        <label><input type=\"radio\" name=\"step-ai-mode\" id=\"step-ai-custom\" value=\"custom\"><span><strong>Customize this step</strong><small>Choose a separate setup for this component.</small></span></label>\n      </fieldset>\n      <div id=\"step-ai-fields\"></div>\n      <p id=\"step-ai-save-hint\" class=\"helper\">Apply saves your current AI setup on this computer. Only this step’s override is changed. API keys last for this server session.</p>\n      </div>\n      <div class=\"ai-dialog-footer\">\n      <p id=\"step-ai-error\" role=\"alert\" class=\"ai-setup-error\" hidden></p>\n      <div class=\"dialog-footer\"><button id=\"step-ai-cancel\" type=\"button\">Cancel</button><button id=\"step-ai-next\" type=\"button\" hidden>Configure next run</button><button id=\"step-ai-apply\" class=\"primary\" type=\"submit\">Apply to step</button></div>\n      </div>\n    </form></dialog>\n    <dialog id=\"generation-check-dialog\" class=\"ai-settings-dialog\" aria-labelledby=\"generation-check-title\"><form id=\"generation-check-form\">\n      <div class=\"ai-dialog-body\">\n      <div class=\"dialog-heading\"><h2 id=\"generation-check-title\">Check model generation</h2><button id=\"close-generation-check\" class=\"quiet\" type=\"button\" aria-label=\"Close generation check\">×</button></div>\n      <p id=\"generation-check-route\" class=\"helper\"></p>\n      <p>This sends a small synthetic prompt to the selected provider and model and <strong>may consume paid usage</strong>, including provider retries. It sends no CV or job description. A successful model listing does not prove generation access.</p>\n      <p class=\"helper\">This checks the setup shown here without applying or saving edits. Success confirms generation access at this time, not CV quality.</p>\n      <p id=\"generation-check-result\" class=\"provider-failure\" role=\"status\" aria-live=\"polite\"></p>\n      </div>\n      <div class=\"ai-dialog-footer\">\n      <div class=\"dialog-footer\"><button id=\"cancel-generation-check\" type=\"button\">Cancel</button><button id=\"confirm-generation-check\" class=\"primary\" type=\"submit\">Run generation check · may use credits</button></div>\n      </div>\n    </form></dialog>\n    <dialog id=\"connection-dialog\" class=\"ai-settings-dialog\" aria-labelledby=\"connection-title\"><form id=\"connection-form\">\n      <div class=\"ai-dialog-body\">\n      <div class=\"dialog-heading\"><h2 id=\"connection-title\">Add API connection</h2><button id=\"close-connection\" class=\"quiet\" type=\"button\" aria-label=\"Close API connection\">×</button></div>\n      <p id=\"connection-service\" class=\"helper\"></p>\n      <label>Connection name<input id=\"connection-name\" maxlength=\"80\" placeholder=\"e.g. Personal account\" autocomplete=\"off\" required></label>\n      <label>API key<input id=\"connection-key\" type=\"password\" maxlength=\"4096\" autocomplete=\"off\" spellcheck=\"false\" required></label>\n      <label class=\"show-key\"><input id=\"show-connection-key\" type=\"checkbox\">Show API key</label>\n      <p class=\"helper\">Get an API key from this provider’s account dashboard. The key stays in this local server’s memory and is never saved in Git, browser storage, or run history. Add it again after restarting the server.</p>\n      </div>\n      <div class=\"ai-dialog-footer\">\n      <p id=\"connection-error\" role=\"alert\" class=\"ai-setup-error\" hidden></p>\n      <div class=\"dialog-footer\"><button id=\"cancel-connection\" type=\"button\">Cancel</button><button id=\"add-connection\" class=\"primary\" type=\"submit\">Add connection</button></div>\n      </div>\n    </form></dialog>", v.append(y("#step-ai-dialog"), y("#connection-dialog"), y("#generation-check-dialog")), v.addEventListener("focusin", (e) => {
		let t = e.target;
		t.closest(".ai-dialog-body") && requestAnimationFrame(() => {
			document.activeElement === t && t.scrollIntoView({
				block: "nearest",
				inline: "nearest"
			});
		});
	});
	let b = (e) => e === "default" ? u.default : u.steps[e] || u.default, x = (e) => c?.providers.find((t) => t.id === e.provider);
	function S(e) {
		return e ? `${x(e)?.name || e.provider} · ${e.model || "Provider default"} · ${e.reasoning ? t[e.reasoning] || e.reasoning : "Automatic reasoning"}${e.backup ? ` · Backup: ${x(e.backup)?.name || e.backup.provider} / ${e.backup.model}` : ""}` : "";
	}
	function C(e) {
		return e.connectionName ? e.connectionName : e.connection ? l.find((t) => t.id === e.connection && t.provider === e.provider)?.name || "Connection expired · add it again" : e.provider === "codex" ? "Local Codex login" : "Existing local credentials";
	}
	function w() {
		p = !0, o.set(s, {
			settings: n(u),
			dirty: p
		}), y("#ai-setup-status").textContent = "Unsaved setup · used immediately for new runs. Save to keep it after reload.", y("#ai-setup-error").hidden = !0, T(), a();
	}
	function T() {
		if (!u) return;
		let t = Object.keys(u.steps).length;
		y("#override-count").textContent = t ? `${t} custom ${t === 1 ? "step" : "steps"}` : "All use shared setup", y("#reset-ai-steps").disabled = d || !t;
		for (let [t] of e) {
			let e = y(`[data-ai-summary="${t}"]`);
			e && (e.textContent = `${u.steps[t] ? "Custom" : "Shared"} · ${S(b(t))}`);
			let n = document.querySelector(`#step-${t}`)?.closest("label")?.querySelector(".step-ai-summary");
			n && (n.textContent = `${u.steps[t] ? "Custom" : "Shared"} · ${b(t).model || x(b(t))?.name || b(t).provider}`);
		}
	}
	function E(e, r = null, a = !1) {
		let o = r ? r.route : b(e), f = a ? o.backup : o, p = e === "default", h = (r ? "popup-" : p ? "" : e + "-") + (a ? "backup-" : ""), _ = d || !!r?.readOnly || !!r?.saving || !!r && !r.custom, v = () => r ? M() : w(), T = () => r ? N() : D(e), j = document.createElement("div");
		j.className = "ai-route-fields", j.innerHTML = `<div class="ai-controls">
      <label>Provider<select id="${h}provider" aria-label="${p ? "Shared" : e} provider"></select></label>
      <label>Model ID<input id="${h}model" list="${h}model-suggestions" maxlength="160" autocomplete="off" spellcheck="false" placeholder="Choose a suggestion or type any model ID" aria-describedby="${h}model-help"><datalist id="${h}model-suggestions"></datalist></label>
      <label>Reasoning<select id="${h}reasoning" aria-describedby="${h}reasoning-help"></select></label>
      <label>Connection<select id="${h}connection"></select></label>
    </div>
    <p id="${h}model-help" class="helper">Choose a suggested model or enter the exact model ID from your provider. Leave empty for its default. Your account must have access.</p>
    <p id="${h}reasoning-help" class="helper"></p>
    <div class="connection-actions"><span class="helper" id="${h}connection-help"></span><button type="button" data-check-generation>Check generation…</button><button type="button" data-add-key>Add API key…</button><button type="button" data-remove-key class="quiet">Remove connection</button></div>`;
		let P = (e) => j.querySelector("#" + h + e);
		P("provider").replaceChildren(...c.providers.map((e) => new Option(e.name, e.id))), P("provider").value = f.provider, P("model").value = f.model;
		let F = c.options.filter((e) => e.provider === f.provider && e.supported && e.model);
		for (let e of [u.default, ...Object.values(u.steps)]) e.provider === f.provider && e.model && !F.some((t) => t.model === e.model) && F.push({
			...e,
			reasoning: []
		});
		P("model-suggestions").replaceChildren(...[...new Set(F.map((e) => e.model))].map((e) => new Option(e, e)));
		let I = x(f);
		function L() {
			let e = c.options.find((e) => e.provider === f.provider && e.model === f.model), n = [...e?.reasoning?.length ? e.reasoning : I?.reasoning || []];
			r?.readOnly && f.reasoning && !n.includes(f.reasoning) && n.push(f.reasoning), n.includes(f.reasoning) || (f.reasoning = ""), P("reasoning").replaceChildren(new Option("Automatic", ""), ...n.map((e) => new Option(t[e] || e, e))), P("reasoning").value = f.reasoning, P("reasoning").disabled = _ || !n.length;
		}
		L(), P("reasoning-help").textContent = f.provider === "codex" ? c.reasoningBridge ? "For custom model IDs, check which reasoning levels that model accepts. Higher levels may take longer." : "Custom reasoning needs the Vita CV source connection. Automatic is available." : "Vita CV currently uses automatic reasoning for this provider.", P("connection").replaceChildren(new Option(f.provider === "codex" ? "Local Codex login" : "Existing local credentials", ""), ...l.filter((e) => e.provider === f.provider).map((e) => new Option(e.name, e.id))), f.connection && !l.some((e) => e.id === f.connection && e.provider === f.provider) && P("connection").add(new Option(r?.readOnly && f.connectionName ? f.connectionName : "Connection expired · add it again", f.connection)), P("connection").value = f.connection || "", P("connection-help").textContent = f.connection ? `${C(f)} · session only; key access is checked when a step runs.` : f.provider === "codex" ? "Uses the Codex CLI account already signed in on this computer." : `Uses ${I?.keyVariable || "the provider API key"} from your local environment or .vita/.env. Or add a key here.`, j.querySelector("[data-add-key]").hidden = f.provider === "codex" || !!r?.readOnly, j.querySelector("[data-remove-key]").hidden = !!r || !f.connection || !l.some((e) => e.id === f.connection);
		for (let e of j.querySelectorAll("input,select,button")) _ && (e.disabled = !0);
		if (j.querySelector("[data-check-generation]").disabled = d || !!r?.readOnly || !!r?.saving, P("provider").onchange = () => {
			let e = P("provider").value, t = c.options.find((t) => t.provider === e && t.supported);
			Object.assign(f, {
				provider: e,
				model: t?.model || "",
				reasoning: "",
				connection: ""
			}), T(), v();
		}, P("model").oninput = () => {
			f.model = P("model").value, v();
		}, P("model").onchange = () => {
			f.model = f.model.trim(), P("model").value = f.model, L(), v();
		}, P("reasoning").onchange = () => {
			f.reasoning = P("reasoning").value, v();
		}, P("connection").onchange = () => {
			f.connection = P("connection").value, T(), v();
		}, j.querySelector("[data-check-generation]").onclick = () => {
			let t = A(f, "Generation check");
			if (t) {
				r ? (y("#step-ai-error").textContent = t, y("#step-ai-error").hidden = !1) : O(t);
				return;
			}
			let i = n(u);
			r && !r.custom && delete i.steps[e], e === "default" ? i.steps = {} : (!r || r.custom) && (i.steps[e] = n(f)), g = {
				branch: s,
				step: e === "default" ? "analyze" : e,
				settings: i
			}, y("#generation-check-route").textContent = `${r && !r.custom || e === "default" || !u.steps[e] && !r ? "Shared setup" : "Step setup"} · ${S(f)} · ${C(f)}`, y("#generation-check-result").textContent = "No request has been sent.", y("#cancel-generation-check").textContent = "Cancel", y("#confirm-generation-check").disabled = !1, y("#cancel-generation-check").disabled = !1, y("#generation-check-dialog").showModal();
		}, j.querySelector("[data-add-key]").onclick = () => {
			m = {
				route: f,
				step: e,
				branch: s,
				editor: r,
				repaint: T,
				notify: v,
				backup: a
			}, y("#connection-service").textContent = `${I?.name} · reusable by any step with this provider`, y("#connection-name").value = `${I?.name} account`, y("#connection-key").value = "", y("#connection-key").type = "password", y("#show-connection-key").checked = !1, y("#connection-error").hidden = !0, y("#connection-dialog").showModal();
		}, j.querySelector("[data-remove-key]").onclick = async () => {
			try {
				l = (await i("/api/connections/remove", { id: f.connection })).connections, k(), w();
			} catch (e) {
				O(e.message);
			}
		}, a) j.querySelector("[data-check-generation]").hidden = !0, P("model-help").textContent = "Enter the exact backup model ID. It must differ from the primary setup.";
		else {
			let t = document.createElement("fieldset");
			t.className = "ai-backup", t.innerHTML = "<legend>Backup AI</legend><label class=\"ai-override-toggle\"><input type=\"checkbox\"><span>Use a backup if this AI fails</span></label><p class=\"helper\"></p><div data-backup-fields></div>";
			let n = t.querySelector("input");
			n.checked = !!f.backup, n.disabled = _ || !c.fallback, t.querySelector("p").textContent = c.fallback ? "Uses the same attempt budget and may use credits from the backup service. Reviews and file conflicts still stop the workflow." : "Update Vita CV and restart Vita Tree to use a backup.";
			let i = t.querySelector("[data-backup-fields]");
			if (f.backup && i.append(E(e, r, !0)), n.onchange = () => {
				n.checked ? f.backup = {
					provider: f.provider,
					model: "",
					reasoning: "",
					connection: f.connection,
					categories: [...c.fallback.default_categories]
				} : f.backup = null, T(), v();
			}, f.backup) {
				let e = document.createElement("details"), n = document.createElement("summary");
				n.textContent = "When to use the backup", e.append(n);
				for (let t of c.fallback?.allowed_categories || f.backup.categories) {
					let n = document.createElement("label");
					n.className = "ai-override-toggle";
					let r = document.createElement("input");
					r.type = "checkbox", r.checked = f.backup.categories.includes(t), r.disabled = _, r.onchange = () => {
						f.backup.categories = r.checked ? [...f.backup.categories, t] : f.backup.categories.filter((e) => e !== t), v();
					}, n.append(r, document.createTextNode(t.replaceAll("_", " "))), e.append(n);
				}
				t.append(e);
			}
			j.append(t);
		}
		return j;
	}
	function D(e) {
		y(e === "default" ? "#shared-ai-fields" : `[data-ai-fields="${e}"]`).replaceChildren(E(e));
	}
	function O(e) {
		y("#ai-setup-error").textContent = e, y("#ai-setup-error").hidden = !1;
	}
	function k() {
		if (!u) return;
		let t = new Set([...r.querySelectorAll(".ai-step-setting[open]")].map((e) => e.querySelector("[data-ai-summary]").dataset.aiSummary));
		D("default"), y("#ai-step-settings").replaceChildren();
		for (let [r, i] of e) {
			let e = document.createElement("details");
			e.className = "ai-step-setting", e.open = t.has(r), e.innerHTML = `<summary><strong></strong><span data-ai-summary="${r}" class="helper"></span></summary><label class="ai-override-toggle"><input type="checkbox" id="${r}-custom-ai">Use custom AI setup for this step</label><div data-ai-fields="${r}"></div>`, e.querySelector("strong").textContent = i;
			let a = e.querySelector("input");
			a.checked = !!u.steps[r], a.disabled = d;
			let o = e.querySelector("[data-ai-fields]");
			o.hidden = !a.checked, a.checked && o.append(E(r)), a.onchange = () => {
				a.checked ? u.steps[r] = n(u.default) : delete u.steps[r], o.hidden = !a.checked, o.replaceChildren(), a.checked && o.append(E(r)), w();
			}, y("#ai-step-settings").append(e);
		}
		y("#save-ai-setup").disabled = d || f, T(), h && N();
	}
	function A(e, t) {
		if (!x(e)) return `${t}: choose a supported provider.`;
		if (e.model.length > 160 || e.model && !/^[a-zA-Z0-9][a-zA-Z0-9_./:@+-]*$/.test(e.model)) return `${t}: enter an exact model ID without spaces.`;
		if (e.connection && !l.some((t) => t.id === e.connection && t.provider === e.provider)) return `${t}: add or select a connection again; the previous session connection expired.`;
		if (e.backup) {
			if (!c.fallback) return "Update Vita CV and restart Vita Tree to use a backup.";
			let n = A(e.backup, `${t} backup`);
			if (n) return n;
			if (!e.backup.model) return `${t}: enter an exact backup model ID.`;
			if (e.backup.provider === e.provider && e.backup.model === e.model) return `${t}: choose a different backup model or provider.`;
			if (!e.backup.categories.length) return `${t}: choose at least one failure category for the backup.`;
			if (e.backup.provider === e.provider && e.backup.connection !== e.connection) return `${t}: use the same connection for models from the same provider.`;
		}
		return "";
	}
	function j(t = e.map(([e]) => e)) {
		if (!u) return "AI setup is loading.";
		for (let n of t.filter((e) => e !== "validating")) {
			let t = A(b(n), e.find(([e]) => e === n)?.[1] || n);
			if (t) return t;
		}
		return "";
	}
	y("#save-ai-setup").onclick = async () => {
		let e = s, t = n(u), r = j();
		if (r) O(r);
		else {
			f = !0, y("#save-ai-setup").disabled = !0;
			try {
				await i("/api/ai-settings", {
					branch: e,
					settings: t
				});
				let n = o.get(e);
				n && JSON.stringify(n.settings) === JSON.stringify(t) && (n.dirty = !1), s === e && JSON.stringify(u) === JSON.stringify(t) && (p = !1, y("#ai-setup-status").textContent = "Setup saved on this computer · API keys last until the server stops.");
			} catch (t) {
				s === e && O(t.message);
			} finally {
				f = !1, y("#save-ai-setup").disabled = d;
			}
		}
	}, y("#reset-ai-steps").onclick = () => {
		u.steps = {}, k(), w();
	};
	function M() {
		h && (y("#step-ai-error").hidden = !0, y("#step-ai-context").textContent = h.readOnly ? h.history ? "Recorded run · view only" : "View only" : h.custom ? "Custom setup for this step" : "Following shared setup");
	}
	function N() {
		let e = h;
		e && (y("#step-ai-fields").replaceChildren(), e.route && y("#step-ai-fields").append(E(e.step, e)), y("#step-ai-shared").checked = !e.custom, y("#step-ai-custom").checked = e.custom, y("#step-ai-mode").hidden = e.readOnly, y("#step-ai-mode").disabled = d || e.readOnly || !!e.saving, y("#step-ai-apply").hidden = e.readOnly, y("#step-ai-apply").disabled = d || !!e.saving, y("#step-ai-apply").textContent = e.saving ? "Applying…" : "Apply to step", y("#step-ai-cancel").textContent = e.readOnly ? "Close" : "Cancel", y("#step-ai-next").hidden = !e.readOnly || !e.allowNext, y("#step-ai-next").disabled = d, y("#step-ai-save-hint").hidden = e.readOnly, y("#close-step-ai").disabled = !!e.saving, y("#step-ai-cancel").disabled = !!e.saving, M());
	}
	function P(t, r = {}) {
		let i = e.find(([e]) => e === t)?.[1];
		if (!u || !i) return;
		let a = !!r.history, o = a || d || !!r.readOnly, c = a ? r.recorded : b(t);
		h = {
			step: t,
			branch: s,
			route: c ? n(c) : null,
			custom: !!u.steps[t],
			readOnly: o,
			history: a,
			allowNext: !!r.allowNext,
			saving: !1
		}, y("#step-requirements").hidden = t !== "extract", y("#step-ai-title").textContent = i, y("#step-ai-description").textContent = o ? c ? "These are the settings captured for this run. Editing the next run does not change these results." : "This older run did not record an AI setup. Configure the next run to choose its settings." : "Choose the AI for this component. Changes are applied only after you select Apply to step.", N(), y("#step-ai-dialog").open || y("#step-ai-dialog").showModal();
	}
	function F() {
		if (h?.saving) return;
		let e = h?.step;
		y("#step-ai-dialog").close(), h = null, queueMicrotask(() => document.querySelector(`.dag-node[data-step="${e}"]`)?.focus({ preventScroll: !0 }));
	}
	y("#close-step-ai").onclick = F, y("#step-ai-cancel").onclick = F, y("#step-ai-dialog").addEventListener("cancel", (e) => {
		e.preventDefault(), F();
	}), y("#step-ai-next").onclick = () => P(h.step);
	for (let e of ["shared", "custom"]) y("#step-ai-" + e).onchange = () => {
		!h || h.readOnly || d || (e === "shared" && h.custom && (h.customDraft = n(h.route)), h.custom = e === "custom", h.route = n(e === "custom" ? h.customDraft || b(h.step) : u.default), N());
	};
	y("#step-ai-form").onsubmit = async (e) => {
		e.preventDefault();
		let t = h;
		if (!t || t.readOnly || t.saving || d) return;
		let r = A(t.custom ? t.route : u.default, "This step");
		if (r) {
			y("#step-ai-error").textContent = r, y("#step-ai-error").hidden = !1;
			return;
		}
		let c = n(u), l = s;
		t.custom ? c.steps[t.step] = n(t.route) : delete c.steps[t.step], t.saving = !0, N();
		try {
			if (await i("/api/ai-settings", {
				branch: l,
				settings: c
			}), s !== l || h !== t) return;
			u = c, p = !1, o.set(s, {
				settings: n(u),
				dirty: p
			}), y("#ai-setup-status").textContent = "Setup saved on this computer · API keys last until the server stops.", t.saving = !1, F(), k(), a();
		} catch (e) {
			if (h === t) {
				t.saving = !1, N(), y("#step-ai-error").textContent = e.message, y("#step-ai-error").hidden = !1;
				let n = y("#step-ai-apply");
				(n.disabled ? y("#step-ai-cancel") : n).focus();
			}
		}
	};
	function I() {
		_ || (y("#generation-check-dialog").close(), g = null);
	}
	y("#close-generation-check").onclick = I, y("#cancel-generation-check").onclick = I, y("#generation-check-dialog").addEventListener("cancel", (e) => {
		e.preventDefault(), I();
	}), y("#generation-check-form").onsubmit = async (e) => {
		if (e.preventDefault(), _ || !g) return;
		let t = g;
		_ = !0;
		for (let e of [
			"confirm-generation-check",
			"cancel-generation-check",
			"close-generation-check"
		]) y("#" + e).disabled = !0;
		y("#generation-check-result").textContent = "Checking generation access… The provider may retry temporary failures.";
		try {
			let e = await i("/api/generation-check", {
				branch: t.branch,
				step: t.step,
				aiConfig: t.settings,
				confirmed: !0
			}), n = `${e.provider || "Effective provider unreported"} / ${e.model || "effective model unreported"}`, r = e.failure;
			y("#generation-check-result").textContent = e.generationVerified ? `Generation succeeded · ${n} · ${e.attempts ?? "unknown"} provider attempts. This does not evaluate CV quality.` : `${r?.title || "Generation was not verified"}${r?.category ? " (" + r.category.replaceAll("_", " ") + ")" : ""} · ${n} · ${e.attempts ?? "unknown"} provider attempts. ${r?.retryable === !0 ? "Retryable. " : r?.retryable === !1 ? "Needs attention before retry. " : ""}${r?.action || "Inspect the Vita CV connection."}`;
		} catch (e) {
			y("#generation-check-result").textContent = e.message;
		} finally {
			_ = !1;
			for (let e of [
				"confirm-generation-check",
				"cancel-generation-check",
				"close-generation-check"
			]) y("#" + e).disabled = !1;
			y("#cancel-generation-check").textContent = "Close";
		}
	};
	function L() {
		y("#add-connection").disabled || (y("#connection-dialog").close(), y("#connection-key").value = "", y("#connection-key").type = "password");
	}
	return y("#cancel-connection").onclick = L, y("#close-connection").onclick = L, y("#connection-dialog").addEventListener("cancel", (e) => {
		e.preventDefault(), L();
	}), y("#show-connection-key").onchange = () => {
		y("#connection-key").type = y("#show-connection-key").checked ? "text" : "password";
	}, y("#connection-form").onsubmit = async (e) => {
		if (e.preventDefault(), d) return;
		let t = m, n = t.route, r = t.branch, a = {
			name: y("#connection-name").value,
			provider: n.provider,
			apiKey: y("#connection-key").value
		};
		y("#add-connection").disabled = !0, y("#connection-error").hidden = !0;
		try {
			let e = await i("/api/connections", a);
			l.push(e);
			let o = s === r && (t.editor ? t.editor === h : n === (t.backup ? b(t.step).backup : b(t.step)));
			o && (n.connection = e.id, t.repaint(), t.notify()), y("#connection-dialog").close(), y("#connection-key").value = "", y("#connection-key").type = "password", o && y("#" + (t.editor ? "popup-" : t.step === "default" ? "" : t.step + "-") + (t.backup ? "backup-" : "") + "connection")?.focus({ preventScroll: !0 });
		} catch (e) {
			y("#connection-error").textContent = e.message, y("#connection-error").hidden = !1;
		} finally {
			a.apiKey = "", y("#add-connection").disabled = !1;
		}
	}, {
		load(e, t, r, i) {
			h &&= (y("#step-ai-dialog").close(), null), s = e, c = t, l = i.connections;
			let a = o.get(e);
			u = n(a?.settings || r), p = !!a?.dirty, o.set(e, {
				settings: n(u),
				dirty: p
			}), d = !1, k(), y("#ai-setup-status").textContent = p ? "Unsaved AI setup · save to keep it after reload." : "Choices are saved locally. API keys last for this server session.", y("#ai-setup-error").hidden = !0;
		},
		setDisabled(e) {
			e !== d && (d = e, k());
		},
		value() {
			return n(u);
		},
		route(e) {
			return b(e);
		},
		summary: S,
		connectionName: C,
		problem: j,
		refresh() {
			T();
		},
		openStep: P
	};
}
export { r as t };
