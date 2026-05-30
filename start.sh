#!/bin/sh
# Container entrypoint.
# On a fresh database, load vendors (with their CSV weights) and seed the demo
# signals so the dashboard is populated immediately — no API keys required.
# Live scans (Bright Data + Claude) work once secrets are set as env vars.
set -e

DB_FILE="${DATABASE_URL:-./risk_radar.db}"

if [ ! -f "$DB_FILE" ]; then
  echo "No database at $DB_FILE — loading vendors and seeding demo data..."
  python -c "from backend.db import database as db; db.init_db(); from backend.main import _load_default_vendors; _load_default_vendors()"
  python seed_demo.py
else
  echo "Existing database found at $DB_FILE — skipping seed."
fi

exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-7860}"
