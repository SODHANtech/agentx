from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from sqlalchemy.exc import SQLAlchemyError

from backend.config import settings
from backend.api.routes import router
from backend.database.session import engine, Base
from backend.database import models
from backend.core.logging_config import setup_logging

# Initialize structured logging
setup_logging()

# Automatically build schemas on startup
Base.metadata.create_all(bind=engine)

import time

app = FastAPI(
    title="Smart Campus AI",
    version="1.0.0"
)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    import logging
    logger = logging.getLogger("campusos")
    logger.error(f"Database error occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "A database operation error occurred. Please contact the administrator."}
    )

app.state.start_time = time.time()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"WebSocket client connected: User #{user_id}")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"WebSocket client disconnected: User #{user_id}")

    async def send_personal_message(self, message: dict, user_id: int):
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending WebSocket message to user #{user_id}: {e}")
                self.disconnect(user_id)

manager = ConnectionManager()
app.state.notification_manager = manager

@app.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection open and check client connection health
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Include API Router
app.include_router(router)
