import numpy as np
import neat

MAX_N_ASSETS = 12

N_INPUTS = 4 * MAX_N_ASSETS + 2
N_OUTPUTS = MAX_N_ASSETS

EPSILON = 1e-8


def encode_market_state(mu, vol, cov, w_return, rf, n_assets):

    mu_padded = np.zeros(MAX_N_ASSETS)
    vol_padded = np.zeros(MAX_N_ASSETS)
    corr_padded = np.zeros(MAX_N_ASSETS)
    mask = np.zeros(MAX_N_ASSETS)

    mu_padded[:n_assets] = mu
    vol_padded[:n_assets] = vol
    mask[:n_assets] = 1.0

    if n_assets > 1:
        corr_matrix = cov / (np.outer(vol + EPSILON, vol + EPSILON))
        np.fill_diagonal(corr_matrix, 0.0)
        avg_corr = corr_matrix.sum(axis=1) / max(n_assets - 1, 1)
        corr_padded[:n_assets] = avg_corr

    mu_scale = max(np.abs(mu_padded).max(), EPSILON)
    vol_scale = max(np.abs(vol_padded).max(), EPSILON)
    mu_norm = mu_padded / mu_scale
    vol_norm = vol_padded / vol_scale
    corr_norm = (corr_padded + 1.0) / 2.0

    inputs = np.concatenate(
        [
            mu_norm,
            vol_norm,
            corr_norm,
            mask,
            np.array([w_return / 100.0, min(rf * 10, 1.0)]),
        ]
    )
    assert inputs.shape == (N_INPUTS,), f"Expected {N_INPUTS}, got {inputs.shape}"
    return inputs


def decode_allocation(raw_output, n_assets):

    active = np.array(raw_output[:n_assets], dtype=float)
    active = active - active.max()
    exp = np.exp(active)
    total = exp.sum()
    if total < EPSILON:
        return np.ones(n_assets) / n_assets
    return exp / total


def generate_scenarios(
    base_mu, base_vol, base_cov, n_scenarios, perturb_strength, seed
):

    rng = np.random.default_rng(seed)
    n_assets = len(base_mu)

    scenarios = [
        {
            "mu": base_mu.copy(),
            "vol": base_vol.copy(),
            "cov": base_cov.copy(),
            "n_assets": n_assets,
        }
    ]

    corr_base = base_cov / np.outer(base_vol + EPSILON, base_vol + EPSILON)

    for _ in range(n_scenarios - 1):
        mu_pert = base_mu * (1.0 + perturb_strength * rng.standard_normal(n_assets))
        vol_pert = base_vol * (
            1.0 + perturb_strength * np.abs(rng.standard_normal(n_assets))
        )
        vol_pert = np.maximum(vol_pert, 0.01)

        cov_pert = np.diag(vol_pert) @ corr_base @ np.diag(vol_pert)

        eigvals, eigvecs = np.linalg.eigh(cov_pert)
        eigvals = np.maximum(eigvals, 1e-10)
        cov_pert = eigvecs @ np.diag(eigvals) @ eigvecs.T

        scenarios.append(
            {
                "mu": mu_pert,
                "vol": vol_pert,
                "cov": cov_pert,
                "n_assets": n_assets,
            }
        )

    return scenarios


def evaluate_genome_on_scenarios(genome, config, scenarios, w_return, rf):

    net = neat.nn.FeedForwardNetwork.create(genome, config)
    fitnesses = []
    w_R = w_return / 100.0

    for scenario in scenarios:
        inputs = encode_market_state(
            scenario["mu"],
            scenario["vol"],
            scenario["cov"],
            w_return,
            rf,
            scenario["n_assets"],
        )
        raw = net.activate(inputs.tolist())
        weights = decode_allocation(raw, scenario["n_assets"])

        portfolio_return = float(weights @ scenario["mu"])
        portfolio_risk = float(np.sqrt(weights @ scenario["cov"] @ weights))

        sharpe = (portfolio_return - rf) / (portfolio_risk + EPSILON)
        utility = w_R * portfolio_return - (1.0 - w_R) * portfolio_risk
        hhi = float(np.sum(weights**2))

        fitness = sharpe + 2.0 * utility - 0.3 * hhi
        fitnesses.append(fitness)

    return float(np.mean(fitnesses))


def make_eval_function(scenarios, w_return, rf):

    def eval_genomes(genomes, config):
        for _, genome in genomes:
            genome.fitness = evaluate_genome_on_scenarios(
                genome,
                config,
                scenarios,
                w_return,
                rf,
            )

    return eval_genomes


def load_neat_config(config_path):
    """Charge la configuration NEAT depuis un fichier."""
    return neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )


def policy_to_allocation(genome, config, mu, vol, cov, w_return, rf, n_assets):
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    inputs = encode_market_state(mu, vol, cov, w_return, rf, n_assets)
    raw_output = net.activate(inputs.tolist())
    return decode_allocation(raw_output, n_assets)
