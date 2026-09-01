import os
import traceback

from pipeline.orchestrator import run_pipeline
from utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    try:
        result = run_pipeline(init_demo_data=True, save_ml_artifacts=True)
        logger.info(
            "Итог: отчёт=%s, аномалии=%s, модель=%s",
            result.report_path,
            int((result.anomalies["anomaly_label"] == "Аномалия").sum()),
            result.anomaly_model_path,
        )
    except Exception as e:
        logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА!", exc_info=True)
        error_path = "data/reports/ОТЧЁТ_ОШИБКИ.txt"
        os.makedirs(os.path.dirname(error_path), exist_ok=True)
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(f"Ошибка выполнения: {str(e)}\n\n{traceback.format_exc()}")
        logger.info(f"Отчёт об ошибке сохранён: {error_path}")
        raise


if __name__ == "__main__":
    main()
