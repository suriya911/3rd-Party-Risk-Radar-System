"""SQLite persistence for risk signals, vendor scores, and scan runs."""
import json
import math
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from backend.config import settings

DB_PATH = Path(settings.database_url)

SCHEMA = """
CREATE TABLE IF NOT EXISTS vendors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT UNIQUE NOT NULL,
    domain      TEXT NOT NULL,
    weight      REAL NOT NULL DEFAULT 1.0,
    stack_role  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS scan_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at      TEXT NOT NULL DEFAULT (datetime('now')),
    vendor_name TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',  -- pending | done | error
    FOREIGN KEY (vendor_name) REFERENCES vendors(name)
);

CREATE TABLE IF NOT EXISTS risk_signals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL,
    vendor        TEXT NOT NULL,
    category      TEXT NOT NULL,   -- Security|Financial|Operational|Regulatory|Reputational
    severity      INTEGER NOT NULL CHECK(severity BETWEEN 1 AND 5),
    summary       TEXT NOT NULL,
    source_url    TEXT NOT NULL,
    date_detected TEXT NOT NULL,
    is_new        INTEGER NOT NULL DEFAULT 1,  -- 1=new since last run, 0=known
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES scan_runs(id)
);

CREATE TABLE IF NOT EXISTS vendor_scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL,
    vendor      TEXT NOT NULL,
    score       REAL NOT NULL,
    signal_count INTEGER NOT NULL DEFAULT 0,
    computed_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES scan_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_signals_vendor ON risk_signals(vendor);
CREATE INDEX IF NOT EXISTS idx_signals_run    ON risk_signals(run_id);
CREATE INDEX IF NOT EXISTS idx_scores_vendor  ON vendor_scores(vendor);
CREATE INDEX IF NOT EXISTS idx_runs_vendor    ON scan_runs(vendor_name);
"""


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA)


# ── Vendors ────────────────────────────────────────────────────────────────

def upsert_vendor(name: str, domain: str, weight: float, stack_role: str = ""):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO vendors (name, domain, weight, stack_role)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                domain=excluded.domain,
                weight=excluded.weight,
                stack_role=excluded.stack_role
            """,
            (name, domain, weight, stack_role),
        )


def get_all_vendors() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM vendors ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def get_vendor(name: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM vendors WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None


# ── Scan Runs ──────────────────────────────────────────────────────────────

def create_run(vendor_name: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO scan_runs (vendor_name, status) VALUES (?, 'pending')",
            (vendor_name,),
        )
        return cur.lastrowid


def complete_run(run_id: int, status: str = "done"):
    with get_db() as conn:
        conn.execute(
            "UPDATE scan_runs SET status = ? WHERE id = ?",
            (status, run_id),
        )


def get_last_run(vendor_name: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT * FROM scan_runs
            WHERE vendor_name = ? AND status = 'done'
            ORDER BY run_at DESC LIMIT 1
            """,
            (vendor_name,),
        ).fetchone()
        return dict(row) if row else None


# ── Risk Signals ───────────────────────────────────────────────────────────

def insert_signals(run_id: int, signals: list[dict]) -> list[int]:
    if not signals:
        return []
    with get_db() as conn:
        ids = []
        for s in signals:
            cur = conn.execute(
                """
                INSERT INTO risk_signals
                    (run_id, vendor, category, severity, summary, source_url, date_detected, is_new)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    s["vendor"],
                    s["category"],
                    int(s["severity"]),
                    s["summary"],
                    s["source_url"],
                    s["date_detected"],
                    s.get("is_new", 1),
                ),
            )
            ids.append(cur.lastrowid)
        return ids


def get_signals_for_run(run_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM risk_signals WHERE run_id = ? ORDER BY severity DESC",
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_latest_signals(vendor: str, limit: int = 50) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT rs.* FROM risk_signals rs
            JOIN scan_runs sr ON rs.run_id = sr.id
            WHERE rs.vendor = ? AND sr.status = 'done'
            ORDER BY sr.run_at DESC, rs.severity DESC
            LIMIT ?
            """,
            (vendor, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_new_signals_since(since_date: str) -> list[dict]:
    """Return signals flagged as new that were detected on or after since_date."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT rs.*, sr.run_at FROM risk_signals rs
            JOIN scan_runs sr ON rs.run_id = sr.id
            WHERE rs.date_detected >= ? AND rs.is_new = 1 AND sr.status = 'done'
            ORDER BY rs.date_detected DESC, rs.severity DESC
            """,
            (since_date,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_known_summaries(vendor: str) -> set[str]:
    """Return summaries from previous runs to detect duplicates."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT rs.summary FROM risk_signals rs
            JOIN scan_runs sr ON rs.run_id = sr.id
            WHERE rs.vendor = ? AND sr.status = 'done'
            ORDER BY sr.run_at DESC
            LIMIT 200
            """,
            (vendor,),
        ).fetchall()
        return {r["summary"] for r in rows}


# ── Vendor Scores ──────────────────────────────────────────────────────────

def upsert_score(run_id: int, vendor: str, score: float, signal_count: int):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO vendor_scores (run_id, vendor, score, signal_count)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, vendor, round(score, 2), signal_count),
        )


def get_latest_score(vendor: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT vs.* FROM vendor_scores vs
            JOIN scan_runs sr ON vs.run_id = sr.id
            WHERE vs.vendor = ? AND sr.status = 'done'
            ORDER BY vs.computed_at DESC LIMIT 1
            """,
            (vendor,),
        ).fetchone()
        return dict(row) if row else None


def get_all_latest_scores() -> list[dict]:
    """Latest score per vendor across all completed runs."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT vs.vendor, vs.score, vs.signal_count, vs.computed_at
            FROM vendor_scores vs
            INNER JOIN (
                SELECT vendor, MAX(computed_at) as max_at
                FROM vendor_scores
                GROUP BY vendor
            ) latest ON vs.vendor = latest.vendor AND vs.computed_at = latest.max_at
            ORDER BY vs.score DESC
            """,
        ).fetchall()
        return [dict(r) for r in rows]
