"""
Configuration centrale : constantes mathématiques, données par défaut,
et tokens de design (palettes de couleurs séparées par mode).
"""

APP_TITLE = "SID — Optimisation Évolutive de Portefeuille"
APP_ICON = "🧬"

DEFAULT_ASSET_NAMES = [
    "NVDA",
    "AAPL",
    "MSFT",
    "GOOGL",
    "Obligations",
    "Or",
    "BTC",
    "Immobilier",
    "Pétrole",
    "EUR/USD",
    "LVMH",
    "ASML",
]
DEFAULT_RETURNS_PCT = [
    35.0,
    22.0,
    18.0,
    15.0,
    4.0,
    8.0,
    55.0,
    10.0,
    14.0,
    3.0,
    16.0,
    24.0,
]
DEFAULT_VOLATILITIES_PCT = [
    42.0,
    25.0,
    22.0,
    24.0,
    6.0,
    15.0,
    75.0,
    12.0,
    30.0,
    5.0,
    20.0,
    28.0,
]

CORR_SAFE_HAVEN_DEFAULT = -0.10
CORR_EQUITY_DEFAULT = 0.55

EPSILON_NUM = 1e-8
EIGENVALUE_FLOOR = 1e-10

EXPERT_PALETTE = {
    "bg_primary": "#0B0F19",
    "bg_secondary": "#141A28",
    "bg_card": "rgba(255, 255, 255, 0.04)",
    "bg_card_hover": "rgba(255, 255, 255, 0.06)",
    "border": "rgba(255, 255, 255, 0.08)",
    "border_strong": "rgba(255, 255, 255, 0.14)",
    "text_primary": "#F3F4F6",
    "text_secondary": "#9CA3AF",
    "text_muted": "#6B7280",
    "accent": "#818CF8",
    "accent_glow": "rgba(129, 140, 248, 0.4)",
    "moep": "#22D3EE",
    "nsga": "#34D399",
    "moep_best": "#F472B6",
    "nsga_best": "#FBBF24",
    "constraint": "#F87171",
    "success": "#34D399",
    "warning": "#FBBF24",
    "error": "#F87171",
    "plotly_template": "plotly_dark",
    "plot_bg": "rgba(20, 26, 40, 0.6)",
    "paper_bg": "rgba(0, 0, 0, 0)",
    "grid": "rgba(255, 255, 255, 0.08)",
}

SIMPLE_PALETTE = {
    "bg_primary": "#FAF7F2",
    "bg_secondary": "#F4EFE6",
    "bg_card": "rgba(255, 255, 255, 0.75)",
    "bg_card_hover": "rgba(255, 255, 255, 0.9)",
    "border": "rgba(15, 23, 42, 0.08)",
    "border_strong": "rgba(15, 23, 42, 0.14)",
    "text_primary": "#1C1917",
    "text_secondary": "#57534E",
    "text_muted": "#78716C",
    "accent": "#0F766E",
    "accent_glow": "rgba(15, 118, 110, 0.25)",
    "moep": "#0EA5E9",
    "nsga": "#F97316",
    "moep_best": "#0369A1",
    "nsga_best": "#C2410C",
    "constraint": "#B91C1C",
    "success": "#15803D",
    "warning": "#B45309",
    "error": "#B91C1C",
    "plotly_template": "plotly_white",
    "plot_bg": "rgba(255, 255, 255, 0.6)",
    "paper_bg": "rgba(0, 0, 0, 0)",
    "grid": "rgba(15, 23, 42, 0.06)",
}


def get_palette(simple_mode: bool) -> dict:
    """Retourne la palette active selon le mode."""
    return SIMPLE_PALETTE if simple_mode else EXPERT_PALETTE
