"""Monthly report generation."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

from app.database import connect
from app.services import alerts, finance, progress


def monthly_report(project_id: int, year: int, month: int) -> dict:
    project = progress.get_project(project_id)
    if not project:
        return {}

    start = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end = date(year, month, last_day)

    with connect() as conn:
        month_expenses = conn.execute(
            """
            SELECT e.*, b.category AS budget_category
            FROM expenses e
            LEFT JOIN budget_items b ON e.budget_item_id = b.id
            WHERE e.project_id = ?
              AND e.expense_date >= ?
              AND e.expense_date <= ?
            ORDER BY e.expense_date
            """,
            (project_id, start.isoformat(), end.isoformat()),
        ).fetchall()

    month_total = sum(float(row["amount"]) for row in month_expenses)
    overall_spent = finance.total_spent(project_id)
    budget = float(project["budget"])
    actual_progress = progress.weighted_progress(project_id)
    expected_progress = progress.schedule_progress(project, end)

    return {
        "project_name": project["name"],
        "period": f"{year}年{month:02d}月",
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "budget": budget,
        "month_spent": month_total,
        "total_spent": overall_spent,
        "budget_remaining": budget - overall_spent,
        "budget_usage_pct": (overall_spent / budget * 100) if budget else 0,
        "actual_progress": actual_progress,
        "expected_progress": expected_progress,
        "progress_gap": expected_progress - actual_progress,
        "month_expenses": [dict(row) for row in month_expenses],
        "finance_match": finance.match_summary(project_id),
        "alerts": alerts.evaluate_alerts(project_id, end),
        "tasks": progress.list_tasks(project_id),
    }


def format_report_text(report: dict) -> str:
    if not report:
        return "无数据"
    lines = [
        f"# {report['project_name']} — {report['period']} 月度报表",
        "",
        "## 进度概览",
        f"- 加权实际进度: {report['actual_progress']:.1f}%",
        f"- 计划进度（月末）: {report['expected_progress']:.1f}%",
        f"- 进度偏差: {report['progress_gap']:.1f} 个百分点",
        "",
        "## 财务概览",
        f"- 项目总预算: {report['budget']:,.2f} 元",
        f"- 本月支出: {report['month_spent']:,.2f} 元",
        f"- 累计支出: {report['total_spent']:,.2f} 元",
        f"- 预算余额: {report['budget_remaining']:,.2f} 元",
        f"- 预算使用率: {report['budget_usage_pct']:.1f}%",
        "",
        "## 财务匹配",
    ]
    for row in report["finance_match"]:
        lines.append(
            f"- {row['category']}: 预算 {row['planned']:,.0f} / "
            f"实际 {row['actual']:,.0f} / 差异 {row['variance']:+,.0f}"
        )
    lines.extend(["", "## 预警"])
    if report["alerts"]:
        for alert in report["alerts"]:
            lines.append(f"- [{alert['type']}] {alert['message']}")
    else:
        lines.append("- 本月无预警")
    lines.extend(["", "## 本月支出明细"])
    if report["month_expenses"]:
        for exp in report["month_expenses"]:
            cat = exp.get("budget_category") or "未匹配"
            lines.append(
                f"- {exp['expense_date']} {exp['description']}: "
                f"{exp['amount']:,.2f} 元 ({cat})"
            )
    else:
        lines.append("- 本月无支出记录")
    return "\n".join(lines)
