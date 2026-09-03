"""Оркестрация полного пайплайна отчётности.

Вынесена из main.py и api/app.py, чтобы оба входа использовали одну логику.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from etl.extract import extract_data
from etl.transform import transform_data
from kpi.calculator import calculate_kpis
from ml.anomaly_detector import detect_anomalies, save_artifacts
from reporting.excel_report import generate_excel_report
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    clean_df: pd.DataFrame
    kpis: dict[str, Any]
    anomalies: pd.DataFrame
    report_path: str
    anomaly_model_path: Path | None = None
    anomaly_metadata_path: Path | None = None
    duration_seconds: float = 0.0


def run_pipeline(
    *,
    init_demo_data: bool = False,
    save_ml_artifacts: bool = True,
    model_dir: Path | str | None = None,
) -> PipelineResult:
    """Полный цикл: demo-данные → ETL → KPI → аномалии → Excel-отчёт."""
    start = datetime.datetime.now()
    logger.info("=" * 70)
    logger.info("🚀 Запуск пайплайна корпоративной отчётности")
    logger.info(f"Время старта: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    if init_demo_data:
        logger.info("Инициализация базы данных (demo)...")
        from database.seed import create_demo_data

        create_demo_data()

    logger.info("Этап 1-2: Извлечение и трансформация данных...")
    raw_df = extract_data()
    clean_df = transform_data(raw_df)

    logger.info("Этап 3: Расчёт KPI...")
    kpis = calculate_kpis(clean_df)

    logger.info("Этап 4: Обнаружение аномалий...")
    anomaly_df = detect_anomalies(clean_df)

    anomaly_model_path: Path | None = None
    anomaly_metadata_path: Path | None = None
    if save_ml_artifacts:
        anomaly_model_path, anomaly_metadata_path = save_artifacts(
            anomaly_df,
            model_dir=model_dir,
        )
        logger.info(
            "Найдено аномалий: %s из %s",
            int((anomaly_df["anomaly_label"] == "Аномалия").sum()),
            len(anomaly_df),
        )

    logger.info("Этап 5: Формирование Excel-отчёта...")
    report_path = generate_excel_report(clean_df, kpis, anomalies=anomaly_df)

    duration = (datetime.datetime.now() - start).total_seconds()
    result = PipelineResult(
        clean_df=clean_df,
        kpis=kpis,
        anomalies=anomaly_df,
        report_path=report_path,
        anomaly_model_path=anomaly_model_path,
        anomaly_metadata_path=anomaly_metadata_path,
        duration_seconds=duration,
    )

    logger.info("=" * 70)
    logger.info("✅ Пайплайн успешно завершён")
    logger.info(f"⏱ Время: {duration:.1f} с")
    logger.info(f"📊 Строк: {len(clean_df):,}")
    logger.info(f"📁 Отчёт: {report_path}")
    logger.info(f"💰 Выручка: {kpis.get('Total_Revenue', 'N/A'):,.2f} ₽")
    mom = kpis.get("MoM_Growth_%")
    logger.info(f"📈 MoM рост: {mom if mom is not None else 'N/A'}%")
    logger.info("=" * 70)

    return result
