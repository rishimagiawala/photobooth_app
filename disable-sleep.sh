#!/usr/bin/env bash
# Keep the booth awake: disable sleep, suspend, hibernate, and screen blanking.
#
# Run once from the photobooth folder:
#   bash disable-sleep.sh
#
# Safe to re-run. Needs sudo for the systemd sleep masks.
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
  echo "error: run this as your normal booth user, not root/sudo" >&2
  echo "The script will ask for sudo when it needs system changes." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"
KEEP_AWAKE_SCRIPT="$ROOT/keep-awake.sh"
KEEP_AWAKE_DESKTOP="$AUTOSTART_DIR/photobooth-keep-awake.desktop"

info() {
  echo "==> $*"
}

set_gsetting() {
  local schema="$1"
  local key="$2"
  local value="$3"

  if ! command -v gsettings >/dev/null 2>&1; then
    return 0
  fi
  if ! gsettings list-schemas 2>/dev/null | grep -qx "$schema"; then
    return 0
  fi
  if ! gsettings list-keys "$schema" 2>/dev/null | grep -qx "$key"; then
    return 0
  fi

  if gsettings set "$schema" "$key" "$value" >/dev/null 2>&1; then
    info "gsettings: $schema $key = $value"
  fi
}

disable_desktop_power_settings() {
  info "disabling desktop sleep / screen blank settings"

  # Cinnamon (Linux Mint default)
  set_gsetting org.cinnamon.settings-daemon.plugins.power sleep-display-ac 0
  set_gsetting org.cinnamon.settings-daemon.plugins.power sleep-display-battery 0
  set_gsetting org.cinnamon.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
  set_gsetting org.cinnamon.settings-daemon.plugins.power sleep-inactive-battery-timeout 0
  set_gsetting org.cinnamon.settings-daemon.plugins.power idle-dim-battery false
  set_gsetting org.cinnamon.settings-daemon.plugins.power idle-dim-time 0
  set_gsetting org.cinnamon.desktop.session idle-delay 0
  set_gsetting org.cinnamon.desktop.screensaver lock-enabled false
  set_gsetting org.cinnamon.desktop.screensaver idle-activation-enabled false

  # GNOME
  set_gsetting org.gnome.desktop.session idle-delay 0
  set_gsetting org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type "'nothing'"
  set_gsetting org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type "'nothing'"
  set_gsetting org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
  set_gsetting org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 0
  set_gsetting org.gnome.desktop.screensaver lock-enabled false
  set_gsetting org.gnome.desktop.screensaver idle-activation-enabled false

  # MATE
  set_gsetting org.mate.session idle-delay 0
  set_gsetting org.mate.power-manager sleep-display-ac 0
  set_gsetting org.mate.power-manager sleep-computer-ac 0
  set_gsetting org.mate.screensaver idle-activation-enabled false
  set_gsetting org.mate.screensaver lock-enabled false
}

mask_systemd_sleep() {
  info "masking systemd sleep / suspend / hibernate targets"
  sudo systemctl mask \
    sleep.target \
    suspend.target \
    hibernate.target \
    hybrid-sleep.target \
    suspend-then-hibernate.target >/dev/null
}

install_keep_awake_autostart() {
  info "installing login keep-awake helper (xset DPMS off)"

  cat > "$KEEP_AWAKE_SCRIPT" <<'EOF'
#!/usr/bin/env bash
# Re-assert no screen blank / DPMS after each graphical login.
set -euo pipefail

if grep -q $'\r' "${BASH_SOURCE[0]}" 2>/dev/null; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}"
  exec bash "${BASH_SOURCE[0]}" "$@"
fi

# Wait briefly for the session/DISPLAY to be ready.
sleep 3

if command -v xset >/dev/null 2>&1; then
  xset s off || true
  xset s noblank || true
  xset -dpms || true
fi

# Cinnamon sometimes re-applies power settings after login; poke them again.
if command -v gsettings >/dev/null 2>&1; then
  gsettings set org.cinnamon.settings-daemon.plugins.power sleep-display-ac 0 2>/dev/null || true
  gsettings set org.cinnamon.settings-daemon.plugins.power sleep-inactive-ac-timeout 0 2>/dev/null || true
  gsettings set org.cinnamon.desktop.session idle-delay 0 2>/dev/null || true
  gsettings set org.gnome.desktop.session idle-delay 0 2>/dev/null || true
fi
EOF

  chmod +x "$KEEP_AWAKE_SCRIPT"
  mkdir -p "$AUTOSTART_DIR"

  cat > "$KEEP_AWAKE_DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=Photobooth Keep Awake
Comment=Disable screen blanking and DPMS for the photobooth
Exec=$KEEP_AWAKE_SCRIPT
Path=$ROOT
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=2
Hidden=false
EOF
}

echo
info "configuring kiosk power settings"
echo

disable_desktop_power_settings
mask_systemd_sleep
install_keep_awake_autostart

# Apply DPMS off immediately if an X display is available right now.
if [[ -n "${DISPLAY:-}" ]] && command -v xset >/dev/null 2>&1; then
  info "applying xset keep-awake for current session"
  xset s off || true
  xset s noblank || true
  xset -dpms || true
fi

echo
echo "Sleep / suspend / screen blanking disabled."
echo
echo "  Systemd sleep targets: masked"
echo "  Desktop power settings: updated when schemas exist"
echo "  Login helper: $KEEP_AWAKE_DESKTOP"
echo
echo "Reboot (or log out/in) so autologin + keep-awake both apply."
echo
echo "To reverse later:"
echo "  sudo systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target suspend-then-hibernate.target"
echo "  rm \"$KEEP_AWAKE_DESKTOP\""
echo
