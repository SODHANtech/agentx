import unittest
import tkinter as tk
from personalai.gui.tokens import THEMES
from personalai.gui.markdown_renderer import TkinterMarkdownRenderer


class TestGUIMarkdownRenderer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()  # Hide window during test execution
        except Exception as e:
            cls.root = None

    @classmethod
    def tearDownClass(cls):
        if cls.root:
            cls.root.destroy()

    def test_theme_tokens_definition(self):
        self.assertIn("dark", THEMES)
        self.assertIn("light", THEMES)
        dark = THEMES["dark"]
        self.assertIn("bg_canvas", dark)
        self.assertIn("user_bubble", dark)
        self.assertIn("ai_bubble", dark)
        self.assertIn("trace_bg", dark)

    def test_markdown_rendering(self):
        if not self.root:
            self.skipTest("Tkinter display not available in headless mode")

        text_widget = tk.Text(self.root)
        renderer = TkinterMarkdownRenderer(text_widget, THEMES["dark"])

        sample_response = (
            "### Retrieved Knowledge Context:\n"
            "**[1] Source: `main.py` (Lines 10-25)**\n"
            "Sample RAG text\n"
            "### Overview\n"
            "Here is **bold text** and `inline_code`.\n"
            "```python\n"
            "print('Hello World')\n"
            "```"
        )

        renderer.render_message("Personal AI", sample_response, citations=["main.py"], is_user=False)
        content = text_widget.get("1.0", tk.END)
        self.assertIn("🤖 Personal AI", content)
        self.assertIn("Overview", content)
        self.assertIn("print('Hello World')", content)


if __name__ == "__main__":
    unittest.main()
