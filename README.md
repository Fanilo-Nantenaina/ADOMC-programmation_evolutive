# SID — Optimisation Évolutive de Portefeuille

Système d'Aide à la Décision multi-objectif pour la sélection de portefeuille
au sens de Markowitz, intégrant **trois approches évolutionnaires complémentaires** :

1. **MOEP** (Multi-Objective Evolutionary Programming, Fogel-style) — optimisation
   directe du vecteur de poids, mutation auto-adaptative log-normale.
2. **NSGA-II** — tri non-dominé + crowding (référence pymoo).
3. **NEAT-Portfolio** — _fusion conceptuelle avec la philosophie neuroevolution_ :
   on évolue **un réseau de neurones qui calcule l'allocation** à partir de
   l'état du marché. Entraînement multi-scénarios → politique généralisable.

Arbitrage final par **TOPSIS pondéré** (Hwang & Yoon, 1981) et indicateurs
**Hypervolume / IGD** pour la qualité du front.

## Lancement

```bash
cd sid_app
pip install -r requirements.txt
streamlit run app.py
```

## Architecture

```
sid_app/
├── app.py              # Point d'entrée Streamlit (5 onglets)
├── config.py           # Constantes + palettes de couleurs
├── styles.py           # CSS (glassmorphism, Inter font) + hero
├── core.py             # MOEP, NSGA-II, math (pymoo)
├── neat_core.py        # Encoding + entraînement NEAT (multi-scénarios)
├── neat_manager.py     # Persistence des politiques apprises
├── config-policy.txt   # Hyper-paramètres NEAT
├── sidebar.py          # Sidebar adaptative
├── viz.py              # Animations Plotly (frames natives)
├── tab_config.py       # Onglet 1 : actifs + corrélations
├── tab_theory.py       # Onglet 2 : explications (simple ↔ expert)
├── tab_exec.py         # Onglet 3 : MOEP/NSGA-II + animation
├── tab_policy.py       # Onglet 4 : NEAT + inférence live
└── tab_analysis.py     # Onglet 5 : rapport TOPSIS + export Excel
```

## Modes

- **Mode Découverte** (toggle activé) : palette pastel haut de gamme,
  langage non-technique, masque LaTeX/HV/IGD.
- **Mode Expert** (par défaut) : palette dark sophistiquée, formules LaTeX,
  indicateurs HV/IGD, terminologie scientifique.

## Trois paradigmes côte à côte

| Aspect                   | MOEP / NSGA-II                 | NEAT-Portfolio                            |
| ------------------------ | ------------------------------ | ----------------------------------------- |
| **Ce qui évolue**        | Vecteur de poids $\mathbf{w}$  | Réseau de neurones $\phi_\theta$          |
| **Sortie**               | $\mathbf{w}^*$ pour 1 scénario | $\phi^*: (\mu,\Sigma) \mapsto \mathbf{w}$ |
| **Changement de marché** | Re-lancer l'optimisation       | Forward pass O(1)                         |
| **Multi-objectif**       | ✅ Pareto front complet        | ❌ Scalaire (Sharpe + utilité − HHI)      |
| **Arbitrage TOPSIS**     | Sur le front Pareto            | Non applicable                            |

Les deux approches sont **complémentaires** : MOEP/NSGA-II pour la décision
ponctuelle multicritère, NEAT pour la politique généralisable.

## Distinctions algorithmiques MOEP vs NSGA-II

| Aspect                     | MOEP (Fogel-style)                             | NSGA-II                                |
| -------------------------- | ---------------------------------------------- | -------------------------------------- |
| Croisement                 | ❌ Aucun                                       | ✅ SBX                                 |
| Mutation                   | Gaussienne auto-adaptative log-normale         | Polynomiale (PM)                       |
| Sélection environnementale | Tournoi q-stochastique sur Pareto              | Tri non-dominé + crowding déterministe |
| σ                          | Vecteur par individu, mute lui-même (Schwefel) | Fixe                                   |
