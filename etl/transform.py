from __future__ import annotations

import pandas as pd

from config.settings import PRODUCT_MARGIN_RATES, settings
from utils.logger import get_logger

logger = get_logger(__name__)


def _resolve_margin_series(
    df: pd.DataFrame,
    margin_rate: float | None,
) -> pd.Series:
    """Маржа по строке: явный rate, либо ставка продукта, либо DEFAULT_MARGIN_RATE."""
    if margin_rate is not None:
        if not 0 < margin_rate < 1:
            raise ValueError(f"margin_rate должен быть в (0, 1), получено: {margin_rate}")
        return pd.Series(float(margin_rate), index=df.index, dtype=float)

    if "product_name" in df.columns:
        rates = (
            df["product_name"]
            .map(PRODUCT_MARGIN_RATES)
            .fillna(settings.DEFAULT_MARGIN_RATE)
            .astype(float)
        )
        return rates

    return pd.Series(float(settings.DEFAULT_MARGIN_RATE), index=df.index, dtype=float)


def transform_data(
    df: pd.DataFrame,
    margin_rate: float | None = None,
) -> pd.DataFrame:
    """Очистка и обогащение данных.

    Реальные проблемы качества отражаются в ``data_quality``.
    Низкая сумма является бизнес-классификацией, а не ошибкой данных.
    """
    logger.info("Этап 2: ETL — Очистка и трансформация данных")

    initial_rows = len(df)

    df = df.drop_duplicates().copy()
    df = df.dropna(subset=["amount", "date"]).copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount", "date"]).copy()

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["year_month"] = df["date"].dt.strftime("%Y-%m")

    if "cost" in df.columns and margin_rate is None:
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
        df["profit"] = (df["amount"] - df["cost"]).round(2)
        df["margin"] = (
            df["profit"] / df["amount"].replace(0, pd.NA)
        ).fillna(0.0).round(4)
    else:
        margins = _resolve_margin_series(df, margin_rate)
        df["margin"] = margins.round(4)
        df["profit"] = (df["amount"] * df["margin"]).round(2)

    if "quantity" not in df.columns:
        df["quantity"] = 1
    else:
        df["quantity"] = (
            pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
        )

    # Data quality describes invalid/missing data, not a valid low-value sale.
    df["data_quality"] = "OK"
    if "cost" in df.columns:
        df.loc[df["cost"] < 0, "data_quality"] = "Некорректная себестоимость"
    df.loc[df["amount"] < 0, "data_quality"] = "Некорректная сумма"

    # Business classification is intentionally separate from data quality.
    df["business_classification"] = "Обычная сумма"
    df.loc[df["amount"] < 1000, "business_classification"] = "Низкая сумма"

    logger.info(f"Трансформация завершена. Строк: {initial_rows} → {len(df)}")
    return df
