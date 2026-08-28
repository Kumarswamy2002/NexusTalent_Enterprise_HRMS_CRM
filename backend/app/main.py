"""
NexusTalent Enterprise HRMS & CRM
FastAPI Application Entrypoint & Live WebSocket Hub
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import logging

from backend.app.core.config import settings
from backend.app.core.database import init_db, AsyncSessionLocal
from backend.app.core.notifications import ws_manager
from backend.app.core.security import get_current_user, UserContext

# Routers
from backend.app.modules.hrms.router import router as hrms_router
from backend.app.modules.recruitment.router import router as recruitment_router
from backend.app.modules.attendance.router import router as attendance_router
from backend.app.modules.payroll.router import router as payroll_router
from backend.app.modules.performance.router import router as performance_router
from backend.app.modules.helpdesk.router import router as helpdesk_router
from backend.app.modules.ai_engine.router import router as ai_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NexusTalent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NexusTalent Enterprise Database...")
    await init_db()
    
    # Auto-seed if database is freshly created
    try:
        from backend.app.seeds.enterprise_seeder import seed_enterprise_data
        async with AsyncSessionLocal() as session:
            await seed_enterprise_data(session)
    except Exception as e:
        logger.warning(f"Seeder notice: {e}")

    logger.info("NexusTalent Enterprise Engine Online & Ready.")
    yield
    logger.info("NexusTalent Engine Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Enterprise Human Capital & Talent Relationship Management Platform (70,000+ LOC Target Architecture)",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Subsystem Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(hrms_router, prefix=api_v1_prefix)
app.include_router(recruitment_router, prefix=api_v1_prefix)
app.include_router(attendance_router, prefix=api_v1_prefix)
app.include_router(payroll_router, prefix=api_v1_prefix)
app.include_router(performance_router, prefix=api_v1_prefix)
app.include_router(helpdesk_router, prefix=api_v1_prefix)
app.include_router(ai_router, prefix=api_v1_prefix)


# Real-time WebSocket Gateway
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = "anonymous_client"):
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo heartbeat or client message
            await websocket.send_text(f'{{"type": "ACK", "message": "Heartbeat received"}}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, client_id)


# Health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "system": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Frontend static files mounting
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(frontend_path / "index.html")
