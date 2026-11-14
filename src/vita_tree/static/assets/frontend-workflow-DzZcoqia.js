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
function d(e, t = !1) {
	let n = Math.max(0, Math.floor(e));
	return t ? `${String(Math.floor(n / 60)).padStart(2, "0")}:${String(n % 60).padStart(2, "0")}` : `${n}s`;
}
function f({ stages: e, run: t, statusNames: n, disabled: r, focusStep: i }) {
	let a = e.filter(({ status: e }) => ![
		"skipped",
		"unavailable",
		"previous"
	].includes(e)), o = a.length > 0 && !a.some(({ status: e }) => e === "unknown"), c = a.filter(({ status: e }) => e === "succeeded").length, l = t?.status === "running" && !t.finishedAt, u = a.find(({ status: e }) => e === "review") ?? a.find(({ status: e }) => e === "running") ?? a.find(({ status: e }) => e === "failed" || e === "interrupted");
	return /* @__PURE__ */ (0, s.jsxs)("div", {
		className: "workflow-progress",
		children: [/* @__PURE__ */ (0, s.jsxs)("div", {
			className: "workflow-progress-label",
			children: [/* @__PURE__ */ (0, s.jsxs)("div", {
				className: "workflow-progress-current",
				children: [/* @__PURE__ */ (0, s.jsx)("strong", { children: o ? `${c} of ${a.length} ${a.length === 1 ? "step" : "steps"} done` : "Step progress wasn’t recorded" }), u && /* @__PURE__ */ (0, s.jsxs)("button", {
					type: "button",
					"data-status": u.status,
					disabled: r,
					title: "Show this step in the workflow",
					onClick: () => i(u.id),
					children: [
						u.title,
						" ·",
						" ",
						n[u.status] || u.status
					]
				})]
			}), t?.startedAt && (l || t.finishedAt) && /* @__PURE__ */ (0, s.jsxs)("span", {
				className: "workflow-elapsed",
				children: [
					/* @__PURE__ */ (0, s.jsx)("span", {
						className: "dag-time",
						"data-started-at": l ? t.startedAt : void 0,
						"data-clock": "",
						children: d((t.finishedAt || Date.now() / 1e3) - t.startedAt, !0)
					}),
					" ",
					"elapsed"
				]
			})]
		}), o && /* @__PURE__ */ (0, s.jsx)("progress", {
			"aria-label": "Steps done",
			value: c,
			max: a.length
		})]
	});
}
function p({ task: e, run: t, select: n, disabled: r }) {
	let i = e.pendingReview, a = i ? "Needs you" : t?.factualReview?.step === "adapt" && t.factualReview.state === "resolved" ? "Decisions saved" : e.status === "unknown" ? "Not recorded" : [
		"skipped",
		"previous",
		"unavailable"
	].includes(e.status) ? "Skipped" : e.status === "succeeded" ? "No review recorded" : "If changes need review", o = /* @__PURE__ */ (0, s.jsxs)(s.Fragment, { children: [/* @__PURE__ */ (0, s.jsx)("svg", {
		className: "dag-symbol",
		viewBox: "0 0 24 24",
		"aria-hidden": "true",
		children: /* @__PURE__ */ (0, s.jsx)("path", { d: u.review })
	}), /* @__PURE__ */ (0, s.jsxs)("span", { children: [/* @__PURE__ */ (0, s.jsx)("strong", { children: "Approve CV changes" }), /* @__PURE__ */ (0, s.jsx)("span", { children: a })] })] });
	return i ? /* @__PURE__ */ (0, s.jsx)("button", {
		type: "button",
		className: "dag-gate",
		"data-pending": "true",
		disabled: r,
		"aria-haspopup": "dialog",
		onClick: () => n(e),
		children: o
	}) : /* @__PURE__ */ (0, s.jsx)("div", {
		className: "dag-gate",
		children: o
	});
}
function m({ stages: e, run: t, selected: n, select: r, config: i, statusNames: a, disabled: o = !1 }) {
	let c = (0, l.useRef)(null), m = Object.fromEntries(e.map(({ id: e, status: t }) => [e, t])), h = !!m.adapt && !!m.review;
	return /* @__PURE__ */ (0, s.jsxs)(s.Fragment, { children: [t && /* @__PURE__ */ (0, s.jsx)(f, {
		stages: e,
		run: t,
		statusNames: a,
		disabled: o,
		focusStep: (e) => c.current?.querySelector(`[data-step="${e}"]`)?.focus()
	}), /* @__PURE__ */ (0, s.jsx)("div", {
		className: "dag",
		ref: c,
		children: /* @__PURE__ */ (0, s.jsxs)("div", {
			className: "dag-map",
			children: [
				h && /* @__PURE__ */ (0, s.jsxs)("div", {
					className: "dag-return",
					children: [/* @__PURE__ */ (0, s.jsx)("svg", {
						viewBox: "0 0 100 100",
						preserveAspectRatio: "none",
						"aria-hidden": "true",
						children: /* @__PURE__ */ (0, s.jsx)("path", {
							d: "M84 34C84 1 16 1 16 76",
							vectorEffect: "non-scaling-stroke"
						})
					}), /* @__PURE__ */ (0, s.jsx)("span", { children: "Revise CV in a new preparation" })]
				}),
				[
					"extract",
					"analyze",
					"adapt"
				].map((e) => m[e] && /* @__PURE__ */ (0, s.jsx)("span", {
					className: "dag-edge",
					"data-from": e,
					"data-status": m[e],
					"aria-hidden": "true"
				}, e)),
				m.review && m.cover && /* @__PURE__ */ (0, s.jsxs)(s.Fragment, { children: [/* @__PURE__ */ (0, s.jsx)("svg", {
					className: "dag-split",
					viewBox: "0 0 100 100",
					preserveAspectRatio: "none",
					"aria-hidden": "true",
					children: /* @__PURE__ */ (0, s.jsx)("path", {
						d: "M0 50C58 50 42 25 100 25M0 50C58 50 42 75 100 75",
						vectorEffect: "non-scaling-stroke"
					})
				}), /* @__PURE__ */ (0, s.jsx)("svg", {
					className: "dag-join",
					viewBox: "0 0 100 100",
					preserveAspectRatio: "none",
					"aria-hidden": "true",
					children: /* @__PURE__ */ (0, s.jsx)("path", {
						d: "M0 25C58 25 42 50 100 50M0 75C58 75 42 50 100 50",
						vectorEffect: "non-scaling-stroke"
					})
				})] }),
				e.map((e, c) => {
					let f = (a[e.status] || e.status) + (e.reusedFrom ? " · reused" : "");
					t?.factualReview?.step === e.id && (f = {
						pending: "Needs factual review",
						resolved: "Factual decisions saved",
						unavailable: "Review unavailable"
					}[t.factualReview.state] || "Review unavailable"), e.id === "extract" && t?.requirementsApprovalNeeded && (f = "Needs requirements review"), [
						"analyze",
						"adapt",
						"review",
						"cover"
					].includes(e.id) && e.status === "succeeded" && t?.requirementsStatus && t.requirementsStatus !== "current" && (f += " · requirements changed");
					let m = i[e.id], h = t?.outcomes?.[e.id]?.backend?.routing, g = h?.effective, _ = !!h?.chain?.length && h.chain.length > 1 && (!!g?.model && g.model !== h.chain[0]?.model || !!g?.provider && g.provider !== h.chain[0]?.provider), v = e.previousRun ? "This step completed in an earlier preparation. Its results were not loaded or verified for this preparation. Use Retry on that earlier preparation to check checkpoint reuse." : e.id === "validating" ? void 0 : t ? "View the AI settings captured for this step" : "Configure the AI for this step";
					return /* @__PURE__ */ (0, s.jsxs)(l.Fragment, { children: [/* @__PURE__ */ (0, s.jsxs)("button", {
						type: "button",
						className: "dag-node",
						disabled: o,
						"data-step": e.id,
						"data-status": e.status,
						"aria-pressed": n === e.id,
						"aria-haspopup": e.id === "validating" ? void 0 : "dialog",
						"aria-label": `${e.title}: ${f}. ${e.detail}`,
						title: v,
						onClick: () => r(e),
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
								children: /* @__PURE__ */ (0, s.jsx)("path", { d: u[e.status] || "M21 12a9 9 0 1 1-9-9 9 9 0 0 1 9 9" })
							}),
							/* @__PURE__ */ (0, s.jsxs)("span", {
								className: "dag-state",
								children: [/* @__PURE__ */ (0, s.jsxs)("span", {
									className: "dag-index",
									children: ["Step ", c + 1]
								}), /* @__PURE__ */ (0, s.jsx)("span", {
									className: "dag-status",
									children: f
								})]
							}),
							/* @__PURE__ */ (0, s.jsx)("strong", { children: e.title }),
							t?.requirementsRevision && e.id !== "validating" && /* @__PURE__ */ (0, s.jsxs)("span", {
								className: "dag-requirements",
								title: t.requirementsRevision,
								children: ["Requirements ", t.requirementsRevision.slice(0, 12)]
							}),
							/* @__PURE__ */ (0, s.jsxs)("span", {
								className: "dag-meta",
								children: [m ? /* @__PURE__ */ (0, s.jsxs)("span", {
									className: "dag-model",
									title: g?.provider ? `Used ${g.provider} / ${g.model || "model unreported"}${_ ? " (backup)" : ""}. Requested ${m.provider} / ${m.model}` : [
										m.provider,
										m.model,
										m.reasoning || "Automatic reasoning"
									].filter(Boolean).join(" · "),
									children: [(g?.provider ? g.model || `${g.provider} · model unreported` : null) || m.model || `${m.provider} default`, _ ? " · Backup" : ""]
								}) : e.id === "validating" ? /* @__PURE__ */ (0, s.jsx)("span", {
									className: "dag-local",
									children: "No AI"
								}) : null, (e.previousRun || e.startedAt) && /* @__PURE__ */ (0, s.jsx)("span", {
									className: "dag-time",
									"data-clock": e.status === "running" ? "" : void 0,
									"data-started-at": e.startedAt && !e.finishedAt && e.status === "running" ? e.startedAt : void 0,
									children: e.previousRun ? "Historical result · not loaded" : e.startedAt ? d((e.finishedAt || Date.now() / 1e3) - e.startedAt, e.status === "running") : ""
								})]
							})
						]
					}), e.id === "adapt" && /* @__PURE__ */ (0, s.jsx)(p, {
						task: e,
						run: t,
						select: r,
						disabled: o
					})] }, e.id);
				})
			]
		})
	})] });
}
// frontend/src/components/renderers.tsx
var h = /* @__PURE__ */ new WeakMap(), g = /* @__PURE__ */ new WeakMap();
function _(e) {
	let t = h.get(e);
	return t || (t = (0, o.createRoot)(e), h.set(e, t)), t;
}
function v(e, t) {
	(0, a.flushSync)(() => _(e).render(/* @__PURE__ */ (0, s.jsx)(c, { ...t })));
}
function y(e, t) {
	g.set(e, t), (0, a.flushSync)(() => _(e).render(/* @__PURE__ */ (0, s.jsx)(m, { ...t })));
}
function b(e) {
	let t = g.get(e);
	t && y(e, {
		...t,
		disabled: !0
	});
}
// frontend/src/compat/workflow.js
var x = [
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
], S = {
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
}, C = (e) => !!(e?.requirementsApprovalNeeded || e?.factualReview?.state === "pending" || e?.status === "awaiting_review"), w = (e, t) => C(e) && (e.source === "jobenu" ? e.pendingStep === t : t === "extract" && e.requirementsApprovalNeeded || e.factualReview?.state === "pending" && e.factualReview.step === t);
function T(e, t = {}, n = {}) {
	return x.map((r) => {
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
function E(e, { run: t, options: n, available: r, selected: i, select: a, history: o = [], config: s = {} }) {
	let c = T(t, n, r).map((e) => {
		if (w(t, e.id)) return {
			...e,
			status: "review",
			pendingReview: !0
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
	y(e, {
		stages: c,
		run: t,
		selected: i,
		select: a,
		config: s,
		statusNames: S
	}), l && e.querySelector(`[data-step="${l}"]`)?.focus({ preventScroll: !0 });
}
export { w as a, v as c, S as i, d as l, C as n, x as o, E as r, b as s, T as t };
