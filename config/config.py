import yaml
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


CONFIG_FILE = BASE_DIR / "config.yaml"


def load_config():
    """
    Загружает настройки из config.yaml
    """

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Config file not found: {CONFIG_FILE}"
        )

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


settings = load_config()
