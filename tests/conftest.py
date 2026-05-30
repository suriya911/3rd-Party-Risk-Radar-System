"""Shared test setup.

Critically, DATABASE_URL is set to a throwaway temp file *before* any backend
module is imported — `database.py` reads the path at import time, so this must
happen first (overrides whatever .env / compose set)."""
import os
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="rr_test_")
os.environ["DATABASE_URL"] = str(Path(_TMP) / "test.db")
os.environ.setdefault("VENDORS_CSV", "./vendors.csv")
# Keep external keys out of the unit-test process so nothing accidentally
# reaches the network during non-live runs.
os.environ.setdefault("LLM_API_KEY", "")

import pytest  # noqa: E402
from backend.db import database as db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    """Every test starts against an empty, freshly-migrated database."""
    db.init_db()
    with db.get_db() as conn:
        for table in ("risk_signals", "vendor_scores", "scan_runs", "vendors"):
            conn.execute(f"DELETE FROM {table}")
    yield
