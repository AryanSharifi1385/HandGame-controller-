from config import (
    DEAD_ZONE,
    MOVEMENT_THRESHOLD,
    SMOOTHING_FACTOR,
    DIRECTION_SWITCH_THRESHOLD,
    MOUSE_SENSITIVITY,
    MOUSE_MOVEMENT_DEAD_ZONE,
    MOUSE_SMOOTHING
)


class MovementTracker:

    def __init__(self):

        # ==========================================
        # LEFT HAND / WALKING
        # ==========================================

        self.neutral_x = 0.50
        self.neutral_y = 0.50

        self.smoothed_x = None
        self.smoothed_y = None

        self.last_direction = "STOP"


        # ==========================================
        # RIGHT THUMB / MOUSE
        # ==========================================

        self.thumb_neutral_x = 0.50
        self.thumb_neutral_y = 0.50

        self.thumb_smoothed_x = None
        self.thumb_smoothed_y = None


    # ==========================================================
    # CALIBRATION
    # ==========================================================

    def calibrate(self, landmarks):

        if landmarks is None:
            return False

        wrist = landmarks[0]

        self.neutral_x = wrist.x
        self.neutral_y = wrist.y

        self.smoothed_x = wrist.x
        self.smoothed_y = wrist.y

        self.last_direction = "STOP"

        return True


    # ==========================================================
    # LEFT HAND MOVEMENT
    # ==========================================================

    def update(self, landmarks):

        if landmarks is None:

            self.last_direction = "STOP"

            return "STOP", None, None


        # ------------------------------------------
        # LEFT WRIST
        # ------------------------------------------

        wrist = landmarks[0]

        x = wrist.x
        y = wrist.y


        # ------------------------------------------
        # INITIALIZATION
        # ------------------------------------------

        if self.smoothed_x is None:

            self.smoothed_x = x
            self.smoothed_y = y

            return "STOP", x, y


        # ------------------------------------------
        # SMOOTH POSITION
        # ------------------------------------------

        self.smoothed_x = (
            SMOOTHING_FACTOR * x
            +
            (1.0 - SMOOTHING_FACTOR)
            * self.smoothed_x
        )

        self.smoothed_y = (
            SMOOTHING_FACTOR * y
            +
            (1.0 - SMOOTHING_FACTOR)
            * self.smoothed_y
        )


        # ------------------------------------------
        # DISTANCE FROM CENTER
        # ------------------------------------------

        dx = (
            self.smoothed_x
            -
            self.neutral_x
        )

        dy = (
            self.smoothed_y
            -
            self.neutral_y
        )


        abs_x = abs(dx)
        abs_y = abs(dy)


        # ==================================================
        # CENTER / STOP
        # ==================================================

        if (
            abs_x < DEAD_ZONE
            and
            abs_y < DEAD_ZONE
        ):

            self.last_direction = "STOP"

            return (
                "STOP",
                self.smoothed_x,
                self.smoothed_y
            )


        # ==================================================
        # CURRENT DIRECTION CONTINUATION
        # ==================================================
        #
        # Once a direction has been selected,
        # don't constantly reconsider it.
        #
        # This is what prevents:
        #
        # W D W D W D W D
        #
        # when the hand is actually being held
        # approximately in one direction.
        #
        # ==================================================

        if self.last_direction == "LEFT":

            # Stay LEFT unless the hand has moved
            # strongly toward another direction.

            if (
                dx > DIRECTION_SWITCH_THRESHOLD
            ):

                self.last_direction = "RIGHT"

            elif (
                abs_y > DIRECTION_SWITCH_THRESHOLD
            ):

                if dy > 0:

                    self.last_direction = "DOWN"

                else:

                    self.last_direction = "UP"

            return (
                self.last_direction,
                self.smoothed_x,
                self.smoothed_y
            )


        if self.last_direction == "RIGHT":

            if (
                dx < -DIRECTION_SWITCH_THRESHOLD
            ):

                self.last_direction = "LEFT"

            elif (
                abs_y > DIRECTION_SWITCH_THRESHOLD
            ):

                if dy > 0:

                    self.last_direction = "DOWN"

                else:

                    self.last_direction = "UP"

            return (
                self.last_direction,
                self.smoothed_x,
                self.smoothed_y
            )


        if self.last_direction == "UP":

            if (
                dy > DIRECTION_SWITCH_THRESHOLD
            ):

                self.last_direction = "DOWN"

            elif (
                abs_x > DIRECTION_SWITCH_THRESHOLD
            ):

                if dx > 0:

                    self.last_direction = "RIGHT"

                else:

                    self.last_direction = "LEFT"

            return (
                self.last_direction,
                self.smoothed_x,
                self.smoothed_y
            )


        if self.last_direction == "DOWN":

            if (
                dy < -DIRECTION_SWITCH_THRESHOLD
            ):

                self.last_direction = "UP"

            elif (
                abs_x > DIRECTION_SWITCH_THRESHOLD
            ):

                if dx > 0:

                    self.last_direction = "RIGHT"

                else:

                    self.last_direction = "LEFT"

            return (
                self.last_direction,
                self.smoothed_x,
                self.smoothed_y
            )


        # ==================================================
        # NO CURRENT DIRECTION
        # ==================================================

        # Only choose a direction when the movement
        # is clearly beyond the threshold.

        if (
            abs_x >= MOVEMENT_THRESHOLD
            or
            abs_y >= MOVEMENT_THRESHOLD
        ):

            # Horizontal movement is dominant.

            if abs_x > abs_y:

                if dx > 0:

                    self.last_direction = "RIGHT"

                else:

                    self.last_direction = "LEFT"


            # Vertical movement is dominant.

            else:

                if dy > 0:

                    self.last_direction = "DOWN"

                else:

                    self.last_direction = "UP"


        else:

            self.last_direction = "STOP"


        return (
            self.last_direction,
            self.smoothed_x,
            self.smoothed_y
        )


    # ==========================================================
    # RIGHT THUMB CALIBRATION
    # ==========================================================

    def calibrate_thumb(self, landmarks):

        if landmarks is None:
            return False

        thumb = landmarks[4]

        self.thumb_neutral_x = thumb.x
        self.thumb_neutral_y = thumb.y

        self.thumb_smoothed_x = thumb.x
        self.thumb_smoothed_y = thumb.y

        return True


    # ==========================================================
    # RIGHT THUMB JOYSTICK
    # ==========================================================

    def update_thumb_mouse(self, landmarks):

        if landmarks is None:
            return 0, 0


        thumb = landmarks[4]

        current_x = thumb.x
        current_y = thumb.y


        if self.thumb_smoothed_x is None:

            self.thumb_smoothed_x = current_x
            self.thumb_smoothed_y = current_y

            return 0, 0


        # ------------------------------------------
        # SMOOTH THUMB
        # ------------------------------------------

        self.thumb_smoothed_x = (
            MOUSE_SMOOTHING * current_x
            +
            (1.0 - MOUSE_SMOOTHING)
            *
            self.thumb_smoothed_x
        )

        self.thumb_smoothed_y = (
            MOUSE_SMOOTHING * current_y
            +
            (1.0 - MOUSE_SMOOTHING)
            *
            self.thumb_smoothed_y
        )


        # ------------------------------------------
        # OFFSET FROM CENTER
        # ------------------------------------------

        dx = (
            self.thumb_smoothed_x
            -
            self.thumb_neutral_x
        )

        dy = (
            self.thumb_smoothed_y
            -
            self.thumb_neutral_y
        )


        # ------------------------------------------
        # DEAD ZONE
        # ------------------------------------------

        if abs(dx) < MOUSE_MOVEMENT_DEAD_ZONE:

            dx = 0

        else:

            if dx > 0:

                dx -= MOUSE_MOVEMENT_DEAD_ZONE

            else:

                dx += MOUSE_MOVEMENT_DEAD_ZONE


        if abs(dy) < MOUSE_MOVEMENT_DEAD_ZONE:

            dy = 0

        else:

            if dy > 0:

                dy -= MOUSE_MOVEMENT_DEAD_ZONE

            else:

                dy += MOUSE_MOVEMENT_DEAD_ZONE


        # ------------------------------------------
        # MOUSE SPEED
        # ------------------------------------------

        mouse_dx = (
            dx
            *
            MOUSE_SENSITIVITY
        )

        mouse_dy = (
            dy
            *
            MOUSE_SENSITIVITY
        )


        return (
            mouse_dx,
            mouse_dy
        )