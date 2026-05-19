import io
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

from pymoo.indicators.hv import Hypervolume
from pymoo.indicators.igd import IGD
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

from app.config import EPSILON_NUM
from app.core import weighted_topsis
from app.viz import build_pareto_front_figure, build_allocation_donut
from styles import section_label


def render_tab_analysis(config: dict) -> None:
    simple_mode = config["simple_mode"]

    st.markdown("### 📋 Recommandation finale et synthèse")

    if st.session_state.results_data is None:
        with st.container(border=True):
            st.warning(
                "⚠️ Aucune simulation n'a encore été lancée. "
                "Rendez-vous dans l'onglet **Simulation en Temps Réel** "
                "pour lancer les calculs."
            )
        return

    data_store = st.session_state.results_data
    rf = data_store.get("risk_free_rate", 0.0)
    has_feasible = any(res.X is not None for res in data_store["raw_results"].values())

    if has_feasible and not simple_mode:
        _render_quality_indicators(data_store)

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        _write_config_sheet(writer, config, data_store, has_feasible, rf)

        if not has_feasible:
            with st.container(border=True):
                st.error("❌ **Aucune solution trouvée respectant vos contraintes.**")
                st.info(
                    "💡 Augmentez le seuil de risque maximum dans la sidebar, "
                    "ou désactivez la contrainte, puis relancez la simulation."
                )
        else:
            for name, res in data_store["raw_results"].items():
                if res.X is None:
                    continue
                _render_algorithm_report(
                    name,
                    res,
                    data_store,
                    config,
                    rf,
                    simple_mode,
                    writer,
                )

    if has_feasible:
        st.markdown("---")
        col_a, col_b = st.columns([2, 1])
        with col_b:
            st.download_button(
                label="📥 Télécharger le rapport Excel",
                data=excel_buffer.getvalue(),
                file_name=f"Rapport_SID_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )


def _render_quality_indicators(data_store: dict) -> None:
    """Bloc HV / IGD pour le mode expert."""
    st.markdown("#### 📊 Indicateurs de qualité des fronts de Pareto")

    all_F = [
        np.atleast_2d(res.F)
        for res in data_store["raw_results"].values()
        if res.F is not None
    ]
    if not all_F:
        return

    union_F = np.vstack(all_F)
    ref_fronts = NonDominatedSorting().do(union_F)
    ref_F = union_F[ref_fronts[0]]

    ref_point = np.array([0.0, float(max(data_store["ui_vol"]))])
    hv_indicator = Hypervolume(ref_point=ref_point)
    igd_indicator = IGD(ref_F)

    cols = st.columns(len(data_store["raw_results"]))
    for col, (name, res) in zip(cols, data_store["raw_results"].items()):
        if res.F is None:
            continue
        hv_val = hv_indicator(res.F)
        igd_val = igd_indicator(res.F)
        with col:
            with st.container(border=True):
                st.markdown(f"**{name}**")
                m1, m2 = st.columns(2)
                m1.metric("Hypervolume", f"{hv_val:.4f}", help="Plus grand = mieux")
                m2.metric("IGD", f"{igd_val:.4f}", help="Plus petit = mieux")
                st.caption(f"Front non-dominé : **{len(res.F)} solutions**")

    st.caption(
        "**HV** : volume dominé avec un point de référence invariant (rendement nul, "
        "volatilité max individuelle) → comparable entre runs. "
        "**IGD** : distance moyenne au front de référence approché (union non-dominée) → relatif."
    )
    st.markdown("---")


def _write_config_sheet(writer, config, data_store, has_feasible, rf):
    """Première feuille Excel : configuration de la simulation."""
    df_configuration = pd.DataFrame(
        {
            "Paramètre Décisionnel": [
                "Date de Simulation",
                "Seed",
                "Priorité Rendement",
                "Priorité Risque",
                "Taux sans risque",
                "Statut Calcul",
            ],
            "Valeur Spécifiée": [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data_store.get("seed", "N/A"),
                f"{config['w_return']} %",
                f"{config['w_risk']} %",
                f"{rf*100:.2f} %",
                "Validé" if has_feasible else "Contraintes saturées",
            ],
        }
    )
    df_configuration.to_excel(writer, sheet_name="Configuration_Générale", index=False)


def _render_algorithm_report(name, res, data_store, config, rf, simple_mode, writer):
    """Bloc de rapport pour un algorithme donné (MOEP ou NSGA-II)."""
    with st.container(border=True):
        st.markdown(f"### 💼 Recommandation — {name}")

        final_X = np.atleast_2d(res.X)
        final_F = np.atleast_2d(res.F)
        weights = final_X / np.maximum(
            np.sum(final_X, axis=1, keepdims=True), EPSILON_NUM
        )
        returns_pct = -final_F[:, 0] * 100
        risks_pct = final_F[:, 1] * 100

        best_idx = weighted_topsis(
            returns_pct,
            risks_pct,
            config["w_return"] / 100,
            config["w_risk"] / 100,
        )
        best_weights = weights[best_idx]
        final_return = float(returns_pct[best_idx])
        final_risk = float(risks_pct[best_idx])
        sharpe_ratio = (
            (final_return / 100 - rf) / (final_risk / 100) if final_risk > 0 else 0.0
        )

        if simple_mode:
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("💰 Rendement attendu", f"{final_return:.2f} % / an")
            col_m2.metric("⚠️ Niveau de risque", f"{final_risk:.2f} %")
        else:
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Rendement R_p", f"{final_return:.2f} %")
            col_m2.metric("Volatilité σ_p", f"{final_risk:.2f} %")
            col_m3.metric(
                f"Sharpe (r_f={rf*100:.1f}%)",
                f"{sharpe_ratio:.2f}",
            )

        st.write("")

        summary_df = pd.DataFrame(
            {
                ("Placement" if simple_mode else "Actif"): data_store["assets_list"],
                ("Pourcentage (%)" if simple_mode else "Allocation (%)"): np.round(
                    best_weights * 100, 2
                ),
            }
        )
        summary_df = summary_df.sort_values(by=summary_df.columns[1], ascending=False)
        summary_df_filtered = summary_df[summary_df.iloc[:, 1] > 0.1]

        if summary_df_filtered.empty:
            summary_df_filtered = summary_df.head(3)
            st.caption("Aucune allocation > 0.1% ; affichage des 3 plus fortes.")

        col_table, col_donut = st.columns([1, 1], gap="large")
        with col_table:
            section_label("Répartition recommandée")
            st.dataframe(
                summary_df_filtered,
                use_container_width=True,
                hide_index=True,
                column_config={
                    summary_df_filtered.columns[1]: st.column_config.ProgressColumn(
                        format="%.2f %%",
                        min_value=0.0,
                        max_value=float(summary_df_filtered.iloc[:, 1].max()),
                    ),
                },
            )
        with col_donut:
            section_label("Vue d'ensemble")
            donut = build_allocation_donut(summary_df_filtered, name, simple_mode)
            st.plotly_chart(donut, use_container_width=True)

        st.write("")
        section_label("Front de Pareto final")
        fig_front = build_pareto_front_figure(
            returns_pct,
            risks_pct,
            final_return,
            final_risk,
            name,
            config["max_risk_val"],
            simple_mode,
        )
        st.plotly_chart(fig_front, use_container_width=True)

        df_pareto_all = pd.DataFrame(weights, columns=data_store["assets_list"])
        df_pareto_all["Rendement_%"] = returns_pct
        df_pareto_all["Risque_%"] = risks_pct
        df_pareto_all.to_excel(writer, sheet_name=f"Pareto_{name}", index=False)
        summary_df.to_excel(writer, sheet_name=f"Allocation_{name}", index=False)

        st.write("")
        highest_asset = summary_df_filtered.iloc[0, 0]
        highest_val = summary_df_filtered.iloc[0, 1]
        max_possible = float(max(data_store["ui_mu"]) * 100)

        if simple_mode:
            st.info(
                f"🎙️ **L'analyse de votre conseiller :** "
                f"Votre argent est principalement placé sur **{highest_asset}** "
                f"(**{highest_val:.2f}%**) car c'est le moteur principal de vos gains. "
                f"\n\n"
                f"Le placement le plus rentable de votre liste plafonne à "
                f"**{max_possible:.2f}%**, donc il est impossible de dépasser ce chiffre. "
                f"L'IA a volontairement réparti une partie sur d'autres placements "
                f"pour vous protéger des baisses brutales."
            )
        else:
            st.info(
                f"📐 **Analyse :** convergence robuste sur le front de Pareto. "
                f"La solution TOPSIS se positionne à **R_p = {final_return:.2f}%** "
                f"pour **σ_p = {final_risk:.2f}%**, dégageant un **Sharpe = {sharpe_ratio:.2f}** "
                f"(r_f = {rf*100:.1f}%). "
                f"\n\n"
                f"**Borne supérieure :** rendement maximum théorique = **{max_possible:.2f}%** "
                f"(portefeuille saturé à 100% sur l'actif à espérance maximale). "
                f"L'algorithme dégage un compromis en deçà de cette frontière pour minimiser "
                f"les facteurs de risque de la matrice de covariance."
            )
