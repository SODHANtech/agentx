import asyncio
import json
import logging
from typing import Dict, Any, Set, Optional
import websockets
from personalai.config import settings

logger = logging.getLogger(__name__)


class P2PEventBroker:
    """Asynchronous WebSocket event broker for peer-to-peer control over Tailscale mesh network."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or settings.mesh_host
        self.port = port or settings.mesh_port
        self.connected_clients: Set[Any] = set()
        self.server: Optional[Any] = None

    async def register(self, websocket: Any):
        self.connected_clients.add(websocket)
        logger.info(f"P2P Node connected: {getattr(websocket, 'remote_address', 'client')}")

    async def unregister(self, websocket: Any):
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
        logger.info(f"P2P Node disconnected: {getattr(websocket, 'remote_address', 'client')}")

    async def handle_connection(self, websocket: Any, path: Optional[str] = None):
        await self.register(websocket)
        try:
            async for message in websocket:
                try:
                    payload = json.loads(message)
                    logger.info(f"Received P2P Mesh payload: {payload}")
                    if "status" in payload:
                        logger.info("Received execution result ACK. Not re-broadcasting.")
                    else:
                        await self.broadcast(payload, sender=websocket)
                except json.JSONDecodeError:

                    logger.error("Received malformed non-JSON message over mesh.")
        except Exception:
            pass
        finally:
            await self.unregister(websocket)

    async def broadcast(self, payload: Dict[str, Any], sender: Optional[Any] = None):
        if not self.connected_clients:
            return

        message = json.dumps(payload)
        for client in list(self.connected_clients):
            if client != sender:
                try:
                    await client.send(message)
                except Exception:
                    pass

    async def start(self):
        logger.info(f"Starting P2P Event Broker on {self.host}:{self.port} over Tailscale P2P...")
        self.server = await websockets.serve(self.handle_connection, self.host, self.port)

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("P2P Event Broker stopped.")
