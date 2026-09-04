import unittest
from personalai.security import SecurityValidator, ActionRequest


class TestSecurity(unittest.TestCase):
    def test_security_validator_safe_action(self):
        validator = SecurityValidator()
        payload = {
            "action_type": "READ_FILE",
            "target": "notes.md",
            "parameters": {},
            "is_destructive": False,
        }
        request = validator.validate_action(payload)
        self.assertFalse(request.is_destructive)
        self.assertTrue(validator.is_action_allowed(request))

    def test_security_validator_destructive_action(self):
        validator = SecurityValidator()
        payload = {
            "action_type": "FILE_DELETE",
            "target": "critical_database.sqlite",
            "parameters": {},
        }
        request = validator.validate_action(payload)
        self.assertTrue(request.is_destructive)

        # Without user confirmation, destructive action must be blocked
        self.assertFalse(validator.is_action_allowed(request, user_confirmed=False))
        # With user confirmation, destructive action is approved
        self.assertTrue(validator.is_action_allowed(request, user_confirmed=True))


if __name__ == "__main__":
    unittest.main()
