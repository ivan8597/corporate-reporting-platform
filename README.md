# Корпоративная Платформа Отчётности

🚀 Автоматизированная система генерации корпоративных отчётов на Python.

## Возможности
- Полный ETL-пайплайн
- Расчёт KPI
- Профессиональные Excel-отчёты с русскими названиями листов
- Логирование
- Поддержка Docker и Render.com

## Быстрый старт
```bash
pip install -r requirements.txt
python main.py
```

## Структура проекта
- `database/` — работа с БД
- `etl/` — Extract, Transform, Load
- `kpi/` — расчёт показателей
- `reporting/` — генерация отчётов

## Деплой
- **Render.com** (рекомендуется)
- Docker
- Local

## Лицензия
MIT


## Локальный запуск

По умолчанию проект использует SQLite, поэтому для первого запуска PostgreSQL не требуется. Конфигурация задаётся через `.env`:

```env
DB_TYPE=sqlite
DB_NAME=data/sales.db
```

Установка и запуск:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python -m database.init_db
python main.py
```

После запуска Excel-отчёт сохраняется в `data/reports/`. API можно запустить командой:

```bash
uvicorn api.app:app --reload
```

Откройте в браузере `http://127.0.0.1:8000`. На главной странице нажмите **«Сгенерировать отчёт»**, чтобы обновить demo-данные и создать новый Excel-файл. Документация FastAPI доступна по адресу `http://127.0.0.1:8000/docs`.

Инициализацию базы необходимо запускать как модуль из корня проекта:

```bash
python -m database.init_db
```

## Источник данных и схема

Для локального режима `database/connection.py` создаёт SQLite-файл `data/sales.db`, таблицы `products`, `managers` и `sales`, а также заполняет демонстрационной историей за 90 дней. ETL-модуль `etl/extract.py` читает продажи через SQL-запрос с объединением товаров и менеджеров.

| Таблица | Назначение |
|---|---|
| `products` | Справочник товаров |
| `managers` | Справочник менеджеров |
| `sales` | Дата, товар, менеджер, сумма, регион |

Для PostgreSQL задайте в `.env`:

```env
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=corporate_reporting
POSTGRES_USER=report_user
POSTGRES_PASSWORD=report_password
```

## Проверка запуска

```bash
python -m database.init_db
python main.py
pytest -q
```

Ожидаемый результат тестов — `1 passed`.

> Demo-данные предназначены для проверки технического запуска. Для ML-аналитики и бизнес-выводов их нельзя считать реальными корпоративными данными.


## Обнаружение аномалий

В проект добавлен ML-модуль `ml/anomaly_detector.py` на базе `IsolationForest`. Он анализирует строки продаж по признакам `amount`, `profit`, `margin`, `quantity`, часу и дню недели.

`IsolationForest.predict()` присваивает строке статус `Аномалия` или `Норма`, а `anomaly_score` рассчитывается так, что **большее значение означает более необычное наблюдение**. Модель не доказывает ошибку в данных: score показывает, какие строки требуют проверки сотрудником.

Модель автоматически запускается из `main.py` после ETL. Артефакты сохраняются в:

```text
ml/models/sales_anomaly_model.joblib
ml/models/sales_anomaly_metadata.json
```

Excel-отчёт теперь содержит лист `Аномалии` с аномальными строками, отсортированными по `anomaly_score`, а на листе `Дашборд` появляются показатели количества и доли аномалий.

API также предоставляет результаты последней генерации:

```text
GET /anomalies
```

До генерации отчёта endpoint возвращает `status: not_ready`. После вызова `POST /generate` он возвращает `status: ready`, количество аномалий и список строк с оценками и причинами для проверки.

Запуск полного pipeline:

```bash
python main.py
```

Параметр `contamination=0.02` означает, что модель ожидает небольшой процент необычных наблюдений. Его следует подбирать по бизнес-контексту и проверять на размеченной истории, если такая разметка появится.
