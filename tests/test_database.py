"""Integration tests for the SQLite persistence layer (temp DB per test)."""
from backend.db import database as db


def _signal(summary="breach", severity=4, vendor="Okta"):
    return {
        "vendor": vendor,
        "category": "Security",
        "severity": severity,
        "summary": summary,
        "source_url": "https://example.com/incident",
        "date_detected": "2026-05-25",
        "is_new": 1,
    }


def test_upsert_and_get_vendor():
    db.upsert_vendor("Okta", "okta.com", 1.4, "Identity")
    v = db.get_vendor("Okta")
    assert v["domain"] == "okta.com"
    assert v["weight"] == 1.4
    # upsert again updates rather than duplicating
    db.upsert_vendor("Okta", "okta.com", 1.6, "Identity / SSO")
    assert db.get_vendor("Okta")["weight"] == 1.6
    assert len(db.get_all_vendors()) == 1


def test_get_missing_vendor_returns_none():
    assert db.get_vendor("Nope") is None


def test_run_and_signals_roundtrip():
    run_id = db.create_run("Okta")
    ids = db.insert_signals(run_id, [_signal("a"), _signal("b")])
    assert len(ids) == 2
    rows = db.get_signals_for_run(run_id)
    assert {r["summary"] for r in rows} == {"a", "b"}


def test_insert_empty_signals_is_noop():
    run_id = db.create_run("Okta")
    assert db.insert_signals(run_id, []) == []


def test_known_summaries_only_from_completed_runs():
    run_id = db.create_run("Okta")
    db.insert_signals(run_id, [_signal("known incident")])
    db.complete_run(run_id)
    known = db.get_known_summaries("Okta")
    assert "known incident" in known


def test_latest_score_requires_completed_run():
    run_id = db.create_run("Okta")
    db.upsert_score(run_id, "Okta", 88.5, 3)
    # run not completed yet → latest_score (status='done' filter) returns None
    assert db.get_latest_score("Okta") is None
    db.complete_run(run_id)
    score = db.get_latest_score("Okta")
    assert score["score"] == 88.5
    assert score["signal_count"] == 3


def test_all_latest_scores_picks_most_recent():
    r1 = db.create_run("Okta")
    db.upsert_score(r1, "Okta", 40.0, 1)
    db.complete_run(r1)
    r2 = db.create_run("Okta")
    db.upsert_score(r2, "Okta", 90.0, 3)
    db.complete_run(r2)
    # computed_at has 1-second resolution, so same-second inserts tie. Force r2
    # strictly newer to deterministically test the "latest score wins" logic.
    with db.get_db() as conn:
        conn.execute(
            "UPDATE vendor_scores SET computed_at = '2099-01-01 00:00:00' WHERE run_id = ?",
            (r2,),
        )
    scores = {s["vendor"]: s["score"] for s in db.get_all_latest_scores()}
    assert scores["Okta"] == 90.0


def test_new_signals_since_filters_by_date_and_flag():
    run_id = db.create_run("Okta")
    db.insert_signals(run_id, [
        {**_signal("recent new"), "date_detected": "2026-05-28", "is_new": 1},
        {**_signal("old known"), "date_detected": "2026-01-01", "is_new": 0},
    ])
    db.complete_run(run_id)
    results = db.get_new_signals_since("2026-05-01")
    summaries = {r["summary"] for r in results}
    assert "recent new" in summaries
    assert "old known" not in summaries  # is_new=0 excluded
