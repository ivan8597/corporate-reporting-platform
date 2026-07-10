import xlwings as xw
import pandas as pd
import datetime
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger()

def generate_excel_report(df: pd.DataFrame, kpis: dict, template_path="templates/report_template.xlsx"):
    logger.info("Этап 4: Формирование профессионального Excel-отчёта")

    # Открываем шаблон (если нет – создаём новый)
    try:
        wb = xw.Book(template_path)
    except FileNotFoundError:
        logger.warning(f"Шаблон {template_path} не найден. Создаётся новый файл.")
        wb = xw.Book()
        # Создаём листы с русскими названиями
        wb.sheets.add("Дашборд")
        wb.sheets.add("Продажи")
        wb.sheets.add("ABC-анализ")
        wb.sheets.add("Ошибки данных")
        # Удаляем стандартный Sheet1
        if "Sheet1" in [s.name for s in wb.sheets]:
            wb.sheets["Sheet1"].delete()

    # --- Дашборд ---
    dash = wb.sheets["Дашборд"]
    dash.range("B2").value = kpis["Total_Revenue"]
    dash.range("B3").value = kpis["Total_Profit"]
    dash.range("B4").value = f"{kpis['Avg_Margin_%']}%"
    dash.range("B5").value = kpis["Total_Orders"]
    dash.range("B6").value = kpis["Avg_Check"]

    # --- Продажи (детальная таблица) ---
    wb.sheets["Продажи"].range("A1").value = df

    # --- ABC-анализ ---
    abc = df.groupby('product_name')['amount'].sum().reset_index()
    abc = abc.sort_values('amount', ascending=False)
    abc['cum_percent'] = abc['amount'].cumsum() / abc['amount'].sum() * 100
    wb.sheets["ABC-анализ"].range("A1").value = abc

    # --- Ошибки данных ---
    quality = df[df['data_quality'] != 'OK']
    wb.sheets["Ошибки данных"].range("A1").value = quality

    # Сохранение
    os.makedirs("data/reports", exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    output_path = f"data/reports/Корпоративный_Отчет_{date_str}.xlsx"
    wb.save(output_path)
    wb.close()

    logger.info(f"Excel-отчёт успешно сохранён: {output_path}")
    return output_path
