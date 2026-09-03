from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.settings import settings
from ml.anomaly_detector import detect_anomalies, save_artifacts


def train_anomaly_model(
    df: pd.DataFrame,
    model_dir: Path | str | None = None,
) -> tuple[pd.DataFrame, Path, Path]:
    """Обучает IsolationForest и сохраняет его артефакты."""
    result = detect_anomalies(df)
    model_path, metadata_path = save_artifacts(
        result,
        model_dir=model_dir or settings.ML_MODEL_DIR,
    )
    return result, model_path, metadata_path


if __name__ == "__main__":
    from etl.extract import extract_data
    from etl.transform import transform_data

    clean_df = transform_data(extract_data())
    _, model_path, metadata_path = train_anomaly_model(clean_df)
    print(f"Model: {model_path}")
    print(f"Metadata: {metadata_path}")
