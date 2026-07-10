from pathlib import Path
import yaml
from types import SimpleNamespace


CONFIG_PATH = Path(__file__).parent / "config.yaml"


def dict_to_namespace(data):
    """
    Преобразует dict в объект
    для доступа через точку.
    """

    if isinstance(data, dict):
        return SimpleNamespace(
            **{
                key: dict_to_namespace(value)
                for key, value in data.items()
            }
        )

    if isinstance(data, list):
        return [
            dict_to_namespace(item)
            for item in data
        ]

    return data


def load_config():

    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        data = yaml.safe_load(file)

    return dict_to_namespace(data)


settings = load_config()
