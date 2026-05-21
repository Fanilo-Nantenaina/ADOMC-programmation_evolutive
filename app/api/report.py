import io
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.inputs import ReportExportRequest

router = APIRouter()


@router.post("/export-report")
async def export_report(req: ReportExportRequest):
    if not req.results:
        raise HTTPException(status_code=400, detail="No results to export.")

    buffer = io.BytesIO()
    asset_names = [a.name for a in req.config.assets]

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        max_risk_str = (
            f"{req.config.max_risk_pct * 100:.0f} %"
            if req.config.max_risk_pct is not None
            else "Aucune"
        )
        df_config = pd.DataFrame(
            {
                "Paramètre Décisionnel": [
                    "Date de simulation",
                    "Seed",
                    "Population",
                    "Générations",
                    "Priorité Rendement",
                    "Priorité Risque",
                    "Taux sans risque",
                    "Algorithme",
                    "Contrainte de risque",
                    "Nombre d'actifs",
                ],
                "Valeur": [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    req.config.seed,
                    req.config.pop_size,
                    req.config.n_gen,
                    f"{req.config.w_return:.0f} %",
                    f"{100 - req.config.w_return:.0f} %",
                    f"{req.config.risk_free_rate * 100:.2f} %",
                    req.config.algorithm,
                    max_risk_str,
                    len(asset_names),
                ],
            }
        )
        df_config.to_excel(writer, sheet_name="Configuration", index=False)

        for algo_name, algo_data in req.results.items():
            if not isinstance(algo_data, dict):
                continue

            weights_matrix = algo_data.get("weights", [])
            returns = algo_data.get("returns_pct", [])
            risks = algo_data.get("risks_pct", [])

            if weights_matrix and returns and risks:
                df_pareto = pd.DataFrame(weights_matrix, columns=asset_names)
                df_pareto["Rendement_%"] = returns
                df_pareto["Risque_%"] = risks
                df_pareto.to_excel(
                    writer,
                    sheet_name=f"Pareto_{algo_name}"[:31],
                    index=False,
                )

            topsis = algo_data.get("topsis", {})
            if topsis and topsis.get("weights"):
                df_alloc = pd.DataFrame(
                    {
                        "Actif": asset_names,
                        "Allocation (%)": [w * 100 for w in topsis["weights"]],
                    }
                )
                df_alloc = df_alloc.sort_values("Allocation (%)", ascending=False)
                df_alloc.to_excel(
                    writer,
                    sheet_name=f"Allocation_{algo_name}"[:31],
                    index=False,
                )

        if req.indicators:
            rows = []
            for algo_name, ind in req.indicators.items():
                rows.append(
                    {
                        "Algorithme": algo_name,
                        "Hypervolume": ind.get("hv"),
                        "IGD": ind.get("igd"),
                    }
                )
            if rows:
                pd.DataFrame(rows).to_excel(
                    writer,
                    sheet_name="Indicateurs",
                    index=False,
                )

    buffer.seek(0)
    filename = f"Rapport_SID_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
