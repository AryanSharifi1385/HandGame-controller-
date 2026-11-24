import math


class GestureDetector:

    def __init__(self):
        pass


    # ==========================================================
    # DISTANCE
    # ==========================================================

    def distance(self, p1, p2):

        return math.sqrt(
            (p1.x - p2.x) ** 2
            +
            (p1.y - p2.y) ** 2
        )


    # ==========================================================
    # FINGER CURL
    # ==========================================================

    def finger_is_curled(
        self,
        landmarks,
        tip,
        pip
    ):

        wrist = landmarks[0]

        tip_distance = self.distance(
            landmarks[tip],
            wrist
        )

        pip_distance = self.distance(
            landmarks[pip],
            wrist
        )

        return tip_distance < pip_distance * 0.90


    # ==========================================================
    # FINGER EXTENSION
    # ==========================================================

    def finger_is_extended(
        self,
        landmarks,
        tip,
        pip
    ):

        wrist = landmarks[0]

        tip_distance = self.distance(
            landmarks[tip],
            wrist
        )

        pip_distance = self.distance(
            landmarks[pip],
            wrist
        )

        return tip_distance > pip_distance * 1.10


    # ==========================================================
    # INDEX
    # ==========================================================

    def index_curled(self, landmarks):

        return self.finger_is_curled(
            landmarks,
            8,
            6
        )


    def index_extended(self, landmarks):

        return self.finger_is_extended(
            landmarks,
            8,
            6
        )


    # ==========================================================
    # MIDDLE
    # ==========================================================

    def middle_curled(self, landmarks):

        return self.finger_is_curled(
            landmarks,
            12,
            10
        )


    def middle_extended(self, landmarks):

        return self.finger_is_extended(
            landmarks,
            12,
            10
        )


    # ==========================================================
    # RING
    # ==========================================================

    def ring_curled(self, landmarks):

        return self.finger_is_curled(
            landmarks,
            16,
            14
        )


    def ring_extended(self, landmarks):

        return self.finger_is_extended(
            landmarks,
            16,
            14
        )


    # ==========================================================
    # PINKY
    # ==========================================================

    def pinky_curled(self, landmarks):

        return self.finger_is_curled(
            landmarks,
            20,
            18
        )


    def pinky_extended(self, landmarks):

        return self.finger_is_extended(
            landmarks,
            20,
            18
        )


    # ==========================================================
    # THUMB
    # ==========================================================

    def thumb_is_extended(self, landmarks):

        wrist = landmarks[0]

        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]

        tip_distance = self.distance(
            thumb_tip,
            wrist
        )

        ip_distance = self.distance(
            thumb_ip,
            wrist
        )

        return tip_distance > ip_distance * 1.05


    # ==========================================================
    # OPEN PALM
    # ==========================================================

    def is_open_palm(self, landmarks):

        if landmarks is None:
            return False

        return (
            self.index_extended(landmarks)
            and
            self.middle_extended(landmarks)
            and
            self.ring_extended(landmarks)
            and
            self.pinky_extended(landmarks)
        )


    # ==========================================================
    # FIST
    # ==========================================================

    def is_fist(self, landmarks):

        if landmarks is None:
            return False

        return (
            self.index_curled(landmarks)
            and
            self.middle_curled(landmarks)
            and
            self.ring_curled(landmarks)
            and
            self.pinky_curled(landmarks)
        )


    # ==========================================================
    # E
    #
    # LEFT THUMB + MIDDLE FINGER
    # ==========================================================

    def is_interact(self, landmarks):

        if landmarks is None:
            return False

        thumb = landmarks[4]
        middle = landmarks[12]

        return self.distance(
            thumb,
            middle
        ) < 0.055


    # ==========================================================
    # SPACE
    #
    # LEFT THUMB + PINKY
    # ==========================================================

    def is_jump(self, landmarks):

        if landmarks is None:
            return False

        thumb = landmarks[4]
        pinky = landmarks[20]

        return self.distance(
            thumb,
            pinky
        ) < 0.060


    # ==========================================================
    # LEFT PINKY ATTACK
    #
    # Used ONLY when AIM is ON.
    # ==========================================================

    def is_pinky_fire(self, landmarks):

        if landmarks is None:
            return False

        pinky = self.pinky_curled(
            landmarks
        )

        index = self.index_extended(
            landmarks
        )

        middle = self.middle_extended(
            landmarks
        )

        ring = self.ring_extended(
            landmarks
        )

        return (
            pinky
            and
            index
            and
            middle
            and
            ring
        )


    # ==========================================================
    # RIGHT HAND AIM
    #
    # RIGHT MIDDLE FINGER
    # ==========================================================

    def is_right_aim(self, landmarks):

        if landmarks is None:
            return False

        middle = self.middle_curled(
            landmarks
        )

        index = self.index_extended(
            landmarks
        )

        ring = self.ring_extended(
            landmarks
        )

        pinky = self.pinky_extended(
            landmarks
        )

        return (
            middle
            and
            index
            and
            ring
            and
            pinky
        )


    # ==========================================================
    # RIGHT HAND SHIFT
    #
    # RIGHT RING FINGER
    # ==========================================================

    def is_right_shift(self, landmarks):

        if landmarks is None:
            return False

        ring = self.ring_curled(
            landmarks
        )

        index = self.index_extended(
            landmarks
        )

        middle = self.middle_extended(
            landmarks
        )

        pinky = self.pinky_extended(
            landmarks
        )

        return (
            ring
            and
            index
            and
            middle
            and
            pinky
        )


    # ==========================================================
    # RIGHT HAND ATTACK
    #
    # RIGHT INDEX FINGER
    #
    # ONLY WHEN AIM IS OFF
    # ==========================================================

    def is_right_index_attack(self, landmarks):

        if landmarks is None:
            return False

        index = self.index_curled(
            landmarks
        )

        middle = self.middle_extended(
            landmarks
        )

        ring = self.ring_extended(
            landmarks
        )

        pinky = self.pinky_extended(
            landmarks
        )

        return (
            index
            and
            middle
            and
            ring
            and
            pinky
        )


    # ==========================================================
    # RIGHT HAND GESTURE
    # ==========================================================

    def detect_right_hand(self, landmarks):

        if landmarks is None:
            return "NONE"

        if self.is_right_aim(landmarks):
            return "AIM"

        if self.is_right_shift(landmarks):
            return "SHIFT"

        if self.is_right_index_attack(landmarks):
            return "ATTACK"

        return "NONE"


    # ==========================================================
    # LEFT HAND GESTURE
    # ==========================================================

    def detect_left_hand(self, landmarks):

        if landmarks is None:
            return "NONE"

        if self.is_fist(landmarks):
            return "FIST"

        if self.is_interact(landmarks):
            return "INTERACT"

        if self.is_jump(landmarks):
            return "JUMP"

        return "NONE"