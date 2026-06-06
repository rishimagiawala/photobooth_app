#!/usr/bin/env bash
# Fix Linux permissions for USB serial (card reader) and camera devices.
#
# Run once, then log out and back in (or reboot):
#   bash fix-device-permissions.sh
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "error: this script is for Linux only" >&2
  exit 1
fi

if grep -q $'\r' "${BASH_SOURCE[0]}" 2>/dev/null; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}"
  exec bash "${BASH_SOURCE[0]}" "$@"
fi

info() {
  echo "==> $*"
}

added=()

for group in dialout video; do
  if ! getent group "$group" >/dev/null 2>&1; then
    echo "note: group '$group' does not exist on this system; skipping"
    continue
  fi

  if id -nG "$USER" | tr ' ' '\n' | grep -qx "$group"; then
    info "already in '$group' group"
  else
    info "adding $USER to '$group' group (sudo required)"
    sudo usermod -aG "$group" "$USER"
    added+=("$group")
  fi
done

echo
if ((${#added[@]} > 0)); then
  echo "Added $USER to: ${added[*]}"
  echo
  echo "IMPORTANT: log out and back in, or reboot, before running the app again."
  echo "Group changes do not apply to an already-open session."
  echo
  echo "Quick test without logging out (current terminal only):"
  echo "  newgrp dialout"
  echo "  source .venv/bin/activate"
  echo "  python app.py"
else
  echo "Device groups are already configured for $USER."
  echo
  echo "If you still get 'Permission denied' on a serial port, log out and back in,"
  echo "or reboot, then try again."
fi

echo
echo "Your card reader path looks correct if it is under /dev/serial/by-id/."
echo "Set it in config/card_reader/reader.json or the Reader settings window."
