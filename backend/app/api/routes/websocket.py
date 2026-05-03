"""WebSocket endpoint for live risk feed streaming."""

import asyncio
import json
from typing import Set

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.session import get_redis

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["websocket"])

# Active WebSocket connections
_connections: Set[WebSocket] = set()

REDIS_CHANNEL = "oracle:live_alerts"


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self) -> None:
        """Initialise the connection manager."""
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket connected", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket."""
        self.active_connections.discard(websocket)
        logger.info("WebSocket disconnected", total=len(self.active_connections))

    async def broadcast(self, message: str) -> None:
        """Broadcast a message to all connected clients."""
        dead: Set[WebSocket] = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.add(connection)
        for conn in dead:
            self.active_connections.discard(conn)


manager = ConnectionManager()


@router.websocket("/risks/live")
async def live_risk_feed(websocket: WebSocket) -> None:
    """
    WebSocket endpoint streaming live risk updates.

    Clients receive JSON messages whenever a new alert is published to Redis.
    """
    await manager.connect(websocket)

    try:
        redis = await get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(REDIS_CHANNEL)

        # Send a welcome message with current connection count
        await websocket.send_text(
            json.dumps({
                "type": "connected",
                "message": "Oracle live feed connected",
                "connections": len(manager.active_connections),
            })
        )

        # Listen for messages from Redis pub/sub
        async def redis_listener() -> None:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await manager.broadcast(message["data"])

        # Also listen for client pings to keep connection alive
        async def client_listener() -> None:
            while True:
                try:
                    data = await websocket.receive_text()
                    if data == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except WebSocketDisconnect:
                    break

        await asyncio.gather(redis_listener(), client_listener())

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")
    except Exception as exc:
        logger.error("WebSocket error", error=str(exc))
    finally:
        manager.disconnect(websocket)
        try:
            await pubsub.unsubscribe(REDIS_CHANNEL)
        except Exception:
            pass


async def publish_alert(alert_data: dict) -> None:
    """Publish a new alert to the Redis channel for WebSocket broadcast."""
    try:
        redis = await get_redis()
        await redis.publish(REDIS_CHANNEL, json.dumps(alert_data))
    except Exception as exc:
        logger.error("Failed to publish alert to Redis", error=str(exc))
