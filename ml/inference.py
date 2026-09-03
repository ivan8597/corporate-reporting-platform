from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ml.anomaly_detector import _business_reason, load_artifacts, prepare_features


def predict_anomalies(
    df: pd.DataFrame,
    model_path: Path | str,
) -> pd.DataFrame:
    """Применяет сохранённый IsolationForest к новым строкам."""
    artifacts = load_artifacts(Path(model_path))
    prepared = prepare_features(df)
    result = prepared.copy()
    features = artifacts.features
    result["anomaly_score"] = np.round(
        -artifacts.model.score_samples(prepared[features]),
        6,
    )
    result["anomaly_label"] = np.where(
        artifacts.model.predict(prepared[features]) == -1,
        "Аномалия",
        "Норма",
    )
    result["business_reason"] = result.apply(_business_reason, axis=1)
    return result


if __name__ == "__main__":
    from etl.extract import extract_data
    from etl.transform import transform_data

    clean_df = transform_data(extract_data())
    predictions = predict_anomalies(
        clean_df,
        Path("ml/models/sales_anomaly_model.joblib"),
    )
    print(predictions["anomaly_label"].value_counts().to_string())
