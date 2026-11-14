import { a as e, i as t, n, r, t as i } from "./frontend-jsx-runtime-DjpXSdWX.js";
// frontend/src/components/ApplicationList.tsx
var a = /* @__PURE__ */ e(r(), 1), o = n(), s = i();
function c({ rows: e, empty: t, onOpen: n, onSelect: r, relative: i }) {
	return e.length ? /* @__PURE__ */ (0, s.jsx)(s.Fragment, { children: e.map(({ branch: e, selected: t, selectable: a, status: o, label: c, failure: l }) => /* @__PURE__ */ (0, s.jsxs)("div", {
		className: "branch-entry",
		"data-branch": e.name,
		children: [/* @__PURE__ */ (0, s.jsx)("input", {
			type: "checkbox",
			className: "select-branch-review",
			"aria-label": `Select unreviewed results for ${e.displayName || e.name}`,
			disabled: !a,
			checked: t,
			onChange: (t) => r(e.name, t.target.checked)
		}), /* @__PURE__ */ (0, s.jsxs)("button", {
			type: "button",
			className: "branch-row",
			"aria-label": `Open ${e.displayName || e.name}`,
			onClick: () => n(e.name),
			children: [
				/* @__PURE__ */ (0, s.jsxs)("span", {
					className: "branch-cell",
					children: [/* @__PURE__ */ (0, s.jsxs)("svg", {
						className: "branch-icon",
						viewBox: "0 0 24 24",
						"aria-hidden": "true",
						width: "18",
						height: "18",
						children: [
							/* @__PURE__ */ (0, s.jsx)("path", { d: "M6 5v11a3 3 0 0 0 3 3h9M6 10h8a4 4 0 0 0 4-4" }),
							/* @__PURE__ */ (0, s.jsx)("circle", {
								cx: "6",
								cy: "4",
								r: "2"
							}),
							/* @__PURE__ */ (0, s.jsx)("circle", {
								cx: "18",
								cy: "4",
								r: "2"
							}),
							/* @__PURE__ */ (0, s.jsx)("circle", {
								cx: "18",
								cy: "19",
								r: "2"
							})
						]
					}), /* @__PURE__ */ (0, s.jsxs)("span", {
						className: "branch-info",
						children: [
							/* @__PURE__ */ (0, s.jsx)("span", {
								className: "branch-name",
								children: e.displayName || e.name
							}),
							/* @__PURE__ */ (0, s.jsx)("span", {
								className: "branch-detail",
								children: e.local ? "Editable CV" : "View only CV"
							}),
							c && /* @__PURE__ */ (0, s.jsx)("span", {
								className: "branch-run",
								"data-status": o,
								children: c
							}),
							l && /* @__PURE__ */ (0, s.jsx)("span", {
								className: "branch-failure",
								children: l
							})
						]
					})]
				}),
				/* @__PURE__ */ (0, s.jsxs)("span", {
					className: "commit-cell",
					children: [/* @__PURE__ */ (0, s.jsx)("span", {
						className: "commit-subject",
						children: e.subject
					}), /* @__PURE__ */ (0, s.jsx)("span", {
						className: "commit-meta",
						children: e.author
					})]
				}),
				/* @__PURE__ */ (0, s.jsx)("time", {
					className: "branch-date",
					dateTime: e.modifiedAt,
					title: new Date(e.modifiedAt).toLocaleString(),
					children: i(e.timestamp)
				})
			]
		})]
	}, e.name)) }) : /* @__PURE__ */ (0, s.jsx)("p", {
		className: "empty",
		children: t
	});
}
// frontend/src/components/WorkflowGraph.tsx
var l = /* @__PURE__ */ e(t(), 1), u = {
	succeeded: "m5 12 4 4L19 6",
	previous: "M12 7v5l3 2m6-2a9 9 0 1 1-9-9 9 9 0 0 1 9 9",
	running: "M12 3a9 9 0 1 1-9 9",
	review: "M8 10a4 4 0 1 0 8 0 4 4 0 0 0-8 0ZM4 21a8 8 0 0 1 16 0",
	failed: "M12 5v9m0 4v.1",
	interrupted: "M9 6v12m6-12v12",
	skipped: "M6 12h12",
	unavailable: "M6 12h12",
	blocked: "M6 12h12"
};
function d({ stages: e, statusNames: t, disabled: n, focusStep: r }) {
	let i = e.filter(({ status: e }) => ![
		"skipped",
		"unavailable",
		"previous"
	].includes(e));
	if (!i.length || i.some(({ status: e }) => e === "unknown")) return null;
	let a = i.filter(({ status: e }) => e === "succeeded").length, o = i.find(({ status: e }) => e === "review") ?? i.find(({ status: e }) => e === "running") ?? i.find(({ status: e }) => e === "failed" || e === "interrupted");
	return /* @__PURE__ */ (0, s.jsxs)("div", {
		className: "workflow-progress",
		children: [/* @__PURE__ */ (0, s.jsxs)("div", {
			className: "workflow-progress-label",
			children: [/* @__PURE__ */ (0, s.jsxs)("strong", { children: [
				a,
				" of ",
				i.length,
				" steps done"
			] }), o && /* @__PURE__ */ (0, s.jsxs)("button", {
				type: "button",
				"data-status": o.status,
				disabled: n,
				title: "Show this step in the workflow",
				onClick: () => r(o.id),
				children: [
					o.title,
					" ·",
					" ",
					t[o.status] || o.status
				]
			})]
		}), /* @__PURE__ */ (0, s.jsx)("progress", {
			"aria-label": "Steps done",
			value: a,
			max: i.length
		})]
	});
}
function f({ stages: e, run: t, selected: n, select: r, config: i, statusNames: a, disabled: o = !1 }) {
	let c = (0, l.useRef)(null);
	return /* @__PURE__ */ (0, s.jsxs)(s.Fragment, { children: [t && /* @__PURE__ */ (0, s.jsx)(d, {
		stages: e,
		statusNames: a,
		disabled: o,
		focusStep: (e) => c.current?.querySelector(`[data-step="${e}"]`)?.focus()
	}), /* @__PURE__ */ (0, s.jsx)("div", {
		className: "dag",
		ref: c,
		children: e.map((c, d) => {
			let f = (a[c.status] || c.status) + (c.reusedFrom ? " · reused" : "");
			t?.factualReview?.step === c.id && (f = {
				pending: "Needs factual review",
				resolved: "Factual decisions saved",
				unavailable: "Review unavailable"
			}[t.factualReview.state] || "Review unavailable"), c.id === "extract" && t?.requirementsApprovalNeeded && (f = "Needs requirements review"), [
				"analyze",
				"adapt",
				"review",
				"cover"
			].includes(c.id) && c.status === "succeeded" && t?.requirementsStatus && t.requirementsStatus !== "current" && (f += " · requirements changed");
			let p = i[c.id], m = t?.outcomes?.[c.id]?.backend?.routing, h = m?.effective, g = !!m?.chain?.length && m.chain.length > 1 && (!!h?.model && h.model !== m.chain[0]?.model || !!h?.provider && h.provider !== m.chain[0]?.provider), _ = c.previousRun ? "This step completed in an earlier preparation. Its results were not loaded or verified for this preparation. Use Retry on that earlier preparation to check checkpoint reuse." : c.id === "validating" ? void 0 : t ? "View the AI settings captured for this step" : "Configure the AI for this step";
			return /* @__PURE__ */ (0, s.jsxs)(l.Fragment, { children: [d > 0 && /* @__PURE__ */ (0, s.jsx)("span", {
				className: "dag-edge",
				"aria-hidden": "true",
				"data-status": e[d - 1].status
			}), /* @__PURE__ */ (0, s.jsxs)("button", {
				type: "button",
				className: "dag-node",
				disabled: o,
				"data-step": c.id,
				"data-status": c.status,
				"aria-pressed": n === c.id,
				"aria-haspopup": c.id === "validating" ? void 0 : "dialog",
				"aria-label": `${c.title}: ${f}. ${c.detail}`,
				title: _,
				onClick: () => r(c),
				onFocus: (e) => {
					let t = e.currentTarget;
					requestAnimationFrame(() => {
						document.activeElement === t && t.scrollIntoView({
							block: "nearest",
							inline: "nearest"
						});
					});
				},
				children: [
					/* @__PURE__ */ (0, s.jsx)("svg", {
						className: "dag-symbol",
						viewBox: "0 0 24 24",
						"aria-hidden": "true",
						children: /* @__PURE__ */ (0, s.jsx)("path", { d: u[c.status] || "M21 12a9 9 0 1 1-9-9 9 9 0 0 1 9 9" })
					}),
					/* @__PURE__ */ (0, s.jsx)("span", {
						className: "dag-status",
						children: f
					}),
					/* @__PURE__ */ (0, s.jsx)("strong", { children: c.title }),
					/* @__PURE__ */ (0, s.jsx)("span", {
						className: "dag-time",
						"data-started-at": c.startedAt && !c.finishedAt && c.status === "running" ? c.startedAt : void 0,
						children: c.previousRun ? "Historical result · not loaded" : c.startedAt ? `${Math.max(0, Math.floor((c.finishedAt || Date.now() / 1e3) - c.startedAt))}s` : c.output
					}),
					t?.requirementsRevision && c.id !== "validating" && /* @__PURE__ */ (0, s.jsxs)("span", {
						className: "dag-requirements",
						title: t.requirementsRevision,
						children: ["Requirements ", t.requirementsRevision.slice(0, 12)]
					}),
					p && /* @__PURE__ */ (0, s.jsxs)("span", {
						className: "dag-model",
						title: h?.provider ? `Used ${h.provider} / ${h.model || "model unreported"}${g ? " (backup)" : ""}. Requested ${p.provider} / ${p.model}` : [
							p.provider,
							p.model,
							p.reasoning || "Automatic reasoning"
						].filter(Boolean).join(" · "),
						children: [(h?.provider ? h.model || `${h.provider} · model unreported` : null) || p.model || `${p.provider} default`, g ? " · Backup" : ""]
					})
				]
			})] }, c.id);
		})
	})] });
}
// frontend/src/components/renderers.tsx
var p = /* @__PURE__ */ new WeakMap(), m = /* @__PURE__ */ new WeakMap();
function h(e) {
	let t = p.get(e);
	return t || (t = (0, o.createRoot)(e), p.set(e, t)), t;
}
function g(e, t) {
	(0, a.flushSync)(() => h(e).render(/* @__PURE__ */ (0, s.jsx)(c, { ...t })));
}
function _(e, t) {
	m.set(e, t), (0, a.flushSync)(() => h(e).render(/* @__PURE__ */ (0, s.jsx)(f, { ...t })));
}
function v(e) {
	let t = m.get(e);
	t && _(e, {
		...t,
		disabled: !0
	});
}
// frontend/src/compat/workflow.js
var y = [
	{
		id: "extract",
		title: "Identify job requirements",
		detail: "Identify the skills and experience the employer wants. On canonical backends, fresh extraction also drafts a reviewable definition in a separate generation operation; both may use provider credits.",
		output: "Job context and reviewable requirements"
	},
	{
		id: "analyze",
		title: "Check CV match",
		detail: "Compare your CV with the job requirements.",
		output: "CV match analysis"
	},
	{
		id: "adapt",
		title: "Tailor CV",
		detail: "Tailor the CV to the role and selected language.",
		output: "Tailored CV and summary"
	},
	{
		id: "review",
		title: "Review CV with AI",
		detail: "Get feedback on your current CV. When an earlier matching analysis is available, compare the scores.",
		output: "Feedback and score comparison"
	},
	{
		id: "cover",
		title: "Cover letter",
		detail: "Write a letter using the current CV and job context. Compiles a PDF before finishing. Adaptation is not required.",
		output: "Cover letter and PDF"
	},
	{
		id: "validating",
		title: "Final checks",
		detail: "Check the final files and protect your existing edits. Final tailoring and local checks compile and save a fresh CV PDF in the application folder.",
		output: "Application files and final PDFs"
	}
], b = {
	pending: "Not started",
	running: "In progress",
	succeeded: "Done",
	failed: "Couldn’t finish",
	blocked: "Waiting for an earlier step",
	interrupted: "Stopped before finishing",
	skipped: "Skipped",
	unavailable: "Not available",
	unknown: "No earlier details",
	review: "Needs your review",
	previous: "Earlier run only"
};
function x(e, t = {}, n = {}) {
	return y.map((r) => {
		let i = e?.stages?.find((e) => e.id === r.id);
		return !i && e && (i = { status: e.step === r.id && e.status === "running" ? "running" : "unknown" }), i ||= { status: [
			"extract",
			"review",
			"cover"
		].includes(r.id) && !n[r.id] ? "unavailable" : r.id === "validating" || t.steps?.includes(r.id) ? "pending" : "skipped" }, {
			...r,
			...i
		};
	});
}
function S(e, { run: t, options: n, available: r, selected: i, select: a, history: o = [], config: s = {} }) {
	let c = x(t, n, r).map((e) => {
		if (t?.factualReview?.state === "pending" && t.factualReview.step === e.id || e.id === "extract" && t?.requirementsApprovalNeeded) return {
			...e,
			status: "review"
		};
		if (e.status === "skipped") {
			let n = o.find((n) => n.id !== t?.id && (!t || n.createdAt < t.createdAt) && n.stages?.some((t) => t.id === e.id && t.status === "succeeded"));
			if (n) return {
				...e,
				status: "previous",
				previousRun: n.id
			};
		}
		return e;
	}), l = e.contains(document.activeElement) ? document.activeElement.dataset.step : null;
	_(e, {
		stages: c,
		run: t,
		selected: i,
		select: a,
		config: s,
		statusNames: b
	}), l && e.querySelector(`[data-step="${l}"]`)?.focus({ preventScroll: !0 });
}
export { v as a, y as i, S as n, g as o, b as r, x as t };
