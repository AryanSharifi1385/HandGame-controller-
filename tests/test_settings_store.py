"""Regression tests for user settings validation."""
import unittest

from settings_store import DEFAULT_SETTINGS, normalize_settings


class SettingsNormalizationTests(unittest.TestCase):
    def test_empty_settings_use_defaults(self):
        self.assertEqual(normalize_settings({}), DEFAULT_SETTINGS)

    def test_mouse_values_are_clamped_and_integer_step_is_rounded(self):
        result = normalize_settings({
            "mouse_sensitivity": 99,
            "mouse_deadzone": -1,
            "mouse_max_step": 8.6,
        })
        self.assertEqual(result["mouse_sensitivity"], 4.0)
        self.assertEqual(result["mouse_deadzone"], 0.0005)
        self.assertEqual(result["mouse_max_step"], 9)

    def test_invalid_key_binding_falls_back_to_default(self):
        result = normalize_settings({"key_jump": "not-a-key"})
        self.assertEqual(result["key_jump"], DEFAULT_SETTINGS["key_jump"])

    def test_valid_key_binding_is_preserved(self):
        result = normalize_settings({"key_jump": "q"})
        self.assertEqual(result["key_jump"], "q")

    def test_new_supported_key_binding_is_preserved(self):
        result = normalize_settings({"key_jump": "up"})
        self.assertEqual(result["key_jump"], "up")

    def test_supported_theme_is_preserved_and_invalid_theme_defaults(self):
        self.assertEqual(normalize_settings({"ui_theme": "GTA VI"})["ui_theme"], "GTA VI")
        self.assertEqual(normalize_settings({"ui_theme": "not-a-theme"})["ui_theme"], "Cyberpunk")

    def test_old_settings_files_gain_new_key_defaults(self):
        result = normalize_settings({"mouse_sensitivity": 1.2})
        self.assertEqual(result["mouse_sensitivity"], 1.2)
        self.assertEqual(result["key_move_forward"], "w")
        self.assertEqual(result["key_reload"], "r")


    def test_function_key_assignment_is_preserved(self):
        normalized = normalize_settings({"key_jump": "f5"})
        self.assertEqual(normalized["key_jump"], "f5")

    def test_numpad_key_assignment_is_preserved(self):
        normalized = normalize_settings({"key_jump": "numpad7"})
        self.assertEqual(normalized["key_jump"], "numpad7")

    def test_punctuation_key_assignment_is_preserved(self):
        normalized = normalize_settings({"key_jump": "bracketleft"})
        self.assertEqual(normalized["key_jump"], "bracketleft")


if __name__ == "__main__":
    unittest.main()

