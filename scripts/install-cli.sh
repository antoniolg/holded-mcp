#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but not found in PATH." >&2
  exit 1
fi

cd "$repo_dir"
uv tool install -e .
uv tool update-shell

printf '\nInstalled holded-cli in editable mode.\n'
printf 'If `holded-cli` is not found, restart your shell or ensure the uv tools dir is on PATH:\n'
printf '  %s\n' "$(uv tool dir)"
