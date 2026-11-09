# Security Policy

## Reporting Security Issues

If you discover a security vulnerability or sensitive data disclosure issue in Vita Tree, please report it directly by email to:

**Abdellah HALLOU** — [abdeallahhallou33@gmail.com](mailto:abdeallahhallou33@gmail.com)

Please do not open a public issue on GitHub for undisclosed security vulnerabilities.

---

## Threat Model and Boundaries

Vita Tree is a local development and version control tool designed for individual developers and researchers managing their LaTeX CVs on their own machines.

### 1. Localhost Binding

The Vita Tree web interface and API bind to `127.0.0.1` by default. It accepts localhost connections only. Because the server can create Git worktrees, commit changes, and write files within the inspected repository, **never expose the server through a public network proxy or shared tunnel**.

### 2. Trusted LaTeX Compilation

Vita Tree executes local TeX compilers (`pdflatex`, `xelatex`, `lualatex`) with shell escape disabled (`-no-shell-escape`). However, disabling shell escape is not an operating-system level sandbox. Always compile only trusted local LaTeX source files.

### 3. Credential Redaction and Privacy

- Structured rotating JSON logs written by `vt run` exclude CV content, job descriptions, prompt texts, and provider credentials.
- AI provider tokens and API keys are passed in child-process memory and are never written to public run records or Git commits.
- Git commits created through the interface include only explicitly reviewed files (the main LaTeX document, `job.md`, generated `cover-letter.tex`, and reviewed reports); unrelated working-tree files are excluded.

### 4. Scoped Review

For architectural details, workflow audits, and local latency evaluations, refer to the [Local Workflow Audit](https://github.com/ABDELLAH-Hallou/vita-tree/blob/main/LOCAL_WORKFLOW_AUDIT.md).
