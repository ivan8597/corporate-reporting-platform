import pandas as pd
import pytest

from ml.anomaly_detector import detect_anomalies, prepare_features


def _sample_sales(n: int = 40) -> pd.DataFrame:
    rows = []
    for i in range(n):
        rows.append(
            {
                "date": f"2024-01-{(i % 28) + 1:02d} 12:00:00",
                "amount": 1000 + (i % 5) * 50,
                "profit": 380 + (i % 5) * 19,
                "margin": 0.38,
                "quantity": 1,
            }
        )
    # явные выбросы
    rows.append(
        {
            "date": "2024-01-15 03:00:00",
            "amount": 5000,
            "profit": 500,
            "margin": 0.1,
            "quantity": 5,
        }
    )
    return pd.DataFrame(rows)


def test_prepare_features_adds_hour_and_dow():
    df = _sample_sales(5)
    prepared = prepare_features(df)
    assert "hour" in prepared.columns
    assert "day_of_week" in prepared.columns
    assert prepared["hour"].notna().all()


def test_detect_anomalies_labels_and_business_reason():
    df = _sample_sales(50)
    result = detect_anomalies(df, contamination=0.05, n_estimators=50, random_state=42)

    assert "anomaly_label" in result.columns
    assert "anomaly_score" in result.columns
    assert "business_reason" in result.columns
    assert "anomaly_reason" in result.columns  # backwards compat

    labels = set(result["anomaly_label"].unique())
    assert labels <= {"Аномалия", "Норма"}
    assert (result["anomaly_label"] == "Аномалия").sum() >= 1

    anomaly_rows = result[result["anomaly_label"] == "Аномалия"]
    assert anomaly_rows["business_reason"].notna().all()
    assert anomaly_rows["business_reason"].str.len().gt(0).all()


def test_detect_anomalies_invalid_contamination():
    df = _sample_sales(10)
    with pytest.raises(ValueError, match="contamination"):
        detect_anomalies(df, contamination=0.0)
    with pytest.raises(ValueError, match="contamination"):
        detect_anomalies(df, contamination=0.9)


def test_prepare_features_missing_columns():
    df = pd.DataFrame({"date": ["2024-01-01"], "amount": [100]})
    with pytest.raises(ValueError, match="отсутствуют столбцы"):
        prepare_features(df)
