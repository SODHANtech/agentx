import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from personalai.config import settings

logger = logging.getLogger(__name__)


class ActionRequest(BaseModel):
    action_type: str = Field(..., description="Type of system action requested (e.g. FILE_WRITE, FILE_DELETE, EXEC_CMD)")
    target: str = Field(..., description="Target file path, command string, or package name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    is_destructive: bool = Field(default=False, description="Flag indicating high-risk destructive action")


class SecurityValidator:
    """Enforces strict schema validation, operational safety locks, and permission gate controls."""

    DESTRUCTIVE_KEYWORDS = ["delete", "remove", "rmdir", "unlink", "drop", "truncate", "format", "wipe"]
    PHONE_ACTIONS = ["OPEN_URL", "VIEW_VIDEO", "LAUNCH_APP", "MUTE", "UNMUTE", "SET_VOLUME", "MAX_VOLUME", "VIBRATE"]

    def validate_action(self, action_payload: Dict[str, Any]) -> ActionRequest:
        """Validates incoming action payload against ActionRequest schema."""
        try:
            request = ActionRequest(**action_payload)
            # Auto-detect destructive intent if target or parameters contain destructive keywords
            if any(kw in request.action_type.lower() or kw in request.target.lower() for kw in self.DESTRUCTIVE_KEYWORDS):
                request.is_destructive = True
            return request
        except ValidationError as e:
            logger.error(f"Action validation failed: {e}")
            raise ValueError(f"Invalid tool action schema: {e}")

    def is_action_allowed(self, request: ActionRequest, user_confirmed: bool = False) -> bool:
        """Determines if action is allowed to execute based on confirmation locks."""
        # 1. Master AI Enable Check
        if not settings.is_ai_enabled:
            logger.warning("BLOCKED: Local AI Engine is turned OFF in permission settings.")
            return False

        # 2. Phone Bridge Permission Lock Gate
        if request.action_type in self.PHONE_ACTIONS and not settings.is_phone_bridge_allowed:
            logger.warning(f"BLOCKED: Phone action '{request.action_type}' blocked because Phone Bridge Permission is LOCKED.")
            return False

        # 3. Destructive Action Authorization Check
        if request.is_destructive and settings.require_confirmation_for_destruction:
            if not user_confirmed:
                logger.warning(f"BLOCKED: Destructive action '{request.action_type}' on '{request.target}' requires user confirmation.")
                return False

        logger.info(f"APPROVED: Action '{request.action_type}' on '{request.target}' passed safety verification.")
        return True

    def check_phone_permission(self) -> bool:
        """Checks whether phone bridge actions are currently allowed."""
        return settings.is_phone_bridge_allowed and settings.is_ai_enabled
