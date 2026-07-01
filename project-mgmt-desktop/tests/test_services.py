"""Unit tests for project-mgmt-desktop services."""

from datetime import date

import pytest
from app.database import init_db, seed_demo_data
from app.services import alerts, finance, progress, reports


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr("app.database.DB_PATH", db_file)
    init_db()
    seed_demo_data()
    yield


def test_weighted_progress_and_alerts():
    projects = progress.list_projects()
    assert projects
    pid = projects[0]["id"]
    actual = progress.weighted_progress(pid)
    assert 0 <= actual <= 100
    result = alerts.evaluate_alerts(pid)
    assert isinstance(result, list)
    assert any(a["type"] == "进度预警" for a in result)


def test_finance_match_summary():
    pid = progress.list_projects()[0]["id"]
    summary = finance.match_summary(pid)
    assert summary
    assert "category" in summary[0]


def test_monthly_report():
    pid = progress.list_projects()[0]["id"]
    today = date.today()
    report = reports.monthly_report(pid, today.year, today.month)
    assert report["project_name"]
    text = reports.format_report_text(report)
    assert "月度报表" in text
