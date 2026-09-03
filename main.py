import os
import traceback

from config.settings import settings
from pipeline.orchestrator import run_pipeline
from utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    try:
        result = run_pipeline(
            init_demo_data=settings.APP_ENV.lower() == "demo",
            save_ml_artifacts=True,
        )
        logger.info(
            "Итог: отчёт=%s, аномалии=%s, модель=%s",
            result.report_path,
            int((result.anomalies["anomaly_label"] == "Аномалия").sum()),
            result.anomaly_model_path,
        )
    except Exception as exc:
        logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА!", exc_info=True)
        error_path = "data/reports/ОТЧЁТ_ОШИБКИ.txt"
        os.makedirs(os.path.dirname(error_path), exist_ok=True)
        with open(error_path, "w", encoding="utf-8") as error_file:
            error_file.write(f"Ошибка выполнения: {exc}\n\n{traceback.format_exc()}")
        logger.info("Отчёт об ошибке сохранён: %s", error_path)
        raise


if __name__ == "__main__":
    main()
