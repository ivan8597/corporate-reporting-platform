from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from pipeline.orchestrator import run_pipeline
from services.report_store import report_store

app = FastAPI(
    title="Corporate Reporting Platform",
    description="Автоматизация корпоративной отчётности",
    version="1.2",
)
templates = Jinja2Templates(directory="templates")


class AnomalyResponse(BaseModel):
    status: str
    count: int
    anomalies: list[dict[str, Any]] = Field(default_factory=list)


class GenerateResponse(BaseModel):
    status: str
    report_path: str
    rows: int
    duration_seconds: float
    kpis: dict[str, Any]
    anomalies: int


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    kpis = report_store.get_kpis()
    anomalies = report_store.get_anomalies()
    anomaly_count = 0
    if anomalies is not None:
        anomaly_count = int((anomalies["anomaly_label"] == "Аномалия").sum())

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "revenue": kpis.get("Total_Revenue", 0),
            "margin": kpis.get("Avg_Margin_%", 0),
            "mom": f"{kpis['MoM_Growth_%']} %" if "MoM_Growth_%" in kpis else "N/A",
            "orders": kpis.get("Total_Orders", 0),
            "anomalies": anomaly_count,
        },
    )


@app.post("/generate", response_model=GenerateResponse)
def generate() -> GenerateResponse:
    result = run_pipeline(init_demo_data=False, save_ml_artifacts=True)
    report_store.update(
        report_path=result.report_path,
        kpis=result.kpis,
        anomalies=result.anomalies,
    )
    anomaly_count = int((result.anomalies["anomaly_label"] == "Аномалия").sum())
    return GenerateResponse(
        status="success",
        report_path=result.report_path,
        rows=len(result.clean_df),
        duration_seconds=round(result.duration_seconds, 3),
        kpis=result.kpis,
        anomalies=anomaly_count,
    )


@app.post("/generate/view", response_class=RedirectResponse)
def generate_view() -> RedirectResponse:
    generate()
    return RedirectResponse(url="/", status_code=303)


@app.get("/anomalies", response_model=AnomalyResponse)
def anomalies() -> AnomalyResponse:
    anomaly_df = report_store.get_anomalies()
    if anomaly_df is None:
        return AnomalyResponse(status="not_ready", count=0)

    filtered = anomaly_df.loc[anomaly_df["anomaly_label"] == "Аномалия"].copy()
    if "date" in filtered.columns:
        filtered["date"] = filtered["date"].astype(str)
    return AnomalyResponse(
        status="ready",
        count=len(filtered),
        anomalies=filtered.to_dict(orient="records"),
    )


@app.get("/download")
def download():
    report_path = report_store.get_report_path()
    if report_path is None:
        return {"error": "Отчёт ещё не создан."}

    report = Path(report_path)
    if not report.exists():
        return {"error": "Файл отчёта не найден."}

    return FileResponse(
        path=report,
        filename=report.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
