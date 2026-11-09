"""Sample CV generation and demo repository creation for Vita Tree."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

SAMPLE_MAIN_TEX = r"""\documentclass{article}
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

SAMPLE_JOB_MD = """# Software Engineer

## About the Role
We are looking for a Software Engineer to build dependable software, maintain automated test suites, and collaborate with team members on system delivery.

## Requirements
- Proficiency with Python and relational databases (SQL / PostgreSQL)
- Experience with Git version control and automated testing
- Clear technical writing and documentation skills
"""


def default_demo_directory() -> Path:
    """Return the default per-user directory for the demo CV repository."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "vita-tree" / "demo"


def prepare_demo_repository(target: Path | None = None) -> Path:
    """Create or reuse an isolated sample Git repository for demonstration.

    Does not require any global Git identity or remote connection.
    If the repository already exists and has main.tex, reuses it without overwriting edits.
    """
    git_bin = shutil.which("git")
    if not git_bin:
        raise RuntimeError("Git is required to create or run the demo repository. Install Git and ensure it is on your PATH.")

    location = Path(target).resolve() if target else default_demo_directory().resolve()

    main_tex = location / "main.tex"
    git_dir = location / ".git"

    if git_dir.exists() and main_tex.is_file():
        return location

    location.mkdir(parents=True, exist_ok=True)

    if not git_dir.exists():
        init_res = subprocess.run(["git", "init", "-b", "main", str(location)], capture_output=True, text=True)
        if init_res.returncode != 0:
            subprocess.run(["git", "init", str(location)], check=True, capture_output=True, text=True)

    if not main_tex.exists():
        main_tex.write_text(SAMPLE_MAIN_TEX, encoding="utf-8")

    job_md = location / "job.md"
    if not job_md.exists():
        job_md.write_text(SAMPLE_JOB_MD, encoding="utf-8")

    gitignore = location / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(".vita/\n*.pdf\n", encoding="utf-8")

    status = subprocess.run(["git", "-C", str(location), "status", "--porcelain"], check=True, capture_output=True, text=True)
    if status.stdout.strip():
        subprocess.run(["git", "-C", str(location), "add", "."], check=True, capture_output=True, text=True)
        subprocess.run(
            [
                "git", "-C", str(location),
                "-c", "user.name=Vita Tree Demo",
                "-c", "user.email=demo@example.invalid",
                "commit", "-m", "Initial sample CV and job description",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    return location
