from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from core.camera_manager import CameraManager
from ai.ai_manager import AIManager
from ai.trafficvision.parking import ParkingManager
from ui.dashboard import create_dashboard


BASE_DIR = Path(__file__).resolve().parent

CONFIG_PATH = (
    BASE_DIR
    / "config"
    / "cameras.json"
)

PARKING_CONFIG_PATH = (
    BASE_DIR
    / "config"
    / "parking_zones.json"
)


parking_manager = ParkingManager(
    str(PARKING_CONFIG_PATH)
)


ai_manager = AIManager(
    parking_manager
)


camera_manager = CameraManager(
    str(CONFIG_PATH),
    ai_manager
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("=" * 60)
    print("MulCamFeed")
    print("Multi-Camera Monitoring Dashboard")
    print("=" * 60)

    print()
    print("Starting cameras...")

    camera_manager.start_all()

    print()
    print("Starting AI systems...")

    ai_manager.start()

    print()
    print("Dashboard running at:")
    print("http://localhost:8000")

    print("=" * 60)

    yield

    print()
    print("Stopping AI systems...")

    ai_manager.stop()

    print()
    print("Stopping cameras...")

    camera_manager.stop_all()


app = create_dashboard(
    camera_manager,
    ai_manager,
    parking_manager
)


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "application": "MulCamFeed",

        "cameras": {
            "total": camera_manager.get_total_count(),
            "active": camera_manager.get_active_count()
        },

        "ai": ai_manager.get_status(),

        "parking": (
            ai_manager.get_global_parking_statistics()
        )
    }


app.router.lifespan_context = lifespan


if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )