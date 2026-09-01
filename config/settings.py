from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_TYPE: str = "sqlite"
    DB_NAME: str = "data/sales.db"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "corporate_reporting"
    POSTGRES_USER: str = "report_user"
    POSTGRES_PASSWORD: str = "report_password"

    # Business defaults
    DEFAULT_MARGIN_RATE: float = 0.38

    # ML / anomaly detection
    ML_CONTAMINATION: float = 0.02
    ML_N_ESTIMATORS: int = 300
    ML_RANDOM_STATE: int = 42
    ML_MODEL_DIR: str = "ml/models"

    # Reporting
    OUTPUT_DIR: str = "data/reports"
    TEMPLATE_PATH: str = "templates/report_template.xlsx"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
