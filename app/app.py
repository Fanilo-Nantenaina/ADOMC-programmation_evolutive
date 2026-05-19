import streamlit as st

from config import APP_TITLE, APP_ICON
from styles import apply_global_styles, render_hero
from sidebar import render_sidebar
from tab_config import render_tab_config
from tab_theory import render_tab_theory
from tab_exec import render_tab_exec
from tab_policy import render_tab_policy
from tab_analysis import render_tab_analysis

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "SID — Optimisation Évolutive Multi-Objectif de Portefeuille",
    },
)

if "results_data" not in st.session_state:
    st.session_state.results_data = None
if "final_fig" not in st.session_state:
    st.session_state.final_fig = None


def main() -> None:
    """Boucle principale de l'application."""
    config = render_sidebar()

    apply_global_styles(simple_mode=config["simple_mode"])

    render_hero(simple_mode=config["simple_mode"])

    tab_labels = (
        [
            "🛠️ Paramètres",
            "📚 Explications",
            "🚀 Simulation",
            "🧠 Politique IA",
            "📋 Choix Final",
        ]
        if config["simple_mode"]
        else [
            "🛠️ Paramètres des Placements",
            "📐 Explications des Modèles",
            "🚀 Simulation en Temps Réel",
            "🧠 Politique Apprise (NEAT)",
            "🧠 Choix Final & Rapport",
        ]
    )
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        portfolio_data = render_tab_config(simple_mode=config["simple_mode"])
    with tabs[1]:
        render_tab_theory(simple_mode=config["simple_mode"])
    with tabs[2]:
        render_tab_exec(config=config, portfolio_data=portfolio_data)
    with tabs[3]:
        render_tab_policy(config=config, portfolio_data=portfolio_data)
    with tabs[4]:
        render_tab_analysis(config=config)


if __name__ == "__main__":
    main()
else:
    main()
