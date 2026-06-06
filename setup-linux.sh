#!/usr/bin/env bash
# Install Python 3.11, create a virtual environment, and install Linux dependencies.
# Prefer running: bash install-linux.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if grep -q $'\r' "${BASH_SOURCE[0]}" 2>/dev/null; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}"
  exec bash "${BASH_SOURCE[0]}" "$@"
fi

VENV_DIR="$ROOT/.venv"
REQ_FILE="$ROOT/requirements-linux.txt"
PY_MINOR="3.11"
SYSTEM_PYTHON="python${PY_MINOR}"
PYTHON="$VENV_DIR/bin/python"

die() {
  echo "error: $*" >&2
  exit 1
}

info() {
  echo "==> $*"
}

venv_has_pip() {
  [[ -x "$PYTHON" ]] && "$PYTHON" -m pip --version >/dev/null 2>&1
}

venv_is_empty() {
  ! venv_has_pip || [[ "$("$PYTHON" -m pip list --format=freeze 2>/dev/null | wc -l)" -lt 2 ]]
}

install_runtime_libs_apt() {
  local optional=(
    libxcb-cursor0
    libxcb-icccm4
    libxcb-image0
    libxcb-keysyms1
    libxcb-render-util0
    libxcb-xinerama0
  )

  sudo apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libfontconfig1 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libegl1

  for pkg in "${optional[@]}"; do
    if apt-cache show "$pkg" >/dev/null 2>&1; then
      sudo apt-get install -y "$pkg"
    else
      echo "note: optional package not available on this distro: $pkg"
    fi
  done
}

ensure_python311_apt_repo() {
  if apt-cache show "python${PY_MINOR}" >/dev/null 2>&1; then
    return 0
  fi

  [[ -f /etc/os-release ]] || die "Python ${PY_MINOR} is not available from apt on this system"

  # shellcheck source=/dev/null
  source /etc/os-release

  case "${ID:-}" in
    ubuntu)
      info "Python ${PY_MINOR} is not in the default Ubuntu repos; adding deadsnakes PPA"
      sudo apt-get install -y software-properties-common ca-certificates gnupg
      sudo add-apt-repository -y ppa:deadsnakes/ppa
      sudo apt-get update
      ;;
    debian)
      case "${VERSION_CODENAME:-}" in
        bookworm)
          return 0
          ;;
        bullseye)
          die "Debian 11 does not ship Python ${PY_MINOR} by default. Upgrade to Debian 12 (bookworm) or install Python ${PY_MINOR} manually."
          ;;
        *)
          die "Could not find Python ${PY_MINOR} for Debian ${VERSION_CODENAME:-unknown}. Install it manually and re-run."
          ;;
      esac
      ;;
    *)
      die "Python ${PY_MINOR} is not available from apt on ${ID:-this distro}. Install it manually and re-run."
      ;;
  esac

  apt-cache show "python${PY_MINOR}" >/dev/null 2>&1 \
    || die "Python ${PY_MINOR} package still not found after repo setup"
}

install_apt_packages() {
  info "installing Python ${PY_MINOR} and system packages (sudo required)..."
  sudo apt-get update
  ensure_python311_apt_repo

  sudo apt-get install -y \
    "python${PY_MINOR}" \
    "python${PY_MINOR}-venv" \
    "python${PY_MINOR}-dev"

  install_runtime_libs_apt
}

install_dnf_packages() {
  info "installing Python ${PY_MINOR} and system packages (sudo required)..."
  sudo dnf install -y \
    "python${PY_MINOR}" \
    "python${PY_MINOR}-pip" \
    "python${PY_MINOR}-devel" \
    gcc \
    gcc-c++ \
    mesa-libGL \
    libXkbcommon-x11 \
    libxcb \
    fontconfig \
    dbus-libs
}

install_pacman_packages() {
  if pacman -Si "python${PY_MINOR}" >/dev/null 2>&1; then
    info "installing Python ${PY_MINOR} and system packages (sudo required)..."
    sudo pacman -Sy --needed \
      "python${PY_MINOR}" \
      base-devel \
      mesa \
      libxkbcommon-x11 \
      fontconfig \
      dbus
    SYSTEM_PYTHON="python${PY_MINOR}"
    return 0
  fi

  die "Arch Linux does not provide Python ${PY_MINOR} in the official repos. Use an Ubuntu/Debian-based booth image, or install Python ${PY_MINOR} manually and re-run."
}

ensure_system_python() {
  if command -v "$SYSTEM_PYTHON" >/dev/null 2>&1 \
      && "$SYSTEM_PYTHON" -c 'import venv' >/dev/null 2>&1; then
    info "found $($SYSTEM_PYTHON --version)"
    return 0
  fi

  info "Python ${PY_MINOR} is not installed"
  if command -v apt-get >/dev/null 2>&1; then
    install_apt_packages
  elif command -v dnf >/dev/null 2>&1; then
    install_dnf_packages
  elif command -v pacman >/dev/null 2>&1; then
    install_pacman_packages
  else
    die "unsupported package manager; install Python ${PY_MINOR} manually and re-run"
  fi

  command -v "$SYSTEM_PYTHON" >/dev/null 2>&1 \
    || die "Python ${PY_MINOR} installation failed"
  "$SYSTEM_PYTHON" -c 'import venv' >/dev/null 2>&1 \
    || die "python${PY_MINOR}-venv is not available after install"

  info "using $($SYSTEM_PYTHON --version)"
}

create_venv() {
  info "creating virtual environment at $VENV_DIR with $SYSTEM_PYTHON"
  if "$SYSTEM_PYTHON" -m venv --help 2>/dev/null | grep -q -- '--upgrade-deps'; then
    "$SYSTEM_PYTHON" -m venv --upgrade-deps "$VENV_DIR"
  else
    "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
  fi
}

ensure_venv() {
  if [[ -d "$VENV_DIR" ]] && venv_is_empty; then
    info "removing broken or empty virtual environment"
    rm -rf "$VENV_DIR"
  fi

  if [[ ! -d "$VENV_DIR" ]]; then
    create_venv
  else
    info "using existing virtual environment at $VENV_DIR"
    if ! "$PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 11)' >/dev/null 2>&1; then
      info "existing venv is not Python 3.11; recreating"
      rm -rf "$VENV_DIR"
      create_venv
    fi
  fi

  if ! venv_has_pip; then
    info "bootstrapping pip inside the virtual environment"
    "$PYTHON" -m ensurepip --upgrade
  fi

  venv_has_pip || die "pip is not available inside $VENV_DIR"
}

install_requirements() {
  info "upgrading pip"
  "$PYTHON" -m pip install --upgrade pip wheel setuptools

  info "installing Python packages from requirements-linux.txt"
  "$PYTHON" -m pip install -r "$REQ_FILE"
}

verify_install() {
  info "verifying Python version and imports"
  "$PYTHON" - <<'PY'
import importlib
import sys

if sys.version_info[:2] != (3, 11):
    print(
        f"verification failed: expected Python 3.11, got {sys.version.split()[0]}",
        file=sys.stderr,
    )
    sys.exit(1)

required = ("PySide6", "cv2", "serial", "PIL", "imutils", "numpy")
missing = []
for name in required:
    try:
        importlib.import_module(name)
    except ImportError as exc:
        missing.append(f"{name}: {exc}")

if missing:
    print("verification failed:", file=sys.stderr)
    for line in missing:
        print(f"  - {line}", file=sys.stderr)
    sys.exit(1)

print(f"Python {sys.version.split()[0]} with all required packages is ready")
PY
}

main() {
  [[ "$(uname -s)" == "Linux" ]] || die "this script is for Linux only"
  [[ -f "$REQ_FILE" ]] || die "missing $REQ_FILE"

  ensure_system_python
  ensure_venv
  install_requirements
  verify_install

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
}

main "$@"
