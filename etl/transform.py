import pandas as pd
from utils.logger import get_logger
from typing import Dict

logger = get_logger(__name__)

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Очистка и обогащение данных."""
    logger.info("Этап 2: ETL — Очистка и трансформация данных")

    initial_rows = len(df)

    # Очистка
    df = df.drop_duplicates().copy()
    df = df.dropna(subset=['amount', 'date']).copy()

    # Приведение типов
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = pd.to_numeric(df['amount'])

    # Новые признаки
    df['month'] = df['date'].dt.to_period('M').astype(str)
    df['profit'] = (df['amount'] * 0.38).round(2)
    df['margin'] = 0.38
    df['year_month'] = df['date'].dt.strftime('%Y-%m')

    # Контроль качества
    df['data_quality'] = 'OK'
    df.loc[df['amount'] < 1000, 'data_quality'] = 'Низкая сумма'

    logger.info(f"Трансформация завершена. Строк: {initial_rows} → {len(df)}")
    return df