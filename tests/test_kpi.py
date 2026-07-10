import pandas as pd

from kpi.calculator import calculate_kpis


def test_calculate_kpis():

    df = pd.DataFrame(
        {
            "amount": [100, 200],
            "profit": [40, 80],
            "margin": [0.4, 0.4],
            "product_name": [
                "A",
                "B"
            ],
            "manager_name": [
                "Manager1",
                "Manager2"
            ]
        }
    )


    result = calculate_kpis(df)


    assert result["Total_Revenue"] == 300
    assert result["Total_Profit"] == 120
    assert result["Total_Orders"] == 2
