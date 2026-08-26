#!/usr/bin/env bash
# Build and install Gutenprint 5.3.4 plus selphy_print on a Linux booth PC.
#
# From the project folder, run:
#   bash driver-setup.sh
set -euo pipefail

if grep -q $'\r' "${BASH_SOURCE[0]}" 2>/dev/null; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}"
  exec bash "${BASH_SOURCE[0]}" "$@"
fi

GUTENPRINT_VERSION="5.3.4"
GUTENPRINT_TARBALL="gutenprint-${GUTENPRINT_VERSION}.tar.xz"
GUTENPRINT_URL="https://sourceforge.net/projects/gimp-print/files/gutenprint-5.3/${GUTENPRINT_VERSION}/${GUTENPRINT_TARBALL}"
SELPHY_REPO="https://git.shaftnet.org/gitea/slp/selphy_print.git"
WORK_DIR="${TMPDIR:-/tmp}/photobooth-driver-setup"
JOBS="${JOBS:-4}"

die() {
  echo "error: $*" >&2
  exit 1
}

info() {
  echo "==> $*"
}

require_apt() {
  command -v apt-get >/dev/null 2>&1 || die "this script expects apt-get (Debian/Ubuntu)"
}

remove_stock_drivers() {
  info "removing packaged gutenprint, ipp-usb, and sane-airscan"
  sudo apt-get remove -y '*gutenprint*' ipp-usb sane-airscan || true
}

install_build_deps() {
  info "installing build dependencies"
  sudo apt-get update
  sudo apt-get install -y \
    build-essential \
    wget \
    git \
    cups \
    cups-client \
    libusb-1.0-0-dev \
    libcups2-dev \
    git-lfs
}

build_gutenprint() {
  info "downloading Gutenprint ${GUTENPRINT_VERSION}"
  mkdir -p "$WORK_DIR"
  cd "$WORK_DIR"

  if [[ ! -f "$GUTENPRINT_TARBALL" ]]; then
    wget -O "$GUTENPRINT_TARBALL" "$GUTENPRINT_URL"
  else
    info "using existing $GUTENPRINT_TARBALL"
  fi

  info "extracting Gutenprint"
  rm -rf "gutenprint-${GUTENPRINT_VERSION}"
  tar -xJf "$GUTENPRINT_TARBALL"

  info "compiling Gutenprint"
  cd "gutenprint-${GUTENPRINT_VERSION}"
  ./configure --without-doc
  make -j"$JOBS"
  sudo make install
  cd "$WORK_DIR"
}

refresh_cups() {
  info "refreshing CUPS PPDs"
  sudo cups-genppdupdate

  info "restarting CUPS"
  sudo systemctl restart cups
}

build_selphy_print() {
  info "getting selphy_print"
  cd "$WORK_DIR"

  if [[ -d selphy_print/.git ]]; then
    info "updating existing selphy_print checkout"
    git -C selphy_print pull --ff-only
  else
    rm -rf selphy_print
    git clone "$SELPHY_REPO"
  fi

  info "compiling selphy_print"
  cd selphy_print
  make -j"$JOBS"
  sudo make install
}

configure_library_path() {
  info "setting library include path"
  echo "/usr/local/lib" | sudo tee /etc/ld.so.conf.d/usr-local.conf >/dev/null
  sudo ldconfig
}

main() {
  [[ "$(uname -s)" == "Linux" ]] || die "this script is for Linux only"
  require_apt

  remove_stock_drivers
  install_build_deps
  build_gutenprint
  refresh_cups
  build_selphy_print
  configure_library_path

  echo
  echo "Printer driver setup complete."
  echo "Build files are in $WORK_DIR"
  echo "Add the printer in CUPS at http://localhost:631"
}

main "$@"
