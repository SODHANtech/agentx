"""Design tokens, color palettes, Tailwind CSS configurations, and CSS variable mappings for Personal AI Desktop GUI."""

from typing import Dict, Any

# CSS Variable Mappings for Contemporary Slate Theme Switching
CSS_VARIABLES = """
:root {
  --bg-canvas: #F8FAFC;
  --card-surface: #FFFFFF;
  --text-primary: #0F172A;
  --text-muted: #64748B;
  --accent-primary: #2563EB;
  --accent-secondary: #F97316;
  --chart-tint: #BAE6FD;
  --card-border: 1px solid rgba(15, 23, 42, 0.08);
  --card-radius: 14px;
  --card-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
}

[data-theme="dark"] {
  --bg-canvas: #121214;
  --card-surface: #1E1E24;
  --text-primary: #F1F5F9;
  --text-muted: #94A3B8;
  --accent-primary: #3B82F6;
  --accent-secondary: #F97316;
  --chart-tint: #0284C7;
  --card-border: 1px solid rgba(255, 255, 255, 0.08);
  --card-shadow: 0 4px 24px -2px rgba(0, 0, 0, 0.35);
}
"""

# Tailwind CSS Configuration Tokens Dictionary
TAILWIND_CONFIG: Dict[str, Any] = {
    "darkMode": "class",
    "theme": {
        "extend": {
            "colors": {
                "canvas": {"light": "#F8FAFC", "dark": "#121214"},
                "surface": {"light": "#FFFFFF", "dark": "#1E1E24"},
                "text": {
                    "primary": {"light": "#0F172A", "dark": "#F1F5F9"},
                    "muted": {"light": "#64748B", "dark": "#94A3B8"},
                },
                "accent": {
                    "blue": {"light": "#2563EB", "dark": "#3B82F6"},
                    "orange": "#F97316",
                    "sky": {"light": "#BAE6FD", "dark": "#0284C7"},
                },
            },
            "borderRadius": {"card": "14px"},
            "boxShadow": {
                "fintech": "0 4px 20px -2px rgba(15, 23, 42, 0.05)",
                "fintechDark": "0 4px 24px -2px rgba(0, 0, 0, 0.35)",
            },
        }
    },
}

# Python GUI Color Schemes (Slate Contemporary Glassmorphism)
THEMES = {
    "dark": {
        "bg_canvas": "#121214",
        "card_surface": "#1E1E24",
        "text_primary": "#F1F5F9",
        "text_muted": "#94A3B8",
        "accent_primary": "#3B82F6",
        "accent_secondary": "#F97316",
        "chart_tint": "#0284C7",
        "card_border": "#2A2A32",
        "user_bubble": "#252836",
        "user_text": "#F1F5F9",
        "ai_bubble": "#1A1D24",
        "ai_text": "#E2E8F0",
        "code_bg": "#161B22",
        "code_text": "#E6EDE3",
        "trace_bg": "#222734",
        "trace_fg": "#94A3B8",
    },
    "light": {
        "bg_canvas": "#F8FAFC",
        "card_surface": "#FFFFFF",
        "text_primary": "#0F172A",
        "text_muted": "#64748B",
        "accent_primary": "#2563EB",
        "accent_secondary": "#F97316",
        "chart_tint": "#BAE6FD",
        "card_border": "#E2E8F0",
        "user_bubble": "#EFF6FF",
        "user_text": "#1E40AF",
        "ai_bubble": "#F1F5F9",
        "ai_text": "#0F172A",
        "code_bg": "#F8FAFC",
        "code_text": "#0F172A",
        "trace_bg": "#E2E8F0",
        "trace_fg": "#475569",
    },
}
