import unittest
from personalai.orchestration import PersonalAIAgentOrchestrator
from personalai.inference import LocalInferenceEngine


class TestOrchestration(unittest.TestCase):
    def test_agent_orchestrator_config(self):
        orchestrator = PersonalAIAgentOrchestrator(model="llama3.1:8b")
        config = orchestrator.build_agent_config()
        self.assertEqual(config.model, "llama3.1:8b")
        self.assertEqual(config.base_url, "http://127.0.0.1:11434/v1")
        self.assertIn("zero-leak", config.system_instruction)

    def test_local_inference_security_flags(self):
        engine = LocalInferenceEngine()
        flags = engine.get_env_security_flags()
        self.assertEqual(flags["OLLAMA_ORIGINS"], "")
        self.assertEqual(flags["OLLAMA_HOST"], "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
