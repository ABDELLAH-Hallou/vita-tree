#!/usr/bin/env bash
set -euo pipefail

version=""
if (( $# )); then version=$1; fi
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo 'Usage: bash setup.sh VERSION [--no-browser] [--repository PATH]' >&2
    exit 2
fi
shift

python=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
        python=$candidate
        break
    fi
done
if [[ -z "$python" ]] || ! command -v git >/dev/null; then
    echo 'Install Python 3.10+ and Git with your system package manager, then rerun setup.' >&2
    exit 1
fi

bootstrap=$(mktemp)
trap 'rm -f -- "$bootstrap"' EXIT
url="https://raw.githubusercontent.com/ABDELLAH-Hallou/vita-tree/v$version/src/vita_tree/setup.py"
if ! curl --fail --silent --show-error --location --connect-timeout 10 --max-time 30 --output "$bootstrap" "$url"; then
    echo "Setup download failed. Check your connection and the published version $version, then retry." >&2
    exit 1
fi
"$python" -I "$bootstrap" --release "$version" "$@"
