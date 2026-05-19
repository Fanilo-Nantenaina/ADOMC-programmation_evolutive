"""
Onglet 1 — Configuration des actifs et corrélations.

Layout en colonnes pour casser l'empilement vertical.
Retourne un dict avec ui_mu, ui_vol, assets_list, ui_cov_matrix.
"""

import numpy as np
import pandas as pd
import streamlit as st

from config import (
    DEFAULT_ASSET_NAMES,
    DEFAULT_RETURNS_PCT,
    DEFAULT_VOLATILITIES_PCT,
    CORR_SAFE_HAVEN_DEFAULT,
    CORR_EQUITY_DEFAULT,
    EIGENVALUE_FLOOR,
)
from core import project_to_psd
from styles import section_label


def render_tab_config(simple_mode: bool) -> dict:
    """Affiche l'onglet de configuration et retourne les paramètres du marché."""

    if simple_mode:
        st.markdown("### 💼 Vos options de placements")
        st.markdown(
            "Décrivez ici les placements que vous voulez analyser : leur nom, "
            "le gain qu'ils peuvent rapporter, et leur niveau de danger."
        )
    else:
        st.markdown("### Définition des actifs et scénarios de marché")
        st.markdown(
            "Ajustez les rendements espérés, volatilités individuelles et "
            "la matrice de corrélation. L'optimisation se reconfigure automatiquement."
        )

    st.write("")

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        with st.container(border=True):
            section_label("Échantillon d'actifs")
            n_assets_ui = st.number_input(
                (
                    "Combien de placements analyser ?"
                    if simple_mode
                    else "Nombre d'actifs (n)"
                ),
                min_value=3,
                max_value=12,
                value=6,
                step=1,
                help="De 3 à 12 actifs simultanés.",
            )
            st.caption(
                f"L'IA explorera des combinaisons sur {n_assets_ui} placements."
                if simple_mode
                else f"Espace de recherche : [0,1]^{n_assets_ui} avec normalisation simplexe."
            )

    with col_right:
        with st.container(border=True):
            section_label("Diversification (rappel)")
            st.markdown(
                "💡 Si deux placements évoluent **dans le sens opposé** (corrélation négative), "
                "l'un compense les baisses de l'autre. Plus vous mélangez de placements "
                "indépendants, plus votre capital est stable."
                if simple_mode
                else "Une corrélation proche de -1 indique des actifs qui se compensent, "
                "réduisant drastiquement le risque global (effet de diversification de Markowitz)."
            )

    st.write("")

    section_label("Rendements espérés et volatilités")
    default_data = {
        ("Nom du Placement" if simple_mode else "Actif"): DEFAULT_ASSET_NAMES[
            :n_assets_ui
        ],
        (
            "Gain annuel estimé (%)" if simple_mode else "Rendement Espéré μ (%)"
        ): DEFAULT_RETURNS_PCT[:n_assets_ui],
        (
            "Danger / Volatilité (%)" if simple_mode else "Volatilité σ (%)"
        ): DEFAULT_VOLATILITIES_PCT[:n_assets_ui],
    }
    df_assets = pd.DataFrame(default_data)
    edited_assets = st.data_editor(
        df_assets,
        key="assets_editor",
        hide_index=True,
        use_container_width=True,
        column_config={
            df_assets.columns[1]: st.column_config.NumberColumn(
                format="%.1f %%",
                min_value=-50.0,
                max_value=200.0,
            ),
            df_assets.columns[2]: st.column_config.NumberColumn(
                format="%.1f %%",
                min_value=0.0,
                max_value=200.0,
            ),
        },
    )

    ui_mu = edited_assets.iloc[:, 1].to_numpy() / 100
    ui_vol = edited_assets.iloc[:, 2].to_numpy() / 100
    assets_list = edited_assets.iloc[:, 0].tolist()

    if len(set(assets_list)) != len(assets_list):
        st.error(
            "⚠️ Vous avez des noms de placements en double. Renommez-les pour pouvoir continuer."
            if simple_mode
            else "⚠️ Les noms d'actifs doivent être uniques (collision d'index dans la matrice de corrélation)."
        )
        st.stop()

    st.write("")

    section_label(
        "Liens de dépendance entre placements"
        if simple_mode
        else "Matrice de corrélation (R)"
    )

    base_corr = np.eye(n_assets_ui)
    is_safe_haven = np.array([("Obligations" in a) or ("Or" in a) for a in assets_list])
    for i in range(n_assets_ui):
        for j in range(i + 1, n_assets_ui):
            base_corr[i, j] = base_corr[j, i] = (
                CORR_SAFE_HAVEN_DEFAULT
                if (is_safe_haven[i] or is_safe_haven[j])
                else CORR_EQUITY_DEFAULT
            )

    df_corr = pd.DataFrame(base_corr, columns=assets_list, index=assets_list)
    edited_corr = st.data_editor(
        df_corr,
        key="corr_editor",
        use_container_width=True,
        column_config={
            col: st.column_config.NumberColumn(
                format="%.2f",
                min_value=-1.0,
                max_value=1.0,
            )
            for col in assets_list
        },
    )

    raw_corr = edited_corr.to_numpy()
    ui_corr = (raw_corr + raw_corr.T) / 2
    np.fill_diagonal(ui_corr, 1.0)
    ui_cov_raw = np.diag(ui_vol) @ ui_corr @ np.diag(ui_vol)

    ui_cov_matrix, min_eig_observed, was_corrected = project_to_psd(ui_cov_raw)
    if was_corrected:
        st.warning(
            f"⚠️ Vos corrélations sont mathématiquement incohérentes (λ_min = "
            f"{min_eig_observed:.2e}). Une correction automatique a été appliquée. "
            f"Pensez à vérifier vos valeurs."
            if simple_mode
            else f"⚠️ **Projection PSD appliquée :** matrice de corrélation non semi-définie "
            f"positive (λ_min = {min_eig_observed:.2e}). Clipping spectral à "
            f"{EIGENVALUE_FLOOR}. La matrice utilisée diffère légèrement de la matrice saisie."
        )

    return {
        "ui_mu": ui_mu,
        "ui_vol": ui_vol,
        "assets_list": assets_list,
        "ui_cov_matrix": ui_cov_matrix,
        "n_assets": n_assets_ui,
    }
