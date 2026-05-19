import streamlit as st

from config import get_palette


def apply_global_styles(simple_mode: bool) -> None:
    """Injecte le CSS global et la typographie selon le mode actif."""
    p = get_palette(simple_mode)

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ===== Masquage du chrome Streamlit ===== */
    #MainMenu, footer, header {{ visibility: hidden; height: 0; }}
    .stDeployButton {{ display: none; }}

    /* ===== Typographie globale ===== */
    /* On applique Inter uniquement au texte, PAS aux icônes Material Symbols
       qui ont besoin de leur police icônique pour s'afficher correctement.
       Sinon le bouton de collapse de la sidebar affiche littéralement
       "keyboard_arrow_left" sur 200px et casse tout. */
    html, body, .stApp, .stMarkdown, p, label,
    [data-testid="stMarkdownContainer"],
    [data-testid="stHeader"] *,
    .stButton button,
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        letter-spacing: -0.01em;
    }}

    /* Restaurer la police icônique pour TOUTES les icônes Material */
    [class*="material-symbols"],
    [class*="MaterialSymbols"],
    [data-testid*="icon"] span,
    .material-symbols-outlined,
    .material-symbols-rounded,
    .material-symbols-sharp {{
        font-family: 'Material Symbols Outlined', 'Material Symbols Rounded',
                     'Material Icons' !important;
        font-feature-settings: 'liga';
        -webkit-font-feature-settings: 'liga';
        letter-spacing: normal !important;
    }}

    code, pre, .katex {{ font-family: 'JetBrains Mono', 'SF Mono', monospace; }}

    /* ===== Bouton de collapse/expand de la sidebar ===== */
    /* On force la taille et le comportement pour que l'icône reste lisible */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    button[kind="header"] {{
        width: 32px !important;
        min-width: 32px !important;
        max-width: 32px !important;
        height: 32px !important;
        overflow: hidden !important;
    }}
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarCollapsedControl"] svg,
    button[kind="header"] svg {{
        width: 20px !important;
        height: 20px !important;
    }}

    /* ===== Fond global ===== */
    .stApp {{
        background: {p['bg_primary']};
        color: {p['text_primary']};
    }}

    /* Gradient subtil en haut, sans rainbow */
    .stApp::before {{
        content: '';
        position: fixed; top: 0; left: 0; right: 0; height: 60vh;
        background: radial-gradient(ellipse at top, {p['accent_glow']} 0%, transparent 60%);
        opacity: 0.4; pointer-events: none; z-index: 0;
    }}
    .main .block-container {{
        position: relative; z-index: 1;
        padding-top: 2rem; padding-bottom: 4rem;
        max-width: 1400px;
    }}

    /* ===== Titres ===== */
    h1, h2, h3, h4 {{
        color: {p['text_primary']};
        font-weight: 700;
        letter-spacing: -0.025em;
    }}
    h1 {{ font-size: 2.25rem; }}
    h2 {{ font-size: 1.5rem; margin-top: 2rem; }}
    h3 {{ font-size: 1.15rem; }}

    /* ===== Sidebar ===== */
    [data-testid="stSidebar"] {{
        background: {p['bg_secondary']};
        border-right: 1px solid {p['border']};
    }}
    [data-testid="stSidebar"] > div:first-child {{ padding-top: 1.5rem; }}
    [data-testid="stSidebar"] h2 {{
        font-size: 0.7rem !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: {p['text_muted']} !important;
        font-weight: 600;
        margin-top: 1.5rem !important; margin-bottom: 0.5rem !important;
    }}
    [data-testid="stSidebar"] label {{
        color: {p['text_secondary']} !important;
        font-size: 0.875rem !important;
        font-weight: 500;
    }}

    /* ===== Onglets ===== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.25rem;
        background: {p['bg_card']};
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        padding: 0.4rem;
        border-radius: 14px;
        border: 1px solid {p['border']};
        margin-bottom: 2rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 44px;
        padding: 0 1.25rem;
        background: transparent;
        border-radius: 10px;
        color: {p['text_secondary']};
        font-weight: 500;
        font-size: 0.9rem;
        border: none;
        transition: all 0.2s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background: {p['bg_card_hover']};
        color: {p['text_primary']};
    }}
    .stTabs [aria-selected="true"] {{
        background: {p['accent']} !important;
        color: white !important;
        box-shadow: 0 4px 12px {p['accent_glow']};
    }}

    /* ===== Métriques (cartes) ===== */
    [data-testid="stMetric"] {{
        background: {p['bg_card']};
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid {p['border']};
        border-radius: 16px;
        padding: 1.5rem 1.75rem;
        transition: all 0.2s ease;
    }}
    [data-testid="stMetric"]:hover {{
        border-color: {p['border_strong']};
        transform: translateY(-2px);
    }}
    [data-testid="stMetricLabel"] {{
        color: {p['text_muted']} !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    [data-testid="stMetricValue"] {{
        color: {p['text_primary']} !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }}

    /* ===== Boutons ===== */
    .stButton > button {{
        background: {p['accent']};
        color: white !important;
        border: none;
        padding: 0.75rem 1.75rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.01em;
        box-shadow: 0 4px 14px {p['accent_glow']};
        transition: all 0.2s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 24px {p['accent_glow']};
    }}
    .stDownloadButton > button {{
        background: {p['bg_card']};
        color: {p['text_primary']} !important;
        border: 1px solid {p['border_strong']};
        backdrop-filter: blur(10px);
    }}

    /* ===== Inputs / sliders ===== */
    .stSlider [data-baseweb="slider"] {{ margin-top: 0.5rem; }}
    .stTextInput input, .stNumberInput input {{
        background: {p['bg_card']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 8px !important;
        color: {p['text_primary']} !important;
    }}

    /* ===== Conteneurs avec bordure (st.container(border=True)) ===== */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: {p['bg_card']};
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid {p['border']} !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
    }}

    /* ===== Alertes (st.info / warning / success / error) ===== */
    [data-testid="stAlert"] {{
        background: {p['bg_card']} !important;
        backdrop-filter: blur(20px);
        border: 1px solid {p['border']} !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
    }}

    /* ===== DataFrame ===== */
    [data-testid="stDataFrame"], [data-testid="stTable"] {{
        background: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 12px;
        overflow: hidden;
    }}

    /* ===== Expander ===== */
    .stExpander {{
        background: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 12px;
    }}

    /* ===== Caption ===== */
    [data-testid="stCaptionContainer"] {{
        color: {p['text_muted']} !important;
        font-size: 0.8rem;
    }}

    /* ===== Progress bar ===== */
    .stProgress > div > div > div {{
        background: {p['accent']} !important;
    }}

    /* ===== Toggle ===== */
    [data-baseweb="checkbox"] {{ font-size: 0.9rem; }}

    /* ===== Hero ===== */
    .sid-hero {{
        padding: 2rem 0 1.5rem 0;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid {p['border']};
    }}
    .sid-hero-title {{
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.035em;
        margin: 0;
        background: linear-gradient(135deg, {p['text_primary']} 0%, {p['accent']} 100%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .sid-hero-subtitle {{
        color: {p['text_secondary']};
        font-size: 1rem;
        font-weight: 400;
        margin-top: 0.5rem;
        max-width: 720px;
        line-height: 1.6;
    }}
    .sid-badge {{
        display: inline-flex; align-items: center; gap: 0.5rem;
        background: {p['bg_card']};
        backdrop-filter: blur(20px);
        border: 1px solid {p['border_strong']};
        border-radius: 999px;
        padding: 0.4rem 1rem;
        font-size: 0.8rem;
        font-weight: 600;
        color: {p['text_primary']};
        margin-bottom: 1rem;
    }}
    .sid-badge-dot {{
        width: 8px; height: 8px; border-radius: 50%;
        background: {p['accent']};
        box-shadow: 0 0 12px {p['accent_glow']};
    }}

    /* ===== Section header ===== */
    .sid-section-label {{
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.7rem;
        font-weight: 700;
        color: {p['text_muted']};
        margin-top: 1rem; margin-bottom: 0.5rem;
    }}

    /* ===== Cartes algorithmes ===== */
    .sid-algo-card {{
        background: {p['bg_card']};
        backdrop-filter: blur(20px);
        border: 1px solid {p['border']};
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }}
    .sid-algo-card-title {{
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: {p['text_muted']};
        margin-bottom: 0.5rem;
    }}
    .sid-algo-card-value {{
        font-size: 1.75rem;
        font-weight: 700;
        color: {p['text_primary']};
        margin: 0;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_hero(simple_mode: bool) -> None:
    """Affiche le hero header avec badge de mode."""
    p = get_palette(simple_mode)

    if simple_mode:
        title = "Votre Conseiller Financier Intelligent"
        subtitle = (
            "Comparez automatiquement des milliers de répartitions possibles "
            "de votre épargne pour trouver l'équilibre parfait entre vos gains "
            "et votre tranquillité d'esprit."
        )
        badge_text = "Mode Découverte"
    else:
        title = "SID — Optimisation Évolutive Multi-Objectif"
        subtitle = (
            "Système d'Aide à la Décision intégrant MOEP (Fogel-style) et NSGA-II "
            "pour la résolution du problème de Markowitz sous contraintes, avec "
            "arbitrage TOPSIS et indicateurs Hypervolume / IGD."
        )
        badge_text = "Mode Expert"

    st.markdown(
        f"""
        <div class="sid-hero">
            <div class="sid-badge">
                <span class="sid-badge-dot"></span>
                {badge_text}
            </div>
            <h1 class="sid-hero-title">{title}</h1>
            <p class="sid-hero-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str) -> None:
    """Affiche un petit label de section en petites capitales."""
    st.markdown(
        f'<div class="sid-section-label">{text}</div>',
        unsafe_allow_html=True,
    )
