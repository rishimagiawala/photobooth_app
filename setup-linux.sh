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
# Prefer 3.11, but accept nearby CPython versions that ship on Mint/Ubuntu.
PREFERRED_PYTHONS=(python3.11 python3.12 python3.10 python3)
MIN_PY_MAJOR=3
MIN_PY_MINOR=10
SYSTEM_PYTHON=""
PYTHON="$VENV_DIR/bin/python"

die() {
  echo "error: $*" >&2
  exit 1
}

info() {
  echo "==> $*"
}

python_version_ok() {
  local bin="$1"
  "$bin" -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (${MIN_PY_MAJOR}, ${MIN_PY_MINOR}) else 1)" >/dev/null 2>&1
}

python_has_venv() {
  local bin="$1"
  # On Debian/Ubuntu/Mint, `import venv` can succeed while ensurepip is missing
  # until the matching python3.x-venv package is installed.
  "$bin" -c 'import venv, ensurepip' >/dev/null 2>&1
}

python_minor_version() {
  local bin="$1"
  "$bin" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")'
}

find_usable_python() {
  local candidate
  for candidate in "${PREFERRED_PYTHONS[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1 \
        && python_version_ok "$candidate" \
        && python_has_venv "$candidate"; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

install_venv_for_python() {
  local bin="$1"
  local minor
  minor="$(python_minor_version "$bin")" || return 1

  if command -v apt-get >/dev/null 2>&1; then
    info "installing python${minor}-venv (required for virtualenvs on Mint/Ubuntu)"
    sudo apt-get update
    sudo apt-get install -y "python${minor}-venv" "python${minor}-dev" || \
      sudo apt-get install -y python3-venv python3-dev
    return 0
  fi

  return 1
}

venv_has_pip() {
  [[ -x "$PYTHON" ]] && "$PYTHON" -m pip --version >/dev/null 2>&1
}

venv_is_empty() {
  ! venv_has_pip || [[ "$("$PYTHON" -m pip list --format=freeze 2>/dev/null | wc -l)" -lt 2 ]]
}

install_runtime_libs_apt() {
  # Required for PySide6's xcb platform plugin on Mint/Ubuntu.
  local required=(
    build-essential
    libgl1
    libglib2.0-0
    libfontconfig1
    libdbus-1-3
    libxkbcommon0
    libxkbcommon-x11-0
    libegl1
    libxcb-cursor0
    libxcb-icccm4
    libxcb-image0
    libxcb-keysyms1
    libxcb-render-util0
    libxcb-xinerama0
    libxcb-shape0
    libxcb-randr0
    libxcb-xfixes0
  )

  local pkg
  local to_install=()
  for pkg in "${required[@]}"; do
    if apt-cache show "$pkg" >/dev/null 2>&1; then
      to_install+=("$pkg")
    else
      echo "note: package not available on this distro: $pkg"
    fi
  done

  sudo apt-get install -y "${to_install[@]}"
}

is_ubuntu_family() {
  [[ -f /etc/os-release ]] || return 1
  # shellcheck source=/dev/null
  source /etc/os-release
  case "${ID:-}" in
    ubuntu|linuxmint|pop|elementary|zorin) return 0 ;;
  esac
  case " ${ID_LIKE:-} " in
    *" ubuntu "*|*" debian "*) return 0 ;;
  esac
  return 1
}

ensure_python311_apt_repo() {
  # Prefer python3.11 when the distro can provide it; otherwise we fall back.
  if apt-cache show "python3.11" >/dev/null 2>&1; then
    return 0
  fi

  [[ -f /etc/os-release ]] || return 1
  # shellcheck source=/dev/null
  source /etc/os-release

  if is_ubuntu_family; then
    info "Python 3.11 is not in the default repos; adding deadsnakes PPA"
    sudo apt-get install -y software-properties-common ca-certificates gnupg
    # Mint/Pop need the Ubuntu base codename (jammy/noble), not the Mint one.
    if [[ -n "${UBUNTU_CODENAME:-}" ]]; then
      info "using Ubuntu base codename: $UBUNTU_CODENAME"
      if ! sudo add-apt-repository -y "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu ${UBUNTU_CODENAME} main"; then
        sudo add-apt-repository -y ppa:deadsnakes/ppa || true
      fi
    else
      sudo add-apt-repository -y ppa:deadsnakes/ppa || true
    fi
    sudo apt-get update || true
    return 0
  fi

  case "${ID:-}" in
    debian)
      case "${VERSION_CODENAME:-}" in
        bookworm|trixie|sid) return 0 ;;
        *) return 1 ;;
      esac
      ;;
    *)
      return 1
      ;;
  esac
}

install_apt_python_packages() {
  local minor="$1"
  sudo apt-get install -y \
    "python${minor}" \
    "python${minor}-venv" \
    "python${minor}-dev"
}

install_apt_packages() {
  info "installing Python and system packages (sudo required)..."
  sudo apt-get update
  ensure_python311_apt_repo || true

  # Try preferred versions from apt, then use whatever usable interpreter exists.
  local minor
  for minor in 3.11 3.12 3.10; do
    if apt-cache show "python${minor}" >/dev/null 2>&1; then
      info "installing python${minor} from apt"
      if install_apt_python_packages "$minor"; then
        SYSTEM_PYTHON="python${minor}"
        break
      fi
    fi
  done

  if [[ -z "$SYSTEM_PYTHON" ]]; then
    info "specific Python package not found; installing python3 + venv"
    sudo apt-get install -y python3 python3-venv python3-dev
  fi

  install_runtime_libs_apt
}

install_dnf_packages() {
  info "installing Python and system packages (sudo required)..."
  local minor
  for minor in 3.11 3.12 3.10; do
    if sudo dnf install -y \
        "python${minor}" \
        "python${minor}-pip" \
        "python${minor}-devel"; then
      SYSTEM_PYTHON="python${minor}"
      break
    fi
  done

  [[ -n "$SYSTEM_PYTHON" ]] || sudo dnf install -y python3 python3-pip python3-devel

  sudo dnf install -y \
    gcc \
    gcc-c++ \
    mesa-libGL \
    libXkbcommon-x11 \
    libxcb \
    fontconfig \
    dbus-libs
}

install_pacman_packages() {
  info "installing Python and system packages (sudo required)..."
  sudo pacman -Sy --needed \
    python \
    base-devel \
    mesa \
    libxkbcommon-x11 \
    fontconfig \
    dbus
  SYSTEM_PYTHON="python3"
}

ensure_system_python() {
  if SYSTEM_PYTHON="$(find_usable_python)"; then
    info "found $($SYSTEM_PYTHON --version)"
    return 0
  fi

  # Common Mint/Ubuntu case: python3.12 is installed, but python3.12-venv is not.
  local candidate
  for candidate in "${PREFERRED_PYTHONS[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1 \
        && python_version_ok "$candidate" \
        && ! python_has_venv "$candidate"; then
      info "found $candidate but ensurepip/venv support is missing"
      install_venv_for_python "$candidate" || true
      if python_has_venv "$candidate"; then
        SYSTEM_PYTHON="$candidate"
        info "using $($SYSTEM_PYTHON --version)"
        return 0
      fi
    fi
  done

  info "no suitable Python ${MIN_PY_MAJOR}.${MIN_PY_MINOR}+ with venv found; installing"
  if command -v apt-get >/dev/null 2>&1; then
    install_apt_packages
  elif command -v dnf >/dev/null 2>&1; then
    install_dnf_packages
  elif command -v pacman >/dev/null 2>&1; then
    install_pacman_packages
  else
    die "unsupported package manager; install Python ${MIN_PY_MAJOR}.${MIN_PY_MINOR}+ manually and re-run"
  fi

  SYSTEM_PYTHON="$(find_usable_python)" \
    || die "could not find Python ${MIN_PY_MAJOR}.${MIN_PY_MINOR}+ with venv after package install"

  info "using $($SYSTEM_PYTHON --version)"
}

create_venv() {
  info "creating virtual environment at $VENV_DIR with $SYSTEM_PYTHON"
  rm -rf "$VENV_DIR"
  if ! "$SYSTEM_PYTHON" -m venv --upgrade-deps "$VENV_DIR" 2>/dev/null \
      && ! "$SYSTEM_PYTHON" -m venv "$VENV_DIR"; then
    rm -rf "$VENV_DIR"
    info "venv creation failed; trying to install the matching python*-venv package"
    install_venv_for_python "$SYSTEM_PYTHON" \
      || die "failed to install venv support for $SYSTEM_PYTHON"
    python_has_venv "$SYSTEM_PYTHON" \
      || die "ensurepip still missing for $SYSTEM_PYTHON after installing venv package"
    if "$SYSTEM_PYTHON" -m venv --help 2>/dev/null | grep -q -- '--upgrade-deps'; then
      "$SYSTEM_PYTHON" -m venv --upgrade-deps "$VENV_DIR"
    else
      "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
    fi
  fi
  [[ -x "$PYTHON" ]] || die "virtual environment was not created at $VENV_DIR"
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
    if ! python_version_ok "$PYTHON"; then
      info "existing venv is older than Python ${MIN_PY_MAJOR}.${MIN_PY_MINOR}; recreating"
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

  # opencv-python ships Qt plugins that break PySide6; always prefer headless.
  if "$PYTHON" -m pip show opencv-python >/dev/null 2>&1; then
    info "removing opencv-python so opencv-python-headless can take over"
    "$PYTHON" -m pip uninstall -y opencv-python
  fi

  info "installing Python packages from requirements-linux.txt"
  "$PYTHON" -m pip install -r "$REQ_FILE"
}

verify_install() {
  info "verifying Python version and imports"
  "$PYTHON" - <<PY
import importlib
import sys

if sys.version_info[:2] < (${MIN_PY_MAJOR}, ${MIN_PY_MINOR}):
    print(
        f"verification failed: expected Python >= ${MIN_PY_MAJOR}.${MIN_PY_MINOR}, got {sys.version.split()[0]}",
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

configure_device_groups() {
  local fix_script="$ROOT/fix-device-permissions.sh"
  if [[ -f "$fix_script" ]]; then
    bash "$fix_script"
  fi
}

main() {
  [[ "$(uname -s)" == "Linux" ]] || die "this script is for Linux only"
  [[ -f "$REQ_FILE" ]] || die "missing $REQ_FILE"

  ensure_system_python
  ensure_venv
  install_requirements
  verify_install
  configure_device_groups

  echo
  echo "Setup complete."
  echo
  echo "Activate the environment:"
  echo "  source \"$VENV_DIR/bin/activate\""
  echo
  echo "Run the app:"
  echo "  python app.py"
  echo
  echo "Optional booth hardware setup (printing):"
  echo "  sudo apt install cups cups-client printer-driver-gutenprint v4l-utils"
  echo "See README.md for printer and card reader config."
}

main "$@"
