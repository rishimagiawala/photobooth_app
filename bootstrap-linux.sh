#!/usr/bin/env bash
# Fresh-machine bootstrap for a Linux booth PC.
#
# Installs git, clones the app, checks out linux-searbreeze, then runs
# the full installer (Python env, printer drivers, autostart, auto-login).
#
# On a new booth PC, run:
#   bash bootstrap-linux.sh
#
# The app is cloned to ~/photobooth_app unless PHOTOBOOTH_DIR is set.
# You will be prompted for sudo.
set -euo pipefail

if [[ -f "${BASH_SOURCE[0]}" ]] && grep -q $'\r' "${BASH_SOURCE[0]}" 2>/dev/null; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}"
  exec bash "${BASH_SOURCE[0]}" "$@"
fi

REPO_URL="https://github.com/rishimagiawala/photobooth_app.git"
BRANCH="linux-searbreeze"
DEST="${PHOTOBOOTH_DIR:-$HOME/photobooth_app}"

die() {
  echo "error: $*" >&2
  exit 1
}

info() {
  echo "==> $*"
}

install_git() {
  if command -v git >/dev/null 2>&1; then
    info "git is already installed ($(git --version))"
    return
  fi

  info "installing git (sudo required)"
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y git ca-certificates
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y git
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --needed git
  else
    die "unsupported package manager; install git manually and re-run"
  fi

  command -v git >/dev/null 2>&1 || die "git installation failed"
}

clone_repo() {
  if [[ -d "$DEST/.git" ]]; then
    info "using existing clone at $DEST"
    return
  fi

  [[ -e "$DEST" ]] && die "$DEST already exists and is not a git repository"

  info "cloning $REPO_URL"
  git clone "$REPO_URL" "$DEST"
}

checkout_branch() {
  info "checking out $BRANCH"
  git -C "$DEST" checkout "$BRANCH"
}

run_install() {
  local install_script="$DEST/install-linux.sh"
  [[ -f "$install_script" ]] || die "missing install-linux.sh in $DEST"

  if grep -q $'\r' "$install_script" 2>/dev/null; then
    info "fixing Windows line endings in install-linux.sh"
    sed -i 's/\r$//' "$install_script"
  fi

  echo
  info "running install-linux.sh"
  echo
  cd "$DEST"
  bash "$install_script"
}

main() {
  [[ "$(uname -s)" == "Linux" ]] || die "this script is for Linux only"

  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    die "run this as your normal user, not with sudo. The script will ask for sudo when it needs it."
  fi

  install_git
  clone_repo
  checkout_branch
  run_install
}

main "$@"
