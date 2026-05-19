"""
Onglet 3 — Moteur d'optimisation et animation.

Lance les algorithmes, construit la figure animée Plotly, et la persiste
dans st.session_state pour qu'elle survive aux changements d'onglet.
"""

import time

import streamlit as st
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

from core import MOEP, PortfolioProblem
from viz import build_animated_figure
from styles import section_label


def render_tab_exec(config: dict, portfolio_data: dict) -> None:
    """Affiche l'onglet d'exécution avec animation interactive."""
    simple_mode = config["simple_mode"]

    if simple_mode:
        st.markdown("### 🚀 Lancement de la recherche automatique")
        st.markdown(
            "Cliquez sur le bouton ci-dessous. L'IA va comparer des milliers de "
            "répartitions possibles et trouver la meilleure courbe. Vous pourrez "
            "ensuite naviguer dans le temps avec le **slider** ou le bouton ▶."
        )
    else:
        st.markdown("### Suivi temps réel de la convergence collective")
        st.markdown(
            "Évolution des fronts génération par génération. L'animation utilise "
            "les frames natives Plotly : navigation libre dans le temps après calcul."
        )

    st.write("")

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        launch = st.button(
            (
                "🚀 Lancer les calculs"
                if simple_mode
                else "🚀 Déclencher l'optimisation stochastique"
            ),
            type="primary",
            use_container_width=True,
        )
    with col_info:
        risk_suffix = (
            f" · contrainte risque ≤ {config['max_risk_val']*100:.0f}%"
            if config["max_risk_val"] is not None
            else ""
        )
        st.caption(
            f"Configuration : population = {config['pop_size']} · "
            f"générations = {config['n_gen']} · seed = {config['seed_val']}{risk_suffix}"
        )

    plot_placeholder = st.empty()
    if st.session_state.final_fig is not None and not launch:
        plot_placeholder.plotly_chart(
            st.session_state.final_fig, use_container_width=True
        )

    if launch:
        problem = PortfolioProblem(
            mu_vec=portfolio_data["ui_mu"],
            cov_mat=portfolio_data["ui_cov_matrix"],
            max_risk=config["max_risk_val"],
        )

        progress_bar = st.progress(0)
        status_text = st.empty()

        algorithms = {}
        if config["algo_choice"] in [
            "MOEP (Programmation Évolutive)",
            "Les deux (Comparaison simultanée)",
        ]:
            algorithms["MOEP"] = MOEP(pop_size=config["pop_size"])
        if config["algo_choice"] in ["NSGA-II", "Les deux (Comparaison simultanée)"]:
            algorithms["NSGA-II"] = NSGA2(pop_size=config["pop_size"])

        raw_results = {}
        n_algos = len(algorithms)
        for i, (name, algo) in enumerate(algorithms.items()):
            status_text.markdown(
                f"⚙️ Optimisation en cours — **{name}**..."
                if simple_mode
                else f"⚙️ Évolution stochastique — **{name}**..."
            )
            res = minimize(
                problem,
                algo,
                ("n_gen", config["n_gen"]),
                seed=config["seed_val"],
                verbose=False,
                save_history=True,
            )
            raw_results[name] = res
            progress_bar.progress((i + 1) / n_algos)
            time.sleep(0.05)

        status_text.markdown("🎨 Construction de l'animation interactive...")
        fig = build_animated_figure(
            raw_results,
            n_gen=config["n_gen"],
            ui_mu=portfolio_data["ui_mu"],
            ui_vol=portfolio_data["ui_vol"],
            w_return=config["w_return"],
            w_risk=config["w_risk"],
            max_risk_val=config["max_risk_val"],
            simple_mode=simple_mode,
            fps=config["anim_fps"],
        )

        plot_placeholder.plotly_chart(fig, use_container_width=True)
        status_text.empty()
        progress_bar.empty()

        st.success(
            "🎉 Calculs terminés ! Utilisez ▶ Lecture ou le slider pour explorer "
            "l'évolution. Consultez ensuite l'onglet **Choix Final & Rapport**."
            if simple_mode
            else "🎉 Optimisation terminée. Naviguez dans le temps via le slider ou le bouton ▶ Lecture. "
            "Le rapport TOPSIS détaillé est disponible dans l'onglet **Choix Final & Rapport**."
        )

        st.session_state.final_fig = fig
        st.session_state.results_data = {
            "raw_results": raw_results,
            "assets_list": portfolio_data["assets_list"],
            "ui_mu": portfolio_data["ui_mu"],
            "ui_vol": portfolio_data["ui_vol"],
            "seed": config["seed_val"],
            "risk_free_rate": config["risk_free_rate"],
        }
