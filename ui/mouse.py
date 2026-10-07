import cv2


class ParkingEditor:

    def __init__(self, parking_manager):

        self.parking_manager = parking_manager

        self.camera_id = None

        self.active = False

        self.points = []

        self.mouse_position = (0, 0)

    def set_camera(self, camera_id):

        self.camera_id = camera_id

        self.cancel()

    def start(self):

        self.active = True
        self.points = []

        print(
            f"[Parking] Drawing mode enabled "
            f"for Camera {self.camera_id}"
        )

    def cancel(self):

        self.active = False
        self.points = []

    def mouse_callback(
        self,
        event,
        x,
        y,
        flags,
        param
    ):

        self.mouse_position = (x, y)

        if not self.active:
            return

        if event != cv2.EVENT_LBUTTONDOWN:
            return

        self.points.append(
            (x, y)
        )

        print(
            f"[Parking] Point "
            f"{len(self.points)}/4: "
            f"({x}, {y})"
        )

        if len(self.points) == 4:

            self.create_zone()

    def create_zone(self):

        if self.camera_id is None:
            return

        if len(self.points) != 4:
            return

        zone = self.parking_manager.add_zone(
            self.camera_id,
            self.points
        )

        print(
            f"[Parking] Created "
            f"Parking {zone['id']} "
            f"on Camera {self.camera_id}"
        )

        self.points = []

        self.active = False

    def reset_camera(self):

        if self.camera_id is None:
            return

        self.parking_manager.clear_zones(
            self.camera_id
        )

        self.points = []

        print(
            f"[Parking] Reset Camera "
            f"{self.camera_id}"
        )

    def draw(
        self,
        frame,
        camera_id
    ):

        self.set_camera_if_needed(
            camera_id
        )

        zones = (
            self.parking_manager.get_zones(
                camera_id
            )
        )

        # Draw saved parking zones
        for zone in zones:

            points = zone["points"]

            color = (
                255,
                0,
                0
            )

            for index in range(
                len(points)
            ):

                start = points[index]

                end = points[
                    (index + 1)
                    % len(points)
                ]

                cv2.line(
                    frame,
                    tuple(start),
                    tuple(end),
                    color,
                    2
                )

            x, y = points[0]

            cv2.putText(
                frame,
                f"P{zone['id']}",
                (
                    int(x),
                    int(y) - 8
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
                cv2.LINE_AA
            )

        # Draw currently selected points
        if self.active:

            for point in self.points:

                cv2.circle(
                    frame,
                    point,
                    5,
                    (0, 255, 255),
                    -1
                )

            for index in range(
                len(self.points) - 1
            ):

                cv2.line(
                    frame,
                    self.points[index],
                    self.points[index + 1],
                    (0, 255, 255),
                    2
                )

            if len(self.points) > 0:

                cv2.line(
                    frame,
                    self.points[-1],
                    self.mouse_position,
                    (0, 255, 255),
                    2
                )

            self.draw_instruction(
                frame
            )

        return frame

    def set_camera_if_needed(
        self,
        camera_id
    ):

        if self.camera_id != camera_id:

            self.camera_id = camera_id

            self.cancel()

    def draw_instruction(
        self,
        frame
    ):

        overlay = frame.copy()

        height, width = frame.shape[:2]

        box_width = 330
        box_height = 80

        x = 15
        y = height - box_height - 15

        cv2.rectangle(
            overlay,
            (x, y),
            (
                x + box_width,
                y + box_height
            ),
            (20, 20, 20),
            -1
        )

        cv2.addWeighted(
            overlay,
            0.75,
            frame,
            0.25,
            0,
            frame
        )

        cv2.putText(
            frame,
            "PARKING EDIT MODE",
            (x + 15, y + 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2,
            cv2.LINE_AA
        )

        cv2.putText(
            frame,
            f"Click corners: "
            f"{len(self.points)}/4",
            (x + 15, y + 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        cv2.putText(
            frame,
            "ESC: Cancel",
            (x + 190, y + 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )