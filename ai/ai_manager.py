import threading

from ai.smartvision.processor import SmartVisionProcessor
from ai.trafficvision.processor import TrafficVisionProcessor


class AIManager:

    def __init__(
        self,
        parking_manager=None
    ):

        self.smartvision = SmartVisionProcessor()
        self.trafficvision = TrafficVisionProcessor()

        self.camera_modes = {}

        self.latest_detections = {}
        self.latest_parking_stats = {}

        self.parking_manager = parking_manager

        self.lock = threading.Lock()

    def set_parking_manager(
        self,
        parking_manager
    ):

        self.parking_manager = parking_manager

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

        with self.lock:

            self.camera_modes[
                camera_id
            ] = mode

        print(
            f"[AI] Camera {camera_id} "
            f"mode: {mode}"
        )

    def get_camera_mode(
        self,
        camera_id
    ):

        with self.lock:

            return self.camera_modes.get(
                camera_id,
                "none"
            )

    def start(self):

        self.smartvision.start()
        self.trafficvision.start()

    def stop(self):

        self.smartvision.stop()
        self.trafficvision.stop()

    def process(
        self,
        camera_id,
        frame
    ):

        mode = self.get_camera_mode(
            camera_id
        )

        detections = []

        processed_frame = frame

        try:

            if mode == "smartvision":

                processed_frame, detections = (
                    self.smartvision.process(
                        frame
                    )
                )

            elif mode == "trafficvision":

                processed_frame, detections = (
                    self.trafficvision.process(
                        frame
                    )
                )

        except Exception as error:

            print(
                f"[AI] Camera {camera_id} "
                f"processing error: {error}"
            )

            processed_frame = frame
            detections = []

        with self.lock:

            self.latest_detections[
                camera_id
            ] = list(detections)

        if (
            mode == "trafficvision"
            and self.parking_manager is not None
        ):

            try:

                (
                    processed_frame,
                    statistics
                ) = self.parking_manager.draw(
                    processed_frame,
                    camera_id,
                    detections
                )

                with self.lock:

                    self.latest_parking_stats[
                        camera_id
                    ] = statistics

            except Exception as error:

                print(
                    f"[Parking] Camera "
                    f"{camera_id} error: {error}"
                )

        else:

            with self.lock:

                self.latest_parking_stats[
                    camera_id
                ] = {
                    "total_spaces": 0,
                    "occupied_spaces": 0,
                    "available_spaces": 0,
                    "occupancy": []
                }

        return (
            processed_frame,
            detections
        )

    def get_detections(
        self,
        camera_id
    ):

        with self.lock:

            return list(
                self.latest_detections.get(
                    camera_id,
                    []
                )
            )

    def get_camera_detection_count(
        self,
        camera_id
    ):

        with self.lock:

            return len(
                self.latest_detections.get(
                    camera_id,
                    []
                )
            )

    def get_global_detection_count(self):

        with self.lock:

            return sum(
                len(detections)
                for detections
                in self.latest_detections.values()
            )

    def get_parking_statistics(
        self,
        camera_id
    ):

        with self.lock:

            statistics = (
                self.latest_parking_stats.get(
                    camera_id
                )
            )

            if statistics is None:

                return {
                    "total_spaces": 0,
                    "occupied_spaces": 0,
                    "available_spaces": 0,
                    "occupancy": []
                }

            return statistics.copy()

    def get_global_parking_statistics(self):

        total_spaces = 0
        occupied_spaces = 0
        available_spaces = 0

        with self.lock:

            for statistics in (
                self.latest_parking_stats.values()
            ):

                total_spaces += statistics.get(
                    "total_spaces",
                    0
                )

                occupied_spaces += statistics.get(
                    "occupied_spaces",
                    0
                )

                available_spaces += statistics.get(
                    "available_spaces",
                    0
                )

        return {
            "total_spaces": total_spaces,
            "occupied_spaces": occupied_spaces,
            "available_spaces": available_spaces
        }

    def get_status(self):

        with self.lock:

            camera_modes = (
                self.camera_modes.copy()
            )

            detection_counts = {
                camera_id: len(detections)
                for camera_id, detections
                in self.latest_detections.items()
            }

        return {

            "smartvision":
                self.smartvision.get_status(),

            "trafficvision":
                self.trafficvision.get_status(),

            "camera_modes":
                camera_modes,

            "detection_counts":
                detection_counts,

            "total_detections":
                sum(
                    detection_counts.values()
                ),

            "parking":
                self.get_global_parking_statistics()
        }