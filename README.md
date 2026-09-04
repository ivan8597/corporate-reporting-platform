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
- `pipeline/` — оркестрация `run_pipeline`
- `services/` — состояние API (`ReportStore`)

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

Ожидаемый результат тестов — `16 passed` (KPI, transform, anomaly, report_store).

> Demo-данные предназначены для проверки технического запуска. Для ML-аналитики и бизнес-выводов их нельзя считать реальными корпоративными данными.

## Архитектура пайплайна

Оркестрация вынесена в `pipeline/orchestrator.py` (`run_pipeline`).  
`main.py` и FastAPI (`POST /generate`) вызывают одну и ту же функцию.

Состояние последнего отчёта в API хранится в `services/report_store.py` (без module-level globals).

Параметры маржи (`DEFAULT_MARGIN_RATE`) и ML (`ML_CONTAMINATION`, `ML_N_ESTIMATORS`, `ML_RANDOM_STATE`) задаются через `config/settings.py` / `.env`.

`MoM_Growth_%` считается по реальным месячным суммам выручки (последние два месяца), а не захардкожен.

У аномалий есть колонка `business_reason` (с fallback `anomaly_reason` для совместимости).


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

Параметр `ML_CONTAMINATION` (по умолчанию `0.02`) означает, что модель ожидает небольшой процент необычных наблюдений. Его следует подбирать по бизнес-контексту и проверять на размеченной истории, если такая разметка появится. Задаётся в `.env` / `config/settings.py`.


## Режимы запуска и demo seed

`main.py` не создаёт demo-данные без явного режима. Режим задаётся через `APP_ENV`:

```env
APP_ENV=demo
```

Для production следует использовать:

```env
APP_ENV=production
```

В production pipeline читает существующий источник данных и не вызывает seed. Demo-данные вынесены в `database/seed.py` и создаются отдельной командой:

```bash
python -m database.init_db --seed
```

## Качество данных и бизнес-сегментация

ETL не смешивает техническую валидность строки с её коммерческой ценностью. Поле `data_quality` содержит статусы `valid`, `missing_amount`, `invalid_date`, `negative_amount`, `zero_amount` и `invalid_quantity`. Поле `business_segment` содержит `low_value`, `medium_value` или `high_value` и используется для бизнес-аналитики.

Низкая сумма сделки не считается ошибкой данных: это корректная бизнес-характеристика, а не признак повреждённой записи.


## Раздельные ML train, inference и evaluation

Обучение и применение модели разделены по модулям:

```text
ml/train.py      — обучение IsolationForest и сохранение artifact
ml/inference.py  — загрузка artifact и предсказание новых строк
ml/evaluate.py   — precision/recall/F1 на ручной разметке
```

Обычный pipeline сохраняет предсказания в `data/reports/anomaly_predictions.csv`. Для ручной валидации скопируйте шаблон:

```bash
cp data/anomaly_labels.example.csv data/anomaly_labels.csv
```

Заполните `id`, `is_anomaly` и комментарий проверяющего, затем выполните:

```bash
python -m ml.evaluate \
  --predictions data/reports/anomaly_predictions.csv \
  --labels data/anomaly_labels.csv
```

Только строки, прошедшие ручную проверку, используются для precision, recall и F1. До появления такой разметки эти метрики не следует указывать в резюме.

## Миграции базы данных

Схема базы управляется Alembic:

```bash
alembic upgrade head
```

Для новой локальной базы с demo-данными:

```bash
alembic upgrade head
python -m database.init_db --seed
```

Откат последней миграции:

```bash
alembic downgrade -1
```


# Архитектура платформы

## Назначение проекта

`corporate-reporting-platform` — это демонстрационная корпоративная платформа отчётности. Она извлекает данные о продажах из базы данных, очищает и обогащает их, рассчитывает KPI, обнаруживает статистически необычные операции и формирует Excel-отчёт. Результаты также доступны через FastAPI.

Система разделена на несколько слоёв:

```text
┌──────────────────────────────────────────────┐
│                 FastAPI API                   │
│  /  /generate  /anomalies  /download         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              Pipeline Orchestrator            │
│ extract → transform → KPI → ML → reporting   │
└──────────────┬─────────────┬─────────────────┘
               │             │
               ▼             ▼
┌────────────────────┐  ┌─────────────────────┐
│   Database layer    │  │      ML layer        │
│ SQLAlchemy/Alembic  │  │ train/inference/     │
│ SQLite/PostgreSQL   │  │ evaluation           │
└─────────┬──────────┘  └──────────┬──────────┘
          │                        │
          ▼                        ▼
┌────────────────────┐  ┌─────────────────────┐
│  products/managers │  │ joblib model + score │
│       /sales       │  │ business_reason      │
└────────────────────┘  └─────────────────────┘
                       │
                       ▼
              Excel report + JSON state
```

## Слои и ответственность модулей

| Слой | Основные файлы | Ответственность |
|---|---|---|
| Configuration | `config/settings.py`, `.env.example` | Настройки БД, отчётности и ML |
| Database | `database/connection.py`, `database/models.py` | Engine, session factory и ORM-модели |
| Migrations | `alembic/`, `alembic.ini` | Версионирование схемы базы |
| Demo seed | `database/seed.py` | Явное заполнение локальной базы демонстрационными данными |
| ETL | `etl/extract.py`, `etl/transform.py` | Извлечение, очистка и финансовые расчёты |
| KPI | `kpi/calculator.py` | Расчёт выручки, маржи, заказов и MoM |
| Pipeline | `pipeline/orchestrator.py` | Координация полного batch-процесса |
| ML | `ml/anomaly_detector.py` | Признаки, IsolationForest и anomaly score |
| ML train | `ml/train.py` | Обучение и сохранение model artifact |
| ML inference | `ml/inference.py` | Применение сохранённой модели к новым данным |
| ML evaluation | `ml/evaluate.py` | Precision, recall и F1 на ручной разметке |
| Reporting | `reporting/excel_report.py` | Excel-листы KPI и аномалий |
| API | `api/app.py`, `templates/index.html` | Typed HTTP API и HTML-интерфейс |

## Pipeline

Основной orchestration находится в `pipeline/orchestrator.py`. Тонкая точка входа `main.py` не содержит бизнес-логики и только запускает pipeline.

```python
if __name__ == "__main__":
    main()
```

В production-режиме pipeline не создаёт demo-данные автоматически. Demo seed запускается только явно через `database.init_db --seed` или при `APP_ENV=demo`.

### Этапы pipeline

| Этап | Действие | Результат |
|---|---|---|
| Extract | SQL-запрос к `sales`, `products`, `managers` | Raw DataFrame |
| Transform | Очистка типов, удаление дублей, data quality | Clean DataFrame |
| Finance | Расчёт `revenue`, `cost`, `profit`, `margin` | Финансовые признаки |
| KPI | Выручка, заказы, средняя маржа, MoM | Словарь KPI |
| ML | IsolationForest и anomaly score | Таблица аномалий |
| Persist | JSON state и CSV predictions | API-ready artifacts |
| Reporting | Excel report | `.xlsx`-отчёт |

## ML-модули

### Обнаружение аномалий

`ml/anomaly_detector.py` использует `IsolationForest` для поиска необычных продаж. Модель не требует заранее размеченных классов и подходит как первый unsupervised baseline для demo-платформы.

Используемые признаки включают:

| Признак | Смысл |
|---|---|
| `amount` | Сумма продажи |
| `profit` | Прибыль |
| `margin` | Относительная маржа |
| `quantity` | Количество единиц |
| `hour` | Час операции |
| `day_of_week` | День недели |

Результат содержит три разных понятия:

```text
anomaly_score    — статистическая оценка необычности
anomaly_label    — «Аномалия» или «Норма»
business_reason  — бизнес-правило для ручной интерпретации
```

`business_reason` не является объяснением внутреннего решения IsolationForest. Это дополнительная эвристическая подсказка, например «высокая сумма» или «низкая маржа».

### Конфигурация модели

ML-параметры задаются через окружение, а не в orchestration-коде:

```env
ML_CONTAMINATION=0.02
ML_N_ESTIMATORS=300
ML_RANDOM_STATE=42
ML_MODEL_DIR=ml/models
```

`contamination=0.02` означает ожидаемую долю выбросов, а не доказанную долю мошеннических операций. В прикладном проекте это значение следует проверять на ручной разметке.

### Train и inference

Обучение и inference разделены:

```bash
python -m ml.train
python -m ml.inference
```

Обучение создаёт:

```text
ml/models/sales_anomaly_model.joblib
ml/models/sales_anomaly_metadata.json
```

Эти артефакты игнорируются Git и генерируются локально. В production их следует хранить в model registry или object storage.

### Evaluation

Pipeline сохраняет предсказания в:

```text
data/reports/anomaly_predictions.csv
```

Создайте собственную ручную разметку:

```bash
cp data/anomaly_labels.example.csv data/anomaly_labels.csv
```

Заполните файл колонками `id`, `is_anomaly` и `reviewer_comment`, затем выполните:

```bash
python -m ml.evaluate \
  --predictions data/reports/anomaly_predictions.csv \
  --labels data/anomaly_labels.csv
```

Evaluation рассчитывает `precision`, `recall` и `F1`. Пока нет независимой ручной разметки, эти метрики нельзя считать подтверждёнными результатами модели.

## API

Приложение запускается через FastAPI:

```bash
uvicorn api.app:app --reload
```

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/` | HTML-страница с KPI |
| `POST` | `/generate` | Запуск pipeline, typed JSON response |
| `POST` | `/generate/view` | Запуск pipeline с redirect на HTML-страницу |
| `GET` | `/anomalies` | Typed JSON со списком аномалий |
| `GET` | `/download` | Скачивание последнего Excel-отчёта |
| `GET` | `/docs` | Swagger UI |

Пример ответа `/anomalies`:

```json
{
  "status": "ready",
  "count": 27,
  "anomalies": [
    {
      "id": 101,
      "anomaly_score": 0.8421,
      "anomaly_label": "Аномалия",
      "business_reason": "высокая сумма"
    }
  ]
}
```

HTML-разметка находится в `templates/index.html`, а API-ответы валидируются Pydantic-моделями `AnomalyResponse` и `GenerateResponse`.

## Alembic и база данных

Для production-like работы схема создаётся миграциями:

```bash
alembic upgrade head
```

Проверка текущей версии:

```bash
alembic current
```

Создание новой миграции после изменения ORM-моделей:

```bash
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

Для локального demo-окружения:

```bash
rm -f data/sales.db
alembic upgrade head
python -m database.init_db --seed
```

Откат последней миграции:

```bash
alembic downgrade -1
```

## Запуск через Docker Compose

Docker Compose поднимает два сервиса:

```text
postgres:16
    ↓ healthcheck
api
    ↓ alembic upgrade head
uvicorn на порту 10000
```

### Запуск

Установите Docker и Docker Compose Plugin, затем выполните:

```bash
git clone https://github.com/ivan8597/corporate-reporting-platform.git
cd corporate-reporting-platform

docker compose up --build -d
```

Compose автоматически:

1. запускает PostgreSQL;
2. ждёт успешного `pg_isready` healthcheck;
3. собирает Python image;
4. применяет `alembic upgrade head`;
5. запускает FastAPI на `0.0.0.0:10000`.

Откройте:

```text
http://localhost:10000
http://localhost:10000/docs
http://localhost:10000/anomalies
```

Проверка состояния контейнеров:

```bash
docker compose ps
docker compose logs -f api
```

Остановка:

```bash
docker compose down
```

Остановка с удалением volume PostgreSQL:

```bash
docker compose down -v
```

Команда `down -v` удаляет локальную базу и все данные PostgreSQL, поэтому в production её применять нельзя без резервной копии.

### Docker-конфигурация

Внутри Compose API подключается к PostgreSQL по имени сервиса `postgres`, а не по `localhost`:

```env
DB_TYPE=postgresql
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=corporate_reporting
POSTGRES_USER=report_user
POSTGRES_PASSWORD=report_password
```

Снаружи API доступен на порту `10000`, а PostgreSQL — на `5432`. Для production-публикации пароль необходимо заменить через secrets или environment variables CI/CD, а не хранить в README или compose-файле.

## CI/CD

Workflow находится в `.github/workflows/ci-cd.yml` и запускается для Pull Request и push в `main`.

```text
Ruff → compileall → pytest → Docker build → Render deploy
```

Deploy выполняется только после успешных проверок и только для push в `main`. Для работы deploy необходимо добавить `RENDER_DEPLOY_HOOK` в GitHub Actions Secrets.

## Ограничения и следующие шаги

Проект остаётся production-like demo, а не готовой промышленной системой. Для дальнейшего усиления следует добавить миграции для каждой последующей schema change, отдельное хранилище отчётов и model registry, background jobs для тяжёлых pipeline, authentication/authorization, retry/timeout для внешних сервисов и независимый набор вручную проверенных аномалий.
