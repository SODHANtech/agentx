import unittest
from personalai.config import settings
from personalai.security import SecurityValidator, ActionRequest


class TestGUIPermissions(unittest.TestCase):
    def setUp(self):
        # Save original permission states
        self.orig_ai = settings.is_ai_enabled
        self.orig_phone = settings.is_phone_bridge_allowed

    def tearDown(self):
        # Restore permission states
        settings.is_ai_enabled = self.orig_ai
        settings.is_phone_bridge_allowed = self.orig_phone

    def test_phone_bridge_locked_by_default(self):
        validator = SecurityValidator()
        settings.is_ai_enabled = True
        settings.is_phone_bridge_allowed = False  # LOCKED

        req = ActionRequest(action_type="OPEN_URL", target="https://youtube.com")
        self.assertFalse(validator.is_action_allowed(req))

    def test_phone_bridge_allowed_when_toggled_on(self):
        validator = SecurityValidator()
        settings.is_ai_enabled = True
        settings.is_phone_bridge_allowed = True  # ALLOWED

        req = ActionRequest(action_type="OPEN_URL", target="https://youtube.com")
        self.assertTrue(validator.is_action_allowed(req))

    def test_ai_disabled_blocks_all_actions(self):
        validator = SecurityValidator()
        settings.is_ai_enabled = False  # OFF
        settings.is_phone_bridge_allowed = True

        req = ActionRequest(action_type="OPEN_URL", target="https://youtube.com")
        self.assertFalse(validator.is_action_allowed(req))


if __name__ == "__main__":
    unittest.main()
