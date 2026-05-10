"""
Audit Trail Logger
Every action is logged: scores, overrides, emails generated, timestamps.
Stored in SQLite for persistence and auditability.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/audit_trail.db")


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            candidate_name TEXT,
            session_id TEXT,
            details TEXT,
            actor TEXT DEFAULT 'system'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS hr_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            candidate_name TEXT NOT NULL,
            original_score REAL,
            override_score REAL,
            reason TEXT NOT NULL,
            hr_name TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_action(action: str, candidate_name: str = None, details: dict = None, actor: str = "system", session_id: str = None):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO audit_log (timestamp, action, candidate_name, session_id, details, actor)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        action,
        candidate_name,
        session_id or "default",
        json.dumps(details or {}),
        actor,
    ))
    conn.commit()
    conn.close()


def log_override(candidate_name: str, original_score: float, override_score: float, reason: str, hr_name: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO hr_overrides (timestamp, candidate_name, original_score, override_score, reason, hr_name)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        candidate_name,
        original_score,
        override_score,
        reason,
        hr_name,
    ))
    conn.commit()
    conn.close()
    log_action("HR_OVERRIDE", candidate_name, {
        "from": original_score, "to": override_score, "reason": reason
    }, actor=hr_name)


def get_audit_log() -> list[dict]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_overrides() -> list[dict]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM hr_overrides ORDER BY timestamp DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
