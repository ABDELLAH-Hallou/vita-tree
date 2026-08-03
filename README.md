# vita-tree

A small, dependency-free dashboard for browsing Git-based CV variants.

It lists local and remote-only branches by latest commit date. Clicking a
branch opens its `main.tex` as a clean, copyable document, with the original
LaTeX available through a source toggle. It never checks out or modifies the
repository it inspects.

## Install

For an editable local installation:

```powershell
python -m pip install --no-build-isolation -e .
```

## Run

Inside the repository you want to inspect:

```powershell
vt run
```

Or point it at another repository from anywhere:

```powershell
vt run C:\path\to\repository
```

Options:

```text
vt run [REPOSITORY] [--host HOST] [--port PORT] [--file PATH] [--no-browser]
```

The default document is `main.tex`. Use `--file` when the document lives at a
different path inside the branches.
