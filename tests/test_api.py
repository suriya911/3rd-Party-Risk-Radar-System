"""API tests using FastAPI's TestClient.

The app lifespan runs init_db + loads vendors.csv into the temp DB, so each
`with TestClient(app)` block starts with the 10 demo vendors present.
Network endpoints (/scan, /proof) are covered by the opt-in live suite."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.db import database as db


def test_health():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_vendors_loaded_from_csv():
    with TestClient(app) as client:
        r = client.get("/vendors")
        assert r.status_code == 200
        names = {v["name"] for v in r.json()}
        assert {"Okta", "AWS", "Datadog"} <= names


def test_vendor_score_surfaces_in_list():
    with TestClient(app) as client:
        run_id = db.create_run("Okta")
        db.upsert_score(run_id, "Okta", 88.5, 3)
        db.complete_run(run_id)

        r = client.get("/vendors")
        okta = next(v for v in r.json() if v["name"] == "Okta")
        assert okta["score"] == 88.5
        assert okta["score_label"] == "Critical"
        assert okta["score_color"] == "red"


def test_vendor_detail_ok():
    with TestClient(app) as client:
        r = client.get("/vendors/Okta")
        assert r.status_code == 200
        assert r.json()["vendor"]["name"] == "Okta"


def test_unknown_vendor_404():
    with TestClient(app) as client:
        assert client.get("/vendors/DoesNotExist").status_code == 404


def test_alerts_structure():
    with TestClient(app) as client:
        run_id = db.create_run("Okta")
        db.insert_signals(run_id, [{
            "vendor": "Okta", "category": "Security", "severity": 5,
            "summary": "fresh breach", "source_url": "https://example.com/b",
            "date_detected": "2026-05-29", "is_new": 1,
        }])
        db.complete_run(run_id)

        r = client.get("/alerts?since=2026-05-01")
        assert r.status_code == 200
        body = r.json()
        assert body["since"] == "2026-05-01"
        assert any(s["summary"] == "fresh breach" for s in body["signals"])
