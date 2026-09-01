from __future__ import annotations

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


def _calculate_mom_growth(df: pd.DataFrame) -> float | None:
    """Реальный Month-over-Month рост выручки по последним двум месяцам.

    Возвращает процент роста (может быть отрицательным) или None,
    если недостаточно данных для расчёта.
    """
    if "year_month" not in df.columns or df.empty:
        return None

    monthly = (
        df.groupby("year_month", as_index=False)["amount"]
        .sum()
        .sort_values("year_month")
    )

    if len(monthly) < 2:
        return None

    prev_revenue = float(monthly.iloc[-2]["amount"])
    curr_revenue = float(monthly.iloc[-1]["amount"])

    if prev_revenue == 0:
        return None

    growth = ((curr_revenue - prev_revenue) / prev_revenue) * 100
    return float(round(growth, 2))


def calculate_kpis(df: pd.DataFrame) -> dict:
    logger.info("Этап 3: Расчёт ключевых показателей эффективности (KPI)")

    top_products = (
        df.groupby("product_name")["amount"]
        .sum()
        .nlargest(5)
    )

    top_managers = (
        df.groupby("manager_name")["amount"]
        .sum()
        .nlargest(5)
    )

    mom_growth = _calculate_mom_growth(df)

    kpis = {
        "Total_Revenue": float(round(df["amount"].sum(), 2)),
        "Total_Profit": float(round(df["profit"].sum(), 2)),
        "Avg_Margin_%": float(round(df["margin"].mean() * 100, 2)),
        "Total_Orders": int(len(df)),
        "Avg_Check": float(round(df["amount"].mean(), 2)),
        "Top_Products": {
            str(k): float(v)
            for k, v in top_products.items()
        },
        "Top_Managers": {
            str(k): float(v)
            for k, v in top_managers.items()
        },
        "MoM_Growth_%": mom_growth,
    }

    logger.info("KPI успешно рассчитаны")
    return kpis
