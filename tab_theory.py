"""
Onglet 2 — Explications théoriques.

Le contenu se transfigure complètement entre simple et expert :
- Simple : analogies visuelles, pas de LaTeX, pas de jargon
- Expert : formules mathématiques, classes d'algorithmes, contraintes
"""

import streamlit as st

from styles import section_label


def render_tab_theory(simple_mode: bool) -> None:
    """Affiche l'onglet d'explication théorique."""
    if simple_mode:
        _render_simple()
    else:
        _render_expert()


def _render_simple() -> None:
    st.markdown("### 📚 Comprendre comment ça marche")

    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        with st.container(border=True):
            st.markdown("#### 🎯 La frontière du choix parfait")
            st.markdown(
                "Imaginez des milliers de répartitions possibles de votre argent, "
                "représentées par des points sur un graphique : **rendement vs risque**."
            )
            st.markdown(
                "La plupart sont mauvaises (peu de gain, beaucoup de risque). "
                "Mais certaines forment une **courbe parfaite** où il devient impossible "
                "de gagner plus sans accepter plus de risque."
            )
            st.success(
                "C'est cette courbe que notre IA recherche : **les choix où plus rien ne se sacrifie inutilement**."
            )

    with col_b:
        with st.container(border=True):
            st.markdown("#### ⚖️ L'arbitre neutre")
            st.markdown(
                "Une fois la courbe trouvée, comment choisir LE point qui vous convient ?"
            )
            st.markdown(
                "Un système d'arbitrage compare chaque point à deux références : "
                "le **paradis financier** (max de gain, zéro risque) et "
                "l'**enfer financier** (zéro gain, max de risque)."
            )
            st.info(
                "Le meilleur point est celui qui est **le plus proche du paradis** "
                "et **le plus loin de l'enfer**, en tenant compte de vos préférences."
            )

    st.write("")
    with st.container(border=True):
        st.markdown("#### 🧬 L'intelligence évolutive")
        st.markdown(
            "L'IA fonctionne comme la sélection naturelle : elle crée une population "
            "de portefeuilles, garde les meilleurs, les fait muter légèrement, et recommence."
        )
        st.markdown(
            "Au fil des générations, la population se rapproche automatiquement de la **courbe parfaite**. "
            "Vous pouvez observer ce processus en action dans l'onglet suivant !"
        )

    st.write("")
    with st.container(border=True):
        st.markdown("#### 🧠 La règle qui s'adapte (Politique IA)")
        st.markdown(
            "Dans l'onglet **Politique IA**, l'approche est différente. Au lieu de trouver "
            "*une* bonne répartition pour *un* scénario, on entraîne une IA qui apprend "
            "**une règle générale**."
        )
        st.markdown(
            "Imaginez la différence entre :\n"
            "- **Mémoriser** la réponse à un problème de maths (limité à ce problème), et\n"
            "- **Apprendre** la méthode (applicable à n'importe quel problème similaire).\n\n"
            "C'est exactement la différence : une fois la règle apprise, vous pouvez "
            "changer vos hypothèses en direct et obtenir instantanément une nouvelle "
            "répartition cohérente — sans recalcul."
        )


def _render_expert() -> None:
    st.markdown("### 🧮 Fondations mathématiques et architecture")

    with st.container(border=True):
        col_a, col_b = st.columns([1, 1.2])
        with col_a:
            section_label("Modèle de Markowitz")
            st.markdown("**Problème bi-objectif :**")
            st.latex(r"\max_{\mathbf{w}} \; R_p = \mathbf{w}^T \boldsymbol{\mu}")
            st.latex(
                r"\min_{\mathbf{w}} \; \sigma_p = \sqrt{\mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w}}"
            )
            st.markdown(r"sous $\sum_i w_i = 1$, $w_i \geq 0$.")
        with col_b:
            section_label("Variables & contraintes")
            st.markdown(
                "- $\\boldsymbol{\\mu} \\in \\mathbb{R}^n$ : vecteur des rendements espérés\n"
                "- $\\boldsymbol{\\Sigma} \\in \\mathbb{R}^{n \\times n}$ : matrice de covariance (PSD)\n"
                "- $\\mathbf{w} \\in \\Delta^{n-1}$ : vecteur d'allocation simplexe\n"
                "- Contrainte optionnelle : $\\sigma_p \\leq \\sigma_{\\max}$"
            )

    st.write("")

    with st.container(border=True):
        col_a, col_b = st.columns([1, 1.2])
        with col_a:
            section_label("Arbitrage TOPSIS pondéré")
            st.latex(r"C_i^* = \frac{d_i^-}{d_i^+ + d_i^-}")
            st.latex(r"d_i^{\pm} = \sqrt{\sum_j w_j \, (n_{ij} - n_j^{\pm})^2}")
        with col_b:
            section_label("Logique")
            st.markdown(
                "TOPSIS (Hwang & Yoon, 1981) sélectionne la solution maximisant la "
                "**proximité relative** à l'idéal positif après normalisation min-max. "
                "Variante : pondération embarquée dans la distance euclidienne (norme L2 pondérée)."
            )
            st.markdown(
                "$n^+$ = (max rendement_norm, min risque_norm) — idéal positif  \n"
                "$n^-$ = (min rendement_norm, max risque_norm) — idéal négatif"
            )

    st.write("")

    with st.container(border=True):
        section_label("Programmation Évolutive Multi-Objectif (MOEP)")
        st.markdown(
            "Implémentation Fogel-style **structurellement distincte de NSGA-II** :"
        )
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**🚫 Pas de croisement**")
            st.caption(
                "Reproduction asexuée pure : chaque parent produit 1 enfant par mutation seule. "
                "C'est le marqueur définitoire de l'EP."
            )
        with col_b:
            st.markdown("**🔄 σ auto-adaptatif**")
            st.caption(
                "Chaque individu porte son propre vecteur σ qui mute lui-même selon la "
                "règle log-normale de Schwefel."
            )
        with col_c:
            st.markdown("**🥊 Tournoi stochastique**")
            st.caption(
                "Sélection (μ+λ) : chaque candidat affronte q adversaires aléatoires. "
                "Les μ avec le plus de victoires survivent."
            )

        st.write("")
        section_label("Auto-adaptation log-normale (Schwefel)")
        st.latex(
            r"\sigma_i'(k) = \sigma_i(k) \cdot \exp\bigl(\tau' \cdot \mathcal{N}(0,1) "
            r"+ \tau \cdot \mathcal{N}_k(0,1)\bigr)"
        )
        st.latex(
            r"\tau' = \frac{1}{\sqrt{2n}}, \quad \tau = \frac{1}{\sqrt{2\sqrt{n}}}"
        )

    st.write("")

    with st.container(border=True):
        section_label("Indicateurs de qualité du front")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Hypervolume (HV)**")
            st.caption(
                "Volume dominé par le front dans l'espace objectif, calculé avec un point "
                "de référence **invariant** (rendement nul, volatilité max individuelle). "
                "Comparable entre runs. Plus grand = mieux."
            )
        with col_b:
            st.markdown("**Inverted Generational Distance (IGD)**")
            st.caption(
                "Distance moyenne du front trouvé au front de référence approché "
                "(union non-dominée). **Relatif** : l'algo qui contribue le plus à "
                "l'union aura un IGD biaisé à la baisse. Plus petit = mieux."
            )

    st.write("")

    with st.container(border=True):
        section_label("Politique apprise par NeuroEvolution (NEAT)")
        st.markdown("**Inversion de paradigme** par rapport à MOEP/NSGA-II :")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown("**MOEP / NSGA-II**")
            st.latex(
                r"\mathbf{w}^* = \arg\max_{\mathbf{w}} \; f(\mathbf{w}; \boldsymbol{\mu}, \boldsymbol{\Sigma})"
            )
            st.caption(
                "Optimisation directe d'un vecteur de poids pour UN état de marché. "
                "Changer μ ou Σ → relancer l'optimisation."
            )
        with col_b:
            st.markdown("**NEAT-Portfolio**")
            st.latex(
                r"\phi_{\theta^*}: (\boldsymbol{\mu}, \boldsymbol{\Sigma}) \mapsto \mathbf{w}"
            )
            st.caption(
                "Évolution d'une politique φ paramétrée par un réseau de neurones. "
                "Entraînée une fois sur N scénarios → généralise à de nouveaux états sans ré-entraînement."
            )
        st.markdown(
            "**Multi-scénarios obligatoires** : la fitness d'un génome est la moyenne du "
            "Sharpe + utilité − HHI sur N scénarios échantillonnés autour de la configuration. "
            "Sans ce multi-sampling, NEAT dégénère en mémorisation de la configuration de base "
            "et perd tout intérêt vs MOEP."
        )
        st.markdown(
            "Différence opérationnelle clé : après entraînement, modifier μ ou σ dans l'UI "
            "déclenche une **inférence en O(1) forward pass** plutôt qu'une optimisation en "
            "O(pop_size × n_gen × n_eval)."
        )
