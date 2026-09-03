from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from pipeline.orchestrator import run_pipeline
from services.report_store import report_store

app = FastAPI(
    title="Corporate Reporting Platform",
    description="Автоматизация корпоративной отчётности",
    version="1.1",
)


@app.get("/", response_class=HTMLResponse)
def home():
    kpis = report_store.get_kpis()
    revenue = kpis.get("Total_Revenue", 0)
    margin = kpis.get("Avg_Margin_%", 0)
    orders = kpis.get("Total_Orders", 0)
    mom = kpis.get("MoM_Growth_%")
    mom_display = f"{mom} %" if mom is not None else "N/A"

    return f"""
    <html>
        <head>
            <title>Corporate Reporting Platform</title>
            <style>
                body {{
                    font-family: Arial;
                    margin: 40px;
                }}
                .card {{
                    padding:20px;
                    border-radius:10px;
                    background:#f2f2f2;
                    width:420px;
                }}
                button {{
                    padding:12px;
                    background:#1976d2;
                    color:white;
                    border:none;
                    border-radius:5px;
                    cursor: pointer;
                }}
            </style>
        </head>
        <body>
        <h1>📊 Корпоративная платформа отчётности</h1>
        <form action="/generate" method="post">
            <button type="submit">Сгенерировать отчёт</button>
        </form>
        <br>
        <div class="card">
        <h2>KPI</h2>
        <p>💰 Выручка: {revenue} ₽</p>
        <p>📈 Маржа: {margin} %</p>
        <p>📉 MoM рост: {mom_display}</p>
        <p>📦 Заказы: {orders}</p>
        <p>
            <a href="/download">
                <button type="button">Скачать последний Excel-отчёт</button>
            </a>
        </p>
        </div>
        </body>
    </html>
    """


@app.post("/generate")
def generate():
    result = run_pipeline(init_demo_data=False, save_ml_artifacts=True)
    report_store.update(
        report_path=result.report_path,
        kpis=result.kpis,
        anomalies=result.anomalies,
    )
    return RedirectResponse(url="/", status_code=303)


@app.get("/anomalies")
def anomalies():
    anomaly_df = report_store.get_anomalies()
    if anomaly_df is None:
        return {"status": "not_ready", "count": 0, "anomalies": []}

    filtered = anomaly_df.loc[anomaly_df["anomaly_label"] == "Аномалия"].copy()
    if "date" in filtered.columns:
        filtered["date"] = filtered["date"].astype(str)

    records = filtered.to_dict(orient="records")
    return {
        "status": "ready",
        "count": len(filtered),
        "anomalies": records,
    }


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
