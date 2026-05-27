from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
import json

router = APIRouter()

# Connected WebSocket clients
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.active_connections.discard(conn)


manager = ConnectionManager()


async def broadcast_action(action_data: dict):
    """Broadcast an action to all connected clients."""
    await manager.broadcast({
        "type": "action",
        "data": action_data
    })


async def broadcast_stats(stats_data: dict):
    """Broadcast updated stats to all connected clients."""
    await manager.broadcast({
        "type": "stats",
        "data": stats_data
    })


async def broadcast_persona(persona_data: dict):
    """Broadcast persona change to all connected clients."""
    await manager.broadcast({
        "type": "persona",
        "data": persona_data
    })


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client messages
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_json({"type": "pong", "message": "alive"})
            
            # Handle subscribe messages
            try:
                msg = json.loads(data)
                if msg.get("type") == "subscribe":
                    # Client subscribing to updates
                    await websocket.send_json({
                        "type": "subscribed",
                        "message": "Connected to Fauxx live updates"
                    })
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
