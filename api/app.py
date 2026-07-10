from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from pathlib import Path

from database.connection import create_demo_data
from etl.extract import extract_data
from etl.transform import transform_data
from kpi.calculator import calculate_kpis
from reporting.excel_report import generate_excel_report


app = FastAPI(
    title="Corporate Reporting Platform",
    description="Автоматизация корпоративной отчётности",
    version="1.0"
)


LAST_REPORT = None
LAST_KPI = {}


@app.get("/", response_class=HTMLResponse)
def home():

    revenue = LAST_KPI.get(
        "Total_Revenue",
        0
    )

    margin = LAST_KPI.get(
        "Avg_Margin_%",
        0
    )

    orders = LAST_KPI.get(
        "Total_Orders",
        0
    )


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
                    width:400px;
                }}

                button {{
                    padding:12px;
                    background:#1976d2;
                    color:white;
                    border:none;
                    border-radius:5px;
                }}
            </style>
        </head>

        <body>

        <h1>
        📊 Корпоративная платформа отчётности
        </h1>


        <form action="/generate" method="post">
            <button>
            Сгенерировать отчёт
            </button>
        </form>


        <br>


        <div class="card">

        <h2>KPI</h2>

        <p>
        💰 Выручка:
        {revenue} ₽
        </p>

        <p>
        📈 Маржа:
        {margin} %
        </p>
        <p>
<a href="/download">
    <button>
        Скачать последний Excel-отчёт
    </button>
</a>
      </p>


        <p>
        📦 Заказы:
        {orders}
        </p>

        </div>

        </body>
    </html>
    """


@app.post("/generate")
def generate():

    global LAST_REPORT
    global LAST_KPI


    create_demo_data()


    df = extract_data()

    df = transform_data(df)


    LAST_KPI = calculate_kpis(df)


    LAST_REPORT = generate_excel_report(
        df,
        LAST_KPI
    )


    return RedirectResponse(
        url="/",
        status_code=303
    )



@app.get("/download")
def download():

    if LAST_REPORT is None:
        return {
            "error": "Отчёт ещё не создан."
        }

    report = Path(LAST_REPORT)

    if not report.exists():
        return {
            "error": "Файл отчёта не найден."
        }

    return FileResponse(
        path=report,
        filename=report.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
