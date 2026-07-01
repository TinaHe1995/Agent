"""Financial data matching between budget lines and expenses."""

from __future__ import annotations

from app.database import connect


def list_budget_items(project_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM budget_items WHERE project_id = ? ORDER BY id",
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_budget_item(project_id: int, category: str, planned_amount: float) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO budget_items (project_id, category, planned_amount)
            VALUES (?, ?, ?)
            """,
            (project_id, category, planned_amount),
        )


def list_expenses(project_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT e.*, b.category AS budget_category
            FROM expenses e
            LEFT JOIN budget_items b ON e.budget_item_id = b.id
            WHERE e.project_id = ?
            ORDER BY e.expense_date DESC, e.id DESC
            """,
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_expense(
    project_id: int,
    description: str,
    amount: float,
    expense_date: str,
    budget_item_id: int | None = None,
    vendor: str | None = None,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO expenses
            (project_id, budget_item_id, description, amount, expense_date, vendor)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, budget_item_id, description, amount, expense_date, vendor),
        )


def total_spent(project_id: int) -> float:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses WHERE project_id = ?
            """,
            (project_id,),
        ).fetchone()
    return float(row["total"])


def match_summary(project_id: int) -> list[dict]:
    """Match budget categories to actual spending."""
    items = list_budget_items(project_id)
    with connect() as conn:
        spent_by_item = {
            row["budget_item_id"]: float(row["total"])
            for row in conn.execute(
                """
                SELECT budget_item_id, COALESCE(SUM(amount), 0) AS total
                FROM expenses
                WHERE project_id = ? AND budget_item_id IS NOT NULL
                GROUP BY budget_item_id
                """,
                (project_id,),
            )
        }
    result = []
    for item in items:
        actual = spent_by_item.get(item["id"], 0.0)
        planned = float(item["planned_amount"])
        variance = actual - planned
        result.append(
            {
                "category": item["category"],
                "planned": planned,
                "actual": actual,
                "variance": variance,
                "match_rate": (actual / planned * 100) if planned else 0.0,
            }
        )
    unmatched = total_unmatched(project_id)
    if unmatched:
        result.append(
            {
                "category": "未匹配支出",
                "planned": 0.0,
                "actual": unmatched,
                "variance": unmatched,
                "match_rate": 0.0,
            }
        )
    return result


def total_unmatched(project_id: int) -> float:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE project_id = ? AND budget_item_id IS NULL
            """,
            (project_id,),
        ).fetchone()
    return float(row["total"])
