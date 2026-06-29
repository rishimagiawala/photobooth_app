#!/usr/bin/env bash
# Launch the photobooth app using the project virtual environment.
set -euo pipefail

if grep -q $'\r' "${BASH_SOURCE[0]}" 2>/dev/null; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}"
  exec bash "${BASH_SOURCE[0]}" "$@"
fi

PHOTOBOOTH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PHOTOBOOTH_DIR/.venv/bin/python"
LOG_FILE="$PHOTOBOOTH_DIR/photobooth.log"

cd "$PHOTOBOOTH_DIR"

if [[ ! -x "$VENV_PYTHON" ]]; then
  {
    echo "$(date -Is) error: virtual environment not found at $VENV_PYTHON"
    echo "Run: bash install-linux.sh"
  } >> "$LOG_FILE"
  exit 1
fi

{
  echo "$(date -Is) starting photobooth from $PHOTOBOOTH_DIR"
} >> "$LOG_FILE"

# Best-effort: point the print queue at whatever DS-RX1 is connected. Only acts
# if the printer changed, and must never block the app from launching (e.g. if
# the printer is off or a sudo password would be required).
if [[ -f "$PHOTOBOOTH_DIR/fix-printer.sh" ]]; then
  bash "$PHOTOBOOTH_DIR/fix-printer.sh" --noninteractive >> "$LOG_FILE" 2>&1 \
    || echo "$(date -Is) printer auto-link skipped (using existing/default printer)" >> "$LOG_FILE"
fi

exec "$VENV_PYTHON" "$PHOTOBOOTH_DIR/app.py" >> "$LOG_FILE" 2>&1
