import asyncio
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Optional
from pathlib import Path

from personalai.config import settings
from personalai.gui.tokens import THEMES
from personalai.gui.markdown_renderer import TkinterMarkdownRenderer
from personalai.inference import LocalInferenceEngine
from personalai.rag import LocalVectorStore
from personalai.orchestration import PersonalAIAgentOrchestrator
from personalai.security import SecurityValidator


class SettingsDialog(tk.Toplevel):
    """Dedicated Modal Dialog for Granular Security Permissions and Persona Configurations."""

    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.title("⚙️ System Security & Persona Settings")
        self.geometry("520x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.theme = self.app.theme
        self.configure(bg=self.theme["bg_canvas"])

        self._build_ui()

    def _build_ui(self):
        t = self.theme

        # Container card
        card = tk.Frame(self, bg=t["card_surface"], padx=20, pady=20, highlightthickness=1, highlightbackground=t["card_border"])
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Title
        title_lbl = tk.Label(card, text="Security & Persona Controls", font=("Segoe UI", 13, "bold"), bg=t["card_surface"], fg=t["text_primary"])
        title_lbl.pack(anchor=tk.W, pady=(0, 15))

        # 1. Local AI Engine Toggle
        self.ai_var = tk.BooleanVar(value=settings.is_ai_enabled)
        ai_check = tk.Checkbutton(
            card,
            text="Local AI Inference Engine (ON / OFF)",
            variable=self.ai_var,
            font=("Segoe UI", 10, "bold"),
            bg=t["card_surface"],
            fg=t["text_primary"],
            selectcolor=t["card_surface"],
        )
        ai_check.pack(anchor=tk.W, pady=6)

        ai_note = tk.Label(card, text="Disabling halts all local inference execution across hardware.", font=("Segoe UI", 8, "italic"), bg=t["card_surface"], fg=t["text_muted"])
        ai_note.pack(anchor=tk.W, pady=(0, 10))

        # 2. P2P Phone Bridge Permission
        self.phone_var = tk.BooleanVar(value=settings.is_phone_bridge_allowed)
        phone_check = tk.Checkbutton(
            card,
            text="P2P Phone Bridge Permission (ALLOWED / LOCKED)",
            variable=self.phone_var,
            font=("Segoe UI", 10, "bold"),
            bg=t["card_surface"],
            fg=t["text_primary"],
            selectcolor=t["card_surface"],
        )
        phone_check.pack(anchor=tk.W, pady=6)

        phone_note = tk.Label(card, text="Locked status blocks all Termux phone intents when family uses laptop.", font=("Segoe UI", 8, "italic"), bg=t["card_surface"], fg=t["text_muted"])
        phone_note.pack(anchor=tk.W, pady=(0, 15))

        # 3. Persona Selector
        persona_lbl = tk.Label(card, text="Active Persona Mode", font=("Segoe UI", 10, "bold"), bg=t["card_surface"], fg=t["text_primary"])
        persona_lbl.pack(anchor=tk.W, pady=(0, 4))

        self.persona_var = tk.StringVar(value=self.app.selected_persona)
        persona_dropdown = ttk.Combobox(
            card,
            textvariable=self.persona_var,
            values=list(self.app.persona_prompts.keys()),
            state="readonly",
            font=("Segoe UI", 9, "bold"),
        )
        persona_dropdown.pack(fill=tk.X, pady=(0, 20))

        # Save Button
        save_btn = tk.Button(
            card,
            text="Save Settings & Apply",
            command=self._save,
            font=("Segoe UI", 10, "bold"),
            bg=t["accent_primary"],
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=15,
            pady=6,
            cursor="hand2",
        )
        save_btn.pack(side=tk.RIGHT)

    def _save(self):
        settings.is_ai_enabled = self.ai_var.get()
        settings.is_phone_bridge_allowed = self.phone_var.get()
        self.app.selected_persona = self.persona_var.get()

        self.app.update_sidebar_sec_buttons()
        self.app.renderer.render_message("System", f"Settings Updated: AI Engine={settings.is_ai_enabled}, Phone Bridge={settings.is_phone_bridge_allowed}, Persona='{self.app.selected_persona}'.", is_user=False)
        self.destroy()



class PersonalAIGUIApp:
    """Contemporary Slate Glassmorphic Desktop Application for Personal AI System."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Personal AI System - Zero-Leak Local Silicon Edition")
        self.root.geometry("1150x780")
        self.root.minsize(980, 680)

        self.orchestrator = PersonalAIAgentOrchestrator()
        self.validator = SecurityValidator()

        self.theme_name = settings.active_theme
        self.theme = THEMES.get(self.theme_name, THEMES["dark"])

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
        self.sidebar_collapsed = False

        self._setup_ui()
        self.apply_theme()
        self._update_rag_badge()

    def _setup_ui(self):
        """Constructs the contemporary layout."""
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # 1. Header Bar
        self.header_frame = tk.Frame(self.main_container, height=60, padx=15, pady=10)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)

        self.title_label = tk.Label(
            self.header_frame,
            text="Personal AI System",
            font=("Segoe UI", 16, "bold"),
        )
        self.title_label.pack(side=tk.LEFT, padx=(5, 10))

        self.subtitle_label = tk.Label(
            self.header_frame,
            text="Zero-Leak Local Silicon Edition",
            font=("Segoe UI", 9, "italic"),
        )
        self.subtitle_label.pack(side=tk.LEFT, padx=5)

        # RAG Memory Badge
        self.rag_badge = tk.Label(
            self.header_frame,
            text="⚡ RAG Memory: Initializing...",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=3,
        )
        self.rag_badge.pack(side=tk.LEFT, padx=15)

        # Settings ⚙️ Button
        self.settings_btn = tk.Button(
            self.header_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.settings_btn.pack(side=tk.RIGHT, padx=5)

        # Theme Switcher Button
        self.theme_btn = tk.Button(
            self.header_frame,
            text="🌙 Dark" if self.theme_name == "dark" else "☀️ Light",
            command=self.toggle_theme,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.theme_btn.pack(side=tk.RIGHT, padx=5)

        # 2. Main Content Split View (Left Collapsible Sidebar + Right Panel)
        self.body_frame = tk.Frame(self.main_container)
        self.body_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Left Sidebar (Collapsible Drawer)
        self.left_sidebar = tk.Frame(self.body_frame, width=340)
        self.left_sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Sidebar Toggle Bar
        self.sidebar_toggle_bar = tk.Frame(self.left_sidebar)
        self.sidebar_toggle_bar.pack(fill=tk.X, pady=(0, 8))

        self.drawer_toggle_btn = tk.Button(
            self.sidebar_toggle_bar,
            text="◀ Drawer",
            command=self.toggle_sidebar,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2",
        )
        self.drawer_toggle_btn.pack(side=tk.LEFT)

        # Sidebar Content Container
        self.sidebar_content = tk.Frame(self.left_sidebar)
        self.sidebar_content.pack(fill=tk.BOTH, expand=True)

        # Right Panel (Chat & RAG Toolbar)
        self.right_panel = tk.Frame(self.body_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_sidebar_content()
        self._build_chat_panel()

    def _build_sidebar_content(self):
        """Builds sidebar cards (Security Quick-View, Persona Mode, Fintech Analytics)."""
        # Security Overview Card
        self.sec_card = tk.LabelFrame(
            self.sidebar_content,
            text=" 🛡️ Security Overview ",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=8,
        )
        self.sec_card.pack(fill=tk.X, pady=(0, 10))

        # Interactive Security Quick Toggles
        self.ai_btn = tk.Button(
            self.sec_card,
            text="AI Engine: ENABLED" if settings.is_ai_enabled else "AI Engine: DISABLED",
            command=self._quick_toggle_ai,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2",
        )
        self.ai_btn.pack(anchor=tk.W, fill=tk.X, pady=3)

        self.phone_btn = tk.Button(
            self.sec_card,
            text="Phone Bridge: ALLOWED" if settings.is_phone_bridge_allowed else "Phone Bridge: LOCKED",
            command=self._quick_toggle_phone,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=8,
            pady=3,
            cursor="hand2",
        )
        self.phone_btn.pack(anchor=tk.W, fill=tk.X, pady=3)

        self.sec_note = tk.Label(
            self.sec_card,
            text="* Click buttons above or ⚙️ Settings to toggle permission locks.",
            font=("Segoe UI", 8, "italic"),
            wraplength=280,
            justify=tk.LEFT,
        )
        self.sec_note.pack(anchor=tk.W, pady=(4, 0))


        # Analytics & Context Flow Widget
        self.widget_card = tk.LabelFrame(
            self.sidebar_content,
            text=" 📊 System Analytics & Flow ",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=10,
        )
        self.widget_card.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.widget_card, text="Memory & Context Capacity (74%)", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.progress = ttk.Progressbar(self.widget_card, length=280, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(4, 10))
        self.progress["value"] = 74

        self.chart_canvas = tk.Canvas(self.widget_card, height=130, bg=self.theme["card_surface"], highlightthickness=0)
        self.chart_canvas.pack(fill=tk.X, pady=5)
        self._draw_widgets()

    def _draw_widgets(self):
        """Renders expense breakdown donut chart and flow diagram on canvas."""
        self.chart_canvas.delete("all")
        bg = self.theme["card_surface"]
        orange = self.theme["accent_secondary"]
        blue = self.theme["accent_primary"]
        text_color = self.theme["text_primary"]

        self.chart_canvas.configure(bg=bg)

        # Donut Chart
        self.chart_canvas.create_arc(15, 10, 95, 90, start=0, extent=240, fill=orange, outline="")
        self.chart_canvas.create_arc(15, 10, 95, 90, start=240, extent=120, fill=blue, outline="")
        self.chart_canvas.create_oval(32, 27, 78, 73, fill=bg, outline="")
        self.chart_canvas.create_text(55, 50, text="74%", fill=text_color, font=("Segoe UI", 9, "bold"))
        self.chart_canvas.create_text(55, 105, text="Context Allocation", fill=text_color, font=("Segoe UI", 8))

        # Flow Diagram
        self.chart_canvas.create_line(130, 25, 200, 45, 260, 35, fill=blue, width=4, smooth=True)
        self.chart_canvas.create_line(130, 80, 180, 60, 260, 75, fill=orange, width=4, smooth=True)
        self.chart_canvas.create_text(195, 15, text="Ingestion Flow", fill=text_color, font=("Segoe UI", 8, "bold"))
        self.chart_canvas.create_text(195, 95, text="Context Usage", fill=text_color, font=("Segoe UI", 8, "bold"))

    def _build_chat_panel(self):
        """Builds Right Panel containing Interactive RAG Chat Display & Ingestion Progress Toolbar."""
        self.chat_card = tk.LabelFrame(
            self.right_panel,
            text=" 💬 Interactive Zero-Leak RAG Shell ",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=10,
        )
        self.chat_card.pack(fill=tk.BOTH, expand=True)

        # Ingestion Toolbar & Live Status
        self.ingest_bar = tk.Frame(self.chat_card)
        self.ingest_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 8))

        self.ingest_btn = tk.Button(
            self.ingest_bar,
            text="📄 Ingest File",
            command=self._on_ingest_file,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor="hand2",
        )
        self.ingest_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.ingest_dir_btn = tk.Button(
            self.ingest_bar,
            text="📁 Ingest Codebase / Folder",
            command=self._on_ingest_directory,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor="hand2",
        )
        self.ingest_dir_btn.pack(side=tk.LEFT)

        self.clear_btn = tk.Button(
            self.ingest_bar,
            text="🗑️ Clear Chat",
            command=self._clear_chat,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor="hand2",
        )
        self.clear_btn.pack(side=tk.RIGHT)

        # Ingestion Progress Bar (Hidden when idle)
        self.ingest_progress_frame = tk.Frame(self.chat_card)
        self.ingest_status_lbl = tk.Label(self.ingest_progress_frame, text="", font=("Segoe UI", 8, "italic"))
        self.ingest_status_lbl.pack(side=tk.LEFT, padx=5)
        self.ingest_progressbar = ttk.Progressbar(self.ingest_progress_frame, mode="indeterminate", length=200)
        self.ingest_progressbar.pack(side=tk.RIGHT, padx=5)

        # Chat Text Display
        self.chat_text = tk.Text(
            self.chat_card,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            state=tk.DISABLED,
            padx=12,
            pady=12,
            relief=tk.FLAT,
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Markdown Renderer
        self.renderer = TkinterMarkdownRenderer(self.chat_text, self.theme)

        # Bottom Prompt Entry Frame
        self.input_frame = tk.Frame(self.chat_card)
        self.input_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.prompt_entry = tk.Entry(self.input_frame, font=("Segoe UI", 10), relief=tk.FLAT, bd=2)
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=6)
        self.prompt_entry.bind("<Return>", lambda e: self._send_prompt())

        self.send_btn = tk.Button(
            self.input_frame,
            text="Send Prompt 🚀",
            command=self._send_prompt,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
        )
        self.send_btn.pack(side=tk.RIGHT)

    def toggle_sidebar(self):
        """Collapses or expands the left sidebar drawer."""
        if self.sidebar_collapsed:
            self.sidebar_content.pack(fill=tk.BOTH, expand=True)
            self.left_sidebar.configure(width=340)
            self.drawer_toggle_btn.config(text="◀ Drawer")
            self.sidebar_collapsed = False
        else:
            self.sidebar_content.pack_forget()
            self.left_sidebar.configure(width=50)
            self.drawer_toggle_btn.config(text="▶")
            self.sidebar_collapsed = True

    def open_settings(self):
        """Opens the Settings Modal dialog."""
        SettingsDialog(self.root, self)

    def _update_rag_badge(self):
        """Updates the RAG Memory Badge count from local ChromaDB."""
        def fetch_count():
            try:
                store = LocalVectorStore()
                count = store.collection.count()
                self.root.after(0, lambda: self.rag_badge.config(text=f"⚡ RAG Memory: {count} chunks"))
            except Exception:
                self.root.after(0, lambda: self.rag_badge.config(text="⚡ RAG Memory: Active"))

        threading.Thread(target=fetch_count, daemon=True).start()

    def _on_ingest_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Knowledge File to Ingest",
            filetypes=[("Supported Files", "*.md *.txt *.pdf *.py *.js *.ts *.json"), ("All Files", "*.*")],
        )
        if file_path:
            path = Path(file_path)
            self._show_ingest_progress(f"Ingesting file '{path.name}'...")

            def bg():
                try:
                    store = LocalVectorStore()
                    from personalai.rag.mass_ingester import MassIngester
                    ingester = MassIngester()
                    content = ingester.read_file_content(path)
                    if content:
                        chunks = ingester.chunk_text(content, path)
                        count = store.ingest_documents(chunks)
                        self.root.after(0, lambda: self._hide_ingest_progress())
                        self.root.after(0, lambda: self.renderer.render_message("System", f"Ingested '{path.name}' ({count} chunks) into RAG Memory.", is_user=False))
                        self._update_rag_badge()
                except Exception as e:
                    self.root.after(0, lambda: self._hide_ingest_progress())
                    self.root.after(0, lambda: self.renderer.render_message("System", f"Error ingesting file '{path.name}': {e}", is_user=False))

            threading.Thread(target=bg, daemon=True).start()

    def _on_ingest_directory(self):
        dir_path = filedialog.askdirectory(title="Select Codebase or Document Directory to Ingest")
        if dir_path:
            target_dir = Path(dir_path)
            self._show_ingest_progress(f"Scanning & ingesting codebase '{target_dir.name}'...")

            def bg_ingest():
                try:
                    store = LocalVectorStore()
                    res = store.ingest_directory(target_dir)
                    n_chunks = res["total_chunks"]
                    self.root.after(0, lambda: self._hide_ingest_progress())
                    self.root.after(0, lambda: self.renderer.render_message("System", f"Ingested codebase/folder '{target_dir.name}' ({n_chunks} chunks in RAG Memory).", is_user=False))
                    self._update_rag_badge()
                except Exception as e:
                    self.root.after(0, lambda: self._hide_ingest_progress())
                    self.root.after(0, lambda: self.renderer.render_message("System", f"Error ingesting folder '{target_dir.name}': {e}", is_user=False))

            threading.Thread(target=bg_ingest, daemon=True).start()

    def _show_ingest_progress(self, msg: str):
        self.ingest_progress_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 6))
        self.ingest_status_lbl.config(text=msg)
        self.ingest_progressbar.start(10)

    def _hide_ingest_progress(self):
        self.ingest_progressbar.stop()
        self.ingest_progress_frame.pack_forget()

    def _quick_toggle_ai(self):
        settings.is_ai_enabled = not settings.is_ai_enabled
        status = "ENABLED" if settings.is_ai_enabled else "DISABLED"
        self.ai_btn.config(
            text=f"AI Engine: {status}",
            bg=self.theme["accent_primary"] if settings.is_ai_enabled else self.theme["trace_bg"],
        )
        self.renderer.render_message("System", f"Security Update: Local AI Engine is now {status}.", is_user=False)

    def _quick_toggle_phone(self):
        settings.is_phone_bridge_allowed = not settings.is_phone_bridge_allowed
        status = "ALLOWED" if settings.is_phone_bridge_allowed else "LOCKED"
        self.phone_btn.config(
            text=f"Phone Bridge: {status}",
            bg=self.theme["accent_secondary"] if settings.is_phone_bridge_allowed else self.theme["trace_bg"],
        )
        self.renderer.render_message("System", f"Security Update: P2P Phone Bridge Permission is now {status}.", is_user=False)

    def update_sidebar_sec_buttons(self):
        """Updates sidebar toggle buttons state."""
        self.ai_btn.config(
            text=f"AI Engine: {'ENABLED' if settings.is_ai_enabled else 'DISABLED'}",
            bg=self.theme["accent_primary"] if settings.is_ai_enabled else self.theme["trace_bg"],
        )
        self.phone_btn.config(
            text=f"Phone Bridge: {'ALLOWED' if settings.is_phone_bridge_allowed else 'LOCKED'}",
            bg=self.theme["accent_secondary"] if settings.is_phone_bridge_allowed else self.theme["trace_bg"],
        )

    def _send_prompt(self):
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            return

        self.prompt_entry.delete(0, tk.END)
        self.renderer.render_message("You", prompt, is_user=True)

        if not settings.is_ai_enabled:
            self.renderer.render_message("Security Gate", "BLOCKED: Local AI Engine is turned OFF in Security Settings.", is_user=False)
            return

        # Show live processing indicator
        thinking_mark = self.renderer.render_thinking_bubble("Personal AI")
        self.send_btn.config(state=tk.DISABLED, text="⏳ Thinking...")

        def run_in_bg():
            custom_instruction = self.persona_prompts[self.selected_persona]
            config = self.orchestrator.build_agent_config()
            config.system_instruction = custom_instruction

            res = asyncio.run(self.orchestrator.execute_query(prompt))

            def on_complete():
                self.renderer.remove_thinking_bubble(thinking_mark)
                self.renderer.render_message("Personal AI", res["response"], citations=res.get("citations"), is_user=False)
                self.send_btn.config(state=tk.NORMAL, text="Send Prompt 🚀")

            self.root.after(0, on_complete)

        threading.Thread(target=run_in_bg, daemon=True).start()


    def _clear_chat(self):
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.DISABLED)

    def toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        settings.active_theme = self.theme_name
        self.theme = THEMES.get(self.theme_name, THEMES["dark"])
        self.theme_btn.config(text="🌙 Dark" if self.theme_name == "dark" else "☀️ Light")
        self.renderer.update_theme(self.theme)
        self.apply_theme()

    def apply_theme(self):
        """Applies Contemporary Slate palette to all GUI widgets."""
        t = self.theme
        self.root.configure(bg=t["bg_canvas"])
        self.main_container.configure(bg=t["bg_canvas"])
        self.header_frame.configure(bg=t["card_surface"])
        self.title_label.configure(bg=t["card_surface"], fg=t["text_primary"])
        self.subtitle_label.configure(bg=t["card_surface"], fg=t["text_muted"])
        self.rag_badge.configure(bg=t["trace_bg"], fg=t["accent_primary"])
        self.settings_btn.configure(bg=t["trace_bg"], fg=t["text_primary"])
        self.theme_btn.configure(bg=t["accent_primary"], fg="#FFFFFF")

        self.body_frame.configure(bg=t["bg_canvas"])
        self.left_sidebar.configure(bg=t["bg_canvas"])
        self.sidebar_toggle_bar.configure(bg=t["bg_canvas"])
        self.drawer_toggle_btn.configure(bg=t["card_surface"], fg=t["text_primary"])
        self.sidebar_content.configure(bg=t["bg_canvas"])
        self.right_panel.configure(bg=t["bg_canvas"])

        # Security Overview Card
        self.sec_card.configure(bg=t["card_surface"], fg=t["text_primary"])
        self.ai_btn.configure(
            bg=t["accent_primary"] if settings.is_ai_enabled else t["trace_bg"],
            fg="#FFFFFF" if settings.is_ai_enabled else t["text_muted"],
        )
        self.phone_btn.configure(
            bg=t["accent_secondary"] if settings.is_phone_bridge_allowed else t["trace_bg"],
            fg="#FFFFFF" if settings.is_phone_bridge_allowed else t["text_muted"],
        )
        self.sec_note.configure(bg=t["card_surface"], fg=t["text_muted"])


        # Analytics Widget Card
        self.widget_card.configure(bg=t["card_surface"], fg=t["text_primary"])
        self._draw_widgets()

        # Chat Card
        self.chat_card.configure(bg=t["card_surface"], fg=t["text_primary"])
        self.ingest_bar.configure(bg=t["card_surface"])
        self.ingest_btn.configure(bg=t["accent_primary"], fg="#FFFFFF")
        self.ingest_dir_btn.configure(bg=t["accent_secondary"], fg="#FFFFFF")
        self.clear_btn.configure(bg=t["card_surface"], fg=t["text_muted"])

        self.ingest_progress_frame.configure(bg=t["card_surface"])
        self.ingest_status_lbl.configure(bg=t["card_surface"], fg=t["accent_primary"])

        self.chat_text.configure(bg=t["card_surface"], fg=t["text_primary"], insertbackground=t["text_primary"])

        self.input_frame.configure(bg=t["card_surface"])
        self.prompt_entry.configure(bg=t["bg_canvas"], fg=t["text_primary"], insertbackground=t["text_primary"])
        self.send_btn.configure(bg=t["accent_primary"], fg="#FFFFFF")


def launch_gui():
    """Launches the Personal AI Desktop Application GUI."""
    root = tk.Tk()
    app = PersonalAIGUIApp(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
