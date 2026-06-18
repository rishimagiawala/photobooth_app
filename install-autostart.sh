#!/usr/bin/env bash
# Register the photobooth app to start automatically when you log in.
#
# Run once from the photobooth folder (e.g. ~/Desktop/photobooth_app):
#   bash install-autostart.sh
set -euo pipefail

if grep -q $'\r' "${BASH_SOURCE[0]}" 2>/dev/null; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}"
  exec bash "${BASH_SOURCE[0]}" "$@"
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_SCRIPT="$ROOT/start-photobooth.sh"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/photobooth.desktop"

info() {
  echo "==> $*"
}

[[ -f "$ROOT/app.py" ]] || {
  echo "error: app.py not found in $ROOT" >&2
  exit 1
}

[[ -f "$START_SCRIPT" ]] || {
  echo "error: missing start-photobooth.sh" >&2
  exit 1
}

fix_crlf() {
  if grep -q $'\r' "$START_SCRIPT" 2>/dev/null; then
    sed -i 's/\r$//' "$START_SCRIPT"
  fi
}

fix_crlf
chmod +x "$START_SCRIPT"
mkdir -p "$AUTOSTART_DIR"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Photobooth
Comment=Photobooth kiosk application
Exec=$START_SCRIPT
Path=$ROOT
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
Hidden=false
EOF

echo
echo "Autostart installed."
echo
echo "  App folder:  $ROOT"
echo "  Launcher:    $START_SCRIPT"
echo "  Autostart:   $DESKTOP_FILE"
echo "  Log file:    $ROOT/photobooth.log"
echo
echo "The app will start automatically the next time you log in."
echo "Reboot or log out and back in to test it."
echo
echo "Test manually now:"
echo "  bash \"$START_SCRIPT\""
echo
echo "Remove autostart later:"
echo "  rm \"$DESKTOP_FILE\""
