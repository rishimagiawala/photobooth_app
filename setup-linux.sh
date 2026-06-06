#!/usr/bin/env bash
# Create a Python virtual environment and install Linux dependencies.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT/.venv"
REQ_FILE="$ROOT/requirements-linux.txt"

die() {
  echo "error: $*" >&2
  exit 1
}

[[ "$(uname -s)" == "Linux" ]] || die "this script is for Linux only"

command -v python3 >/dev/null 2>&1 || die "python3 is not installed"

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "python3-venv is not available; installing system packages..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-pip
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --needed python python-pip
  else
    die "install python3-venv with your package manager, then re-run this script"
  fi
fi

[[ -f "$REQ_FILE" ]] || die "missing $REQ_FILE"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "creating virtual environment at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
else
  echo "using existing virtual environment at $VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
pip install -r "$REQ_FILE"

echo
echo "Setup complete."
echo
echo "Activate the environment:"
echo "  source \"$VENV_DIR/bin/activate\""
echo
echo "Run the app:"
echo "  python app.py"
echo
echo "Optional booth hardware setup (camera, serial, printing):"
echo "  sudo apt install cups cups-client printer-driver-gutenprint v4l-utils"
echo "  sudo usermod -aG video,dialout \"\$USER\""
echo "Then log out and back in. See README.md for printer and card reader config."
