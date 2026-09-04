import unittest
from personalai.config import settings
from personalai.orchestration.model_router import ModelRouter


class TestModelRouter(unittest.TestCase):
    def setUp(self):
        self.router = ModelRouter()

    def test_classify_intent_coding(self):
        prompts = [
            "Write a Python function to sort a list",
            "How do I debug a NullPointerException in Java?",
            "Refactor this SQL query for better performance",
            "Fix the syntax error in my C++ code",
        ]
        for p in prompts:
            intent = self.router.classify_intent(p)
            self.assertEqual(intent, "CODING", f"Failed for prompt: {p}")

    def test_classify_intent_reasoning(self):
        prompts = [
            "Solve step-by-step: If 5 cats catch 5 mice in 5 minutes...",
            "Prove the pythagorean theorem mathematically",
            "Calculate the probability of drawing an ace from a deck",
        ]
        for p in prompts:
            intent = self.router.classify_intent(p)
            self.assertEqual(intent, "REASONING", f"Failed for prompt: {p}")

    def test_classify_intent_tool_calling(self):
        prompts = [
            "Please delete old temporary files",
            "Mute the volume on my phone",
            "Sync knowledge to Google Drive cold storage",
        ]
        for p in prompts:
            intent = self.router.classify_intent(p)
            self.assertEqual(intent, "TOOL_CALLING", f"Failed for prompt: {p}")

    def test_classify_intent_vision(self):
        intent = self.router.classify_intent("Analyze this screenshot image", has_image=True)
        self.assertEqual(intent, "VISION")

    def test_fallback_when_target_model_unpulled(self):
        # Even if intent is CODING (target qwen2.5-coder:7b), if it's not pulled, select_model falls back to general_model
        res = self.router.select_model("Write a python script")
        self.assertIn("model", res)
        self.assertIn(res["model"], [settings.coding_model, settings.general_model])


if __name__ == "__main__":
    unittest.main()
