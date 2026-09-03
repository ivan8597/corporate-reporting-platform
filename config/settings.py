from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

# Целевая маржа по продуктам (доля от выручки).
# Используется, пока в источнике нет фактической себестоимости.
PRODUCT_MARGIN_RATES: dict[str, float] = {
    "Ноутбук": 0.22,
    "Монитор": 0.28,
    "Клавиатура": 0.45,
    "Мышь": 0.48,
    "Гарнитура": 0.35,
}


class Settings(BaseSettings):
    APP_ENV: str = "production"
    DB_TYPE: str = "sqlite"
    DB_NAME: str = "data/sales.db"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "corporate_reporting"
    POSTGRES_USER: str = "report_user"
    POSTGRES_PASSWORD: str = "report_password"

    # Fallback, если продукт не найден в PRODUCT_MARGIN_RATES
    DEFAULT_MARGIN_RATE: float = 0.30

    # ML / anomaly detection
    ML_CONTAMINATION: float = 0.02
    ML_N_ESTIMATORS: int = 300
    ML_RANDOM_STATE: int = 42
    ML_MODEL_DIR: str = "ml/models"

    # Reporting
    OUTPUT_DIR: str = "data/reports"
    TEMPLATE_PATH: str = "templates/report_template.xlsx"

    @property
    def database_url(self) -> str:
        if self.DB_TYPE.lower() == "sqlite":
            return f"sqlite:///{self.DB_NAME}"
        return (
            "postgresql+psycopg2://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
