import os
import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    import neat

    NEAT_AVAILABLE = True
except ImportError:
    NEAT_AVAILABLE = False

from config import get_palette
from style import section_label

if NEAT_AVAILABLE:
    from neat_core import (
        encode_market_state,
        decode_allocation,
        generate_scenarios,
        make_eval_function,
        load_neat_config,
        policy_to_allocation,
        MAX_N_ASSETS,
    )
    from neat_manager import PolicyManager
    from viz import build_allocation_donut


def render_tab_policy(config: dict, portfolio_data: dict) -> None:
    """Onglet de la politique apprise NEAT."""
    if not NEAT_AVAILABLE:
        st.error(
            "📦 Module `neat-python` non installé. "
            "Lancez : `pip install neat-python` puis redémarrez l'application."
        )
        return

    simple_mode = config["simple_mode"]
    _ensure_session_state()

    _render_header(simple_mode)
    st.write("")

    train_params = _render_training_params()
    st.write("")

    policy_mgr = PolicyManager()
    do_train, do_load, do_delete = _render_action_buttons(policy_mgr, simple_mode)

    if do_delete:
        policy_mgr.delete()
        st.session_state.neat_policy = None
        st.session_state.neat_history = None
        st.rerun()

    if do_train:
        _run_training(config, portfolio_data, train_params, policy_mgr)

    if do_load:
        bundle = policy_mgr.load()
        if bundle is None:
            st.error("Échec du chargement (fichier corrompu).")
        else:
            st.session_state.neat_policy = bundle
            st.success(
                "✅ Politique chargée. Faites défiler vers le bas pour l'utiliser."
            )

    if st.session_state.neat_policy is not None:
        st.markdown("---")
        _render_inference_panel(config, portfolio_data, simple_mode)


def _ensure_session_state():
    if "neat_policy" not in st.session_state:
        st.session_state.neat_policy = None
    if "neat_history" not in st.session_state:
        st.session_state.neat_history = None


def _render_header(simple_mode: bool):
    if simple_mode:
        st.markdown("### 🧠 IA apprenante : une stratégie qui s'adapte")
        st.markdown(
            "Jusqu'ici, vous avez utilisé une IA qui **calcule** la meilleure répartition "
            "pour un scénario donné. Ici, c'est différent : vous entraînez une IA qui "
            "**apprend une règle générale** sur un éventail de scénarios. Une fois entraînée, "
            "vous pouvez modifier vos hypothèses en direct et elle vous propose instantanément "
            "une nouvelle répartition cohérente — comme un vrai conseiller financier qui "
            "raisonne, pas seulement qui se souvient."
        )
    else:
        st.markdown("### 🧠 Politique d'allocation apprise (NeuroEvolution)")
        st.markdown(
            "**Inversion du paradigme :** au lieu d'évoluer un vecteur de poids "
            "$\\mathbf{w} \\in \\Delta^{n-1}$ pour un état de marché fixe (MOEP/NSGA-II), "
            "**NEAT évolue un réseau de neurones** $\\phi_{\\theta}: \\text{marché} \\to \\mathbf{w}$ "
            "qui apprend une politique d'allocation **généralisable**. "
            "L'entraînement multi-scénarios force la politique à découvrir les "
            "**principes** de l'arbitrage rendement/risque, pas à mémoriser une réponse."
        )


def _render_training_params() -> dict:
    with st.container(border=True):
        section_label("Configuration de l'entraînement")
        c1, c2, c3 = st.columns(3)
        with c1:
            pop_size = st.slider("Population", 30, 100, 50, key="neat_pop")
        with c2:
            n_gen = st.slider("Générations", 10, 80, 30, key="neat_gen")
        with c3:
            n_scenarios = st.slider(
                "Scénarios par évaluation",
                1,
                20,
                8,
                key="neat_scen",
                help="Plus de scénarios = politique plus robuste mais entraînement plus lent.",
            )
        c4, c5 = st.columns(2)
        with c4:
            perturb = (
                st.slider(
                    "Diversité des scénarios (%)",
                    0,
                    60,
                    25,
                    key="neat_perturb",
                    help="Amplitude de perturbation de μ et σ autour de votre configuration de base.",
                )
                / 100
            )
        with c5:
            seed = st.number_input(
                "Seed",
                min_value=0,
                max_value=99999,
                value=42,
                step=1,
                key="neat_seed",
            )

    return {
        "pop_size": pop_size,
        "n_gen": n_gen,
        "n_scenarios": n_scenarios,
        "perturb": perturb,
        "seed": int(seed),
    }


def _render_action_buttons(policy_mgr, simple_mode):
    has_saved = policy_mgr.exists()
    has_in_memory = st.session_state.neat_policy is not None

    cols = st.columns(3)
    with cols[0]:
        do_train = st.button(
            "🧬 Entraîner la politique",
            type="primary",
            use_container_width=True,
            key="btn_neat_train",
        )
    with cols[1]:
        if has_saved:
            do_load = st.button(
                "📂 Charger la politique sauvegardée",
                use_container_width=True,
                key="btn_neat_load",
            )
        else:
            st.button(
                "📂 Aucune politique sauvegardée",
                disabled=True,
                use_container_width=True,
                key="btn_neat_load_disabled",
            )
            do_load = False
    with cols[2]:
        if has_in_memory or has_saved:
            do_delete = st.button(
                "🗑️ Réinitialiser",
                use_container_width=True,
                key="btn_neat_delete",
                help="Efface la politique en mémoire et le fichier sauvegardé.",
            )
        else:
            do_delete = False

    return do_train, do_load, do_delete


def _run_training(config, portfolio_data, params, policy_mgr):
    simple_mode = config["simple_mode"]
    config_path = os.path.join(os.path.dirname(__file__), "config-policy.txt")
    if not os.path.exists(config_path):
        st.error(f"Fichier `config-policy.txt` introuvable à {config_path}")
        return

    neat_config = load_neat_config(config_path)
    neat_config.pop_size = params["pop_size"]

    scenarios = generate_scenarios(
        portfolio_data["ui_mu"],
        portfolio_data["ui_vol"],
        portfolio_data["ui_cov_matrix"],
        n_scenarios=params["n_scenarios"],
        perturb_strength=params["perturb"],
        seed=params["seed"],
    )

    eval_fn = make_eval_function(
        scenarios,
        w_return=config["w_return"],
        rf=config["risk_free_rate"],
    )

    np.random.seed(params["seed"])
    population = neat.Population(neat_config)

    progress_bar = st.progress(0)
    status_text = st.empty()
    chart_placeholder = st.empty()
    history = {"max": [], "mean": [], "species": []}

    reporter = _StreamlitReporter(
        progress_bar,
        status_text,
        chart_placeholder,
        params["n_gen"],
        history,
        simple_mode,
    )
    population.add_reporter(reporter)

    t0 = time.time()
    try:
        best_genome = population.run(eval_fn, params["n_gen"])
    except Exception as e:
        st.error(f"❌ Erreur d'entraînement : {e}")
        return
    elapsed = time.time() - t0

    progress_bar.empty()
    status_text.empty()
    chart_placeholder.empty()

    metadata = {
        "n_assets": len(portfolio_data["ui_mu"]),
        "assets_list": portfolio_data["assets_list"],
        "base_mu": portfolio_data["ui_mu"].tolist(),
        "base_vol": portfolio_data["ui_vol"].tolist(),
        "base_cov": portfolio_data["ui_cov_matrix"].tolist(),
        "w_return": config["w_return"],
        "risk_free_rate": config["risk_free_rate"],
        "n_gen": params["n_gen"],
        "n_scenarios": params["n_scenarios"],
        "perturb": params["perturb"],
        "seed": params["seed"],
        "training_time_s": elapsed,
        "final_fitness": float(best_genome.fitness),
    }
    saved_path = policy_mgr.save(best_genome, metadata)

    st.session_state.neat_policy = {"genome": best_genome, "metadata": metadata}
    st.session_state.neat_history = history

    msg = (
        f"🎉 Entraînement terminé en **{elapsed:.1f}s**. "
        f"Fitness final : **{best_genome.fitness:.3f}**. "
        f"Politique sauvegardée dans `{os.path.basename(saved_path)}`."
    )
    st.success(msg)


class _StreamlitReporter(neat.reporting.BaseReporter):
    """Reporter NEAT qui actualise l'UI Streamlit à chaque génération."""

    def __init__(self, progress, status, chart, n_gen, history, simple_mode):
        self.progress = progress
        self.status = status
        self.chart = chart
        self.n_gen = n_gen
        self.history = history
        self.simple_mode = simple_mode
        self.gen = 0

    def post_evaluate(self, config, population, species, best_genome):
        self.gen += 1
        fitnesses = [g.fitness for g in population.values() if g.fitness is not None]
        if not fitnesses:
            return

        self.history["max"].append(max(fitnesses))
        self.history["mean"].append(float(np.mean(fitnesses)))
        self.history["species"].append(len(species.species))

        self.progress.progress(self.gen / self.n_gen)
        if self.simple_mode:
            self.status.markdown(
                f"⚙️ Étape **{self.gen}/{self.n_gen}** — "
                f"Meilleur score : **{max(fitnesses):.3f}**"
            )
        else:
            self.status.markdown(
                f"⚙️ Génération **{self.gen}/{self.n_gen}** — "
                f"f<sub>max</sub> = **{max(fitnesses):.3f}** · "
                f"f<sub>avg</sub> = **{np.mean(fitnesses):.3f}** · "
                f"Espèces actives : **{len(species.species)}**",
                unsafe_allow_html=True,
            )
        self._update_chart()

    def _update_chart(self):
        p = get_palette(self.simple_mode)
        gens = list(range(1, len(self.history["max"]) + 1))

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=gens,
                y=self.history["max"],
                mode="lines+markers",
                name="Meilleur" if self.simple_mode else "f_max",
                line=dict(color=p["accent"], width=2.5),
                marker=dict(size=6, color=p["accent"]),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=gens,
                y=self.history["mean"],
                mode="lines",
                name="Moyenne" if self.simple_mode else "f_avg",
                line=dict(color=p["moep"], width=2, dash="dot"),
            )
        )
        fig.update_layout(
            template=p["plotly_template"],
            plot_bgcolor=p["plot_bg"],
            paper_bgcolor=p["paper_bg"],
            height=280,
            margin=dict(l=40, r=20, t=20, b=40),
            xaxis=dict(
                title=dict(
                    text="Génération", font=dict(color=p["text_secondary"], size=11)
                ),
                gridcolor=p["grid"],
                tickfont=dict(color=p["text_secondary"], size=10),
            ),
            yaxis=dict(
                title=dict(
                    text="Fitness", font=dict(color=p["text_secondary"], size=11)
                ),
                gridcolor=p["grid"],
                tickfont=dict(color=p["text_secondary"], size=10),
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=1.15,
                font=dict(size=10, color=p["text_secondary"]),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
        self.chart.plotly_chart(
            fig, use_container_width=True, key=f"neat_chart_g{self.gen}"
        )


def _render_inference_panel(config, portfolio_data, simple_mode):
    p = get_palette(simple_mode)
    bundle = st.session_state.neat_policy
    genome = bundle["genome"]
    metadata = bundle["metadata"]

    if simple_mode:
        st.markdown("### 🔮 Testez la politique en direct")
        st.markdown(
            "L'IA a appris une règle d'allocation. Modifiez vos hypothèses ci-dessous "
            "et regardez la répartition recommandée s'adapter **instantanément**."
        )
    else:
        st.markdown("### 🔮 Inférence en temps réel")
        st.markdown(
            "Le réseau entraîné est maintenant une fonction $(\\boldsymbol{\\mu}, \\boldsymbol{\\sigma}) \\to \\mathbf{w}$. "
            "Ajustez les paramètres pour observer l'adaptation de la politique sans re-entraînement."
        )

    with st.expander("📋 Détails du modèle chargé", expanded=False):
        cm1, cm2, cm3 = st.columns(3)
        cm1.metric("Actifs entraînés", metadata["n_assets"])
        cm2.metric("Fitness final", f"{metadata['final_fitness']:.3f}")
        cm3.metric("Temps d'entraînement", f"{metadata.get('training_time_s', 0):.1f}s")

        info_md = (
            f"- **Générations** : {metadata['n_gen']}\n"
            f"- **Scénarios d'entraînement** : {metadata['n_scenarios']}\n"
            f"- **Perturbation** : ±{metadata['perturb']*100:.0f}%\n"
            f"- **Seed** : {metadata['seed']}\n"
            f"- **Profil** : rendement {metadata['w_return']}% / risque {100-metadata['w_return']}%\n"
            f"- **Taux sans risque** : {metadata['risk_free_rate']*100:.2f}%\n"
            f"- **Actifs** : {', '.join(metadata['assets_list'])}"
        )
        st.markdown(info_md)

    current_n_assets = len(portfolio_data["ui_mu"])
    trained_n_assets = metadata["n_assets"]
    incompatible_count = current_n_assets != trained_n_assets

    if incompatible_count:
        st.warning(
            f"⚠️ Le modèle a été entraîné pour **{trained_n_assets} actifs** mais votre "
            f"configuration actuelle en contient **{current_n_assets}**. "
            f"L'inférence utilise la base de l'entraînement, pas la nouvelle config. "
            f"Pour utiliser les nouveaux actifs, réentraînez la politique."
        )
        infer_mu_init = np.array(metadata["base_mu"])
        infer_vol_init = np.array(metadata["base_vol"])
        infer_cov = np.array(metadata["base_cov"])
        n_assets_inf = trained_n_assets
        assets_names = metadata["assets_list"]
    else:
        infer_mu_init = portfolio_data["ui_mu"].copy()
        infer_vol_init = portfolio_data["ui_vol"].copy()
        infer_cov = portfolio_data["ui_cov_matrix"].copy()
        n_assets_inf = current_n_assets
        assets_names = portfolio_data["assets_list"]

    with st.container(border=True):
        section_label("Modifier l'état du marché en direct")

        col_returns, col_vols = st.columns(2, gap="large")
        edited_mu = []
        edited_vol = []
        with col_returns:
            st.markdown("**📈 Rendements espérés (%)**")
            for i, name in enumerate(assets_names):
                v = st.slider(
                    name,
                    -10.0,
                    80.0,
                    float(infer_mu_init[i] * 100),
                    0.5,
                    key=f"infer_mu_{i}",
                )
                edited_mu.append(v / 100)
        with col_vols:
            st.markdown("**⚠️ Volatilités (%)**")
            for i, name in enumerate(assets_names):
                v = st.slider(
                    f"σ — {name}",
                    1.0,
                    100.0,
                    float(infer_vol_init[i] * 100),
                    0.5,
                    key=f"infer_vol_{i}",
                )
                edited_vol.append(v / 100)

    edited_mu = np.array(edited_mu)
    edited_vol = np.array(edited_vol)

    base_vol = np.array(metadata["base_vol"])
    base_cov = np.array(metadata["base_cov"])
    corr_ref = base_cov / np.outer(base_vol + 1e-8, base_vol + 1e-8)
    np.fill_diagonal(corr_ref, 1.0)
    cov_live = np.diag(edited_vol) @ corr_ref @ np.diag(edited_vol)
    eigvals, eigvecs = np.linalg.eigh(cov_live)
    eigvals = np.maximum(eigvals, 1e-10)
    cov_live = eigvecs @ np.diag(eigvals) @ eigvecs.T

    config_path = os.path.join(os.path.dirname(__file__), "config-policy.txt")
    neat_config = load_neat_config(config_path)
    weights = policy_to_allocation(
        genome,
        neat_config,
        edited_mu,
        edited_vol,
        cov_live,
        config["w_return"],
        config["risk_free_rate"],
        n_assets_inf,
    )

    ret = float(weights @ edited_mu) * 100
    risk = float(np.sqrt(weights @ cov_live @ weights)) * 100
    rf = config["risk_free_rate"]
    sharpe = (ret / 100 - rf) / (risk / 100 + 1e-8) if risk > 0 else 0.0

    st.write("")
    section_label("Allocation proposée par la politique apprise")

    if simple_mode:
        c1, c2 = st.columns(2)
        c1.metric("💰 Rendement attendu", f"{ret:.2f} % / an")
        c2.metric("⚠️ Niveau de risque", f"{risk:.2f} %")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Rendement R_p", f"{ret:.2f} %")
        c2.metric("Volatilité σ_p", f"{risk:.2f} %")
        c3.metric(f"Sharpe (r_f={rf*100:.1f}%)", f"{sharpe:.2f}")

    alloc_df = pd.DataFrame(
        {
            ("Placement" if simple_mode else "Actif"): assets_names,
            ("Pourcentage (%)" if simple_mode else "Allocation (%)"): np.round(
                weights * 100, 2
            ),
        }
    ).sort_values(by=1, axis=0, ascending=False, ignore_index=False)
    alloc_df = alloc_df.sort_values(by=alloc_df.columns[1], ascending=False)
    alloc_df_filtered = alloc_df[alloc_df.iloc[:, 1] > 0.1]
    if alloc_df_filtered.empty:
        alloc_df_filtered = alloc_df.head(3)

    col_t, col_d = st.columns([1, 1], gap="large")
    with col_t:
        st.dataframe(
            alloc_df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                alloc_df_filtered.columns[1]: st.column_config.ProgressColumn(
                    format="%.2f %%",
                    min_value=0.0,
                    max_value=float(alloc_df_filtered.iloc[:, 1].max()),
                ),
            },
        )
    with col_d:
        donut = build_allocation_donut(alloc_df_filtered, "Politique NEAT", simple_mode)
        st.plotly_chart(donut, use_container_width=True)

    if (
        st.session_state.neat_history is not None
        and len(st.session_state.neat_history["max"]) > 0
    ):
        st.write("")
        with st.expander("📊 Courbe de convergence de l'apprentissage", expanded=False):
            _draw_final_fitness_curve(st.session_state.neat_history, simple_mode)


def _draw_final_fitness_curve(history, simple_mode):
    p = get_palette(simple_mode)
    gens = list(range(1, len(history["max"]) + 1))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=gens,
            y=history["max"],
            mode="lines+markers",
            name="Meilleur" if simple_mode else "f_max",
            line=dict(color=p["accent"], width=2.5),
            marker=dict(size=6),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=gens,
            y=history["mean"],
            mode="lines",
            name="Moyenne" if simple_mode else "f_avg",
            line=dict(color=p["moep"], width=2, dash="dot"),
        )
    )
    if not simple_mode and "species" in history:
        fig.add_trace(
            go.Scatter(
                x=gens,
                y=history["species"],
                mode="lines",
                name="Espèces",
                line=dict(color=p["nsga"], width=1.5, dash="dash"),
                yaxis="y2",
            )
        )
        fig.update_layout(
            yaxis2=dict(
                title=dict(text="Espèces", font=dict(color=p["nsga"], size=11)),
                overlaying="y",
                side="right",
                gridcolor="rgba(0,0,0,0)",
                tickfont=dict(color=p["nsga"], size=10),
            ),
        )

    fig.update_layout(
        template=p["plotly_template"],
        plot_bgcolor=p["plot_bg"],
        paper_bgcolor=p["paper_bg"],
        height=320,
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(
            title=dict(
                text="Génération", font=dict(color=p["text_secondary"], size=11)
            ),
            gridcolor=p["grid"],
        ),
        yaxis=dict(
            title=dict(text="Fitness", font=dict(color=p["text_secondary"], size=11)),
            gridcolor=p["grid"],
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.25,
            font=dict(color=p["text_secondary"]),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    st.plotly_chart(fig, use_container_width=True)
