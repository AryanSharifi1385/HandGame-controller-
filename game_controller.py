import ctypes
from ctypes import wintypes


user32 = ctypes.windll.user32


# ==========================================================
# WINDOWS INPUT CONSTANTS
# ==========================================================

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_SCANCODE = 0x0008

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010


# ==========================================================
# WINDOWS STRUCTURES
# ==========================================================

class KEYBDINPUT(ctypes.Structure):

    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]


class MOUSEINPUT(ctypes.Structure):

    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]


class HARDWAREINPUT(ctypes.Structure):

    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]


class INPUT_UNION(ctypes.Union):

    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT)
    ]


class INPUT(ctypes.Structure):

    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION)
    ]


# ==========================================================
# SCAN CODES
# ==========================================================

# These are physical keyboard scan codes.
#
# W = 0x11
# A = 0x1E
# S = 0x1F
# D = 0x20

SCAN_CODES = {
    # Standard US-layout physical keyboard scan codes (Set 1).
    **{chr(ord("a") + i): code for i, code in enumerate([
        0x1E, 0x30, 0x2E, 0x20, 0x12, 0x21, 0x22, 0x23, 0x17, 0x24,
        0x25, 0x26, 0x32, 0x31, 0x18, 0x19, 0x10, 0x13, 0x1F, 0x14,
        0x16, 0x2F, 0x11, 0x2D, 0x15, 0x2C])},
    **{str(i): code for i, code in enumerate([0x0B, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A])},
    "grave": 0x29, "minus": 0x0C, "equal": 0x0D,
    "bracketleft": 0x1A, "bracketright": 0x1B, "backslash": 0x2B,
    "semicolon": 0x27, "apostrophe": 0x28, "comma": 0x33,
    "period": 0x34, "slash": 0x35,
    "space": 0x39, "enter": 0x1C, "tab": 0x0F, "esc": 0x01,
    "backspace": 0x0E, "capslock": 0x3A,
    "lshift": 0x2A, "rshift": 0x36, "lctrl": 0x1D, "rctrl": 0x1D,
    "lalt": 0x38, "ralt": 0x38,
    "up": 0x48, "down": 0x50, "left": 0x4B, "right": 0x4D,
    "insert": 0x52, "delete": 0x53, "home": 0x47, "end": 0x4F,
    "pageup": 0x49, "pagedown": 0x51, "numlock": 0x45,
    "scrolllock": 0x46, "printscreen": 0x37, "pause": 0x45,
    "numpad0": 0x52, "numpad1": 0x4F, "numpad2": 0x50,
    "numpad3": 0x51, "numpad4": 0x4B, "numpad5": 0x4C,
    "numpad6": 0x4D, "numpad7": 0x47, "numpad8": 0x48,
    "numpad9": 0x49, "numpad_decimal": 0x53, "numpad_divide": 0x35,
    "numpad_multiply": 0x37, "numpad_subtract": 0x4A,
    "numpad_add": 0x4E, "numpad_enter": 0x1C,
    **{f"f{i}": code for i, code in enumerate(
        [0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43, 0x44, 0x57, 0x58], 1)},
}

EXTENDED_KEYS = {
    "rctrl", "ralt", "up", "down", "left", "right", "insert", "delete",
    "home", "end", "pageup", "pagedown", "numpad_divide", "numpad_enter",
    "printscreen",
}



class GameController:

    def __init__(self):

        self.held_keys = set()

        self.mouse_left_held = False

        self.mouse_right_held = False

        self.current_movement = "STOP"
        self.movement_key_map = {
            "LEFT": "a", "RIGHT": "d", "UP": "w", "DOWN": "s"
        }

    def set_movement_keys(self, mapping):
        """Configure the physical keys used for the four movement directions."""
        allowed = set(SCAN_CODES)
        normalized = {}
        for direction, setting_name in (
            ("LEFT", "key_move_left"),
            ("RIGHT", "key_move_right"),
            ("UP", "key_move_forward"),
            ("DOWN", "key_move_backward"),
        ):
            value = str(mapping.get(setting_name, self.movement_key_map[direction])).lower()
            normalized[direction] = value if value in allowed else self.movement_key_map[direction]
        # Release the old direction before replacing its mapping.
        self.set_movement("STOP")
        self.movement_key_map = normalized


    # ==========================================================
    # LOW-LEVEL KEY INPUT
    # ==========================================================

    def _send_key(self, key, key_up=False):

        key = key.lower()

        if key not in SCAN_CODES:
            return

        scan_code = SCAN_CODES[key]

        flags = KEYEVENTF_SCANCODE
        if key in EXTENDED_KEYS:
            flags |= KEYEVENTF_EXTENDEDKEY

        if key_up:
            flags |= KEYEVENTF_KEYUP

        extra = ctypes.c_ulong(0)

        keyboard = KEYBDINPUT(

            wVk=0,

            wScan=scan_code,

            dwFlags=flags,

            time=0,

            dwExtraInfo=ctypes.pointer(extra)
        )

        input_data = INPUT(

            type=INPUT_KEYBOARD,

            union=INPUT_UNION(

                ki=keyboard
            )
        )

        result = user32.SendInput(

            1,

            ctypes.byref(input_data),

            ctypes.sizeof(INPUT)
        )

        return result


    # ==========================================================
    # KEY DOWN
    # ==========================================================

    def key_down(self, key):

        key = key.lower()

        if key not in SCAN_CODES:
            return False

        if key in self.held_keys:
            return True

        result = self._send_key(
            key,
            key_up=False
        )

        if result == 1:
            self.held_keys.add(key)
            return True

        return False


    # ==========================================================
    # KEY UP
    # ==========================================================

    def key_up(self, key):

        key = key.lower()

        if key not in SCAN_CODES:
            return False

        if key not in self.held_keys:
            return True

        result = self._send_key(
            key,
            key_up=True
        )

        # Keep the key marked as held if Windows rejects the release. This
        # allows later tracking-loss/shutdown cleanup to retry it.
        if result == 1:
            self.held_keys.discard(key)
            return True

        return False


    # ==========================================================
    # PRESS
    # ==========================================================

    def press(self, key):

        if not self.key_down(key):
            return False

        return self.key_up(key)


    # ==========================================================
    # LEFT MOUSE DOWN
    # ==========================================================

    def mouse_left_down(self):

        if self.mouse_left_held:
            return True

        extra = ctypes.c_ulong(0)

        mouse = MOUSEINPUT(

            dx=0,

            dy=0,

            mouseData=0,

            dwFlags=MOUSEEVENTF_LEFTDOWN,

            time=0,

            dwExtraInfo=ctypes.pointer(extra)
        )

        input_data = INPUT(

            type=INPUT_MOUSE,

            union=INPUT_UNION(

                mi=mouse
            )
        )

        result = user32.SendInput(

            1,

            ctypes.byref(input_data),

            ctypes.sizeof(INPUT)
        )

        if result == 1:
            self.mouse_left_held = True
            return True

        return False


    # ==========================================================
    # LEFT MOUSE UP
    # ==========================================================

    def mouse_left_up(self):

        if not self.mouse_left_held:
            return True

        extra = ctypes.c_ulong(0)

        mouse = MOUSEINPUT(

            dx=0,

            dy=0,

            mouseData=0,

            dwFlags=MOUSEEVENTF_LEFTUP,

            time=0,

            dwExtraInfo=ctypes.pointer(extra)
        )

        input_data = INPUT(

            type=INPUT_MOUSE,

            union=INPUT_UNION(

                mi=mouse
            )
        )

        result = user32.SendInput(

            1,

            ctypes.byref(input_data),

            ctypes.sizeof(INPUT)
        )

        if result == 1:
            self.mouse_left_held = False
            return True

        return False


    # ==========================================================
    # RIGHT MOUSE DOWN
    # ==========================================================

    def mouse_right_down(self):

        if self.mouse_right_held:
            return True

        extra = ctypes.c_ulong(0)

        mouse = MOUSEINPUT(

            dx=0,

            dy=0,

            mouseData=0,

            dwFlags=MOUSEEVENTF_RIGHTDOWN,

            time=0,

            dwExtraInfo=ctypes.pointer(extra)
        )

        input_data = INPUT(

            type=INPUT_MOUSE,

            union=INPUT_UNION(

                mi=mouse
            )
        )

        result = user32.SendInput(

            1,

            ctypes.byref(input_data),

            ctypes.sizeof(INPUT)
        )

        if result == 1:
            self.mouse_right_held = True
            return True

        return False


    # ==========================================================
    # RIGHT MOUSE UP
    # ==========================================================

    def mouse_right_up(self):

        if not self.mouse_right_held:
            return True

        extra = ctypes.c_ulong(0)

        mouse = MOUSEINPUT(

            dx=0,

            dy=0,

            mouseData=0,

            dwFlags=MOUSEEVENTF_RIGHTUP,

            time=0,

            dwExtraInfo=ctypes.pointer(extra)
        )

        input_data = INPUT(

            type=INPUT_MOUSE,

            union=INPUT_UNION(

                mi=mouse
            )
        )

        result = user32.SendInput(

            1,

            ctypes.byref(input_data),

            ctypes.sizeof(INPUT)
        )

        if result == 1:
            self.mouse_right_held = False
            return True

        return False


    # ==========================================================
    # MOUSE MOVEMENT
    # ==========================================================

    def move_mouse(self, dx, dy):

        dx = int(dx)

        dy = int(dy)

        if dx == 0 and dy == 0:
            return

        extra = ctypes.c_ulong(0)

        mouse = MOUSEINPUT(

            dx=dx,

            dy=dy,

            mouseData=0,

            dwFlags=MOUSEEVENTF_MOVE,

            time=0,

            dwExtraInfo=ctypes.pointer(extra)
        )

        input_data = INPUT(

            type=INPUT_MOUSE,

            union=INPUT_UNION(

                mi=mouse
            )
        )

        result = user32.SendInput(

            1,

            ctypes.byref(input_data),

            ctypes.sizeof(INPUT)
        )

        return result == 1


    # ==========================================================
    # MOVEMENT
    # ==========================================================

    def set_movement(self, direction):

        direction = direction.upper()


        movement_keys = self.movement_key_map


        # Nothing changed.
        #
        # IMPORTANT:
        # We do NOT resend the key.
        #
        # If W is already held, W stays held.

        if direction == self.current_movement:
            # If an earlier key-up failed, retry releasing it instead of
            # assuming that the movement state is safe.
            if direction == "STOP":
                for movement_key in set(self.movement_key_map.values()):
                    if movement_key in self.held_keys:
                        self.key_up(movement_key)
            return


        # ------------------------------------------
        # RELEASE OLD MOVEMENT
        # ------------------------------------------

        if self.current_movement in movement_keys:
            old_key = movement_keys[self.current_movement]
            if not self.key_up(old_key):
                return


        # ------------------------------------------
        # PRESS NEW MOVEMENT
        # ------------------------------------------

        if direction in movement_keys:
            new_key = movement_keys[direction]
            if not self.key_down(new_key):
                self.current_movement = "STOP"
                return


        self.current_movement = direction


    # ==========================================================
    # EMERGENCY STOP
    # ==========================================================

    def emergency_stop(self):

        # Best-effort cleanup with retries. If Windows rejects one event,
        # keep the internal state marked as held and try again.
        for _attempt in range(3):

            for key in list(self.held_keys):
                self.key_up(key)

            if self.mouse_left_held:
                self.mouse_left_up()

            if self.mouse_right_held:
                self.mouse_right_up()

            if (
                not self.held_keys
                and not self.mouse_left_held
                and not self.mouse_right_held
            ):
                break

        self.current_movement = "STOP"