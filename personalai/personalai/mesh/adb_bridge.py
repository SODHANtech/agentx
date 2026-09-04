import logging
import subprocess
from typing import Dict, Any, Optional
from personalai.config import settings

logger = logging.getLogger(__name__)


class MobileADBBridge:
    """Wireless ADB Bridge for dispatching cross-platform actions to Android mobile nodes over P2P mesh network."""

    def __init__(self, device_ip: Optional[str] = None, port: Optional[int] = None):
        self.device_ip = device_ip or settings.mobile_device_ip
        self.port = port or settings.mobile_adb_port
        self.target = f"{self.device_ip}:{self.port}"

    def connect(self) -> bool:
        """Establishes TCP connection to remote mobile ADB daemon over private mesh."""
        cmd = ["adb", "connect", self.target]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if "connected" in result.stdout.lower():
                logger.info(f"Connected to mobile ADB target at {self.target}")
                return True
            logger.warning(f"ADB connection output: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"Failed to connect to mobile ADB target {self.target}: {e}")
        return False

    def launch_application(self, package_name: str) -> Dict[str, Any]:
        """Dispatches an application launch intent to Android device (e.g. org.mozilla.firefox)."""
        cmd = ["adb", "-s", self.target, "shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"]
        logger.info(f"Dispatching application launch intent for {package_name} on {self.target}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            success = result.returncode == 0
            return {
                "action": "LAUNCH_APP",
                "package": package_name,
                "success": success,
                "output": result.stdout.strip(),
            }
        except Exception as e:
            logger.error(f"Failed to launch package {package_name}: {e}")
            return {
                "action": "LAUNCH_APP",
                "package": package_name,
                "success": False,
                "error": str(e),
            }

    def execute_custom_intent(self, intent_action: str, uri: str) -> Dict[str, Any]:
        """Executes a generic Android intent via am start."""
        cmd = ["adb", "-s", self.target, "shell", "am", "start", "-a", intent_action, "-d", uri]
        logger.info(f"Executing intent {intent_action} with URI {uri}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return {
                "action": "EXECUTE_INTENT",
                "intent": intent_action,
                "uri": uri,
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
            }
        except Exception as e:
            return {
                "action": "EXECUTE_INTENT",
                "intent": intent_action,
                "uri": uri,
                "success": False,
                "error": str(e),
            }
