from ai.smartvision.processor import SmartVisionProcessor
from ai.trafficvision.processor import TrafficVisionProcessor


class AIManager:

    def __init__(self):

        self.smartvision = SmartVisionProcessor()

        self.trafficvision = TrafficVisionProcessor()

        self.camera_modes = {}

    # --------------------------------------------------

    def set_camera_mode(
        self,
        camera_id,
        mode
    ):

        valid_modes = [
            "none",
            "smartvision",
            "trafficvision"
        ]

        if mode not in valid_modes:

            raise ValueError(
                f"Invalid AI mode: {mode}"
            )

        self.camera_modes[
            camera_id
        ] = mode

        print(
            f"[AI] Camera {camera_id} "
            f"mode: {mode}"
        )

    # --------------------------------------------------

    def get_camera_mode(
        self,
        camera_id
    ):

        return self.camera_modes.get(
            camera_id,
            "none"
        )

    # --------------------------------------------------

    def start(self):

        self.smartvision.start()

        self.trafficvision.start()

    # --------------------------------------------------

    def stop(self):

        self.smartvision.stop()

        self.trafficvision.stop()

    # --------------------------------------------------

    def process(
        self,
        camera_id,
        frame
    ):

        mode = self.get_camera_mode(
            camera_id
        )

        if mode == "smartvision":

            return self.smartvision.process(
                frame
            )

        if mode == "trafficvision":

            return self.trafficvision.process(
                frame
            )

        return frame, []

    # --------------------------------------------------

    def get_status(self):

        return {
            "smartvision":
                self.smartvision.get_status(),

            "trafficvision":
                self.trafficvision.get_status(),

            "camera_modes":
                self.camera_modes.copy()
        }