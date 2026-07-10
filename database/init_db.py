from database.connection import engine
from database.models import Base


def create_tables():

    print("Создание таблиц PostgreSQL...")

    Base.metadata.create_all(
        bind=engine
    )

    print("Таблицы успешно созданы!")


if __name__ == "__main__":
    create_tables()
