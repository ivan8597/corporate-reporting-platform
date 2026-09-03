from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report, precision_recall_fscore_support

LABEL_COLUMNS = {"id", "is_anomaly"}


def evaluate_predictions(
    predictions: pd.DataFrame,
    labels: pd.DataFrame,
) -> dict[str, float | int]:
    """Считает метрики на ручной разметке, объединённой по id продажи."""
    missing = LABEL_COLUMNS.difference(labels.columns)
    if missing:
        raise ValueError(f"В labels отсутствуют столбцы: {sorted(missing)}")
    if "id" not in predictions.columns or "anomaly_label" not in predictions.columns:
        raise ValueError("В predictions нужны столбцы id и anomaly_label")

    merged = predictions[["id", "anomaly_label"]].merge(
        labels[["id", "is_anomaly"]],
        on="id",
        how="inner",
        validate="one_to_one",
    )
    if merged.empty:
        raise ValueError("Нет пересечения между predictions и ручной разметкой")

    y_true = merged["is_anomaly"].astype(bool)
    y_pred = merged["anomaly_label"].eq("Аномалия")
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="binary",
        zero_division=0,
    )
    return {
        "labeled_rows": int(len(merged)),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Оценка anomaly detection на разметке")
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    args = parser.parse_args()

    metrics = evaluate_predictions(
        pd.read_csv(args.predictions),
        pd.read_csv(args.labels),
    )
    print(pd.Series(metrics).to_string())
    print("\nDetailed report:")
    predictions = pd.read_csv(args.predictions)
    labels = pd.read_csv(args.labels)
    merged = predictions[["id", "anomaly_label"]].merge(labels, on="id", how="inner")
    print(
        classification_report(
            merged["is_anomaly"].astype(bool),
            merged["anomaly_label"].eq("Аномалия"),
            zero_division=0,
        )
    )


if __name__ == "__main__":
    main()
