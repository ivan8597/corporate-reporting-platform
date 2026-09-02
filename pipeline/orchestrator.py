"""Оркестрация полного пайплайна отчётности."""

from __future__ import annotations

import datetime
import uuid
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
    run_id: str
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
    """Полный цикл: ETL → KPI → аномалии → Excel-отчёт.

    Demo-данные отключены по умолчанию. Для локальной демонстрации вызывающий
    код может явно передать ``init_demo_data=True``.
    """
    run_id = str(uuid.uuid4())
    start = datetime.datetime.now()
    logger.info("[%s] Запуск пайплайна корпоративной отчётности", run_id)
    logger.info("[%s] Время старта: %s", run_id, start.strftime("%Y-%m-%d %H:%M:%S"))

    if init_demo_data:
        from database.seed import create_demo_data

        logger.info("[%s] Инициализация базы данных (demo)...", run_id)
        create_demo_data()

    logger.info("[%s] Этап 1-2: Извлечение и трансформация данных...", run_id)
    raw_df = extract_data()
    clean_df = transform_data(raw_df)

    logger.info("[%s] Этап 3: Расчёт KPI...", run_id)
    kpis = calculate_kpis(clean_df)

    logger.info("[%s] Этап 4: Обнаружение аномалий...", run_id)
    anomaly_df = detect_anomalies(clean_df)

    anomaly_model_path: Path | None = None
    anomaly_metadata_path: Path | None = None
    if save_ml_artifacts:
        anomaly_model_path, anomaly_metadata_path = save_artifacts(
            anomaly_df,
            model_dir=model_dir,
        )
        logger.info(
            "[%s] Найдено аномалий: %s из %s",
            run_id,
            int((anomaly_df["anomaly_label"] == "Аномалия").sum()),
            len(anomaly_df),
        )

    logger.info("[%s] Этап 5: Формирование Excel-отчёта...", run_id)
    report_path = generate_excel_report(clean_df, kpis, anomalies=anomaly_df)

    duration = (datetime.datetime.now() - start).total_seconds()
    result = PipelineResult(
        run_id=run_id,
        clean_df=clean_df,
        kpis=kpis,
        anomalies=anomaly_df,
        report_path=report_path,
        anomaly_model_path=anomaly_model_path,
        anomaly_metadata_path=anomaly_metadata_path,
        duration_seconds=duration,
    )

    logger.info("[%s] Пайплайн успешно завершён за %.1f с", run_id, duration)
    logger.info("[%s] Строк: %s", run_id, f"{len(clean_df):,}")
    logger.info("[%s] Отчёт: %s", run_id, report_path)
    return result
