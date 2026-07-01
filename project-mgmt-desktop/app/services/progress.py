"""Project progress tracking and schedule analysis."""

from __future__ import annotations

from datetime import date

from app.database import connect


def list_projects() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_project(project_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    return dict(row) if row else None


def add_project(
    name: str, planned_start: str, planned_end: str, budget: float
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO projects (name, planned_start, planned_end, budget)
            VALUES (?, ?, ?, ?)
            """,
            (name, planned_start, planned_end, budget),
        )
        return int(cur.lastrowid)


def list_tasks(project_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE project_id = ? ORDER BY id",
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_task(
    project_id: int,
    name: str,
    weight: float,
    progress: float,
    planned_end: str | None,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO tasks (project_id, name, weight, progress, planned_end)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, name, weight, progress, planned_end),
        )


def update_task_progress(task_id: int, progress: float) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE tasks SET progress = ? WHERE id = ?",
            (max(0.0, min(100.0, progress)), task_id),
        )


def weighted_progress(project_id: int) -> float:
    tasks = list_tasks(project_id)
    if not tasks:
        return 0.0
    total_weight = sum(t["weight"] for t in tasks)
    if total_weight <= 0:
        return 0.0
    return sum(t["progress"] * t["weight"] for t in tasks) / total_weight


def schedule_progress(project: dict, on_day: date | None = None) -> float:
    """Expected progress based on elapsed time in the project window."""
    today = on_day or date.today()
    start = date.fromisoformat(project["planned_start"])
    end = date.fromisoformat(project["planned_end"])
    if today <= start:
        return 0.0
    if today >= end:
        return 100.0
    total_days = (end - start).days or 1
    elapsed = (today - start).days
    return min(100.0, max(0.0, elapsed / total_days * 100))
