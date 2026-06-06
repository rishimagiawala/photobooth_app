#!/usr/bin/env bash
# One-command Linux installer for the photobooth app.
#
# From the project folder, run:
#   bash install-linux.sh
#
# No chmod or manual cleanup required.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_SCRIPT="$ROOT/setup-linux.sh"
VENV_DIR="$ROOT/.venv"

info() {
  echo "==> $*"
}

fix_crlf() {
  local file="$1"
  if [[ -f "$file" ]] && grep -q $'\r' "$file" 2>/dev/null; then
    info "fixing Windows line endings in $(basename "$file")"
    sed -i 's/\r$//' "$file"
  fi
}

venv_is_broken() {
  [[ ! -d "$VENV_DIR" ]] && return 1
  [[ ! -x "$VENV_DIR/bin/python" ]] && return 0
  ! "$VENV_DIR/bin/python" -m pip --version >/dev/null 2>&1 && return 0
  [[ "$("$VENV_DIR/bin/python" -m pip list --format=freeze 2>/dev/null | wc -l)" -lt 2 ]]
}

fix_crlf "$ROOT/install-linux.sh"
fix_crlf "$SETUP_SCRIPT"

[[ -f "$SETUP_SCRIPT" ]] || {
  echo "error: missing setup-linux.sh next to install-linux.sh" >&2
  exit 1
}

if venv_is_broken; then
  info "removing broken or empty virtual environment"
  rm -rf "$VENV_DIR"
fi

chmod +x "$SETUP_SCRIPT"
exec bash "$SETUP_SCRIPT" "$@"
