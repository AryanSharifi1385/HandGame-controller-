import cv2
import time
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from app_paths import asset_path


class HandTracker:

    def __init__(self):

        base_options = python.BaseOptions(
            model_asset_path=str(asset_path("hand_landmarker.task"))
        )

        options = vision.HandLandmarkerOptions(

            base_options=base_options,

            running_mode=(
                vision.RunningMode.VIDEO
            ),

            num_hands=2,

            min_hand_detection_confidence=0.6,

            min_hand_presence_confidence=0.6,

            min_tracking_confidence=0.6
        )

        self.detector = (
            vision.HandLandmarker
            .create_from_options(options)
        )

        self.start_time = time.monotonic()


    def process(self, frame):

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        timestamp_ms = int(
            (
                time.monotonic()
                -
                self.start_time
            )
            *
            1000
        )

        results = (
            self.detector.detect_for_video(
                mp_image,
                timestamp_ms
            )
        )

        return results


    def close(self):
        """Release the MediaPipe task resources when the app exits."""
        if getattr(self, "detector", None) is not None:
            self.detector.close()
            self.detector = None


    def get_hands(self, results):

        left_hand = None
        right_hand = None

        if not results.hand_landmarks:

            return left_hand, right_hand

        for i, landmarks in enumerate(
            results.hand_landmarks
        ):

            if i >= len(
                results.handedness
            ):
                continue

            handedness = (
                results.handedness[i]
            )

            if not handedness:
                continue

            label = (
                handedness[0]
                .category_name
            )

            if label == "Left":

                left_hand = landmarks

            elif label == "Right":

                right_hand = landmarks

        return left_hand, right_hand


    def draw_landmarks(
        self,
        frame,
        results
    ):

        if not results.hand_landmarks:
            return

        height, width, _ = frame.shape

        connections = [

            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),

            (0, 5),
            (5, 6),
            (6, 7),
            (7, 8),

            (5, 9),
            (9, 10),
            (10, 11),
            (11, 12),

            (9, 13),
            (13, 14),
            (14, 15),
            (15, 16),

            (13, 17),
            (17, 18),
            (18, 19),
            (19, 20),

            (0, 17)
        ]

        for i, hand_landmarks in enumerate(
            results.hand_landmarks
        ):

            points = []

            for landmark in hand_landmarks:

                x = int(
                    landmark.x * width
                )

                y = int(
                    landmark.y * height
                )

                points.append(
                    (x, y)
                )

                cv2.circle(
                    frame,
                    (x, y),
                    5,
                    (0, 255, 0),
                    -1
                )

            for start, end in connections:

                cv2.line(
                    frame,
                    points[start],
                    points[end],
                    (255, 0, 0),
                    2
                )

            if i < len(
                results.handedness
            ):

                handedness = (
                    results.handedness[i]
                )

                if handedness:

                    label = (
                        handedness[0]
                        .category_name
                    )
                    # Display-only swap requested for the camera overlay.
                    # Keep the actual handedness labels used by get_hands unchanged.
                    display_label = "Right" if label == "Left" else "Left" if label == "Right" else label

                    wrist = points[0]

                    cv2.putText(
                        frame,
                        display_label,
                        (
                            wrist[0] - 30,
                            wrist[1] - 20
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2
                    )