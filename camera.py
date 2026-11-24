import cv2

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT
)


class Camera:

    def __init__(self):

        self.camera = cv2.VideoCapture(
            CAMERA_INDEX
        )

        self.camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            FRAME_WIDTH
        )

        self.camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            FRAME_HEIGHT
        )

        if not self.camera.isOpened():

            raise RuntimeError(
                "Could not open webcam."
            )


    def read(self):

        success, frame = self.camera.read()

        if not success:

            raise RuntimeError(
                "Could not read frame from webcam."
            )

        frame = cv2.flip(frame, 1)

        return frame


    def release(self):

        self.camera.release()

        cv2.destroyAllWindows()