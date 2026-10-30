"""Local state and crash-safe JSON storage."""
import json
import os
import tempfile
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ.get("PPBC_STATE_DIR", CODE_DIR / ".local"))

def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def load_state(name, legacy, validate):
    path = STATE_DIR / name
    backup = path.with_suffix(path.suffix + ".bak")
    if not path.exists():
        legacy_path = CODE_DIR / legacy
        example_path = CODE_DIR / (legacy_path.stem + '.example.json')
        value = read_json(legacy_path if legacy_path.exists() else example_path)
        validate(value)
        atomic_json(path, value)
        return value
    try:
        value = read_json(path)
        validate(value)
        return value
    except (OSError, ValueError, TypeError, KeyError):
        value = read_json(backup)
        validate(value)
        return value

def save_state(name, value, validate):
    validate(value)
    path = STATE_DIR / name
    backup = path.with_suffix(path.suffix + ".bak")
    if path.exists():
        try:
            old = read_json(path)
            validate(old)
        except (OSError, ValueError, TypeError, KeyError):
            pass
        else:
            atomic_json(backup, old)
    atomic_json(path, value)

def object_value(value):
    if not isinstance(value, dict):
        raise ValueError("Expected an object")

def device_settings(value):
    object_value(value)
    required = ("animationSpeed", "textColor", "fontName", "textSpacing", "customText",
                "weatherZipLocation", "weatherCityLocation", "tempUnits", "content",
                "bgColor", "brightness", "timeFormat", "boardType", "lineCount")
    if any(key not in value for key in required):
        raise ValueError("Missing device setting")
    if value["boardType"] not in ("normal", "xl") or value["lineCount"] not in (1, 2):
        raise ValueError("Invalid board configuration")
    if value["boardType"] == "normal" and value["lineCount"] != 1:
        raise ValueError("Normal board supports one line")
    if not isinstance(value["brightness"], int) or not 0 <= value["brightness"] <= 255:
        raise ValueError("Invalid brightness")
    if value["fontName"] not in ("slanted", "digits") or value["timeFormat"] not in ("12h", "24h") or value["tempUnits"] not in ("f", "c", "k"):
        raise ValueError("Invalid display setting")
    import math
    speeds = value["animationSpeed"]
    if not isinstance(speeds, list) or len(speeds) != 2 or any(not isinstance(n, (int, float)) or isinstance(n, bool) or not math.isfinite(n) for n in speeds):
        raise ValueError("Invalid animation speed")
    for key in ("customText", "weatherZipLocation", "weatherCityLocation"):
        if not isinstance(value[key], str):
            raise ValueError("Invalid text setting")
    if not isinstance(value["textSpacing"], int) or not 0 <= value["textSpacing"] <= 10:
        raise ValueError("Invalid text spacing")
    if not isinstance(value["content"], list) or any(item not in (f"{kind} {line}" for kind in ("time", "date", "text", "weather") for line in (0, 1)) for item in value["content"]) or len(value["content"]) > 8 or len(set(value["content"])) != len(value["content"]):
        raise ValueError("Invalid content")
    for key, animations in (("textColor", ("rainbow", "rainbowCycle", "breathing")), ("bgColor", ("rainbow", "rainbowCycle", "breathing", "twinkle"))):
        color = value[key]
        if not isinstance(color, list) or len(color) != 2 or not ((color[0] == "solid" and isinstance(color[1], int) and 0 <= color[1] <= 0xffffff) or (color[0] == "animation" and color[1] in animations)):
            raise ValueError("Invalid color")

def api_keys(value):
    object_value(value)
    if not isinstance(value.get("openweather"), str):
        raise ValueError("Invalid weather key")

def page_settings(value):
    object_value(value)
    if not isinstance(value.get("title"), str):
        raise ValueError("Invalid title")
    if not isinstance(value.get("mainBGColor"), str):
        raise ValueError("Invalid page color")
