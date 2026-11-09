#!/usr/bin/env bash
set -euo pipefail

echo "Vita Tree Setup (Linux/macOS)"
echo "=============================="

PYTHON_CMD=""
for cmd in python3 python py; do
    if command -v "$cmd" >/dev/null 2>&1; then
        VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
        if [ -n "$VER" ]; then
            MAJOR=$(echo "$VER" | cut -d. -f1)
            MINOR=$(echo "$VER" | cut -d. -f2)
            if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
                PYTHON_CMD="$cmd"
                echo "Found compatible Python: $VER ($cmd)"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Compatible Python (3.10+) not found."
    echo "Please install Python 3.10 or newer from your package manager (brew, apt, dnf)."
    exit 1
fi

if command -v git >/dev/null 2>&1; then
    echo "Found Git: $(command -v git)"
else
    echo "Git not found on PATH. Git is required to manage CV versions."
    echo "Please install git from your package manager."
    exit 1
fi

if command -v pdflatex >/dev/null 2>&1 || command -v xelatex >/dev/null 2>&1; then
    echo "Found TeX engine for PDF previews."
else
    echo "TeX engine not found. Note: TeX is only needed for PDF compilation; browsing and editing works without it."
    echo "Install TeX Live if you want PDF compilation (e.g. brew install --cask mactex-no-gui or apt install texlive-latex-extra)."
fi

"$PYTHON_CMD" -m vita_tree.setup "$@"
