import asyncio
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Optional
from personalai.config import settings
from personalai.gui.tokens import THEMES, CSS_VARIABLES
from personalai.inference import LocalInferenceEngine
from personalai.rag import LocalVectorStore
from personalai.orchestration import PersonalAIAgentOrchestrator
from personalai.security import SecurityValidator


class PersonalAIGUIApp:
    """Modern Fintech Desktop GUI Application for Personal AI System."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Personal AI System - Fintech Edition")
        self.root.geometry("1100x750")
        self.root.minsize(950, 650)

        self.orchestrator = PersonalAIAgentOrchestrator()
        self.validator = SecurityValidator()

        self.theme_name = settings.active_theme
        self.theme = THEMES[self.theme_name]

        self.persona_prompts = {
            "Default Zero-Leak AI": (
                "You are a production-grade, zero-leak personal AI assistant running entirely on local silicon.\n"
                "Strict rules:\n1. NEVER attempt external cloud calls.\n2. Utilize local RAG context."
            ),
            "The Mentor / Teacher 🎓": (
                "You are an encouraging, structured Mentor and Teacher during exam preparation.\n"
                "Break down complex topics step-by-step, quiz the user, and keep them focused on their study goals."
            ),
            "Tony (Senior Software Engineer) 💻": (
                "You are Tony, a veteran Senior Software Engineer and Tech Lead.\n"
                "Critique the user's code against industry standards, identify potential failure points, "
                "point out architectural mistakes, and enforce clean coding principles."
            ),
        }
        self.selected_persona = "Default Zero-Leak AI"

        self._setup_ui()
        self.apply_theme()

    def _setup_ui(self):
        """Constructs the desktop GUI layout."""
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # 1. Header Bar
        self.header_frame = tk.Frame(self.main_container, height=60, padx=10, pady=10)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)

        self.title_label = tk.Label(
            self.header_frame,
            text="Personal AI System",
            font=("Segoe UI", 16, "bold"),
        )
        self.title_label.pack(side=tk.LEFT, padx=15)

        self.subtitle_label = tk.Label(
            self.header_frame,
            text="Zero-Leak Local Silicon Edition",
            font=("Segoe UI", 10, "italic"),
        )
        self.subtitle_label.pack(side=tk.LEFT, padx=5)

        # Theme Switcher Button
        self.theme_btn = tk.Button(
            self.header_frame,
            text="🌙 Dark Mode" if self.theme_name == "dark" else "☀️ Light Mode",
            command=self.toggle_theme,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=4,
        )
        self.theme_btn.pack(side=tk.RIGHT, padx=15)

        # 2. Main Content Split View (Left Sidebar + Right Panel)
        self.body_frame = tk.Frame(self.main_container)
        self.body_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Left Sidebar (Security Panel, Persona Selector, Fintech Widgets)
        self.left_sidebar = tk.Frame(self.body_frame, width=360)
        self.left_sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Right Panel (Chat & RAG File Ingestion)
        self.right_panel = tk.Frame(self.body_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_security_card()
        self._build_persona_card()
        self._build_fintech_widgets_card()
        self._build_chat_panel()

    def _build_security_card(self):
        """Builds Security & Permission Control Panel with rounded aesthetics."""
        self.sec_card = tk.LabelFrame(
            self.left_sidebar,
            text=" 🛡️ Security & Permission Control ",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=10,
        )
        self.sec_card.pack(fill=tk.X, pady=(0, 10))

        # Toggle 1: Local AI Engine
        self.ai_var = tk.BooleanVar(value=settings.is_ai_enabled)
        self.ai_check = tk.Checkbutton(
            self.sec_card,
            text="Local AI Engine (ON / OFF)",
            variable=self.ai_var,
            command=self._on_ai_toggle,
            font=("Segoe UI", 10, "bold"),
        )
        self.ai_check.pack(anchor=tk.W, pady=4)

        # Toggle 2: Phone Bridge Lock
        self.phone_var = tk.BooleanVar(value=settings.is_phone_bridge_allowed)
        self.phone_check = tk.Checkbutton(
            self.sec_card,
            text="P2P Phone Bridge Permission (ALLOWED / LOCKED)",
            variable=self.phone_var,
            command=self._on_phone_toggle,
            font=("Segoe UI", 10, "bold"),
        )
        self.phone_check.pack(anchor=tk.W, pady=4)

        self.sec_note = tk.Label(
            self.sec_card,
            text="* Locked status blocks all phone intents when family uses laptop.",
            font=("Segoe UI", 8, "italic"),
            wraplength=320,
            justify=tk.LEFT,
        )
        self.sec_note.pack(anchor=tk.W, pady=(2, 0))

    def _build_persona_card(self):
        """Builds Active Persona Mode selector."""
        self.persona_card = tk.LabelFrame(
            self.left_sidebar,
            text=" 🎭 Active Persona Mode ",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=10,
        )
        self.persona_card.pack(fill=tk.X, pady=(0, 10))

        self.persona_var = tk.StringVar(value=self.selected_persona)
        self.persona_dropdown = ttk.Combobox(
            self.persona_card,
            textvariable=self.persona_var,
            values=list(self.persona_prompts.keys()),
            state="readonly",
            font=("Segoe UI", 9, "bold"),
        )
        self.persona_dropdown.pack(fill=tk.X, pady=4)
        self.persona_dropdown.bind("<<ComboboxSelected>>", self._on_persona_change)

    def _build_fintech_widgets_card(self):
        """Builds Fintech Dashboard Analytics & Data Flow Widgets."""
        self.widget_card = tk.LabelFrame(
            self.left_sidebar,
            text=" 📊 System Analytics & Data Flow ",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=10,
        )
        self.widget_card.pack(fill=tk.BOTH, expand=True)

        # 1. Resource / Spending Limit Progress Bar
        tk.Label(self.widget_card, text="Memory & Context Capacity (74%)", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.progress = ttk.Progressbar(self.widget_card, length=300, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(2, 10))
        self.progress["value"] = 74

        # 2. Donut & Flow Canvas
        self.chart_canvas = tk.Canvas(self.widget_card, height=140, bg=self.theme["card_surface"], highlightthickness=0)
        self.chart_canvas.pack(fill=tk.X, pady=5)
        self._draw_widgets()

    def _draw_widgets(self):
        """Renders expense breakdown donut chart and Sankey flow diagram on canvas."""
        self.chart_canvas.delete("all")
        bg = self.theme["card_surface"]
        orange = self.theme["accent_secondary"]
        blue = self.theme["accent_primary"]
        text_color = self.theme["text_primary"]

        self.chart_canvas.configure(bg=bg)

        # Donut Chart (Left)
        # Outer arc
        self.chart_canvas.create_arc(15, 15, 105, 105, start=0, extent=240, fill=orange, outline="")
        self.chart_canvas.create_arc(15, 15, 105, 105, start=240, extent=120, fill=blue, outline="")
        # Inner cutout
        self.chart_canvas.create_oval(35, 35, 85, 85, fill=bg, outline="")
        self.chart_canvas.create_text(60, 60, text="75%", fill=text_color, font=("Segoe UI", 9, "bold"))
        self.chart_canvas.create_text(60, 120, text="Allocation", fill=text_color, font=("Segoe UI", 8))

        # Sankey Dual-Stream Flow Representation (Right)
        # Flow 1 (Income -> RAG)
        self.chart_canvas.create_line(140, 30, 220, 50, 280, 40, fill=blue, width=4, smooth=True)
        # Flow 2 (Credit -> Local Storage)
        self.chart_canvas.create_line(140, 90, 200, 70, 280, 85, fill=orange, width=4, smooth=True)

        self.chart_canvas.create_text(210, 20, text="Income Flow", fill=text_color, font=("Segoe UI", 8, "bold"))
        self.chart_canvas.create_text(210, 105, text="Credit Expense", fill=text_color, font=("Segoe UI", 8, "bold"))

    def _build_chat_panel(self):
        """Builds Right Panel containing Interactive RAG Chat Display & Document Ingestion Controls."""
        self.chat_card = tk.LabelFrame(
            self.right_panel,
            text=" 💬 Interactive Zero-Leak RAG Shell ",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=10,
        )
        self.chat_card.pack(fill=tk.BOTH, expand=True)

        # Top Bar: Ingest Document Button
        self.ingest_bar = tk.Frame(self.chat_card)
        self.ingest_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 8))

        self.ingest_btn = tk.Button(
            self.ingest_bar,
            text="📄 Ingest Document (.md, .txt, .pdf)",
            command=self._on_ingest_file,
            font=("Segoe UI", 9, "bold"),
            relief=tk.RAISED,
            padx=8,
            pady=3,
        )
        self.ingest_btn.pack(side=tk.LEFT)

        self.clear_btn = tk.Button(
            self.ingest_bar,
            text="🗑️ Clear Chat",
            command=self._clear_chat,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=8,
            pady=3,
        )
        self.clear_btn.pack(side=tk.RIGHT)

        # Chat Text Bubble Display
        self.chat_text = tk.Text(
            self.chat_card,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            state=tk.DISABLED,
            padx=10,
            pady=10,
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Bottom Entry Frame
        self.input_frame = tk.Frame(self.chat_card)
        self.input_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.prompt_entry = tk.Entry(self.input_frame, font=("Segoe UI", 10))
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=4)
        self.prompt_entry.bind("<Return>", lambda e: self._send_prompt())

        self.send_btn = tk.Button(
            self.input_frame,
            text="Send Prompt 🚀",
            command=self._send_prompt,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=4,
        )
        self.send_btn.pack(side=tk.RIGHT)

    def _on_ai_toggle(self):
        settings.is_ai_enabled = self.ai_var.get()
        status = "ENABLED" if settings.is_ai_enabled else "DISABLED"
        self._append_system_msg(f"Security Update: Local AI Engine is now {status}.")

    def _on_phone_toggle(self):
        settings.is_phone_bridge_allowed = self.phone_var.get()
        status = "ALLOWED" if settings.is_phone_bridge_allowed else "LOCKED (Owner Protected)"
        self._append_system_msg(f"Security Update: P2P Phone Bridge Permission is now {status}.")

    def _on_persona_change(self, event=None):
        self.selected_persona = self.persona_var.get()
        self._append_system_msg(f"Persona Switched: Active Mode is now '{self.selected_persona}'.")

    def _on_ingest_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Knowledge File to Ingest",
            filetypes=[("Documents", "*.md *.txt *.pdf"), ("All Files", "*.*")],
        )
        if file_path:
            path = Path(file_path)
            store = LocalVectorStore()
            from personalai.cli import _read_file_text
            text = _read_file_text(path)
            if text:
                store.ingest_documents([{"id": path.name, "text": text, "metadata": {"source": str(path)}}])
                messagebox.showinfo("Ingestion Success", f"Successfully ingested {path.name} into local RAG vector store!")
                self._append_system_msg(f"Ingested '{path.name}' into RAG Memory.")

    def _send_prompt(self):
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            return

        self.prompt_entry.delete(0, tk.END)
        self._append_chat_msg("You", prompt, is_user=True)

        if not settings.is_ai_enabled:
            self._append_chat_msg("Security Gate", "BLOCKED: Local AI Engine is turned OFF in Security Controls.", is_user=False)
            return

        def run_in_bg():
            custom_instruction = self.persona_prompts[self.selected_persona]
            config = self.orchestrator.build_agent_config()
            config.system_instruction = custom_instruction

            res = asyncio.run(self.orchestrator.execute_query(prompt))
            self.root.after(0, lambda: self._append_chat_msg("Personal AI", res["response"], citations=res.get("citations"), is_user=False))

        threading.Thread(target=run_in_bg, daemon=True).start()

    def _append_chat_msg(self, sender: str, text: str, citations=None, is_user: bool = False):
        self.chat_text.config(state=tk.NORMAL)
        prefix = f"\n{sender} >\n"
        self.chat_text.insert(tk.END, prefix, "bold_tag")
        self.chat_text.insert(tk.END, text + "\n")
        if citations:
            self.chat_text.insert(tk.END, f"Citations: {citations}\n", "dim_tag")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def _append_system_msg(self, msg: str):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"\n[System] {msg}\n", "sys_tag")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def _clear_chat(self):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.DISABLED)

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        settings.active_theme = self.theme_name
        self.theme = THEMES[self.theme_name]
        self.theme_btn.config(text="🌙 Dark Mode" if self.theme_name == "dark" else "☀️ Light Mode")
        self.apply_theme()

    def apply_theme(self):
        """Applies Light or Dark theme colors to all widgets."""
        t = self.theme
        self.root.configure(bg=t["bg_canvas"])
        self.main_container.configure(bg=t["bg_canvas"])
        self.header_frame.configure(bg=t["card_surface"])
        self.title_label.configure(bg=t["card_surface"], fg=t["text_primary"])
        self.subtitle_label.configure(bg=t["card_surface"], fg=t["text_muted"])
        self.theme_btn.configure(bg=t["accent_primary"], fg="#FFFFFF")

        self.body_frame.configure(bg=t["bg_canvas"])
        self.left_sidebar.configure(bg=t["bg_canvas"])
        self.right_panel.configure(bg=t["bg_canvas"])

        # Security Card
        self.sec_card.configure(bg=t["card_surface"], fg=t["text_primary"])
        self.ai_check.configure(bg=t["card_surface"], fg=t["text_primary"], selectcolor=t["card_surface"])
        self.phone_check.configure(bg=t["card_surface"], fg=t["text_primary"], selectcolor=t["card_surface"])
        self.sec_note.configure(bg=t["card_surface"], fg=t["text_muted"])

        # Persona Card
        self.persona_card.configure(bg=t["card_surface"], fg=t["text_primary"])

        # Widget Card
        self.widget_card.configure(bg=t["card_surface"], fg=t["text_primary"])
        self._draw_widgets()

        # Chat Card
        self.chat_card.configure(bg=t["card_surface"], fg=t["text_primary"])
        self.ingest_bar.configure(bg=t["card_surface"])
        self.ingest_btn.configure(bg=t["accent_primary"], fg="#FFFFFF")
        self.clear_btn.configure(bg=t["card_surface"], fg=t["text_muted"])

        self.chat_text.configure(bg=t["card_surface"], fg=t["text_primary"], insertbackground=t["text_primary"])
        self.chat_text.tag_config("bold_tag", font=("Segoe UI", 10, "bold"), foreground=t["accent_primary"])
        self.chat_text.tag_config("dim_tag", font=("Segoe UI", 9, "italic"), foreground=t["text_muted"])
        self.chat_text.tag_config("sys_tag", font=("Segoe UI", 9, "italic"), foreground=t["accent_secondary"])

        self.input_frame.configure(bg=t["card_surface"])
        self.prompt_entry.configure(bg=t["card_surface"], fg=t["text_primary"], insertbackground=t["text_primary"])
        self.send_btn.configure(bg=t["accent_primary"], fg="#FFFFFF")


def launch_gui():
    """Launches the Personal AI Desktop Application GUI."""
    root = tk.Tk()
    app = PersonalAIGUIApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
