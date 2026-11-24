import cv2
import time
import math
import logging
from types import SimpleNamespace

from camera import Camera
from hand_tracker import HandTracker
from movement_tracker import MovementTracker
from gesture_detector import GestureDetector
from game_controller import GameController
from settings_store import (
    load_settings,
    write_status,
    stop_requested
)
from app_paths import data_dir

from config import (
    EXIT_KEY,
    FINGER_STABILITY_FRAMES,
    ATTACK_STABILITY_FRAMES
)


# ============================================================
# INITIALIZATION
# ============================================================

try:
    data_dir().mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(data_dir() / "controller.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
except OSError:
    logging.basicConfig(level=logging.INFO)

# Camera and MediaPipe resources are created inside the guarded main try block
# so a failure during startup still reaches safe cleanup.
camera = None
tracker = None
movement = MovementTracker()
gestures = GestureDetector()
controller = GameController()


# ============================================================
# CALIBRATION STATE
# ============================================================

calibrated = False

calibration_start = None

# True when we are allowed to perform a new calibration.
calibration_armed = True

# Becomes True after BOTH hands have completely disappeared
# from the camera.
#
# This is the important part:
#
# HAND MOVEMENT != recalibration
#
# BOTH HANDS OUT OF CAMERA = re-arm calibration
#
both_hands_were_gone = False


# ============================================================
# LEFT-HAND STATE
# ============================================================

space_held = False
interact_held = False
fist_active = False
crouch_held = False
ctrl_held = False
alt_held = False
q_was_detected = False


# ============================================================
# RIGHT-HAND STATE
# ============================================================

aim_held = False
shift_held = False
thumb_mouse_active = False

# Relative mouse tracking state. The cursor moves only when the hand moves;
# holding the hand still therefore stops the cursor instead of continuously
# drifting based on a fixed joystick position.
previous_mouse_hand_center = None
# Mouse values are reloaded from user_settings.json while the controller runs.
# Keyboard bindings are read once at startup so changing a held key cannot strand it.
runtime_settings = load_settings()
MOUSE_HAND_SENSITIVITY = runtime_settings["mouse_sensitivity"]
MOUSE_HAND_DEADZONE = runtime_settings["mouse_deadzone"]
MOUSE_HAND_MAX_STEP = runtime_settings["mouse_max_step"]
last_settings_check = 0.0
last_status_write = 0.0
fps_window_start = time.monotonic()
fps_frame_count = 0
current_fps = 0.0

aim_counter = 0
shift_counter = 0
# True while the right hand is in thumbs-up mouse mode. This lets us
# immediately release a pointing-aim hold when mouse mode ends.
pointing_aim_mode_was_active = False

KEY_BINDINGS = {
    "move_left": runtime_settings["key_move_left"],
    "move_right": runtime_settings["key_move_right"],
    "move_forward": runtime_settings["key_move_forward"],
    "move_backward": runtime_settings["key_move_backward"],
    "jump": runtime_settings["key_jump"],
    "interact": runtime_settings["key_interact"],
    "fist_action": runtime_settings["key_fist_action"],
    "sprint": runtime_settings["key_sprint"],
    "reload": runtime_settings["key_reload"],
    "crouch": runtime_settings["key_crouch"],
    "ability": runtime_settings["key_ability"],
    "ctrl": runtime_settings["key_ctrl"],
    "alt": runtime_settings["key_alt"],
}
controller.set_movement_keys({
    "key_move_left": KEY_BINDINGS["move_left"],
    "key_move_right": KEY_BINDINGS["move_right"],
    "key_move_forward": KEY_BINDINGS["move_forward"],
    "key_move_backward": KEY_BINDINGS["move_backward"],
})


# ============================================================
# ATTACK STATE
# ============================================================

attack_held = False
attack_stability = 0
r_active = False
r_counter = 0
r_display_until = 0.0
q_display_until = 0.0


# ============================================================
# LEFT INDEX + THUMB PINCH
# ============================================================

def left_index_pinch(landmarks):

    if landmarks is None:
        return False

    thumb = landmarks[4]
    index = landmarks[8]

    distance = math.sqrt(
        (thumb.x - index.x) ** 2
        +
        (thumb.y - index.y) ** 2
    )

    return distance < 0.055


# ============================================================
# RIGHT-HAND THUMB-TO-FINGER PINCHES
# ============================================================

def right_finger_pinch(landmarks, fingertip_index, threshold=0.055):

    if landmarks is None:
        return False

    thumb = landmarks[4]
    fingertip = landmarks[fingertip_index]

    distance = math.sqrt(
        (thumb.x - fingertip.x) ** 2
        +
        (thumb.y - fingertip.y) ** 2
    )

    return distance < threshold


def left_finger_pinch(landmarks, fingertip_index, threshold=0.055):
    """Detect a left-hand thumb-to-fingertip pinch."""
    if landmarks is None:
        return False
    thumb = landmarks[4]
    fingertip = landmarks[fingertip_index]
    return math.hypot(thumb.x - fingertip.x, thumb.y - fingertip.y) < threshold


def is_left_shaka(landmarks):
    """Thumb and pinky extended; index, middle, and ring fingers curled."""
    if landmarks is None:
        return False
    return (
        gestures.thumb_is_extended(landmarks)
        and gestures.pinky_extended(landmarks)
        and gestures.index_curled(landmarks)
        and gestures.middle_curled(landmarks)
        and gestures.ring_curled(landmarks)
    )


def is_left_q_pose(landmarks):
    """Pinky extended, remaining fingers curled, and thumb not extended."""
    if landmarks is None:
        return False
    return (
        not gestures.thumb_is_extended(landmarks)
        and gestures.pinky_extended(landmarks)
        and gestures.index_curled(landmarks)
        and gestures.middle_curled(landmarks)
        and gestures.ring_curled(landmarks)
    )


# ============================================================
# WHOLE-HAND MOUSE REFERENCE
# ============================================================

def hand_center_position(landmarks):
    """Return the normalized center of the hand using the wrist and knuckles."""

    if landmarks is None:
        return None

    center_indices = (0, 5, 9, 13, 17)

    center_x = sum(
        landmarks[index].x for index in center_indices
    ) / len(center_indices)

    center_y = sum(
        landmarks[index].y for index in center_indices
    ) / len(center_indices)

    return center_x, center_y


def hand_center_mouse_reference(landmarks):
    """Keep the existing calibration helper compatible with MovementTracker."""

    if landmarks is None:
        return None

    center = hand_center_position(landmarks)
    reference_landmarks = list(landmarks)
    reference_landmarks[4] = SimpleNamespace(
        x=center[0],
        y=center[1],
        z=0.0
    )

    return reference_landmarks


# ============================================================
# RIGHT THUMBS-UP GESTURE
# ============================================================

def is_thumbs_up(landmarks):

    if landmarks is None:
        return False

    wrist = landmarks[0]
    thumb_ip = landmarks[3]
    thumb_tip = landmarks[4]

    # The thumb must point upward in the camera image.
    thumb_is_up = (
        thumb_tip.y < thumb_ip.y - 0.025
        and
        thumb_tip.y < wrist.y - 0.035
    )

    # The four non-thumb fingers must be curled toward the palm.
    finger_pairs = (
        (8, 6),
        (12, 10),
        (16, 14),
        (20, 18)
    )

    curled_fingers = 0

    for tip_index, pip_index in finger_pairs:

        tip = landmarks[tip_index]
        pip = landmarks[pip_index]

        tip_distance = math.sqrt(
            (tip.x - wrist.x) ** 2
            +
            (tip.y - wrist.y) ** 2
        )

        pip_distance = math.sqrt(
            (pip.x - wrist.x) ** 2
            +
            (pip.y - wrist.y) ** 2
        )

        if tip_distance < pip_distance * 1.12:
            curled_fingers += 1

    return thumb_is_up and curled_fingers >= 3


def is_index_pointing(landmarks):
    """Detect index pointing while the other three fingers remain curled.

    Distances are measured from the wrist so the detector is less sensitive
    to whether the hand is rotated slightly in the camera view.
    """
    if landmarks is None:
        return False

    wrist = landmarks[0]

    def distance_from_wrist(index):
        point = landmarks[index]
        return math.hypot(point.x - wrist.x, point.y - wrist.y)

    index_extended = distance_from_wrist(8) > distance_from_wrist(6) * 1.12
    curled_count = 0
    for tip_index, pip_index in ((12, 10), (16, 14), (20, 18)):
        if distance_from_wrist(tip_index) < distance_from_wrist(pip_index) * 1.12:
            curled_count += 1

    return index_extended and curled_count >= 2


# ============================================================
# MAIN LOOP
# ============================================================

try:

    camera = Camera()
    tracker = HandTracker()

    while True:

        # The launcher requests a clean shutdown through a small flag file.
        # This keeps held keys/buttons releasable through the normal finally path.
        if stop_requested():
            break

        now = time.monotonic()
        if now - last_settings_check >= 0.5:
            runtime_settings = load_settings()
            MOUSE_HAND_SENSITIVITY = runtime_settings["mouse_sensitivity"]
            MOUSE_HAND_DEADZONE = runtime_settings["mouse_deadzone"]
            MOUSE_HAND_MAX_STEP = runtime_settings["mouse_max_step"]
            last_settings_check = now

        # ----------------------------------------------------
        # CAMERA
        # ----------------------------------------------------

        frame = camera.read()
        fps_frame_count += 1


        # ----------------------------------------------------
        # HAND TRACKING
        # ----------------------------------------------------

        results = tracker.process(frame)

        left_hand, right_hand = tracker.get_hands(results)

        tracker.draw_landmarks(
            frame,
            results
        )


        # ====================================================
        # HAND PRESENCE
        # ====================================================

        left_present = left_hand is not None
        right_present = right_hand is not None

        both_hands_present = (
            left_present
            and
            right_present
        )

        both_hands_missing = (
            not left_present
            and
            not right_present
        )


        # ====================================================
        # CALIBRATION RE-ARM LOGIC
        # ====================================================
        #
        # IMPORTANT:
        #
        # We DO NOT care about hand movement here.
        #
        # We only care whether BOTH hands completely disappear
        # from the camera.
        #
        # Example:
        #
        # Both hands visible
        #       ↓
        # Move hands around
        #       ↓
        # NO recalibration
        #
        # Both hands leave camera
        #       ↓
        # calibration becomes armed
        #
        # Both hands return
        #       ↓
        # recalibrate
        # ====================================================

        if calibrated:

            if both_hands_missing:

                both_hands_were_gone = True

                calibration_armed = True


        # ====================================================
        # INITIAL / RE-CALIBRATION
        # ====================================================

        if not calibrated:

            # ------------------------------------------------
            # Wait until BOTH hands are visible
            # ------------------------------------------------

            if both_hands_present:

                if calibration_start is None:

                    calibration_start = time.monotonic()


                elapsed = (
                    time.monotonic()
                    -
                    calibration_start
                )


                remaining = max(
                    0,
                    1.0 - elapsed
                )


                cv2.putText(
                    frame,
                    f"CALIBRATING {remaining:.1f}",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )


                # --------------------------------------------
                # CALIBRATION COMPLETE
                # --------------------------------------------

                if elapsed >= 1.0:

                    # ----------------------------------------
                    # LEFT WRIST MOVEMENT CENTER
                    # ----------------------------------------

                    movement.calibrate(
                        left_hand
                    )


                    # ----------------------------------------
                    # RIGHT-HAND MOUSE REFERENCE
                    # ----------------------------------------

                    movement.calibrate_thumb(
                        hand_center_mouse_reference(right_hand)
                    )


                    # ----------------------------------------
                    # CALIBRATION FINISHED
                    # ----------------------------------------

                    calibrated = True

                    calibration_start = None

                    # We have now consumed this calibration.
                    calibration_armed = False

                    both_hands_were_gone = False


            else:

                # At least one hand is missing.
                # Do NOT calibrate.

                calibration_start = None


                cv2.putText(
                    frame,
                    "SHOW BOTH HANDS TO CALIBRATE",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )


        # ====================================================
        # NORMAL CONTROLLER OPERATION
        # ====================================================

        else:

            # =================================================
            # NEW CALIBRATION
            # =================================================
            #
            # A new calibration is allowed ONLY if:
            #
            # 1. The previous calibration already happened.
            #
            # 2. BOTH hands completely disappeared.
            #
            # 3. BOTH hands have now returned.
            #
            # Hand movement alone cannot trigger this.
            # =================================================

            if (
                both_hands_present
                and
                calibration_armed
                and
                both_hands_were_gone
            ):

                # ---------------------------------------------
                # Release all active controls
                # ---------------------------------------------

                controller.emergency_stop()


                # ---------------------------------------------
                # Reset controller states
                # ---------------------------------------------

                space_held = False
                interact_held = False
                fist_active = False
                crouch_held = False
                ctrl_held = False
                alt_held = False
                q_was_detected = False
                r_active = False
                r_counter = 0

                aim_held = False
                shift_held = False

                aim_counter = 0
                shift_counter = 0

                attack_held = False
                attack_stability = 0


                # ---------------------------------------------
                # Start new calibration
                # ---------------------------------------------

                calibrated = False

                calibration_start = time.monotonic()

                calibration_armed = False

                both_hands_were_gone = False


                cv2.putText(
                    frame,
                    "RECALIBRATING...",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )


            else:

                # =================================================
                # SAFE RELEASE WHEN HAND TRACKING IS LOST
                # =================================================

                if left_hand is None:

                    controller.set_movement("STOP")

                    if space_held or KEY_BINDINGS["jump"] in controller.held_keys:

                        controller.key_up(KEY_BINDINGS["jump"])
                        space_held = KEY_BINDINGS["jump"] in controller.held_keys

                    if interact_held or KEY_BINDINGS["interact"] in controller.held_keys:

                        controller.key_up(KEY_BINDINGS["interact"])
                        interact_held = KEY_BINDINGS["interact"] in controller.held_keys

                    if attack_held or controller.mouse_left_held:

                        controller.mouse_left_up()

                        attack_held = controller.mouse_left_held

                    attack_stability = 0
                    fist_active = False
                    q_was_detected = False
                    for held_state, binding_name in (
                        (crouch_held, "crouch"),
                        (ctrl_held, "ctrl"),
                    ):
                        if held_state or KEY_BINDINGS[binding_name] in controller.held_keys:
                            controller.key_up(KEY_BINDINGS[binding_name])
                    crouch_held = False
                    ctrl_held = False


                if right_hand is None:
                    if alt_held or KEY_BINDINGS["alt"] in controller.held_keys:
                        controller.key_up(KEY_BINDINGS["alt"])
                    alt_held = False


                    if controller.mouse_right_held:

                        controller.mouse_right_up()

                    if shift_held or KEY_BINDINGS["sprint"] in controller.held_keys:

                        controller.key_up(KEY_BINDINGS["sprint"])

                    if attack_held or controller.mouse_left_held:

                        controller.mouse_left_up()

                        attack_held = controller.mouse_left_held

                    aim_held = False
                    shift_held = False
                    aim_counter = 0
                    shift_counter = 0
                    attack_stability = 0
                    r_active = False
                    r_counter = 0
                    thumb_mouse_active = False
                    previous_mouse_hand_center = None


                # =================================================
                # LEFT HAND MOVEMENT
                # =================================================

                if left_hand is not None:

                    direction, _, _ = (
                        movement.update(
                            left_hand
                        )
                    )

                    controller.set_movement(
                        direction
                    )

                else:

                    controller.set_movement(
                        "STOP"
                    )


                # =================================================
                # LEFT HAND GESTURES
                # =================================================

                left_gesture = (
                    gestures.detect_left_hand(
                        left_hand
                    )
                )


                # =================================================
                # SPACE
                #
                # LEFT THUMB + LEFT PINKY PINCH
                #
                # Pinch  = hold Space
                # Release = release Space
                # =================================================

                jump_detected = (
                    left_hand is not None
                    and
                    gestures.is_jump(
                        left_hand
                    )
                )


                if jump_detected:

                    if not space_held or KEY_BINDINGS["jump"] not in controller.held_keys:

                        controller.key_down(KEY_BINDINGS["jump"])
                        space_held = KEY_BINDINGS["jump"] in controller.held_keys


                else:

                    if space_held or KEY_BINDINGS["jump"] in controller.held_keys:

                        controller.key_up(KEY_BINDINGS["jump"])
                        space_held = KEY_BINDINGS["jump"] in controller.held_keys


                # =================================================
                # E
                #
                # LEFT THUMB + LEFT MIDDLE PINCH
                #
                # Pinch  = hold E
                # Release = release E
                # =================================================

                interact_detected = (
                    left_hand is not None
                    and
                    gestures.is_interact(
                        left_hand
                    )
                )


                if interact_detected:

                    if not interact_held or KEY_BINDINGS["interact"] not in controller.held_keys:

                        controller.key_down(KEY_BINDINGS["interact"])
                        interact_held = KEY_BINDINGS["interact"] in controller.held_keys


                else:

                    if interact_held or KEY_BINDINGS["interact"] in controller.held_keys:

                        controller.key_up(KEY_BINDINGS["interact"])
                        interact_held = KEY_BINDINGS["interact"] in controller.held_keys


                # =================================================
                # NEW LEFT-HAND KEYS: C, Q, LEFT CTRL
                # =================================================

                # C: left thumb + ring fingertip pinch (hold).
                crouch_detected = (
                    left_hand is not None
                    and left_finger_pinch(left_hand, 16)
                )
                if crouch_detected:
                    if not crouch_held or KEY_BINDINGS["crouch"] not in controller.held_keys:
                        controller.key_down(KEY_BINDINGS["crouch"])
                        crouch_held = KEY_BINDINGS["crouch"] in controller.held_keys
                else:
                    if crouch_held or KEY_BINDINGS["crouch"] in controller.held_keys:
                        controller.key_up(KEY_BINDINGS["crouch"])
                        crouch_held = KEY_BINDINGS["crouch"] in controller.held_keys

                # Q: pinky extended, other fingers curled (tap once per pose).
                q_detected = is_left_q_pose(left_hand)
                if q_detected and not q_was_detected:
                    controller.press(KEY_BINDINGS["ability"])
                    q_display_until = time.monotonic() + 0.55
                q_was_detected = q_detected

                # Left Ctrl: shaka pose (thumb + pinky extended).
                ctrl_detected = is_left_shaka(left_hand)
                if ctrl_detected:
                    if not ctrl_held or KEY_BINDINGS["ctrl"] not in controller.held_keys:
                        controller.key_down(KEY_BINDINGS["ctrl"])
                        ctrl_held = KEY_BINDINGS["ctrl"] in controller.held_keys
                else:
                    if ctrl_held or KEY_BINDINGS["ctrl"] in controller.held_keys:
                        controller.key_up(KEY_BINDINGS["ctrl"])
                        ctrl_held = KEY_BINDINGS["ctrl"] in controller.held_keys

                # =================================================
                # F
                #
                # LEFT HAND FIST
                # =================================================

                fist_detected = (
                    left_gesture == "FIST"
                )


                if fist_detected:

                    if not fist_active:

                        controller.press(KEY_BINDINGS["fist_action"])

                        fist_active = True


                else:

                    fist_active = False


                # One-shot keys should never remain held. If Windows rejected
                # a key-up event, retry the release on the next frame.
                for transient_key in (KEY_BINDINGS["fist_action"], KEY_BINDINGS["reload"]):
                    if transient_key in controller.held_keys:
                        controller.key_up(transient_key)

                # =================================================
                # THUMBS-UP DETECTION
                # =================================================

                thumbs_up_detected = is_thumbs_up(right_hand)


                # =================================================
                # R - RIGHT THUMB + PINKY PINCH
                # =================================================

                r_detected = (
                    right_hand is not None
                    and
                    not thumbs_up_detected
                    and
                    right_finger_pinch(right_hand, 20)
                )

                if thumbs_up_detected:

                    # Do not allow the curled pinky used by a
                    # thumbs-up to trigger R when mouse mode ends.
                    r_active = True
                    r_counter = 0

                elif r_detected:

                    # Require two consecutive frames before firing R.
                    # This filters one-frame landmark noise without changing
                    # the one-shot / release-to-rearm behavior.
                    r_counter = min(2, r_counter + 1)

                    if r_counter >= 2 and not r_active:

                        controller.press(KEY_BINDINGS["reload"])

                        # Keep a brief on-screen indicator so the one-shot
                        # R key press is visible in the controller GUI.
                        r_display_until = time.monotonic() + 0.5

                        r_active = True

                else:

                    r_counter = 0
                    r_active = False


                # =================================================
                # THUMBS-UP = WHOLE-HAND MOUSE CONTROL
                # =================================================
                # Mouse control remains active only while the right
                # hand shows a thumbs-up. The mouse reference point is
                # now the center of the hand (wrist + four MCP joints),
                # not the tip of the thumb. Existing MovementTracker
                # sensitivity and joystick-style behavior are preserved.

                if right_hand is not None and thumbs_up_detected:

                    current_hand_center = hand_center_position(
                        right_hand
                    )

                    if not thumb_mouse_active:

                        # Establish a fresh starting point whenever mouse mode
                        # begins, so activating thumbs-up cannot jump the cursor.
                        previous_mouse_hand_center = current_hand_center
                        thumb_mouse_active = True

                    elif previous_mouse_hand_center is not None:

                        # Relative tracking: mouse motion follows the change in
                        # whole-hand position from one frame to the next. If the
                        # hand stops moving, the cursor stops too.
                        frame_height, frame_width = frame.shape[:2]

                        hand_dx = (
                            current_hand_center[0]
                            - previous_mouse_hand_center[0]
                        )
                        hand_dy = (
                            current_hand_center[1]
                            - previous_mouse_hand_center[1]
                        )

                        # Always refresh the reference so small movements do not
                        # accumulate into unwanted cursor drift.
                        previous_mouse_hand_center = current_hand_center

                        # Ignore tiny landmark jitter independently on each axis.
                        if abs(hand_dx) < MOUSE_HAND_DEADZONE:
                            hand_dx = 0.0

                        if abs(hand_dy) < MOUSE_HAND_DEADZONE:
                            hand_dy = 0.0

                        mouse_dx = round(
                            hand_dx * frame_width * MOUSE_HAND_SENSITIVITY
                        )
                        mouse_dy = round(
                            hand_dy * frame_height * MOUSE_HAND_SENSITIVITY
                        )

                        # Limit per-frame movement to keep the cursor controllable.
                        mouse_dx = max(
                            -MOUSE_HAND_MAX_STEP,
                            min(MOUSE_HAND_MAX_STEP, mouse_dx)
                        )
                        mouse_dy = max(
                            -MOUSE_HAND_MAX_STEP,
                            min(MOUSE_HAND_MAX_STEP, mouse_dy)
                        )

                        controller.move_mouse(
                            mouse_dx,
                            mouse_dy
                        )

                else:

                    thumb_mouse_active = False
                    previous_mouse_hand_center = None


                # =================================================
                # RIGHT HAND GESTURES
                # =================================================

                # Left Alt: right thumb + index fingertip pinch. Suppress it
                # during thumbs-up mouse mode so mouse activation/movement is untouched.
                alt_detected = (
                    right_hand is not None
                    and not thumbs_up_detected
                    and right_finger_pinch(right_hand, 8)
                )
                if alt_detected:
                    if not alt_held or KEY_BINDINGS["alt"] not in controller.held_keys:
                        controller.key_down(KEY_BINDINGS["alt"])
                        alt_held = KEY_BINDINGS["alt"] in controller.held_keys
                else:
                    if alt_held or KEY_BINDINGS["alt"] in controller.held_keys:
                        controller.key_up(KEY_BINDINGS["alt"])
                        alt_held = KEY_BINDINGS["alt"] in controller.held_keys

                # Right-hand controls that previously depended on
                # finger curling/movement now require thumb-to-finger
                # pinches: middle finger = AIM, ring finger = SHIFT.
                # A single pinch must be present so overlapping pinches
                # do not activate both controls at once.
                middle_pinch_detected = (
                    right_hand is not None
                    and right_finger_pinch(right_hand, 12)
                )

                ring_pinch_detected = (
                    right_hand is not None
                    and right_finger_pinch(right_hand, 16)
                )

                if middle_pinch_detected and not ring_pinch_detected and not thumbs_up_detected:
                    right_gesture = "AIM"
                elif ring_pinch_detected and not middle_pinch_detected and not thumbs_up_detected:
                    right_gesture = "SHIFT"
                else:
                    right_gesture = "NONE"

                # Thumbs-up activates mouse mode. In that mode, pointing with
                # the index finger holds AIM/RMB; curling it releases AIM while
                # mouse movement remains active. Outside mouse mode, the
                # original middle-finger pinch continues to control AIM.
                mouse_aim_mode = bool(
                    right_hand is not None and thumbs_up_detected and thumb_mouse_active
                )

                if thumbs_up_detected:
                    shift_counter = 0
                    if shift_held or KEY_BINDINGS["sprint"] in controller.held_keys:
                        controller.key_up(KEY_BINDINGS["sprint"])
                        shift_held = KEY_BINDINGS["sprint"] in controller.held_keys

                if mouse_aim_mode:
                    if not pointing_aim_mode_was_active:
                        # Do not carry a previous middle-pinch hold into mouse mode.
                        aim_counter = 0
                    aim_detected = is_index_pointing(right_hand)
                    pointing_aim_mode_was_active = True
                else:
                    aim_detected = right_gesture == "AIM"
                    # Leaving thumbs-up mode must release pointing AIM at once.
                    # Normal middle-pinch AIM can begin its own stability check
                    # on this same frame and is not disabled by this transition.
                    if pointing_aim_mode_was_active:
                        pointing_aim_mode_was_active = False
                        aim_counter = 0
                        if aim_held:
                            aim_held = False
                            if controller.mouse_right_held:
                                controller.mouse_right_up()
                            if attack_held or controller.mouse_left_held:
                                controller.mouse_left_up()
                                attack_held = controller.mouse_left_held
                                attack_stability = 0

                if aim_detected:

                    aim_counter = min(
                        FINGER_STABILITY_FRAMES,
                        aim_counter + 1
                    )

                else:

                    aim_counter = max(
                        0,
                        aim_counter - 1
                    )


                if (
                    aim_counter
                    >=
                    FINGER_STABILITY_FRAMES
                ):

                    new_aim = True

                elif aim_counter == 0:

                    new_aim = False

                else:

                    new_aim = aim_held


                # -------------------------------------------------
                # AIM STATE CHANGED
                # -------------------------------------------------

                if new_aim != aim_held:

                    aim_held = new_aim


                    # Release attack when switching modes.

                    if attack_held or controller.mouse_left_held:

                        controller.mouse_left_up()

                        attack_held = controller.mouse_left_held

                        attack_stability = 0


                # =================================================
                # RIGHT MOUSE / AIM
                # =================================================

                if aim_held:

                    if not controller.mouse_right_held:

                        controller.mouse_right_down()

                else:

                    if controller.mouse_right_held:

                        controller.mouse_right_up()


                # =================================================
                # SHIFT
                #
                # RIGHT THUMB + RING-FINGER PINCH
                # =================================================

                shift_detected = (
                    right_gesture == "SHIFT"
                )


                if shift_detected:

                    shift_counter = min(
                        FINGER_STABILITY_FRAMES,
                        shift_counter + 1
                    )

                else:

                    shift_counter = max(
                        0,
                        shift_counter - 1
                    )


                # -------------------------------------------------
                # SHIFT DOWN
                # -------------------------------------------------

                if (
                    shift_counter
                    >=
                    FINGER_STABILITY_FRAMES
                ):

                    if not shift_held or KEY_BINDINGS["sprint"] not in controller.held_keys:

                        controller.key_down(KEY_BINDINGS["sprint"])
                        shift_held = KEY_BINDINGS["sprint"] in controller.held_keys


                # -------------------------------------------------
                # SHIFT UP
                # -------------------------------------------------

                elif shift_counter == 0:

                    if shift_held or KEY_BINDINGS["sprint"] in controller.held_keys:

                        controller.key_up(KEY_BINDINGS["sprint"])
                        shift_held = KEY_BINDINGS["sprint"] in controller.held_keys


                # =================================================
                # ATTACK / FIRE
                # =================================================
                #
                # AIM OFF:
                #
                #     LEFT THUMB + LEFT INDEX PINCH
                #
                # AIM ON:
                #
                #     LEFT PINKY CURL
                #
                # =================================================

                if aim_held:

                    # ---------------------------------------------
                    # AIM ON
                    #
                    # LEFT PINKY = FIRE
                    # ---------------------------------------------

                    if left_hand is not None and right_hand is not None:

                        attack_detected = (
                            gestures.is_pinky_fire(
                                left_hand
                            )
                        )

                    else:

                        attack_detected = False


                else:

                    # ---------------------------------------------
                    # AIM OFF
                    #
                    # LEFT THUMB + LEFT INDEX = ATTACK
                    # ---------------------------------------------

                    attack_detected = (
                        left_hand is not None
                        and
                        right_hand is not None
                        and
                        left_index_pinch(
                            left_hand
                        )
                    )


                # =================================================
                # ATTACK STABILITY
                # =================================================

                if attack_detected:

                    attack_stability = min(
                        ATTACK_STABILITY_FRAMES,
                        attack_stability + 1
                    )

                else:

                    attack_stability = max(
                        0,
                        attack_stability - 1
                    )


                # =================================================
                # LMB DOWN
                # =================================================

                if (
                    attack_stability
                    >=
                    ATTACK_STABILITY_FRAMES
                ):

                    if not attack_held or not controller.mouse_left_held:

                        controller.mouse_left_down()

                        attack_held = controller.mouse_left_held


                # =================================================
                # LMB UP
                # =================================================

                elif attack_stability == 0:

                    if attack_held or controller.mouse_left_held:

                        controller.mouse_left_up()

                        attack_held = controller.mouse_left_held


                # =================================================
                # STATUS DISPLAY
                # =================================================

                attack_source = (
                    "RIGHT PINKY"
                    if aim_held
                    else
                    "RIGHT INDEX PINCH"
                )


                cv2.putText(
                    frame,
                    f"ATTACK: {attack_source}",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                cv2.putText(
                    frame,
                    f"AIM: {'ON' if aim_held else 'OFF'}",
                    (30, 85),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                cv2.putText(
                    frame,
                    f"LMB: {'HELD' if attack_held else 'OFF'}",
                    (30, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                cv2.putText(
                    frame,
                    f"RMB: {'HELD' if controller.mouse_right_held else 'OFF'}",
                    (30, 155),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                cv2.putText(
                    frame,
                    f"SHIFT: {'HELD' if shift_held else 'OFF'}",
                    (30, 190),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                cv2.putText(
                    frame,
                    f"SPACE: {'HELD' if space_held else 'OFF'}",
                    (30, 225),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                cv2.putText(
                    frame,
                    f"E: {'HELD' if interact_held else 'OFF'}",
                    (30, 260),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                cv2.putText(
                    frame,
                    f"MOVE: {movement.last_direction}",
                    (30, 295),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                cv2.putText(
                    frame,
                    f"THUMB MOUSE: {'ACTIVE' if thumb_mouse_active else 'OFF'}",
                    (30, 330),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0) if thumb_mouse_active else (180, 180, 180),
                    2
                )


                cv2.putText(
                    frame,
                    f"R: {'TRIGGERED' if time.monotonic() < r_display_until else 'OFF'}",
                    (30, 365),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0) if time.monotonic() < r_display_until else (180, 180, 180),
                    2
                )


                # NEW KEYS STATUS: show each key's live state on the camera UI.
                # Q is a tap action, so show TRIGGERED briefly after it fires.
                new_key_status = [
                    (f"C / {KEY_BINDINGS['crouch'].upper()}: {'HELD' if crouch_held else 'OFF'}", crouch_held),
                    (f"Q / {KEY_BINDINGS['ability'].upper()}: {'TRIGGERED' if time.monotonic() < q_display_until else 'OFF'}", time.monotonic() < q_display_until),
                    (f"RIGHT CTRL: {'HELD' if ctrl_held else 'OFF'}", ctrl_held),
                    (f"RIGHT ALT: {'HELD' if alt_held else 'OFF'}", alt_held),
                ]
                for status_index, (status_text, status_active) in enumerate(new_key_status):
                    cv2.putText(
                        frame,
                        status_text,
                        (360, 50 + status_index * 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.62,
                        (0, 255, 0) if status_active else (180, 180, 180),
                        2
                    )


        # ====================================================
        # EXIT TEXT
        # ====================================================

        cv2.putText(
            frame,
            "] = EXIT",
            (
                frame.shape[1] - 150,
                frame.shape[0] - 20
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )


        # ====================================================
        # STATUS FOR THE CONTROL PANEL
        # ====================================================

        status_now = time.monotonic()
        fps_elapsed = status_now - fps_window_start
        if fps_elapsed >= 1.0:
            current_fps = fps_frame_count / fps_elapsed
            fps_frame_count = 0
            fps_window_start = status_now

        if status_now - last_status_write >= 0.15:
            active_controls = []
            if aim_held:
                active_controls.append("AIM / RMB")
            if shift_held:
                active_controls.append(f"SPRINT / {KEY_BINDINGS['sprint'].upper()}")
            if attack_held:
                active_controls.append("FIRE / LMB")
            if space_held:
                active_controls.append(f"JUMP / {KEY_BINDINGS['jump'].upper()}")
            if interact_held:
                active_controls.append(f"INTERACT / {KEY_BINDINGS['interact'].upper()}")
            if crouch_held:
                active_controls.append(f"C / {KEY_BINDINGS['crouch'].upper()}")
            if ctrl_held:
                active_controls.append("RIGHT CTRL")
            if alt_held:
                active_controls.append("RIGHT ALT")
            if q_was_detected:
                active_controls.append(f"Q / {KEY_BINDINGS['ability'].upper()}")
            if fist_active:
                active_controls.append("F")
            if thumb_mouse_active:
                active_controls.append("MOUSE")
            if status_now < r_display_until:
                active_controls.append("R")

            write_status({
                "running": True,
                "calibrated": bool(calibrated),
                "left_hand_detected": bool(left_present),
                "right_hand_detected": bool(right_present),
                "mouse_active": bool(thumb_mouse_active),
                "aim_active": bool(aim_held),
                "sprint_active": bool(shift_held),
                "attack_active": bool(attack_held),
                "movement": movement.last_direction if calibrated else "CALIBRATING",
                "active_controls": active_controls,
                "mouse_sensitivity": MOUSE_HAND_SENSITIVITY,
                "fps": round(current_fps, 1),
            })
            last_status_write = status_now

        # ====================================================
        # DISPLAY
        # ====================================================

        cv2.imshow(
            "Hand Game Controller",
            frame
        )


        # ====================================================
        # EXIT KEY
        # ====================================================

        key = cv2.waitKey(1) & 0xFF


        if key == ord(EXIT_KEY):

            break

except Exception:
    logging.exception("The hand game controller stopped because of an error.")
    raise


# ============================================================
# SAFE SHUTDOWN
# ============================================================

finally:

    # Shutdown is deliberately nested so a failure while releasing one
    # resource cannot prevent the remaining cleanup steps from running.
    try:
        controller.emergency_stop()
    finally:
        try:
            if tracker is not None:
                tracker.close()
        finally:
            try:
                if camera is not None:
                    camera.release()
            finally:
                try:
                    cv2.destroyAllWindows()
                finally:
                    write_status({
                        "running": False,
                        "calibrated": False,
                        "left_hand_detected": False,
                        "right_hand_detected": False,
                        "mouse_active": False,
                        "aim_active": False,
                        "sprint_active": False,
                        "attack_active": False,
                        "movement": "STOP",
                        "active_controls": [],
                        "mouse_sensitivity": MOUSE_HAND_SENSITIVITY,
                        "fps": 0.0,
                    })