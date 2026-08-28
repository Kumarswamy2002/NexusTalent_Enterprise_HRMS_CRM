"""
NexusTalent Universal Omnichannel Notification & WebSocket Hub
Dispatches Real-time In-App WebSocket Events, Toasts, Emails, and System Alerts.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json
import logging
from fastapi import WebSocket
from backend.app.core.database import Base
from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.event_bus import event_bus, DomainEvent

logger = logging.getLogger("Notifications")


class NotificationRecord(Base):
    __tablename__ = "core_notifications"

    recipient_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default="general")  # recruitment, leave, payroll, alert
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    action_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class WebSocketConnectionManager:
    """Manages active live WebSocket connections for real-time dashboard updates."""

    def __init__(self):
        # Map user_id -> List of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.broadcast_pool: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: str = "anonymous"):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.broadcast_pool.append(websocket)
        logger.info(f"WebSocket client connected: user={user_id} (total={len(self.broadcast_pool)})")

    def disconnect(self, websocket: WebSocket, user_id: str = "anonymous"):
        if user_id in self.active_connections and websocket in self.active_connections[user_id]:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        if websocket in self.broadcast_pool:
            self.broadcast_pool.remove(websocket)
        logger.info(f"WebSocket client disconnected: user={user_id}")

    async def send_personal_message(self, message: Dict[str, Any], user_id: str):
        if user_id in self.active_connections:
            payload = json.dumps(message)
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(payload)
                except Exception:
                    pass

    async def broadcast(self, message: Dict[str, Any]):
        payload = json.dumps(message)
        dead_connections = []
        for connection in self.broadcast_pool:
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            if dead in self.broadcast_pool:
                self.broadcast_pool.remove(dead)


ws_manager = WebSocketConnectionManager()


# Realtime Event Bridge: pushes selected domain events directly to live UI clients
async def realtime_event_dispatcher(event: DomainEvent) -> None:
    message = {
        "type": "DOMAIN_EVENT",
        "event_type": event.event_type,
        "actor_id": event.actor_id,
        "payload": event.payload,
        "timestamp": event.timestamp
    }
    await ws_manager.broadcast(message)

event_bus.subscribe("*", realtime_event_dispatcher)
