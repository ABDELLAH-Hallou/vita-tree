// frontend/src/compat/jobenu-history.js
function e(e) {
	let t = new Map(e.map((e) => [e.id, e])), n = /* @__PURE__ */ new Map();
	for (let r of e) {
		if (r.parentBatchId && !r.startedAt || !r.startedAt && !r.entries.length && !r.error) continue;
		let e = r.retryRootId || r.id;
		n.has(e) || n.set(e, {
			batch: t.get(e) || r,
			attempts: []
		}), n.get(e).attempts.push(r);
	}
	return [...n.values()].map((e) => {
		e.attempts.sort((e, t) => (e.startedAt || e.createdAt) - (t.startedAt || t.createdAt));
		let t = /* @__PURE__ */ new Map();
		for (let n of e.attempts) for (let e of n.entries) t.set(e.key || e.branch, e);
		return {
			...e,
			entries: [...t.values()]
		};
	}).sort((e, t) => t.batch.createdAt - e.batch.createdAt);
}
function t(e) {
	return e.status === "failed" && !e.pending;
}
function n(e) {
	return e.attempts.some((e) => e.status === "running");
}
function r(e, r) {
	if (n(e)) return "In progress";
	let i = e.entries.filter(t).length, a = e.entries.filter((e) => e.pending || e.status === "awaiting_requirements_approval").length;
	return i ? `${i} failed job${i === 1 ? "" : "s"}${a ? ` · ${a} waiting for review` : ""}` : a ? "Waiting for review" : r(e.attempts.at(-1)?.status);
}
export { t as i, r as n, n as r, e as t };
