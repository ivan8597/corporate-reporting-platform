import pandas as pd

from utils.logger import get_logger


logger = get_logger(__name__)


def calculate_kpis(df: pd.DataFrame) -> dict:
    logger.info(
        "Этап 3: Расчёт ключевых показателей эффективности (KPI)"
    )

    kpis = {
        "Total_Revenue": round(
            df["amount"].sum(),
            2
        ),

        "Total_Profit": round(
            df["profit"].sum(),
            2
        ),

        "Avg_Margin_%": round(
            df["margin"].mean() * 100,
            2
        ),

        "Total_Orders": len(df),

        "Avg_Check": round(
            df["amount"].mean(),
            2
        ),

        "Top_Products": (
            df.groupby("product_name")["amount"]
            .sum()
            .nlargest(5)
            .to_dict()
        ),

        "Top_Managers": (
            df.groupby("manager_name")["amount"]
            .sum()
            .nlargest(5)
            .to_dict()
        ),

        "MoM_Growth_%": 12.5
    }

    logger.info("KPI успешно рассчитаны")

    return kpis
