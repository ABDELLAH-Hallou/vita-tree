// frontend/src/compat/jobenu-history.js
function e(e) {
	let t = new Map(e.map((e) => [e.id, e])), n = /* @__PURE__ */ new Map();
	for (let r of e) {
		if (r.parentBatchId && !r.startedAt) continue;
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
function n(e, n) {
	if (e.attempts.some((e) => e.status === "running")) return "In progress";
	let r = e.entries.filter(t).length, i = e.entries.filter((e) => e.pending || e.status === "awaiting_requirements_approval").length;
	return r ? `${r} failed job${r === 1 ? "" : "s"}${i ? ` · ${i} waiting for review` : ""}` : i ? "Waiting for review" : n(e.attempts.at(-1)?.status);
}
export { n, t as r, e as t };
