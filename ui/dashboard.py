import asyncio
import json
from pathlib import Path

import cv2
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel


class ParkingZoneRequest(BaseModel):
    points: list[list[int]]


def create_dashboard(
    camera_manager,
    ai_manager,
    parking_manager
):

    app = FastAPI(
        title="MulCamFeed",
        version="1.0"
    )

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():

        return HTMLResponse(
            content=HTML_PAGE
        )

    @app.get("/api/cameras")
    async def cameras():

        return {
            "cameras": camera_manager.get_camera_info(),
            "total": camera_manager.get_total_count(),
            "active": camera_manager.get_active_count()
        }

    @app.get("/api/parking/{camera_id}")
    async def get_parking(camera_id: int):

        return {
            "camera_id": camera_id,
            "zones": parking_manager.get_zones(camera_id)
        }

    @app.post("/api/parking/{camera_id}")
    async def add_parking(
        camera_id: int,
        data: ParkingZoneRequest
    ):

        points = data.points

        if len(points) < 4:
            raise HTTPException(
                status_code=400,
                detail="A parking zone requires 4 points."
            )

        points = points[:4]

        zone = parking_manager.add_zone(
            camera_id,
            points
        )

        return {
            "success": True,
            "zone": zone
        }

    @app.delete("/api/parking/{camera_id}")
    async def clear_parking(camera_id: int):

        parking_manager.clear_zones(
            camera_id
        )

        return {
            "success": True,
            "camera_id": camera_id
        }

    @app.get("/api/parking/statistics")
    async def parking_statistics():

        return ai_manager.get_global_parking_statistics()

    @app.get("/placeholder")
    async def placeholder():

        camera = None

        frame = create_placeholder(
            "NOT AVAILABLE"
        )

        success, encoded = cv2.imencode(
            ".jpg",
            frame
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Could not create placeholder."
            )

        return Response(
            content=encoded.tobytes(),
            media_type="image/jpeg"
        )

    @app.get("/stream/{camera_id}")
    async def stream(camera_id: int):

        camera = camera_manager.get_camera(
            camera_id
        )

        if camera is None:
            raise HTTPException(
                status_code=404,
                detail="Camera not found."
            )

        async def generate():

            while True:

                frame = camera.get_stream_frame()

                if frame is None:
                    frame = create_placeholder(
                        camera.name
                    )

                success, encoded = cv2.imencode(
                    ".jpg",
                    frame,
                    [
                        cv2.IMWRITE_JPEG_QUALITY,
                        75
                    ]
                )

                if success:

                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n"
                        + encoded.tobytes()
                        + b"\r\n"
                    )

                await asyncio.sleep(
                    0.04
                )

        return StreamingResponse(
            generate(),
            media_type=(
                "multipart/x-mixed-replace; "
                "boundary=frame"
            )
        )

    return app


def create_placeholder(text):

    width = 640
    height = 360

    frame = cv2.UMat(
        height,
        width,
        cv2.CV_8UC3
    )

    image = frame.get()

    image[:] = 25

    cv2.putText(
        image,
        text,
        (35, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (220, 220, 220),
        2,
        cv2.LINE_AA
    )

    return image


HTML_PAGE = """
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
    background: #101114;
    color: #ffffff;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

header {
    height: 70px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    background: #17191e;
    border-bottom: 1px solid #292c33;
}

.logo {
    font-size: 22px;
    font-weight: 700;
}

.header-right {
    display: flex;
    gap: 24px;
    align-items: center;
}

.stat {
    color: #b8bcc5;
    font-size: 14px;
}

.stat strong {
    color: #ffffff;
    margin-left: 5px;
}

main {
    padding: 20px;
}

.toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
}

.page-title {
    font-size: 18px;
    font-weight: 600;
}

.page-controls {
    display: flex;
    gap: 8px;
}

button {
    border: 1px solid #363a43;
    background: #20232a;
    color: white;
    padding: 9px 14px;
    border-radius: 7px;
    cursor: pointer;
    font-size: 13px;
}

button:hover {
    background: #2a2e37;
}

button.primary {
    background: #2563eb;
    border-color: #2563eb;
}

button.danger {
    background: #8f1d1d;
    border-color: #8f1d1d;
}

button:disabled {
    opacity: 0.45;
    cursor: not-allowed;
}

.grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
}

.card {
    background: #181a20;
    border: 1px solid #292c34;
    border-radius: 10px;
    overflow: hidden;
}

.card-header {
    height: 46px;
    padding: 0 13px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #292c34;
}

.camera-name {
    font-size: 14px;
    font-weight: 600;
}

.status {
    font-size: 11px;
    padding: 4px 8px;
    border-radius: 20px;
    background: #292c34;
}

.status.live {
    color: #62e58a;
}

.status.offline {
    color: #ff6b6b;
}

.video-wrapper {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #08090b;
    overflow: hidden;
}

.video {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
}

.editor {
    position: absolute;
    inset: 0;
    display: none;
}

.editor.active {
    display: block;
}

.editor canvas {
    width: 100%;
    height: 100%;
    display: block;
    cursor: crosshair;
}

.card-footer {
    min-height: 48px;
    padding: 8px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
}

.controls {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}

.camera-info {
    color: #858a95;
    font-size: 11px;
}

.empty {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 250px;
    color: #777d87;
    border: 1px dashed #30343c;
    border-radius: 10px;
}

.footer-stats {
    margin-top: 18px;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.big-stat {
    background: #181a20;
    border: 1px solid #292c34;
    border-radius: 8px;
    padding: 12px 18px;
    min-width: 150px;
}

.big-stat-label {
    color: #858a95;
    font-size: 11px;
}

.big-stat-value {
    font-size: 22px;
    font-weight: 700;
    margin-top: 4px;
}

@media (max-width: 900px) {

    .grid {
        grid-template-columns: 1fr;
    }

    .header-right {
        gap: 10px;
    }

}

</style>

</head>


<body>

<header>

    <div class="logo">
        MulCamFeed
    </div>

    <div class="header-right">

        <div class="stat">
            Cameras:
            <strong id="cameraCount">0 / 0</strong>
        </div>

        <div class="stat">
            Vehicles:
            <strong id="vehicleCount">0</strong>
        </div>

        <div class="stat">
            Parking:
            <strong id="parkingCount">0 / 0</strong>
        </div>

    </div>

</header>


<main>

    <div class="toolbar">

        <div class="page-title">
            Camera Dashboard
        </div>

        <div class="page-controls">

            <button
                id="previousButton"
                onclick="previousPage()"
            >
                Previous
            </button>

            <button
                id="nextButton"
                onclick="nextPage()"
            >
                Next
            </button>

        </div>

    </div>


    <div
        id="cameraGrid"
        class="grid"
    ></div>


    <div class="footer-stats">

        <div class="big-stat">

            <div class="big-stat-label">
                Total Parking Spaces
            </div>

            <div
                class="big-stat-value"
                id="totalSpaces"
            >
                0
            </div>

        </div>


        <div class="big-stat">

            <div class="big-stat-label">
                Occupied
            </div>

            <div
                class="big-stat-value"
                id="occupiedSpaces"
            >
                0
            </div>

        </div>


        <div class="big-stat">

            <div class="big-stat-label">
                Available
            </div>

            <div
                class="big-stat-value"
                id="availableSpaces"
            >
                0
            </div>

        </div>

    </div>

</main>


<script>

let cameras = [];

let currentPage = 0;

const camerasPerPage = 4;

const editors = {};


async function loadCameras() {

    try {

        const response = await fetch(
            "/api/cameras"
        );

        const data = await response.json();

        cameras = data.cameras || [];

        document.getElementById(
            "cameraCount"
        ).textContent =
            `${data.active} / ${data.total}`;

        renderPage();

    } catch (error) {

        console.error(
            "Camera API error:",
            error
        );

    }

}


function renderPage() {

    const grid =
        document.getElementById(
            "cameraGrid"
        );

    grid.innerHTML = "";

    const start =
        currentPage * camerasPerPage;

    const pageCameras =
        cameras.slice(
            start,
            start + camerasPerPage
        );

    if (pageCameras.length === 0) {

        grid.innerHTML = `
            <div class="empty">
                No cameras configured
            </div>
        `;

        updatePagination();

        return;

    }


    for (
        let index = 0;
        index < camerasPerPage;
        index++
    ) {

        const camera =
            pageCameras[index];

        if (camera) {

            grid.appendChild(
                createCameraCard(camera)
            );

        } else {

            const empty =
                document.createElement(
                    "div"
                );

            empty.className = "empty";

            empty.textContent =
                "NOT AVAILABLE";

            grid.appendChild(empty);

        }

    }

    updatePagination();

}


function createCameraCard(camera) {

    const card =
        document.createElement("div");

    card.className = "card";

    const live =
        camera.status === "LIVE";

    const statusClass =
        live
            ? "live"
            : "offline";

    const streamUrl =
        `/stream/${camera.id}?t=${Date.now()}`;

    card.innerHTML = `

        <div class="card-header">

            <div class="camera-name">
                ${escapeHtml(camera.name)}
            </div>

            <div class="status ${statusClass}">
                ${escapeHtml(camera.status)}
            </div>

        </div>


        <div
            class="video-wrapper"
            id="wrapper-${camera.id}"
        >

            <img
                class="video"
                src="${streamUrl}"
                alt="${escapeHtml(camera.name)}"
                onerror="this.src='/placeholder'"
            >

            <div
                class="editor"
                id="editor-${camera.id}"
            >

                <canvas
                    id="canvas-${camera.id}"
                ></canvas>

            </div>

        </div>


        <div class="card-footer">

            <div class="controls">

                <button
                    onclick="startDrawing(${camera.id})"
                >
                    Draw Parking
                </button>

                <button
                    id="finish-${camera.id}"
                    class="primary"
                    onclick="finishDrawing(${camera.id})"
                    disabled
                >
                    Finish
                </button>

                <button
                    onclick="cancelDrawing(${camera.id})"
                    disabled
                    id="cancel-${camera.id}"
                >
                    Cancel
                </button>

                <button
                    class="danger"
                    onclick="clearParking(${camera.id})"
                >
                    Clear
                </button>

            </div>

            <div class="camera-info">

                AI:
                ${escapeHtml(camera.ai_mode)}

                <br>

                ${camera.fps} FPS

            </div>

        </div>
    `;

    setTimeout(
        () => setupEditor(camera.id),
        0
    );

    return card;

}


function setupEditor(cameraId) {

    const canvas =
        document.getElementById(
            `canvas-${cameraId}`
        );

    if (!canvas) {
        return;
    }

    const wrapper =
        document.getElementById(
            `wrapper-${cameraId}`
        );

    editors[cameraId] = {
        canvas: canvas,
        wrapper: wrapper,
        points: [],
        drawing: false
    };

    canvas.addEventListener(
        "click",
        event => handleCanvasClick(
            cameraId,
            event
        )
    );

}


function startDrawing(cameraId) {

    const editor =
        editors[cameraId];

    if (!editor) {
        return;
    }

    editor.points = [];

    editor.drawing = true;

    const element =
        document.getElementById(
            `editor-${cameraId}`
        );

    element.classList.add("active");

    document.getElementById(
        `finish-${cameraId}`
    ).disabled = false;

    document.getElementById(
        `cancel-${cameraId}`
    ).disabled = false;

    resizeCanvas(
        cameraId
    );

    redrawEditor(
        cameraId
    );

}


function finishDrawing(cameraId) {

    const editor =
        editors[cameraId];

    if (!editor) {
        return;
    }

    editor.drawing = false;

    document.getElementById(
        `finish-${cameraId}`
    ).disabled = true;

    document.getElementById(
        `cancel-${cameraId}`
    ).disabled = true;

    const element =
        document.getElementById(
            `editor-${cameraId}`
        );

    element.classList.remove("active");

    editor.points = [];

}


function cancelDrawing(cameraId) {

    const editor =
        editors[cameraId];

    if (!editor) {
        return;
    }

    editor.points = [];

    editor.drawing = false;

    redrawEditor(
        cameraId
    );

    document.getElementById(
        `finish-${cameraId}`
    ).disabled = true;

    document.getElementById(
        `cancel-${cameraId}`
    ).disabled = true;

    document.getElementById(
        `editor-${cameraId}`
    ).classList.remove("active");

}


function handleCanvasClick(
    cameraId,
    event
) {

    const editor =
        editors[cameraId];

    if (!editor || !editor.drawing) {
        return;
    }

    const rect =
        editor.canvas.getBoundingClientRect();

    const x =
        Math.round(
            (event.clientX - rect.left)
            * editor.canvas.width
            / rect.width
        );

    const y =
        Math.round(
            (event.clientY - rect.top)
            * editor.canvas.height
            / rect.height
        );

    editor.points.push([
        x,
        y
    ]);

    redrawEditor(
        cameraId
    );

    if (editor.points.length === 4) {

        saveCurrentZone(
            cameraId
        );

    }

}


async function saveCurrentZone(cameraId) {

    const editor =
        editors[cameraId];

    if (
        !editor ||
        editor.points.length !== 4
    ) {
        return;
    }

    const points =
        editor.points
            .slice(0, 4)
            .map(point => [
                Math.round(point[0]),
                Math.round(point[1])
            ]);

    try {

        const response =
            await fetch(
                `/api/parking/${cameraId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        points: points
                    })
                }
            );

        if (!response.ok) {

            console.error(
                "Could not save parking zone"
            );

            return;

        }

        editor.points = [];

        redrawEditor(
            cameraId
        );

        updateParkingStats();

    } catch (error) {

        console.error(
            "Parking save error:",
            error
        );

    }

}


function resizeCanvas(cameraId) {

    const editor =
        editors[cameraId];

    if (!editor) {
        return;
    }

    const image =
        document.querySelector(
            `#wrapper-${cameraId} img`
        );

    if (!image) {
        return;
    }

    const width =
        image.naturalWidth || 640;

    const height =
        image.naturalHeight || 360;

    editor.canvas.width =
        width;

    editor.canvas.height =
        height;

    editor.canvas.style.width =
        "100%";

    editor.canvas.style.height =
        "100%";

}


function redrawEditor(cameraId) {

    const editor =
        editors[cameraId];

    if (!editor) {
        return;
    }

    resizeCanvas(
        cameraId
    );

    const ctx =
        editor.canvas.getContext(
            "2d"
        );

    ctx.clearRect(
        0,
        0,
        editor.canvas.width,
        editor.canvas.height
    );

    const points =
        editor.points;

    if (points.length === 0) {
        return;
    }


    ctx.lineWidth = 3;

    ctx.strokeStyle =
        "#00ff66";

    ctx.fillStyle =
        "rgba(0,255,100,0.18)";

    ctx.beginPath();

    ctx.moveTo(
        points[0][0],
        points[0][1]
    );

    for (
        let i = 1;
        i < points.length;
        i++
    ) {

        ctx.lineTo(
            points[i][0],
            points[i][1]
        );

    }

    if (points.length === 4) {

        ctx.lineTo(
            points[0][0],
            points[0][1]
        );

        ctx.fill();

    }

    ctx.stroke();


    for (
        let i = 0;
        i < points.length;
        i++
    ) {

        ctx.beginPath();

        ctx.arc(
            points[i][0],
            points[i][1],
            7,
            0,
            Math.PI * 2
        );

        ctx.fillStyle =
            "#ffffff";

        ctx.fill();

        ctx.strokeStyle =
            "#00ff66";

        ctx.stroke();

    }

}


async function clearParking(cameraId) {

    const confirmed =
        confirm(
            "Clear all parking spaces for this camera?"
        );

    if (!confirmed) {
        return;
    }

    try {

        await fetch(
            `/api/parking/${cameraId}`,
            {
                method: "DELETE"
            }
        );

        updateParkingStats();

    } catch (error) {

        console.error(
            "Parking clear error:",
            error
        );

    }

}


function previousPage() {

    if (currentPage > 0) {

        currentPage--;

        renderPage();

    }

}


function nextPage() {

    const totalPages =
        Math.ceil(
            cameras.length
            / camerasPerPage
        );

    if (
        currentPage
        < totalPages - 1
    ) {

        currentPage++;

        renderPage();

    }

}


function updatePagination() {

    const totalPages =
        Math.max(
            1,
            Math.ceil(
                cameras.length
                / camerasPerPage
            )
        );

    document.getElementById(
        "previousButton"
    ).disabled =
        currentPage === 0;

    document.getElementById(
        "nextButton"
    ).disabled =
        currentPage >= totalPages - 1;

}


async function updateParkingStats() {

    try {

        const response =
            await fetch(
                "/api/parking/statistics"
            );

        const data =
            await response.json();

        document.getElementById(
            "totalSpaces"
        ).textContent =
            data.total_spaces || 0;

        document.getElementById(
            "occupiedSpaces"
        ).textContent =
            data.occupied_spaces || 0;

        document.getElementById(
            "availableSpaces"
        ).textContent =
            data.available_spaces || 0;

        document.getElementById(
            "parkingCount"
        ).textContent =
            `${data.occupied_spaces || 0} / ${data.total_spaces || 0}`;

    } catch (error) {

        console.error(
            "Parking statistics error:",
            error
        );

    }

}


async function updateVehicleStats() {

    try {

        const response =
            await fetch(
                "/health"
            );

        const data =
            await response.json();

        const total =
            data.ai?.total_detections || 0;

        document.getElementById(
            "vehicleCount"
        ).textContent =
            total;

    } catch (error) {

        console.error(
            "Vehicle statistics error:",
            error
        );

    }

}


function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


loadCameras();

updateParkingStats();

updateVehicleStats();

setInterval(
    loadCameras,
    5000
);

setInterval(
    updateParkingStats,
    2000
);

setInterval(
    updateVehicleStats,
    2000
);

</script>

</body>

</html>
"""