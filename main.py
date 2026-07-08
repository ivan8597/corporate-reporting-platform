import traceback
import datetime
import os
from utils.logger import get_logger
from database.connection import create_demo_data
from etl.extract import extract_data
from etl.transform import transform_data
from kpi.calculator import calculate_kpis
from reporting.excel_report import generate_excel_report

logger = get_logger(__name__)

def main() -> None:
    start_time = datetime.datetime.now()
    logger.info("=" * 70)
    logger.info("🚀 Платформа Автоматизации Корпоративной Отчётности")
    logger.info(f"Запуск: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    try:
        logger.info("Инициализация базы данных...")
        create_demo_data()

        logger.info("Этап 1-2: Извлечение и трансформация данных...")
        raw_df = extract_data()
        clean_df = transform_data(raw_df)

        logger.info("Этап 3: Расчёт ключевых показателей...")
        kpis = calculate_kpis(clean_df)

        logger.info("Этап 4: Создание профессионального Excel-отчёта...")
        report_path = generate_excel_report(clean_df, kpis)

        # Итоговый summary
        duration = datetime.datetime.now() - start_time
        logger.info("=" * 70)
        logger.info("✅ ПРОЦЕСС УСПЕШНО ЗАВЕРШЁН!")
        logger.info(f"⏱ Время выполнения: {duration.seconds} секунд")
        logger.info(f"📊 Обработано строк: {len(clean_df):,}")
        logger.info(f"📁 Отчёт сохранён: {report_path}")
        logger.info(f"💰 Общая выручка: {kpis.get('Total_Revenue', 'N/A'):,.2f} ₽")
        logger.info(f"📈 Маржинальность: {kpis.get('Avg_Margin_%', 'N/A')}%")
        logger.info("=" * 70)

    except Exception as e:
        logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА!", exc_info=True)
        
        error_path = "data/reports/ОТЧЁТ_ОШИБКИ.txt"
        os.makedirs(os.path.dirname(error_path), exist_ok=True)
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(f"Ошибка выполнения: {str(e)}\n\n{traceback.format_exc()}")
        logger.info(f"Отчёт об ошибке сохранён: {error_path}")


if __name__ == "__main__":
    main()