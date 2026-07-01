"""Progress and budget alert evaluation."""

from __future__ import annotations

from datetime import date

from app.database import connect
from app.services import finance, progress


def list_rules(project_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM alert_rules WHERE project_id = ? ORDER BY id",
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def upsert_rule(project_id: int, rule_type: str, threshold: float) -> None:
    with connect() as conn:
        existing = conn.execute(
            """
            SELECT id FROM alert_rules
            WHERE project_id = ? AND rule_type = ?
            """,
            (project_id, rule_type),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE alert_rules SET threshold = ?, enabled = 1 WHERE id = ?",
                (threshold, existing["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO alert_rules (project_id, rule_type, threshold)
                VALUES (?, ?, ?)
                """,
                (project_id, rule_type, threshold),
            )


def evaluate_alerts(project_id: int, on_day: date | None = None) -> list[dict]:
    project = progress.get_project(project_id)
    if not project:
        return []

    rules = {r["rule_type"]: r for r in list_rules(project_id) if r["enabled"]}
    alerts: list[dict] = []
    today = on_day or date.today()

    progress_rule = rules.get("progress_behind")
    if progress_rule:
        actual = progress.weighted_progress(project_id)
        expected = progress.schedule_progress(project, today)
        gap = expected - actual
        threshold = float(progress_rule["threshold"])
        if gap >= threshold:
            alerts.append(
                {
                    "level": "warning" if gap < threshold * 2 else "critical",
                    "type": "进度预警",
                    "message": (
                        f"实际进度 {actual:.1f}% 低于计划进度 {expected:.1f}%，"
                        f"落后 {gap:.1f} 个百分点（阈值 {threshold:.0f}%）"
                    ),
                }
            )

    budget_rule = rules.get("budget_overrun")
    if budget_rule:
        spent = finance.total_spent(project_id)
        budget = float(project["budget"])
        if budget > 0:
            usage_pct = spent / budget * 100
            expected_pct = progress.schedule_progress(project, today)
            overrun = usage_pct - expected_pct
            threshold = float(budget_rule["threshold"])
            if overrun >= threshold:
                alerts.append(
                    {
                        "level": "warning" if overrun < threshold * 2 else "critical",
                        "type": "财务预算预警",
                        "message": (
                            f"已支出 {spent:,.0f} 元（{usage_pct:.1f}% 总预算），"
                            f"高于计划消耗节奏 {expected_pct:.1f}%，"
                            f"超支节奏 {overrun:.1f} 个百分点（阈值 {threshold:.0f}%）"
                        ),
                    }
                )
        if spent > budget:
            alerts.append(
                {
                    "level": "critical",
                    "type": "财务预算预警",
                    "message": f"总支出 {spent:,.0f} 元已超过项目预算 {budget:,.0f} 元",
                }
            )

    overdue_tasks = [
        t
        for t in progress.list_tasks(project_id)
        if t.get("planned_end")
        and date.fromisoformat(t["planned_end"]) < today
        and t["progress"] < 100
    ]
    for task in overdue_tasks:
        alerts.append(
            {
                "level": "warning",
                "type": "进度预警",
                "message": (
                    f"任务「{task['name']}」已逾期（计划 {task['planned_end']}），"
                    f"当前完成 {task['progress']:.0f}%"
                ),
            }
        )

    return alerts
