import time

import cv2
import numpy as np

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse


def create_dashboard(camera_manager, ai_manager=None):

    app = FastAPI(
        title="MulCamFeed",
        version="1.0.0"
    )
    app.state.ai_manager = ai_manager

    # --------------------------------------------------
    # Dashboard
    # --------------------------------------------------

    @app.get(
        "/",
        response_class=HTMLResponse
    )
    async def dashboard():

        html = """
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>MulCamFeed</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    background: #080a0d;

    color: white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

}

.header {

    height: 72px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 0 28px;

    background: rgba(18, 21, 26, 0.95);

    border-bottom:
        1px solid
        rgba(255, 255, 255, 0.08);

}

.logo {

    font-size: 23px;

    font-weight: 700;

    letter-spacing: 0.2px;

}

.subtitle {

    margin-top: 3px;

    color: #89929d;

    font-size: 13px;

}

.camera-count {

    color: #aeb6c0;

    font-size: 13px;

}

.dashboard {

    padding: 24px;

}

.grid {

    display: grid;

    grid-template-columns:
        repeat(2, minmax(0, 1fr));

    gap: 20px;

}

.camera-card {

    overflow: hidden;

    background: #11151a;

    border:
        1px solid
        rgba(255, 255, 255, 0.08);

    border-radius: 14px;

}

.camera-header {

    height: 50px;

    padding: 0 16px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    border-bottom:
        1px solid
        rgba(255, 255, 255, 0.07);

}

.camera-name {

    font-size: 14px;

    font-weight: 600;

}

.status {

    display: flex;

    align-items: center;

    gap: 7px;

    font-size: 11px;

    font-weight: 600;

    letter-spacing: 0.3px;

}

.status-dot {

    width: 8px;

    height: 8px;

    border-radius: 50%;

    background: #666;

}

.status-live
.status-dot {

    background: #35d07f;

    box-shadow:
        0 0 8px
        rgba(53, 208, 127, 0.7);

}

.status-connecting
.status-dot {

    background: #f0b429;

}

.status-error
.status-dot {

    background: #ff4d4d;

}

.status-unavailable
.status-dot {

    background: #666;

}

.video {

    width: 100%;

    aspect-ratio: 16 / 9;

    background: #030405;

}

.video img {

    display: block;

    width: 100%;

    height: 100%;

    object-fit: cover;

}

.controls {

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 14px;

    margin-top: 24px;

}

button {

    border:
        1px solid
        rgba(255, 255, 255, 0.12);

    background: #171c22;

    color: white;

    padding:
        10px
        20px;

    border-radius: 8px;

    cursor: pointer;

    font-size: 13px;

}

button:hover:not(:disabled) {

    background: #222932;

}

button:disabled {

    opacity: 0.35;

    cursor: default;

}

.page {

    min-width: 100px;

    text-align: center;

    color: #969faa;

    font-size: 13px;

}

@media (max-width: 800px) {

    .grid {

        grid-template-columns: 1fr;

    }

    .dashboard {

        padding: 14px;

    }

    .header {

        padding: 0 16px;

    }

}

</style>

</head>


<body>


<header class="header">


    <div>

        <div class="logo">
            MulCamFeed
        </div>

        <div class="subtitle">
            Multi-Camera Monitoring Dashboard
        </div>

    </div>


    <div
        class="camera-count"
        id="cameraCount"
    >
        Loading...
    </div>


</header>


<main class="dashboard">


    <section
        class="grid"
        id="cameraGrid"
    >
    </section>


    <div class="controls">


        <button
            id="previousButton"
            onclick="previousPage()"
        >
            ← Previous
        </button>


        <div
            class="page"
            id="pageNumber"
        >
            Page 1
        </div>


        <button
            id="nextButton"
            onclick="nextPage()"
        >
            Next →
        </button>


    </div>


</main>


<script>


let cameras = [];

let currentPage = 0;

const camerasPerPage = 4;


// --------------------------------------------------
// Load camera information
// --------------------------------------------------

async function loadCameras() {

    try {

        const response =
            await fetch("/api/cameras");

        const data =
            await response.json();

        cameras =
            data.cameras;

        document.getElementById(
            "cameraCount"
        ).textContent =
            `${data.active} / ${data.total} Active`;

        renderPage();

    }

    catch (error) {

        console.error(
            "Camera API error:",
            error
        );

    }

}


// --------------------------------------------------
// Status CSS
// --------------------------------------------------

function getStatusClass(status) {

    if (status === "LIVE") {

        return "status-live";

    }

    if (status === "CONNECTING") {

        return "status-connecting";

    }

    if (status === "ERROR") {

        return "status-error";

    }

    return "status-unavailable";

}


// --------------------------------------------------
// Render camera page
// --------------------------------------------------

function renderPage() {

    const grid =
        document.getElementById(
            "cameraGrid"
        );

    grid.innerHTML = "";


    const totalPages = Math.max(
        1,
        Math.ceil(
            cameras.length /
            camerasPerPage
        )
    );


    if (
        currentPage >=
        totalPages
    ) {

        currentPage =
            totalPages - 1;

    }


    const start =
        currentPage *
        camerasPerPage;


    const pageCameras =
        cameras.slice(
            start,
            start + camerasPerPage
        );


    // ----------------------------------------------
    // Camera cards
    // ----------------------------------------------

    for (
        const camera
        of pageCameras
    ) {

        const card =
            document.createElement(
                "div"
            );

        card.className =
            "camera-card";


        card.innerHTML = `

            <div class="camera-header">

                <div class="camera-name">
                    ${camera.name}
                </div>

                <div
                    class="
                        status
                        ${getStatusClass(
                            camera.status
                        )}
                    "
                >

                    <span
                        class="status-dot"
                    ></span>

                    <span>
                        ${camera.status}
                    </span>

                </div>

            </div>


            <div class="video">

                <img
                    src="/stream/${camera.id}"
                    alt="${camera.name}"
                >

            </div>

        `;


        grid.appendChild(
            card
        );

    }


    // ----------------------------------------------
    // Empty slots
    // ----------------------------------------------

    while (
        grid.children.length <
        camerasPerPage
    ) {

        const card =
            document.createElement(
                "div"
            );

        card.className =
            "camera-card";


        card.innerHTML = `

            <div class="camera-header">

                <div class="camera-name">
                    Camera Slot
                </div>

                <div
                    class="
                        status
                        status-unavailable
                    "
                >

                    <span
                        class="status-dot"
                    ></span>

                    <span>
                        NOT AVAILABLE
                    </span>

                </div>

            </div>


            <div class="video">

                <img
                    src="/placeholder"
                    alt="Not available"
                >

            </div>

        `;


        grid.appendChild(
            card
        );

    }


    // ----------------------------------------------
    // Page controls
    // ----------------------------------------------

    document.getElementById(
        "pageNumber"
    ).textContent =
        `Page ${
            currentPage + 1
        } / ${totalPages}`;


    document.getElementById(
        "cameraCount"
    ).textContent =
        `${cameras.length} Camera Slots`;


    document.getElementById(
        "previousButton"
    ).disabled =
        currentPage === 0;


    document.getElementById(
        "nextButton"
    ).disabled =
        currentPage >=
        totalPages - 1;

}


// --------------------------------------------------
// Next page
// --------------------------------------------------

function nextPage() {

    const totalPages =
        Math.ceil(
            cameras.length /
            camerasPerPage
        );


    if (
        currentPage <
        totalPages - 1
    ) {

        currentPage++;

        renderPage();

    }

}


// --------------------------------------------------
// Previous page
// --------------------------------------------------

function previousPage() {

    if (
        currentPage > 0
    ) {

        currentPage--;

        renderPage();

    }

}


// --------------------------------------------------
// Refresh camera status
// --------------------------------------------------

setInterval(
    loadCameras,
    3000
);

document.addEventListener(
    "keydown",
    function(event) {

        if (event.key === "ArrowRight") {

            nextPage();

        }

        if (event.key === "ArrowLeft") {

            previousPage();

        }

    }
);


// Initial load

loadCameras();


</script>


</body>

</html>
"""

        return HTMLResponse(
            content=html
        )


    # --------------------------------------------------
    # Camera API
    # --------------------------------------------------

    @app.get("/api/cameras")
    async def get_cameras():

        return JSONResponse(
        {
            "total": camera_manager.get_total_count(),
            "active": camera_manager.get_active_count(),
            "cameras": camera_manager.get_camera_info()
        }
    )


    # --------------------------------------------------
    # Placeholder image
    # --------------------------------------------------

    @app.get("/placeholder")
    async def placeholder():

        frame = np.zeros(
            (
                360,
                640,
                3
            ),
            dtype=np.uint8
        )


        cv2.putText(
            frame,
            "NOT AVAILABLE",
            (150, 190),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (255, 255, 255),
            3,
            cv2.LINE_AA
        )


        success, encoded = cv2.imencode(
            ".jpg",
            frame
        )


        if not success:

            return JSONResponse(
                {
                    "error":
                    "Unable to create image"
                },
                status_code=500
            )


        return StreamingResponse(
            iter(
                [encoded.tobytes()]
            ),
            media_type="image/jpeg"
        )


    # --------------------------------------------------
    # Camera stream
    # --------------------------------------------------

    @app.get(
        "/stream/{camera_id}"
    )
    async def camera_stream(
        camera_id: int
    ):

        camera = camera_manager.get_camera(
            camera_id
        )


        if camera is None:

            return JSONResponse(
                {
                    "error":
                    "Camera not found"
                },
                status_code=404
            )


        def generate():

            while True:

                frame = camera.get_stream_frame()


                success, encoded = cv2.imencode(
                    ".jpg",
                    frame,
                    [
                        cv2.IMWRITE_JPEG_QUALITY,
                        80
                    ]
                )


                if success:

                    yield (
                        b"--frame\r\n"
                        b"Content-Type: "
                        b"image/jpeg\r\n\r\n"
                        +
                        encoded.tobytes()
                        +
                        b"\r\n"
                    )


                time.sleep(
                    0.04
                )


        return StreamingResponse(
            generate(),
            media_type=
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )


    return app