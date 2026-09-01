from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_TYPE: str = "sqlite"
    DB_NAME: str = "data/sales.db"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "corporate_reporting"
    POSTGRES_USER: str = "report_user"
    POSTGRES_PASSWORD: str = "report_password"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
