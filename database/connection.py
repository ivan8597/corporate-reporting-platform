from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from database.models import Base, Manager, Product, Sale


def build_database_url() -> str:
    if settings.DB_TYPE.lower() == "sqlite":
        db_path = Path(settings.DB_NAME)
        if not db_path.is_absolute():
            db_path = Path(__file__).resolve().parents[1] / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    return (
        "postgresql+psycopg2://"
        f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/"
        f"{settings.POSTGRES_DB}"
    )


DATABASE_URL = build_database_url()
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False}
    if settings.DB_TYPE.lower() == "sqlite"
    else {},
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_engine():
    return engine


def create_demo_data() -> None:
    """Создаёт минимальный повторяемый demo-набор для отчётности."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        has_sales = session.scalar(select(Sale.id).limit(1)) is not None
        if has_sales:
            return

        products = [
            Product(product_id=1, product_name="Ноутбук"),
            Product(product_id=2, product_name="Монитор"),
            Product(product_id=3, product_name="Клавиатура"),
            Product(product_id=4, product_name="Мышь"),
            Product(product_id=5, product_name="Гарнитура"),
        ]
        managers = [
            Manager(manager_id=1, manager_name="Анна"),
            Manager(manager_id=2, manager_name="Борис"),
            Manager(manager_id=3, manager_name="Виктор"),
        ]
        session.add_all(products + managers)
        session.flush()

        base_date = datetime(2024, 1, 1)
        sales: list[Sale] = []
        sale_id = 1
        for day in range(90):
            current_date = base_date + timedelta(days=day)
            for product_id in range(1, 6):
                for manager_id in range(1, 4):
                    amount = float(
                        700
                        + product_id * 180
                        + manager_id * 90
                        + (day % 7) * 75
                        + ((day * product_id + manager_id) % 5) * 50
                    )
                    sales.append(
                        Sale(
                            id=sale_id,
                            date=current_date,
                            product_id=product_id,
                            manager_id=manager_id,
                            amount=amount,
                            region=["Центр", "Север", "Юг"][manager_id - 1],
                        )
                    )
                    sale_id += 1

        session.add_all(sales)
        session.commit()
