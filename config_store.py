import json
from json import JSONDecodeError

from paths import app_path


DEFAULT_COUNT_CONFIG = {
    "count": 0,
    "startup_viewer": False,
    "mobile_view": False,
    "save_photos": False,
}

DEFAULT_LAYOUT_CONFIG = {
    "image_height": 365,
    "logo_height": 350,
    "marginy": 10,
    "marginx": 0,
    "logo_path": "./assets/images/logos/test_logo_dont_delete.png",
    "logo2_path": "./assets/images/logos/test_logo_dont_delete.png",
    "logo_rotate": True,
    "image_marginy": 0,
    "image_marginx": 0,
    "num_of_photos": 4,
    "logo_position": 4,
    "logo_square": True,
    "background_path": "./assets/images/background/white.png",
    "include_background": True,
    "background_color": "#ffffff",
    "angle": 0,
}

DEFAULT_READER_CONFIG = {
    "serial_port": "/dev/ttyUSB0",
    "credits_trigger": 7,
}


COUNT_CONFIG_PATH = app_path("config", "printing", "count.json")
LAYOUT_CONFIG_PATH = app_path("config", "printing", "layout.json")
READER_CONFIG_PATH = app_path("config", "card_reader", "reader.json")


def load_count_config():
    return load_json_config(COUNT_CONFIG_PATH, DEFAULT_COUNT_CONFIG)


def load_layout_config():
    return load_json_config(LAYOUT_CONFIG_PATH, DEFAULT_LAYOUT_CONFIG)


def load_reader_config():
    return load_json_config(READER_CONFIG_PATH, DEFAULT_READER_CONFIG)


def save_json_config(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as config_file:
        json.dump(data, config_file)


def load_json_config(path, defaults):
    try:
        with open(path, "r") as config_file:
            data = json.load(config_file)
    except (FileNotFoundError, JSONDecodeError):
        data = {}

    if not isinstance(data, dict):
        data = {}

    config = defaults.copy()
    config.update(data)
    if data != config:
        save_json_config(path, config)
    return config
