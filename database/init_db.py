import argparse

from database.connection import engine
from database.models import Base


def create_tables() -> None:
    print("Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Инициализация базы отчётности")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="заполнить базу демонстрационными данными",
    )
    args = parser.parse_args()

    create_tables()
    if args.seed:
        from database.seed import create_demo_data

        create_demo_data()
        print("Demo-данные успешно добавлены!")


if __name__ == "__main__":
    main()
