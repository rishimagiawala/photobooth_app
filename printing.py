import os
import shlex
import subprocess
from contextlib import suppress
from datetime import datetime

from PIL import Image, ImageColor, ImageOps

from config_store import load_layout_config
from paths import app_path, ensure_runtime_dirs, resolve_app_path


right_off = 6
STRIP_HEIGHT = 1200
DEFAULT_PRINTER = "Dai_Nippon_Printing_DS-RX1"
# Don't let a stuck CUPS/printer block the print thread forever.
LP_TIMEOUT_SECONDS = 120
# Keep only the most recent rendered strips so storage doesn't fill up, while
# still leaving a few around in case a strip needs to be reprinted.
MAX_KEPT_STRIPS = 5


def printImages(image_arr, test=False):
    print("Print Job Received")
    strip_path = render_strip(image_arr, test)
    _submit_to_cups(strip_path)
    _prune_old_strips()
    return strip_path


def _prune_old_strips(keep=MAX_KEPT_STRIPS):
    """Keep only the most recent rendered strips; delete the older ones."""
    strips_dir = app_path("printed_strips")
    if not strips_dir.exists():
        return

    strips = sorted(
        (path for path in strips_dir.glob("*.png") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for old_strip in strips[keep:]:
        with suppress(OSError):
            old_strip.unlink()


def render_strip(image_arr, test=False):
    ensure_runtime_dirs()
    layout_data = load_layout_config()

    background_color = layout_data["background_color"]
    transparent_tuple = ImageColor.getcolor(background_color, "RGB") + (0,)
    logo_pos = layout_data["logo_position"]

    image_paths = [_photo_path(element, test) for element in image_arr]
    image_paths.insert(logo_pos, resolve_app_path(layout_data["logo_path"]))

    with Image.open(resolve_app_path(layout_data["logo2_path"])) as logo2_raw:
        logo2 = logo2_raw.convert("RGBA")
    logo2 = logo2.rotate(90, expand=True)
    logo2 = makeTransparent(logo2, transparent_tuple)

    image_height = layout_data["image_height"]
    logo_height = layout_data["logo_height"]
    marginy = layout_data["marginy"]
    logo_square = layout_data["logo_square"]
    logo_rotate = layout_data["logo_rotate"]
    total_width = sum(logo_height if i == logo_pos else image_height for i in range(len(image_paths))) + marginy + 40
    canvas = Image.new("RGBA", (total_width, STRIP_HEIGHT), background_color)

    marginx = 10
    image_offset = 0
    # Track the customer photos so they're only deleted after the strip is
    # saved successfully (a render crash must not lose the originals).
    photo_sources = []
    for i, image_path in enumerate(image_paths):
        with Image.open(image_path) as opened:
            bmp = opened.convert("RGBA")
        if bmp.size[0] > bmp.size[1] or (i == logo_pos and logo_rotate is True):
            bmp = bmp.rotate(90, expand=True)
        if logo_pos == i:
            bmp = makeTransparent(bmp, transparent_tuple)

        init = 20 if i == 0 else 0
        if logo_pos != i:
            boxes = [
                (image_offset + marginy + init, marginx * 3 + right_off, image_offset + image_height, int(STRIP_HEIGHT / 2) - (marginx * 2)),
                (image_offset + marginy + init, int(STRIP_HEIGHT / 2) + marginx, image_offset + image_height, STRIP_HEIGHT - (marginx * 4)),
            ]
            _paste_fit(canvas, bmp, boxes[0])
            _paste_fit(canvas, bmp, boxes[1])
            image_offset += image_height
            photo_sources.append(image_path)
        else:
            if logo_square is False:
                boxes = [
                    (image_offset + marginy + init, marginx * 3 + right_off, image_offset + logo_height, int(STRIP_HEIGHT / 2) - (marginx * 2)),
                    (image_offset + marginy + init, int(STRIP_HEIGHT / 2) + marginx, image_offset + logo_height, STRIP_HEIGHT - (marginx * 4)),
                ]
            else:
                square_margin = 54
                boxes = [
                    (image_offset + marginy + init, int(square_margin * 2.7) + right_off, image_offset + logo_height, int(STRIP_HEIGHT / 2 - (square_margin * 2.3))),
                    (image_offset + marginy + init, int(STRIP_HEIGHT / 2) + (square_margin + 70), image_offset + logo_height, int(STRIP_HEIGHT - (square_margin * 4 - 70))),
                ]
            _paste_fit(canvas, bmp, boxes[0])
            _paste_fit(canvas, logo2, boxes[1])
            image_offset += logo_height

    output_path = app_path("printed_strips", f"photo_strip_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
    canvas.convert("RGB").save(output_path)
    print(f"Rendered print strip: {output_path}")

    if test is False:
        for source in photo_sources:
            with suppress(OSError):
                os.remove(source)

    return output_path


def makeTransparent(img, transparent_tuple):
    rgba = img.convert("RGBA")
    datas = rgba.getdata()

    newData = []
    for item in datas:
        if item[3] == 0:
            newData.append(transparent_tuple)
        else:
            newData.append(item)

    rgba.putdata(newData)
    return rgba


def changeBackgroundColor(img, transparent_tuple):
    rgba = img.convert("RGBA")
    datas = rgba.getdata()

    newData = []
    for item in datas:
        newData.append(transparent_tuple)

    rgba.putdata(newData)
    return rgba


def _photo_path(filename, test):
    directory = "test_photos" if test else "photos"
    return app_path(directory, filename)


def _paste_fit(canvas, image, box):
    left, top, right, bottom = box
    width = max(1, right - left)
    height = max(1, bottom - top)
    fitted = ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS)
    canvas.alpha_composite(fitted, (left, top))


def _submit_to_cups(strip_path):
    command = ["lp"]
    printer_name = os.environ.get("PHOTOBOOTH_PRINTER", DEFAULT_PRINTER)
    if printer_name:
        command.extend(["-d", printer_name])

    lp_options = os.environ.get("PHOTOBOOTH_LP_OPTIONS")
    if lp_options:
        command.extend(shlex.split(lp_options))

    command.append(str(strip_path))
    try:
        subprocess.run(command, check=True, timeout=LP_TIMEOUT_SECONDS)
        print("Print job submitted to CUPS")
    except FileNotFoundError:
        print("Could not submit print job: 'lp' command is not installed")
    except subprocess.TimeoutExpired:
        print(f"Could not submit print job: lp timed out after {LP_TIMEOUT_SECONDS}s")
    except subprocess.CalledProcessError as error:
        print(f"Could not submit print job: lp exited with status {error.returncode}")
