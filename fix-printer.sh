#!/usr/bin/env bash
# Re-point the photobooth's CUPS print queue at the DS-RX1 that is currently
# plugged in. Useful when moving the PC to a different physical printer of the
# same model (the USB device URI is tied to each unit's serial number).
#
# Run manually after plugging in the printer:
#   bash fix-printer.sh
#
# It is also called automatically (with --noninteractive) by
# start-photobooth.sh, where it only acts if the connected printer changed.
set -euo pipefail

if grep -q $'\r' "${BASH_SOURCE[0]}" 2>/dev/null; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}"
  exec bash "${BASH_SOURCE[0]}" "$@"
fi

# Must match DEFAULT_PRINTER in printing.py so the app keeps finding it.
QUEUE="Dai_Nippon_Printing_DS-RX1"

# Non-interactive mode (used at startup): never prompt for a sudo password.
SUDO="sudo"
QUIET="false"
if [[ "${1:-}" == "--noninteractive" ]]; then
  SUDO="sudo -n"
  QUIET="true"
fi

log() {
  [[ "$QUIET" == "true" ]] || echo "$*"
}

# Find the connected DS-RX1 device URI.
uri="$(lpinfo -v 2>/dev/null | grep -iE 'dsrx1|dnp' | awk '{print $2}' | head -n1 || true)"

if [[ -z "$uri" ]]; then
  log "error: no DS-RX1 detected. Plug it in and power it on, then run again."
  exit 1
fi

# What is the queue pointed at right now?
current="$(lpstat -v "$QUEUE" 2>/dev/null | sed -n 's/^device for [^:]*: //p' || true)"

if [[ -z "$current" ]]; then
  log "error: print queue '$QUEUE' does not exist."
  log "Create it once at http://localhost:631 named exactly '$QUEUE', then re-run."
  exit 1
fi

# Already correct -> do nothing (and avoid needing sudo at all).
if [[ "$current" == "$uri" ]]; then
  log "Printer queue '$QUEUE' is already linked to the connected printer."
  exit 0
fi

log "Connected printer changed:"
log "  was: $current"
log "  now: $uri"
log "Updating queue '$QUEUE'..."

$SUDO lpadmin -p "$QUEUE" -v "$uri"
$SUDO cupsenable "$QUEUE"
$SUDO cupsaccept "$QUEUE"

log "Done. '$QUEUE' now points at the connected printer."
