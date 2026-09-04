"""Design tokens, color palettes, Tailwind CSS configurations, and CSS variable mappings for Personal AI Desktop GUI."""

from typing import Dict, Any

# CSS Variable Mappings for Theme Switching
CSS_VARIABLES = """
:root {
  --bg-canvas: #E9EEF2;
  --card-surface: #FFFFFF;
  --text-primary: #0F172A;
  --text-muted: #64748B;
  --accent-primary: #1E75FF;
  --accent-secondary: #FF782D;
  --chart-tint: #BAE6FD;
  --card-border: 1px solid rgba(15, 23, 42, 0.08);
  --card-radius: 16px;
  --card-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
}

[data-theme="dark"] {
  --bg-canvas: #0B0E14;
  --card-surface: #131920;
  --text-primary: #F8FAFC;
  --text-muted: #94A3B8;
  --accent-primary: #388BFD;
  --accent-secondary: #FF782D;
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
                "canvas": {"light": "#E9EEF2", "dark": "#0B0E14"},
                "surface": {"light": "#FFFFFF", "dark": "#131920"},
                "text": {
                    "primary": {"light": "#0F172A", "dark": "#F8FAFC"},
                    "muted": {"light": "#64748B", "dark": "#94A3B8"},
                },
                "accent": {
                    "blue": {"light": "#1E75FF", "dark": "#388BFD"},
                    "orange": "#FF782D",
                    "sky": {"light": "#BAE6FD", "dark": "#0284C7"},
                },
            },
            "borderRadius": {"card": "16px"},
            "boxShadow": {
                "fintech": "0 4px 20px -2px rgba(15, 23, 42, 0.05)",
                "fintechDark": "0 4px 24px -2px rgba(0, 0, 0, 0.35)",
            },
        }
    },
}

# Python GUI Color Schemes (Dark & Light)
THEMES = {
    "dark": {
        "bg_canvas": "#0B0E14",
        "card_surface": "#131920",
        "text_primary": "#F8FAFC",
        "text_muted": "#94A3B8",
        "accent_primary": "#388BFD",
        "accent_secondary": "#FF782D",
        "chart_tint": "#0284C7",
        "card_border": "#1E293B",
        "user_bubble": "#1E293B",
        "ai_bubble": "#1E3A8A",
    },
    "light": {
        "bg_canvas": "#E9EEF2",
        "card_surface": "#FFFFFF",
        "text_primary": "#0F172A",
        "text_muted": "#64748B",
        "accent_primary": "#1E75FF",
        "accent_secondary": "#FF782D",
        "chart_tint": "#BAE6FD",
        "card_border": "#CBD5E1",
        "user_bubble": "#E2E8F0",
        "ai_bubble": "#DBEAFE",
    },
}
