import cv2


def test_camera(index):

    print(f"Testing camera index {index}...")

    camera = cv2.VideoCapture(index)

    if not camera.isOpened():

        print(f"Camera {index}: NOT AVAILABLE")
        camera.release()
        return False

    success, frame = camera.read()

    if success and frame is not None:

        height, width = frame.shape[:2]

        print(
            f"Camera {index}: AVAILABLE "
            f"({width}x{height})"
        )

        camera.release()

        return True

    print(
        f"Camera {index}: CONNECTED "
        f"BUT NO FRAME"
    )

    camera.release()

    return False


def main():

    print("=" * 50)
    print("MulCamFeed USB Camera Scanner")
    print("=" * 50)

    available = []

    for index in range(10):

        if test_camera(index):

            available.append(index)

    print()
    print("=" * 50)
    print("Available USB camera indexes:")

    if available:

        for index in available:

            print(f"  Camera index {index}")

    else:

        print("  No USB cameras detected.")

    print("=" * 50)


if __name__ == "__main__":

    main()