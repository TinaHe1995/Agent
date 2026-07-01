"""SQLite persistence for the project management desktop app."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                planned_start TEXT NOT NULL,
                planned_end TEXT NOT NULL,
                budget REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                weight REAL NOT NULL DEFAULT 1,
                progress REAL NOT NULL DEFAULT 0,
                planned_end TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS budget_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                planned_amount REAL NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                budget_item_id INTEGER,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                expense_date TEXT NOT NULL,
                vendor TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (budget_item_id) REFERENCES budget_items(id)
            );

            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                rule_type TEXT NOT NULL,
                threshold REAL NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """
        )


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def seed_demo_data() -> None:
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if count:
            return
        conn.execute(
            """
            INSERT INTO projects (name, planned_start, planned_end, budget)
            VALUES (?, ?, ?, ?)
            """,
            ("办公楼装修", "2026-01-01", "2026-06-30", 500000),
        )
        project_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        tasks = [
            (project_id, "设计阶段", 20, 100, "2026-02-15"),
            (project_id, "主体施工", 50, 45, "2026-05-31"),
            (project_id, "验收交付", 30, 10, "2026-06-30"),
        ]
        conn.executemany(
            "INSERT INTO tasks (project_id, name, weight, progress, planned_end) "
            "VALUES (?, ?, ?, ?, ?)",
            tasks,
        )
        budget_rows = [
            (project_id, "设计费", 80000),
            (project_id, "材料费", 250000),
            (project_id, "人工费", 120000),
            (project_id, "管理费", 50000),
        ]
        conn.executemany(
            "INSERT INTO budget_items (project_id, category, planned_amount) "
            "VALUES (?, ?, ?)",
            budget_rows,
        )
        budget_ids = [
            row[0]
            for row in conn.execute(
                "SELECT id FROM budget_items WHERE project_id = ? ORDER BY id",
                (project_id,),
            )
        ]
        today = date.today().isoformat()
        expenses = [
            (project_id, budget_ids[0], "方案设计", 75000, "2026-01-20", "设计院A"),
            (project_id, budget_ids[1], "钢材采购", 120000, today, "建材商B"),
            (project_id, budget_ids[2], "施工队首期", 60000, today, "施工队C"),
            (project_id, None, "临时杂项", 8000, today, "杂项"),
        ]
        conn.executemany(
            """
            INSERT INTO expenses
            (project_id, budget_item_id, description, amount, expense_date, vendor)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            expenses,
        )
        rules = [
            (project_id, "progress_behind", 15),
            (project_id, "budget_overrun", 10),
        ]
        conn.executemany(
            "INSERT INTO alert_rules (project_id, rule_type, threshold) "
            "VALUES (?, ?, ?)",
            rules,
        )
