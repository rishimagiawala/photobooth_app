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
