import { a as e, n as t, r as n, t as r } from "./frontend-jsx-runtime-DjpXSdWX.js";
// frontend/src/components/ApplicationList.tsx
var i = /* @__PURE__ */ e(n(), 1), a = t(), o = r();
function s({ rows: e, empty: t, onOpen: n, onSelect: r, relative: i }) {
	return e.length ? /* @__PURE__ */ (0, o.jsx)(o.Fragment, { children: e.map(({ branch: e, selected: t, selectable: a, status: s, label: c, failure: l }) => /* @__PURE__ */ (0, o.jsxs)("div", {
		className: "branch-entry",
		"data-branch": e.name,
		children: [/* @__PURE__ */ (0, o.jsx)("input", {
			type: "checkbox",
			className: "select-branch-review",
			"aria-label": `Select unreviewed results for ${e.displayName || e.name}`,
			disabled: !a,
			checked: t,
			onChange: (t) => r(e.name, t.target.checked)
		}), /* @__PURE__ */ (0, o.jsxs)("button", {
			type: "button",
			className: "branch-row",
			"aria-label": `Open ${e.displayName || e.name}`,
			onClick: () => n(e.name),
			children: [
				/* @__PURE__ */ (0, o.jsxs)("span", {
					className: "branch-cell",
					children: [/* @__PURE__ */ (0, o.jsxs)("svg", {
						className: "branch-icon",
						viewBox: "0 0 24 24",
						"aria-hidden": "true",
						width: "18",
						height: "18",
						children: [
							/* @__PURE__ */ (0, o.jsx)("path", { d: "M6 5v11a3 3 0 0 0 3 3h9M6 10h8a4 4 0 0 0 4-4" }),
							/* @__PURE__ */ (0, o.jsx)("circle", {
								cx: "6",
								cy: "4",
								r: "2"
							}),
							/* @__PURE__ */ (0, o.jsx)("circle", {
								cx: "18",
								cy: "4",
								r: "2"
							}),
							/* @__PURE__ */ (0, o.jsx)("circle", {
								cx: "18",
								cy: "19",
								r: "2"
							})
						]
					}), /* @__PURE__ */ (0, o.jsxs)("span", {
						className: "branch-info",
						children: [
							/* @__PURE__ */ (0, o.jsx)("span", {
								className: "branch-name",
								children: e.displayName || e.name
							}),
							/* @__PURE__ */ (0, o.jsx)("span", {
								className: "branch-detail",
								children: e.local ? "Editable CV" : "View only CV"
							}),
							c && /* @__PURE__ */ (0, o.jsx)("span", {
								className: "branch-run",
								"data-status": s,
								children: c
							}),
							l && /* @__PURE__ */ (0, o.jsx)("span", {
								className: "branch-failure",
								children: l
							})
						]
					})]
				}),
				/* @__PURE__ */ (0, o.jsxs)("span", {
					className: "commit-cell",
					children: [/* @__PURE__ */ (0, o.jsx)("span", {
						className: "commit-subject",
						children: e.subject
					}), /* @__PURE__ */ (0, o.jsx)("span", {
						className: "commit-meta",
						children: e.author
					})]
				}),
				/* @__PURE__ */ (0, o.jsx)("time", {
					className: "branch-date",
					dateTime: e.modifiedAt,
					title: new Date(e.modifiedAt).toLocaleString(),
					children: i(e.timestamp)
				})
			]
		})]
	}, e.name)) }) : /* @__PURE__ */ (0, o.jsx)("p", {
		className: "empty",
		children: t
	});
}
// frontend/src/components/WorkflowGraph.tsx
function c({ stages: e, run: t, selected: n, select: r, config: i, statusNames: a, disabled: s = !1 }) {
	return /* @__PURE__ */ (0, o.jsx)(o.Fragment, { children: e.map((c, l) => {
		let u = (a[c.status] || c.status) + (c.reusedFrom ? " · reused" : "");
		t?.factualReview?.step === c.id && (u = {
			pending: "Needs factual review",
			resolved: "Factual decisions saved",
			unavailable: "Review unavailable"
		}[t.factualReview.state] || "Review unavailable"), c.id === "extract" && t?.requirementsApprovalNeeded && (u = "Needs requirements review"), [
			"analyze",
			"adapt",
			"review",
			"cover"
		].includes(c.id) && c.status === "succeeded" && t?.requirementsStatus && t.requirementsStatus !== "current" && (u += " · requirements changed");
		let d = i[c.id], f = c.previousRun ? "This step completed in an earlier preparation. Its results were not loaded or verified for this preparation. Use Retry on that earlier preparation to check checkpoint reuse." : c.id === "validating" ? void 0 : t ? "View the AI settings captured for this step" : "Configure the AI for this step";
		return /* @__PURE__ */ (0, o.jsxs)("span", {
			className: "workflow-stage-group",
			children: [l > 0 && /* @__PURE__ */ (0, o.jsx)("span", {
				className: "dag-edge",
				"aria-hidden": "true",
				"data-status": e[l - 1].status,
				children: "→"
			}), /* @__PURE__ */ (0, o.jsxs)("button", {
				type: "button",
				className: "dag-node",
				disabled: s,
				"data-step": c.id,
				"data-status": c.status,
				"aria-pressed": n === c.id,
				"aria-haspopup": c.id === "validating" ? void 0 : "dialog",
				"aria-label": `${c.title}: ${a[c.status] || c.status}. ${c.detail}`,
				title: f,
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
					/* @__PURE__ */ (0, o.jsx)("svg", {
						className: "dag-symbol",
						viewBox: "0 0 24 24",
						"aria-hidden": "true",
						children: /* @__PURE__ */ (0, o.jsx)("path", { d: ["succeeded", "previous"].includes(c.status) ? "m5 12 4 4L19 6" : ["failed", "interrupted"].includes(c.status) ? "M12 5v9m0 4v.1" : [
							"skipped",
							"unavailable",
							"blocked"
						].includes(c.status) ? "M6 12h12" : "M21 12a9 9 0 1 1-9-9 9 9 0 0 1 9 9" })
					}),
					/* @__PURE__ */ (0, o.jsx)("strong", { children: c.title }),
					/* @__PURE__ */ (0, o.jsx)("span", {
						className: "dag-status",
						children: u
					}),
					/* @__PURE__ */ (0, o.jsx)("span", {
						className: "dag-time",
						"data-started-at": c.startedAt && !c.finishedAt && c.status === "running" ? c.startedAt : void 0,
						children: c.previousRun ? "Historical result · not loaded" : c.startedAt ? `${Math.max(0, Math.floor((c.finishedAt || Date.now() / 1e3) - c.startedAt))}s` : c.output
					}),
					t?.requirementsRevision && c.id !== "validating" && /* @__PURE__ */ (0, o.jsxs)("span", {
						className: "dag-requirements",
						title: t.requirementsRevision,
						children: ["Requirements ", t.requirementsRevision.slice(0, 12)]
					}),
					d && /* @__PURE__ */ (0, o.jsx)("span", {
						className: "dag-model",
						title: `${d.provider} · ${d.reasoning || "Automatic reasoning"}`,
						children: d.model || `${d.provider} default`
					})
				]
			})]
		}, c.id);
	}) });
}
// frontend/src/components/renderers.tsx
var l = /* @__PURE__ */ new WeakMap(), u = /* @__PURE__ */ new WeakMap();
function d(e) {
	let t = l.get(e);
	return t || (t = (0, a.createRoot)(e), l.set(e, t)), t;
}
function f(e, t) {
	(0, i.flushSync)(() => d(e).render(/* @__PURE__ */ (0, o.jsx)(s, { ...t })));
}
function p(e, t) {
	u.set(e, t), (0, i.flushSync)(() => d(e).render(/* @__PURE__ */ (0, o.jsx)(c, { ...t })));
}
function m(e) {
	let t = u.get(e);
	t && p(e, {
		...t,
		disabled: !0
	});
}
// frontend/src/compat/workflow.js
var h = [
	{
		id: "extract",
		title: "Identify job requirements",
		detail: "Identify the skills and experience the employer wants.",
		output: "Job requirements"
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
		detail: "Check the document files and protect your existing edits. CV PDF previews are created separately.",
		output: "Application files"
	}
], g = {
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
function _(e, t = {}, n = {}) {
	return h.map((r) => {
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
function v(e, { run: t, options: n, available: r, selected: i, select: a, history: o = [], config: s = {} }) {
	let c = _(t, n, r).map((e) => {
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
	p(e, {
		stages: c,
		run: t,
		selected: i,
		select: a,
		config: s,
		statusNames: g
	}), l && e.querySelector(`[data-step="${l}"]`)?.focus({ preventScroll: !0 });
}
export { m as a, h as i, v as n, f as o, g as r, _ as t };
