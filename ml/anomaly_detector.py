from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

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


def detect_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.02,
    random_state: int = 42,
) -> pd.DataFrame:
    """Обучает IsolationForest и добавляет anomaly_label и anomaly_score.

    anomaly_score больше означает более необычное наблюдение.
    IsolationForest.predict возвращает -1 для аномалий и 1 для обычных строк.
    """
    if not 0 < contamination < 0.5:
        raise ValueError("contamination должна быть между 0 и 0.5.")

    prepared = prepare_features(df)
    model = IsolationForest(
        n_estimators=300,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(prepared[FEATURES])

    result = prepared.copy()
    result["anomaly_score"] = np.round(-model.score_samples(prepared[FEATURES]), 6)
    result["anomaly_label"] = np.where(model.predict(prepared[FEATURES]) == -1, "Аномалия", "Норма")
    result["anomaly_reason"] = result.apply(_reason, axis=1)
    result.attrs["model"] = model
    return result


def _reason(row: pd.Series) -> str:
    """Даёт простое объяснение для пользователя отчёта."""
    reasons = []
    if row["amount"] >= 1_500:
        reasons.append("высокая сумма")
    if row["margin"] < 0.2:
        reasons.append("низкая маржа")
    if row["quantity"] >= 3:
        reasons.append("большое количество")
    if row["hour"] < 9 or row["hour"] >= 21:
        reasons.append("нетипичное время")
    return ", ".join(reasons) if reasons else "комбинация признаков"


def save_artifacts(
    result: pd.DataFrame,
    model_dir: Path,
    contamination: float,
) -> tuple[Path, Path]:
    model = result.attrs.get("model")
    if model is None:
        raise ValueError("В result отсутствует обученная модель.")

    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "sales_anomaly_model.joblib"
    metadata_path = model_dir / "sales_anomaly_metadata.json"
    joblib.dump(AnomalyArtifacts(model=model, features=FEATURES), model_path)

    metadata = {
        "model_type": "IsolationForest",
        "features": FEATURES,
        "contamination": contamination,
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
