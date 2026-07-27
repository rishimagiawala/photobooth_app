#!/usr/bin/env bash
# One-command booth setup after cloning.
#
# From the project folder:
#   bash setup-booth.sh
#
# Steps:
#   1) install-linux.sh     — Python venv + Linux dependencies
#   2) install-autostart.sh — launch app on desktop login
#   3) enable-autologin.sh  — boot straight to the desktop user
#   4) disable-sleep.sh     — no sleep / suspend / screen blank
#   5) start-photobooth.sh  — optional; only with --start
#
# Flags:
#   --start     launch the app when setup finishes (blocks this terminal)
#   --no-start  skip launching (default)
set -euo pipefail

if grep -q $'\r' "${BASH_SOURCE[0]}" 2>/dev/null; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}"
  exec bash "${BASH_SOURCE[0]}" "$@"
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_APP=0

info() {
  echo "==> $*"
}

die() {
  echo "error: $*" >&2
  exit 1
}

usage() {
  cat <<EOF
Usage: bash setup-booth.sh [--start | --no-start]

One-command setup after cloning the photobooth repo.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --start) START_APP=1 ;;
    --no-start) START_APP=0 ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $arg (try --help)"
      ;;
  esac
done

if [[ "$(uname -s)" != "Linux" ]]; then
  die "this script is for Linux only"
fi

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  die "run this as your normal booth user, not root/sudo"
fi

cd "$ROOT"

[[ -f "$ROOT/app.py" ]] || die "app.py not found in $ROOT"
[[ -f "$ROOT/install-linux.sh" ]] || die "missing install-linux.sh"
[[ -f "$ROOT/install-autostart.sh" ]] || die "missing install-autostart.sh"
[[ -f "$ROOT/enable-autologin.sh" ]] || die "missing enable-autologin.sh"
[[ -f "$ROOT/disable-sleep.sh" ]] || die "missing disable-sleep.sh"
[[ -f "$ROOT/start-photobooth.sh" ]] || die "missing start-photobooth.sh"

fix_crlf() {
  local file="$1"
  if [[ -f "$file" ]] && grep -q $'\r' "$file" 2>/dev/null; then
    info "fixing Windows line endings in $(basename "$file")"
    sed -i 's/\r$//' "$file"
  fi
}

for script in \
  install-linux.sh \
  setup-linux.sh \
  install-autostart.sh \
  enable-autologin.sh \
  disable-sleep.sh \
  start-photobooth.sh \
  fix-printer.sh
do
  fix_crlf "$ROOT/$script"
  [[ -f "$ROOT/$script" ]] && chmod +x "$ROOT/$script"
done

echo
info "Step 1/4 — install dependencies and virtualenv"
bash "$ROOT/install-linux.sh"

echo
info "Step 2/4 — install desktop autostart"
bash "$ROOT/install-autostart.sh"

echo
info "Step 3/4 — enable automatic login"
bash "$ROOT/enable-autologin.sh"

echo
info "Step 4/4 — disable sleep / suspend / screen blanking"
bash "$ROOT/disable-sleep.sh"

echo
echo "=========================================="
echo " Booth setup complete."
echo "=========================================="
echo
echo "  App folder:  $ROOT"
echo "  Autostart:   $HOME/.config/autostart/photobooth.desktop"
echo "  Log file:    $ROOT/photobooth.log"
echo
echo "Reboot to test the full boot → login → app path:"
echo "  sudo reboot"
echo
echo "Or start the app now without rebooting:"
echo "  bash \"$ROOT/start-photobooth.sh\""
echo

if [[ "$START_APP" -eq 1 ]]; then
  info "Starting photobooth now (--start)"
  exec bash "$ROOT/start-photobooth.sh"
fi
