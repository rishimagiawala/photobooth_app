# photobooth_app

Main photobooth application.

## Linux Setup

Create a Python environment and install the Linux dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-linux.txt
```

Install system packages for camera, serial, and printing support:

```bash
sudo apt install python3-venv cups cups-client printer-driver-gutenprint v4l-utils
```

Add the booth user to the device groups, then log out and back in:

```bash
sudo usermod -aG video,dialout "$USER"
```

Configure the DNP RX1 in CUPS after installing the Gutenprint driver. The app renders every strip to `printed_strips/` and submits it with `lp`. By default it prints to `Dai_Nippon_Printing_DS-RX1`. To override the queue or pass printer options:

```bash
export PHOTOBOOTH_PRINTER="DNP_RX1"
export PHOTOBOOTH_LP_OPTIONS="-o media=Custom.4x6in -o fit-to-page"
python app.py
```

Set the card reader path in `config/card_reader/reader.json` or in the Reader settings window. On Linux this should be a full device path such as `/dev/ttyUSB0`, `/dev/ttyACM0`, or a stable `/dev/serial/by-id/...` path.

The old `req.txt` file is a Windows conda export and should not be used for Linux installs.

## Running the app

```bash
bash start-photobooth.sh   # launches the app; logs to photobooth.log
```

- Exit the fullscreen viewer with **Esc** (or **Ctrl+Q**), or tap the top-left corner of the screen.
- All output and errors go to `photobooth.log` in this folder: `tail -n 40 photobooth.log`.

## Maintenance & troubleshooting

**Changing the logo:** Open the dashboard and click **Change Logo** — pick an image from anywhere (it's copied in automatically) or tap a previously used one. No file copying or restart needed.

**Moving to a different printer (same DS-RX1 model):** Each printer's USB device URI is tied to its serial number, so a new unit won't match the existing queue until it's re-linked. Plug in the printer and run:

```bash
bash fix-printer.sh
```

This re-points the `Dai_Nippon_Printing_DS-RX1` queue at the connected unit (keeping the same name/driver). It also runs automatically on every startup (via `start-photobooth.sh`) and only acts when the printer actually changed. If it can't link, the app falls back to the CUPS **default** printer — so setting your printer as default at `http://localhost:631` (Administration → Set As Server Default) is the simplest fix if prints don't come out.

**Passwordless sudo (needed for the auto printer-link on boot):** Without it, the startup printer step is skipped (the app still runs). To enable it for the booth user:

```bash
echo "$(whoami) ALL=(ALL) NOPASSWD: ALL" | sudo EDITOR='tee' visudo -f /etc/sudoers.d/nopasswd
sudo chmod 0440 /etc/sudoers.d/nopasswd
sudo -n whoami   # should print "root"
```

**Rendered strips** are auto-pruned to the 5 most recent in `printed_strips/` (for reprints); older ones are deleted automatically. Captured photos in `photos/` are deleted after each print.
