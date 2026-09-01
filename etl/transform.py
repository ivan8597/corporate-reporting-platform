from __future__ import annotations

import pandas as pd

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def transform_data(
    df: pd.DataFrame,
    margin_rate: float | None = None,
) -> pd.DataFrame:
    """Очистка и обогащение данных.

    Маржа берётся из settings.DEFAULT_MARGIN_RATE (или явного аргумента),
    а не хардкодится в теле функции.
    """
    logger.info("Этап 2: ETL — Очистка и трансформация данных")

    if margin_rate is None:
        margin_rate = settings.DEFAULT_MARGIN_RATE

    if not 0 < margin_rate < 1:
        raise ValueError(f"margin_rate должен быть в (0, 1), получено: {margin_rate}")

    initial_rows = len(df)

    # Очистка
    df = df.drop_duplicates().copy()
    df = df.dropna(subset=["amount", "date"]).copy()

    # Приведение типов
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"]).copy()

    # Новые признаки
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df["profit"] = (df["amount"] * margin_rate).round(2)
    df["margin"] = float(margin_rate)

    # quantity: если нет в источнике — считаем 1 (единица продажи)
    if "quantity" not in df.columns:
        df["quantity"] = 1
    else:
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)

    # Контроль качества
    df["data_quality"] = "OK"
    df.loc[df["amount"] < 1000, "data_quality"] = "Низкая сумма"

    logger.info(f"Трансформация завершена. Строк: {initial_rows} → {len(df)}")
    return df
