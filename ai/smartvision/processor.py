class SmartVisionProcessor:

    def __init__(self):

        self.enabled = False

        self.name = "SmartVision AI"

    # --------------------------------------------------

    def start(self):

        self.enabled = True

        print(
            f"[AI] {self.name} started"
        )

    # --------------------------------------------------

    def stop(self):

        self.enabled = False

        print(
            f"[AI] {self.name} stopped"
        )

    # --------------------------------------------------

    def process(self, frame):

        if not self.enabled:

            return frame, []

        return frame, []

    # --------------------------------------------------

    def get_status(self):

        return {
            "name": self.name,
            "enabled": self.enabled
        }