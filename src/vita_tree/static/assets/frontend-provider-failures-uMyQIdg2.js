// frontend/src/compat/provider-failures.js
function e(e, t) {
	let n = e?.failures?.[t];
	if (!n) return "";
	let r = e.stepConfig?.[t], i = n.routeEvidence === "backend" ? `Effective: ${n.provider || "provider unreported"} / ${n.model || "model unreported"}` : `Effective route unreported${r ? `; captured request: ${r.provider} / ${r.model || "provider default"}` : ""}`, a = n.retryable === !0 ? "Retryable" : n.retryable === !1 ? "Needs attention before retry" : "Retryability unknown";
	return `${n.title} (${n.category.replaceAll("_", " ")})${n.httpStatus ? ` · HTTP ${n.httpStatus}` : ""}. ${i}. ${a}; ${n.attempts ?? "unknown"} provider attempts${n.exhausted ? " · retry budget exhausted" : ""}. ${n.retryAfterSeconds == null ? "" : `Provider asks to wait ${n.retryAfterSeconds}s. `}${n.action}`;
}
function t(t) {
	return Object.keys(t?.failures || {}).map((n) => `${n}: ${e(t, n)}`).join(" ");
}
export { t as n, e as t };
