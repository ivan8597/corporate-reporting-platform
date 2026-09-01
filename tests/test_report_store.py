import pandas as pd

from services.report_store import ReportStore


def test_report_store_update_and_get():
    store = ReportStore()
    assert store.get_report_path() is None
    assert store.get_kpis() == {}
    assert store.get_anomalies() is None

    anomalies = pd.DataFrame(
        {
            "anomaly_label": ["Аномалия", "Норма"],
            "amount": [5000, 100],
            "business_reason": ["высокая сумма", ""],
        }
    )
    store.update(
        report_path="data/reports/test.xlsx",
        kpis={"Total_Revenue": 1000.0, "MoM_Growth_%": 5.5},
        anomalies=anomalies,
    )

    assert store.get_report_path() == "data/reports/test.xlsx"
    assert store.get_kpis()["Total_Revenue"] == 1000.0
    assert store.get_kpis()["MoM_Growth_%"] == 5.5

    got = store.get_anomalies()
    assert got is not None
    assert len(got) == 2
    # изоляция: изменение копии не должно портить store
    got.loc[0, "amount"] = -1
    assert store.get_anomalies().iloc[0]["amount"] == 5000


def test_report_store_clear():
    store = ReportStore()
    store.update(
        report_path="x.xlsx",
        kpis={"a": 1},
        anomalies=pd.DataFrame({"anomaly_label": ["Норма"]}),
    )
    store.clear()
    assert store.get_report_path() is None
    assert store.get_kpis() == {}
    assert store.get_anomalies() is None
