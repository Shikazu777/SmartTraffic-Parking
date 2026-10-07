import json
from pathlib import Path

from core.camera import Camera


class CameraManager:

    def __init__(
        self,
        config_path,
        ai_manager=None
    ):

        self.config_path = Path(
            config_path
        )

        self.ai_manager = ai_manager

        self.cameras = {}

        self.load_config()

    def load_config(self):

        if not self.config_path.exists():

            raise FileNotFoundError(
                f"Camera configuration not found: "
                f"{self.config_path}"
            )

        with self.config_path.open(
            "r",
            encoding="utf-8"
        ) as file:

            config = json.load(file)

        self.cameras.clear()

        for camera_config in config.get(
            "cameras",
            []
        ):

            camera = Camera(
                camera_config,
                self.process_frame
            )

            self.cameras[
                camera.id
            ] = camera

            if self.ai_manager is not None:

                ai_mode = camera_config.get(
                    "ai_mode",
                    "none"
                )

                self.ai_manager.set_camera_mode(
                    camera.id,
                    ai_mode
                )

    def process_frame(
        self,
        camera_id,
        frame
    ):

        if self.ai_manager is None:

            return frame, []

        return self.ai_manager.process(
            camera_id,
            frame
        )

    def start_all(self):

        print(
            f"Starting {len(self.cameras)} "
            f"camera slots..."
        )

        for camera in self.cameras.values():

            camera.start()

    def get_camera(
        self,
        camera_id
    ):

        return self.cameras.get(
            camera_id
        )

    def get_all(self):

        return list(
            self.cameras.values()
        )

    def get_camera_info(self):

        cameras = []

        for camera in self.cameras.values():

            ai_mode = "none"

            if self.ai_manager is not None:

                ai_mode = (
                    self.ai_manager.get_camera_mode(
                        camera.id
                    )
                )

            cameras.append(
                {
                    "id": camera.id,
                    "name": camera.name,
                    "type": camera.camera_type,
                    "source": camera.source,
                    "enabled": camera.enabled,
                    "status": camera.get_status(),
                    "fps": camera.get_fps(),
                    "ai_mode": ai_mode
                }
            )

        return cameras

    def get_available_cameras(self):

        available = []

        for camera in self.cameras.values():

            if camera.connected:

                available.append(
                    camera.id
                )

        return available

    def get_active_count(self):

        count = 0

        for camera in self.cameras.values():

            if camera.connected:

                count += 1

        return count

    def get_total_count(self):

        return len(self.cameras)

    def stop_all(self):

        print(
            "Stopping all cameras..."
        )

        for camera in self.cameras.values():

            camera.stop()