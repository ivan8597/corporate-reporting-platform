import pandas as pd
from database.connection import get_engine
from utils.logger import get_logger

logger = get_logger(__name__)

def extract_data() -> pd.DataFrame:
    """Извлечение данных из базы с join-ами."""
    logger.info("Этап 1: Извлечение данных из базы")
    engine = get_engine()

    query = """
    SELECT s.*, p.product_name, m.manager_name 
    FROM sales s
    LEFT JOIN products p ON s.product_id = p.product_id
    LEFT JOIN managers m ON s.manager_id = m.manager_id
    """
    df = pd.read_sql(query, engine)
    logger.info(f"Извлечено {len(df):,} записей")
    return df