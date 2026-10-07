import cv2
import threading
import time
import numpy as np


class Camera:

    def __init__(
        self,
        config,
        frame_processor=None
    ):

        self.id = int(config["id"])
        self.name = config["name"]
        self.camera_type = config.get(
            "type",
            "usb"
        )
        self.source = config["source"]
        self.enabled = config.get(
            "enabled",
            True
        )

        self.frame_processor = frame_processor

        self.capture = None

        self.frame = None
        self.lock = threading.Lock()

        self.connected = False
        self.status = "NOT AVAILABLE"

        self.running = False
        self.thread = None

        self.last_attempt = 0
        self.reconnect_interval = 3

        self.fps = 0
        self.frame_count = 0
        self.fps_start = time.time()

    def set_frame_processor(
        self,
        frame_processor
    ):

        self.frame_processor = frame_processor

    def get_source(self):

        if self.camera_type.lower() == "usb":

            try:
                return int(self.source)

            except (
                ValueError,
                TypeError
            ):

                return self.source

        return self.source

    def connect(self):

        if not self.enabled:

            self.connected = False
            self.status = "NOT AVAILABLE"

            return False

        self.status = "CONNECTING"

        try:

            if self.capture is not None:

                self.capture.release()
                self.capture = None

            self.capture = cv2.VideoCapture(
                self.get_source()
            )

            self.capture.set(
                cv2.CAP_PROP_BUFFERSIZE,
                1
            )

            if self.capture.isOpened():

                success, frame = (
                    self.capture.read()
                )

                if (
                    success
                    and frame is not None
                ):

                    processed_frame = (
                        self.process_frame(frame)
                    )

                    with self.lock:

                        self.frame = (
                            processed_frame.copy()
                        )

                    self.connected = True
                    self.status = "LIVE"

                    self.frame_count = 0
                    self.fps_start = time.time()

                    print(
                        f"[Camera {self.id}] "
                        f"Connected: {self.name}"
                    )

                    return True

            if self.capture is not None:

                self.capture.release()
                self.capture = None

        except Exception as error:

            print(
                f"[Camera {self.id}] "
                f"Connection error: {error}"
            )

        self.connected = False
        self.status = "NOT AVAILABLE"

        return False

    def process_frame(self, frame):

        if self.frame_processor is None:

            return frame

        try:

            processed_frame, _ = (
                self.frame_processor(
                    self.id,
                    frame
                )
            )

            if processed_frame is not None:

                return processed_frame

        except Exception as error:

            print(
                f"[Camera {self.id}] "
                f"AI processing error: {error}"
            )

        return frame

    def start(self):

        if self.running:

            return

        self.running = True

        self.thread = threading.Thread(
            target=self.capture_loop,
            daemon=True
        )

        self.thread.start()

    def capture_loop(self):

        while self.running:

            if not self.enabled:

                self.connected = False
                self.status = "NOT AVAILABLE"

                time.sleep(1)

                continue

            if (
                self.capture is None
                or not self.connected
            ):

                current_time = time.time()

                if (
                    current_time
                    - self.last_attempt
                    >= self.reconnect_interval
                ):

                    self.last_attempt = (
                        current_time
                    )

                    self.connect()

                time.sleep(0.1)

                continue

            try:

                success, frame = (
                    self.capture.read()
                )

                if (
                    not success
                    or frame is None
                ):

                    print(
                        f"[Camera {self.id}] "
                        f"Connection lost: "
                        f"{self.name}"
                    )

                    self.connected = False
                    self.status = "NOT AVAILABLE"

                    if self.capture is not None:

                        self.capture.release()
                        self.capture = None

                    time.sleep(0.1)

                    continue

                frame = self.process_frame(
                    frame
                )

                with self.lock:

                    self.frame = frame.copy()

                self.status = "LIVE"

                self.update_fps()

            except Exception as error:

                print(
                    f"[Camera {self.id}] "
                    f"Read error: {error}"
                )

                self.connected = False
                self.status = "NOT AVAILABLE"

                if self.capture is not None:

                    self.capture.release()
                    self.capture = None

                time.sleep(0.5)

    def update_fps(self):

        self.frame_count += 1

        elapsed = (
            time.time()
            - self.fps_start
        )

        if elapsed >= 1:

            self.fps = (
                self.frame_count
                / elapsed
            )

            self.frame_count = 0

            self.fps_start = time.time()

    def get_frame(self):

        with self.lock:

            if self.frame is None:

                return None

            return self.frame.copy()

    def get_status(self):

        if not self.enabled:

            return "NOT AVAILABLE"

        if self.connected:

            return "LIVE"

        if self.status == "CONNECTING":

            return "CONNECTING"

        return "NOT AVAILABLE"

    def get_fps(self):

        return round(
            self.fps,
            1
        )

    def create_placeholder(self):

        width = 640
        height = 360

        frame = np.zeros(
            (
                height,
                width,
                3
            ),
            dtype=np.uint8
        )

        cv2.putText(
            frame,
            self.name,
            (35, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        cv2.putText(
            frame,
            self.get_status(),
            (35, 190),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        return frame

    def get_stream_frame(self):

        frame = self.get_frame()

        if frame is None:

            return self.create_placeholder()

        height, width = frame.shape[:2]

        cv2.putText(
            frame,
            self.name,
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        cv2.putText(
            frame,
            f"{self.get_fps()} FPS",
            (15, height - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        return frame

    def stop(self):

        self.running = False

        if self.thread is not None:

            self.thread.join(
                timeout=2
            )

        if self.capture is not None:

            self.capture.release()

        self.capture = None

        self.connected = False
        self.status = "NOT AVAILABLE"