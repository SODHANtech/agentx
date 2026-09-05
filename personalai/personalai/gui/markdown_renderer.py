import re
import tkinter as tk
from typing import Dict, Any, Optional, List


class TkinterMarkdownRenderer:
    """Renders formatted Markdown and collapsible trace accordions inside Tkinter Text widgets."""

    def __init__(self, text_widget: tk.Text, theme: Dict[str, Any]):
        self.text_widget = text_widget
        self.theme = theme
        self.accordion_count = 0
        self._configure_tags()

    def _configure_tags(self):
        """Configures font, color, margin, and layout tags on the Tkinter Text widget."""
        t = self.theme
        w = self.text_widget

        # Headings
        w.tag_config("h1", font=("Segoe UI", 14, "bold"), foreground=t["accent_primary"], spacing1=6, spacing3=4)
        w.tag_config("h2", font=("Segoe UI", 12, "bold"), foreground=t["text_primary"], spacing1=5, spacing3=3)
        w.tag_config("h3", font=("Segoe UI", 10, "bold"), foreground=t["accent_secondary"], spacing1=4, spacing3=2)

        # Inline formatting
        w.tag_config("bold", font=("Segoe UI", 10, "bold"), foreground=t["text_primary"])
        w.tag_config("italic", font=("Segoe UI", 10, "italic"), foreground=t["text_muted"])
        w.tag_config("inline_code", font=("Consolas", 9, "bold"), background=t["code_bg"], foreground=t["accent_primary"])
        w.tag_config("normal", font=("Segoe UI", 10), foreground=t["text_primary"])

        # Code block
        w.tag_config("code_block", font=("Consolas", 9), background=t["code_bg"], foreground=t["code_text"], lmargin1=15, lmargin2=15, rmargin=15, spacing1=4, spacing3=4)

        # Bullet list
        w.tag_config("bullet", font=("Segoe UI", 10), foreground=t["text_primary"], lmargin1=15, lmargin2=25)

        # Trace Accordion tags
        w.tag_config("trace_header", font=("Segoe UI", 9, "bold"), background=t["trace_bg"], foreground=t["trace_fg"], lmargin1=10, lmargin2=10, rmargin=10, spacing1=4, spacing3=4)
        w.tag_config("trace_body", font=("Consolas", 8), background=t["code_bg"], foreground=t["text_muted"], lmargin1=20, lmargin2=20, rmargin=20, spacing1=2, spacing3=2)

        # Speech Bubbles
        w.tag_config("user_header", font=("Segoe UI", 10, "bold"), foreground=t["accent_primary"], spacing1=8)
        w.tag_config("thinking_tag", font=("Segoe UI", 9, "italic"), foreground=t["accent_secondary"], spacing1=4, spacing3=4)

    def update_theme(self, theme: Dict[str, Any]):
        self.theme = theme
        self._configure_tags()

    def render_thinking_bubble(self, sender: str = "Personal AI") -> str:
        """Appends a temporary thinking indicator bubble to show active processing."""
        w = self.text_widget
        w.config(state=tk.NORMAL)
        start_mark = w.index(tk.END + "-1c")
        w.insert(tk.END, f"\n🤖 {sender}\n", "ai_header")
        w.insert(tk.END, "⏳ Thinking... Running RAG search & local AI model inference...\n", "thinking_tag")
        w.config(state=tk.DISABLED)
        w.see(tk.END)
        return start_mark

    def remove_thinking_bubble(self, start_mark: str):
        """Removes the temporary thinking indicator bubble."""
        w = self.text_widget
        w.config(state=tk.NORMAL)
        try:
            w.delete(start_mark, tk.END)
        except Exception:
            pass
        w.config(state=tk.DISABLED)

    def render_message(self, sender: str, text: str, citations: Optional[List[str]] = None, is_user: bool = False):
        """Appends a styled speech bubble with Markdown parsing and collapsible RAG trace accordions."""
        w = self.text_widget
        w.config(state=tk.NORMAL)

        # 1. Sender Header
        if is_user:
            w.insert(tk.END, f"\n👤 {sender}\n", "user_header")
        elif sender.lower() == "system":
            w.insert(tk.END, f"\n⚙️ {sender}\n", "system_header")
        else:
            w.insert(tk.END, f"\n🤖 {sender}\n", "ai_header")


        # 2. Extract and format collapsible RAG citations trace if present
        cleaned_text = text
        retrieved_context_block = ""

        if "### Retrieved Knowledge Context:" in cleaned_text:
            parts = cleaned_text.split("### Retrieved Knowledge Context:")
            prefix = parts[0]
            context_and_rest = parts[1]
            
            # Find end of retrieved knowledge block
            if "\n### " in context_and_rest:
                subparts = context_and_rest.split("\n### ", 1)
                retrieved_context_block = "### Retrieved Knowledge Context:" + subparts[0]
                cleaned_text = prefix + "\n### " + subparts[1]
            else:
                retrieved_context_block = "### Retrieved Knowledge Context:" + context_and_rest
                cleaned_text = prefix

        # Insert collapsible trace accordion if RAG citations or traces exist
        if citations or retrieved_context_block:
            self._insert_trace_accordion(citations=citations, trace_text=retrieved_context_block)

        # 3. Parse and insert main body text as Markdown
        self._render_markdown_body(cleaned_text.strip())
        w.insert(tk.END, "\n")

        w.config(state=tk.DISABLED)
        w.see(tk.END)

    def _insert_trace_accordion(self, citations: Optional[List[str]] = None, trace_text: str = ""):
        """Inserts an interactive collapsible accordion widget inside the Tkinter text stream."""
        w = self.text_widget
        self.accordion_count += 1
        acc_id = f"acc_{self.accordion_count}"
        
        n_sources = len(citations) if citations else (trace_text.count("Source:") or 1)
        header_title = f" [ ▶ {n_sources} Source(s) & Internal RAG Traces Retrieved ] "

        # Collapsible state frame
        body_visible = [False]

        # Embedded frame container
        frame = tk.Frame(w, bg=self.theme["trace_bg"], bd=1, relief=tk.FLAT)
        
        # Toggle Button
        toggle_btn = tk.Button(
            frame,
            text=f"▶ {n_sources} Source(s) & RAG Traces Retrieved",
            font=("Segoe UI", 9, "bold"),
            bg=self.theme["trace_bg"],
            fg=self.theme["trace_fg"],
            activebackground=self.theme["trace_bg"],
            activeforeground=self.theme["accent_primary"],
            relief=tk.FLAT,
            anchor=tk.W,
            cursor="hand2",
            padx=8,
            pady=3,
        )
        toggle_btn.pack(fill=tk.X, expand=True)

        # Body Frame (Hidden by default)
        body_frame = tk.Frame(frame, bg=self.theme["code_bg"], padx=10, pady=8)
        
        body_label_text = ""
        if citations:
            body_label_text += f"Citations: {citations}\n\n"
        if trace_text:
            body_label_text += trace_text.strip()

        body_lbl = tk.Label(
            body_frame,
            text=body_label_text,
            font=("Consolas", 8),
            bg=self.theme["code_bg"],
            fg=self.theme["text_muted"],
            justify=tk.LEFT,
            wraplength=600,
            anchor=tk.W,
        )
        body_lbl.pack(fill=tk.BOTH, expand=True)

        def toggle_body():
            if body_visible[0]:
                body_frame.pack_forget()
                toggle_btn.config(text=f"▶ {n_sources} Source(s) & RAG Traces Retrieved")
                body_visible[0] = False
            else:
                body_frame.pack(fill=tk.X, expand=True, pady=(4, 0))
                toggle_btn.config(text=f"▼ {n_sources} Source(s) & RAG Traces (Click to Hide)")
                body_visible[0] = True

        toggle_btn.config(command=toggle_body)

        w.insert(tk.END, "\n")
        w.window_create(tk.END, window=frame)
        w.insert(tk.END, "\n")

    def _render_markdown_body(self, text: str):
        """Parses headers, code blocks, lists, and inline formatting into text tags."""
        w = self.text_widget
        lines = text.splitlines()
        in_code_block = False
        code_lines = []

        for line in lines:
            # Code block toggle
            if line.startswith("```"):
                if in_code_block:
                    # End code block
                    code_text = "\n".join(code_lines)
                    w.insert(tk.END, code_text + "\n", "code_block")
                    code_lines = []
                    in_code_block = False
                else:
                    # Start code block
                    in_code_block = True
                    code_lines = []
                continue

            if in_code_block:
                code_lines.append(line)
                continue

            # Headers
            if line.startswith("# "):
                w.insert(tk.END, line[2:] + "\n", "h1")
            elif line.startswith("## "):
                w.insert(tk.END, line[3:] + "\n", "h2")
            elif line.startswith("### "):
                w.insert(tk.END, line[4:] + "\n", "h3")
            elif line.startswith("* ") or line.startswith("- "):
                w.insert(tk.END, "• ", "bold")
                self._render_inline_formatting(line[2:] + "\n")
            else:
                self._render_inline_formatting(line + "\n")

        if in_code_block and code_lines:
            w.insert(tk.END, "\n".join(code_lines) + "\n", "code_block")

    def _render_inline_formatting(self, line: str):
        """Parses bold (**), italic (*), and inline code (`) within a line."""
        w = self.text_widget
        # Pattern matching for **bold**, *italic*, and `code`
        pattern = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)")
        parts = pattern.split(line)

        for part in parts:
            if not part:
                continue
            if part.startswith("**") and part.endswith("**") and len(part) > 4:
                w.insert(tk.END, part[2:-2], "bold")
            elif part.startswith("*") and part.endswith("*") and len(part) > 2:
                w.insert(tk.END, part[1:-1], "italic")
            elif part.startswith("`") and part.endswith("`") and len(part) > 2:
                w.insert(tk.END, part[1:-1], "inline_code")
            else:
                w.insert(tk.END, part, "normal")
