"""Unit tests for the weighted risk-scoring engine."""
from datetime import datetime, timedelta

import pytest

from backend.scoring.risk_scorer import (
    compute_score,
    recency_decay,
    mark_new_signals,
    score_label,
    score_color,
)


def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _days_ago(n: int) -> str:
    return (datetime.utcnow() - timedelta(days=n)).strftime("%Y-%m-%d")


# ── recency_decay ───────────────────────────────────────────────────────────

def test_decay_today_is_one():
    assert recency_decay(_today()) == pytest.approx(1.0, abs=0.02)


def test_decay_halves_at_half_life():
    # 30-day half-life → ~0.5 weight
    assert recency_decay(_days_ago(30)) == pytest.approx(0.5, abs=0.05)


def test_decay_invalid_date_defaults_to_half():
    assert recency_decay("not-a-date") == 0.5


# ── compute_score ───────────────────────────────────────────────────────────

def test_no_signals_scores_zero():
    assert compute_score([], 1.0) == 0.0


def test_three_fresh_criticals_near_max():
    signals = [{"severity": 5, "date_detected": _today()} for _ in range(3)]
    assert compute_score(signals, vendor_weight=1.0) == pytest.approx(100.0, abs=1.0)


def test_score_never_exceeds_100():
    signals = [{"severity": 5, "date_detected": _today()} for _ in range(10)]
    assert compute_score(signals, vendor_weight=2.0) == 100.0


def test_weight_amplifies_score():
    signals = [{"severity": 3, "date_detected": _today()}]
    low = compute_score(signals, vendor_weight=1.0)
    high = compute_score(signals, vendor_weight=1.5)
    assert high > low


def test_old_signal_scores_less_than_fresh():
    fresh = compute_score([{"severity": 4, "date_detected": _today()}], 1.0)
    stale = compute_score([{"severity": 4, "date_detected": _days_ago(90)}], 1.0)
    assert stale < fresh


# ── delta / new-signal flagging ─────────────────────────────────────────────

def test_mark_new_signals_flags_correctly():
    signals = [
        {"summary": "brand new breach"},
        {"summary": "already seen"},
    ]
    known = {"already seen"}
    marked = mark_new_signals(signals, known)
    assert marked[0]["is_new"] == 1
    assert marked[1]["is_new"] == 0


# ── labels / colors ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,label", [
    (95.0, "Critical"),
    (75.0, "Critical"),
    (60.0, "High"),
    (30.0, "Medium"),
    (5.0, "Low"),
    (0.0, "Clear"),
])
def test_score_label_thresholds(score, label):
    assert score_label(score) == label


@pytest.mark.parametrize("score,color", [
    (80.0, "red"),
    (55.0, "orange"),
    (30.0, "yellow"),
    (0.0, "green"),
])
def test_score_color_thresholds(score, color):
    assert score_color(score) == color
