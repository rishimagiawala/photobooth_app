#!/usr/bin/env bash
# One-command Linux installer for the photobooth booth PC.
#
# Installs the Python app, printer drivers, login autostart, and auto-login.
#
# From the project folder, run:
#   bash install-linux.sh
#
# No chmod or manual cleanup required. You will be prompted for sudo.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SETUP_SCRIPT="$ROOT/setup-linux.sh"
DRIVER_SCRIPT="$ROOT/driver-setup.sh"
AUTOSTART_SCRIPT="$ROOT/install-autostart.sh"
AUTOLOGIN_SCRIPT="$ROOT/enable-autologin.sh"
VENV_DIR="$ROOT/.venv"

info() {
  echo "==> $*"
}

die() {
  echo "error: $*" >&2
  exit 1
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

run_step() {
  local label="$1"
  local script="$2"
  shift 2

  [[ -f "$script" ]] || die "missing $(basename "$script")"
  fix_crlf "$script"
  chmod +x "$script"

  echo
  info "$label"
  echo
  bash "$script" "$@"
}

fix_crlf "$ROOT/install-linux.sh"

if [[ "$(uname -s)" != "Linux" ]]; then
  die "this script is for Linux only"
fi

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  die "run this as your normal user, not with sudo. The script will ask for sudo when it needs it."
fi

if venv_is_broken; then
  info "removing broken or empty virtual environment"
  rm -rf "$VENV_DIR"
fi

export PHOTOBOOTH_NESTED=1
run_step "1/4  Python environment and app dependencies" "$SETUP_SCRIPT" "$@"
unset PHOTOBOOTH_NESTED

run_step "2/4  Printer drivers (Gutenprint + selphy_print)" "$DRIVER_SCRIPT"
run_step "3/4  Autostart on login" "$AUTOSTART_SCRIPT"
run_step "4/4  Auto-login at boot" "$AUTOLOGIN_SCRIPT"

echo
echo "Booth install complete."
echo
echo "  App folder:  $ROOT"
echo "  Autostart:   $HOME/.config/autostart/photobooth.desktop"
echo "  Log file:    $ROOT/photobooth.log"
echo
echo "Next steps:"
echo "  1. Add the printer in CUPS at http://localhost:631"
echo "  2. Reboot to test auto-login and autostart:"
echo "       sudo reboot"
echo
