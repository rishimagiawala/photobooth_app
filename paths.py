from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent


def app_path(*parts):
    return APP_ROOT.joinpath(*parts)


def resolve_app_path(path):
    path = Path(path)
    if path.is_absolute():
        return path
    return APP_ROOT / path


def display_path(path):
    path = Path(path)
    try:
        return f"./{path.resolve().relative_to(APP_ROOT).as_posix()}"
    except ValueError:
        return path.as_posix()


def ensure_runtime_dirs():
    for directory in ("photos", "saved_photos", "printed_strips"):
        app_path(directory).mkdir(parents=True, exist_ok=True)
