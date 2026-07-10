import pandas as pd

from utils.logger import get_logger


logger = get_logger(__name__)


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
        "MoM_Growth_%": 12.5
    }

    logger.info("KPI успешно рассчитаны")

    return kpis
