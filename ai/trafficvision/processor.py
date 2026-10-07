from pathlib import Path

import cv2
from ultralytics import YOLO


class TrafficVisionProcessor:

    VEHICLE_CLASSES = {
        1: "bicycle",
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck"
    }

    def __init__(self):

        self.enabled = False

        self.name = "TrafficVision AI"

        base_dir = Path(__file__).resolve().parents[2]

        self.model_path = (
            base_dir
            / "models"
            / "yolo11n.pt"
        )

        self.model = None

        self.confidence = 0.35

        self.device = "cpu"

    def start(self):

        print(
            f"[AI] Loading TrafficVision model: "
            f"{self.model_path}"
        )

        try:

            self.model = YOLO(
                str(self.model_path)
            )

            self.enabled = True

            print(
                "[AI] TrafficVision AI started"
            )

        except Exception as error:

            self.enabled = False

            print(
                "[AI] TrafficVision failed "
                f"to start: {error}"
            )

    def stop(self):

        self.enabled = False

        self.model = None

        print(
            "[AI] TrafficVision AI stopped"
        )

    def process(
        self,
        frame
    ):

        if (
            not self.enabled
            or self.model is None
        ):

            return frame, []

        try:

            results = self.model.track(
                frame,
                persist=True,
                conf=self.confidence,
                device=self.device,
                verbose=False,
                tracker="bytetrack.yaml"
            )

            result = results[0]

            detections = []

            if result.boxes is None:

                return frame, detections

            for box in result.boxes:

                class_id = int(
                    box.cls[0].item()
                )

                if (
                    class_id
                    not in self.VEHICLE_CLASSES
                ):

                    continue

                confidence = float(
                    box.conf[0].item()
                )

                coordinates = (
                    box.xyxy[0]
                    .cpu()
                    .numpy()
                    .astype(int)
                )

                x1, y1, x2, y2 = (
                    coordinates
                )

                track_id = None

                if box.id is not None:

                    track_id = int(
                        box.id[0].item()
                    )

                vehicle_type = (
                    self.VEHICLE_CLASSES[
                        class_id
                    ]
                )

                detections.append(
                    {
                        "track_id": track_id,
                        "class_id": class_id,
                        "class_name": vehicle_type,
                        "confidence": confidence,
                        "bbox": [
                            int(x1),
                            int(y1),
                            int(x2),
                            int(y2)
                        ]
                    }
                )

                self.draw_detection(
                    frame,
                    x1,
                    y1,
                    x2,
                    y2,
                    track_id,
                    vehicle_type,
                    confidence
                )

            return frame, detections

        except Exception as error:

            print(
                "[AI] TrafficVision "
                f"processing error: {error}"
            )

            return frame, []

    def draw_detection(
        self,
        frame,
        x1,
        y1,
        x2,
        y2,
        track_id,
        vehicle_type,
        confidence
    ):

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        if track_id is not None:

            label = (
                f"{vehicle_type} "
                f"#{track_id} "
                f"{confidence:.2f}"
            )

        else:

            label = (
                f"{vehicle_type} "
                f"{confidence:.2f}"
            )

        label_y = max(
            y1 - 10,
            20
        )

        cv2.putText(
            frame,
            label,
            (x1, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

    def get_status(self):

        return {
            "name": self.name,
            "enabled": self.enabled,
            "model": (
                self.model_path.name
            ),
            "device": self.device
        }