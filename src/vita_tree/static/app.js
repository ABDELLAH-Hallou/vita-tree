import { a as e, i as t, n, r, t as i } from "./assets/frontend-jsx-runtime-DjpXSdWX.js";
import { n as a } from "./assets/frontend-client-Cqgf6Pc4.js";
// node_modules/@tanstack/react-query/build/modern/QueryClientProvider.js
var o = /* @__PURE__ */ e(t(), 1), s = i(), c = o.createContext(void 0), l = ({ client: e, children: t }) => (o.useEffect(() => (e.mount(), () => {
	e.unmount();
}), [e]), /* @__PURE__ */ (0, s.jsx)(c.Provider, {
	value: e,
	children: t
})), u = /* @__PURE__ */ e(r(), 1), d = n(), f = (0, o.memo)(function() {
	return /* @__PURE__ */ (0, s.jsx)("section", {
		id: "board",
		children: /* @__PURE__ */ (0, s.jsxs)("div", {
			className: "board-layout",
			children: [/* @__PURE__ */ (0, s.jsxs)("aside", {
				className: "board-nav",
				"aria-label": "Application filters",
				children: [
					/* @__PURE__ */ (0, s.jsx)("p", {
						className: "nav-label",
						children: "Applications"
					}),
					/* @__PURE__ */ (0, s.jsxs)("button", {
						"data-filter": "all",
						"aria-pressed": "true",
						children: [/* @__PURE__ */ (0, s.jsx)("span", { children: "All applications" }), /* @__PURE__ */ (0, s.jsx)("span", {
							id: "filter-all",
							children: "0"
						})]
					}),
					/* @__PURE__ */ (0, s.jsxs)("button", {
						"data-filter": "running",
						"aria-pressed": "false",
						children: [/* @__PURE__ */ (0, s.jsxs)("span", { children: [/* @__PURE__ */ (0, s.jsx)("i", { className: "status-dot running" }), "In progress"] }), /* @__PURE__ */ (0, s.jsx)("span", {
							id: "filter-running",
							children: "0"
						})]
					}),
					/* @__PURE__ */ (0, s.jsxs)("button", {
						"data-filter": "review",
						"aria-pressed": "false",
						children: [/* @__PURE__ */ (0, s.jsxs)("span", { children: [/* @__PURE__ */ (0, s.jsx)("i", { className: "status-dot succeeded" }), "Needs review"] }), /* @__PURE__ */ (0, s.jsx)("span", {
							id: "filter-review",
							children: "0"
						})]
					}),
					/* @__PURE__ */ (0, s.jsxs)("button", {
						"data-filter": "failed",
						"aria-pressed": "false",
						children: [/* @__PURE__ */ (0, s.jsxs)("span", { children: [/* @__PURE__ */ (0, s.jsx)("i", { className: "status-dot failed" }), "Needs attention"] }), /* @__PURE__ */ (0, s.jsx)("span", {
							id: "filter-failed",
							children: "0"
						})]
					}),
					/* @__PURE__ */ (0, s.jsx)("button", {
						id: "show-activity",
						"data-open-diagnostics": "",
						children: "Activity & support"
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "workspace-note",
						children: [
							/* @__PURE__ */ (0, s.jsx)("strong", { children: "A tailored CV for every opportunity" }),
							/* @__PURE__ */ (0, s.jsx)("p", { children: "Choose a starting CV, add the job description, and prepare your application. Review the results before saving." }),
							/* @__PURE__ */ (0, s.jsx)("span", { children: "Powered by Vita CV" })
						]
					})
				]
			}), /* @__PURE__ */ (0, s.jsxs)("div", {
				className: "branch-table",
				children: [
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "page-heading",
						children: [/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsxs)("h1", { children: [
							"Applications",
							" ",
							/* @__PURE__ */ (0, s.jsx)("span", {
								id: "total-count",
								className: "count",
								children: "0"
							})
						] }), /* @__PURE__ */ (0, s.jsx)("p", {
							className: "subtitle",
							children: "A tailored CV and cover letter for every opportunity."
						})] }), /* @__PURE__ */ (0, s.jsx)("button", {
							id: "new-branch",
							className: "primary",
							disabled: !0,
							children: "＋ New application"
						})]
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "list-toolbar",
						children: [/* @__PURE__ */ (0, s.jsxs)("label", {
							className: "search",
							children: [
								/* @__PURE__ */ (0, s.jsx)("span", {
									"aria-hidden": "true",
									children: "⌕"
								}),
								/* @__PURE__ */ (0, s.jsx)("input", {
									id: "search",
									type: "search",
									placeholder: "Search applications…",
									"aria-label": "Search applications"
								}),
								/* @__PURE__ */ (0, s.jsx)("kbd", { children: "/" })
							]
						}), /* @__PURE__ */ (0, s.jsx)("button", {
							id: "refresh",
							className: "quiet",
							children: "↻ Refresh"
						})]
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "bulk-review-toolbar",
						children: [
							/* @__PURE__ */ (0, s.jsxs)("label", { children: [/* @__PURE__ */ (0, s.jsx)("input", {
								id: "select-review-visible",
								type: "checkbox"
							}), " Select visible applications with unreviewed results"] }),
							/* @__PURE__ */ (0, s.jsx)("button", {
								id: "bulk-review",
								disabled: !0,
								children: "Mark selected as reviewed"
							}),
							/* @__PURE__ */ (0, s.jsx)("span", {
								id: "bulk-review-count",
								className: "helper"
							})
						]
					}),
					/* @__PURE__ */ (0, s.jsx)("p", {
						id: "bulk-review-status",
						className: "bulk-review-status",
						role: "status",
						hidden: !0
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "list-head",
						children: [
							/* @__PURE__ */ (0, s.jsx)("span", { children: "Application" }),
							/* @__PURE__ */ (0, s.jsx)("span", { children: "Last saved update" }),
							/* @__PURE__ */ (0, s.jsx)("span", { children: "Updated" })
						]
					}),
					/* @__PURE__ */ (0, s.jsx)("div", {
						id: "branch-list",
						"aria-live": "polite",
						children: /* @__PURE__ */ (0, s.jsx)("p", {
							className: "empty",
							children: "Loading applications…"
						})
					}),
					/* @__PURE__ */ (0, s.jsxs)("footer", {
						className: "list-footer",
						children: [/* @__PURE__ */ (0, s.jsx)("span", { id: "result-count" }), /* @__PURE__ */ (0, s.jsx)("span", { children: "Latest activity first" })]
					})
				]
			})]
		})
	});
}), p = (0, o.memo)(function() {
	return /* @__PURE__ */ (0, s.jsxs)("section", {
		id: "workspace",
		hidden: !0,
		children: [
			/* @__PURE__ */ (0, s.jsxs)("div", {
				className: "workspace-heading",
				children: [/* @__PURE__ */ (0, s.jsxs)("div", { children: [
					/* @__PURE__ */ (0, s.jsx)("button", {
						id: "back",
						className: "back",
						children: "← All applications"
					}),
					/* @__PURE__ */ (0, s.jsx)("h1", { id: "branch-title" }),
					/* @__PURE__ */ (0, s.jsx)("p", {
						id: "workspace-caption",
						className: "subtitle"
					})
				] }), /* @__PURE__ */ (0, s.jsxs)("div", {
					className: "actions",
					children: [/* @__PURE__ */ (0, s.jsx)("button", {
						id: "reload",
						children: "↻ Reload"
					}), /* @__PURE__ */ (0, s.jsx)("button", {
						id: "branch-from",
						children: "＋ Use this CV for a new application"
					})]
				})]
			}),
			/* @__PURE__ */ (0, s.jsxs)("div", {
				className: "setup-bar",
				children: [/* @__PURE__ */ (0, s.jsx)("p", {
					id: "setup-summary",
					role: "status",
					children: "CV files are checked automatically before preparation."
				}), /* @__PURE__ */ (0, s.jsx)("button", {
					"data-open-setup": "",
					type: "button",
					children: "Check CV files"
				})]
			}),
			/* @__PURE__ */ (0, s.jsxs)("section", {
				className: "workflow-panel",
				"aria-labelledby": "workflow-title",
				children: [
					/* @__PURE__ */ (0, s.jsxs)("header", {
						className: "workflow-heading",
						children: [/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("h2", {
							id: "workflow-title",
							children: "Prepare your application"
						}), /* @__PURE__ */ (0, s.jsx)("p", {
							id: "workflow-summary",
							role: "status",
							children: "Choose how to prepare this application."
						})] }), /* @__PURE__ */ (0, s.jsxs)("div", {
							className: "actions",
							children: [
								/* @__PURE__ */ (0, s.jsxs)("label", {
									className: "run-picker",
									children: [/* @__PURE__ */ (0, s.jsx)("span", {
										className: "sr-only",
										children: "Preparation history"
									}), /* @__PURE__ */ (0, s.jsx)("select", {
										id: "workflow-run",
										"aria-label": "Preparation history",
										children: /* @__PURE__ */ (0, s.jsx)("option", {
											value: "draft",
											children: "New preparation"
										})
									})]
								}),
								/* @__PURE__ */ (0, s.jsx)("button", {
									id: "inspect-run",
									className: "quiet",
									hidden: !0,
									children: "Execution details"
								}),
								/* @__PURE__ */ (0, s.jsx)("button", {
									id: "view-run",
									className: "quiet",
									hidden: !0,
									children: "View results"
								}),
								/* @__PURE__ */ (0, s.jsx)("button", {
									id: "requirements-current-open",
									children: "Job requirements"
								}),
								/* @__PURE__ */ (0, s.jsx)("button", {
									id: "requirements-captured",
									hidden: !0
								}),
								/* @__PURE__ */ (0, s.jsx)("button", {
									id: "review-facts",
									hidden: !0,
									children: "Review factual changes"
								}),
								/* @__PURE__ */ (0, s.jsx)("button", {
									id: "resume-run",
									hidden: !0,
									children: "Retry preparation"
								}),
								/* @__PURE__ */ (0, s.jsx)("button", {
									id: "mark-run-reviewed",
									hidden: !0,
									children: "Mark as reviewed"
								}),
								/* @__PURE__ */ (0, s.jsx)("button", {
									id: "toggle-workflow",
									className: "quiet",
									"aria-expanded": "true",
									"aria-controls": "workflow-body",
									children: "Hide steps"
								})
							]
						})]
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						id: "workflow-action",
						className: "workflow-action",
						children: [/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("strong", { children: "Your next step" }), /* @__PURE__ */ (0, s.jsx)("p", { id: "workflow-next-help" })] }), /* @__PURE__ */ (0, s.jsx)("button", {
							id: "workflow-next",
							className: "primary",
							children: "Prepare application"
						})]
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						id: "workflow-body",
						children: [
							/* @__PURE__ */ (0, s.jsx)("div", {
								id: "workflow-graph",
								className: "dag",
								role: "group",
								"aria-label": "Application preparation steps"
							}),
							/* @__PURE__ */ (0, s.jsxs)("footer", {
								className: "workflow-footer",
								children: [/* @__PURE__ */ (0, s.jsx)("span", { children: "Click an AI step to configure it. Prepare everything, choose a few steps, or start one step on its own." }), /* @__PURE__ */ (0, s.jsxs)("span", { children: [
									/* @__PURE__ */ (0, s.jsx)("i", { className: "status-dot running" }),
									"In progress",
									" ",
									/* @__PURE__ */ (0, s.jsx)("i", { className: "status-dot succeeded" }),
									"Done",
									" ",
									/* @__PURE__ */ (0, s.jsx)("i", { className: "status-dot failed" }),
									"Couldn’t finish"
								] })]
							}),
							/* @__PURE__ */ (0, s.jsxs)("div", {
								id: "task-inspector",
								className: "task-inspector",
								hidden: !0,
								children: [/* @__PURE__ */ (0, s.jsxs)("div", { children: [
									/* @__PURE__ */ (0, s.jsx)("strong", { id: "task-title" }),
									/* @__PURE__ */ (0, s.jsx)("p", { id: "task-description" }),
									/* @__PURE__ */ (0, s.jsx)("span", {
										id: "task-status",
										className: "helper"
									})
								] }), /* @__PURE__ */ (0, s.jsxs)("div", {
									className: "actions",
									children: [
										/* @__PURE__ */ (0, s.jsx)("button", {
											id: "task-requirements",
											hidden: !0,
											children: "Review job requirements"
										}),
										/* @__PURE__ */ (0, s.jsx)("button", {
											id: "task-configure",
											children: "Configure AI"
										}),
										/* @__PURE__ */ (0, s.jsx)("button", {
											id: "inspect-step",
											className: "quiet",
											hidden: !0,
											children: "Inspect execution"
										}),
										/* @__PURE__ */ (0, s.jsx)("button", {
											id: "task-output",
											children: "View results"
										}),
										/* @__PURE__ */ (0, s.jsx)("button", {
											id: "task-run",
											className: "primary",
											children: "Start this step"
										})
									]
								})]
							})
						]
					})
				]
			}),
			/* @__PURE__ */ (0, s.jsxs)("dialog", {
				id: "factual-review-panel",
				className: "factual-review",
				"aria-labelledby": "factual-review-title",
				hidden: !0,
				children: [
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "review-heading",
						children: [/* @__PURE__ */ (0, s.jsx)("h2", {
							id: "factual-sheet-title",
							children: "Check your changes"
						}), /* @__PURE__ */ (0, s.jsx)("button", {
							id: "close-factual-review",
							type: "button",
							"aria-label": "Close factual review",
							children: "Close"
						})]
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "review-scroll",
						children: [
							/* @__PURE__ */ (0, s.jsx)("h2", {
								id: "factual-review-title",
								tabIndex: -1,
								children: "Review factual changes"
							}),
							/* @__PURE__ */ (0, s.jsx)("p", { id: "factual-review-summary" }),
							/* @__PURE__ */ (0, s.jsx)("p", {
								className: "helper",
								children: "Check that the proposed wording is accurate. Reject keeps your original wording. Keeping all originals for a cover letter preserves the previous letter, if any."
							}),
							/* @__PURE__ */ (0, s.jsxs)("details", {
								className: "technical-details",
								children: [/* @__PURE__ */ (0, s.jsx)("summary", { children: "Captured revision" }), /* @__PURE__ */ (0, s.jsx)("code", { id: "factual-review-revision" })]
							}),
							/* @__PURE__ */ (0, s.jsxs)("form", {
								id: "factual-review-form",
								children: [
									/* @__PURE__ */ (0, s.jsxs)("div", {
										id: "factual-bulk",
										className: "review-bulk",
										children: [
											/* @__PURE__ */ (0, s.jsx)("span", {
												id: "factual-choice-count",
												role: "status"
											}),
											/* @__PURE__ */ (0, s.jsx)("button", {
												id: "accept-all-facts",
												type: "button",
												children: "Accept all"
											}),
											/* @__PURE__ */ (0, s.jsx)("button", {
												id: "reject-all-facts",
												type: "button",
												children: "Keep all originals"
											})
										]
									}),
									/* @__PURE__ */ (0, s.jsx)("div", { id: "factual-review-items" }),
									/* @__PURE__ */ (0, s.jsxs)("details", { children: [/* @__PURE__ */ (0, s.jsx)("summary", { children: "Full proposed LaTeX · syntax check" }), /* @__PURE__ */ (0, s.jsx)("div", {
										id: "factual-source-preview",
										className: "review-source-preview"
									})] }),
									/* @__PURE__ */ (0, s.jsx)("p", {
										id: "factual-provenance",
										className: "helper",
										hidden: !0
									})
								]
							})
						]
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "review-controls",
						children: [
							/* @__PURE__ */ (0, s.jsxs)("label", {
								id: "factual-review-confirmation",
								className: "factual-confirm",
								children: [
									/* @__PURE__ */ (0, s.jsx)("input", {
										id: "confirm-factual-meaning",
										form: "factual-review-form",
										type: "checkbox",
										required: !0
									}),
									" ",
									"I reviewed every change and confirm the factual meaning of my accepted and edited wording."
								]
							}),
							/* @__PURE__ */ (0, s.jsx)("p", {
								id: "factual-review-error",
								className: "error",
								role: "alert"
							}),
							/* @__PURE__ */ (0, s.jsx)("p", {
								id: "factual-review-progress",
								role: "status"
							}),
							/* @__PURE__ */ (0, s.jsxs)("div", {
								className: "panel-footer",
								children: [/* @__PURE__ */ (0, s.jsx)("span", { children: "Your application updates after the remaining steps and final checks succeed." }), /* @__PURE__ */ (0, s.jsxs)("div", {
									className: "actions",
									children: [/* @__PURE__ */ (0, s.jsx)("button", {
										id: "cancel-factual-review",
										type: "button",
										children: "Close without changes"
									}), /* @__PURE__ */ (0, s.jsx)("button", {
										id: "apply-factual-review",
										form: "factual-review-form",
										className: "primary",
										type: "submit",
										children: "Approve & continue"
									})]
								})]
							})
						]
					})
				]
			}),
			/* @__PURE__ */ (0, s.jsxs)("div", {
				className: "workspace-toolbar",
				children: [/* @__PURE__ */ (0, s.jsxs)("div", {
					className: "tabs",
					role: "tablist",
					"aria-label": "Application view",
					children: [
						/* @__PURE__ */ (0, s.jsx)("button", {
							role: "tab",
							"data-view": "structure",
							"aria-selected": "true",
							children: "Edit CV"
						}),
						/* @__PURE__ */ (0, s.jsx)("button", {
							role: "tab",
							"data-view": "source",
							"aria-selected": "false",
							children: "Source · Advanced"
						}),
						/* @__PURE__ */ (0, s.jsx)("button", {
							role: "tab",
							"data-view": "pdf",
							"aria-selected": "false",
							children: "PDF preview"
						}),
						/* @__PURE__ */ (0, s.jsxs)("button", {
							role: "tab",
							"data-view": "changes",
							"aria-selected": "false",
							children: ["Changes ", /* @__PURE__ */ (0, s.jsx)("span", { id: "change-count" })]
						}),
						/* @__PURE__ */ (0, s.jsxs)("button", {
							role: "tab",
							"data-view": "ai",
							"aria-selected": "false",
							children: ["Job details & AI ", /* @__PURE__ */ (0, s.jsx)("span", { id: "ai-dot" })]
						})
					]
				}), /* @__PURE__ */ (0, s.jsxs)("div", {
					id: "document-actions",
					className: "actions",
					children: [
						/* @__PURE__ */ (0, s.jsx)("span", {
							id: "save-state",
							children: "Saved"
						}),
						/* @__PURE__ */ (0, s.jsx)("button", {
							id: "save-source",
							disabled: !0,
							children: "Save draft"
						}),
						/* @__PURE__ */ (0, s.jsx)("button", {
							id: "commit-push",
							className: "primary",
							disabled: !0,
							children: "Save"
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, s.jsx)("div", {
				id: "notice",
				className: "notice",
				role: "status",
				hidden: !0
			}),
			/* @__PURE__ */ (0, s.jsxs)("details", {
				id: "message-details",
				className: "technical-details",
				hidden: !0,
				children: [/* @__PURE__ */ (0, s.jsx)("summary", { children: "Technical details" }), /* @__PURE__ */ (0, s.jsx)("pre", { id: "message-technical" })]
			}),
			/* @__PURE__ */ (0, s.jsxs)("div", {
				id: "structure-hint",
				className: "view-hint",
				children: [/* @__PURE__ */ (0, s.jsx)("span", { children: "Double-click text in your current CV to edit it." }), /* @__PURE__ */ (0, s.jsx)("span", { children: "PDF shows the exact layout." })]
			}),
			/* @__PURE__ */ (0, s.jsxs)("section", {
				id: "file-navigation",
				className: "file-navigation",
				"aria-label": "CV files",
				children: [
					/* @__PURE__ */ (0, s.jsx)("label", {
						htmlFor: "cv-file",
						children: "CV file"
					}),
					/* @__PURE__ */ (0, s.jsx)("select", { id: "cv-file" }),
					/* @__PURE__ */ (0, s.jsx)("p", {
						id: "file-help",
						className: "helper",
						children: "Each file is edited separately. PDF assembles the complete CV; Structure approximates each file without executing macros or conditional includes."
					}),
					/* @__PURE__ */ (0, s.jsxs)("details", {
						id: "include-problems",
						hidden: !0,
						children: [/* @__PURE__ */ (0, s.jsx)("summary", { children: "Include files need attention" }), /* @__PURE__ */ (0, s.jsx)("ul", { id: "include-diagnostics" })]
					})
				]
			}),
			/* @__PURE__ */ (0, s.jsxs)("div", {
				id: "pdf-toolbar",
				className: "view-hint",
				hidden: !0,
				children: [/* @__PURE__ */ (0, s.jsxs)("div", {
					className: "actions",
					children: [
						/* @__PURE__ */ (0, s.jsxs)("label", { children: [
							"Document",
							" ",
							/* @__PURE__ */ (0, s.jsxs)("select", {
								id: "pdf-document",
								children: [/* @__PURE__ */ (0, s.jsx)("option", {
									value: "cv",
									children: "CV comparison"
								}), /* @__PURE__ */ (0, s.jsx)("option", {
									value: "cover",
									children: "Cover letter"
								})]
							})
						] }),
						/* @__PURE__ */ (0, s.jsxs)("details", {
							className: "pdf-settings",
							children: [/* @__PURE__ */ (0, s.jsx)("summary", { children: "Advanced PDF settings" }), /* @__PURE__ */ (0, s.jsxs)("label", { children: [
								"PDF engine",
								" ",
								/* @__PURE__ */ (0, s.jsxs)("select", {
									id: "engine",
									children: [
										/* @__PURE__ */ (0, s.jsx)("option", {
											value: "auto",
											children: "Automatic"
										}),
										/* @__PURE__ */ (0, s.jsx)("option", { children: "pdflatex" }),
										/* @__PURE__ */ (0, s.jsx)("option", { children: "xelatex" }),
										/* @__PURE__ */ (0, s.jsx)("option", { children: "lualatex" })
									]
								})
							] })]
						}),
						/* @__PURE__ */ (0, s.jsx)("button", {
							id: "compile",
							children: "Create PDF previews"
						})
					]
				}), /* @__PURE__ */ (0, s.jsxs)("div", {
					className: "actions",
					children: [/* @__PURE__ */ (0, s.jsxs)("label", { children: [
						"Zoom",
						" ",
						/* @__PURE__ */ (0, s.jsxs)("select", {
							id: "zoom",
							children: [
								/* @__PURE__ */ (0, s.jsx)("option", {
									value: "fit",
									children: "Fit width"
								}),
								/* @__PURE__ */ (0, s.jsx)("option", {
									value: "1",
									children: "100%"
								}),
								/* @__PURE__ */ (0, s.jsx)("option", {
									value: "1.25",
									children: "125%"
								}),
								/* @__PURE__ */ (0, s.jsx)("option", {
									value: "1.5",
									children: "150%"
								})
							]
						})
					] }), /* @__PURE__ */ (0, s.jsx)("span", { children: "Select and copy text directly from the PDF" })]
				})]
			}),
			/* @__PURE__ */ (0, s.jsxs)("div", {
				id: "comparison",
				className: "comparison",
				children: [/* @__PURE__ */ (0, s.jsxs)("section", {
					className: "pane",
					children: [
						/* @__PURE__ */ (0, s.jsxs)("header", {
							className: "pane-heading",
							children: [/* @__PURE__ */ (0, s.jsxs)("div", { children: [
								/* @__PURE__ */ (0, s.jsx)("span", { className: "pane-dot" }),
								/* @__PURE__ */ (0, s.jsx)("strong", { children: "Before" }),
								/* @__PURE__ */ (0, s.jsx)("span", { id: "original-label" })
							] }), /* @__PURE__ */ (0, s.jsx)("span", {
								className: "pill",
								children: "View only"
							})]
						}),
						/* @__PURE__ */ (0, s.jsx)("div", {
							id: "original-document",
							className: "document-scroll",
							children: /* @__PURE__ */ (0, s.jsx)("article", { className: "cv-document" })
						}),
						/* @__PURE__ */ (0, s.jsx)("div", {
							id: "original-source",
							className: "source-editor",
							hidden: !0
						}),
						/* @__PURE__ */ (0, s.jsx)("div", {
							id: "original-pdf",
							className: "pdf-scroll",
							hidden: !0
						})
					]
				}), /* @__PURE__ */ (0, s.jsxs)("section", {
					className: "pane",
					children: [
						/* @__PURE__ */ (0, s.jsxs)("header", {
							className: "pane-heading",
							children: [/* @__PURE__ */ (0, s.jsxs)("div", { children: [
								/* @__PURE__ */ (0, s.jsx)("span", { className: "pane-dot purple" }),
								/* @__PURE__ */ (0, s.jsx)("strong", { children: "Current CV" }),
								/* @__PURE__ */ (0, s.jsx)("span", { id: "current-label" })
							] }), /* @__PURE__ */ (0, s.jsx)("span", {
								id: "version-label",
								className: "pill accent",
								children: "Editable"
							})]
						}),
						/* @__PURE__ */ (0, s.jsx)("div", {
							id: "current-document",
							className: "document-scroll",
							children: /* @__PURE__ */ (0, s.jsx)("article", { className: "cv-document" })
						}),
						/* @__PURE__ */ (0, s.jsx)("div", {
							id: "current-source",
							className: "source-editor",
							hidden: !0
						}),
						/* @__PURE__ */ (0, s.jsx)("div", {
							id: "current-pdf",
							className: "pdf-scroll",
							hidden: !0
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, s.jsxs)("section", {
				id: "cover-pdf-pane",
				className: "pane cover-pdf-pane",
				hidden: !0,
				children: [/* @__PURE__ */ (0, s.jsxs)("header", {
					className: "pane-heading",
					children: [/* @__PURE__ */ (0, s.jsx)("strong", { children: "Cover letter" }), /* @__PURE__ */ (0, s.jsx)("span", {
						id: "cover-pdf-label",
						className: "helper"
					})]
				}), /* @__PURE__ */ (0, s.jsx)("div", {
					id: "cover-pdf",
					className: "pdf-scroll"
				})]
			}),
			/* @__PURE__ */ (0, s.jsxs)("section", {
				id: "changes-panel",
				className: "content-panel",
				hidden: !0,
				children: [/* @__PURE__ */ (0, s.jsxs)("div", {
					className: "panel-heading",
					children: [/* @__PURE__ */ (0, s.jsx)("h2", { children: "What changed" }), /* @__PURE__ */ (0, s.jsx)("p", { children: "Compared with the original shown on the left." })]
				}), /* @__PURE__ */ (0, s.jsx)("pre", {
					id: "diff",
					className: "diff"
				})]
			}),
			/* @__PURE__ */ (0, s.jsxs)("section", {
				id: "ai-panel",
				className: "ai-grid",
				hidden: !0,
				children: [
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "content-panel",
						children: [
							/* @__PURE__ */ (0, s.jsxs)("div", {
								className: "panel-heading",
								children: [/* @__PURE__ */ (0, s.jsx)("h2", { children: "Job description" }), /* @__PURE__ */ (0, s.jsx)("p", { children: "Keep the role, company, and requirements with this application." })]
							}),
							/* @__PURE__ */ (0, s.jsx)("textarea", {
								id: "job-description",
								"aria-label": "Job description",
								placeholder: "Paste the role, company, requirements, and full job description…"
							}),
							/* @__PURE__ */ (0, s.jsxs)("div", {
								className: "panel-footer",
								children: [/* @__PURE__ */ (0, s.jsx)("span", { id: "job-state" }), /* @__PURE__ */ (0, s.jsx)("button", {
									id: "save-job",
									children: "Save job description"
								})]
							})
						]
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "content-panel",
						children: [
							/* @__PURE__ */ (0, s.jsxs)("div", {
								className: "panel-heading",
								children: [/* @__PURE__ */ (0, s.jsx)("h2", { children: "Prepare with AI" }), /* @__PURE__ */ (0, s.jsx)("p", { children: "Connect your AI, choose the steps, and prepare your application. Customize a step whenever it needs a different model." })]
							}),
							/* @__PURE__ */ (0, s.jsx)("div", { id: "ai-configuration" }),
							/* @__PURE__ */ (0, s.jsx)("div", {
								className: "ai-language",
								children: /* @__PURE__ */ (0, s.jsxs)("label", { children: ["Output language", /* @__PURE__ */ (0, s.jsx)("select", {
									id: "language",
									disabled: !0,
									children: /* @__PURE__ */ (0, s.jsx)("option", {
										value: "en",
										children: "English"
									})
								})] })
							}),
							/* @__PURE__ */ (0, s.jsxs)("label", {
								className: "review-policy",
								children: [
									"Review mode",
									/* @__PURE__ */ (0, s.jsxs)("select", {
										id: "review-policy",
										children: [/* @__PURE__ */ (0, s.jsx)("option", {
											value: "manual",
											children: "Review before continuing"
										}), /* @__PURE__ */ (0, s.jsx)("option", {
											value: "automatic",
											children: "Automatic · accept AI proposals"
										})]
									}),
									/* @__PURE__ */ (0, s.jsx)("small", { children: "Automatic mode accepts requirements and factual changes for this run. Validation still runs. It does not save to Git or push." })
								]
							}),
							/* @__PURE__ */ (0, s.jsxs)("fieldset", {
								className: "workflow-options",
								children: [
									/* @__PURE__ */ (0, s.jsx)("legend", { children: "Choose your steps" }),
									/* @__PURE__ */ (0, s.jsxs)("label", { children: [/* @__PURE__ */ (0, s.jsx)("input", {
										id: "step-extract",
										type: "checkbox"
									}), /* @__PURE__ */ (0, s.jsxs)("span", { children: [
										"Identify job requirements",
										/* @__PURE__ */ (0, s.jsx)("small", {
											id: "hint-extract",
											children: "Understand what the employer is looking for."
										}),
										/* @__PURE__ */ (0, s.jsx)("small", { className: "step-ai-summary" })
									] })] }),
									/* @__PURE__ */ (0, s.jsxs)("label", { children: [/* @__PURE__ */ (0, s.jsx)("input", {
										id: "step-analyze",
										type: "checkbox"
									}), /* @__PURE__ */ (0, s.jsxs)("span", { children: [
										"Check CV match",
										/* @__PURE__ */ (0, s.jsx)("small", { children: "See how your CV matches the job." }),
										/* @__PURE__ */ (0, s.jsx)("small", { className: "step-ai-summary" })
									] })] }),
									/* @__PURE__ */ (0, s.jsxs)("label", { children: [/* @__PURE__ */ (0, s.jsx)("input", {
										id: "step-adapt",
										type: "checkbox"
									}), /* @__PURE__ */ (0, s.jsxs)("span", { children: [
										"Tailor CV",
										/* @__PURE__ */ (0, s.jsx)("small", { children: "Adjust your CV for this opportunity." }),
										/* @__PURE__ */ (0, s.jsx)("small", { className: "step-ai-summary" })
									] })] }),
									/* @__PURE__ */ (0, s.jsxs)("label", { children: [/* @__PURE__ */ (0, s.jsx)("input", {
										id: "step-review",
										type: "checkbox"
									}), /* @__PURE__ */ (0, s.jsxs)("span", { children: [
										"Review CV with AI",
										/* @__PURE__ */ (0, s.jsx)("small", {
											id: "hint-review",
											children: "Get feedback on your current CV."
										}),
										/* @__PURE__ */ (0, s.jsx)("small", { className: "step-ai-summary" })
									] })] }),
									/* @__PURE__ */ (0, s.jsxs)("label", { children: [/* @__PURE__ */ (0, s.jsx)("input", {
										id: "step-cover",
										type: "checkbox"
									}), /* @__PURE__ */ (0, s.jsxs)("span", { children: [
										"Cover letter",
										/* @__PURE__ */ (0, s.jsx)("small", {
											id: "hint-cover",
											children: "Write the cover letter and create its PDF."
										}),
										/* @__PURE__ */ (0, s.jsx)("small", { className: "step-ai-summary" })
									] })] })
								]
							}),
							/* @__PURE__ */ (0, s.jsx)("p", {
								id: "ai-config-validation",
								className: "ai-setup-error",
								role: "alert",
								hidden: !0
							}),
							/* @__PURE__ */ (0, s.jsxs)("details", {
								className: "technical-details",
								children: [/* @__PURE__ */ (0, s.jsx)("summary", { children: "AI connection details" }), /* @__PURE__ */ (0, s.jsx)("pre", { id: "model-details" })]
							}),
							/* @__PURE__ */ (0, s.jsx)("p", {
								id: "ai-capability",
								className: "helper"
							}),
							/* @__PURE__ */ (0, s.jsxs)("div", {
								className: "panel-footer",
								children: [/* @__PURE__ */ (0, s.jsx)("span", {
									id: "ai-status",
									role: "status",
									children: "Save a job description to get started"
								}), /* @__PURE__ */ (0, s.jsxs)("div", {
									className: "actions",
									children: [/* @__PURE__ */ (0, s.jsx)("button", {
										id: "run-all",
										children: "Prepare application"
									}), /* @__PURE__ */ (0, s.jsx)("button", {
										id: "run-adapt",
										className: "primary",
										children: "Start selected steps"
									})]
								})]
							}),
							/* @__PURE__ */ (0, s.jsx)("p", {
								className: "helper privacy",
								children: "Uses your configured AI provider and sends it the CV and job context."
							})
						]
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "content-panel artifacts",
						children: [/* @__PURE__ */ (0, s.jsxs)("div", {
							className: "panel-heading",
							children: [/* @__PURE__ */ (0, s.jsx)("h2", { children: "AI results" }), /* @__PURE__ */ (0, s.jsx)("p", { children: "Read the feedback and suggested changes for this application." })]
						}), /* @__PURE__ */ (0, s.jsx)("div", { id: "artifacts" })]
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						id: "selected-run",
						className: "content-panel artifacts",
						hidden: !0,
						children: [
							/* @__PURE__ */ (0, s.jsxs)("div", {
								className: "panel-heading",
								children: [/* @__PURE__ */ (0, s.jsx)("h2", { children: "Results from this preparation" }), /* @__PURE__ */ (0, s.jsx)("p", { id: "selected-run-info" })]
							}),
							/* @__PURE__ */ (0, s.jsx)("div", {
								id: "attempt-history",
								className: "attempt-history"
							}),
							/* @__PURE__ */ (0, s.jsx)("div", { id: "selected-run-files" })
						]
					})
				]
			}),
			/* @__PURE__ */ (0, s.jsxs)("footer", {
				className: "workspace-footer",
				children: [/* @__PURE__ */ (0, s.jsxs)("details", {
					className: "technical-details",
					children: [
						/* @__PURE__ */ (0, s.jsx)("summary", { children: "Application details" }),
						/* @__PURE__ */ (0, s.jsxs)("p", { children: ["Internal identifier: ", /* @__PURE__ */ (0, s.jsx)("code", { id: "application-id" })] }),
						/* @__PURE__ */ (0, s.jsxs)("p", { children: ["Application folder: ", /* @__PURE__ */ (0, s.jsx)("code", { id: "worktree-path" })] }),
						/* @__PURE__ */ (0, s.jsxs)("p", { children: [
							"CV source: ",
							/* @__PURE__ */ (0, s.jsx)("code", { children: "main.tex" }),
							" · Job description:",
							" ",
							/* @__PURE__ */ (0, s.jsx)("code", { children: "job.md" })
						] })
					]
				}), /* @__PURE__ */ (0, s.jsxs)("div", {
					className: "actions",
					children: [/* @__PURE__ */ (0, s.jsx)("span", { children: "Save draft keeps your edits on this computer. Save records a version and syncs it." }), /* @__PURE__ */ (0, s.jsx)("button", {
						className: "quiet",
						"data-open-diagnostics": "",
						children: "Activity & support"
					})]
				})]
			})
		]
	});
}), m = Object.defineProperty, h = (e, t) => m(e, "name", {
	value: t,
	configurable: !0
});
function g(e, t) {
	if (typeof e == "function") return e(t);
	e != null && (e.current = t);
}
h(g, "setRef");
function _(...e) {
	return (t) => {
		let n = !1, r = e.map((e) => {
			let r = g(e, t);
			return !n && typeof r == "function" && (n = !0), r;
		});
		if (n) return () => {
			for (let t = 0; t < r.length; t++) {
				let n = r[t];
				typeof n == "function" ? n() : g(e[t], null);
			}
		};
	};
}
h(_, "composeRefs");
function v(...e) {
	return o.useCallback(_(...e), e);
}
h(v, "useComposedRefs");
// node_modules/@radix-ui/react-slot/dist/index.mjs
var y = Object.defineProperty, b = (e, t) => y(e, "name", {
	value: t,
	configurable: !0
});
// @__NO_SIDE_EFFECTS__
function x(e) {
	let t = o.forwardRef((t, n) => {
		let { children: r, ...i } = t, a = null, s = !1, c = [];
		r = j(r), o.Children.forEach(r, (e) => {
			if (D(e)) {
				s = !0;
				let t = e, n = "child" in t.props ? t.props.child : t.props.children;
				for (; k(n) && typeof P == "function";) n = P(n._payload);
				a = w(t, n), c.push(a?.props?.children);
			} else c.push(e);
		}), a ? a = o.cloneElement(a, void 0, c) : !s && o.Children.count(r) === 1 && o.isValidElement(r) && (a = r);
		let l = a ? E(a) : void 0, u = v(n, l);
		if (!a) {
			if (r || r === 0) throw Error(s ? N(e) : ee(e));
			return r;
		}
		let d = T(i, a.props ?? {});
		return a.type !== o.Fragment && (d.ref = n ? u : l), o.cloneElement(a, d);
	});
	return t.displayName = `${e}.Slot`, t;
}
b(x, "createSlot");
var S = Symbol.for("radix.slottable");
// @__NO_SIDE_EFFECTS__
function C(e) {
	let t = /* @__PURE__ */ b((e) => "child" in e ? e.children(e.child) : e.children, "Slottable");
	return t.displayName = `${e}.Slottable`, t.__radixId = S, t;
}
b(C, "createSlottable");
var w = /* @__PURE__ */ b((e, t) => "child" in e.props ? o.isValidElement(t) ? o.cloneElement(t, void 0, e.props.children(t.props.children)) : null : o.isValidElement(t) ? t : null, "getSlottableElementFromSlottable");
function T(e, t) {
	let n = { ...t };
	for (let r in t) {
		let i = e[r], a = t[r];
		/^on[A-Z]/.test(r) ? i && a ? n[r] = (...e) => {
			let t = a(...e);
			return i(...e), t;
		} : i && (n[r] = i) : r === "style" ? n[r] = {
			...i,
			...a
		} : r === "className" ? n[r] = [i, a].filter(Boolean).join(" ") : r === "aria-describedby" && (n[r] = M(a, i));
	}
	return {
		...e,
		...n
	};
}
b(T, "mergeProps");
function E(e) {
	let t = Object.getOwnPropertyDescriptor(e.props, "ref")?.get, n = t && "isReactWarning" in t && t.isReactWarning;
	return n ? e.ref : (t = Object.getOwnPropertyDescriptor(e, "ref")?.get, n = t && "isReactWarning" in t && t.isReactWarning, n ? e.props.ref : e.props.ref || e.ref);
}
b(E, "getElementRef");
function D(e) {
	return o.isValidElement(e) && typeof e.type == "function" && "__radixId" in e.type && e.type.__radixId === S;
}
b(D, "isSlottable");
var O = Symbol.for("react.lazy");
function k(e) {
	return typeof e == "object" && !!e && "$$typeof" in e && e.$$typeof === O && "_payload" in e && A(e._payload);
}
b(k, "isLazyComponent");
function A(e) {
	return typeof e == "object" && !!e && "then" in e;
}
b(A, "isPromiseLike");
function j(e) {
	let t = e;
	for (; k(t) && typeof P == "function";) t = P(t._payload);
	return t;
}
b(j, "useUnwrappedLazy");
function M(...e) {
	let t = /* @__PURE__ */ new Set();
	for (let n of e) if (typeof n == "string") for (let e of String(n).trim().split(/\s+/)) e && t.add(e);
	return t.size > 0 ? Array.from(t).join(" ") : void 0;
}
b(M, "concatAriaDescribedby");
var ee = /* @__PURE__ */ b((e) => `${e} failed to slot onto its children. Expected a single React element child or \`Slottable\`.`, "createSlotError"), N = /* @__PURE__ */ b((e) => `${e} failed to slot onto its \`Slottable\`. Expected \`Slottable\` to receive a single React element child.`, "createSlottableError"), P = o.use, te = Object.defineProperty, ne = (e, t) => te(e, "name", {
	value: t,
	configurable: !0
}), F = [
	"a",
	"button",
	"div",
	"form",
	"h2",
	"h3",
	"img",
	"input",
	"label",
	"li",
	"nav",
	"ol",
	"p",
	"select",
	"span",
	"svg",
	"ul"
].reduce((e, t) => {
	let n = /* @__PURE__ */ x(`Primitive.${t}`), r = o.forwardRef((e, r) => {
		let { asChild: i, ...a } = e, o = i ? n : t;
		return typeof window < "u" && (window[Symbol.for("radix-ui")] = !0), /* @__PURE__ */ (0, s.jsx)(o, {
			...a,
			ref: r
		});
	});
	return r.displayName = `Primitive.${t}`, {
		...e,
		[t]: r
	};
}, {});
function re(e, t) {
	e && u.flushSync(() => e.dispatchEvent(t));
}
ne(re, "dispatchDiscreteCustomEvent");
// node_modules/@radix-ui/react-context/dist/index.mjs
var ie = Object.defineProperty, I = (e, t) => ie(e, "name", {
	value: t,
	configurable: !0
});
// @__NO_SIDE_EFFECTS__
function ae(e, t) {
	let n = o.createContext(t);
	n.displayName = e + "Context";
	let r = /* @__PURE__ */ I((e) => {
		let { children: t, ...r } = e, i = o.useMemo(() => r, Object.values(r));
		return /* @__PURE__ */ (0, s.jsx)(n.Provider, {
			value: i,
			children: t
		});
	}, "Provider");
	r.displayName = e + "Provider";
	function i(r, i = {}) {
		let { optional: a = !1 } = i, s = o.useContext(n);
		if (s) return s;
		if (t !== void 0) return t;
		if (!a) throw Error(`\`${r}\` must be used within \`${e}\``);
	}
	return I(i, "useContext"), [r, i];
}
I(ae, "createContext");
// @__NO_SIDE_EFFECTS__
function L(e, t = []) {
	let n = [];
	function r(t, r) {
		let i = o.createContext(r);
		i.displayName = t + "Context";
		let a = n.length;
		n = [...n, r];
		let c = /* @__PURE__ */ I((t) => {
			let { scope: n, children: r, ...c } = t, l = n?.[e]?.[a] || i, u = o.useMemo(() => c, Object.values(c));
			return /* @__PURE__ */ (0, s.jsx)(l.Provider, {
				value: u,
				children: r
			});
		}, "Provider");
		c.displayName = t + "Provider";
		function l(n, s, c = {}) {
			let { optional: l = !1 } = c, u = s?.[e]?.[a] || i, d = o.useContext(u);
			if (d) return d;
			if (r !== void 0) return r;
			if (!l) throw Error(`\`${n}\` must be used within \`${t}\``);
		}
		return I(l, "useContext"), [c, l];
	}
	I(r, "createContext");
	let i = /* @__PURE__ */ I(() => {
		let t = n.map((e) => o.createContext(e));
		return /* @__PURE__ */ I(function(n) {
			let r = n?.[e] || t;
			return o.useMemo(() => ({ [`__scope${e}`]: {
				...n,
				[e]: r
			} }), [n, r]);
		}, "useScope");
	}, "createScope");
	return i.scopeName = e, [r, oe(i, ...t)];
}
I(L, "createContextScope");
function oe(...e) {
	let t = e[0];
	if (e.length === 1) return t;
	let n = /* @__PURE__ */ I(() => {
		let n = e.map((e) => ({
			useScope: e(),
			scopeName: e.scopeName
		}));
		return /* @__PURE__ */ I(function(e) {
			let r = n.reduce((t, { useScope: n, scopeName: r }) => {
				let i = n(e)[`__scope${r}`];
				return {
					...t,
					...i
				};
			}, {});
			return o.useMemo(() => ({ [`__scope${t.scopeName}`]: r }), [r]);
		}, "useComposedScopes");
	}, "createScope");
	return n.scopeName = t.scopeName, n;
}
I(oe, "composeContextScopes");
// node_modules/@radix-ui/react-use-layout-effect/dist/index.mjs
var R = globalThis?.document ? o.useLayoutEffect : () => {}, se = Object.defineProperty, z = (e, t) => se(e, "name", {
	value: t,
	configurable: !0
});
// @__NO_SIDE_EFFECTS__
function ce(e) {
	let t = e + "CollectionProvider", [n, r] = /* @__PURE__ */ L(t), [i, a] = n(t, {
		collectionRef: { current: null },
		itemMap: /* @__PURE__ */ new Map()
	}), c = /* @__PURE__ */ z((e) => {
		let { scope: t, children: n } = e, r = o.useRef(null), a = o.useRef(/* @__PURE__ */ new Map()).current;
		return /* @__PURE__ */ (0, s.jsx)(i, {
			scope: t,
			itemMap: a,
			collectionRef: r,
			children: n
		});
	}, "CollectionProvider");
	c.displayName = t;
	let l = e + "CollectionSlot", u = /* @__PURE__ */ x(l), d = o.forwardRef((e, t) => {
		let { scope: n, children: r } = e, i = v(t, a(l, n).collectionRef);
		return /* @__PURE__ */ (0, s.jsx)(u, {
			ref: i,
			children: r
		});
	});
	d.displayName = l;
	let f = e + "CollectionItemSlot", p = "data-radix-collection-item", m = /* @__PURE__ */ x(f), h = o.forwardRef((e, t) => {
		let { scope: n, children: r, ...i } = e, c = o.useRef(null), l = v(t, c), u = a(f, n);
		return o.useEffect(() => (u.itemMap.set(c, {
			ref: c,
			...i
		}), () => void u.itemMap.delete(c))), /* @__PURE__ */ (0, s.jsx)(m, {
			[p]: "",
			ref: l,
			children: r
		});
	});
	h.displayName = f;
	function g(t) {
		let n = a(e + "CollectionConsumer", t);
		return o.useCallback(() => {
			let e = n.collectionRef.current;
			if (!e) return [];
			let t = Array.from(e.querySelectorAll(`[${p}]`));
			return Array.from(n.itemMap.values()).sort((e, n) => t.indexOf(e.ref.current) - t.indexOf(n.ref.current));
		}, [n.collectionRef, n.itemMap]);
	}
	return z(g, "useCollection"), [
		{
			Provider: c,
			Slot: d,
			ItemSlot: h
		},
		g,
		r
	];
}
z(ce, "createCollection");
var le = /* @__PURE__ */ new WeakMap(), ue = class e extends Map {
	static {
		z(this, "OrderedDict");
	}
	#e;
	constructor(e) {
		super(e), this.#e = [...super.keys()], le.set(this, !0);
	}
	set(e, t) {
		return le.get(this) && !this.has(e) && this.#e.push(e), super.set(e, t), this;
	}
	insert(e, t, n) {
		let r = this.has(t), i = r ? this.size : this.size + 1, a = pe(e), o = a >= 0 ? Math.min(a, i - 1) : Math.max(i + a, 0);
		if (r ? this.#e.indexOf(t) === o : o === this.size) return this.set(t, n), this;
		let s = this.#e.filter((e) => e !== t);
		s.splice(o, 0, t);
		let c = s.map((e) => [e, e === t ? n : this.get(e)]);
		this.clear();
		for (let [e, t] of c) this.set(e, t);
		return this;
	}
	with(t, n, r) {
		let i = new e(this);
		return i.insert(t, n, r), i;
	}
	before(e) {
		let t = this.#e.indexOf(e) - 1;
		if (!(t < 0)) return this.entryAt(t);
	}
	setBefore(e, t, n) {
		let r = this.#e.indexOf(e);
		if (r === -1) return this;
		let i = this.#e.indexOf(t), a = i !== -1 && i < r ? r - 1 : r;
		return this.insert(a, t, n);
	}
	after(e) {
		let t = this.#e.indexOf(e);
		if (t = t === -1 || t === this.size - 1 ? -1 : t + 1, t !== -1) return this.entryAt(t);
	}
	setAfter(e, t, n) {
		let r = this.#e.indexOf(e);
		if (r === -1) return this;
		let i = this.#e.indexOf(t), a = i !== -1 && i <= r ? r : r + 1;
		return this.insert(a, t, n);
	}
	first() {
		return this.entryAt(0);
	}
	last() {
		return this.entryAt(-1);
	}
	clear() {
		return this.#e = [], super.clear();
	}
	delete(e) {
		let t = super.delete(e);
		return t && this.#e.splice(this.#e.indexOf(e), 1), t;
	}
	deleteAt(e) {
		let t = this.keyAt(e);
		return t !== void 0 && this.delete(t);
	}
	at(e) {
		let t = de(this.#e, e);
		if (t !== void 0) return this.get(t);
	}
	entryAt(e) {
		let t = de(this.#e, e);
		if (t !== void 0) return [t, this.get(t)];
	}
	indexOf(e) {
		return this.#e.indexOf(e);
	}
	keyAt(e) {
		return de(this.#e, e);
	}
	from(e, t) {
		let n = this.indexOf(e);
		if (n === -1) return;
		let r = n + t;
		return r < 0 && (r = 0), r >= this.size && (r = this.size - 1), this.at(r);
	}
	keyFrom(e, t) {
		let n = this.indexOf(e);
		if (n === -1) return;
		let r = n + t;
		return r < 0 && (r = 0), r >= this.size && (r = this.size - 1), this.keyAt(r);
	}
	find(e, t) {
		let n = 0;
		for (let r of this) {
			if (Reflect.apply(e, t, [
				r,
				n,
				this
			])) return r;
			n++;
		}
	}
	findIndex(e, t) {
		let n = 0;
		for (let r of this) {
			if (Reflect.apply(e, t, [
				r,
				n,
				this
			])) return n;
			n++;
		}
		return -1;
	}
	filter(t, n) {
		let r = [], i = 0;
		for (let e of this) Reflect.apply(t, n, [
			e,
			i,
			this
		]) && r.push(e), i++;
		return new e(r);
	}
	map(t, n) {
		let r = [], i = 0;
		for (let e of this) r.push([e[0], Reflect.apply(t, n, [
			e,
			i,
			this
		])]), i++;
		return new e(r);
	}
	reduce(...e) {
		let [t, n] = e, r = e.length > 1;
		if (!r && this.size === 0) throw TypeError("Reduce of empty OrderedDict with no initial value");
		let i = 0, a = n;
		for (let e of this) a = i === 0 && !r ? e : Reflect.apply(t, this, [
			a,
			e,
			i,
			this
		]), i++;
		return a;
	}
	reduceRight(...e) {
		let [t, n] = e, r = e.length > 1;
		if (!r && this.size === 0) throw TypeError("Reduce of empty OrderedDict with no initial value");
		let i = n;
		for (let e = this.size - 1; e >= 0; e--) {
			let n = this.entryAt(e);
			i = e === this.size - 1 && !r ? n : Reflect.apply(t, this, [
				i,
				n,
				e,
				this
			]);
		}
		return i;
	}
	sort(e) {
		if (typeof e != "function") throw TypeError("OrderedDict.sort requires a compare function");
		let t = [...this.entries()].sort(e);
		this.clear();
		for (let [e, n] of t) this.set(e, n);
		return this;
	}
	toSorted(t) {
		if (typeof t != "function") throw TypeError("OrderedDict.toSorted requires a compare function");
		let n = [...this.entries()].sort(t);
		return new e(n);
	}
	toReversed() {
		let t = new e();
		for (let e = this.size - 1; e >= 0; e--) {
			let n = this.keyAt(e), r = this.get(n);
			t.set(n, r);
		}
		return t;
	}
	toSpliced(...t) {
		let n = [...this.entries()];
		return n.splice(...t), new e(n);
	}
	slice(t, n) {
		let r = new e();
		for (let e of this.#e.slice(t, n)) r.set(e, this.get(e));
		return r;
	}
	every(e, t) {
		let n = 0;
		for (let r of this) {
			if (!Reflect.apply(e, t, [
				r,
				n,
				this
			])) return !1;
			n++;
		}
		return !0;
	}
	some(e, t) {
		let n = 0;
		for (let r of this) {
			if (Reflect.apply(e, t, [
				r,
				n,
				this
			])) return !0;
			n++;
		}
		return !1;
	}
};
function de(e, t) {
	if ("at" in Array.prototype) return Array.prototype.at.call(e, t);
	let n = fe(e, t);
	return n === -1 ? void 0 : e[n];
}
z(de, "at");
function fe(e, t) {
	let n = e.length, r = pe(t), i = r >= 0 ? r : n + r;
	return i < 0 || i >= n ? -1 : i;
}
z(fe, "toSafeIndex");
function pe(e) {
	return e !== e || e === 0 ? 0 : Math.trunc(e);
}
z(pe, "toSafeInteger");
// @__NO_SIDE_EFFECTS__
function me(e) {
	let t = e + "CollectionProvider", [n, r] = /* @__PURE__ */ L(t), [i, a] = n(t);
	i.displayName = e + "CollectionStableContextProvider";
	let [c, l] = n(t);
	c.displayName = e + "CollectionStatefulContextProvider";
	let u = /* @__PURE__ */ z(({ state: e, ...t }) => e ? /* @__PURE__ */ (0, s.jsx)(f, {
		...t,
		state: e
	}) : /* @__PURE__ */ (0, s.jsx)(d, { ...t }), "CollectionProvider");
	u.displayName = t;
	let d = /* @__PURE__ */ z((e) => {
		let t = b();
		return /* @__PURE__ */ (0, s.jsx)(f, {
			...e,
			state: t
		});
	}, "CollectionInit");
	d.displayName = e + "CollectionInit";
	let f = /* @__PURE__ */ z((e) => {
		let { scope: t, children: n, state: r } = e, a = o.useRef(null), [l, u] = o.useState(null), d = v(a, u), [f, p] = r, m = o.useRef(new ue()), h = o.useCallback(() => {
			let e = m.current;
			return _e(e) || e.sort(ve), e;
		}, []);
		return o.useEffect(() => {
			if (!l) return;
			let e = ye(() => {
				p((e) => {
					let t = e.toSorted(ve);
					return t.some(([t], n) => e.keyAt(n) !== t) ? t : e;
				});
			});
			return e.observe(l, {
				childList: !0,
				subtree: !0
			}), () => {
				e.disconnect();
			};
		}, [l, p]), /* @__PURE__ */ (0, s.jsx)(i, {
			scope: t,
			collectionElementRef: d,
			collectionElementRefObject: a,
			getCollection: h,
			setCollection: p,
			registryRef: m,
			children: /* @__PURE__ */ (0, s.jsx)(c, {
				scope: t,
				collectionElement: l,
				collection: f,
				children: n
			})
		});
	}, "CollectionProviderImpl");
	f.displayName = e + "CollectionProviderImpl";
	let p = e + "CollectionSlot", m = /* @__PURE__ */ x(p), h = o.forwardRef((e, t) => {
		let { scope: n, children: r } = e, i = v(t, a(p, n).collectionElementRef);
		return /* @__PURE__ */ (0, s.jsx)(m, {
			ref: i,
			children: r
		});
	});
	h.displayName = p;
	let g = e + "CollectionItemSlot", _ = /* @__PURE__ */ x(g), y = o.forwardRef((e, t) => {
		let { scope: n, children: r, ...i } = e, c = o.useRef(null), { setCollection: l, registryRef: u } = a(g, n), d = o.useRef(i);
		he(d.current, i) || (d.current = i);
		let f = d.current, p = v(t, o.useCallback((e) => {
			let t = u.current;
			e ? t.set(e, {
				...d.current,
				element: e
			}) : c.current && t.delete(c.current);
		}, [u]), c);
		R(() => {
			let e = c.current, t = u.current;
			e && t.has(e) && t.set(e, {
				...f,
				element: e
			});
		}, [f, u]);
		let m = o.useRef(null);
		return o.useEffect(() => {
			let e = c.current, t = m.current;
			((t?.element ?? null) !== e || e && t?.itemData !== f) && (m.current = e ? {
				element: e,
				itemData: f
			} : null, l((n) => {
				let r = new ue(n);
				return t && t.element !== e && r.delete(t.element), e && r.set(e, {
					...f,
					element: e
				}), r.sort(ve);
			}));
		}), o.useEffect(() => () => {
			let e = m.current;
			m.current = null, e && l((t) => {
				if (!t.has(e.element)) return t;
				let n = new ue(t);
				return n.delete(e.element), n;
			});
		}, [l]), /* @__PURE__ */ (0, s.jsx)(_, {
			"data-radix-collection-item": "",
			ref: p,
			children: r
		});
	});
	y.displayName = g;
	function b() {
		return o.useState(new ue());
	}
	z(b, "useInitCollection");
	function S(t) {
		let { collection: n } = l(e + "CollectionConsumer", t);
		return n;
	}
	z(S, "useCollection");
	function C(t) {
		let { getCollection: n } = a(e + "CollectionConsumer", t);
		return n;
	}
	return z(C, "useGetCollection"), [{
		Provider: u,
		Slot: h,
		ItemSlot: y
	}, {
		createCollectionScope: r,
		useCollection: S,
		useGetCollection: C,
		useInitCollection: b
	}];
}
z(me, "createCollection");
function he(e, t) {
	if (e === t) return !0;
	if (typeof e != "object" || typeof t != "object" || e == null || t == null) return !1;
	let n = Object.keys(e), r = Object.keys(t);
	if (n.length !== r.length) return !1;
	for (let r of n) if (!Object.prototype.hasOwnProperty.call(t, r) || e[r] !== t[r]) return !1;
	return !0;
}
z(he, "shallowEqual");
function ge(e, t) {
	return !!(t.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_PRECEDING);
}
z(ge, "isElementPreceding");
function _e(e) {
	let t;
	for (let n of e.keys()) {
		if (t) {
			let e = t.compareDocumentPosition(n);
			if (!(e & Node.DOCUMENT_POSITION_DISCONNECTED) && e & Node.DOCUMENT_POSITION_PRECEDING) return !1;
		}
		t = n;
	}
	return !0;
}
z(_e, "isInDocumentOrder");
function ve(e, t) {
	return !e[1].element || !t[1].element ? 0 : ge(e[1].element, t[1].element) ? -1 : 1;
}
z(ve, "sortByDocumentPosition");
function ye(e) {
	return new MutationObserver((t) => {
		for (let n of t) if (n.type === "childList") {
			e();
			return;
		}
	});
}
z(ye, "getChildListObserver");
// node_modules/@radix-ui/primitive/dist/index.mjs
var be = Object.defineProperty, xe = (e, t) => be(e, "name", {
	value: t,
	configurable: !0
}), Se = !!(typeof window < "u" && window.document && window.document.createElement);
function B(e, t, { checkForDefaultPrevented: n = !0 } = {}) {
	return /* @__PURE__ */ xe(function(r) {
		if (e?.(r), n === !1 || !r || !r.defaultPrevented) return t?.(r);
	}, "handleEvent");
}
xe(B, "composeEventHandlers");
function Ce(e) {
	if (!Se) throw Error("Cannot access window outside of the DOM");
	return e?.ownerDocument?.defaultView ?? window;
}
xe(Ce, "getOwnerWindow");
function we(e) {
	if (!Se) throw Error("Cannot access document outside of the DOM");
	return e?.ownerDocument ?? document;
}
xe(we, "getOwnerDocument");
function Te(e, t = !1) {
	let { activeElement: n } = we(e);
	if (!n?.nodeName) return null;
	if (Ee(n) && n.contentDocument) return Te(n.contentDocument.body, t);
	if (t) {
		let e = n.getAttribute("aria-activedescendant");
		if (e) {
			let t = we(n).getElementById(e);
			if (t) return t;
		}
	}
	return n;
}
xe(Te, "getActiveElement");
function Ee(e) {
	return e.tagName === "IFRAME";
}
xe(Ee, "isFrame");
// node_modules/@radix-ui/react-use-effect-event/dist/index.mjs
var De = Object.defineProperty, Oe = (e, t) => De(e, "name", {
	value: t,
	configurable: !0
}), ke = o.useEffectEvent, Ae = o.useInsertionEffect;
function je(e) {
	if (typeof ke == "function") return ke(e);
	let t = o.useRef(() => {
		throw Error("Cannot call an event handler while rendering.");
	});
	return typeof Ae == "function" ? Ae(() => {
		t.current = e;
	}) : R(() => {
		t.current = e;
	}), o.useMemo(() => ((...e) => t.current?.(...e)), []);
}
Oe(je, "useEffectEvent");
// node_modules/@radix-ui/react-use-controllable-state/dist/index.mjs
var Me = Object.defineProperty, Ne = (e, t) => Me(e, "name", {
	value: t,
	configurable: !0
}), Pe = o.useInsertionEffect || R;
function Fe({ prop: e, defaultProp: t, onChange: n = /* @__PURE__ */ Ne(() => {}, "onChange"), caller: r }) {
	let [i, a, s] = Ie({
		defaultProp: t,
		onChange: n
	}), c = e !== void 0;
	return [c ? e : i, o.useCallback((t) => {
		if (c) {
			let n = Le(t) ? t(e) : t;
			n !== e && s.current?.(n);
		} else a(t);
	}, [
		c,
		e,
		a,
		s
	])];
}
Ne(Fe, "useControllableState");
function Ie({ defaultProp: e, onChange: t }) {
	let [n, r] = o.useState(e), i = o.useRef(n), a = o.useRef(t);
	return Pe(() => {
		a.current = t;
	}, [t]), o.useEffect(() => {
		i.current !== n && (a.current?.(n), i.current = n);
	}, [n, i]), [
		n,
		r,
		a
	];
}
Ne(Ie, "useUncontrolledState");
function Le(e) {
	return typeof e == "function";
}
Ne(Le, "isFunction");
var Re = Symbol("RADIX:SYNC_STATE");
function ze(e, t, n, r) {
	let { prop: i, defaultProp: a, onChange: s, caller: c } = t, l = i !== void 0, u = je(s), d = [{
		...n,
		state: a
	}];
	r && d.push(r);
	let [f, p] = o.useReducer((t, n) => {
		if (n.type === Re) return {
			...t,
			state: n.state
		};
		let r = e(t, n);
		return l && !Object.is(r.state, t.state) && u(r.state), r;
	}, ...d), m = f.state, h = o.useRef(m);
	o.useEffect(() => {
		h.current !== m && (h.current = m, l || u(m));
	}, [
		m,
		h,
		l
	]);
	let g = o.useMemo(() => i === void 0 ? f : {
		...f,
		state: i
	}, [f, i]);
	return o.useEffect(() => {
		l && !Object.is(i, f.state) && p({
			type: Re,
			state: i
		});
	}, [
		i,
		f.state,
		l
	]), [g, p];
}
Ne(ze, "useControllableStateReducer");
// node_modules/@radix-ui/react-presence/dist/index.mjs
var Be = Object.defineProperty, V = (e, t) => Be(e, "name", {
	value: t,
	configurable: !0
});
function Ve(e, t) {
	return o.useReducer((e, n) => t[e][n] ?? e, e);
}
V(Ve, "useStateMachine");
var He = /* @__PURE__ */ V((e) => {
	let { present: t, children: n } = e, r = Ue(t), i = typeof n == "function" ? n({ present: r.isPresent }) : o.Children.only(n), a = Ge(r.ref, qe(i));
	return typeof n == "function" || r.isPresent ? o.cloneElement(i, { ref: a }) : null;
}, "Presence");
function Ue(e) {
	let [t, n] = o.useState(), r = o.useRef(null), i = o.useRef(e), a = o.useRef("none"), s = o.useRef(void 0), [c, l] = Ve(e ? "mounted" : "unmounted", {
		mounted: {
			UNMOUNT: "unmounted",
			ANIMATION_OUT: "unmountSuspended"
		},
		unmountSuspended: {
			MOUNT: "mounted",
			ANIMATION_END: "unmounted"
		},
		unmounted: { MOUNT: "mounted" }
	});
	return o.useEffect(() => {
		c === "mounted" ? (a.current = s.current ?? Ke(r.current), s.current = void 0) : a.current = "none";
	}, [c]), R(() => {
		let t = r.current, n = i.current;
		if (n !== e) {
			let r = a.current, o = Ke(t);
			e ? (s.current = o, l("MOUNT")) : o === "none" || t?.display === "none" ? l("UNMOUNT") : l(n && r !== o ? "ANIMATION_OUT" : "UNMOUNT"), i.current = e;
		}
	}, [e, l]), R(() => {
		if (t) {
			let e, n = t.ownerDocument.defaultView ?? window, o = /* @__PURE__ */ V((a) => {
				let o = Ke(r.current).includes(CSS.escape(a.animationName));
				if (a.target === t && o && (l("ANIMATION_END"), !i.current)) {
					let r = t.style.animationFillMode;
					t.style.animationFillMode = "forwards", e = n.setTimeout(() => {
						t.style.animationFillMode === "forwards" && (t.style.animationFillMode = r);
					});
				}
			}, "handleAnimationEnd"), s = /* @__PURE__ */ V((e) => {
				e.target === t && (a.current = Ke(r.current));
			}, "handleAnimationStart");
			return t.addEventListener("animationstart", s), t.addEventListener("animationcancel", o), t.addEventListener("animationend", o), () => {
				n.clearTimeout(e), t.removeEventListener("animationstart", s), t.removeEventListener("animationcancel", o), t.removeEventListener("animationend", o);
			};
		}
		l("ANIMATION_END");
	}, [t, l]), {
		isPresent: ["mounted", "unmountSuspended"].includes(c),
		ref: o.useCallback((e) => {
			if (e) {
				let t = getComputedStyle(e);
				r.current = t, s.current = Ke(t);
			} else r.current = null;
			n(e);
		}, [])
	};
}
V(Ue, "usePresence");
function We(e, t) {
	if (typeof e == "function") return e(t);
	e != null && (e.current = t);
}
V(We, "setRef");
function Ge(...e) {
	let t = o.useRef(e);
	return t.current = e, o.useCallback((e) => {
		let n = t.current, r = !1, i = n.map((t) => {
			let n = We(t, e);
			return !r && typeof n == "function" && (r = !0), n;
		});
		if (r) return () => {
			for (let e = 0; e < i.length; e++) {
				let t = i[e];
				typeof t == "function" ? t() : We(n[e], null);
			}
		};
	}, []);
}
V(Ge, "useStableComposedRefs");
function Ke(e) {
	return e?.animationName || "none";
}
V(Ke, "getAnimationName");
function qe(e) {
	let t = Object.getOwnPropertyDescriptor(e.props, "ref")?.get, n = t && "isReactWarning" in t && t.isReactWarning;
	return n ? e.ref : (t = Object.getOwnPropertyDescriptor(e, "ref")?.get, n = t && "isReactWarning" in t && t.isReactWarning, n ? e.props.ref : e.props.ref || e.ref);
}
V(qe, "getElementRef");
// node_modules/@radix-ui/react-id/dist/index.mjs
var Je = Object.defineProperty, Ye = (e, t) => Je(e, "name", {
	value: t,
	configurable: !0
}), Xe = o.useId || (() => void 0), Ze = 0;
function Qe(e) {
	let [t, n] = o.useState(Xe());
	return R(() => {
		e || n((e) => e ?? String(Ze++));
	}, [e]), e || (t ? `radix-${t}` : "");
}
Ye(Qe, "useId");
// node_modules/@radix-ui/react-direction/dist/index.mjs
var $e = Object.defineProperty, et = (e, t) => $e(e, "name", {
	value: t,
	configurable: !0
}), tt = {
	LTR: "ltr",
	RTL: "rtl"
}, nt = o.createContext(void 0);
function rt(e) {
	let t = o.useContext(nt);
	return e || t || tt.LTR;
}
et(rt, "useDirection");
// node_modules/@radix-ui/react-use-callback-ref/dist/index.mjs
var it = Object.defineProperty, at = (e, t) => it(e, "name", {
	value: t,
	configurable: !0
}), ot = o.useInsertionEffect;
function st(e) {
	let t = o.useRef(e);
	return typeof ot == "function" ? ot(() => {
		t.current = e;
	}) : R(() => {
		t.current = e;
	}), o.useMemo(() => ((...e) => t.current?.(...e)), []);
}
at(st, "useCallbackRef");
// node_modules/@radix-ui/react-dismissable-layer/dist/index.mjs
var ct = Object.defineProperty, H = (e, t) => ct(e, "name", {
	value: t,
	configurable: !0
}), lt = "dismissableLayer.update", ut = "dismissableLayer.pointerDownOutside", dt = "dismissableLayer.focusOutside", ft, pt = o.createContext({
	layers: /* @__PURE__ */ new Set(),
	layersWithOutsidePointerEventsDisabled: /* @__PURE__ */ new Set(),
	branches: /* @__PURE__ */ new Set(),
	dismissableSurfaces: /* @__PURE__ */ new Set()
}), mt = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ H(function(e, t) {
	let { disableOutsidePointerEvents: n = !1, deferPointerDownOutside: r = !1, onEscapeKeyDown: i, onPointerDownOutside: a, onFocusOutside: c, onInteractOutside: l, onDismiss: u, ...d } = e, f = o.useContext(pt), [p, m] = o.useState(null), h = p?.ownerDocument ?? globalThis?.document, [, g] = o.useState({}), _ = v(t, m), y = Array.from(f.layers), [b] = [...f.layersWithOutsidePointerEventsDisabled].slice(-1), x = b ? y.indexOf(b) : -1, S = p ? y.indexOf(p) : -1, C = f.layersWithOutsidePointerEventsDisabled.size > 0, w = S >= x, T = o.useRef(!1), E = _t((e) => {
		a?.(e), l?.(e), e.defaultPrevented || u?.();
	}, {
		ownerDocument: h,
		deferPointerDownOutside: r,
		isDeferredPointerDownOutsideRef: T,
		dismissableSurfaces: f.dismissableSurfaces,
		shouldHandlePointerDownOutside: o.useCallback((e) => {
			if (!(e instanceof Node)) return !1;
			let t = [...f.branches].some((t) => t.contains(e));
			return w && !t;
		}, [f.branches, w])
	}), D = vt((e) => {
		if (r && T.current) return;
		let t = e.target;
		[...f.branches].some((e) => e.contains(t)) || (c?.(e), l?.(e), e.defaultPrevented || u?.());
	}, h), O = p ? S === y.length - 1 : !1, k = st((e) => {
		e.key === "Escape" && (i?.(e), !e.defaultPrevented && u && (e.preventDefault(), u()));
	});
	return o.useEffect(() => {
		if (O) return h.addEventListener("keydown", k, { capture: !0 }), () => h.removeEventListener("keydown", k, { capture: !0 });
	}, [
		h,
		O,
		k
	]), o.useEffect(() => {
		if (p) return n && (f.layersWithOutsidePointerEventsDisabled.size === 0 && (ft = h.body.style.pointerEvents, h.body.style.pointerEvents = "none"), f.layersWithOutsidePointerEventsDisabled.add(p)), f.layers.add(p), yt(), () => {
			n && (f.layersWithOutsidePointerEventsDisabled.delete(p), f.layersWithOutsidePointerEventsDisabled.size === 0 && (h.body.style.pointerEvents = ft));
		};
	}, [
		p,
		h,
		n,
		f
	]), o.useEffect(() => () => {
		p && (f.layers.delete(p), f.layersWithOutsidePointerEventsDisabled.delete(p), yt());
	}, [p, f]), o.useEffect(() => {
		let e = /* @__PURE__ */ H(() => g({}), "handleUpdate");
		return document.addEventListener(lt, e), () => document.removeEventListener(lt, e);
	}, []), /* @__PURE__ */ (0, s.jsx)(F.div, {
		...d,
		ref: _,
		style: {
			pointerEvents: C ? w ? "auto" : "none" : void 0,
			...e.style
		},
		onFocusCapture: B(e.onFocusCapture, D.onFocusCapture),
		onBlurCapture: B(e.onBlurCapture, D.onBlurCapture),
		onPointerDownCapture: B(e.onPointerDownCapture, E.onPointerDownCapture)
	});
}, "DismissableLayer"));
function ht() {
	let e = o.useContext(pt), [t, n] = o.useState(null);
	return o.useEffect(() => {
		if (t) return e.dismissableSurfaces.add(t), () => {
			e.dismissableSurfaces.delete(t);
		};
	}, [t, e.dismissableSurfaces]), n;
}
H(ht, "useDismissableLayerSurface");
var gt = /* @__PURE__ */ H(() => !0, "IS_TRUE");
function _t(e, t) {
	let { ownerDocument: n = globalThis?.document, deferPointerDownOutside: r = !1, isDeferredPointerDownOutsideRef: i, dismissableSurfaces: a, shouldHandlePointerDownOutside: s = gt } = t, c = st(e), l = o.useRef(!1), u = o.useRef(!1), d = o.useRef(/* @__PURE__ */ new Map()), f = o.useRef(() => {});
	return o.useEffect(() => {
		function e() {
			u.current = !1, i.current = !1, d.current.clear();
		}
		H(e, "resetOutsideInteraction");
		function t() {
			return Array.from(d.current.values()).some(Boolean);
		}
		H(t, "isOutsideInteractionIntercepted");
		function o(e) {
			if (!u.current) return;
			let t = e.target;
			t instanceof Node && [...a].some((e) => e.contains(t)) || d.current.set(e.type, !0), e.type === "click" && window.setTimeout(() => {
				u.current && f.current();
			}, 0);
		}
		H(o, "handleInteractionCapture");
		function p(e) {
			u.current && d.current.set(e.type, !1);
		}
		H(p, "handleInteractionBubble");
		let m = /* @__PURE__ */ H((a) => {
			if (a.target && !l.current) {
				let o = function() {
					n.removeEventListener("click", f.current);
					let r = t();
					e(), r || bt(ut, c, p, { discrete: !0 });
				};
				if (H(o, "handleAndDispatchPointerDownOutsideEvent"), !s(a.target)) {
					n.removeEventListener("click", f.current), e(), l.current = !1;
					return;
				}
				let p = { originalEvent: a };
				u.current = !0, i.current = r && a.button === 0, d.current.clear(), !r || a.button !== 0 ? o() : (n.removeEventListener("click", f.current), f.current = o, n.addEventListener("click", f.current, { once: !0 }));
			} else n.removeEventListener("click", f.current), e();
			l.current = !1;
		}, "handlePointerDown"), h = [
			"pointerup",
			"mousedown",
			"mouseup",
			"touchstart",
			"touchend",
			"click"
		];
		for (let e of h) n.addEventListener(e, o, !0), n.addEventListener(e, p);
		let g = window.setTimeout(() => {
			n.addEventListener("pointerdown", m);
		}, 0);
		return () => {
			window.clearTimeout(g), n.removeEventListener("pointerdown", m), n.removeEventListener("click", f.current);
			for (let e of h) n.removeEventListener(e, o, !0), n.removeEventListener(e, p);
		};
	}, [
		n,
		c,
		r,
		i,
		a,
		s
	]), { onPointerDownCapture: /* @__PURE__ */ H(() => l.current = !0, "onPointerDownCapture") };
}
H(_t, "usePointerDownOutside");
function vt(e, t = globalThis?.document) {
	let n = st(e), r = o.useRef(!1);
	return o.useEffect(() => {
		let e = /* @__PURE__ */ H((e) => {
			e.target && !r.current && bt(dt, n, { originalEvent: e }, { discrete: !1 });
		}, "handleFocus");
		return t.addEventListener("focusin", e), () => t.removeEventListener("focusin", e);
	}, [t, n]), {
		onFocusCapture: /* @__PURE__ */ H(() => r.current = !0, "onFocusCapture"),
		onBlurCapture: /* @__PURE__ */ H(() => r.current = !1, "onBlurCapture")
	};
}
H(vt, "useFocusOutside");
function yt() {
	let e = new CustomEvent(lt);
	document.dispatchEvent(e);
}
H(yt, "dispatchUpdate");
function bt(e, t, n, { discrete: r }) {
	let i = n.originalEvent.target, a = new CustomEvent(e, {
		bubbles: !1,
		cancelable: !0,
		detail: n
	});
	t && i.addEventListener(e, t, { once: !0 }), r ? re(i, a) : i.dispatchEvent(a);
}
H(bt, "handleAndDispatchCustomEvent");
// node_modules/@radix-ui/react-focus-scope/dist/index.mjs
var xt = Object.defineProperty, U = (e, t) => xt(e, "name", {
	value: t,
	configurable: !0
}), St = "focusScope.autoFocusOnMount", Ct = "focusScope.autoFocusOnUnmount", wt = {
	bubbles: !1,
	cancelable: !0
}, Tt = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ U(function(e, t) {
	let { loop: n = !1, trapped: r = !1, branches: i, onMountAutoFocus: a, onUnmountAutoFocus: c, ...l } = e, [u, d] = o.useState(null), f = st(a), p = st(c), m = o.useRef(null), h = v(t, d), g = o.useRef(i);
	o.useEffect(() => {
		g.current = i;
	});
	let _ = o.useCallback((e) => e ? u?.contains(e) ? !0 : !!g.current?.some((t) => t.contains(e)) : !1, [u]), y = o.useRef({
		paused: !1,
		pause() {
			this.paused = !0;
		},
		resume() {
			this.paused = !1;
		}
	}).current;
	o.useEffect(() => {
		if (r) {
			let e = function(e) {
				if (y.paused || !u) return;
				let t = e.target;
				_(t) ? m.current = t : W(m.current, { select: !0 });
			}, t = function(e) {
				if (y.paused || !u) return;
				let t = e.relatedTarget;
				t !== null && (_(t) || W(m.current, { select: !0 }));
			}, n = function(e) {
				if (document.activeElement === document.body) for (let t of e) t.removedNodes.length > 0 && W(u);
			};
			U(e, "handleFocusIn"), U(t, "handleFocusOut"), U(n, "handleMutations"), document.addEventListener("focusin", e), document.addEventListener("focusout", t);
			let r = new MutationObserver(n);
			return u && r.observe(u, {
				childList: !0,
				subtree: !0
			}), () => {
				document.removeEventListener("focusin", e), document.removeEventListener("focusout", t), r.disconnect();
			};
		}
	}, [
		r,
		u,
		y.paused,
		_
	]), o.useEffect(() => {
		if (u) {
			It.add(y);
			let e = document.activeElement;
			if (!u.contains(e)) {
				let t = new CustomEvent(St, wt);
				u.addEventListener(St, f), u.dispatchEvent(t), t.defaultPrevented || (At(zt(Mt(u)), { select: !0 }), document.activeElement === e && W(u));
			}
			return () => {
				u.removeEventListener(St, f);
				let t = u.ownerDocument, n = CustomEvent;
				setTimeout(() => {
					let r = new n(Ct, wt);
					u.addEventListener(Ct, p), u.dispatchEvent(r), r.defaultPrevented || W(e ?? t.body, { select: !0 }), u.removeEventListener(Ct, p), It.remove(y);
				}, 0);
			};
		}
	}, [
		u,
		f,
		p,
		y
	]);
	let b = o.useCallback((e) => {
		if (!n && !r || y.paused) return;
		let t = e.key === "Tab" && !e.altKey && !e.ctrlKey && !e.metaKey, i = document.activeElement;
		if (t && i) {
			let t = e.currentTarget, [r, a] = jt(t);
			r && a ? !e.shiftKey && i === a ? (e.preventDefault(), n && W(r, { select: !0 })) : e.shiftKey && i === r && (e.preventDefault(), n && W(a, { select: !0 })) : i === t && e.preventDefault();
		}
	}, [
		n,
		r,
		y.paused
	]);
	return /* @__PURE__ */ (0, s.jsx)(F.div, {
		tabIndex: -1,
		...l,
		ref: h,
		onKeyDown: b
	});
}, "FocusScope")), Et = o.createContext(null);
function Dt({ registry: e, children: t }) {
	return e ? /* @__PURE__ */ (0, s.jsx)(Et.Provider, {
		value: e,
		children: t
	}) : t;
}
U(Dt, "FocusScopeBranchProvider");
function Ot() {
	let [e, t] = o.useState([]);
	return {
		nodes: e,
		registry: o.useMemo(() => ({
			add: /* @__PURE__ */ U((e) => t((t) => t.includes(e) ? t : [...t, e]), "add"),
			remove: /* @__PURE__ */ U((e) => t((t) => t.filter((t) => t !== e)), "remove")
		}), [])
	};
}
U(Ot, "useFocusScopeBranchRegistry");
function kt(e) {
	let t = o.useContext(Et);
	o.useEffect(() => {
		if (e && t) return t.add(e), () => t.remove(e);
	}, [e, t]);
}
U(kt, "useFocusScopeBranch");
function At(e, { select: t = !1 } = {}) {
	let n = document.activeElement;
	for (let r of e) if (W(r, { select: t }), document.activeElement !== n) return;
}
U(At, "focusFirst");
function jt(e) {
	let t = Mt(e);
	return [Nt(t, e), Nt(t.reverse(), e)];
}
U(jt, "getTabbableEdges");
function Mt(e) {
	let t = [], n = e.ownerDocument.createTreeWalker(e, NodeFilter.SHOW_ELEMENT, { acceptNode: /* @__PURE__ */ U((e) => {
		let t = e.tagName === "INPUT" && e.type === "hidden";
		return e.disabled || e.hidden || t ? NodeFilter.FILTER_SKIP : e.tabIndex >= 0 ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
	}, "acceptNode") });
	for (; n.nextNode();) t.push(n.currentNode);
	return t;
}
U(Mt, "getTabbableCandidates");
function Nt(e, t) {
	let n = typeof t.checkVisibility == "function" && t.checkVisibility({ checkVisibilityCSS: !0 });
	for (let r of e) if (!(n ? !r.checkVisibility({ checkVisibilityCSS: !0 }) : Pt(r, { upTo: t }))) return r;
}
U(Nt, "findVisible");
function Pt(e, { upTo: t }) {
	if (getComputedStyle(e).visibility === "hidden") return !0;
	for (; e;) {
		if (t !== void 0 && e === t) return !1;
		if (getComputedStyle(e).display === "none") return !0;
		e = e.parentElement;
	}
	return !1;
}
U(Pt, "isHidden");
function Ft(e) {
	return e.tagName === "INPUT" && typeof e.select == "function";
}
U(Ft, "isSelectableInput");
function W(e, { select: t = !1 } = {}) {
	if (e && e.focus) {
		let n = (e.ownerDocument ?? document).activeElement;
		e.focus({ preventScroll: !0 }), e !== n && Ft(e) && t && e.select();
	}
}
U(W, "focus");
var It = Lt();
function Lt() {
	let e = [];
	return {
		add(t) {
			let n = e[0];
			t !== n && n?.pause(), e = Rt(e, t), e.unshift(t);
		},
		remove(t) {
			e = Rt(e, t), e[0]?.resume();
		}
	};
}
U(Lt, "createFocusScopesStack");
function Rt(e, t) {
	let n = [...e], r = n.indexOf(t);
	return r !== -1 && n.splice(r, 1), n;
}
U(Rt, "arrayRemove");
function zt(e) {
	return e.filter((e) => e.tagName !== "A");
}
U(zt, "removeLinks");
// node_modules/@radix-ui/react-portal/dist/index.mjs
var Bt = Object.defineProperty, Vt = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ ((e, t) => Bt(e, "name", {
	value: t,
	configurable: !0
}))(function(e, t) {
	let { container: n, ...r } = e, [i, a] = o.useState(!1);
	R(() => a(!0), []);
	let c = n || i && globalThis?.document?.body;
	return c ? u.createPortal(/* @__PURE__ */ (0, s.jsx)(F.div, {
		...r,
		ref: t
	}), c) : null;
}, "Portal")), Ht = Object.defineProperty, Ut = (e, t) => Ht(e, "name", {
	value: t,
	configurable: !0
}), Wt = 0, Gt = null;
function Kt(e) {
	return qt(), e.children;
}
Ut(Kt, "FocusGuards");
function qt() {
	o.useEffect(() => {
		Gt ||= {
			start: Jt(),
			end: Jt()
		};
		let { start: e, end: t } = Gt;
		return document.body.firstElementChild !== e && document.body.insertAdjacentElement("afterbegin", e), document.body.lastElementChild !== t && document.body.insertAdjacentElement("beforeend", t), Wt++, () => {
			Wt === 1 && (Gt?.start.remove(), Gt?.end.remove(), Gt = null), Wt = Math.max(0, Wt - 1);
		};
	}, []);
}
Ut(qt, "useFocusGuards");
function Jt() {
	let e = document.createElement("span");
	return e.setAttribute("data-radix-focus-guard", ""), e.tabIndex = 0, e.style.outline = "none", e.style.opacity = "0", e.style.position = "fixed", e.style.pointerEvents = "none", e;
}
Ut(Jt, "createFocusGuard");
// node_modules/tslib/tslib.es6.mjs
var G = function() {
	return G = Object.assign || function(e) {
		for (var t, n = 1, r = arguments.length; n < r; n++) for (var i in t = arguments[n], t) Object.prototype.hasOwnProperty.call(t, i) && (e[i] = t[i]);
		return e;
	}, G.apply(this, arguments);
};
function Yt(e, t) {
	var n = {};
	for (var r in e) Object.prototype.hasOwnProperty.call(e, r) && t.indexOf(r) < 0 && (n[r] = e[r]);
	if (e != null && typeof Object.getOwnPropertySymbols == "function") for (var i = 0, r = Object.getOwnPropertySymbols(e); i < r.length; i++) t.indexOf(r[i]) < 0 && Object.prototype.propertyIsEnumerable.call(e, r[i]) && (n[r[i]] = e[r[i]]);
	return n;
}
function Xt(e, t, n) {
	if (n || arguments.length === 2) for (var r = 0, i = t.length, a; r < i; r++) (a || !(r in t)) && (a ||= Array.prototype.slice.call(t, 0, r), a[r] = t[r]);
	return e.concat(a || Array.prototype.slice.call(t));
}
// node_modules/react-remove-scroll-bar/dist/es2015/constants.js
var Zt = "right-scroll-bar-position", Qt = "width-before-scroll-bar", $t = "with-scroll-bars-hidden", en = "--removed-body-scroll-bar-size";
// node_modules/use-callback-ref/dist/es2015/assignRef.js
function tn(e, t) {
	return typeof e == "function" ? e(t) : e && (e.current = t), e;
}
// node_modules/use-callback-ref/dist/es2015/useRef.js
function nn(e, t) {
	var n = (0, o.useState)(function() {
		return {
			value: e,
			callback: t,
			facade: {
				get current() {
					return n.value;
				},
				set current(e) {
					var t = n.value;
					t !== e && (n.value = e, n.callback(e, t));
				}
			}
		};
	})[0];
	return n.callback = t, n.facade;
}
// node_modules/use-callback-ref/dist/es2015/useMergeRef.js
var rn = typeof window < "u" ? o.useLayoutEffect : o.useEffect, an = /* @__PURE__ */ new WeakMap();
function on(e, t) {
	var n = nn(t || null, function(t) {
		return e.forEach(function(e) {
			return tn(e, t);
		});
	});
	return rn(function() {
		var t = an.get(n);
		if (t) {
			var r = new Set(t), i = new Set(e), a = n.current;
			r.forEach(function(e) {
				i.has(e) || tn(e, null);
			}), i.forEach(function(e) {
				r.has(e) || tn(e, a);
			});
		}
		an.set(n, e);
	}, [e]), n;
}
// node_modules/use-sidecar/dist/es2015/medium.js
function sn(e) {
	return e;
}
function cn(e, t) {
	t === void 0 && (t = sn);
	var n = [], r = !1;
	return {
		read: function() {
			if (r) throw Error("Sidecar: could not `read` from an `assigned` medium. `read` could be used only with `useMedium`.");
			return n.length ? n[n.length - 1] : e;
		},
		useMedium: function(e) {
			var i = t(e, r);
			return n.push(i), function() {
				n = n.filter(function(e) {
					return e !== i;
				});
			};
		},
		assignSyncMedium: function(e) {
			for (r = !0; n.length;) {
				var t = n;
				n = [], t.forEach(e);
			}
			n = {
				push: function(t) {
					return e(t);
				},
				filter: function() {
					return n;
				}
			};
		},
		assignMedium: function(e) {
			r = !0;
			var t = [];
			if (n.length) {
				var i = n;
				n = [], i.forEach(e), t = n;
			}
			var a = function() {
				var n = t;
				t = [], n.forEach(e);
			}, o = function() {
				return Promise.resolve().then(a);
			};
			o(), n = {
				push: function(e) {
					t.push(e), o();
				},
				filter: function(e) {
					return t = t.filter(e), n;
				}
			};
		}
	};
}
function ln(e) {
	e === void 0 && (e = {});
	var t = cn(null);
	return t.options = G({
		async: !0,
		ssr: !1
	}, e), t;
}
// node_modules/use-sidecar/dist/es2015/exports.js
var un = function(e) {
	var t = e.sideCar, n = Yt(e, ["sideCar"]);
	if (!t) throw Error("Sidecar: please provide `sideCar` property to import the right car");
	var r = t.read();
	if (!r) throw Error("Sidecar medium not found");
	return o.createElement(r, G({}, n));
};
un.isSideCarExport = !0;
function dn(e, t) {
	return e.useMedium(t), un;
}
// node_modules/react-remove-scroll/dist/es2015/medium.js
var fn = ln(), pn = function() {}, mn = o.forwardRef(function(e, t) {
	var n = o.useRef(null), r = o.useState({
		onScrollCapture: pn,
		onWheelCapture: pn,
		onTouchMoveCapture: pn
	}), i = r[0], a = r[1], s = e.forwardProps, c = e.children, l = e.className, u = e.removeScrollBar, d = e.enabled, f = e.shards, p = e.sideCar, m = e.noRelative, h = e.noIsolation, g = e.inert, _ = e.allowPinchZoom, v = e.as, y = v === void 0 ? "div" : v, b = e.gapMode, x = Yt(e, [
		"forwardProps",
		"children",
		"className",
		"removeScrollBar",
		"enabled",
		"shards",
		"sideCar",
		"noRelative",
		"noIsolation",
		"inert",
		"allowPinchZoom",
		"as",
		"gapMode"
	]), S = p, C = on([n, t]), w = G(G({}, x), i);
	return o.createElement(o.Fragment, null, d && o.createElement(S, {
		sideCar: fn,
		removeScrollBar: u,
		shards: f,
		noRelative: m,
		noIsolation: h,
		inert: g,
		setCallbacks: a,
		allowPinchZoom: !!_,
		lockRef: n,
		gapMode: b
	}), s ? o.cloneElement(o.Children.only(c), G(G({}, w), { ref: C })) : o.createElement(y, G({}, w, {
		className: l,
		ref: C
	}), c));
});
mn.defaultProps = {
	enabled: !0,
	removeScrollBar: !0,
	inert: !1
}, mn.classNames = {
	fullWidth: Qt,
	zeroRight: Zt
};
// node_modules/get-nonce/dist/es2015/index.js
var hn = function() {
	if (typeof __webpack_nonce__ < "u") return __webpack_nonce__;
};
// node_modules/react-style-singleton/dist/es2015/singleton.js
function gn() {
	if (!document) return null;
	var e = document.createElement("style");
	e.type = "text/css";
	var t = hn();
	return t && e.setAttribute("nonce", t), e;
}
function _n(e, t) {
	e.styleSheet ? e.styleSheet.cssText = t : e.appendChild(document.createTextNode(t));
}
function vn(e) {
	(document.head || document.getElementsByTagName("head")[0]).appendChild(e);
}
var yn = function() {
	var e = 0, t = null;
	return {
		add: function(n) {
			e == 0 && (t = gn()) && (_n(t, n), vn(t)), e++;
		},
		remove: function() {
			e--, !e && t && (t.parentNode && t.parentNode.removeChild(t), t = null);
		}
	};
}, bn = function() {
	var e = yn();
	return function(t, n) {
		o.useEffect(function() {
			return e.add(t), function() {
				e.remove();
			};
		}, [t && n]);
	};
}, xn = function() {
	var e = bn();
	return function(t) {
		var n = t.styles, r = t.dynamic;
		return e(n, r), null;
	};
}, Sn = {
	left: 0,
	top: 0,
	right: 0,
	gap: 0
}, Cn = function(e) {
	return parseInt(e || "", 10) || 0;
}, wn = function(e) {
	var t = window.getComputedStyle(document.body), n = t[e === "padding" ? "paddingLeft" : "marginLeft"], r = t[e === "padding" ? "paddingTop" : "marginTop"], i = t[e === "padding" ? "paddingRight" : "marginRight"];
	return [
		Cn(n),
		Cn(r),
		Cn(i)
	];
}, Tn = function(e) {
	if (e === void 0 && (e = "margin"), typeof window > "u") return Sn;
	var t = wn(e), n = document.documentElement.clientWidth, r = window.innerWidth;
	return {
		left: t[0],
		top: t[1],
		right: t[2],
		gap: Math.max(0, r - n + t[2] - t[0])
	};
}, En = xn(), Dn = "data-scroll-locked", On = function(e, t, n, r) {
	var i = e.left, a = e.top, o = e.right, s = e.gap;
	return n === void 0 && (n = "margin"), `
  .${$t} {
   overflow: hidden ${r};
   padding-right: ${s}px ${r};
  }
  body[${Dn}] {
    overflow: hidden ${r};
    overscroll-behavior: contain;
    ${[
		t && `position: relative ${r};`,
		n === "margin" && `
    padding-left: ${i}px;
    padding-top: ${a}px;
    padding-right: ${o}px;
    margin-left:0;
    margin-top:0;
    margin-right: ${s}px ${r};
    `,
		n === "padding" && `padding-right: ${s}px ${r};`
	].filter(Boolean).join("")}
  }
  
  .${Zt} {
    right: ${s}px ${r};
  }
  
  .${Qt} {
    margin-right: ${s}px ${r};
  }
  
  .${Zt} .${Zt} {
    right: 0 ${r};
  }
  
  .${Qt} .${Qt} {
    margin-right: 0 ${r};
  }
  
  body[${Dn}] {
    ${en}: ${s}px;
  }
`;
}, kn = function() {
	var e = parseInt(document.body.getAttribute("data-scroll-locked") || "0", 10);
	return isFinite(e) ? e : 0;
}, An = function() {
	o.useEffect(function() {
		return document.body.setAttribute(Dn, (kn() + 1).toString()), function() {
			var e = kn() - 1;
			e <= 0 ? document.body.removeAttribute(Dn) : document.body.setAttribute(Dn, e.toString());
		};
	}, []);
}, jn = function(e) {
	var t = e.noRelative, n = e.noImportant, r = e.gapMode, i = r === void 0 ? "margin" : r;
	An();
	var a = o.useMemo(function() {
		return Tn(i);
	}, [i]);
	return o.createElement(En, { styles: On(a, !t, i, n ? "" : "!important") });
}, Mn = !1;
if (typeof window < "u") try {
	var Nn = Object.defineProperty({}, "passive", { get: function() {
		return Mn = !0, !0;
	} });
	window.addEventListener("test", Nn, Nn), window.removeEventListener("test", Nn, Nn);
} catch {
	Mn = !1;
}
var Pn = Mn ? { passive: !1 } : !1, Fn = function(e) {
	return e.tagName === "TEXTAREA";
}, In = function(e, t) {
	if (!(e instanceof Element)) return !1;
	var n = window.getComputedStyle(e);
	return n[t] !== "hidden" && !(n.overflowY === n.overflowX && !Fn(e) && n[t] === "visible");
}, Ln = function(e) {
	return In(e, "overflowY");
}, Rn = function(e) {
	return In(e, "overflowX");
}, zn = function(e, t) {
	var n = t.ownerDocument, r = t;
	do {
		if (typeof ShadowRoot < "u" && r instanceof ShadowRoot && (r = r.host), Hn(e, r)) {
			var i = Un(e, r);
			if (i[1] > i[2]) return !0;
		}
		r = r.parentNode;
	} while (r && r !== n.body);
	return !1;
}, Bn = function(e) {
	return [
		e.scrollTop,
		e.scrollHeight,
		e.clientHeight
	];
}, Vn = function(e) {
	return [
		e.scrollLeft,
		e.scrollWidth,
		e.clientWidth
	];
}, Hn = function(e, t) {
	return e === "v" ? Ln(t) : Rn(t);
}, Un = function(e, t) {
	return e === "v" ? Bn(t) : Vn(t);
}, Wn = function(e, t) {
	return e === "h" && t === "rtl" ? -1 : 1;
}, Gn = function(e, t, n, r, i) {
	var a = Wn(e, window.getComputedStyle(t).direction), o = a * r, s = n.target, c = t.contains(s), l = !1, u = o > 0, d = 0, f = 0;
	do {
		if (!s) break;
		var p = Un(e, s), m = p[0], h = p[1] - p[2] - a * m;
		(m || h) && Hn(e, s) && (d += h, f += m);
		var g = s.parentNode;
		s = g && g.nodeType === Node.DOCUMENT_FRAGMENT_NODE ? g.host : g;
	} while (!c && s !== document.body || c && (t.contains(s) || t === s));
	return (u && (i && Math.abs(d) < 1 || !i && o > d) || !u && (i && Math.abs(f) < 1 || !i && -o > f)) && (l = !0), l;
}, Kn = function(e) {
	return "changedTouches" in e ? [e.changedTouches[0].clientX, e.changedTouches[0].clientY] : [0, 0];
}, qn = function(e) {
	return [e.deltaX, e.deltaY];
}, Jn = function(e) {
	return e && "current" in e ? e.current : e;
}, Yn = function(e, t) {
	return e[0] === t[0] && e[1] === t[1];
}, Xn = function(e) {
	return `
  .block-interactivity-${e} {pointer-events: none;}
  .allow-interactivity-${e} {pointer-events: all;}
`;
}, Zn = 0, Qn = [];
function $n(e) {
	var t = o.useRef([]), n = o.useRef([0, 0]), r = o.useRef(), i = o.useState(Zn++)[0], a = o.useState(xn)[0], s = o.useRef(e);
	o.useEffect(function() {
		s.current = e;
	}, [e]), o.useEffect(function() {
		if (e.inert) {
			document.body.classList.add(`block-interactivity-${i}`);
			var t = Xt([e.lockRef.current], (e.shards || []).map(Jn), !0).filter(Boolean);
			return t.forEach(function(e) {
				return e.classList.add(`allow-interactivity-${i}`);
			}), function() {
				document.body.classList.remove(`block-interactivity-${i}`), t.forEach(function(e) {
					return e.classList.remove(`allow-interactivity-${i}`);
				});
			};
		}
	}, [
		e.inert,
		e.lockRef.current,
		e.shards
	]);
	var c = o.useCallback(function(e, t) {
		if ("touches" in e && e.touches.length === 2 || e.type === "wheel" && e.ctrlKey) return !s.current.allowPinchZoom;
		var i = Kn(e), a = n.current, o = "deltaX" in e ? e.deltaX : a[0] - i[0], c = "deltaY" in e ? e.deltaY : a[1] - i[1], l, u = e.target, d = Math.abs(o) > Math.abs(c) ? "h" : "v";
		if ("touches" in e && d === "h" && u.type === "range") return !1;
		var f = window.getSelection(), p = f && f.anchorNode;
		if (p && (p === u || p.contains(u))) return !1;
		var m = zn(d, u);
		if (!m) return !0;
		if (m ? l = d : (l = d === "v" ? "h" : "v", m = zn(d, u)), !m) return !1;
		if (!r.current && "changedTouches" in e && (o || c) && (r.current = l), !l) return !0;
		var h = r.current || l;
		return Gn(h, t, e, h === "h" ? o : c, !0);
	}, []), l = o.useCallback(function(e) {
		var n = e;
		if (Qn.length && Qn[Qn.length - 1] === a) {
			var r = "deltaY" in n ? qn(n) : Kn(n), i = t.current.filter(function(e) {
				return e.name === n.type && (e.target === n.target || n.target === e.shadowParent) && Yn(e.delta, r);
			})[0];
			if (i && i.should) n.cancelable && n.preventDefault();
			else if (!i) {
				var o = (s.current.shards || []).map(Jn).filter(Boolean).filter(function(e) {
					return e.contains(n.target);
				});
				(o.length > 0 ? c(n, o[0]) : !s.current.noIsolation) && n.cancelable && n.preventDefault();
			}
		}
	}, []), u = o.useCallback(function(e, n, r, i) {
		var a = {
			name: e,
			delta: n,
			target: r,
			should: i,
			shadowParent: er(r)
		};
		t.current.push(a), setTimeout(function() {
			t.current = t.current.filter(function(e) {
				return e !== a;
			});
		}, 1);
	}, []), d = o.useCallback(function(e) {
		n.current = Kn(e), r.current = void 0;
	}, []), f = o.useCallback(function(t) {
		u(t.type, qn(t), t.target, c(t, e.lockRef.current));
	}, []), p = o.useCallback(function(t) {
		u(t.type, Kn(t), t.target, c(t, e.lockRef.current));
	}, []);
	o.useEffect(function() {
		return Qn.push(a), e.setCallbacks({
			onScrollCapture: f,
			onWheelCapture: f,
			onTouchMoveCapture: p
		}), document.addEventListener("wheel", l, Pn), document.addEventListener("touchmove", l, Pn), document.addEventListener("touchstart", d, Pn), function() {
			Qn = Qn.filter(function(e) {
				return e !== a;
			}), document.removeEventListener("wheel", l, Pn), document.removeEventListener("touchmove", l, Pn), document.removeEventListener("touchstart", d, Pn);
		};
	}, []);
	var m = e.removeScrollBar, h = e.inert;
	return o.createElement(o.Fragment, null, h ? o.createElement(a, { styles: Xn(i) }) : null, m ? o.createElement(jn, {
		noRelative: e.noRelative,
		gapMode: e.gapMode
	}) : null);
}
function er(e) {
	for (var t = null; e !== null;) e instanceof ShadowRoot && (t = e.host, e = e.host), e = e.parentNode;
	return t;
}
// node_modules/react-remove-scroll/dist/es2015/sidecar.js
var tr = dn(fn, $n), nr = o.forwardRef(function(e, t) {
	return o.createElement(mn, G({}, e, {
		ref: t,
		sideCar: tr
	}));
});
nr.classNames = mn.classNames;
// node_modules/aria-hidden/dist/es2015/index.js
var rr = function(e) {
	return typeof document > "u" ? null : (Array.isArray(e) ? e[0] : e).ownerDocument.body;
}, ir = /* @__PURE__ */ new WeakMap(), ar = /* @__PURE__ */ new WeakMap(), or = {}, sr = 0, cr = function(e) {
	return e && (e.host || cr(e.parentNode));
}, lr = function(e, t) {
	return t.map(function(t) {
		if (e.contains(t)) return t;
		var n = cr(t);
		return n && e.contains(n) ? n : (console.error("aria-hidden", t, "in not contained inside", e, ". Doing nothing"), null);
	}).filter(function(e) {
		return !!e;
	});
}, ur = function(e, t, n, r) {
	var i = lr(t, Array.isArray(e) ? e : [e]);
	or[n] || (or[n] = /* @__PURE__ */ new WeakMap());
	var a = or[n], o = [], s = /* @__PURE__ */ new Set(), c = new Set(i), l = function(e) {
		e && !s.has(e) && (s.add(e), l(e.parentNode));
	};
	i.forEach(l);
	var u = function(e) {
		e && !c.has(e) && Array.prototype.forEach.call(e.children, function(e) {
			if (s.has(e)) u(e);
			else try {
				var t = e.getAttribute(r), i = t !== null && t !== "false", c = (ir.get(e) || 0) + 1, l = (a.get(e) || 0) + 1;
				ir.set(e, c), a.set(e, l), o.push(e), c === 1 && i && ar.set(e, !0), l === 1 && e.setAttribute(n, "true"), i || e.setAttribute(r, "true");
			} catch (t) {
				console.error("aria-hidden: cannot operate on ", e, t);
			}
		});
	};
	return u(t), s.clear(), sr++, function() {
		o.forEach(function(e) {
			var t = ir.get(e) - 1, i = a.get(e) - 1;
			ir.set(e, t), a.set(e, i), t || (ar.has(e) || e.removeAttribute(r), ar.delete(e)), i || e.removeAttribute(n);
		}), sr--, sr || (ir = /* @__PURE__ */ new WeakMap(), ir = /* @__PURE__ */ new WeakMap(), ar = /* @__PURE__ */ new WeakMap(), or = {});
	};
}, dr = function(e, t, n) {
	n === void 0 && (n = "data-aria-hidden");
	var r = Array.from(Array.isArray(e) ? e : [e]), i = t || rr(e);
	return i ? (r.push.apply(r, Array.from(i.querySelectorAll("[aria-live], script"))), ur(r, i, n, "aria-hidden")) : function() {
		return null;
	};
}, fr = Object.defineProperty, K = (e, t) => fr(e, "name", {
	value: t,
	configurable: !0
}), pr = "Dialog", [mr, hr] = /* @__PURE__ */ L(pr), [gr, q] = mr(pr), _r = /* @__PURE__ */ K((e) => {
	let { __scopeDialog: t, children: n, open: r, defaultOpen: i, onOpenChange: a, modal: c = !0 } = e, l = o.useRef(null), u = o.useRef(null), { nodes: d, registry: f } = Ot(), [p, m] = Fe({
		prop: r,
		defaultProp: i ?? !1,
		onChange: a,
		caller: pr
	}), [h, g] = o.useState(0), [_, v] = o.useState(0);
	return /* @__PURE__ */ (0, s.jsx)(gr, {
		scope: t,
		triggerRef: l,
		contentRef: u,
		contentId: Qe(),
		titleId: Qe(),
		descriptionId: Qe(),
		titlePresent: h > 0,
		descriptionPresent: _ > 0,
		setTitleCount: g,
		setDescriptionCount: v,
		open: p,
		onOpenChange: m,
		onOpenToggle: o.useCallback(() => m((e) => !e), [m]),
		modal: c,
		branchNodes: d,
		branchRegistry: f,
		children: n
	});
}, "Dialog"), vr = "DialogTrigger", yr = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ K(function(e, t) {
	let { __scopeDialog: n, ...r } = e, i = q(vr, n), a = v(t, i.triggerRef);
	return /* @__PURE__ */ (0, s.jsx)(F.button, {
		type: "button",
		"aria-haspopup": "dialog",
		"aria-expanded": i.open,
		"aria-controls": i.open ? i.contentId : void 0,
		"data-state": Rr(i.open),
		...r,
		ref: a,
		onClick: B(e.onClick, i.onOpenToggle)
	});
}, "DialogTrigger")), br = "DialogPortal", [xr, Sr] = mr(br, { forceMount: void 0 }), Cr = /* @__PURE__ */ K((e) => {
	let { __scopeDialog: t, forceMount: n, children: r, container: i } = e, a = q(br, t);
	return /* @__PURE__ */ (0, s.jsx)(xr, {
		scope: t,
		forceMount: n,
		children: o.Children.map(r, (e) => /* @__PURE__ */ (0, s.jsx)(He, {
			present: n || a.open,
			children: /* @__PURE__ */ (0, s.jsx)(Vt, {
				asChild: !0,
				container: i,
				children: e
			})
		}))
	});
}, "DialogPortal"), wr = "DialogOverlay", Tr = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ K(function(e, t) {
	let n = Sr(wr, e.__scopeDialog), { forceMount: r = n.forceMount, ...i } = e, a = q(wr, e.__scopeDialog);
	return a.modal ? /* @__PURE__ */ (0, s.jsx)(He, {
		present: r || a.open,
		children: /* @__PURE__ */ (0, s.jsx)(Dr, {
			...i,
			ref: t
		})
	}) : null;
}, "DialogOverlay")), Er = /* @__PURE__ */ x("DialogOverlay.RemoveScroll"), Dr = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ K(function(e, t) {
	let { __scopeDialog: n, ...r } = e, i = q(wr, n), a = v(t, ht());
	return /* @__PURE__ */ (0, s.jsx)(nr, {
		as: Er,
		allowPinchZoom: !0,
		shards: o.useMemo(() => [i.contentRef, ...i.branchNodes.map((e) => ({ current: e }))], [i.contentRef, i.branchNodes]),
		children: /* @__PURE__ */ (0, s.jsx)(F.div, {
			"data-state": Rr(i.open),
			...r,
			ref: a,
			style: {
				pointerEvents: "auto",
				...r.style
			}
		})
	});
}, "DialogOverlayImpl")), Or = "DialogContent", kr = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ K(function(e, t) {
	let n = Sr(Or, e.__scopeDialog), { forceMount: r = n.forceMount, ...i } = e, a = q(Or, e.__scopeDialog);
	return /* @__PURE__ */ (0, s.jsx)(He, {
		present: r || a.open,
		children: a.modal ? /* @__PURE__ */ (0, s.jsx)(Ar, {
			...i,
			ref: t
		}) : /* @__PURE__ */ (0, s.jsx)(jr, {
			...i,
			ref: t
		})
	});
}, "DialogContent")), Ar = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ K(function(e, t) {
	let n = q(Or, e.__scopeDialog), r = o.useRef(null), i = v(t, n.contentRef, r);
	return o.useEffect(() => {
		let e = r.current;
		if (e) return dr(e);
	}, []), /* @__PURE__ */ (0, s.jsx)(Mr, {
		...e,
		ref: i,
		trapFocus: n.open,
		disableOutsidePointerEvents: n.open,
		onCloseAutoFocus: B(e.onCloseAutoFocus, (e) => {
			e.preventDefault(), n.triggerRef.current?.focus();
		}),
		onPointerDownOutside: B(e.onPointerDownOutside, (e) => {
			let t = e.detail.originalEvent, n = t.button === 0 && t.ctrlKey === !0;
			(t.button === 2 || n) && e.preventDefault();
		}),
		onFocusOutside: B(e.onFocusOutside, (e) => e.preventDefault())
	});
}, "DialogContentModal")), jr = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ K(function(e, t) {
	let n = q(Or, e.__scopeDialog), r = o.useRef(!1), i = o.useRef(!1);
	return /* @__PURE__ */ (0, s.jsx)(Mr, {
		...e,
		ref: t,
		trapFocus: !1,
		disableOutsidePointerEvents: !1,
		onCloseAutoFocus: (t) => {
			e.onCloseAutoFocus?.(t), t.defaultPrevented || (r.current || n.triggerRef.current?.focus(), t.preventDefault()), r.current = !1, i.current = !1;
		},
		onInteractOutside: (t) => {
			e.onInteractOutside?.(t), t.defaultPrevented || (r.current = !0, t.detail.originalEvent.type === "pointerdown" && (i.current = !0));
			let a = t.target;
			n.triggerRef.current?.contains(a) && t.preventDefault(), t.detail.originalEvent.type === "focusin" && i.current && t.preventDefault();
		}
	});
}, "DialogContentNonModal")), Mr = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ K(function(e, t) {
	let { __scopeDialog: n, trapFocus: r, onOpenAutoFocus: i, onCloseAutoFocus: a, "aria-describedby": o, children: c, ...l } = e, u = q(Or, n);
	return qt(), /* @__PURE__ */ (0, s.jsx)(Dt, {
		registry: u.branchRegistry,
		children: /* @__PURE__ */ (0, s.jsx)(Tt, {
			asChild: !0,
			loop: !0,
			trapped: r,
			branches: u.branchNodes,
			onMountAutoFocus: i,
			onUnmountAutoFocus: a,
			children: /* @__PURE__ */ (0, s.jsx)(mt, {
				role: "dialog",
				id: u.contentId,
				"aria-labelledby": u.titlePresent ? u.titleId : void 0,
				"aria-describedby": u.descriptionPresent ? Lr(o, u.descriptionId) : o,
				"data-state": Rr(u.open),
				...l,
				ref: t,
				deferPointerDownOutside: !0,
				onDismiss: () => u.onOpenChange(!1),
				children: c
			})
		})
	});
}, "DialogContentImpl")), Nr = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ K(function(e, t) {
	let { __scopeDialog: n, ...r } = e, i = q("DialogTitle", n), { setTitleCount: a } = i;
	return R(() => (a((e) => e + 1), () => a((e) => e - 1)), [a]), /* @__PURE__ */ (0, s.jsx)(F.h2, {
		id: i.titleId,
		...r,
		ref: t
	});
}, "DialogTitle")), Pr = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ K(function(e, t) {
	let { __scopeDialog: n, ...r } = e, i = q("DialogDescription", n), { setDescriptionCount: a } = i;
	return R(() => (a((e) => e + 1), () => a((e) => e - 1)), [a]), /* @__PURE__ */ (0, s.jsx)(F.p, {
		id: i.descriptionId,
		...r,
		ref: t
	});
}, "DialogDescription")), Fr = "DialogClose", Ir = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ K(function(e, t) {
	let { __scopeDialog: n, ...r } = e, i = q(Fr, n);
	return /* @__PURE__ */ (0, s.jsx)(F.button, {
		type: "button",
		...r,
		ref: t,
		onClick: B(e.onClick, () => i.onOpenChange(!1))
	});
}, "DialogClose"));
function Lr(...e) {
	let t = /* @__PURE__ */ new Set();
	for (let n of e) if (typeof n == "string") for (let e of String(n).trim().split(/\s+/)) e && t.add(e);
	return t.size > 0 ? Array.from(t).join(" ") : void 0;
}
K(Lr, "concatAriaDescribedby");
function Rr(e) {
	return e ? "open" : "closed";
}
K(Rr, "getState");
// node_modules/@radix-ui/react-use-size/dist/index.mjs
var zr = Object.defineProperty, Br = (e, t) => zr(e, "name", {
	value: t,
	configurable: !0
});
function Vr(e) {
	let [t, n] = o.useState(void 0);
	return R(() => {
		if (e) {
			n({
				width: e.offsetWidth,
				height: e.offsetHeight
			});
			let t = 0, r = new ResizeObserver((r) => {
				if (!Array.isArray(r) || !r.length) return;
				let i = r[0];
				window.cancelAnimationFrame(t), t = window.requestAnimationFrame(() => {
					let t, r;
					if ("borderBoxSize" in i) {
						let e = i.borderBoxSize, n = Array.isArray(e) ? e[0] : e;
						t = n.inlineSize, r = n.blockSize;
					} else t = e.offsetWidth, r = e.offsetHeight;
					n({
						width: t,
						height: r
					});
				});
			});
			return r.observe(e, { box: "border-box" }), () => {
				window.cancelAnimationFrame(t), r.unobserve(e);
			};
		}
		n(void 0);
	}, [e]), t;
}
Br(Vr, "useSize");
// node_modules/@floating-ui/utils/dist/floating-ui.utils.mjs
var Hr = [
	"top",
	"right",
	"bottom",
	"left"
], Ur = Math.min, Wr = Math.max, Gr = Math.round, Kr = Math.floor, qr = (e) => ({
	x: e,
	y: e
}), Jr = {
	left: "right",
	right: "left",
	bottom: "top",
	top: "bottom"
};
function Yr(e, t, n) {
	return Wr(e, Ur(t, n));
}
function Xr(e, t) {
	return typeof e == "function" ? e(t) : e;
}
function Zr(e) {
	return e.split("-")[0];
}
function Qr(e) {
	return e.split("-")[1];
}
function $r(e) {
	return e === "x" ? "y" : "x";
}
function ei(e) {
	return e === "y" ? "height" : "width";
}
function J(e) {
	let t = e[0];
	return t === "t" || t === "b" ? "y" : "x";
}
function ti(e) {
	return $r(J(e));
}
function ni(e, t, n) {
	n === void 0 && (n = !1);
	let r = Qr(e), i = ti(e), a = ei(i), o = i === "x" ? r === (n ? "end" : "start") ? "right" : "left" : r === "start" ? "bottom" : "top";
	return t.reference[a] > t.floating[a] && (o = di(o)), [o, di(o)];
}
function ri(e) {
	let t = di(e);
	return [
		ii(e),
		t,
		ii(t)
	];
}
function ii(e) {
	return e.includes("start") ? e.replace("start", "end") : e.replace("end", "start");
}
var ai = ["left", "right"], oi = ["right", "left"], si = ["top", "bottom"], ci = ["bottom", "top"];
function li(e, t, n) {
	switch (e) {
		case "top":
		case "bottom": return n ? t ? oi : ai : t ? ai : oi;
		case "left":
		case "right": return t ? si : ci;
		default: return [];
	}
}
function ui(e, t, n, r) {
	let i = Qr(e), a = li(Zr(e), n === "start", r);
	return i && (a = a.map((e) => e + "-" + i), t && (a = a.concat(a.map(ii)))), a;
}
function di(e) {
	let t = Zr(e);
	return Jr[t] + e.slice(t.length);
}
function fi(e) {
	return {
		top: e.top ?? 0,
		right: e.right ?? 0,
		bottom: e.bottom ?? 0,
		left: e.left ?? 0
	};
}
function pi(e) {
	return typeof e == "number" ? {
		top: e,
		right: e,
		bottom: e,
		left: e
	} : fi(e);
}
function mi(e) {
	let { x: t, y: n, width: r, height: i } = e;
	return {
		width: r,
		height: i,
		top: n,
		left: t,
		right: t + r,
		bottom: n + i,
		x: t,
		y: n
	};
}
// node_modules/@floating-ui/core/dist/floating-ui.core.mjs
function hi(e, t, n) {
	let { reference: r, floating: i } = e, a = J(t), o = ti(t), s = ei(o), c = Zr(t), l = a === "y", u = r.x + r.width / 2 - i.width / 2, d = r.y + r.height / 2 - i.height / 2, f = r[s] / 2 - i[s] / 2, p;
	switch (c) {
		case "top":
			p = {
				x: u,
				y: r.y - i.height
			};
			break;
		case "bottom":
			p = {
				x: u,
				y: r.y + r.height
			};
			break;
		case "right":
			p = {
				x: r.x + r.width,
				y: d
			};
			break;
		case "left":
			p = {
				x: r.x - i.width,
				y: d
			};
			break;
		default: p = {
			x: r.x,
			y: r.y
		};
	}
	let m = Qr(t);
	return m && (p[o] += f * (m === "end" ? 1 : -1) * (n && l ? -1 : 1)), p;
}
async function gi(e, t) {
	t === void 0 && (t = {});
	let { x: n, y: r, platform: i, rects: a, elements: o, strategy: s } = e, { boundary: c = "clippingAncestors", rootBoundary: l = "viewport", elementContext: u = "floating", altBoundary: d = !1, padding: f = 0 } = Xr(t, e), p = pi(f), m = o[d ? u === "floating" ? "reference" : "floating" : u], h = mi(await i.getClippingRect({
		element: await (i.isElement == null ? void 0 : i.isElement(m)) ?? !0 ? m : m.contextElement || await (i.getDocumentElement == null ? void 0 : i.getDocumentElement(o.floating)),
		boundary: c,
		rootBoundary: l,
		strategy: s
	})), g = u === "floating" ? {
		x: n,
		y: r,
		width: a.floating.width,
		height: a.floating.height
	} : a.reference, _ = await (i.getOffsetParent == null ? void 0 : i.getOffsetParent(o.floating)), v = await (i.isElement == null ? void 0 : i.isElement(_)) && await (i.getScale == null ? void 0 : i.getScale(_)) || {
		x: 1,
		y: 1
	}, y = mi(i.convertOffsetParentRelativeRectToViewportRelativeRect ? await i.convertOffsetParentRelativeRectToViewportRelativeRect({
		elements: o,
		rect: g,
		offsetParent: _,
		strategy: s
	}) : g);
	return {
		top: (h.top - y.top + p.top) / v.y,
		bottom: (y.bottom - h.bottom + p.bottom) / v.y,
		left: (h.left - y.left + p.left) / v.x,
		right: (y.right - h.right + p.right) / v.x
	};
}
var _i = 50, vi = async (e, t, n) => {
	let { placement: r = "bottom", strategy: i = "absolute", middleware: a = [], platform: o } = n, s = o.detectOverflow ? o : {
		...o,
		detectOverflow: gi
	}, c = await (o.isRTL == null ? void 0 : o.isRTL(t)), l = await o.getElementRects({
		reference: e,
		floating: t,
		strategy: i
	}), { x: u, y: d } = hi(l, r, c), f = r, p = 0, m = {};
	for (let n = 0; n < a.length; n++) {
		let h = a[n];
		if (!h) continue;
		let { name: g, fn: _ } = h, { x: v, y, data: b, reset: x } = await _({
			x: u,
			y: d,
			initialPlacement: r,
			placement: f,
			strategy: i,
			middlewareData: m,
			rects: l,
			platform: s,
			elements: {
				reference: e,
				floating: t
			}
		});
		u = v ?? u, d = y ?? d, m[g] = {
			...m[g],
			...b
		}, x && p < _i && (p++, typeof x == "object" && (x.placement && (f = x.placement), x.rects && (l = x.rects === !0 ? await o.getElementRects({
			reference: e,
			floating: t,
			strategy: i
		}) : x.rects), {x: u, y: d} = hi(l, f, c)), n = -1);
	}
	return {
		x: u,
		y: d,
		placement: f,
		strategy: i,
		middlewareData: m
	};
}, yi = (e) => ({
	name: "arrow",
	options: e,
	async fn(t) {
		let { x: n, y: r, placement: i, rects: a, platform: o, elements: s, middlewareData: c } = t, { element: l, padding: u = 0 } = Xr(e, t) || {};
		if (l == null) return {};
		let d = pi(u), f = {
			x: n,
			y: r
		}, p = ti(i), m = ei(p), h = await o.getDimensions(l), g = p === "y", _ = g ? "top" : "left", v = g ? "bottom" : "right", y = g ? "clientHeight" : "clientWidth", b = a.reference[m] + a.reference[p] - f[p] - a.floating[m], x = f[p] - a.reference[p], S = await (o.getOffsetParent == null ? void 0 : o.getOffsetParent(l)), C = S ? S[y] : 0;
		C && await (o.isElement == null ? void 0 : o.isElement(S)) || (C = s.floating[y] || a.floating[m]);
		let w = b / 2 - x / 2, T = C / 2 - h[m] / 2 - 1, E = Ur(d[_], T), D = Ur(d[v], T), O = C - h[m] - D, k = C / 2 - h[m] / 2 + w, A = Yr(E, k, O), j = !c.arrow && Qr(i) != null && k !== A && a.reference[m] / 2 - (k < E ? E : D) - h[m] / 2 < 0, M = j ? k < E ? k - E : k - O : 0;
		return {
			[p]: f[p] + M,
			data: {
				[p]: A,
				centerOffset: k - A - M,
				...j && { alignmentOffset: M }
			},
			reset: j
		};
	}
}), bi = function(e) {
	return e === void 0 && (e = {}), {
		name: "flip",
		options: e,
		async fn(t) {
			var n;
			let { placement: r, middlewareData: i, rects: a, initialPlacement: o, platform: s, elements: c } = t, { mainAxis: l = !0, crossAxis: u = !0, fallbackPlacements: d, fallbackStrategy: f = "bestFit", fallbackAxisSideDirection: p = "none", flipAlignment: m = !0, ...h } = Xr(e, t);
			if ((n = i.arrow) != null && n.alignmentOffset) return {};
			let g = Zr(r), _ = J(o), v = Zr(o) === o, y = await (s.isRTL == null ? void 0 : s.isRTL(c.floating)), b = d || (v || !m ? [di(o)] : ri(o)), x = p !== "none";
			!d && x && b.push(...ui(o, m, p, y));
			let S = [o, ...b], C = await s.detectOverflow(t, h), w = [], T = i.flip?.overflows || [];
			if (l && w.push(C[g]), u) {
				let e = ni(r, a, y);
				w.push(C[e[0]], C[e[1]]);
			}
			if (T = [...T, {
				placement: r,
				overflows: w
			}], !w.every((e) => e <= 0)) {
				let e = (i.flip?.index || 0) + 1, t = S[e];
				if (t && (u !== "alignment" || _ === J(t) || T.every((e) => J(e.placement) !== _ || e.overflows[0] > 0))) return {
					data: {
						index: e,
						overflows: T
					},
					reset: { placement: t }
				};
				let n = T.filter((e) => e.overflows[0] <= 0).sort((e, t) => e.overflows[1] - t.overflows[1])[0]?.placement;
				if (!n) switch (f) {
					case "bestFit": {
						let e = T.filter((e) => {
							if (x) {
								let t = J(e.placement);
								return t === _ || t === "y";
							}
							return !0;
						}).map((e) => [e.placement, e.overflows.filter((e) => e > 0).reduce((e, t) => e + t, 0)]).sort((e, t) => e[1] - t[1])[0]?.[0];
						e && (n = e);
						break;
					}
					case "initialPlacement": n = o;
				}
				if (r !== n) return { reset: { placement: n } };
			}
			return {};
		}
	};
};
function xi(e, t) {
	return {
		top: e.top - t.height,
		right: e.right - t.width,
		bottom: e.bottom - t.height,
		left: e.left - t.width
	};
}
function Si(e) {
	return Hr.some((t) => e[t] >= 0);
}
var Ci = function(e) {
	return e === void 0 && (e = {}), {
		name: "hide",
		options: e,
		async fn(t) {
			let { rects: n, platform: r } = t, { strategy: i = "referenceHidden", ...a } = Xr(e, t);
			switch (i) {
				case "referenceHidden": {
					let e = xi(await r.detectOverflow(t, {
						...a,
						elementContext: "reference"
					}), n.reference);
					return { data: {
						referenceHiddenOffsets: e,
						referenceHidden: Si(e)
					} };
				}
				case "escaped": {
					let e = xi(await r.detectOverflow(t, {
						...a,
						altBoundary: !0
					}), n.floating);
					return { data: {
						escapedOffsets: e,
						escaped: Si(e)
					} };
				}
				default: return {};
			}
		}
	};
}, wi = /*#__PURE__*/ new Set(["left", "top"]);
async function Ti(e, t) {
	let { placement: n, platform: r, elements: i } = e, a = await (r.isRTL == null ? void 0 : r.isRTL(i.floating)), o = Zr(n), s = Qr(n), c = J(n) === "y", l = wi.has(o) ? -1 : 1, u = a && c ? -1 : 1, d = Xr(t, e), { mainAxis: f, crossAxis: p, alignmentAxis: m } = typeof d == "number" ? {
		mainAxis: d,
		crossAxis: 0,
		alignmentAxis: null
	} : {
		mainAxis: d.mainAxis || 0,
		crossAxis: d.crossAxis || 0,
		alignmentAxis: d.alignmentAxis
	};
	return s && typeof m == "number" && (p = s === "end" ? m * -1 : m), c ? {
		x: p * u,
		y: f * l
	} : {
		x: f * l,
		y: p * u
	};
}
var Ei = function(e) {
	return e === void 0 && (e = 0), {
		name: "offset",
		options: e,
		async fn(t) {
			var n;
			let { x: r, y: i, placement: a, middlewareData: o } = t, s = await Ti(t, e);
			return a === o.offset?.placement && (n = o.arrow) != null && n.alignmentOffset ? {} : {
				x: r + s.x,
				y: i + s.y,
				data: {
					...s,
					placement: a
				}
			};
		}
	};
}, Di = function(e) {
	return e === void 0 && (e = {}), {
		name: "shift",
		options: e,
		async fn(t) {
			let { x: n, y: r, placement: i, platform: a } = t, { mainAxis: o = !0, crossAxis: s = !1, limiter: c = { fn: (e) => {
				let { x: t, y: n } = e;
				return {
					x: t,
					y: n
				};
			} }, ...l } = Xr(e, t), u = {
				x: n,
				y: r
			}, d = await a.detectOverflow(t, l), f = J(i), p = $r(f), m = u[p], h = u[f], g = (e, t) => Yr(t + d[e === "y" ? "top" : "left"], t, t - d[e === "y" ? "bottom" : "right"]);
			o && (m = g(p, m)), s && (h = g(f, h));
			let _ = c.fn({
				...t,
				[p]: m,
				[f]: h
			});
			return {
				..._,
				data: {
					x: _.x - n,
					y: _.y - r,
					enabled: {
						[p]: o,
						[f]: s
					}
				}
			};
		}
	};
}, Oi = function(e) {
	return e === void 0 && (e = {}), {
		options: e,
		fn(t) {
			let { x: n, y: r, placement: i, rects: a, middlewareData: o } = t, { offset: s = 0, mainAxis: c = !0, crossAxis: l = !0 } = Xr(e, t), u = {
				x: n,
				y: r
			}, d = J(i), f = $r(d), p = u[f], m = u[d], h = Xr(s, t), g = typeof h == "number" ? {
				mainAxis: h,
				crossAxis: 0
			} : {
				mainAxis: h.mainAxis ?? 0,
				crossAxis: h.crossAxis ?? 0
			};
			if (c) {
				let e = f === "y" ? "height" : "width", t = a.reference[f] - a.floating[e] + g.mainAxis, n = a.reference[f] + a.reference[e] - g.mainAxis;
				p < t ? p = t : p > n && (p = n);
			}
			if (l) {
				let e = f === "y" ? "width" : "height", t = wi.has(Zr(i)), n = a.reference[d] - a.floating[e] + (t && o.offset?.[d] || 0) + (t ? 0 : g.crossAxis), r = a.reference[d] + a.reference[e] + (t ? 0 : o.offset?.[d] || 0) - (t ? g.crossAxis : 0);
				m < n ? m = n : m > r && (m = r);
			}
			return {
				[f]: p,
				[d]: m
			};
		}
	};
}, ki = function(e) {
	return e === void 0 && (e = {}), {
		name: "size",
		options: e,
		async fn(t) {
			let { placement: n, rects: r, platform: i, elements: a } = t, { apply: o = () => {}, ...s } = Xr(e, t), c = await i.detectOverflow(t, s), l = Zr(n), u = Qr(n), d = J(n) === "y", { width: f, height: p } = r.floating, m, h;
			l === "top" || l === "bottom" ? (m = l, h = u === (await (i.isRTL == null ? void 0 : i.isRTL(a.floating)) ? "start" : "end") ? "left" : "right") : (h = l, m = u === "end" ? "top" : "bottom");
			let g = p - c.top - c.bottom, _ = f - c.left - c.right, v = Ur(p - c[m], g), y = Ur(f - c[h], _), b = t.middlewareData.shift, x = !b, S = v, C = y;
			b != null && b.enabled.x && (C = _), b != null && b.enabled.y && (S = g), x && !u && (d ? C = f - 2 * Wr(c.left, c.right) : S = p - 2 * Wr(c.top, c.bottom)), await o({
				...t,
				availableWidth: C,
				availableHeight: S
			});
			let w = await i.getDimensions(a.floating);
			return f !== w.width || p !== w.height ? { reset: { rects: !0 } } : {};
		}
	};
};
// node_modules/@floating-ui/utils/dist/floating-ui.utils.dom.mjs
function Ai() {
	return typeof window < "u";
}
function ji(e) {
	return Ni(e) ? (e.nodeName || "").toLowerCase() : "#document";
}
function Y(e) {
	var t;
	return (e == null || (t = e.ownerDocument) == null ? void 0 : t.defaultView) || window;
}
function Mi(e) {
	return ((Ni(e) ? e.ownerDocument : e.document) || window.document)?.documentElement;
}
function Ni(e) {
	return Ai() ? e instanceof Node || e instanceof Y(e).Node : !1;
}
function X(e) {
	return Ai() ? e instanceof Element || e instanceof Y(e).Element : !1;
}
function Pi(e) {
	return Ai() ? e instanceof HTMLElement || e instanceof Y(e).HTMLElement : !1;
}
function Fi(e) {
	return !Ai() || typeof ShadowRoot > "u" ? !1 : e instanceof ShadowRoot || e instanceof Y(e).ShadowRoot;
}
function Ii(e) {
	let { overflow: t, overflowX: n, overflowY: r, display: i } = Z(e);
	return /auto|scroll|overlay|hidden|clip/.test(t + r + n) && i !== "inline" && i !== "contents";
}
function Li(e) {
	return /^(table|td|th)$/.test(ji(e));
}
function Ri(e) {
	try {
		if (e.matches(":popover-open")) return !0;
	} catch {}
	try {
		return e.matches(":modal");
	} catch {
		return !1;
	}
}
var zi = /transform|translate|scale|rotate|perspective|filter/, Bi = /paint|layout|strict|content/, Vi = (e) => !!e && e !== "none", Hi;
function Ui(e) {
	let t = X(e) ? Z(e) : e;
	return Vi(t.transform) || Vi(t.translate) || Vi(t.scale) || Vi(t.rotate) || Vi(t.perspective) || !Gi() && (Vi(t.backdropFilter) || Vi(t.filter)) || zi.test(t.willChange || "") || Bi.test(t.contain || "");
}
function Wi(e) {
	let t = Ji(e);
	for (; Pi(t) && !Ki(t);) {
		if (Ui(t)) return t;
		if (Ri(t)) return null;
		t = Ji(t);
	}
	return null;
}
function Gi() {
	return Hi ??= typeof CSS < "u" && CSS.supports && CSS.supports("-webkit-backdrop-filter", "none"), Hi;
}
function Ki(e) {
	return /^(html|body|#document)$/.test(ji(e));
}
function Z(e) {
	return Y(e).getComputedStyle(e);
}
function qi(e) {
	return X(e) ? {
		scrollLeft: e.scrollLeft,
		scrollTop: e.scrollTop
	} : {
		scrollLeft: e.scrollX,
		scrollTop: e.scrollY
	};
}
function Ji(e) {
	if (ji(e) === "html") return e;
	let t = e.assignedSlot || e.parentNode || Fi(e) && e.host || Mi(e);
	return Fi(t) ? t.host : t;
}
function Yi(e) {
	let t = Ji(e);
	return Ki(t) ? (e.ownerDocument || e).body : Pi(t) && Ii(t) ? t : Yi(t);
}
function Xi(e, t, n) {
	t === void 0 && (t = []), n === void 0 && (n = !0);
	let r = Yi(e), i = r === e.ownerDocument?.body, a = Y(r);
	if (i) {
		let e = Zi(a);
		return t.concat(a, a.visualViewport || [], Ii(r) ? r : [], e && n ? Xi(e) : []);
	}
	return t.concat(r, Xi(r, [], n));
}
function Zi(e) {
	return e.parent && Object.getPrototypeOf(e.parent) ? e.frameElement : null;
}
// node_modules/@floating-ui/dom/dist/floating-ui.dom.mjs
function Qi(e) {
	let t = Z(e), n = parseFloat(t.width) || 0, r = parseFloat(t.height) || 0, i = Pi(e), a = i ? e.offsetWidth : n, o = i ? e.offsetHeight : r, s = Gr(n) !== a || Gr(r) !== o;
	return s && (n = a, r = o), {
		width: n,
		height: r,
		$: s
	};
}
function $i(e) {
	return X(e) ? e : e.contextElement;
}
function ea(e) {
	let t = $i(e);
	if (!Pi(t)) return qr(1);
	let n = t.getBoundingClientRect(), { width: r, height: i, $: a } = Qi(t), o = (a ? Gr(n.width) : n.width) / r, s = (a ? Gr(n.height) : n.height) / i;
	return o && Number.isFinite(o) || (o = 1), s && Number.isFinite(s) || (s = 1), {
		x: o,
		y: s
	};
}
var ta = /*#__PURE__*/ qr(0);
function na(e) {
	let t = Y(e);
	return !Gi() || !t.visualViewport ? ta : {
		x: t.visualViewport.offsetLeft,
		y: t.visualViewport.offsetTop
	};
}
function ra(e, t, n) {
	return t === void 0 && (t = !1), !!n && t && n === Y(e);
}
function ia(e, t, n, r) {
	t === void 0 && (t = !1), n === void 0 && (n = !1);
	let i = e.getBoundingClientRect(), a = $i(e), o = qr(1);
	t && (r ? X(r) && (o = ea(r)) : o = ea(e));
	let s = ra(a, n, r) ? na(a) : qr(0), c = (i.left + s.x) / o.x, l = (i.top + s.y) / o.y, u = i.width / o.x, d = i.height / o.y;
	if (a && r) {
		let e = Y(a), t = X(r) ? Y(r) : r, n = e, i = Zi(n);
		for (; i && t !== n;) {
			let e = ea(i), t = i.getBoundingClientRect(), r = Z(i), a = t.left + (i.clientLeft + parseFloat(r.paddingLeft)) * e.x, o = t.top + (i.clientTop + parseFloat(r.paddingTop)) * e.y;
			c *= e.x, l *= e.y, u *= e.x, d *= e.y, c += a, l += o, n = Y(i), i = Zi(n);
		}
	}
	return mi({
		width: u,
		height: d,
		x: c,
		y: l
	});
}
function aa(e, t) {
	let n = qi(e).scrollLeft;
	return t ? t.left + n : ia(Mi(e)).left + n;
}
function oa(e, t) {
	let n = e.getBoundingClientRect();
	return {
		x: n.left + t.scrollLeft - aa(e, n),
		y: n.top + t.scrollTop
	};
}
function sa(e) {
	let { elements: t, rect: n, offsetParent: r, strategy: i } = e, a = i === "fixed", o = Mi(r), s = t ? Ri(t.floating) : !1;
	if (r === o || s && a) return n;
	let c = {
		scrollLeft: 0,
		scrollTop: 0
	}, l = qr(1), u = qr(0), d = Pi(r);
	if ((d || !a) && ((ji(r) !== "body" || Ii(o)) && (c = qi(r)), d)) {
		let e = ia(r);
		l = ea(r), u.x = e.x + r.clientLeft, u.y = e.y + r.clientTop;
	}
	let f = o && !d && !a ? oa(o, c) : qr(0);
	return {
		width: n.width * l.x,
		height: n.height * l.y,
		x: n.x * l.x - c.scrollLeft * l.x + u.x + f.x,
		y: n.y * l.y - c.scrollTop * l.y + u.y + f.y
	};
}
function ca(e) {
	return e.getClientRects ? Array.from(e.getClientRects()) : [];
}
function la(e) {
	let t = qi(e), n = e.ownerDocument.body, r = Wr(e.scrollWidth, e.clientWidth, n.scrollWidth, n.clientWidth), i = Wr(e.scrollHeight, e.clientHeight, n.scrollHeight, n.clientHeight), a = -t.scrollLeft + aa(e), o = -t.scrollTop;
	return Z(n).direction === "rtl" && (a += Wr(e.clientWidth, n.clientWidth) - r), {
		width: r,
		height: i,
		x: a,
		y: o
	};
}
var ua = 25;
function da(e, t, n) {
	n === void 0 && (n = "viewport");
	let r = n === "layoutViewport", i = Y(e), a = Mi(e), o = i.visualViewport, s = a.clientWidth, c = a.clientHeight, l = 0, u = 0;
	if (o) {
		let e = !Gi() || t === "fixed";
		r ? e || (l = -o.offsetLeft, u = -o.offsetTop) : (s = o.width, c = o.height, e && (l = o.offsetLeft, u = o.offsetTop));
	}
	if (aa(a) <= 0) {
		let e = a.ownerDocument, t = e.body, n = getComputedStyle(t), r = e.compatMode === "CSS1Compat" && parseFloat(n.marginLeft) + parseFloat(n.marginRight) || 0, i = Math.abs(a.clientWidth - t.clientWidth - r), o = getComputedStyle(a).scrollbarGutter === "stable both-edges" ? i / 2 : i;
		o <= ua && (s -= o);
	}
	return {
		width: s,
		height: c,
		x: l,
		y: u
	};
}
function fa(e, t) {
	let n = ia(e, !0, t === "fixed"), r = n.top + e.clientTop, i = n.left + e.clientLeft, a = ea(e);
	return {
		width: e.clientWidth * a.x,
		height: e.clientHeight * a.y,
		x: i * a.x,
		y: r * a.y
	};
}
function pa(e, t, n) {
	let r;
	if (t === "viewport" || t === "layoutViewport") r = da(e, n, t);
	else if (t === "document") r = la(Mi(e));
	else if (X(t)) r = fa(t, n);
	else {
		let n = na(e);
		r = {
			x: t.x - n.x,
			y: t.y - n.y,
			width: t.width,
			height: t.height
		};
	}
	return mi(r);
}
function ma(e, t) {
	let n = t.get(e);
	if (n) return n;
	let r = Xi(e, [], !1).filter((e) => X(e) && ji(e) !== "body"), i = null, a = Z(e).position === "fixed", o = a ? Ji(e) : e;
	for (; X(o) && !Ki(o);) {
		let e = Z(o), t = Ui(o), n = i ? i.position : a ? "fixed" : "";
		!t && (n === "fixed" || n === "absolute" && e.position === "static") ? r = r.filter((e) => e !== o) : i = e, o = Ji(o);
	}
	return t.set(e, r), r;
}
function ha(e) {
	let { element: t, boundary: n, rootBoundary: r, strategy: i } = e, a = [...n === "clippingAncestors" ? Ri(t) ? [] : ma(t, this._c) : [].concat(n), r], o = pa(t, a[0], i), s = o.top, c = o.right, l = o.bottom, u = o.left;
	for (let e = 1; e < a.length; e++) {
		let n = pa(t, a[e], i);
		s = Wr(n.top, s), c = Ur(n.right, c), l = Ur(n.bottom, l), u = Wr(n.left, u);
	}
	return {
		width: c - u,
		height: l - s,
		x: u,
		y: s
	};
}
function ga(e) {
	let { width: t, height: n } = Qi(e);
	return {
		width: t,
		height: n
	};
}
function _a(e, t, n) {
	let r = Pi(t), i = Mi(t), a = n === "fixed", o = ia(e, !0, a, t), s = {
		scrollLeft: 0,
		scrollTop: 0
	}, c = qr(0);
	if ((r || !a) && ((ji(t) !== "body" || Ii(i)) && (s = qi(t)), r)) {
		let e = ia(t, !0, a, t);
		c.x = e.x + t.clientLeft, c.y = e.y + t.clientTop;
	}
	!r && i && (c.x = aa(i));
	let l = i && !r && !a ? oa(i, s) : qr(0);
	return {
		x: o.left + s.scrollLeft - c.x - l.x,
		y: o.top + s.scrollTop - c.y - l.y,
		width: o.width,
		height: o.height
	};
}
function va(e) {
	return Z(e).position === "static";
}
function ya(e, t) {
	if (!Pi(e) || Z(e).position === "fixed") return null;
	if (t) return t(e);
	let n = e.offsetParent;
	return Mi(e) === n && (n = n.ownerDocument.body), n;
}
function ba(e, t) {
	let n = Y(e);
	if (Ri(e)) return n;
	if (!Pi(e)) {
		let t = Ji(e);
		for (; t && !Ki(t);) {
			if (X(t) && !va(t)) return t;
			t = Ji(t);
		}
		return n;
	}
	let r = ya(e, t);
	for (; r && Li(r) && va(r);) r = ya(r, t);
	return r && Ki(r) && va(r) && !Ui(r) ? n : r || Wi(e) || n;
}
var xa = async function(e) {
	let t = this.getOffsetParent || ba, n = this.getDimensions, r = await n(e.floating);
	return {
		reference: _a(e.reference, await t(e.floating), e.strategy),
		floating: {
			x: 0,
			y: 0,
			width: r.width,
			height: r.height
		}
	};
};
function Sa(e) {
	return Z(e).direction === "rtl";
}
var Ca = {
	convertOffsetParentRelativeRectToViewportRelativeRect: sa,
	getDocumentElement: Mi,
	getClippingRect: ha,
	getOffsetParent: ba,
	getElementRects: xa,
	getClientRects: ca,
	getDimensions: ga,
	getScale: ea,
	isElement: X,
	isRTL: Sa
};
function wa(e, t) {
	return e.x === t.x && e.y === t.y && e.width === t.width && e.height === t.height;
}
function Ta(e, t, n) {
	let r = null, i, a = Mi(e);
	function o() {
		var e;
		clearTimeout(i), (e = r) == null || e.disconnect(), r = null;
	}
	function s(n, c) {
		n === void 0 && (n = !1), c === void 0 && (c = 1), o();
		let l = e.getBoundingClientRect(), { left: u, top: d, width: f, height: p } = l;
		if (n || t(), !f || !p) return;
		let m = Kr(d), h = Kr(a.clientWidth - (u + f)), g = Kr(a.clientHeight - (d + p)), _ = Kr(u), v = {
			rootMargin: -m + "px " + -h + "px " + -g + "px " + -_ + "px",
			threshold: Wr(0, Ur(1, c)) || 1
		}, y = !0;
		function b(t) {
			let n = t[0].intersectionRatio;
			if (!wa(l, e.getBoundingClientRect())) return s();
			if (n !== c) {
				if (!y) return s();
				n ? s(!1, n) : i = setTimeout(() => {
					s(!1, 1e-7);
				}, 1e3);
			}
			y = !1;
		}
		try {
			r = new IntersectionObserver(b, {
				...v,
				root: a.ownerDocument
			});
		} catch {
			r = new IntersectionObserver(b, v);
		}
		r.observe(e);
	}
	let c = Y(e), l = () => s(n);
	return c.addEventListener("resize", l), s(!0), () => {
		c.removeEventListener("resize", l), o();
	};
}
function Ea(e, t, n, r) {
	r === void 0 && (r = {});
	let { ancestorScroll: i = !0, ancestorResize: a = !0, elementResize: o = typeof ResizeObserver == "function", layoutShift: s = typeof IntersectionObserver == "function", animationFrame: c = !1 } = r, l = $i(e), u = i || a ? [...l ? Xi(l) : [], ...t ? Xi(t) : []] : [];
	u.forEach((e) => {
		i && e.addEventListener("scroll", n), a && e.addEventListener("resize", n);
	});
	let d = l && s ? Ta(l, n, a) : null, f = -1, p = null;
	o && (p = new ResizeObserver((e) => {
		let [r] = e;
		r && r.target === l && p && t && (p.unobserve(t), cancelAnimationFrame(f), f = requestAnimationFrame(() => {
			var e;
			(e = p) == null || e.observe(t);
		})), n();
	}), l && !c && p.observe(l), t && p.observe(t));
	let m, h = c ? ia(e) : null;
	c && g();
	function g() {
		let t = ia(e);
		h && !wa(h, t) && n(), h = t, m = requestAnimationFrame(g);
	}
	return n(), () => {
		var e;
		u.forEach((e) => {
			i && e.removeEventListener("scroll", n), a && e.removeEventListener("resize", n);
		}), d?.(), (e = p) == null || e.disconnect(), p = null, c && cancelAnimationFrame(m);
	};
}
var Da = Ei, Oa = Di, ka = bi, Aa = ki, ja = Ci, Ma = yi, Na = Oi, Pa = (e, t, n) => {
	let r = /* @__PURE__ */ new Map(), i = n ?? {}, a = {
		...Ca,
		...i.platform,
		_c: r
	};
	return vi(e, t, {
		...i,
		platform: a
	});
}, Fa = typeof document < "u" ? o.useLayoutEffect : function() {};
function Ia(e, t) {
	if (e === t) return !0;
	if (typeof e != typeof t) return !1;
	if (typeof e == "function" && e.toString() === t.toString()) return !0;
	let n, r, i;
	if (e && t && typeof e == "object") {
		if (Array.isArray(e)) {
			if (n = e.length, n !== t.length) return !1;
			for (r = n; r-- !== 0;) if (!Ia(e[r], t[r])) return !1;
			return !0;
		}
		if (i = Object.keys(e), n = i.length, n !== Object.keys(t).length) return !1;
		for (r = n; r-- !== 0;) if (!{}.hasOwnProperty.call(t, i[r])) return !1;
		for (r = n; r-- !== 0;) {
			let n = i[r];
			if (!(n === "_owner" && e.$$typeof) && !Ia(e[n], t[n])) return !1;
		}
		return !0;
	}
	return e !== e && t !== t;
}
function La(e) {
	return typeof window > "u" ? 1 : (e.ownerDocument.defaultView || window).devicePixelRatio || 1;
}
function Ra(e, t) {
	let n = La(e);
	return Math.round(t * n) / n;
}
function za(e) {
	let t = o.useRef(e);
	return Fa(() => {
		t.current = e;
	}), t;
}
function Ba(e) {
	e === void 0 && (e = {});
	let { placement: t = "bottom", strategy: n = "absolute", middleware: r = [], platform: i, elements: { reference: a, floating: s } = {}, transform: c = !0, whileElementsMounted: l, open: d } = e, [f, p] = o.useState({
		x: 0,
		y: 0,
		strategy: n,
		placement: t,
		middlewareData: {},
		isPositioned: !1
	}), [m, h] = o.useState(r);
	Ia(m, r) || h(r);
	let [g, _] = o.useState(null), [v, y] = o.useState(null), b = o.useCallback((e) => {
		e !== w.current && (w.current = e, _(e));
	}, []), x = o.useCallback((e) => {
		e !== T.current && (T.current = e, y(e));
	}, []), S = a || g, C = s || v, w = o.useRef(null), T = o.useRef(null), E = o.useRef(f), D = l != null, O = za(l), k = za(i), A = za(d), j = o.useCallback(() => {
		if (!w.current || !T.current) return;
		let e = {
			placement: t,
			strategy: n,
			middleware: m
		};
		k.current && (e.platform = k.current), Pa(w.current, T.current, e).then((e) => {
			let t = {
				...e,
				isPositioned: A.current !== !1
			};
			M.current && !Ia(E.current, t) && (E.current = t, u.flushSync(() => {
				p(t);
			}));
		});
	}, [
		m,
		t,
		n,
		k,
		A
	]);
	Fa(() => {
		d === !1 && E.current.isPositioned && (E.current.isPositioned = !1, p((e) => ({
			...e,
			isPositioned: !1
		})));
	}, [d]);
	let M = o.useRef(!1);
	Fa(() => (M.current = !0, () => {
		M.current = !1;
	}), []), Fa(() => {
		if (S && (w.current = S), C && (T.current = C), S && C) {
			if (O.current) return O.current(S, C, j);
			j();
		}
	}, [
		S,
		C,
		j,
		O,
		D
	]);
	let ee = o.useMemo(() => ({
		reference: w,
		floating: T,
		setReference: b,
		setFloating: x
	}), [b, x]), N = o.useMemo(() => ({
		reference: S,
		floating: C
	}), [S, C]), P = o.useMemo(() => {
		let e = {
			position: n,
			left: 0,
			top: 0
		};
		if (!N.floating) return e;
		let t = Ra(N.floating, f.x), r = Ra(N.floating, f.y);
		return c ? {
			...e,
			transform: "translate(" + t + "px, " + r + "px)",
			...La(N.floating) >= 1.5 && { willChange: "transform" }
		} : {
			position: n,
			left: t,
			top: r
		};
	}, [
		n,
		c,
		N.floating,
		f.x,
		f.y
	]);
	return o.useMemo(() => ({
		...f,
		update: j,
		refs: ee,
		elements: N,
		floatingStyles: P
	}), [
		f,
		j,
		ee,
		N,
		P
	]);
}
var Va = (e) => {
	function t(e) {
		return {}.hasOwnProperty.call(e, "current");
	}
	return {
		name: "arrow",
		options: e,
		fn(n) {
			let { element: r, padding: i } = typeof e == "function" ? e(n) : e;
			return r && t(r) ? r.current == null ? {} : Ma({
				element: r.current,
				padding: i
			}).fn(n) : r ? Ma({
				element: r,
				padding: i
			}).fn(n) : {};
		}
	};
}, Ha = (e, t) => {
	let n = Da(e);
	return {
		name: n.name,
		fn: n.fn,
		options: [e, t]
	};
}, Ua = (e, t) => {
	let n = Oa(e);
	return {
		name: n.name,
		fn: n.fn,
		options: [e, t]
	};
}, Wa = (e, t) => ({
	fn: Na(e).fn,
	options: [e, t]
}), Ga = (e, t) => {
	let n = ka(e);
	return {
		name: n.name,
		fn: n.fn,
		options: [e, t]
	};
}, Ka = (e, t) => {
	let n = Aa(e);
	return {
		name: n.name,
		fn: n.fn,
		options: [e, t]
	};
}, qa = (e, t) => {
	let n = ja(e);
	return {
		name: n.name,
		fn: n.fn,
		options: [e, t]
	};
}, Ja = (e, t) => {
	let n = Va(e);
	return {
		name: n.name,
		fn: n.fn,
		options: [e, t]
	};
}, Ya = Object.defineProperty, Xa = (e, t) => Ya(e, "name", {
	value: t,
	configurable: !0
}), Za = {
	Partial: "partial",
	Always: "always"
}, Qa = {
	Optimized: "optimized",
	Always: "always"
}, $a = "Popper", [eo, to] = /* @__PURE__ */ L($a), [no, ro] = eo($a), io = /* @__PURE__ */ Xa((e) => {
	let { __scopePopper: t, children: n } = e, [r, i] = o.useState(null), [a, c] = o.useState(void 0);
	return /* @__PURE__ */ (0, s.jsx)(no, {
		scope: t,
		anchor: r,
		onAnchorChange: i,
		placementState: a,
		setPlacementState: c,
		children: n
	});
}, "Popper"), ao = "PopperAnchor", oo = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Xa(function(e, t) {
	let { __scopePopper: n, virtualRef: r, ...i } = e, a = ro(ao, n), c = o.useRef(null), l = a.onAnchorChange, u = v(t, o.useCallback((e) => {
		c.current = e, e && l(e);
	}, [l])), d = o.useRef(null);
	o.useEffect(() => {
		if (!r) return;
		let e = d.current;
		d.current = r.current, e !== d.current && l(d.current);
	});
	let f = a.placementState && mo(a.placementState), p = f?.[0], m = f?.[1];
	return r ? null : /* @__PURE__ */ (0, s.jsx)(F.div, {
		"data-radix-popper-side": p,
		"data-radix-popper-align": m,
		...i,
		ref: u
	});
}, "PopperAnchor")), so = "PopperContent", [co, lo] = eo(so), uo = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Xa(function(e, t) {
	let { __scopePopper: n, side: r = "bottom", sideOffset: i = 0, align: a = "center", alignOffset: c = 0, arrowPadding: l = 0, avoidCollisions: u = !0, collisionBoundary: d = [], collisionPadding: f = 0, sticky: p = Za.Partial, hideWhenDetached: m = !1, updatePositionStrategy: h = Qa.Optimized, onPlaced: g, ..._ } = e, y = ro(so, n), [b, x] = o.useState(null), S = v(t, x), [C, w] = o.useState(null), T = Vr(C), E = T?.width ?? 0, D = T?.height ?? 0, O = r + (a === "center" ? "" : "-" + a), k = typeof f == "number" ? f : {
		top: 0,
		right: 0,
		bottom: 0,
		left: 0,
		...f
	}, A = Array.isArray(d) ? d : [d], j = A.length > 0, M = {
		padding: k,
		boundary: A.filter(fo),
		altBoundary: j
	}, { refs: ee, floatingStyles: N, placement: P, isPositioned: te, middlewareData: ne } = Ba({
		strategy: "fixed",
		placement: O,
		whileElementsMounted: /* @__PURE__ */ Xa((...e) => Ea(...e, { animationFrame: h === Qa.Always }), "whileElementsMounted"),
		elements: { reference: y.anchor },
		middleware: [
			Ha({
				mainAxis: i + D,
				alignmentAxis: c
			}),
			u && Ua({
				mainAxis: !0,
				crossAxis: !1,
				...p === Za.Partial ? { limiter: Wa() } : {},
				...M
			}),
			u && Ga({ ...M }),
			Ka({
				...M,
				apply: /* @__PURE__ */ Xa(({ elements: e, rects: t, availableWidth: n, availableHeight: r }) => {
					let { width: i, height: a } = t.reference, o = e.floating.style;
					o.setProperty("--radix-popper-available-width", `${n}px`), o.setProperty("--radix-popper-available-height", `${r}px`), o.setProperty("--radix-popper-anchor-width", `${i}px`), o.setProperty("--radix-popper-anchor-height", `${a}px`);
				}, "apply")
			}),
			C && Ja({
				element: C,
				padding: l
			}),
			po({
				arrowWidth: E,
				arrowHeight: D
			}),
			m && qa(j ? {
				strategy: "referenceHidden",
				...M
			} : {
				strategy: "referenceHidden",
				padding: M.padding,
				altBoundary: M.altBoundary
			})
		]
	}), re = y.setPlacementState;
	R(() => (re(P), () => {
		re(void 0);
	}), [P, re]);
	let [ie, I] = mo(P), ae = st(g);
	R(() => {
		te && ae?.();
	}, [te, ae]);
	let L = ne.arrow?.x, oe = ne.arrow?.y, se = ne.arrow?.centerOffset !== 0, [z, ce] = o.useState();
	return R(() => {
		b && ce(window.getComputedStyle(b).zIndex);
	}, [b]), /* @__PURE__ */ (0, s.jsx)("div", {
		ref: ee.setFloating,
		"data-radix-popper-content-wrapper": "",
		style: {
			...N,
			transform: te ? N.transform : "translate(0, -200%)",
			minWidth: "max-content",
			zIndex: z,
			"--radix-popper-transform-origin": [ne.transformOrigin?.x, ne.transformOrigin?.y].join(" "),
			...ne.hide?.referenceHidden && {
				visibility: "hidden",
				pointerEvents: "none"
			}
		},
		dir: e.dir,
		children: /* @__PURE__ */ (0, s.jsx)(co, {
			scope: n,
			placedSide: ie,
			placedAlign: I,
			onArrowChange: w,
			arrowX: L,
			arrowY: oe,
			shouldHideArrow: se,
			children: /* @__PURE__ */ (0, s.jsx)(F.div, {
				"data-side": ie,
				"data-align": I,
				..._,
				ref: S,
				style: {
					..._.style,
					animation: te ? _.style?.animation : "none"
				}
			})
		})
	});
}, "PopperContent"));
function fo(e) {
	return e !== null;
}
Xa(fo, "isNotNull");
var po = /* @__PURE__ */ Xa((e) => ({
	name: "transformOrigin",
	options: e,
	fn(t) {
		let { placement: n, rects: r, middlewareData: i } = t, a = i.arrow?.centerOffset !== 0, o = a ? 0 : e.arrowWidth, s = a ? 0 : e.arrowHeight, [c, l] = mo(n), u = {
			start: "0%",
			center: "50%",
			end: "100%"
		}[l], d = (i.arrow?.x ?? 0) + o / 2, f = (i.arrow?.y ?? 0) + s / 2, p = "", m = "";
		return c === "bottom" ? (p = a ? u : `${d}px`, m = `${-s}px`) : c === "top" ? (p = a ? u : `${d}px`, m = `${r.floating.height + s}px`) : c === "right" ? (p = `${-s}px`, m = a ? u : `${f}px`) : c === "left" && (p = `${r.floating.width + s}px`, m = a ? u : `${f}px`), { data: {
			x: p,
			y: m
		} };
	}
}), "transformOrigin");
function mo(e) {
	let [t, n = "center"] = e.split("-");
	return [t, n];
}
Xa(mo, "getSideAndAlignFromPlacement");
// node_modules/@radix-ui/react-use-is-hydrated/dist/index.mjs
var ho = Object.defineProperty, go = (e, t) => ho(e, "name", {
	value: t,
	configurable: !0
}), _o = !1;
function vo() {
	let [e, t] = o.useState(_o);
	return o.useEffect(() => {
		_o || (_o = !0, t(!0));
	}, []), e;
}
go(vo, "useIsHydrated");
var yo = o.useSyncExternalStore;
function bo() {
	return () => {};
}
go(bo, "subscribe");
function xo() {
	return yo(bo, () => !0, () => !1);
}
go(xo, "useIsHydratedModern");
var So = typeof yo == "function" ? xo : vo, Co = Object.defineProperty, wo = (e, t) => Co(e, "name", {
	value: t,
	configurable: !0
}), To = "rovingFocusGroup.onEntryFocus", Eo = {
	bubbles: !1,
	cancelable: !0
}, Do = "RovingFocusGroup", [Oo, ko, Ao] = /* @__PURE__ */ ce(Do), [jo, Mo] = /* @__PURE__ */ L(Do, [Ao]), No = {
	Vertical: "vertical",
	Horizontal: "horizontal"
}, Po = {
	LTR: "ltr",
	RTL: "rtl"
}, [Fo, Io] = jo(Do), Lo = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ wo(function(e, t) {
	return /* @__PURE__ */ (0, s.jsx)(Oo.Provider, {
		scope: e.__scopeRovingFocusGroup,
		children: /* @__PURE__ */ (0, s.jsx)(Oo.Slot, {
			scope: e.__scopeRovingFocusGroup,
			children: /* @__PURE__ */ (0, s.jsx)(Ro, {
				...e,
				ref: t
			})
		})
	});
}, "RovingFocusGroup")), Ro = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ wo(function(e, t) {
	let { __scopeRovingFocusGroup: n, orientation: r, loop: i = !1, dir: a, currentTabStopId: c, defaultCurrentTabStopId: l, onCurrentTabStopIdChange: u, onEntryFocus: d, preventScrollOnEntryFocus: f = !1, ...p } = e, m = o.useRef(null), h = v(t, m), g = rt(a), [_, y] = Fe({
		prop: c,
		defaultProp: l ?? null,
		onChange: u,
		caller: Do
	}), [b, x] = o.useState(!1), S = st(d), C = ko(n), w = o.useRef(!1), [T, E] = o.useState(0);
	return o.useEffect(() => {
		let e = m.current;
		if (e) return e.addEventListener(To, S), () => e.removeEventListener(To, S);
	}, [S]), /* @__PURE__ */ (0, s.jsx)(Fo, {
		scope: n,
		orientation: r,
		dir: g,
		loop: i,
		currentTabStopId: _,
		onItemFocus: o.useCallback((e) => y(e), [y]),
		onItemShiftTab: o.useCallback(() => x(!0), []),
		onFocusableItemAdd: o.useCallback(() => E((e) => e + 1), []),
		onFocusableItemRemove: o.useCallback(() => E((e) => e - 1), []),
		children: /* @__PURE__ */ (0, s.jsx)(F.div, {
			tabIndex: b || T === 0 ? -1 : 0,
			"data-orientation": r,
			...p,
			ref: h,
			style: {
				outline: "none",
				...e.style
			},
			onMouseDown: B(e.onMouseDown, () => {
				w.current = !0;
			}),
			onFocus: B(e.onFocus, (e) => {
				let t = !w.current;
				if (e.target === e.currentTarget && t && !b) {
					let t = new CustomEvent(To, Eo);
					if (e.currentTarget.dispatchEvent(t), !t.defaultPrevented) {
						let e = C().filter((e) => e.focusable);
						Wo([
							e.find((e) => e.active),
							e.find((e) => e.id === _),
							...e
						].filter(Boolean).map((e) => e.ref.current), f);
					}
				}
				w.current = !1;
			}),
			onBlur: B(e.onBlur, () => x(!1))
		})
	});
}, "RovingFocusGroupImpl")), zo = "RovingFocusGroupItem", Bo = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ wo(function(e, t) {
	let { __scopeRovingFocusGroup: n, focusable: r = !0, active: i = !1, tabStopId: a, children: c, ...l } = e, u = Qe(), d = a || u, f = Io(zo, n), p = f.currentTabStopId === d, m = ko(n), { onFocusableItemAdd: h, onFocusableItemRemove: g, currentTabStopId: _ } = f, v = So();
	return R(() => {
		if (v && r) return h(), () => g();
	}, [
		v,
		r,
		h,
		g
	]), o.useEffect(() => {
		if (!v && r) return h(), () => g();
	}, [
		v,
		r,
		h,
		g
	]), /* @__PURE__ */ (0, s.jsx)(Oo.ItemSlot, {
		scope: n,
		id: d,
		focusable: r,
		active: i,
		children: /* @__PURE__ */ (0, s.jsx)(F.span, {
			tabIndex: p ? 0 : -1,
			"data-orientation": f.orientation,
			...l,
			ref: t,
			onMouseDown: B(e.onMouseDown, (e) => {
				r ? f.onItemFocus(d) : e.preventDefault();
			}),
			onFocus: B(e.onFocus, () => f.onItemFocus(d)),
			onKeyDown: B(e.onKeyDown, (e) => {
				if (e.key === "Tab" && e.shiftKey) {
					f.onItemShiftTab();
					return;
				}
				if (e.target !== e.currentTarget) return;
				let t = Uo(e, f.orientation, f.dir);
				if (t !== void 0) {
					if (e.metaKey || e.ctrlKey || e.altKey || e.shiftKey) return;
					e.preventDefault();
					let n = m().filter((e) => e.focusable).map((e) => e.ref.current);
					if (t === "last") n.reverse();
					else if (t === "prev" || t === "next") {
						t === "prev" && n.reverse();
						let r = n.indexOf(e.currentTarget);
						n = f.loop ? Go(n, r + 1) : n.slice(r + 1);
					}
					setTimeout(() => Wo(n));
				}
			}),
			children: typeof c == "function" ? c({
				isCurrentTabStop: p,
				hasTabStop: _ != null
			}) : c
		})
	});
}, "RovingFocusGroupItem")), Vo = {
	ArrowLeft: "prev",
	ArrowUp: "prev",
	ArrowRight: "next",
	ArrowDown: "next",
	PageUp: "first",
	Home: "first",
	PageDown: "last",
	End: "last"
};
function Ho(e, t) {
	return t === Po.RTL ? e === "ArrowLeft" ? "ArrowRight" : e === "ArrowRight" ? "ArrowLeft" : e : e;
}
wo(Ho, "getDirectionAwareKey");
function Uo(e, t, n) {
	let r = Ho(e.key, n);
	if (!(t === No.Vertical && ["ArrowLeft", "ArrowRight"].includes(r)) && !(t === No.Horizontal && ["ArrowUp", "ArrowDown"].includes(r))) return Vo[r];
}
wo(Uo, "getFocusIntent");
function Wo(e, t = !1) {
	let n = document.activeElement;
	for (let r of e) if (r === n || (r.focus({ preventScroll: t }), document.activeElement !== n)) return;
}
wo(Wo, "focusFirst");
function Go(e, t) {
	return e.map((n, r) => e[(t + r) % e.length]);
}
wo(Go, "wrapArray");
// node_modules/@radix-ui/react-menu/dist/index.mjs
var Ko = Object.defineProperty, Q = (e, t) => Ko(e, "name", {
	value: t,
	configurable: !0
}), qo = ["Enter", " "], Jo = [
	"ArrowDown",
	"PageUp",
	"Home"
], Yo = [
	"ArrowUp",
	"PageDown",
	"End"
], Xo = [...Jo, ...Yo];
[...qo], [...qo];
var Zo = "Menu", [Qo, $o, es] = /* @__PURE__ */ ce(Zo), [ts, ns] = /* @__PURE__ */ L(Zo, [
	es,
	to,
	Mo
]), rs = to(), is = Mo(), [as, os] = ts(Zo), [ss, cs] = ts(Zo), ls = /* @__PURE__ */ Q((e) => {
	let { __scopeMenu: t, open: n = !1, children: r, dir: i, onOpenChange: a, modal: c = !0 } = e, l = rs(t), [u, d] = o.useState(null), f = o.useRef(!1), p = st(a), m = rt(i);
	return o.useEffect(() => {
		let e = /* @__PURE__ */ Q(() => {
			f.current = !0, document.addEventListener("pointerdown", t, {
				capture: !0,
				once: !0
			}), document.addEventListener("pointermove", t, {
				capture: !0,
				once: !0
			});
		}, "handleKeyDown"), t = /* @__PURE__ */ Q(() => f.current = !1, "handlePointer");
		return document.addEventListener("keydown", e, { capture: !0 }), () => {
			document.removeEventListener("keydown", e, { capture: !0 }), document.removeEventListener("pointerdown", t, { capture: !0 }), document.removeEventListener("pointermove", t, { capture: !0 });
		};
	}, []), o.useEffect(() => {
		if (!n) return;
		let e = /* @__PURE__ */ Q(() => p(!1), "handleBlur");
		return window.addEventListener("blur", e), () => window.removeEventListener("blur", e);
	}, [n, p]), /* @__PURE__ */ (0, s.jsx)(io, {
		...l,
		children: /* @__PURE__ */ (0, s.jsx)(as, {
			scope: t,
			open: n,
			onOpenChange: p,
			content: u,
			onContentChange: d,
			children: /* @__PURE__ */ (0, s.jsx)(ss, {
				scope: t,
				onClose: o.useCallback(() => p(!1), [p]),
				isUsingKeyboardRef: f,
				dir: m,
				modal: c,
				children: r
			})
		})
	});
}, "Menu"), us = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Q(function(e, t) {
	let { __scopeMenu: n, ...r } = e, i = rs(n);
	return /* @__PURE__ */ (0, s.jsx)(oo, {
		...i,
		...r,
		ref: t
	});
}, "MenuAnchor")), ds = "MenuPortal", [fs, ps] = ts(ds, { forceMount: void 0 }), ms = /* @__PURE__ */ Q((e) => {
	let { __scopeMenu: t, forceMount: n, children: r, container: i } = e, a = os(ds, t);
	return /* @__PURE__ */ (0, s.jsx)(fs, {
		scope: t,
		forceMount: n,
		children: /* @__PURE__ */ (0, s.jsx)(He, {
			present: n || a.open,
			children: /* @__PURE__ */ (0, s.jsx)(Vt, {
				asChild: !0,
				container: i,
				children: r
			})
		})
	});
}, "MenuPortal"), hs = "MenuContent", [gs, _s] = ts(hs), vs = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Q(function(e, t) {
	let n = ps(hs, e.__scopeMenu), { forceMount: r = n.forceMount, ...i } = e, a = os(hs, e.__scopeMenu), o = cs(hs, e.__scopeMenu);
	return /* @__PURE__ */ (0, s.jsx)(Qo.Provider, {
		scope: e.__scopeMenu,
		children: /* @__PURE__ */ (0, s.jsx)(He, {
			present: r || a.open,
			children: /* @__PURE__ */ (0, s.jsx)(Qo.Slot, {
				scope: e.__scopeMenu,
				children: o.modal ? /* @__PURE__ */ (0, s.jsx)(ys, {
					...i,
					ref: t
				}) : /* @__PURE__ */ (0, s.jsx)(bs, {
					...i,
					ref: t
				})
			})
		})
	});
}, "MenuContent")), ys = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Q(function(e, t) {
	let n = os(hs, e.__scopeMenu), r = o.useRef(null), i = v(t, r);
	return o.useEffect(() => {
		let e = r.current;
		if (e) return dr(e);
	}, []), /* @__PURE__ */ (0, s.jsx)(Ss, {
		...e,
		ref: i,
		trapFocus: n.open,
		disableOutsidePointerEvents: n.open,
		disableOutsideScroll: !0,
		onFocusOutside: B(e.onFocusOutside, (e) => e.preventDefault(), { checkForDefaultPrevented: !1 }),
		onDismiss: () => n.onOpenChange(!1)
	});
}, "MenuRootContentModal")), bs = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Q(function(e, t) {
	let n = os(hs, e.__scopeMenu);
	return /* @__PURE__ */ (0, s.jsx)(Ss, {
		...e,
		ref: t,
		trapFocus: !1,
		disableOutsidePointerEvents: !1,
		disableOutsideScroll: !1,
		onDismiss: () => n.onOpenChange(!1)
	});
}, "MenuRootContentNonModal")), xs = /* @__PURE__ */ x("MenuContent.ScrollLock"), Ss = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Q(function(e, t) {
	let { __scopeMenu: n, loop: r = !1, trapFocus: i, onOpenAutoFocus: a, onCloseAutoFocus: c, disableOutsidePointerEvents: l, onEntryFocus: u, onEscapeKeyDown: d, onPointerDownOutside: f, onFocusOutside: p, onInteractOutside: m, onDismiss: h, disableOutsideScroll: g, ..._ } = e, y = os(hs, n), b = cs(hs, n), x = rs(n), S = is(n), C = $o(n), [w, T] = o.useState(null), E = o.useRef(null), [D, O] = o.useState(null);
	kt(D);
	let { nodes: k, registry: A } = Ot(), j = !!(i || g), M = v(t, E, y.onContentChange, O), ee = o.useRef(0), N = o.useRef(""), P = o.useRef(0), te = o.useRef(null), ne = o.useRef("right"), F = o.useRef(0), re = o.useMemo(() => g ? [E, ...k.map((e) => ({ current: e }))] : [], [
		E,
		k,
		g
	]), ie = g ? nr : o.Fragment, I = g ? {
		as: xs,
		allowPinchZoom: !0,
		shards: re
	} : void 0, ae = /* @__PURE__ */ Q((e) => {
		let t = N.current + e, n = C().filter((e) => !e.disabled), r = document.activeElement, i = n.find((e) => e.ref.current === r)?.textValue, a = Rs(n.map((e) => e.textValue), t, i), o = n.find((e) => e.textValue === a)?.ref.current;
		function s(e) {
			N.current = e, window.clearTimeout(ee.current), e !== "" && (ee.current = window.setTimeout(() => s(""), 1e3));
		}
		Q(s, "updateSearch"), s(t), o && setTimeout(() => o.focus());
	}, "handleTypeaheadSearch");
	o.useEffect(() => () => window.clearTimeout(ee.current), []), qt();
	let L = o.useCallback((e) => ne.current === te.current?.side && Bs(e, te.current?.area), []);
	return /* @__PURE__ */ (0, s.jsx)(gs, {
		scope: n,
		searchRef: N,
		onItemEnter: o.useCallback((e) => {
			L(e) && e.preventDefault();
		}, [L]),
		onItemLeave: o.useCallback((e) => {
			L(e) || (E.current?.focus(), T(null));
		}, [L]),
		onTriggerLeave: o.useCallback((e) => {
			L(e) && e.preventDefault();
		}, [L]),
		pointerGraceTimerRef: P,
		onPointerGraceIntentChange: o.useCallback((e) => {
			te.current = e;
		}, []),
		children: /* @__PURE__ */ (0, s.jsx)(Dt, {
			registry: j ? A : null,
			children: /* @__PURE__ */ (0, s.jsx)(ie, {
				...I,
				children: /* @__PURE__ */ (0, s.jsx)(Tt, {
					asChild: !0,
					trapped: i,
					branches: k,
					onMountAutoFocus: B(a, (e) => {
						e.preventDefault(), E.current?.focus({ preventScroll: !0 });
					}),
					onUnmountAutoFocus: c,
					children: /* @__PURE__ */ (0, s.jsx)(mt, {
						asChild: !0,
						disableOutsidePointerEvents: l,
						onEscapeKeyDown: d,
						onPointerDownOutside: f,
						onFocusOutside: p,
						onInteractOutside: m,
						onDismiss: h,
						children: /* @__PURE__ */ (0, s.jsx)(Lo, {
							asChild: !0,
							...S,
							dir: b.dir,
							orientation: "vertical",
							loop: r,
							currentTabStopId: w,
							onCurrentTabStopIdChange: T,
							onEntryFocus: B(u, (e) => {
								b.isUsingKeyboardRef.current || e.preventDefault();
							}),
							preventScrollOnEntryFocus: !0,
							children: /* @__PURE__ */ (0, s.jsx)(uo, {
								role: "menu",
								"aria-orientation": "vertical",
								"data-state": Ns(y.open),
								"data-radix-menu-content": "",
								dir: b.dir,
								...x,
								..._,
								ref: M,
								style: {
									outline: "none",
									..._.style
								},
								onKeyDown: B(_.onKeyDown, (e) => {
									let t = e.target.closest("[data-radix-menu-content]") === e.currentTarget, n = e.ctrlKey || e.altKey || e.metaKey, r = e.key.length === 1;
									t && (e.key === "Tab" && e.preventDefault(), !n && r && ae(e.key));
									let i = E.current;
									if (e.target !== i || !Xo.includes(e.key)) return;
									e.preventDefault();
									let a = C().filter((e) => !e.disabled).map((e) => e.ref.current);
									Yo.includes(e.key) && a.reverse(), Is(a);
								}),
								onBlur: B(e.onBlur, (e) => {
									e.currentTarget.contains(e.target) || (window.clearTimeout(ee.current), N.current = "");
								}),
								onPointerMove: B(e.onPointerMove, Vs((e) => {
									let t = e.target, n = F.current !== e.clientX;
									if (e.currentTarget.contains(t) && n) {
										let t = e.clientX > F.current ? "right" : "left";
										ne.current = t, F.current = e.clientX;
									}
								}))
							})
						})
					})
				})
			})
		})
	});
}, "MenuContentImpl")), Cs = "MenuItem", ws = "menu.itemSelect", Ts = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Q(function(e, t) {
	let { disabled: n = !1, onSelect: r, ...i } = e, a = o.useRef(null), c = cs(Cs, e.__scopeMenu), l = _s(Cs, e.__scopeMenu), u = v(t, a), d = o.useRef(!1), f = /* @__PURE__ */ Q(() => {
		let e = a.current;
		if (!n && e) {
			let t = new CustomEvent(ws, {
				bubbles: !0,
				cancelable: !0
			});
			e.addEventListener(ws, (e) => r?.(e), { once: !0 }), re(e, t), t.defaultPrevented ? d.current = !1 : c.onClose();
		}
	}, "handleSelect");
	return /* @__PURE__ */ (0, s.jsx)(Es, {
		...i,
		ref: u,
		disabled: n,
		onClick: B(e.onClick, f),
		onPointerDown: (t) => {
			e.onPointerDown?.(t), d.current = !0;
		},
		onPointerUp: B(e.onPointerUp, (e) => {
			d.current || e.currentTarget?.click();
		}),
		onKeyDown: B(e.onKeyDown, (e) => {
			n || e.target !== e.currentTarget || (l.searchRef.current === "" || e.key !== " ") && qo.includes(e.key) && (e.currentTarget.click(), e.preventDefault());
		})
	});
}, "MenuItem")), Es = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Q(function(e, t) {
	let { __scopeMenu: n, disabled: r = !1, textValue: i, ...a } = e, c = _s(Cs, n), l = is(n), u = o.useRef(null), d = v(t, u), [f, p] = o.useState(!1), [m, h] = o.useState("");
	return o.useEffect(() => {
		let e = u.current;
		e && h((e.textContent ?? "").trim());
	}, [a.children]), /* @__PURE__ */ (0, s.jsx)(Qo.ItemSlot, {
		scope: n,
		disabled: r,
		textValue: i ?? m,
		children: /* @__PURE__ */ (0, s.jsx)(Bo, {
			asChild: !0,
			...l,
			focusable: !r,
			children: /* @__PURE__ */ (0, s.jsx)(F.div, {
				role: "menuitem",
				"data-highlighted": f ? "" : void 0,
				"aria-disabled": r || void 0,
				"data-disabled": r ? "" : void 0,
				...a,
				ref: d,
				onPointerMove: B(e.onPointerMove, Vs((e) => {
					r ? c.onItemLeave(e) : (c.onItemEnter(e), e.defaultPrevented || e.currentTarget.focus({ preventScroll: !0 }));
				})),
				onPointerLeave: B(e.onPointerLeave, Vs((e) => c.onItemLeave(e))),
				onFocus: B(e.onFocus, () => p(!0)),
				onBlur: B(e.onBlur, () => p(!1))
			})
		})
	});
}, "MenuItemImpl")), [Ds, Os] = ts("MenuRadioGroup", {
	value: void 0,
	onValueChange: /* @__PURE__ */ Q(() => {}, "onValueChange")
}), [ks, As] = ts("MenuItemIndicator", { checked: !1 }), [js, Ms] = ts("MenuSub");
function Ns(e) {
	return e ? "open" : "closed";
}
Q(Ns, "getOpenState");
function Ps(e) {
	return e === "indeterminate";
}
Q(Ps, "isIndeterminate");
function Fs(e) {
	return Ps(e) ? "indeterminate" : e ? "checked" : "unchecked";
}
Q(Fs, "getCheckedState");
function Is(e) {
	let t = document.activeElement;
	for (let n of e) if (n === t || (n.focus(), document.activeElement !== t)) return;
}
Q(Is, "focusFirst");
function Ls(e, t) {
	return e.map((n, r) => e[(t + r) % e.length]);
}
Q(Ls, "wrapArray");
function Rs(e, t, n) {
	let r = t.length > 1 && Array.from(t).every((e) => e === t[0]) ? t[0] : t, i = n ? e.indexOf(n) : -1, a = Ls(e, Math.max(i, 0));
	r.length === 1 && (a = a.filter((e) => e !== n));
	let o = a.find((e) => e.toLowerCase().startsWith(r.toLowerCase()));
	return o === n ? void 0 : o;
}
Q(Rs, "getNextMatch");
function zs(e, t) {
	let { x: n, y: r } = e, i = !1;
	for (let e = 0, a = t.length - 1; e < t.length; a = e++) {
		let o = t[e], s = t[a], c = o.x, l = o.y, u = s.x, d = s.y;
		l > r != d > r && n < (u - c) * (r - l) / (d - l) + c && (i = !i);
	}
	return i;
}
Q(zs, "isPointInPolygon");
function Bs(e, t) {
	return t ? zs({
		x: e.clientX,
		y: e.clientY
	}, t) : !1;
}
Q(Bs, "isPointerInGraceArea");
function Vs(e) {
	return (t) => t.pointerType === "mouse" ? e(t) : void 0;
}
Q(Vs, "whenMouse");
// node_modules/@radix-ui/react-dropdown-menu/dist/index.mjs
var Hs = Object.defineProperty, Us = (e, t) => Hs(e, "name", {
	value: t,
	configurable: !0
}), Ws = "DropdownMenu", [Gs, Ks] = /* @__PURE__ */ L(Ws, [ns]), qs = ns(), [Js, Ys] = Gs(Ws), Xs = /* @__PURE__ */ Us((e) => {
	let { __scopeDropdownMenu: t, children: n, dir: r, open: i, defaultOpen: a, onOpenChange: c, modal: l = !0 } = e, u = qs(t), d = o.useRef(null), [f, p] = Fe({
		prop: i,
		defaultProp: a ?? !1,
		onChange: c,
		caller: Ws
	});
	return /* @__PURE__ */ (0, s.jsx)(Js, {
		scope: t,
		triggerId: Qe(),
		triggerRef: d,
		contentId: Qe(),
		open: f,
		onOpenChange: p,
		onOpenToggle: o.useCallback(() => p((e) => !e), [p]),
		modal: l,
		children: /* @__PURE__ */ (0, s.jsx)(ls, {
			...u,
			open: f,
			onOpenChange: p,
			dir: r,
			modal: l,
			children: n
		})
	});
}, "DropdownMenu"), Zs = "DropdownMenuTrigger", Qs = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Us(function(e, t) {
	let { __scopeDropdownMenu: n, disabled: r = !1, ...i } = e, a = Ys(Zs, n), o = qs(n), c = v(t, a.triggerRef);
	return /* @__PURE__ */ (0, s.jsx)(us, {
		asChild: !0,
		...o,
		children: /* @__PURE__ */ (0, s.jsx)(F.button, {
			type: "button",
			id: a.triggerId,
			"aria-haspopup": "menu",
			"aria-expanded": a.open,
			"aria-controls": a.open ? a.contentId : void 0,
			"data-state": a.open ? "open" : "closed",
			"data-disabled": r ? "" : void 0,
			disabled: r,
			...i,
			ref: c,
			onPointerDown: B(e.onPointerDown, (e) => {
				!r && e.button === 0 && e.ctrlKey === !1 && (a.onOpenToggle(), a.open || e.preventDefault());
			}),
			onKeyDown: B(e.onKeyDown, (e) => {
				r || (["Enter", " "].includes(e.key) && a.onOpenToggle(), e.key === "ArrowDown" && a.onOpenChange(!0), [
					"Enter",
					" ",
					"ArrowDown"
				].includes(e.key) && e.preventDefault());
			})
		})
	});
}, "DropdownMenuTrigger")), $s = /* @__PURE__ */ Us((e) => {
	let { __scopeDropdownMenu: t, ...n } = e, r = qs(t);
	return /* @__PURE__ */ (0, s.jsx)(ms, {
		...r,
		...n
	});
}, "DropdownMenuPortal"), ec = "DropdownMenuContent", tc = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Us(function(e, t) {
	let { __scopeDropdownMenu: n, ...r } = e, i = Ys(ec, n), a = qs(n), c = o.useRef(!1);
	return /* @__PURE__ */ (0, s.jsx)(vs, {
		id: i.contentId,
		"aria-labelledby": i.triggerId,
		...a,
		...r,
		ref: t,
		onCloseAutoFocus: B(e.onCloseAutoFocus, (e) => {
			c.current || i.triggerRef.current?.focus(), c.current = !1, e.preventDefault();
		}),
		onInteractOutside: B(e.onInteractOutside, (e) => {
			let t = e.detail.originalEvent, n = t.button === 0 && t.ctrlKey === !0, r = t.button === 2 || n;
			(!i.modal || r) && (c.current = !0);
		}),
		style: {
			...e.style,
			"--radix-dropdown-menu-content-transform-origin": "var(--radix-popper-transform-origin)",
			"--radix-dropdown-menu-content-available-width": "var(--radix-popper-available-width)",
			"--radix-dropdown-menu-content-available-height": "var(--radix-popper-available-height)",
			"--radix-dropdown-menu-trigger-width": "var(--radix-popper-anchor-width)",
			"--radix-dropdown-menu-trigger-height": "var(--radix-popper-anchor-height)"
		}
	});
}, "DropdownMenuContent")), nc = /* @__PURE__ */ o.forwardRef(/* @__PURE__ */ Us(function(e, t) {
	let { __scopeDropdownMenu: n, ...r } = e, i = qs(n);
	return /* @__PURE__ */ (0, s.jsx)(Ts, {
		...i,
		...r,
		ref: t
	});
}, "DropdownMenuItem")), $ = {
	application: "_application_c0l5u_1",
	quickTrigger: "_quickTrigger_c0l5u_335",
	navigationTrigger: "_navigationTrigger_c0l5u_336",
	overlay: "_overlay_c0l5u_364",
	command: "_command_c0l5u_370",
	commandHeading: "_commandHeading_c0l5u_386",
	commandDescription: "_commandDescription_c0l5u_396",
	commandSearch: "_commandSearch_c0l5u_401",
	commandItems: "_commandItems_c0l5u_416",
	menu: "_menu_c0l5u_438",
	menuItem: "_menuItem_c0l5u_449"
}, rc = [
	{
		name: "New application",
		target: "#new-branch"
	},
	{
		name: "All applications",
		target: "[data-filter=\"all\"]"
	},
	{
		name: "In progress",
		target: "[data-filter=\"running\"]"
	},
	{
		name: "Needs review",
		target: "[data-filter=\"review\"]"
	},
	{
		name: "Needs attention",
		target: "[data-filter=\"failed\"]"
	},
	{
		name: "Import jobs",
		target: "#open-jobenu"
	},
	{
		name: "Activity & support",
		target: "#show-activity"
	}
];
function ic(e) {
	requestAnimationFrame(() => {
		if (e.startsWith("[data-filter") || e === "#open-jobenu") {
			let t = document.querySelector("#workspace");
			if (t && !t.hidden && (document.querySelector("#back")?.click(), !t.hidden)) return;
			let n = document.querySelector("#jobenu-import");
			n && !n.hidden && e !== "#open-jobenu" && document.querySelector("#jobenu-back")?.click();
		}
		let t = document.querySelector(e);
		t && !t.disabled && t.click();
	});
}
function ac() {
	let [e, t] = (0, o.useState)(document.documentElement.dataset.theme || "light");
	(0, o.useEffect)(() => {
		let e = matchMedia("(prefers-color-scheme: dark)"), n = () => {
			let n = null;
			try {
				n = localStorage.getItem("vita-tree-theme");
			} catch {}
			n && n !== "system" || t(e.matches ? "dark" : "light");
		};
		return e.addEventListener("change", n), () => e.removeEventListener("change", n);
	}, []), (0, o.useEffect)(() => {
		document.documentElement.dataset.theme = e;
	}, [e]);
	let n = `Switch to ${e === "dark" ? "light" : "dark"} mode`;
	return /* @__PURE__ */ (0, s.jsx)("button", {
		id: "theme",
		type: "button",
		className: "theme-toggle",
		"aria-label": n,
		title: n,
		onClick: () => {
			let n = e === "dark" ? "light" : "dark";
			try {
				localStorage.setItem("vita-tree-theme", n);
			} catch {}
			t(n);
		},
		children: /* @__PURE__ */ (0, s.jsx)("svg", {
			className: e === "dark" ? "theme-moon" : "theme-sun",
			viewBox: "0 0 24 24",
			"aria-hidden": "true",
			children: e === "dark" ? /* @__PURE__ */ (0, s.jsx)("path", { d: "M20.8 13A9 9 0 0 1 11 3.2 9 9 0 1 0 20.8 13Z" }) : /* @__PURE__ */ (0, s.jsxs)(s.Fragment, { children: [/* @__PURE__ */ (0, s.jsx)("circle", {
				cx: "12",
				cy: "12",
				r: "4"
			}), /* @__PURE__ */ (0, s.jsx)("path", { d: "M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" })] })
		})
	});
}
function oc() {
	let [e, t] = (0, o.useState)(!1), [n, r] = (0, o.useState)(""), i = (0, o.useRef)(null);
	return (0, o.useEffect)(() => {
		let e = (e) => {
			if (!(e.ctrlKey || e.metaKey) || e.key.toLowerCase() !== "k" || document.querySelector("dialog[open]")) return;
			let n = e.target;
			n instanceof Element && n.closest("input,textarea,[contenteditable=\"true\"],.cm-editor") || (e.preventDefault(), t((e) => !e), r(""));
		};
		return addEventListener("keydown", e), () => removeEventListener("keydown", e);
	}, []), /* @__PURE__ */ (0, s.jsxs)(_r, {
		open: e,
		onOpenChange: (e) => {
			t(e), e && r("");
		},
		children: [/* @__PURE__ */ (0, s.jsx)(yr, {
			asChild: !0,
			children: /* @__PURE__ */ (0, s.jsxs)("button", {
				type: "button",
				className: $.quickTrigger,
				"aria-label": "Quick actions",
				children: [/* @__PURE__ */ (0, s.jsx)("span", { children: "Quick actions" }), /* @__PURE__ */ (0, s.jsx)("kbd", { children: "Ctrl K" })]
			})
		}), /* @__PURE__ */ (0, s.jsxs)(Cr, { children: [/* @__PURE__ */ (0, s.jsx)(Tr, { className: $.overlay }), /* @__PURE__ */ (0, s.jsxs)(kr, {
			className: $.command,
			onOpenAutoFocus: (e) => {
				e.preventDefault(), i.current?.focus();
			},
			children: [
				/* @__PURE__ */ (0, s.jsxs)("div", {
					className: $.commandHeading,
					children: [/* @__PURE__ */ (0, s.jsx)(Nr, { children: "Quick actions" }), /* @__PURE__ */ (0, s.jsx)(Ir, {
						"aria-label": "Close quick actions",
						children: "Close"
					})]
				}),
				/* @__PURE__ */ (0, s.jsx)(Pr, {
					className: $.commandDescription,
					children: "Jump to an application task."
				}),
				/* @__PURE__ */ (0, s.jsxs)("label", {
					className: $.commandSearch,
					children: ["Find an action", /* @__PURE__ */ (0, s.jsx)("input", {
						ref: i,
						value: n,
						onChange: (e) => r(e.target.value),
						placeholder: "Search actions…"
					})]
				}),
				/* @__PURE__ */ (0, s.jsx)("div", {
					className: $.commandItems,
					children: rc.filter((e) => e.name.toLowerCase().includes(n.toLowerCase())).map((e) => /* @__PURE__ */ (0, s.jsxs)("button", {
						type: "button",
						onClick: () => {
							t(!1), ic(e.target);
						},
						children: [e.name, /* @__PURE__ */ (0, s.jsx)("span", {
							"aria-hidden": "true",
							children: "→"
						})]
					}, e.target))
				})
			]
		})] })]
	});
}
function sc() {
	return /* @__PURE__ */ (0, s.jsxs)(Xs, { children: [/* @__PURE__ */ (0, s.jsx)(Qs, {
		asChild: !0,
		children: /* @__PURE__ */ (0, s.jsxs)("button", {
			type: "button",
			className: $.navigationTrigger,
			"aria-label": "Navigation",
			children: [/* @__PURE__ */ (0, s.jsx)("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true",
				children: /* @__PURE__ */ (0, s.jsx)("path", { d: "M4 6h16M4 12h16M4 18h16" })
			}), /* @__PURE__ */ (0, s.jsx)("span", { children: "Menu" })]
		})
	}), /* @__PURE__ */ (0, s.jsx)($s, { children: /* @__PURE__ */ (0, s.jsx)(tc, {
		className: $.menu,
		align: "end",
		sideOffset: 8,
		"aria-label": "Application navigation",
		children: rc.map((e) => /* @__PURE__ */ (0, s.jsx)(nc, {
			className: $.menuItem,
			onSelect: () => ic(e.target),
			children: e.name
		}, e.target))
	}) })] });
}
// frontend/src/components/ApplicationShell.tsx
var cc = (0, o.memo)(function() {
	return /* @__PURE__ */ (0, s.jsxs)("div", {
		className: $.application,
		children: [
			/* @__PURE__ */ (0, s.jsx)("a", {
				className: "skip-link",
				href: "#main-content",
				children: "Skip to application"
			}),
			/* @__PURE__ */ (0, s.jsx)("header", {
				className: "topbar",
				children: /* @__PURE__ */ (0, s.jsxs)("div", {
					className: "topbar-inner",
					children: [
						/* @__PURE__ */ (0, s.jsxs)("a", {
							className: "brand",
							href: "/",
							"aria-label": "Vita Tree home",
							children: [/* @__PURE__ */ (0, s.jsxs)("svg", {
								className: "brand-mark",
								viewBox: "0 0 32 32",
								"aria-hidden": "true",
								children: [
									/* @__PURE__ */ (0, s.jsx)("path", { d: "M8 7v13a5 5 0 0 0 5 5h11M8 13h11a5 5 0 0 0 5-5" }),
									/* @__PURE__ */ (0, s.jsx)("circle", {
										cx: "8",
										cy: "7",
										r: "3"
									}),
									/* @__PURE__ */ (0, s.jsx)("circle", {
										cx: "24",
										cy: "7",
										r: "3"
									}),
									/* @__PURE__ */ (0, s.jsx)("circle", {
										cx: "24",
										cy: "25",
										r: "3"
									})
								]
							}), "Vita Tree"]
						}),
						/* @__PURE__ */ (0, s.jsx)("span", {
							className: "divider",
							children: "/"
						}),
						/* @__PURE__ */ (0, s.jsx)("span", {
							id: "repository",
							children: "CV collection"
						}),
						/* @__PURE__ */ (0, s.jsx)(oc, {}),
						/* @__PURE__ */ (0, s.jsx)(sc, {}),
						/* @__PURE__ */ (0, s.jsx)(ac, {})
					]
				})
			}),
			/* @__PURE__ */ (0, s.jsxs)("main", {
				className: "shell",
				id: "main-content",
				tabIndex: -1,
				children: [
					/* @__PURE__ */ (0, s.jsx)("p", {
						id: "runs-error",
						className: "helper",
						role: "status"
					}),
					/* @__PURE__ */ (0, s.jsx)(f, {}),
					/* @__PURE__ */ (0, s.jsx)(p, {})
				]
			}),
			/* @__PURE__ */ (0, s.jsx)("dialog", {
				id: "create-dialog",
				children: /* @__PURE__ */ (0, s.jsxs)("form", {
					id: "create-form",
					children: [
						/* @__PURE__ */ (0, s.jsxs)("div", {
							className: "dialog-heading",
							children: [/* @__PURE__ */ (0, s.jsx)("div", { children: /* @__PURE__ */ (0, s.jsx)("h2", { children: "Create an application" }) }), /* @__PURE__ */ (0, s.jsx)("button", {
								type: "button",
								className: "close-dialog quiet",
								"aria-label": "Close create dialog",
								children: "×"
							})]
						}),
						/* @__PURE__ */ (0, s.jsxs)("label", { children: ["Starting CV", /* @__PURE__ */ (0, s.jsx)("select", {
							id: "base-branch",
							required: !0
						})] }),
						/* @__PURE__ */ (0, s.jsxs)("label", { children: ["Application name", /* @__PURE__ */ (0, s.jsx)("input", {
							id: "branch-name",
							placeholder: "Company — Role",
							required: !0,
							maxLength: 100,
							autoComplete: "off"
						})] }),
						/* @__PURE__ */ (0, s.jsxs)("label", { children: ["Job description", /* @__PURE__ */ (0, s.jsx)("textarea", {
							id: "new-job",
							placeholder: "Paste the full job description…",
							required: !0
						})] }),
						/* @__PURE__ */ (0, s.jsx)("p", {
							className: "helper",
							children: "Creates a separate application using this CV. Your original remains unchanged. You can use a saved CV or an earlier application as your starting point."
						}),
						/* @__PURE__ */ (0, s.jsx)("p", {
							id: "create-error",
							className: "form-error",
							role: "alert"
						}),
						/* @__PURE__ */ (0, s.jsxs)("footer", {
							className: "dialog-footer",
							children: [/* @__PURE__ */ (0, s.jsx)("button", {
								type: "button",
								className: "close-dialog",
								children: "Cancel"
							}), /* @__PURE__ */ (0, s.jsx)("button", {
								type: "submit",
								className: "primary",
								children: "Create application"
							})]
						})
					]
				})
			}),
			/* @__PURE__ */ (0, s.jsx)("dialog", {
				id: "edit-dialog",
				children: /* @__PURE__ */ (0, s.jsxs)("form", {
					id: "edit-form",
					children: [
						/* @__PURE__ */ (0, s.jsxs)("div", {
							className: "dialog-heading",
							children: [/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("h2", { children: "Edit CV text" }), /* @__PURE__ */ (0, s.jsx)("p", {
								id: "edit-origin",
								className: "helper"
							})] }), /* @__PURE__ */ (0, s.jsx)("button", {
								type: "button",
								className: "close-dialog quiet",
								"aria-label": "Close text editor",
								children: "×"
							})]
						}),
						/* @__PURE__ */ (0, s.jsxs)("label", { children: ["Text", /* @__PURE__ */ (0, s.jsx)("textarea", {
							id: "edit-text",
							required: !0
						})] }),
						/* @__PURE__ */ (0, s.jsx)("p", {
							className: "helper",
							children: "Updates the selected text in its originating file. Formatting is handled for you."
						}),
						/* @__PURE__ */ (0, s.jsx)("p", {
							id: "edit-error",
							className: "form-error",
							role: "alert"
						}),
						/* @__PURE__ */ (0, s.jsxs)("footer", {
							className: "dialog-footer",
							children: [/* @__PURE__ */ (0, s.jsx)("button", {
								type: "button",
								className: "close-dialog",
								children: "Cancel"
							}), /* @__PURE__ */ (0, s.jsx)("button", {
								type: "submit",
								className: "primary",
								children: "Save draft"
							})]
						})
					]
				})
			}),
			/* @__PURE__ */ (0, s.jsx)("dialog", {
				id: "commit-dialog",
				children: /* @__PURE__ */ (0, s.jsxs)("form", {
					id: "commit-form",
					children: [
						/* @__PURE__ */ (0, s.jsxs)("div", {
							className: "dialog-heading",
							children: [/* @__PURE__ */ (0, s.jsx)("div", { children: /* @__PURE__ */ (0, s.jsx)("h2", { children: "Save" }) }), /* @__PURE__ */ (0, s.jsx)("button", {
								type: "button",
								className: "close-dialog quiet",
								"aria-label": "Close save review",
								children: "×"
							})]
						}),
						/* @__PURE__ */ (0, s.jsx)("p", {
							className: "helper",
							children: "Save records a version of these changes and syncs them to the destination below. Save draft keeps edits on this computer."
						}),
						/* @__PURE__ */ (0, s.jsxs)("dl", {
							className: "commit-summary",
							children: [/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("dt", { children: "Application" }), /* @__PURE__ */ (0, s.jsx)("dd", { id: "commit-branch" })] }), /* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("dt", { children: "Sync destination" }), /* @__PURE__ */ (0, s.jsx)("dd", { id: "commit-destination" })] })]
						}),
						/* @__PURE__ */ (0, s.jsxs)("details", {
							className: "technical-details",
							children: [
								/* @__PURE__ */ (0, s.jsx)("summary", { children: "Connection setup" }),
								/* @__PURE__ */ (0, s.jsxs)("p", { children: ["Internal destination: ", /* @__PURE__ */ (0, s.jsx)("code", { id: "sync-details" })] }),
								/* @__PURE__ */ (0, s.jsx)("p", { children: "For setup, configure the CV collection’s Git destination and your save identity." }),
								/* @__PURE__ */ (0, s.jsx)("pre", { children: "git remote add origin <destination URL> git config user.name \"Your name\" git config user.email \"Your email\"" })
							]
						}),
						/* @__PURE__ */ (0, s.jsxs)("div", {
							className: "commit-files",
							children: [
								/* @__PURE__ */ (0, s.jsx)("strong", { children: "Changes to save" }),
								/* @__PURE__ */ (0, s.jsx)("ul", { id: "commit-files" }),
								/* @__PURE__ */ (0, s.jsx)("p", {
									id: "commit-empty",
									className: "helper",
									hidden: !0,
									children: "No new edits. Any versions waiting to sync will be included."
								}),
								/* @__PURE__ */ (0, s.jsx)("p", {
									id: "commit-excluded",
									className: "helper",
									hidden: !0
								})
							]
						}),
						/* @__PURE__ */ (0, s.jsxs)("label", { children: ["Change note", /* @__PURE__ */ (0, s.jsx)("input", {
							id: "commit-message",
							maxLength: 200,
							placeholder: "Update CV for this opportunity",
							required: !0,
							autoComplete: "off"
						})] }),
						/* @__PURE__ */ (0, s.jsx)("p", {
							id: "commit-progress",
							className: "helper",
							role: "status"
						}),
						/* @__PURE__ */ (0, s.jsx)("p", {
							id: "commit-error",
							className: "form-error",
							role: "alert"
						}),
						/* @__PURE__ */ (0, s.jsxs)("footer", {
							className: "dialog-footer",
							children: [/* @__PURE__ */ (0, s.jsx)("button", {
								type: "button",
								className: "close-dialog",
								children: "Cancel"
							}), /* @__PURE__ */ (0, s.jsx)("button", {
								id: "confirm-commit",
								type: "submit",
								className: "primary",
								children: "Save"
							})]
						})
					]
				})
			}),
			/* @__PURE__ */ (0, s.jsx)("dialog", {
				id: "resume-dialog",
				"aria-labelledby": "resume-title",
				children: /* @__PURE__ */ (0, s.jsxs)("form", {
					id: "resume-form",
					children: [
						/* @__PURE__ */ (0, s.jsxs)("div", {
							className: "dialog-heading",
							children: [/* @__PURE__ */ (0, s.jsx)("h2", {
								id: "resume-title",
								children: "Resume preparation"
							}), /* @__PURE__ */ (0, s.jsx)("button", {
								type: "button",
								className: "close-dialog quiet",
								"aria-label": "Close resume review",
								children: "×"
							})]
						}),
						/* @__PURE__ */ (0, s.jsx)("p", {
							className: "helper",
							children: "Continue as a new attempt. Verified results are reused only when the captured inputs, requirements, and AI setup match. All other selected steps run again."
						}),
						/* @__PURE__ */ (0, s.jsx)("p", { id: "resume-summary" }),
						/* @__PURE__ */ (0, s.jsxs)("label", {
							id: "resume-config-choice",
							hidden: !0,
							children: [/* @__PURE__ */ (0, s.jsx)("input", {
								type: "checkbox",
								id: "resume-current-config"
							}), " Use the current application setup instead of the captured setup"]
						}),
						/* @__PURE__ */ (0, s.jsx)("h3", { children: "Reuse verified results" }),
						/* @__PURE__ */ (0, s.jsx)("p", { id: "resume-reuse" }),
						/* @__PURE__ */ (0, s.jsx)("h3", { children: "Run again" }),
						/* @__PURE__ */ (0, s.jsx)("p", { id: "resume-rerun" }),
						/* @__PURE__ */ (0, s.jsx)("p", {
							id: "resume-adapted",
							className: "helper",
							hidden: !0,
							children: "The matching tailored CV from the earlier attempt will be used for the remaining steps, including the cover letter. Your current draft stays unchanged until the preparation finishes successfully."
						}),
						/* @__PURE__ */ (0, s.jsx)("p", {
							className: "helper",
							children: "A change invalidates that step and all later selected steps. Final checks always run. Expired, missing, or unverifiable checkpoints are never reused."
						}),
						/* @__PURE__ */ (0, s.jsx)("p", {
							id: "resume-error",
							className: "form-error",
							role: "alert"
						}),
						/* @__PURE__ */ (0, s.jsxs)("footer", {
							className: "dialog-footer",
							children: [/* @__PURE__ */ (0, s.jsx)("button", {
								type: "button",
								className: "close-dialog",
								children: "Cancel"
							}), /* @__PURE__ */ (0, s.jsx)("button", {
								id: "confirm-resume",
								type: "submit",
								className: "primary",
								children: "Start new attempt"
							})]
						})
					]
				})
			}),
			/* @__PURE__ */ (0, s.jsxs)("dialog", {
				id: "diagnostics-dialog",
				"aria-labelledby": "diagnostics-title",
				children: [
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "dialog-heading",
						children: [/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("h2", {
							id: "diagnostics-title",
							children: "Activity & support"
						}), /* @__PURE__ */ (0, s.jsx)("p", {
							className: "helper",
							children: "Preparation progress and help with recent problems."
						})] }), /* @__PURE__ */ (0, s.jsx)("button", {
							className: "close-dialog quiet",
							"aria-label": "Close activity and support",
							children: "×"
						})]
					}),
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "diagnostics-metrics",
						children: [
							/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("strong", {
								id: "metric-active",
								children: "0"
							}), /* @__PURE__ */ (0, s.jsx)("span", { children: "In progress" })] }),
							/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("strong", {
								id: "metric-completed",
								children: "0"
							}), /* @__PURE__ */ (0, s.jsx)("span", { children: "Completed preparations" })] }),
							/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("strong", {
								id: "metric-failed",
								children: "0"
							}), /* @__PURE__ */ (0, s.jsx)("span", { children: "Preparations needing attention" })] }),
							/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("strong", {
								id: "metric-requests",
								children: "0"
							}), /* @__PURE__ */ (0, s.jsx)("span", { children: "Requests this session" })] }),
							/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("strong", {
								id: "metric-errors",
								children: "0"
							}), /* @__PURE__ */ (0, s.jsx)("span", { children: "Failed requests" })] }),
							/* @__PURE__ */ (0, s.jsxs)("div", { children: [/* @__PURE__ */ (0, s.jsx)("strong", {
								id: "metric-latency",
								children: "0"
							}), /* @__PURE__ */ (0, s.jsx)("span", { children: "Average response time (ms)" })] })
						]
					}),
					/* @__PURE__ */ (0, s.jsx)("section", {
						id: "execution-inspector",
						"aria-label": "Execution inspector"
					}),
					/* @__PURE__ */ (0, s.jsx)("ul", {
						id: "activity-summary",
						className: "activity-summary"
					}),
					/* @__PURE__ */ (0, s.jsxs)("details", {
						className: "technical-details",
						children: [
							/* @__PURE__ */ (0, s.jsx)("summary", { children: "Retained retry results" }),
							/* @__PURE__ */ (0, s.jsx)("p", { children: "Verified checkpoints are kept for up to 7 days, 20 preparations, and 256 MB. Active preparations are protected. Cleanup removes only retry checkpoints; application drafts, preparation history, and review results remain." }),
							/* @__PURE__ */ (0, s.jsx)("button", {
								id: "cleanup-checkpoints",
								children: "Clean expired checkpoints"
							}),
							/* @__PURE__ */ (0, s.jsx)("p", {
								id: "cleanup-checkpoints-status",
								role: "status"
							})
						]
					}),
					/* @__PURE__ */ (0, s.jsxs)("details", {
						className: "technical-details",
						children: [
							/* @__PURE__ */ (0, s.jsx)("summary", { children: "Technical details" }),
							/* @__PURE__ */ (0, s.jsx)("p", {
								id: "diagnostics-uptime",
								className: "helper"
							}),
							/* @__PURE__ */ (0, s.jsxs)("p", {
								className: "helper",
								children: ["Log file: ", /* @__PURE__ */ (0, s.jsx)("code", { id: "diagnostics-location" })]
							}),
							/* @__PURE__ */ (0, s.jsx)("p", {
								id: "diagnostics-logging",
								className: "helper"
							}),
							/* @__PURE__ */ (0, s.jsxs)("div", {
								className: "diagnostics-toolbar",
								children: [/* @__PURE__ */ (0, s.jsxs)("label", { children: ["Find an event", /* @__PURE__ */ (0, s.jsx)("input", {
									id: "diagnostics-search",
									type: "search",
									placeholder: "Request ID, step, or error type"
								})] }), /* @__PURE__ */ (0, s.jsxs)("div", {
									className: "actions",
									children: [
										/* @__PURE__ */ (0, s.jsx)("button", {
											id: "refresh-diagnostics",
											children: "Refresh activity"
										}),
										/* @__PURE__ */ (0, s.jsx)("button", {
											id: "download-diagnostics",
											children: "Download support report"
										}),
										/* @__PURE__ */ (0, s.jsx)("a", {
											href: "/metrics",
											target: "_blank",
											rel: "noopener",
											children: "View performance statistics"
										})
									]
								})]
							}),
							/* @__PURE__ */ (0, s.jsx)("p", {
								id: "diagnostics-error",
								className: "form-error",
								role: "status"
							}),
							/* @__PURE__ */ (0, s.jsx)("div", {
								className: "diagnostics-table",
								children: /* @__PURE__ */ (0, s.jsxs)("table", { children: [/* @__PURE__ */ (0, s.jsx)("thead", { children: /* @__PURE__ */ (0, s.jsxs)("tr", { children: [
									/* @__PURE__ */ (0, s.jsx)("th", { children: "Time" }),
									/* @__PURE__ */ (0, s.jsx)("th", { children: "Event" }),
									/* @__PURE__ */ (0, s.jsx)("th", { children: "Operation" }),
									/* @__PURE__ */ (0, s.jsx)("th", { children: "Result" }),
									/* @__PURE__ */ (0, s.jsx)("th", { children: "Error details" }),
									/* @__PURE__ */ (0, s.jsx)("th", { children: "Reference" })
								] }) }), /* @__PURE__ */ (0, s.jsx)("tbody", { id: "diagnostics-events" })] })
							}),
							/* @__PURE__ */ (0, s.jsx)("p", {
								className: "helper",
								children: "Updates every 3 seconds. The last 200 events are shown. Logs exclude CV text, prompts, credentials, and raw AI output. Downloaded diagnostics also omit local log paths."
							})
						]
					})
				]
			}),
			/* @__PURE__ */ (0, s.jsxs)("dialog", {
				id: "setup-dialog",
				"aria-labelledby": "setup-title",
				children: [
					/* @__PURE__ */ (0, s.jsxs)("div", {
						className: "dialog-heading",
						children: [/* @__PURE__ */ (0, s.jsx)("h2", {
							id: "setup-title",
							children: "Check CV files"
						}), /* @__PURE__ */ (0, s.jsx)("button", {
							type: "button",
							className: "close-dialog quiet",
							"aria-label": "Close setup checks",
							children: "×"
						})]
					}),
					/* @__PURE__ */ (0, s.jsx)("p", { children: "Find missing files or PDF tools. Your CV stays unchanged." }),
					/* @__PURE__ */ (0, s.jsxs)("label", { children: ["CV", /* @__PURE__ */ (0, s.jsx)("select", { id: "setup-branch" })] }),
					/* @__PURE__ */ (0, s.jsxs)("details", {
						id: "setup-technical",
						className: "technical-details",
						children: [
							/* @__PURE__ */ (0, s.jsx)("summary", { children: "Technical details" }),
							/* @__PURE__ */ (0, s.jsxs)("label", { children: ["PDF tool for checks and new preparations", /* @__PURE__ */ (0, s.jsxs)("select", {
								id: "setup-engine",
								children: [
									/* @__PURE__ */ (0, s.jsx)("option", {
										value: "auto",
										children: "Automatic"
									}),
									/* @__PURE__ */ (0, s.jsx)("option", {
										value: "pdflatex",
										children: "PDFLaTeX"
									}),
									/* @__PURE__ */ (0, s.jsx)("option", {
										value: "xelatex",
										children: "XeLaTeX"
									}),
									/* @__PURE__ */ (0, s.jsx)("option", {
										value: "lualatex",
										children: "LuaLaTeX"
									})
								]
							})] }),
							/* @__PURE__ */ (0, s.jsx)("p", {
								className: "helper",
								children: "Automatic uses XeLaTeX when main.tex declares fontspec, polyglossia or unicode-math; otherwise PDFLaTeX. Choose explicitly when a class or included file requires another engine. Retries preserve their captured engine."
							}),
							/* @__PURE__ */ (0, s.jsxs)("p", { children: [
								"Use a UTF-8 LaTeX project with ",
								/* @__PURE__ */ (0, s.jsx)("code", { children: "main.tex" }),
								" at the project root. Include all required classes, styles, fonts, images and included files in Git. PDF, Word and scanned-CV import are not available. A different ",
								/* @__PURE__ */ (0, s.jsx)("code", { children: "vt run --file" }),
								" entry supports viewing and PDF previews; AI preparation requires",
								" ",
								/* @__PURE__ */ (0, s.jsx)("code", { children: "main.tex" }),
								"."
							] }),
							/* @__PURE__ */ (0, s.jsx)("p", {
								className: "helper",
								children: "Checks compile a temporary copy with shell escape and automatic package installation disabled. No AI service is contacted. Only open templates and TeX installations you trust; these restrictions are not an OS sandbox."
							}),
							/* @__PURE__ */ (0, s.jsx)("p", {
								id: "setup-revision",
								className: "helper"
							})
						]
					}),
					/* @__PURE__ */ (0, s.jsx)("p", {
						id: "setup-progress",
						role: "status"
					}),
					/* @__PURE__ */ (0, s.jsx)("h3", {
						id: "setup-result-heading",
						tabIndex: -1,
						hidden: !0
					}),
					/* @__PURE__ */ (0, s.jsx)("ul", { id: "setup-results" }),
					/* @__PURE__ */ (0, s.jsxs)("footer", {
						className: "dialog-footer",
						children: [/* @__PURE__ */ (0, s.jsx)("button", {
							type: "button",
							className: "close-dialog",
							children: "Close"
						}), /* @__PURE__ */ (0, s.jsx)("button", {
							type: "button",
							id: "check-setup",
							className: "primary",
							children: "Check files"
						})]
					})
				]
			}),
			/* @__PURE__ */ (0, s.jsx)("div", {
				id: "toast",
				className: "toast",
				role: "status",
				hidden: !0
			})
		]
	});
}), lc = document.getElementById("react-root");
if (!lc) throw Error("Vita Tree could not find its application root.");
(0, u.flushSync)(() => (0, d.createRoot)(lc).render(/* @__PURE__ */ (0, s.jsx)(l, {
	client: a,
	children: /* @__PURE__ */ (0, s.jsx)(cc, {})
})));
try {
	await import("./assets/frontend-app-CXdKPmjn.js"), lc.dataset.ready = "true";
} catch (e) {
	let t = document.createElement("p");
	throw t.setAttribute("role", "alert"), t.textContent = e instanceof Error ? e.message : "The application could not start. Reload to try again.", lc.prepend(t), e;
}
