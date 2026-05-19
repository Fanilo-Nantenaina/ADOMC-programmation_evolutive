"""
Rendu de la barre latérale et collecte de tous les paramètres de configuration.

Retourne un dictionnaire unique consommé par les onglets.
"""

import streamlit as st


def render_sidebar() -> dict:
    """
    Affiche la sidebar complète et retourne un dict avec toutes les valeurs.

    Le contenu et le langage s'adaptent automatiquement au mode (simple/expert).
    """
    st.sidebar.markdown(
        '<div style="font-size: 0.7rem; text-transform: uppercase; '
        "letter-spacing: 0.12em; font-weight: 700; opacity: 0.6; "
        "margin-bottom: 0.5rem;\">Niveau d'expertise</div>",
        unsafe_allow_html=True,
    )
    simple_mode = st.sidebar.toggle(
        "🔰 Mode vulgarisation",
        value=False,
        help="Active une interface simplifiée avec un langage non-technique.",
    )

    st.sidebar.markdown("---")

    st.sidebar.subheader(
        "Méthode d'optimisation" if simple_mode else "Algorithme évolutif"
    )

    if simple_mode:
        algo_label = "Choisissez la méthode de recherche"
        algo_options = [
            "Méthode rapide (NSGA-II)",
            "Méthode avancée (MOEP)",
            "Comparer les deux",
        ]
        algo_map = {
            "Méthode rapide (NSGA-II)": "NSGA-II",
            "Méthode avancée (MOEP)": "MOEP (Programmation Évolutive)",
            "Comparer les deux": "Les deux (Comparaison simultanée)",
        }
        algo_ui_choice = st.sidebar.selectbox(
            algo_label,
            algo_options,
            index=2,
            help="MOEP : algorithme adaptatif. NSGA-II : algorithme de référence.",
        )
        algo_choice = algo_map[algo_ui_choice]
    else:
        algo_choice = st.sidebar.selectbox(
            "Algorithme",
            [
                "MOEP (Programmation Évolutive)",
                "NSGA-II",
                "Les deux (Comparaison simultanée)",
            ],
            index=2,
        )

    pop_size = st.sidebar.slider(
        "Taille de la population" if simple_mode else "Taille de la population (μ)",
        40,
        150,
        80,
        help="Nombre de portefeuilles candidats à chaque génération.",
    )
    n_gen = st.sidebar.slider(
        "Nombre d'itérations" if simple_mode else "Générations (T)",
        20,
        100,
        50,
        help="Plus c'est élevé, plus la recherche est précise (mais plus lente).",
    )
    seed_val = st.sidebar.number_input(
        "Graine aléatoire" if simple_mode else "Seed (reproductibilité)",
        min_value=0,
        max_value=99999,
        value=42,
        step=1,
        help="Même graine = même résultat. Changez-la pour explorer d'autres trajectoires.",
    )
    anim_fps = st.sidebar.slider(
        "Vitesse d'animation (FPS)" if simple_mode else "FPS de l'animation",
        1,
        30,
        12,
    )

    st.sidebar.markdown("---")

    st.sidebar.subheader("Limite de sécurité" if simple_mode else "Contraintes")

    apply_risk_limit = st.sidebar.checkbox(
        (
            "Interdire les portefeuilles trop risqués"
            if simple_mode
            else "Activer la contrainte de volatilité maximale"
        ),
        help="Élimine les portefeuilles dépassant le seuil de risque que vous fixez.",
    )
    max_risk_val = None
    if apply_risk_limit:
        max_risk_val = st.sidebar.slider("Risque maximum accepté (%)", 5, 60, 25) / 100

    st.sidebar.markdown("---")

    st.sidebar.subheader(
        "Votre profil" if simple_mode else "Profil du décideur (ADOMC)"
    )

    if simple_mode:
        w_return = st.sidebar.slider(
            "Importance accordée au gain (%)",
            10,
            90,
            60,
            help="100% = je veux gagner le plus possible. 0% = je veux juste me protéger.",
        )
    else:
        w_return = st.sidebar.slider(
            "Priorité Rendement (%)",
            10,
            90,
            60,
            help="Poids w_R dans le TOPSIS pondéré.",
        )
    w_risk = 100 - w_return

    if not simple_mode:
        risk_free_rate = (
            st.sidebar.slider(
                "Taux sans risque (% annuel)",
                0.0,
                10.0,
                2.0,
                0.1,
                help="Utilisé dans le calcul du Sharpe Ratio.",
            )
            / 100
        )
    else:
        risk_free_rate = 0.02

    return {
        "simple_mode": simple_mode,
        "algo_choice": algo_choice,
        "pop_size": pop_size,
        "n_gen": n_gen,
        "seed_val": int(seed_val),
        "anim_fps": anim_fps,
        "apply_risk_limit": apply_risk_limit,
        "max_risk_val": max_risk_val,
        "w_return": w_return,
        "w_risk": w_risk,
        "risk_free_rate": risk_free_rate,
    }
