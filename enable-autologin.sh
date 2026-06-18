#!/usr/bin/env bash
# Enable automatic login so the booth boots straight to the desktop.
#
# Run once:
#   bash enable-autologin.sh
#
# Reboot afterward to test.
set -euo pipefail

if grep -q $'\r' "${BASH_SOURCE[0]}" 2>/dev/null; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}"
  exec bash "${BASH_SOURCE[0]}" "$@"
fi

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "error: this script is for Linux only" >&2
  exit 1
fi

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  echo "error: run this as your normal user, not with sudo" >&2
  echo "The script will ask for sudo when it needs to change system settings." >&2
  exit 1
fi

LOGIN_USER="${SUDO_USER:-$USER}"
BACKUP_SUFFIX="$(date +%Y%m%d-%H%M%S)"

info() {
  echo "==> $*"
}

detect_display_manager() {
  if [[ -f /etc/X11/default-display-manager ]]; then
    case "$(tr '[:upper:]' '[:lower:]' < /etc/X11/default-display-manager)" in
      *gdm*) echo "gdm"; return ;;
      *lightdm*) echo "lightdm"; return ;;
      *sddm*) echo "sddm"; return ;;
    esac
  fi

  for service in gdm gdm3 lightdm sddm; do
    if systemctl list-unit-files "${service}.service" >/dev/null 2>&1 \
        && systemctl is-enabled "${service}.service" >/dev/null 2>&1; then
      case "$service" in
        gdm|gdm3) echo "gdm"; return ;;
        lightdm) echo "lightdm"; return ;;
        sddm) echo "sddm"; return ;;
      esac
    fi
  done

  echo "unknown"
}

configure_gdm() {
  local conf="/etc/gdm3/custom.conf"
  local tmp
  tmp="$(mktemp)"

  info "configuring GDM auto-login for $LOGIN_USER"

  sudo mkdir -p /etc/gdm3
  if [[ -f "$conf" ]]; then
    sudo cp "$conf" "${conf}.bak.${BACKUP_SUFFIX}"
    sudo cat "$conf" > "$tmp"
  else
    echo "[daemon]" > "$tmp"
  fi

  grep -v '^AutomaticLoginEnable=' "$tmp" | grep -v '^AutomaticLogin=' > "${tmp}.clean"
  mv "${tmp}.clean" "$tmp"

  if grep -q '^\[daemon\]' "$tmp"; then
    awk -v user="$LOGIN_USER" '
      /^\[daemon\]/ {
        print
        print "AutomaticLoginEnable=true"
        print "AutomaticLogin=" user
        next
      }
      { print }
    ' "$tmp" > "${tmp}.out"
  else
    cat "$tmp" > "${tmp}.out"
    {
      echo
      echo "[daemon]"
      echo "AutomaticLoginEnable=true"
      echo "AutomaticLogin=$LOGIN_USER"
    } >> "${tmp}.out"
  fi

  sudo cp "${tmp}.out" "$conf"
  rm -f "$tmp" "${tmp}.out"
}

configure_lightdm() {
  local dropin="/etc/lightdm/lightdm.conf.d/50-photobooth-autologin.conf"

  info "configuring LightDM auto-login for $LOGIN_USER"
  sudo mkdir -p /etc/lightdm/lightdm.conf.d

  if [[ -f "$dropin" ]]; then
    sudo cp "$dropin" "${dropin}.bak.${BACKUP_SUFFIX}"
  fi

  sudo tee "$dropin" >/dev/null <<EOF
[Seat:*]
autologin-user=$LOGIN_USER
autologin-user-timeout=0
EOF
}

configure_sddm() {
  local dropin="/etc/sddm.conf.d/zz-photobooth-autologin.conf"
  local session=""

  info "configuring SDDM auto-login for $LOGIN_USER"
  sudo mkdir -p /etc/sddm.conf.d

  if [[ -f "$dropin" ]]; then
    sudo cp "$dropin" "${dropin}.bak.${BACKUP_SUFFIX}"
  fi

  if [[ -n "${XDG_CURRENT_DESKTOP:-}" ]]; then
    case "${XDG_CURRENT_DESKTOP,,}" in
      *kde*) session="plasma" ;;
      *)
        if command -v loginctl >/dev/null 2>&1; then
          session="$(loginctl show-user "$LOGIN_USER" -p Display 2>/dev/null | sed -n 's/.*Session=\([^;]*\).*/\1/p' | head -n1)"
        fi
        ;;
    esac
  fi

  if [[ -n "$session" ]]; then
    sudo tee "$dropin" >/dev/null <<EOF
[Autologin]
User=$LOGIN_USER
Session=$session
EOF
  else
    sudo tee "$dropin" >/dev/null <<EOF
[Autologin]
User=$LOGIN_USER
EOF
  fi
}

display_manager="$(detect_display_manager)"

echo
info "detected display manager: $display_manager"
info "auto-login user: $LOGIN_USER"
echo

case "$display_manager" in
  gdm)
    configure_gdm
    ;;
  lightdm)
    configure_lightdm
    ;;
  sddm)
    configure_sddm
    ;;
  *)
    echo "error: could not detect a supported display manager (GDM, LightDM, or SDDM)." >&2
    echo "Check with: cat /etc/X11/default-display-manager" >&2
    exit 1
    ;;
esac

echo
echo "Auto-login enabled for user: $LOGIN_USER"
echo
echo "Reboot to test:"
echo "  sudo reboot"
echo
echo "After reboot, the desktop should load automatically and your photobooth"
echo "autostart entry should launch the app."
echo
echo "To disable auto-login later:"
case "$display_manager" in
  gdm)
    echo "  sudo sed -i '/^AutomaticLogin/d;/^AutomaticLoginEnable/d' /etc/gdm3/custom.conf"
    ;;
  lightdm)
    echo "  sudo rm /etc/lightdm/lightdm.conf.d/50-photobooth-autologin.conf"
    ;;
  sddm)
    echo "  sudo rm /etc/sddm.conf.d/zz-photobooth-autologin.conf"
    ;;
esac
