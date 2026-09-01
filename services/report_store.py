"""Хранилище последнего результата пайплайна для API.

Вместо глобальных переменных в api/app.py используем явный объект состояния,
который можно подменить в тестах и который не зависит от module-level globals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any

import pandas as pd


@dataclass
class ReportState:
    report_path: str | None = None
    kpis: dict[str, Any] = field(default_factory=dict)
    anomalies: pd.DataFrame | None = None


class ReportStore:
    """Потокобезопасное in-memory хранилище последнего отчёта."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._state = ReportState()

    def update(
        self,
        *,
        report_path: str,
        kpis: dict[str, Any],
        anomalies: pd.DataFrame,
    ) -> None:
        with self._lock:
            self._state = ReportState(
                report_path=report_path,
                kpis=dict(kpis),
                anomalies=anomalies.copy() if anomalies is not None else None,
            )

    def get_kpis(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._state.kpis)

    def get_report_path(self) -> str | None:
        with self._lock:
            return self._state.report_path

    def get_anomalies(self) -> pd.DataFrame | None:
        with self._lock:
            if self._state.anomalies is None:
                return None
            return self._state.anomalies.copy()

    def clear(self) -> None:
        with self._lock:
            self._state = ReportState()


# Единственный экземпляр для процесса приложения.
# В тестах можно создать отдельный ReportStore и передать его в зависимости.
report_store = ReportStore()
