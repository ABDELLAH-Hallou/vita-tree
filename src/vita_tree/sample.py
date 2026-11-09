"""Sample CV generation and demo repository creation for Vita Tree."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from .setup import data_directory, single_writer

SAMPLE_MAIN_TEX = r"""\documentclass{article}
\usepackage[margin=0.65in]{geometry}
\usepackage{hyperref}
\usepackage{tabularx}
\newenvironment{rSection}[1]{\section*{#1}}{}
\begin{document}
\begin{center}{\Large\textbf{Jordan Lee}}\\Software Engineer\end{center}
\begin{rSection}{Summary}
Software engineer who builds reliable tools and makes them easier to maintain.
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
    return data_directory() / "demo"


def prepare_demo_repository(target: Path | None = None) -> Path:
    """Create a complete sample or reopen one previously created by Vita Tree."""
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git is required to run the demo. Install Git and add it to PATH.")

    requested = (target or default_demo_directory()).expanduser().absolute()
    if requested.is_symlink() or (hasattr(requested, "is_junction") and requested.is_junction()):
        raise RuntimeError("Choose a fresh demo folder instead of a link.")
    location = requested.resolve()
    marker = Path(".git/vita-tree-demo")
    if location.exists():
        if (location / marker).is_file() and (location / "main.tex").is_file():
            return location
        raise RuntimeError("The demo folder already exists. Choose a new folder or use vt run to open it.")

    # Do not inherit a caller's Git index, repository override, hooks, or signing configuration.
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    parent = next(path for path in location.parents if path.is_dir())
    probe = subprocess.run(
        [git, "-C", str(parent), "rev-parse", "--git-dir"],
        env=environment, capture_output=True, timeout=15,
    )
    if probe.returncode == 0:
        raise RuntimeError("Choose a demo folder outside existing Git repositories.")

    with single_writer(location.parent / f".{location.name}.vita-tree.lock"):
        if location.exists():
            if (location / marker).is_file() and (location / "main.tex").is_file():
                return location
            raise RuntimeError("The demo folder already exists. Choose a new folder.")
        with TemporaryDirectory(prefix=".vita-demo-", dir=location.parent) as staging:
            repo = Path(staging) / "sample"
            repo.mkdir()
            files = {"main.tex": SAMPLE_MAIN_TEX, "job.md": SAMPLE_JOB_MD, ".gitignore": ".vita/\n*.pdf\n"}
            for filename, content in files.items():
                (repo / filename).write_text(content, encoding="utf-8")
            try:
                for command in (
                    ["init", "--template=", "--initial-branch=main"],
                    ["add", "--", *files],
                    ["-c", "user.name=Vita Tree Demo", "-c", "user.email=demo@example.invalid",
                     "commit", "-m", "Add synthetic CV and job description"],
                ):
                    subprocess.run(
                        [git, "-C", str(repo), *command], env=environment,
                        check=True, capture_output=True, timeout=15,
                    )
            except subprocess.SubprocessError as exc:
                raise RuntimeError("Git could not initialize the demo. Check Git and folder permissions.") from exc
            (repo / marker).touch()
            repo.rename(location)
    return location
