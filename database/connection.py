import os
import sqlalchemy as sa
import pandas as pd
from typing import Optional
from config.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_engine: Optional[sa.Engine] = None

def get_engine() -> sa.Engine:
    """Возвращает SQLAlchemy engine (singleton)."""
    global _engine
    if _engine is None:
        db_config = settings.database
        if db_config.type == "sqlite":
            db_path = db_config.dbname
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            _engine = sa.create_engine(
                f"sqlite:///{db_path}",
                echo=False,
                connect_args={"check_same_thread": False}
            )
        else:
            raise NotImplementedError(f"Database type {db_config.type} not supported yet.")
    return _engine

def create_demo_data():
    """Создаёт демонстрационные данные для тестового запуска."""
    engine = get_engine()
    logger.info("Создание демо-данных...")

    # Таблица продаж
    sales = pd.DataFrame({
        'sale_id': range(1, 501),
        'date': pd.date_range('2025-01-01', periods=500),
        'product_id': [i % 20 + 1 for i in range(500)],
        'manager_id': [i % 8 + 1 for i in range(500)],
        'amount': [round(abs(i * 150 + 5000 + (i % 50) * 100), 2) for i in range(500)],
        'region': ['Москва', 'СПб', 'ЕКБ', 'Новосибирск'] * 125
    })
    sales.to_sql('sales', engine, if_exists='replace', index=False)
    
    # Дополнительные таблицы
    products = pd.DataFrame({
        'product_id': range(1, 21),
        'product_name': [f'Товар {i}' for i in range(1, 21)],
        'category': ['Категория A', 'Категория B'] * 10
    })
    products.to_sql('products', engine, if_exists='replace', index=False)

    managers = pd.DataFrame({
        'manager_id': range(1, 9),
        'manager_name': [f'Менеджер {i}' for i in range(1, 9)],
        'team': ['Команда 1', 'Команда 2'] * 4
    })
    managers.to_sql('managers', engine, if_exists='replace', index=False)

    logger.info("Демо-данные успешно созданы.")
    return sales