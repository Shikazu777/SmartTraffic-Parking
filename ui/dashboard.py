import time

import cv2
import numpy as np

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse


def create_dashboard(
    camera_manager,
    ai_manager=None,
    parking_manager=None
):

    app = FastAPI(
        title="MulCamFeed",
        version="1.0.0"
    )

    app.state.ai_manager = ai_manager
    app.state.parking_manager = parking_manager

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

    min-height: 78px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 12px 28px;

    background: #12151a;

    border-bottom:
        1px solid
        rgba(255,255,255,0.08);

}

.logo {

    font-size: 23px;

    font-weight: 700;

}

.subtitle {

    margin-top: 3px;

    color: #89929d;

    font-size: 13px;

}

.header-right {

    display: flex;

    align-items: center;

    gap: 18px;

}

.stat {

    padding:
        7px
        12px;

    border-radius: 7px;

    background: #1a2027;

    color: #b9c1ca;

    font-size: 12px;

}

.stat strong {

    color: white;

    font-size: 14px;

}

.dashboard {

    padding: 20px;

}

.grid {

    display: grid;

    grid-template-columns:
        repeat(2, minmax(0, 1fr));

    gap: 18px;

}

.camera-card {

    overflow: hidden;

    background: #11151a;

    border:
        1px solid
        rgba(255,255,255,0.08);

    border-radius: 12px;

}

.camera-header {

    min-height: 52px;

    padding:
        8px
        14px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    border-bottom:
        1px solid
        rgba(255,255,255,0.07);

}

.camera-title {

    display: flex;

    flex-direction: column;

    gap: 3px;

}

.camera-name {

    font-size: 14px;

    font-weight: 600;

}

.camera-meta {

    color: #737d88;

    font-size: 10px;

}

.status {

    display: flex;

    align-items: center;

    gap: 6px;

    font-size: 10px;

    font-weight: 600;

}

.status-dot {

    width: 7px;

    height: 7px;

    border-radius: 50%;

    background: #666;

}

.status-live .status-dot {

    background: #35d07f;

    box-shadow:
        0 0 8px
        rgba(53,208,127,0.7);

}

.status-connecting .status-dot {

    background: #f0b429;

}

.status-error .status-dot {

    background: #ff4d4d;

}

.video-container {

    position: relative;

    width: 100%;

    aspect-ratio: 16 / 9;

    background: #030405;

    overflow: hidden;

}

.video-container img {

    display: block;

    width: 100%;

    height: 100%;

    object-fit: contain;

}

.parking-canvas {

    position: absolute;

    inset: 0;

    width: 100%;

    height: 100%;

    cursor: default;

}

.parking-canvas.drawing {

    cursor: crosshair;

}

.camera-footer {

    min-height: 48px;

    padding:
        8px
        12px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 8px;

    border-top:
        1px solid
        rgba(255,255,255,0.06);

}

.parking-info {

    display: flex;

    gap: 10px;

    flex-wrap: wrap;

}

.parking-stat {

    font-size: 11px;

    color: #8d96a0;

}

.parking-stat strong {

    color: white;

}

.parking-stat.occupied strong {

    color: #ff5252;

}

.parking-stat.free strong {

    color: #35d07f;

}

.camera-actions {

    display: flex;

    gap: 6px;

}

button {

    border:
        1px solid
        rgba(255,255,255,0.12);

    background: #171c22;

    color: white;

    padding:
        7px
        10px;

    border-radius: 6px;

    cursor: pointer;

    font-size: 10px;

}

button:hover:not(:disabled) {

    background: #222932;

}

button:disabled {

    opacity: 0.35;

    cursor: default;

}

.draw-active {

    background: #244d38;

    border-color: #35d07f;

}

.controls {

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 14px;

    margin-top: 20px;

}

.page {

    min-width: 110px;

    text-align: center;

    color: #969faa;

    font-size: 12px;

}

.empty-card {

    min-height: 260px;

    display: flex;

    align-items: center;

    justify-content: center;

    flex-direction: column;

    gap: 8px;

    background: #0e1115;

    border:
        1px solid
        rgba(255,255,255,0.06);

    border-radius: 12px;

    color: #626b75;

}

.empty-title {

    color: #858e98;

    font-size: 13px;

}

.empty-subtitle {

    font-size: 11px;

}

.toast {

    position: fixed;

    right: 20px;

    bottom: 20px;

    padding:
        10px
        14px;

    background: #1b222a;

    border:
        1px solid
        rgba(255,255,255,0.12);

    border-radius: 7px;

    color: white;

    font-size: 12px;

    opacity: 0;

    pointer-events: none;

    transform:
        translateY(10px);

    transition:
        opacity 0.2s,
        transform 0.2s;

    z-index: 1000;

}

.toast.show {

    opacity: 1;

    transform:
        translateY(0);

}

.legend {

    display: flex;

    justify-content: center;

    gap: 18px;

    margin-top: 14px;

    color: #747e89;

    font-size: 10px;

}

.legend-item {

    display: flex;

    align-items: center;

    gap: 5px;

}

.legend-box {

    width: 9px;

    height: 9px;

    border-radius: 2px;

}

.legend-free {

    background: #35d07f;

}

.legend-occupied {

    background: #ff3f3f;

}

@media (max-width: 900px) {

    .grid {

        grid-template-columns: 1fr;

    }

    .header {

        padding:
            12px
            16px;

    }

    .header-right {

        gap: 6px;

    }

    .dashboard {

        padding: 12px;

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


    <div class="header-right">

        <div class="stat">
            Cameras:
            <strong id="cameraCount">0 / 0</strong>
        </div>

        <div class="stat">
            Parked:
            <strong id="parkedCount">0</strong>
        </div>

        <div class="stat">
            Free:
            <strong id="freeCount">0</strong>
        </div>

    </div>

</header>


<main class="dashboard">

    <section
        class="grid"
        id="cameraGrid"
    >
    </section>


    <div class="legend">

        <div class="legend-item">
            <span
                class="legend-box legend-free"
            ></span>
            FREE
        </div>

        <div class="legend-item">
            <span
                class="legend-box legend-occupied"
            ></span>
            OCCUPIED
        </div>

    </div>


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
            Page 1 / 1
        </div>


        <button
            id="nextButton"
            onclick="nextPage()"
        >
            Next →
        </button>

    </div>

</main>


<div
    class="toast"
    id="toast"
>
    Saved
</div>


<script>

let cameras = [];

let currentPage = 0;

const camerasPerPage = 4;

const drawingStates = {};

const cameraZones = {};


// --------------------------------------------------
// Toast
// --------------------------------------------------

function showToast(message) {

    const toast =
        document.getElementById("toast");

    toast.textContent = message;

    toast.classList.add("show");

    setTimeout(
        () => {
            toast.classList.remove("show");
        },
        1800
    );
}


// --------------------------------------------------
// Camera API
// --------------------------------------------------

async function loadCameras() {

    try {

        const response =
            await fetch("/api/cameras");

        const data =
            await response.json();

        cameras = data.cameras || [];

        document.getElementById(
            "cameraCount"
        ).textContent =
            `${data.active} / ${data.total}`;

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
// Parking statistics
// --------------------------------------------------

async function loadParkingStatistics() {

    try {

        const response =
            await fetch(
                "/api/parking/statistics"
            );

        if (!response.ok) {
            return;
        }

        const data =
            await response.json();

        document.getElementById(
            "parkedCount"
        ).textContent =
            data.occupied_spaces || 0;

        document.getElementById(
            "freeCount"
        ).textContent =
            data.available_spaces || 0;

    }

    catch (error) {

        console.error(
            "Parking statistics error:",
            error
        );

    }

}


// --------------------------------------------------
// Load parking zones
// --------------------------------------------------

async function loadZones(cameraId) {

    try {

        const response =
            await fetch(
                `/api/parking/${cameraId}`
            );

        if (!response.ok) {
            return [];
        }

        const data =
            await response.json();

        cameraZones[cameraId] =
            data.zones || [];

        return cameraZones[cameraId];

    }

    catch (error) {

        console.error(
            "Parking zone error:",
            error
        );

        return [];

    }

}


// --------------------------------------------------
// Load camera parking stats
// --------------------------------------------------

async function loadCameraParking(
    cameraId
) {

    try {

        const response =
            await fetch(
                `/api/parking/${cameraId}/statistics`
            );

        if (!response.ok) {
            return;
        }

        const data =
            await response.json();

        const total =
            document.getElementById(
                `parking-total-${cameraId}`
            );

        const occupied =
            document.getElementById(
                `parking-occupied-${cameraId}`
            );

        const free =
            document.getElementById(
                `parking-free-${cameraId}`
            );

        if (total) {
            total.textContent =
                data.total_spaces || 0;
        }

        if (occupied) {
            occupied.textContent =
                data.occupied_spaces || 0;
        }

        if (free) {
            free.textContent =
                data.available_spaces || 0;
        }

    }

    catch (error) {

        console.error(
            "Camera parking error:",
            error
        );

    }

}


// --------------------------------------------------
// Status
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
// Render dashboard
// --------------------------------------------------

function renderPage() {

    const grid =
        document.getElementById(
            "cameraGrid"
        );

    grid.innerHTML = "";

    const totalPages =
        Math.max(
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

                <div class="camera-title">

                    <div class="camera-name">
                        ${camera.name}
                    </div>

                    <div class="camera-meta">
                        Camera ${camera.id}
                        ·
                        ${camera.ai_mode || "none"}
                    </div>

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


            <div class="video-container">

                <img
                    src="/stream/${camera.id}"
                    alt="${camera.name}"
                >

                <canvas
                    id="canvas-${camera.id}"
                    class="parking-canvas"
                ></canvas>

            </div>


            <div class="camera-footer">

                <div class="parking-info">

                    <div
                        class="parking-stat"
                    >
                        Spaces:
                        <strong
                            id="parking-total-${camera.id}"
                        >
                            0
                        </strong>
                    </div>

                    <div
                        class="
                            parking-stat
                            occupied
                        "
                    >
                        Occupied:
                        <strong
                            id="parking-occupied-${camera.id}"
                        >
                            0
                        </strong>
                    </div>

                    <div
                        class="
                            parking-stat
                            free
                        "
                    >
                        Free:
                        <strong
                            id="parking-free-${camera.id}"
                        >
                            0
                        </strong>
                    </div>

                </div>


                <div class="camera-actions">

                    <button
                        id="draw-${camera.id}"
                        onclick="
                            toggleDrawing(
                                ${camera.id}
                            )
                        "
                    >
                        Draw Parking
                    </button>

                    <button
                        onclick="
                            clearParking(
                                ${camera.id}
                            )
                        "
                    >
                        Clear
                    </button>

                </div>

            </div>
        `;

        grid.appendChild(card);

        setupCanvas(camera.id);

        loadZones(camera.id);

        loadCameraParking(camera.id);

    }


    while (
        grid.children.length <
        camerasPerPage
    ) {

        const empty =
            document.createElement(
                "div"
            );

        empty.className =
            "empty-card";

        empty.innerHTML = `

            <div class="empty-title">
                NOT AVAILABLE
            </div>

            <div class="empty-subtitle">
                No camera assigned
                to this slot
            </div>

        `;

        grid.appendChild(empty);

    }


    document.getElementById(
        "pageNumber"
    ).textContent =
        `Page ${
            currentPage + 1
        } / ${totalPages}`;


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
// Canvas setup
// --------------------------------------------------

function setupCanvas(cameraId) {

    const canvas =
        document.getElementById(
            `canvas-${cameraId}`
        );

    if (!canvas) {
        return;
    }

    const container =
        canvas.parentElement;

    function resizeCanvas() {

        canvas.width =
            container.clientWidth;

        canvas.height =
            container.clientHeight;

        drawZones(cameraId);

    }

    resizeCanvas();

    window.addEventListener(
        "resize",
        resizeCanvas
    );

    canvas.onclick =
        function(event) {

            if (
                !drawingStates[cameraId]
                ||
                !drawingStates[
                    cameraId
                ].active
            ) {
                return;
            }

            const rect =
                canvas.getBoundingClientRect();

            const x =
                event.clientX -
                rect.left;

            const y =
                event.clientY -
                rect.top;

            const state =
                drawingStates[
                    cameraId
                ];

            state.points.push([
                x,
                y
            ]);

            drawZones(cameraId);

            if (
                state.points.length === 4
            ) {

                saveNewZone(
                    cameraId,
                    state.points
                );

            }

        };

}


// --------------------------------------------------
// Drawing mode
// --------------------------------------------------

function toggleDrawing(cameraId) {

    if (
        !drawingStates[cameraId]
    ) {

        drawingStates[cameraId] = {
            active: false,
            points: []
        };

    }

    const state =
        drawingStates[cameraId];

    state.active =
        !state.active;

    state.points = [];

    const button =
        document.getElementById(
            `draw-${cameraId}`
        );

    const canvas =
        document.getElementById(
            `canvas-${cameraId}`
        );

    if (state.active) {

        button.textContent =
            "Click 4 Corners";

        button.classList.add(
            "draw-active"
        );

        canvas.classList.add(
            "drawing"
        );

        showToast(
            "Click 4 corners of the parking space"
        );

    }

    else {

        button.textContent =
            "Draw Parking";

        button.classList.remove(
            "draw-active"
        );

        canvas.classList.remove(
            "drawing"
        );

    }

    drawZones(cameraId);

}


// --------------------------------------------------
// Save parking zone
// --------------------------------------------------

async function saveNewZone(
    cameraId,
    points
) {

    const canvas =
        document.getElementById(
            `canvas-${cameraId}`
        );

    const videoWidth = 640;

    const videoHeight = 360;

    const scaleX =
        videoWidth /
        canvas.width;

    const scaleY =
        videoHeight /
        canvas.height;

    const converted =
        points.map(
            point => [
                Math.round(
                    point[0] * scaleX
                ),
                Math.round(
                    point[1] * scaleY
                )
            ]
        );

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
                        points: converted
                    })
                }
            );

        if (!response.ok) {

            showToast(
                "Failed to save parking space"
            );

            return;

        }

        const data =
            await response.json();

        cameraZones[cameraId] =
            data.zones || [];

        drawingStates[
            cameraId
        ].points = [];

        drawingStates[
            cameraId
        ].active = false;

        const button =
            document.getElementById(
                `draw-${cameraId}`
            );

        const canvasElement =
            document.getElementById(
                `canvas-${cameraId}`
            );

        button.textContent =
            "Draw Parking";

        button.classList.remove(
            "draw-active"
        );

        canvasElement.classList.remove(
            "drawing"
        );

        drawZones(cameraId);

        await loadCameraParking(
            cameraId
        );

        await loadParkingStatistics();

        showToast(
            "Parking space saved"
        );

    }

    catch (error) {

        console.error(
            "Save parking error:",
            error
        );

        showToast(
            "Failed to save parking space"
        );

    }

}


// --------------------------------------------------
// Clear parking
// --------------------------------------------------

async function clearParking(cameraId) {

    const confirmed =
        window.confirm(
            "Clear all parking spaces for this camera?"
        );

    if (!confirmed) {
        return;
    }

    try {

        const response =
            await fetch(
                `/api/parking/${cameraId}`,
                {
                    method: "DELETE"
                }
            );

        if (!response.ok) {

            showToast(
                "Failed to clear parking"
            );

            return;

        }

        cameraZones[cameraId] = [];

        if (
            drawingStates[cameraId]
        ) {

            drawingStates[
                cameraId
            ].points = [];

        }

        drawZones(cameraId);

        await loadCameraParking(
            cameraId
        );

        await loadParkingStatistics();

        showToast(
            "Parking spaces cleared"
        );

    }

    catch (error) {

        console.error(
            "Clear parking error:",
            error
        );

    }

}


// --------------------------------------------------
// Draw parking zones
// --------------------------------------------------

function drawZones(cameraId) {

    const canvas =
        document.getElementById(
            `canvas-${cameraId}`
        );

    if (!canvas) {
        return;
    }

    const context =
        canvas.getContext("2d");

    context.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
    );

    const zones =
        cameraZones[cameraId] || [];

    const scaleX =
        canvas.width / 640;

    const scaleY =
        canvas.height / 360;


    for (
        const zone
        of zones
    ) {

        const points =
            zone.points.map(
                point => [
                    point[0] * scaleX,
                    point[1] * scaleY
                ]
            );

        context.beginPath();

        context.moveTo(
            points[0][0],
            points[0][1]
        );

        for (
            let i = 1;
            i < points.length;
            i++
        ) {

            context.lineTo(
                points[i][0],
                points[i][1]
            );

        }

        context.closePath();

        context.strokeStyle =
            "#35d07f";

        context.lineWidth = 2;

        context.stroke();

        context.fillStyle =
            "rgba(53, 208, 127, 0.08)";

        context.fill();

        context.fillStyle =
            "white";

        context.font =
            "11px sans-serif";

        context.fillText(
            `P${zone.id}`,
            points[0][0] + 4,
            points[0][1] - 4
        );

    }


    const state =
        drawingStates[cameraId];

    if (
        !state
        ||
        state.points.length === 0
    ) {
        return;
    }


    context.strokeStyle =
        "#f0b429";

    context.fillStyle =
        "#f0b429";

    context.lineWidth = 2;


    for (
        const point
        of state.points
    ) {

        context.beginPath();

        context.arc(
            point[0],
            point[1],
            5,
            0,
            Math.PI * 2
        );

        context.fill();

    }


    if (
        state.points.length > 1
    ) {

        context.beginPath();

        context.moveTo(
            state.points[0][0],
            state.points[0][1]
        );

        for (
            let i = 1;
            i < state.points.length;
            i++
        ) {

            context.lineTo(
                state.points[i][0],
                state.points[i][1]
            );

        }

        context.stroke();

    }

}


// --------------------------------------------------
// Page navigation
// --------------------------------------------------

function nextPage() {

    const totalPages =
        Math.max(
            1,
            Math.ceil(
                cameras.length /
                camerasPerPage
            )
        );

    if (
        currentPage <
        totalPages - 1
    ) {

        currentPage++;

        renderPage();

    }

}


function previousPage() {

    if (
        currentPage > 0
    ) {

        currentPage--;

        renderPage();

    }

}


// --------------------------------------------------
// Keyboard navigation
// --------------------------------------------------

document.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "ArrowRight"
        ) {

            nextPage();

        }

        if (
            event.key === "ArrowLeft"
        ) {

            previousPage();

        }

    }
);


// --------------------------------------------------
// Refresh
// --------------------------------------------------

setInterval(
    loadCameras,
    3000
);

setInterval(
    loadParkingStatistics,
    2000
);

setInterval(
    function() {

        for (
            const camera
            of cameras
        ) {

            loadCameraParking(
                camera.id
            );

        }

    },
    2000
);


// --------------------------------------------------
// Initial load
// --------------------------------------------------

loadCameras();

loadParkingStatistics();

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

    @app.get(
        "/api/cameras"
    )
    async def get_cameras():

        return JSONResponse(
            {
                "total":
                    camera_manager.get_total_count(),

                "active":
                    camera_manager.get_active_count(),

                "cameras":
                    camera_manager.get_camera_info()
            }
        )


    # --------------------------------------------------
    # Parking zones
    # --------------------------------------------------

    @app.get(
        "/api/parking/{camera_id}"
    )
    async def get_parking_zones(
        camera_id: int
    ):

        if parking_manager is None:

            return JSONResponse(
                {
                    "camera_id": camera_id,
                    "zones": []
                }
            )

        zones = (
            parking_manager.get_zones(
                camera_id
            )
        )

        return JSONResponse(
            {
                "camera_id": camera_id,
                "zones": zones
            }
        )


    @app.post(
        "/api/parking/{camera_id}"
    )
    async def add_parking_zone(
        camera_id: int,
        payload: dict
    ):

        if parking_manager is None:

            return JSONResponse(
                {
                    "error":
                        "Parking manager unavailable"
                },
                status_code=500
            )

        points = payload.get(
            "points",
            []
        )

        if len(points) != 4:

            return JSONResponse(
                {
                    "error":
                        "Exactly 4 points are required"
                },
                status_code=400
            )

        zone = (
            parking_manager.add_zone(
                camera_id,
                points
            )
        )

        return JSONResponse(
            {
                "success": True,
                "zone": zone,
                "zones":
                    parking_manager.get_zones(
                        camera_id
                    )
            }
        )


    @app.delete(
        "/api/parking/{camera_id}"
    )
    async def delete_parking_zones(
        camera_id: int
    ):

        if parking_manager is None:

            return JSONResponse(
                {
                    "error":
                        "Parking manager unavailable"
                },
                status_code=500
            )

        parking_manager.clear_zones(
            camera_id
        )

        return JSONResponse(
            {
                "success": True,
                "camera_id": camera_id,
                "zones": []
            }
        )


    # --------------------------------------------------
    # Per-camera parking statistics
    # --------------------------------------------------

    @app.get(
        "/api/parking/{camera_id}/statistics"
    )
    async def get_camera_parking_statistics(
        camera_id: int
    ):

        if ai_manager is None:

            return JSONResponse(
                {
                    "camera_id": camera_id,
                    "total_spaces": 0,
                    "occupied_spaces": 0,
                    "available_spaces": 0,
                    "occupancy": []
                }
            )

        statistics = (
            ai_manager.get_parking_statistics(
                camera_id
            )
        )

        return JSONResponse(
            {
                "camera_id": camera_id,
                **statistics
            }
        )


    # --------------------------------------------------
    # Global parking statistics
    # --------------------------------------------------

    @app.get(
        "/api/parking/statistics"
    )
    async def get_global_parking_statistics():

        if ai_manager is None:

            return JSONResponse(
                {
                    "total_spaces": 0,
                    "occupied_spaces": 0,
                    "available_spaces": 0
                }
            )

        statistics = (
            ai_manager.get_global_parking_statistics()
        )

        return JSONResponse(
            statistics
        )


    # --------------------------------------------------
    # Placeholder
    # --------------------------------------------------

    @app.get(
        "/placeholder"
    )
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

        success, encoded = (
            cv2.imencode(
                ".jpg",
                frame
            )
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
                [
                    encoded.tobytes()
                ]
            ),
            media_type="image/jpeg"
        )


    # --------------------------------------------------
    # Camera stream
    # --------------------------------------------------

    @app.get(
        "/stream/{camera_id}"
    )
    async def stream_camera(
        camera_id: int
    ):

        camera = (
            camera_manager.get_camera(
                camera_id
            )
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

                frame = (
                    camera.get_stream_frame()
                )

                if frame is None:

                    frame = (
                        camera.create_placeholder()
                    )

                success, encoded = (
                    cv2.imencode(
                        ".jpg",
                        frame,
                        [
                            cv2.IMWRITE_JPEG_QUALITY,
                            75
                        ]
                    )
                )

                if not success:

                    time.sleep(0.05)

                    continue

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + encoded.tobytes()
                    + b"\r\n"
                )

                time.sleep(0.03)


        return StreamingResponse(
            generate(),
            media_type=(
                "multipart/x-mixed-replace; "
                "boundary=frame"
            )
        )


    return app