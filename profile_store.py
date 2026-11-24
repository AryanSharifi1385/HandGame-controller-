"""Persistent user control profiles for Hand Game Controller."""
import json
import os
import tempfile

from app_paths import data_dir
from settings_store import DEFAULT_SETTINGS, normalize_settings

DEFAULT_PROFILE_NAME = "Default"
MAX_PROFILE_NAME_LENGTH = 32


def profiles_path():
    return data_dir() / "profiles.json"


def _read_custom_profiles():
    path = profiles_path()
    try:
        with open(path, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(payload, dict):
        return {}

    result = {}
    for raw_name, raw_settings in payload.items():
        name = str(raw_name).strip()
        if not name or len(name) > MAX_PROFILE_NAME_LENGTH:
            continue
        if name.casefold() == DEFAULT_PROFILE_NAME.casefold():
            continue
        if not isinstance(raw_settings, dict):
            continue
        result[name] = normalize_settings(raw_settings)
    return result


def load_profiles():
    """Return built-in Default plus validated user-created profiles."""
    profiles = {DEFAULT_PROFILE_NAME: dict(DEFAULT_SETTINGS)}
    profiles.update(_read_custom_profiles())
    return profiles


def _write_custom_profiles(profiles):
    path = profiles_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(
        prefix=".tmp_profiles_", suffix=".json", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(profiles, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    finally:
        try:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
        except OSError:
            pass


def validate_profile_name(name):
    name = " ".join(str(name or "").split())
    if not name:
        raise ValueError("Enter a profile name.")
    if len(name) > MAX_PROFILE_NAME_LENGTH:
        raise ValueError(f"Profile names must be {MAX_PROFILE_NAME_LENGTH} characters or fewer.")
    if any(ord(character) < 32 for character in name):
        raise ValueError("Profile names cannot contain control characters.")
    if name.casefold() == DEFAULT_PROFILE_NAME.casefold():
        raise ValueError("The built-in Default profile cannot be overwritten. Choose another name.")
    return name


def save_profile(name, settings):
    """Create or replace a named user profile; returns its normalized name/settings."""
    name = validate_profile_name(name)
    profiles = _read_custom_profiles()
    # Replace an existing case-insensitive name instead of creating duplicates.
    existing = next((item for item in profiles if item.casefold() == name.casefold()), None)
    if existing is not None and existing != name:
        del profiles[existing]
    normalized = normalize_settings(settings)
    profiles[name] = normalized
    _write_custom_profiles(profiles)
    return name, normalized


def delete_profile(name):
    """Delete a user profile. The built-in Default profile is protected."""
    name = str(name or "").strip()
    if not name or name.casefold() == DEFAULT_PROFILE_NAME.casefold():
        raise ValueError("The built-in Default profile cannot be deleted.")
    profiles = _read_custom_profiles()
    existing = next((item for item in profiles if item.casefold() == name.casefold()), None)
    if existing is None:
        return False
    del profiles[existing]
    _write_custom_profiles(profiles)
    return True
