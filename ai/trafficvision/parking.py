import json
from pathlib import Path

import cv2
import numpy as np


class ParkingManager:

    def __init__(self, config_path):

        self.config_path = Path(config_path)

        self.zones = {}

        self.load()

    def load(self):

        if not self.config_path.exists():

            self.zones = {}

            return

        try:

            with self.config_path.open(
                "r",
                encoding="utf-8"
            ) as file:

                self.zones = json.load(file)

        except Exception:

            self.zones = {}

    def save(self):

        self.config_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with self.config_path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.zones,
                file,
                indent=4
            )

    def get_zones(
        self,
        camera_id
    ):

        return self.zones.get(
            str(camera_id),
            []
        )

    def set_zones(
        self,
        camera_id,
        zones
    ):

        self.zones[
            str(camera_id)
        ] = zones

        self.save()

    def add_zone(
        self,
        camera_id,
        points
    ):

        camera_key = str(camera_id)

        if camera_key not in self.zones:

            self.zones[camera_key] = []

        zone_id = len(
            self.zones[camera_key]
        ) + 1

        zone = {
            "id": zone_id,
            "points": [
                [
                    int(point[0]),
                    int(point[1])
                ]
                for point in points
            ]
        }

        self.zones[camera_key].append(
            zone
        )

        self.save()

        return zone

    def remove_zone(
        self,
        camera_id,
        zone_id
    ):

        camera_key = str(camera_id)

        zones = self.zones.get(
            camera_key,
            []
        )

        self.zones[camera_key] = [
            zone
            for zone in zones
            if zone["id"] != zone_id
        ]

        self.save()

    def clear_zones(
        self,
        camera_id
    ):

        self.zones[
            str(camera_id)
        ] = []

        self.save()

    def get_occupancy(
        self,
        camera_id,
        detections
    ):

        zones = self.get_zones(
            camera_id
        )

        results = []

        for zone in zones:

            polygon = np.array(
                zone["points"],
                dtype=np.int32
            )

            occupied = False
            vehicle = None
            best_overlap = 0.0

            for detection in detections:

                bbox = detection.get(
                    "bbox"
                )

                if not bbox:
                    continue

                x1, y1, x2, y2 = bbox

                vehicle_polygon = np.array(
                    [
                        [x1, y1],
                        [x2, y1],
                        [x2, y2],
                        [x1, y2]
                    ],
                    dtype=np.int32
                )

                zone_area = abs(
                    cv2.contourArea(
                        polygon
                    )
                )

                if zone_area <= 0:
                    continue

                intersection = cv2.intersectConvexConvex(
                    polygon.astype(np.float32),
                    vehicle_polygon.astype(np.float32)
                )

                intersection_area = float(
                    intersection[0]
                )

                overlap = (
                    intersection_area
                    / zone_area
                )

                if overlap > best_overlap:

                    best_overlap = overlap
                    vehicle = detection

            if best_overlap >= 0.35:

                occupied = True

            results.append(
                {
                    "id": zone["id"],
                    "points": zone["points"],
                    "occupied": occupied,
                    "vehicle": vehicle,
                    "overlap": round(
                        best_overlap,
                        3
                    )
                }
            )

        return results

    def get_statistics(
        self,
        camera_id,
        detections
    ):

        occupancy = self.get_occupancy(
            camera_id,
            detections
        )

        total = len(occupancy)

        occupied = sum(
            1
            for zone in occupancy
            if zone["occupied"]
        )

        available = (
            total - occupied
        )

        return {
            "total_spaces": total,
            "occupied_spaces": occupied,
            "available_spaces": available,
            "occupancy": occupancy
        }

    def draw(
        self,
        frame,
        camera_id,
        detections
    ):

        statistics = self.get_statistics(
            camera_id,
            detections
        )

        for zone in statistics[
            "occupancy"
        ]:

            points = np.array(
                zone["points"],
                dtype=np.int32
            )

            if zone["occupied"]:

                color = (
                    0,
                    0,
                    255
                )

                label = (
                    f"P{zone['id']} "
                    f"OCCUPIED"
                )

            else:

                color = (
                    0,
                    255,
                    0
                )

                label = (
                    f"P{zone['id']} "
                    f"FREE"
                )

            cv2.polylines(
                frame,
                [points],
                True,
                color,
                2
            )

            x, y = points[0]

            cv2.putText(
                frame,
                label,
                (int(x), int(y) - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
                cv2.LINE_AA
            )

        return frame, statistics