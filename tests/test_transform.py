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


def test_transform_uses_margin_rate():
    df = transform_data(_sample_raw(), margin_rate=0.25)
    assert "profit" in df.columns
    assert "margin" in df.columns
    assert (df["margin"] == 0.25).all()
    # 1500 * 0.25 = 375
    assert float(df.loc[df["amount"] == 1500, "profit"].iloc[0]) == 375.0


def test_transform_drops_duplicates_and_nulls():
    df = transform_data(_sample_raw(), margin_rate=0.38)
    # duplicate id=2 dropped, null amount dropped → 2 rows
    assert len(df) == 2
    assert df["amount"].notna().all()


def test_transform_adds_year_month_and_quantity():
    df = transform_data(_sample_raw().dropna(subset=["amount"]), margin_rate=0.38)
    assert "year_month" in df.columns
    assert "quantity" in df.columns
    assert (df["quantity"] == 1).all()
    assert set(df["year_month"]) <= {"2024-01", "2024-02"}


def test_transform_data_quality_flag():
    df = transform_data(_sample_raw(), margin_rate=0.38)
    low = df[df["amount"] < 1000]
    assert (low["data_quality"] == "Низкая сумма").all()
    ok = df[df["amount"] >= 1000]
    assert (ok["data_quality"] == "OK").all()


def test_invalid_margin_rate():
    with pytest.raises(ValueError, match="margin_rate"):
        transform_data(_sample_raw(), margin_rate=0)
    with pytest.raises(ValueError, match="margin_rate"):
        transform_data(_sample_raw(), margin_rate=1.5)
