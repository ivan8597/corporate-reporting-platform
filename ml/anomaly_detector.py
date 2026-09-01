from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from config.settings import settings

FEATURES = [
    "amount",
    "profit",
    "margin",
    "quantity",
    "hour",
    "day_of_week",
]


@dataclass
class AnomalyArtifacts:
    model: IsolationForest
    features: list[str]


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Формирует числовые признаки продаж для IsolationForest."""
    required = {"date", "amount", "profit", "margin"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Для anomaly detection отсутствуют столбцы: {sorted(missing)}")

    result = df.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result["amount"] = pd.to_numeric(result["amount"], errors="coerce")
    result["profit"] = pd.to_numeric(result["profit"], errors="coerce")
    result["margin"] = pd.to_numeric(result["margin"], errors="coerce")
    result["quantity"] = pd.to_numeric(result.get("quantity", 1), errors="coerce")
    result["hour"] = result["date"].dt.hour
    result["day_of_week"] = result["date"].dt.dayofweek

    if result[FEATURES].isna().any().any():
        raise ValueError("В признаках аномалий обнаружены пропуски.")
    return result


def _business_reason(row: pd.Series) -> str:
    """Бизнес-объяснение, почему строка выглядит необычной для проверки аналитиком."""
    reasons: list[str] = []

    if row["amount"] >= 1_500:
        reasons.append("аномально высокая сумма сделки")
    if row["margin"] < 0.25:
        reasons.append("маржа ниже целевой")
    if row["quantity"] >= 3:
        reasons.append("нетипично большой объём в одной транзакции")
    if row["hour"] < 9 or row["hour"] >= 21:
        reasons.append("продажа вне обычных рабочих часов")
    if row.get("day_of_week") is not None and int(row["day_of_week"]) >= 5:
        reasons.append("выходной день")

    return "; ".join(reasons) if reasons else "необычная комбинация признаков"


def detect_anomalies(
    df: pd.DataFrame,
    contamination: float | None = None,
    n_estimators: int | None = None,
    random_state: int | None = None,
) -> pd.DataFrame:
    """Обучает IsolationForest и добавляет anomaly_label, anomaly_score, business_reason.

    anomaly_score больше означает более необычное наблюдение.
    IsolationForest.predict возвращает -1 для аномалий и 1 для обычных строк.
    Параметры по умолчанию берутся из settings.
    """
    if contamination is None:
        contamination = settings.ML_CONTAMINATION
    if n_estimators is None:
        n_estimators = settings.ML_N_ESTIMATORS
    if random_state is None:
        random_state = settings.ML_RANDOM_STATE

    if not 0 < contamination < 0.5:
        raise ValueError("contamination должна быть между 0 и 0.5.")

    prepared = prepare_features(df)
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(prepared[FEATURES])

    result = prepared.copy()
    result["anomaly_score"] = np.round(-model.score_samples(prepared[FEATURES]), 6)
    result["anomaly_label"] = np.where(
        model.predict(prepared[FEATURES]) == -1, "Аномалия", "Норма"
    )
    result["business_reason"] = result.apply(_business_reason, axis=1)
    # Обратная совместимость со старым именем колонки в отчётах
    result["anomaly_reason"] = result["business_reason"]
    result.attrs["model"] = model
    result.attrs["contamination"] = contamination
    return result


def save_artifacts(
    result: pd.DataFrame,
    model_dir: Path | str | None = None,
    contamination: float | None = None,
) -> tuple[Path, Path]:
    model = result.attrs.get("model")
    if model is None:
        raise ValueError("В result отсутствует обученная модель.")

    if model_dir is None:
        model_dir = Path(settings.ML_MODEL_DIR)
    else:
        model_dir = Path(model_dir)

    if contamination is None:
        contamination = result.attrs.get("contamination", settings.ML_CONTAMINATION)

    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "sales_anomaly_model.joblib"
    metadata_path = model_dir / "sales_anomaly_metadata.json"
    joblib.dump(AnomalyArtifacts(model=model, features=FEATURES), model_path)

    metadata = {
        "model_type": "IsolationForest",
        "features": FEATURES,
        "contamination": contamination,
        "n_estimators": getattr(model, "n_estimators", settings.ML_N_ESTIMATORS),
        "random_state": getattr(model, "random_state", settings.ML_RANDOM_STATE),
        "rows": int(len(result)),
        "anomalies": int((result["anomaly_label"] == "Аномалия").sum()),
        "anomaly_share_percent": round(
            float((result["anomaly_label"] == "Аномалия").mean() * 100),
            2,
        ),
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return model_path, metadata_path


def load_artifacts(model_path: Path) -> AnomalyArtifacts:
    artifact = joblib.load(model_path)
    if not isinstance(artifact, AnomalyArtifacts):
        raise TypeError("Некорректный формат anomaly model artifact.")
    return artifact
