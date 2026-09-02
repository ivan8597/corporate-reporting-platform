import pandas as pd

from kpi.calculator import _calculate_mom_growth, calculate_kpis


def test_calculate_kpis_basic():
    df = pd.DataFrame(
        {
            "amount": [100, 200],
            "profit": [40, 80],
            "margin": [0.4, 0.4],
            "product_name": ["A", "B"],
            "manager_name": ["Manager1", "Manager2"],
            "year_month": ["2024-01", "2024-01"],
        }
    )

    result = calculate_kpis(df)

    assert result["Total_Revenue"] == 300
    assert result["Total_Profit"] == 120
    assert result["Total_Orders"] == 2
    assert result["Avg_Check"] == 150.0
    assert result["Avg_Margin_%"] == 40.0
    # Один месяц — MoM не считается
    assert result["MoM_Growth_%"] is None


def test_mom_growth_positive():
    df = pd.DataFrame(
        {
            "amount": [100, 100, 150, 150],
            "year_month": ["2024-01", "2024-01", "2024-02", "2024-02"],
        }
    )
    growth = _calculate_mom_growth(df)
    # (300 - 200) / 200 * 100 = 50
    assert growth == 50.0


def test_mom_growth_negative():
    df = pd.DataFrame(
        {
            "amount": [200, 100],
            "year_month": ["2024-01", "2024-02"],
        }
    )
    growth = _calculate_mom_growth(df)
    assert growth == -50.0


def test_mom_growth_insufficient_data():
    df = pd.DataFrame({"amount": [100], "year_month": ["2024-01"]})
    assert _calculate_mom_growth(df) is None

    empty = pd.DataFrame(columns=["amount", "year_month"])
    assert _calculate_mom_growth(empty) is None


def test_top_products_and_managers():
    df = pd.DataFrame(
        {
            "amount": [100, 200, 50],
            "profit": [38, 76, 19],
            "margin": [0.38, 0.38, 0.38],
            "product_name": ["A", "B", "A"],
            "manager_name": ["X", "Y", "X"],
            "year_month": ["2024-01", "2024-01", "2024-01"],
        }
    )
    result = calculate_kpis(df)
    assert result["Top_Products"]["B"] == 200.0
    assert result["Top_Products"]["A"] == 150.0
    assert result["Top_Managers"]["Y"] == 200.0
    assert result["Top_Managers"]["X"] == 150.0
