// frontend/src/compat/reports.js
function e(e, t, n) {
	let r = /(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^\s)]+\))/g, i = 0;
	for (let a of t.matchAll(r)) {
		if (n.remaining-- <= 0) break;
		e.append(document.createTextNode(t.slice(i, a.index)));
		let r = a[0], o;
		if (r.startsWith("`")) o = document.createElement("code"), o.textContent = r.slice(1, -1);
		else if (r.startsWith("**")) o = document.createElement("strong"), o.textContent = r.slice(2, -2);
		else {
			let [, e, t] = r.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
			o = document.createElement("span"), o.textContent = e, /^https?:\/\//i.test(t) && (o = document.createElement("a"), o.textContent = e, o.href = t, o.target = "_blank", o.rel = "noopener noreferrer");
		}
		e.append(o), i = a.index + r.length;
	}
	e.append(document.createTextNode(t.slice(i)));
}
function t(t) {
	let n = document.createElement("article");
	n.className = "report-prose";
	let r = t.slice(0, 2e5).replace(/\r\n/g, "\n").split("\n"), i = r.slice(0, 2e3), a = { remaining: 4e3 };
	if (t.length > 2e5 || r.length > 2e3) {
		let e = document.createElement("p");
		e.textContent = "Preview shortened for readability. Open the saved report file for the full text.", n.append(e);
	}
	for (let t = 0; t < i.length; t++) {
		let r = i[t];
		if (!r.trim()) continue;
		if (r.startsWith("```")) {
			let e = document.createElement("pre"), r = document.createElement("code"), a = [];
			for (; ++t < i.length && !i[t].startsWith("```");) a.push(i[t]);
			r.textContent = a.join("\n"), e.append(r), n.append(e);
			continue;
		}
		if (r.includes("|") && /^\s*\|?\s*:?-{3,}/.test(i[t + 1] || "")) {
			let o = document.createElement("div");
			o.className = "report-table", o.tabIndex = 0, o.setAttribute("role", "region"), o.setAttribute("aria-label", "Report table");
			let s = document.createElement("table"), c = (e) => e.trim().replace(/^\||\|$/g, "").split("|"), l = (t, n) => {
				let r = document.createElement("tr");
				for (let i of c(t).slice(0, 40)) {
					let t = document.createElement(n);
					n === "th" && (t.scope = "col"), e(t, i.trim(), a), r.append(t);
				}
				return r;
			}, u = document.createElement("thead");
			u.append(l(r, "th")), s.append(u), t++;
			let d = document.createElement("tbody");
			for (; t + 1 < i.length && i[t + 1].includes("|") && i[t + 1].trim();) d.append(l(i[++t], "td"));
			s.append(d), o.append(s), n.append(o);
			continue;
		}
		let o = r.match(/^(#{1,6})\s+(.+)/);
		if (o) {
			let t = document.createElement("h" + Math.min(o[1].length + 2, 6));
			e(t, o[2], a), n.append(t);
			continue;
		}
		if (/^\s*([-*]|\d+\.)\s+/.test(r)) {
			let o = /^\s*\d+\./.test(r), s = document.createElement(o ? "ol" : "ul");
			do {
				let n = document.createElement("li");
				e(n, i[t].replace(/^\s*([-*]|\d+\.)\s+/, ""), a), s.append(n), t++;
			} while (t < i.length && (o ? /^\s*\d+\.\s+/ : /^\s*[-*]\s+/).test(i[t]));
			t--, n.append(s);
			continue;
		}
		if (/^\s*([-*_])\1{2,}\s*$/.test(r)) {
			n.append(document.createElement("hr"));
			continue;
		}
		let s = document.createElement(r.startsWith("> ") ? "blockquote" : "p");
		e(s, r.replace(/^> /, ""), a), n.append(s);
	}
	return n;
}
function n(e) {
	let t = e.split("/").pop();
	return {
		"analysis.md": "CV match analysis",
		"analyze.md": "CV match analysis",
		"adapt.md": "Tailoring summary",
		"review.md": "AI review",
		"delta.md": "Changes since the previous review",
		"cover.md": "Cover-letter summary",
		"main.tex": "CV source",
		"cover-letter.tex": "Cover-letter source",
		"job.md": "Job description",
		"job.json": "Job requirements · data",
		"job.toon": "Job requirements · data",
		"analysis.json": "CV match scores · data",
		"review.json": "Review scores · data",
		"delta.json": "Score changes · data"
	}[t] || t;
}
function r(e, r, { open: i = !1, label: a = null } = {}) {
	let o = document.createElement("details");
	o.open = i, o.dataset.path = e;
	let s = document.createElement("summary");
	s.textContent = a || n(e), o.append(s);
	let c = document.createElement("details");
	c.className = "technical-details";
	let l = document.createElement("summary");
	l.textContent = "File details";
	let u = document.createElement("code");
	if (u.textContent = e, c.append(l, u), o.append(c), e.endsWith(".md")) o.append(t(r));
	else {
		let e = document.createElement("pre");
		e.textContent = r, o.append(e);
	}
	return o;
}
export { t as n, r, n as t };
