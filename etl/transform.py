from __future__ import annotations

import pandas as pd

from config.settings import PRODUCT_MARGIN_RATES, settings
from utils.logger import get_logger

logger = get_logger(__name__)


def _resolve_margin_series(
    df: pd.DataFrame,
    margin_rate: float | None,
) -> pd.Series:
    """Возвращает маржу из cost, явного rate или продуктовой конфигурации."""
    if margin_rate is not None:
        if not 0 < margin_rate < 1:
            raise ValueError(f"margin_rate должен быть в (0, 1), получено: {margin_rate}")
        return pd.Series(float(margin_rate), index=df.index, dtype=float)

    if "product_name" in df.columns:
        return (
            df["product_name"]
            .map(PRODUCT_MARGIN_RATES)
            .fillna(settings.DEFAULT_MARGIN_RATE)
            .astype(float)
        )

    return pd.Series(float(settings.DEFAULT_MARGIN_RATE), index=df.index, dtype=float)


def transform_data(
    df: pd.DataFrame,
    margin_rate: float | None = None,
) -> pd.DataFrame:
    """Очищает данные, рассчитывает финансы и добавляет quality/segment labels."""
    logger.info("Этап 2: ETL — Очистка и трансформация данных")
    initial_rows = len(df)
    result = df.drop_duplicates().copy()

    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result["amount"] = pd.to_numeric(result["amount"], errors="coerce")
    if "quantity" not in result.columns:
        result["quantity"] = 1
    result["quantity"] = pd.to_numeric(result["quantity"], errors="coerce")

    result["data_quality"] = "valid"
    result.loc[result["date"].isna(), "data_quality"] = "invalid_date"
    result.loc[result["amount"].isna(), "data_quality"] = "missing_amount"
    result.loc[result["amount"] < 0, "data_quality"] = "negative_amount"
    result.loc[result["amount"] == 0, "data_quality"] = "zero_amount"
    result.loc[result["quantity"].isna() | (result["quantity"] <= 0), "data_quality"] = "invalid_quantity"

    invalid = result["data_quality"] != "valid"
    if invalid.any():
        logger.warning("Исключено невалидных строк: %s", int(invalid.sum()))
    result = result.loc[~invalid].copy()

    result["month"] = result["date"].dt.to_period("M").astype(str)
    result["year_month"] = result["date"].dt.strftime("%Y-%m")

    if "cost" in result.columns and margin_rate is None:
        result["cost"] = pd.to_numeric(result["cost"], errors="coerce")
        result["cost"] = result["cost"].fillna(result["amount"] * (1 - _resolve_margin_series(result, None)))
        result["profit"] = (result["amount"] - result["cost"]).round(2)
        result["margin"] = result["profit"].div(result["amount"]).fillna(0).round(4)
    else:
        result["margin"] = _resolve_margin_series(result, margin_rate).round(4)
        result["profit"] = (result["amount"] * result["margin"]).round(2)

    result["business_segment"] = pd.cut(
        result["amount"],
        bins=[-float("inf"), 1_000, 5_000, float("inf")],
        labels=["low_value", "medium_value", "high_value"],
    ).astype(str)

    logger.info("Трансформация завершена. Строк: %s → %s", initial_rows, len(result))
    return result
