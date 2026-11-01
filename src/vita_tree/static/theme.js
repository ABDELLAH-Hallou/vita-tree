// frontend/src/theme-bootstrap.ts
try {
	let e = localStorage.getItem("vita-tree-theme");
	document.documentElement.dataset.theme = e === "light" || e === "dark" ? e : matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
} catch {
	document.documentElement.dataset.theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}
