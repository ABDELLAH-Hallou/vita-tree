import { i as e } from "./frontend-workflow-DqtU3Lxp.js";
// frontend/src/compat/runs.js
var t = (e) => e && ["queued", "running"].includes(e.status), n = (e) => e.source === "jobenu" ? "Jobenu · " + ({
	succeeded: "Completed",
	awaiting_review: "Needs review",
	awaiting_resume: "Ready to continue",
	running: "In progress",
	imported: "Imported",
	failed: "Couldn’t finish",
	interrupted: "Interrupted"
}[e.status] || e.status) : e.requirementsApprovalNeeded ? "Needs requirements review" : e.factualReview ? {
	pending: "Needs factual review",
	resolved: "Ready to continue",
	unavailable: "Review unavailable"
}[e.factualReview.state] || "Review unavailable" : {
	queued: "Queued",
	preparing: "Preparing",
	extract: "Identifying requirements",
	review: "Reviewing CV",
	cover: "Writing cover letter",
	analyze: "Checking CV match",
	adapt: "Tailoring CV",
	preflight: "Checking setup",
	validating: "Checking results",
	completed: "Completed",
	failed: "Couldn’t finish",
	interrupted: "Stopped before finishing"
}[e.step] || e.status, r = (t) => (t.stages || []).filter((e) => e.status !== "skipped" && e.id !== "validating").map((t) => e.find((e) => e.id === t.id)?.title).join(" → ") || (t.stages?.length ? "Final checks" : "Preparation");
function i({ api: e, changed: t }) {
	let n = (e) => document.querySelector(e), r = "", i = !1;
	async function a() {
		if (!i) {
			i = !0;
			try {
				let i = (await e("/api/jobs")).runs, a = JSON.stringify(i.map(({ elapsedSeconds: e, ...t }) => t));
				n("#runs-error").textContent = "", a !== r && (r = a, await t(i));
			} catch {
				n("#runs-error").textContent = "Preparation updates are unavailable. Reconnecting…";
			} finally {
				i = !1;
			}
		}
	}
	async function o() {
		await a(), setTimeout(o, 1500);
	}
	return {
		start: o,
		refresh: a
	};
}
export { r as i, t as n, n as r, i as t };
