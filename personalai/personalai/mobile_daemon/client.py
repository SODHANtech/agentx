import asyncio
import json
import logging
import subprocess
from typing import Dict, Any, Optional
import websockets
from personalai.config import settings

logger = logging.getLogger(__name__)


class MobileNodeDaemon:
    """Background client daemon running on Android/Termux to receive P2P mesh intent payloads."""

    def __init__(self, broker_url: Optional[str] = None):
        self.broker_url = broker_url or f"ws://{settings.mesh_host}:{settings.mesh_port}"
        self.running = False

    def handle_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes incoming device intent payload."""
        action = payload.get("action")
        logger.info(f"Mobile node handling action: {action}")

        if action in ["OPEN_URL", "VIEW_VIDEO"]:
            url = payload.get("url") or payload.get("uri") or ""
            logger.info(f"Opening URL/Video on mobile device: {url}")
            try:
                # Try termux-open-url first
                subprocess.run(["termux-open-url", url], check=True)
                return {"status": "success", "action": action, "url": url}
            except Exception as e:
                # Fallback to Android am start intent
                try:
                    subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", url], check=True)
                    return {"status": "success", "action": action, "url": url, "fallback": "am_start"}
                except Exception as fallback_err:
                    return {"status": "error", "action": action, "error": str(e)}

        elif action == "LAUNCH_APP":
            package = payload.get("package", "")
            cmd = ["am", "start", "-n", f"{package}/.MainActivity"]
            try:
                subprocess.run(cmd, check=True)
                return {"status": "success", "action": action, "package": package}
            except Exception as e:
                # Termux open fallback
                try:
                    subprocess.run(["termux-open-url", f"https://app.launch/{package}"], check=True)
                    return {"status": "success", "action": action, "fallback": "termux-open-url"}
                except Exception as fallback_err:
                    return {"status": "error", "action": action, "error": str(e)}

        elif action == "VIBRATE":
            try:
                subprocess.run(["termux-vibrate", "-d", "500"], check=True)
                return {"status": "success", "action": action}
            except Exception as e:
                return {"status": "error", "action": action, "error": str(e)}

        return {"status": "unknown_action", "action": action}

    async def start_listening(self):
        """Connects to the orchestrator's P2P WebSocket broker and listens for tasks."""
        self.running = True
        logger.info(f"Mobile Node Daemon connecting to mesh broker at {self.broker_url}...")
        while self.running:
            try:
                async with websockets.connect(self.broker_url) as websocket:
                    logger.info("Connected to mesh broker. Listening for intent payloads...")
                    async for message in websocket:
                        try:
                            payload = json.loads(message)
                            response = self.handle_payload(payload)
                            await websocket.send(json.dumps(response))
                        except json.JSONDecodeError:
                            logger.error("Received malformed JSON on mobile client.")
            except Exception as e:
                logger.warning(f"Connection lost to mesh broker: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
