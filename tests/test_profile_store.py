"""Tests for persistent named control profiles."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import profile_store
from settings_store import DEFAULT_SETTINGS


class ProfileStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "profiles.json"
        self.patch_path = patch.object(profile_store, "profiles_path", return_value=self.path)
        self.patch_path.start()

    def tearDown(self):
        self.patch_path.stop()
        self.temp_dir.cleanup()

    def test_default_profile_always_exists(self):
        self.assertEqual(profile_store.load_profiles()["Default"], DEFAULT_SETTINGS)

    def test_save_and_reload_custom_profile(self):
        settings = dict(DEFAULT_SETTINGS, mouse_sensitivity=2.4, key_jump="f")
        name, saved = profile_store.save_profile("  My FPS Setup  ", settings)
        self.assertEqual(name, "My FPS Setup")
        self.assertEqual(saved["mouse_sensitivity"], 2.4)
        loaded = profile_store.load_profiles()
        self.assertEqual(loaded[name]["key_jump"], "f")

    def test_default_profile_cannot_be_overwritten_or_deleted(self):
        with self.assertRaises(ValueError):
            profile_store.save_profile("default", DEFAULT_SETTINGS)
        with self.assertRaises(ValueError):
            profile_store.delete_profile("Default")

    def test_delete_custom_profile(self):
        profile_store.save_profile("Test Profile", DEFAULT_SETTINGS)
        self.assertTrue(profile_store.delete_profile("Test Profile"))
        self.assertNotIn("Test Profile", profile_store.load_profiles())

    def test_invalid_saved_entries_are_ignored(self):
        self.path.write_text(json.dumps({"": {}, "Default": {"key_jump": "q"}, "Broken": "nope"}), encoding="utf-8")
        profiles = profile_store.load_profiles()
        self.assertEqual(profiles["Default"], DEFAULT_SETTINGS)
        self.assertNotIn("Broken", profiles)
        self.assertEqual(len(profiles), 1)


if __name__ == "__main__":
    unittest.main()
