import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DATABASE = os.environ.get("DATABASE_PATH", "actions.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS action_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_name TEXT,
                task TEXT,
                person_raw TEXT,
                person_slack_id TEXT,
                deadline TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS name_mapping (
                raw_name TEXT PRIMARY KEY,
                slack_id TEXT,
                email TEXT
            )
        """)
        conn.execute("""
    CREATE TABLE IF NOT EXISTS meeting_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_name TEXT,
        transcript_excerpt TEXT,
        score INTEGER,
        breakdown TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
           )
          """)
        # Demo mappings – REPLACE with real Slack IDs using update_slack_ids.py
        conn.execute("INSERT OR IGNORE INTO name_mapping VALUES ('john', 'U123456', 'john@example.com')")
        conn.execute("INSERT OR IGNORE INTO name_mapping VALUES ('sarah', 'U789012', 'sarah@example.com')")
        conn.execute("INSERT OR IGNORE INTO name_mapping VALUES ('alex', 'U111111', 'alex@example.com')")
        print("Database initialized.")

def add_action_item(meeting_name, task, person_raw, person_slack_id, deadline):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO action_items (meeting_name, task, person_raw, person_slack_id, deadline) VALUES (?, ?, ?, ?, ?)",
            (meeting_name, task, person_raw, person_slack_id, deadline)
        )
        return cursor.lastrowid

def get_pending_items_for_slack_id(slack_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT id, task, deadline FROM action_items WHERE person_slack_id = ? AND status = 'pending'",
            (slack_id,)
        ).fetchall()

def mark_completed(item_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE action_items SET status = 'completed', completed_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), item_id)
        )

def get_all_uncompleted():
    with get_db() as conn:
        return conn.execute("SELECT * FROM action_items WHERE status = 'pending'").fetchall()

def get_stats_for_week():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as count FROM action_items WHERE created_at >= date('now', '-7 days')").fetchone()['count']
        completed = conn.execute("SELECT COUNT(*) as count FROM action_items WHERE status = 'completed' AND completed_at >= date('now', '-7 days')").fetchone()['count']
        pending_by_person = conn.execute("""
            SELECT person_raw, COUNT(*) as cnt FROM action_items
            WHERE status = 'pending' GROUP BY person_raw
        """).fetchall()
        return total, completed, pending_by_person
def save_meeting_score(meeting_name, transcript_excerpt, score, breakdown):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO meeting_scores (meeting_name, transcript_excerpt, score, breakdown) VALUES (?, ?, ?, ?)",
            (meeting_name, transcript_excerpt[:500], score, str(breakdown))
        )

def get_all_meeting_scores(limit=20):
    with get_db() as conn:
        return conn.execute(
            "SELECT meeting_name, score, created_at FROM meeting_scores ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()