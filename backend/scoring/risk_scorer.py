"""
Weighted risk scoring + delta alerting.

Score formula (0-100):
  raw = sum( severity_i * recency_decay(days_i) )  for each signal
  normalized = (raw / max_possible_raw) * 100 * vendor_weight
  clamped to [0, 100]

Recency decay: exponential with half-life of 30 days.
  decay(d) = 0.5 ^ (d / 30)
"""
import logging
import math
from datetime import datetime

from backend.db import database as db

logger = logging.getLogger(__name__)

HALF_LIFE_DAYS = 30
MAX_SIGNALS_FOR_NORM = 3  # 3 critical recent signals = score ~100
MAX_SEVERITY = 5


def recency_decay(date_detected: str) -> float:
    """Exponential decay: severity halves every 30 days."""
    try:
        detected = datetime.strptime(date_detected, "%Y-%m-%d")
    except ValueError:
        return 0.5
    days = max(0, (datetime.utcnow() - detected).days)
    return math.pow(0.5, days / HALF_LIFE_DAYS)


def compute_score(signals: list[dict], vendor_weight: float = 1.0) -> float:
    """
    Compute 0-100 risk score for a vendor given its extracted signals.
    Higher weight = score amplified (critical vendors punished harder).
    """
    if not signals:
        return 0.0

    raw = sum(
        s["severity"] * recency_decay(s["date_detected"]) for s in signals
    )
    # decay=1 at day 0
    max_possible = float(MAX_SIGNALS_FOR_NORM * MAX_SEVERITY)
    normalized = (raw / max_possible) * 100.0 * vendor_weight
    return round(min(normalized, 100.0), 2)


def mark_new_signals(
    signals: list[dict], known_summaries: set[str]
) -> list[dict]:
    """Flag each signal as new (1) or known (0) based on previous run summaries."""
    for s in signals:
        s["is_new"] = 0 if s["summary"] in known_summaries else 1
    return signals


async def score_and_persist(
    vendor_name: str,
    domain: str,
    signals: list[dict],
    run_id: int,
) -> float:
    """
    1. Load known summaries from prior runs (delta logic).
    2. Mark each signal as new/known.
    3. Compute weighted score.
    4. Persist signals + score.
    Returns the computed score.
    """
    vendor = db.get_vendor(vendor_name)
    weight = vendor["weight"] if vendor else 1.0

    known = db.get_known_summaries(vendor_name)
    signals = mark_new_signals(signals, known)

    db.insert_signals(run_id, signals)

    score = compute_score(signals, weight)
    db.upsert_score(run_id, vendor_name, score, len(signals))

    new_count = sum(1 for s in signals if s.get("is_new", 1))
    logger.info(
        "Score for %s: %.1f (signals=%d, new=%d, weight=%.1f)",
        vendor_name, score, len(signals), new_count, weight,
    )
    return score


def score_label(score: float) -> str:
    """Human-readable risk level from numeric score."""
    if score >= 75:
        return "Critical"
    if score >= 50:
        return "High"
    if score >= 25:
        return "Medium"
    if score > 0:
        return "Low"
    return "Clear"


def score_color(score: float) -> str:
    """Tailwind/CSS color class hint for the dashboard."""
    if score >= 75:
        return "red"
    if score >= 50:
        return "orange"
    if score >= 25:
        return "yellow"
    return "green"
