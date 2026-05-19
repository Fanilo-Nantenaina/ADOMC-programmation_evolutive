import numpy as np
import plotly.graph_objects as go

from app.config import get_palette
from app.core import weighted_topsis


def build_animated_figure(
    raw_results,
    n_gen,
    ui_mu,
    ui_vol,
    w_return,
    w_risk,
    max_risk_val,
    simple_mode: bool,
    fps: int,
):
    p = get_palette(simple_mode)
    x_max = max(ui_vol) * 110
    y_max = max(ui_mu) * 110
    frame_duration_ms = max(33, int(1000 / fps))

    def traces_for_step(step):
        traces = []
        for name, res in raw_results.items():
            if not res.history or step >= len(res.history):
                continue
            pop = res.history[step].pop
            F = pop.get("F")
            returns = -F[:, 0] * 100
            risks = F[:, 1] * 100

            best_idx = weighted_topsis(returns, risks, w_return / 100, w_risk / 100)

            if name == "MOEP":
                color = p["moep"]
                color_best = p["moep_best"]
            else:
                color = p["nsga"]
                color_best = p["nsga_best"]

            traces.append(
                go.Scatter(
                    x=risks,
                    y=returns,
                    mode="markers",
                    marker=dict(
                        color=color,
                        opacity=0.55,
                        size=9,
                        line=dict(color=color, width=0),
                    ),
                    name=("Portefeuille testé" if simple_mode else f"Front ({name})"),
                    hovertemplate="Risque: %{x:.2f}%<br>Rendement: %{y:.2f}%<extra></extra>",
                )
            )
            traces.append(
                go.Scatter(
                    x=[risks[best_idx]],
                    y=[returns[best_idx]],
                    mode="markers",
                    marker=dict(
                        color=color_best,
                        size=20,
                        symbol="star",
                        line=dict(color="white" if simple_mode else "#0B0F19", width=2),
                    ),
                    name=(
                        "Meilleur choix trouvé"
                        if simple_mode
                        else f"Compromis TOPSIS ({name})"
                    ),
                    hovertemplate="<b>%{text}</b><br>Risque: %{x:.2f}%<br>Rendement: %{y:.2f}%<extra></extra>",
                    text=[f"Best — {name}"],
                )
            )
        return traces

    frames = [
        go.Frame(data=traces_for_step(step), name=str(step + 1))
        for step in range(n_gen)
    ]
    fig = go.Figure(data=traces_for_step(0), frames=frames)

    if max_risk_val is not None:
        fig.add_vline(
            x=max_risk_val * 100,
            line_dash="dash",
            line_color=p["constraint"],
            line_width=2,
            annotation_text=(
                "Limite de sécurité" if simple_mode else "Contrainte de risque"
            ),
            annotation_position="top",
            annotation=dict(font=dict(color=p["constraint"], size=11)),
        )

    fig.update_layout(
        title=dict(
            text=(
                "L'IA cherche la meilleure répartition"
                if simple_mode
                else "Dynamique temporelle des fronts de compromis"
            ),
            font=dict(size=18, color=p["text_primary"], family="Inter"),
            x=0.02,
            xanchor="left",
        ),
        xaxis=dict(
            title=dict(
                text=(
                    "Niveau de risque global (%)"
                    if simple_mode
                    else "Volatilité σ_p (%) — à minimiser"
                ),
                font=dict(size=12, color=p["text_secondary"]),
            ),
            range=[0, x_max],
            gridcolor=p["grid"],
            zerolinecolor=p["grid"],
            tickfont=dict(color=p["text_secondary"], size=11),
        ),
        yaxis=dict(
            title=dict(
                text=(
                    "Rendement espéré (%)"
                    if simple_mode
                    else "Rendement E[R_p] (%) — à maximiser"
                ),
                font=dict(size=12, color=p["text_secondary"]),
            ),
            range=[0, y_max],
            gridcolor=p["grid"],
            zerolinecolor=p["grid"],
            tickfont=dict(color=p["text_secondary"], size=11),
        ),
        template=p["plotly_template"],
        plot_bgcolor=p["plot_bg"],
        paper_bgcolor=p["paper_bg"],
        margin=dict(l=60, r=40, t=60, b=110),
        height=520,
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=1.08,
            font=dict(size=11, color=p["text_secondary"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.0,
                y=-0.18,
                xanchor="left",
                yanchor="top",
                showactive=False,
                pad=dict(r=10, t=10),
                bgcolor=p["bg_card"],
                bordercolor=p["border"],
                font=dict(color=p["text_primary"], size=11),
                buttons=[
                    dict(
                        label="▶  Lecture",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=frame_duration_ms, redraw=True),
                                fromcurrent=True,
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                    dict(
                        label="⏸  Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                ],
            )
        ],
        sliders=[
            dict(
                active=0,
                currentvalue=dict(
                    prefix=("Étape " if simple_mode else "Génération ") + ": ",
                    visible=True,
                    xanchor="right",
                    font=dict(color=p["text_secondary"], size=11),
                ),
                x=0.18,
                y=-0.18,
                len=0.78,
                xanchor="left",
                yanchor="top",
                pad=dict(t=10),
                bgcolor=p["border"],
                bordercolor=p["border"],
                font=dict(color=p["text_secondary"], size=10),
                steps=[
                    dict(
                        method="animate",
                        label=str(step + 1),
                        args=[
                            [str(step + 1)],
                            dict(
                                frame=dict(duration=0, redraw=True),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    )
                    for step in range(n_gen)
                ],
            )
        ],
    )
    return fig


def build_pareto_front_figure(
    returns_pct,
    risks_pct,
    best_return,
    best_risk,
    algo_name,
    max_risk_val,
    simple_mode: bool,
):
    """Trace le front de Pareto final avec compromis TOPSIS surligné."""
    p = get_palette(simple_mode)
    color = p["moep"] if algo_name == "MOEP" else p["nsga"]
    color_best = p["moep_best"] if algo_name == "MOEP" else p["nsga_best"]

    order = np.argsort(risks_pct)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=risks_pct[order],
            y=returns_pct[order],
            mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(
                color=color,
                size=9,
                line=dict(color="white" if simple_mode else "#0B0F19", width=1),
            ),
            name="Front de Pareto",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[best_risk],
            y=[best_return],
            mode="markers",
            marker=dict(
                color=color_best,
                size=22,
                symbol="star",
                line=dict(color="white" if simple_mode else "#0B0F19", width=2),
            ),
            name="Compromis TOPSIS retenu",
        )
    )
    if max_risk_val is not None:
        fig.add_vline(
            x=max_risk_val * 100,
            line_dash="dash",
            line_color=p["constraint"],
            line_width=2,
            annotation_text="Contrainte",
            annotation=dict(font=dict(color=p["constraint"], size=11)),
        )

    fig.update_layout(
        title=dict(
            text=f"Front de Pareto final — {algo_name}",
            font=dict(size=15, color=p["text_primary"], family="Inter"),
            x=0.02,
            xanchor="left",
        ),
        xaxis=dict(
            title=dict(
                text="Risque (%)",
                font=dict(color=p["text_secondary"], size=12),
            ),
            gridcolor=p["grid"],
            zerolinecolor=p["grid"],
            tickfont=dict(color=p["text_secondary"], size=11),
        ),
        yaxis=dict(
            title=dict(
                text="Rendement (%)",
                font=dict(color=p["text_secondary"], size=12),
            ),
            gridcolor=p["grid"],
            zerolinecolor=p["grid"],
            tickfont=dict(color=p["text_secondary"], size=11),
        ),
        template=p["plotly_template"],
        plot_bgcolor=p["plot_bg"],
        paper_bgcolor=p["paper_bg"],
        height=380,
        margin=dict(l=50, r=30, t=50, b=40),
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.18,
            font=dict(size=11, color=p["text_secondary"]),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


def build_allocation_donut(summary_df, algo_name, simple_mode: bool):
    """Donut chart des allocations majoritaires."""
    p = get_palette(simple_mode)

    base_color = p["moep"] if algo_name == "MOEP" else p["nsga"]
    n = len(summary_df)
    colors = [base_color] * n
    opacities = np.linspace(1.0, 0.45, n) if n > 1 else [1.0]

    def _to_rgba(hex_color, alpha):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    final_colors = [_to_rgba(c, o) for c, o in zip(colors, opacities)]

    labels = summary_df.iloc[:, 0].tolist()
    values = summary_df.iloc[:, 1].tolist()

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.6,
                marker=dict(
                    colors=final_colors, line=dict(color=p["bg_primary"], width=2)
                ),
                textfont=dict(color=p["text_primary"], family="Inter", size=11),
                hovertemplate="<b>%{label}</b><br>%{value:.2f}%<extra></extra>",
                sort=False,
            )
        ]
    )
    fig.update_layout(
        template=p["plotly_template"],
        plot_bgcolor=p["paper_bg"],
        paper_bgcolor=p["paper_bg"],
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.0,
            xanchor="right",
            y=0.5,
            yanchor="middle",
            font=dict(size=11, color=p["text_secondary"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        annotations=[
            dict(
                text=f"<b>{algo_name}</b>",
                x=0.5,
                y=0.5,
                font=dict(size=14, color=p["text_primary"], family="Inter"),
                showarrow=False,
            )
        ],
    )
    return fig
