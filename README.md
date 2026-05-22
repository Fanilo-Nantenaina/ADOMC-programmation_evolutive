# SID — Optimisation Évolutive de Portefeuille

Architecture découplée :

- **Backend** FastAPI (Python) avec streaming SSE génération-par-génération
- **Frontend** Next.js 14 App Router (TypeScript, Tailwind, shadcn/ui, Recharts)

Trois paradigmes algorithmiques intégrés, mathématiques préservées à l'identique
depuis la version Streamlit historique :

- **MOEP** — Programmation Évolutive Multi-Objectif (Fogel-style, σ auto-adaptatif Schwefel, tournoi q-stochastique)
- **NSGA-II** — référence comparative
- **NEAT-Policy** — NeuroEvolution of Augmenting Topologies entraînant un réseau de neurones qui mappe l'état du marché à une allocation généralisable (l'IA apprend des **principes** plutôt qu'une réponse pour un état donné)

Avec arbitrage **TOPSIS pondéré**, projection PSD de la covariance, indicateurs Hypervolume / IGD, et export Excel stylé.

## Structure du projet

```text
sid_platform/
├── backend/                              FastAPI
│   ├── app/
│   │   ├── main.py                       Entry, CORS, routers
│   │   ├── api/
│   │   │   ├── correlation.py            POST /api/validate-correlation
│   │   │   ├── simulate.py               POST /api/simulate  (SSE)
│   │   │   ├── report.py                 POST /api/export-report
│   │   │   └── neat.py                   /api/neat/{train,infer,status}
│   │   ├── core/
│   │   │   ├── psd.py                    Projection spectrale PSD
│   │   │   ├── topsis.py                 TOPSIS pondéré (MinMaxScaler + L2)
│   │   │   ├── problem.py                PortfolioProblem (pymoo)
│   │   │   ├── algorithms.py             MOEP + EPTournamentSurvival
│   │   │   ├── indicators.py             HV / IGD
│   │   │   ├── neat_core.py              Politique NEAT (env, eval, scénarios)
│   │   │   └── config-policy.txt         Hyper-paramètres NEAT
│   │   └── schemas/
│   │       ├── inputs.py                 Pydantic requests
│   │       └── outputs.py                Pydantic responses + SSE
│   └── requirements.txt
│
└── frontend/                             Next.js 14 + Tailwind
    ├── app/
    │   ├── layout.tsx                    Root layout (Geist font + Providers)
    │   ├── page.tsx                      Orchestration (sidebar + sections)
    │   └── globals.css                   Tailwind `@theme inline` + oklch
    ├── components/
    │   ├── pareto-stream-chart.tsx       ★ Graphe SSE Pareto (Recharts SVG)
    │   ├── neat-training-chart.tsx       Courbe fitness NEAT
    │   ├── allocation-donut.tsx          Donut d'allocation
    │   ├── playback-control.tsx          Slider replay des générations
    │   ├── metric-card.tsx               Carte de métrique
    │   ├── sidebar-nav.tsx               Sidebar verticale + StepperMobile
    │   ├── hero.tsx                      Header de page
    │   ├── theme-toggle.tsx              Toggle CSS-only (zéro hydration mismatch)
    │   ├── mode-toggle.tsx               Toggle Simple/Expert
    │   ├── providers.tsx                 ThemeProvider + Toaster Sonner
    │   ├── sections/
    │   │   ├── config-section.tsx        Étape 1 : actifs + matrice + PSD live
    │   │   ├── theory-section.tsx        Étape 2 : pédagogie (simple) / formules (expert)
    │   │   ├── simulate-section.tsx      Étape 3 : MOEP/NSGA-II live + replay
    │   │   ├── policy-section.tsx        Étape 4 : entraînement NEAT + inférence
    │   │   └── report-section.tsx        Étape 5 : rapport TOPSIS + export Excel
    │   └── ui/                           Primitives shadcn (button, card, slider, …)
    ├── lib/
    │   ├── api.ts                        Client backend + parser SSE
    │   ├── store.ts                      Zustand global state
    │   ├── types.ts                      Miroir des schémas Pydantic
    │   └── utils.ts                      cn() helper
    ├── package.json
    ├── tsconfig.json
    ├── next.config.mjs                   (pas de rewrite — appels directs au backend)
    ├── postcss.config.mjs                Tailwind (`@tailwindcss/postcss`)
    └── components.json                   shadcn config (Tailwind, config="")
```

> **Pas de `tailwind.config.ts`** : Tailwind inline toute la configuration dans
> `app/globals.css` via les directives `@theme inline` et `@custom-variant`.

## Démarrage rapide

### 1. Backend FastAPI

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Endpoints exposés sur `http://localhost:8000` :

| Méthode | URL                         | Description                                                        |
| ------- | --------------------------- | ------------------------------------------------------------------ |
| `GET`   | `/health`                   | Sanity check                                                       |
| `POST`  | `/api/validate-correlation` | Validation matrice + correction PSD live                           |
| `POST`  | `/api/simulate`             | **SSE** streaming génération-par-génération (MOEP + NSGA-II)       |
| `POST`  | `/api/export-report`        | Excel stylé (4 feuilles : Config, Pareto, Allocation, Indicateurs) |
| `POST`  | `/api/neat/train`           | **SSE** streaming entraînement NEAT                                |
| `POST`  | `/api/neat/infer`           | Inférence : état du marché → allocation                            |
| `GET`   | `/api/neat/status`          | Politique entraînée disponible ?                                   |
| `GET`   | `/docs`                     | Swagger UI interactif                                              |

### 2. Frontend Next.js

```bash
cd frontend
cp .env.example .env.local        # facultatif
pnpm install
pnpm dev                          # http://localhost:3000
```

Le frontend appelle directement le backend via `http://localhost:8000`
(configurable par `NEXT_PUBLIC_API_URL`). Le CORS du backend whitelist
`localhost:3000`, donc le cross-origin fonctionne sans rewrites Next.

## Architecture des trois paradigmes

### MOEP (Fogel-style)

- **Pas de croisement** — chaque parent produit un enfant par mutation seule
- **σ auto-adaptatif log-normal** (Schwefel) : `σ′(k) = σ(k)·exp(τ′·N + τ·Nₖ)` avec `τ′=1/√(2n), τ=1/√(2√n)`
- **Tournoi (μ+λ) q-stochastique** sur dominance Pareto avec crowding pour départage

### NSGA-II (référence)

Standard pymoo. Conservé pour comparaison HV / IGD.

### NEAT-Policy

Le réseau évolué prend en entrée un vecteur de 50 dimensions encodant l'état du marché :

- 12 × rendements normalisés
- 12 × volatilités normalisées
- 12 × corrélations moyennes par actif
- 12 × masque d'activation (n_assets ≤ 12)
- 2 × contexte (profil rendement, taux sans risque)

Et produit 12 logits → softmax sur les actifs actifs → allocation valide (simplexe).

L'entraînement multi-scénarios force la **généralisation** : le réseau ne mémorise pas
une réponse mais apprend les principes d'arbitrage rendement/risque/diversification.

Fitness composite : `f = E_scen[ Sharpe + 2·utilité_profil − 0.3·HHI ]`

## UX details qui valent la peine d'être notés

- **Frame pacing** : le paramètre `frame_delay_ms` côté backend ralentit le SSE pour rendre la convergence visuellement digeste (défaut 150 ms ≈ 6 FPS). Réglable depuis l'UI.
- **Replay slider** : après la simulation, on peut scrubber n'importe quelle génération passée pour analyser la dynamique de convergence.
- **Mode Simple / Expert strictement découplé du thème dark/light** : deux toggles indépendants.
- **Slider visibles** : track contrasté en `bg-foreground/15` pour rester lisible sur palettes oklch greyscale.
- **Hydration zéro mismatch** : `ThemeToggle` utilise des icônes CSS empilées (Sun + Moon en surimpression, visibilité contrôlée par `.dark`). Aucun state, aucun risque de divergence SSR/CSR.

## Production

- Backend : `uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000`
- Frontend : `pnpm build && pnpm start`
- Restreindre `allow_origins` dans `app/main.py` au domaine de prod
- Reverse proxy Nginx : `proxy_buffering off;` sur la route `/api/simulate` et `/api/neat/train` (SSE)
- Pour la persistance des politiques NEAT en multi-instance, remplacer le store en mémoire de `app/api/neat.py` par Redis ou disque

## Test rapide du backend (cURL)

```bash
# Health
curl http://localhost:8000/health

# Validation PSD
curl -X POST http://localhost:8000/api/validate-correlation \
  -H 'Content-Type: application/json' \
  -d '{"asset_names":["A","B"],"volatilities":[0.2,0.3],"correlation_matrix":[[1,0.5],[0.5,1]]}'

# Streaming SSE simulation
curl -N -X POST http://localhost:8000/api/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "assets":[{"name":"A","expected_return_pct":20,"volatility_pct":25},{"name":"B","expected_return_pct":5,"volatility_pct":8}],
    "correlation_matrix":[[1,0.3],[0.3,1]],
    "algorithm":"both","pop_size":40,"n_gen":15,"seed":42,
    "w_return":60,"risk_free_rate":0.02,"frame_delay_ms":0
  }'

# Status politique NEAT
curl http://localhost:8000/api/neat/status
```
