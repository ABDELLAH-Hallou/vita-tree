from pathlib import Path
import shutil
import subprocess
import time
import json


def cleanup_repo(temporary):
    """Retry short Windows file-indexer locks without hiding cleanup failures."""
    target = Path(temporary.name).resolve()
    if target.parent != Path.cwd().resolve() or not target.name.startswith('.vita-tree-test-'):
        raise ValueError('Refusing to clean a directory outside the test workspace')
    for attempt in range(10):
        try:
            temporary.cleanup()
            return
        except PermissionError as error:
            if getattr(error, 'winerror', None) not in (5, 32) or attempt == 9:
                raise
            time.sleep(.2 * (attempt + 1))

SOURCE = r"""\documentclass{article}
\usepackage[margin=0.65in]{geometry}
\usepackage{hyperref}
\usepackage{tabularx}
\newenvironment{rSection}[1]{\section*{#1}}{}
\begin{document}
\begin{center}{\Large\textbf{Jordan Lee}}\\Software Engineer\end{center}
\begin{rSection}{Summary}
Engineer building \textbf{reliable systems} for people. Improved delivery by 20\%.
\end{rSection}
\begin{rSection}{Experience}
\textbf{Software Engineer} \hfill 2023--2026\\
Sample Organization
\begin{itemize}
\item Built Python services with automated tests.
\item Documented APIs and collaborated with product teams.
\end{itemize}
\end{rSection}
\begin{rSection}{Skills}
\begin{tabularx}{\linewidth}{lX}
Languages & Python, SQL, JavaScript \\
Tools & Git, Docker, PostgreSQL \\
\end{tabularx}
\end{rSection}
\end{document}
"""


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def assert_public_run_privacy(payload, private_values):
    """Allow fixed guidance, but reject fixture secrets, source and raw fields."""
    public = json.dumps(payload)
    for value in private_values:
        assert value not in public, 'Private fixture content leaked into the global API'
    forbidden = {'env', 'stdout', 'stderr', 'prompt', 'source', 'content', 'sourcecontent', 'rawoutput'}
    def check(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(key.casefold() for key in value), 'Raw run payload field leaked into the global API'
            for child in value.values():
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)
    check(payload)


def init_repo(root):
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-b", "master")
    git(root, "config", "user.name", "Vita Tree Tests")
    git(root, "config", "user.email", "tests@example.invalid")
    (root / "main.tex").write_text(SOURCE, encoding="utf-8")
    (root / ".gitignore").write_text(".vita/\n*.pdf\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "Base CV")
    return root


def set_theme(page, theme):
    """Choose an explicit theme through the visible icon button."""
    from playwright.sync_api import expect
    if page.locator('html').get_attribute('data-theme') != theme:
        page.get_by_role('button', name=f'Switch to {theme} mode', exact=True).click()
    expect(page.locator('html')).to_have_attribute('data-theme', theme)


# Sanitized minimal reproduction from issue #37; no optional TeX packages.
CUSTOM_ENVIRONMENT_SOURCE = r"""\documentclass{article}
\newenvironment{indentsection}[1]%
{\begin{list}{}%
{\setlength{\leftmargin}{#1}}%
     \item[]
}
{\end{list}}
\begin{document}
\begin{indentsection}{1em}Sample experience.\end{indentsection}
\end{document}
"""
