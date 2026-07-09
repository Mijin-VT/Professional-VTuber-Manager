"""Centralized theme system for VT Manager.
Warm, cheerful dark theme with muted pastels — easy on the eyes.
"""

import customtkinter as ctk

# ─── Color Palette ───────────────────────────────────────────────────────────
# Warm dark theme with soft muted pastels. No harsh whites or neon colors.
COLORS = {
    # Backgrounds — warm dark tones (slightly purple/blue undertone)
    "bg_primary": "#1A1B2E",          # Main background (warm navy)
    "bg_secondary": "#1E1F34",        # Sidebar / panels
    "bg_tertiary": "#252640",         # Cards / elevated surfaces
    "bg_elevated": "#2D2E4A",         # Hover states / inputs
    "bg_hover": "#353658",            # Active hover

    # Accent colors — soft muted pastels
    "accent": "#7C9EF7",              # Soft periwinkle blue (primary)
    "accent_hover": "#9BB5FA",        # Lighter periwinkle
    "accent_muted": "#5A7AD4",        # Deeper periwinkle
    "accent_glow": "#2A2D4A",         # Subtle glow background

    "accent_green": "#7ECBA1",        # Soft mint green
    "accent_green_hover": "#9AD8B8",
    "accent_amber": "#E8C47A",        # Soft warm gold
    "accent_red": "#E88B8B",          # Soft coral/rose
    "accent_purple": "#B89CF7",       # Soft lavender
    "accent_cyan": "#7ECFC9",         # Soft teal

    # Text — warm off-whites, never pure white
    "text_primary": "#E4E2F0",        # Warm off-white (slightly lavender)
    "text_secondary": "#A8A6BE",      # Muted lavender-gray
    "text_muted": "#7A7892",          # Soft gray-purple
    "text_accent": "#B3C8FA",         # Soft blue text

    # Borders — subtle warm tones
    "border": "#2E2F48",             # Subtle warm border
    "border_hover": "#3D3E5C",       # Hover border
    "border_accent": "#3A3D60",      # Accent border (opaque)

    # Specific UI elements
    "sidebar_bg": "#181929",
    "sidebar_active": "#2A2D4A",
    "sidebar_hover": "#232440",
    "header_bg": "#1C1D32",
    "input_bg": "#1F2038",
    "input_border": "#353658",
    "scrollbar": "#353658",

    # Chat specific
    "msg_user": "#252848",
    "msg_ai": "#222340",
    "msg_user_border": "#3A3F6A",
    "msg_ai_border": "#3A2F5A",

    # Status
    "online": "#7ECBA1",
    "offline": "#7A7892",
    "busy": "#E8C47A",
}

# ─── Typography ──────────────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Cascadia Code"


def font(size=13, weight=None):
    """Create a standard font."""
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def font_bold(size=13):
    """Create a bold font."""
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")


def font_mono(size=12, weight=None):
    """Create a monospace font."""
    return ctk.CTkFont(family=FONT_FAMILY_MONO, size=size, weight=weight)


def font_heading(size=20):
    """Create a heading font."""
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")


def font_subheading(size=15):
    """Create a subheading font."""
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")


# ─── Spacing ─────────────────────────────────────────────────────────────────
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "2xl": 32,
    "3xl": 48,
}

# ─── Radius ──────────────────────────────────────────────────────────────────
RADIUS = {
    "sm": 6,
    "md": 10,
    "lg": 14,
    "xl": 18,
    "pill": 50,
}
