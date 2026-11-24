"""Small, dependency-free settings and runtime-status store."""
import json
import os
import tempfile
import time

from app_paths import data_dir


DEFAULT_SETTINGS = {
    "mouse_sensitivity": 1.70,
    "mouse_deadzone": 0.0025,
    "mouse_max_step": 14,
    "ui_theme": "Cyberpunk",
    "key_move_left": "a",
    "key_move_right": "d",
    "key_move_forward": "w",
    "key_move_backward": "s",
    "key_jump": "space",
    "key_interact": "e",
    "key_fist_action": "f",
    "key_sprint": "lshift",
    "key_reload": "r",
    "key_crouch": "c",
    "key_ability": "q",
    "key_ctrl": "lctrl",
    "key_alt": "lalt",
}

MIN_SETTINGS = {
    "mouse_sensitivity": 0.25,
    "mouse_deadzone": 0.0005,
    "mouse_max_step": 3,
}

MAX_SETTINGS = {
    "mouse_sensitivity": 4.0,
    "mouse_deadzone": 0.02,
    "mouse_max_step": 30,
}

# Canonical key names accepted by the capture widget and Windows input layer.
ALLOWED_KEYS = {
    *[chr(code) for code in range(ord("a"), ord("z") + 1)],
    *[str(i) for i in range(10)],
    "grave", "minus", "equal", "bracketleft", "bracketright", "backslash",
    "semicolon", "apostrophe", "comma", "period", "slash",
    "space", "enter", "tab", "esc", "backspace", "capslock",
    "lshift", "rshift", "lctrl", "rctrl", "lalt", "ralt",
    "up", "down", "left", "right", "insert", "delete", "home", "end",
    "pageup", "pagedown", "numlock", "scrolllock", "printscreen", "pause",
    *[f"f{i}" for i in range(1, 13)],
    *[f"numpad{i}" for i in range(10)],
    "numpad_decimal", "numpad_divide", "numpad_multiply", "numpad_subtract",
    "numpad_add", "numpad_enter",
}
ALLOWED_THEMES = {"Cyberpunk", "Ghost of Tsushima", "The Last of Us", "God of War", "GTA VI", "Matrix", "Synthwave", "Arctic"}
KEY_SETTING_NAMES = tuple(key for key in DEFAULT_SETTINGS if key.startswith("key_"))


def settings_path():
    return data_dir() / "user_settings.json"


def status_path():
    return data_dir() / "runtime_status.json"


def stop_flag_path():
    return data_dir() / "stop_controller.flag"


def _atomic_json_write(path, payload):
    path = str(path)
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(
        prefix=".tmp_controller_",
        suffix=".json",
        dir=directory
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    finally:
        try:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
        except OSError:
            pass


def normalize_settings(values):
    normalized = {}
    values = values if isinstance(values, dict) else {}
    for key, default in DEFAULT_SETTINGS.items():
        if key.startswith("key_") or key == "ui_theme":
            continue
        try:
            value = float(values.get(key, default))
        except (TypeError, ValueError):
            value = float(default)
        value = max(MIN_SETTINGS[key], min(MAX_SETTINGS[key], value))
        if key == "mouse_max_step":
            value = int(round(value))
        normalized[key] = value

    theme = str(values.get("ui_theme", DEFAULT_SETTINGS["ui_theme"])).strip()
    normalized["ui_theme"] = theme if theme in ALLOWED_THEMES else DEFAULT_SETTINGS["ui_theme"]

    for key in KEY_SETTING_NAMES:
        candidate = str(values.get(key, DEFAULT_SETTINGS[key])).strip().lower()
        normalized[key] = candidate if candidate in ALLOWED_KEYS else DEFAULT_SETTINGS[key]

    return normalized


def load_settings():
    path = settings_path()
    try:
        with open(path, "r", encoding="utf-8") as file:
            loaded = json.load(file)
    except (OSError, ValueError, TypeError):
        loaded = DEFAULT_SETTINGS.copy()
    normalized = normalize_settings(loaded)
    if not path.exists():
        try:
            save_settings(normalized)
        except OSError:
            pass
    return normalized


def save_settings(values):
    normalized = normalize_settings(values)
    _atomic_json_write(settings_path(), normalized)
    return normalized


def write_status(payload):
    data = dict(payload)
    data["updated_at"] = time.time()
    try:
        _atomic_json_write(status_path(), data)
    except OSError:
        # Status display is auxiliary and must never crash the controller.
        pass


def read_status():
    try:
        with open(status_path(), "r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, dict):
            return {}
        return payload
    except (OSError, ValueError, TypeError):
        return {}


def request_stop():
    try:
        stop_flag_path().write_text("stop", encoding="utf-8")
    except OSError:
        pass


def stop_requested():
    return stop_flag_path().exists()


def clear_stop_request():
    try:
        stop_flag_path().unlink(missing_ok=True)
    except OSError:
        pass
