import pandas as pd
import pytest

from etl.transform import transform_data


def _sample_raw() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1, 2, 2, 3],
            "date": ["2024-01-15", "2024-02-01", "2024-02-01", "2024-03-10"],
            "amount": [1500.0, 800.0, 800.0, None],
            "product_name": ["Ноутбук", "Мышь", "Мышь", "Монитор"],
            "manager_name": ["Анна", "Борис", "Борис", "Виктор"],
            "region": ["Центр", "Север", "Север", "Юг"],
        }
    )


def test_transform_product_specific_margins():
    df = transform_data(_sample_raw())
    notebook = df.loc[df["product_name"] == "Ноутбук"].iloc[0]
    mouse = df.loc[df["product_name"] == "Мышь"].iloc[0]

    assert notebook["margin"] == pytest.approx(0.22)
    assert mouse["margin"] == pytest.approx(0.48)
    assert float(notebook["profit"]) == pytest.approx(1500 * 0.22, abs=0.01)
    assert float(mouse["profit"]) == pytest.approx(800 * 0.48, abs=0.01)
    assert notebook["margin"] != mouse["margin"]


def test_transform_uses_explicit_margin_rate():
    df = transform_data(_sample_raw(), margin_rate=0.25)
    assert (df["margin"] == 0.25).all()
    assert float(df.loc[df["amount"] == 1500, "profit"].iloc[0]) == 375.0


def test_transform_from_cost_column():
    raw = pd.DataFrame(
        {
            "date": ["2024-01-15", "2024-02-01"],
            "amount": [1000.0, 2000.0],
            "cost": [700.0, 1200.0],
            "product_name": ["Ноутбук", "Монитор"],
        }
    )
    df = transform_data(raw)
    assert float(df.iloc[0]["profit"]) == 300.0
    assert float(df.iloc[0]["margin"]) == pytest.approx(0.3)
    assert float(df.iloc[1]["profit"]) == 800.0
    assert float(df.iloc[1]["margin"]) == pytest.approx(0.4)


def test_transform_drops_duplicates_and_nulls():
    df = transform_data(_sample_raw())
    assert len(df) == 2
    assert df["amount"].notna().all()


def test_transform_adds_year_month_and_quantity():
    df = transform_data(_sample_raw().dropna(subset=["amount"]))
    assert "year_month" in df.columns
    assert "quantity" in df.columns
    assert (df["quantity"] == 1).all()
    assert set(df["year_month"]) <= {"2024-01", "2024-02"}


def test_low_amount_is_business_classification_not_data_error():
    df = transform_data(_sample_raw())
    low = df[df["amount"] < 1000]
    assert (low["business_classification"] == "Низкая сумма").all()
    assert (low["data_quality"] == "OK").all()


def test_negative_amount_is_data_quality_error():
    raw = pd.DataFrame(
        {
            "date": ["2024-01-15"],
            "amount": [-100.0],
            "product_name": ["Мышь"],
        }
    )
    df = transform_data(raw)
    assert df.iloc[0]["data_quality"] == "Некорректная сумма"


def test_invalid_margin_rate():
    with pytest.raises(ValueError, match="margin_rate"):
        transform_data(_sample_raw(), margin_rate=0)
    with pytest.raises(ValueError, match="margin_rate"):
        transform_data(_sample_raw(), margin_rate=1.5)
