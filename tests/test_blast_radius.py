"""Tests for the Blast Radius cross-vendor cascade engine."""
from datetime import datetime, timedelta

from backend.analysis.blast_radius import detect_blast_radius


def _recent(days_ago=2):
    return (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def _sig(vendor, summary, severity=4, category="Security", date=None):
    return {
        "vendor": vendor,
        "category": category,
        "severity": severity,
        "summary": summary,
        "source_url": f"https://example.com/{vendor.lower()}",
        "date_detected": date or _recent(),
    }


# ── cascade detection ───────────────────────────────────────────────────────

def test_shared_campaign_links_vendors_into_one_incident():
    signals = [
        _sig("Salesforce", "Salesloft Drift OAuth token cascade reached connected orgs"),
        _sig("GitHub", "Salesloft attack chain traced back to GitHub repository tokens"),
        _sig("CrowdStrike", "Named among firms affected by the Salesloft Drift OAuth cascade"),
        _sig("Slack", "Slack OAuth integration tokens targeted in the Salesloft cascade"),
    ]
    res = detect_blast_radius(signals, window_days=30)
    assert res["incident_count"] == 1
    inc = res["incidents"][0]
    assert set(inc["affected_vendors"]) == {"Salesforce", "GitHub", "CrowdStrike", "Slack"}
    assert inc["verdict"] == "INVESTIGATE"
    assert "salesloft" in inc["link_terms"]
    assert len(inc["citations"]) == 4


def test_unrelated_vendors_do_not_cluster():
    signals = [
        _sig("AWS", "us-east-1 EC2 degradation affecting availability"),
        _sig("Workday", "Researchers disclose an isolated PII endpoint issue"),
    ]
    res = detect_blast_radius(signals, window_days=30)
    # No shared connection term → no cascade incidents, both standalone.
    assert res["incident_count"] == 0
    assert len(res["standalone"]) == 2


def test_cross_vendor_mention_creates_a_link():
    # Cloudflare's signal mentions Okta → they are connected.
    signals = [
        _sig("Cloudflare", "Atlassian instance compromised via Okta stolen credentials"),
        _sig("Okta", "Okta credentials abused to pivot into Cloudflare Atlassian"),
    ]
    res = detect_blast_radius(signals, window_days=30)
    assert res["incident_count"] == 1
    assert set(res["incidents"][0]["affected_vendors"]) == {"Cloudflare", "Okta"}


# ── verdict logic ───────────────────────────────────────────────────────────

def test_high_severity_single_vendor_is_investigate():
    res = detect_blast_radius([_sig("Okta", "Critical source code theft", severity=5)], 30)
    assert res["standalone"][0]["verdict"] == "INVESTIGATE"


def test_moderate_single_vendor_is_monitor():
    res = detect_blast_radius([_sig("Workday", "Moderate API issue reported", severity=3)], 30)
    assert res["standalone"][0]["verdict"] == "MONITOR"


def test_low_severity_is_no_action():
    res = detect_blast_radius([_sig("AWS", "Brief minor latency blip", severity=2)], 30)
    assert res["standalone"][0]["verdict"] == "NO_ACTION"


# ── filtering ───────────────────────────────────────────────────────────────

def test_non_security_signals_ignored():
    res = detect_blast_radius([_sig("Workday", "GDPR fine levied", severity=4, category="Regulatory")], 30)
    assert res["incident_count"] == 0
    assert res["standalone"] == []


def test_stale_signals_excluded_by_window():
    old = (datetime.utcnow() - timedelta(days=120)).strftime("%Y-%m-%d")
    res = detect_blast_radius([_sig("Okta", "Old breach", severity=5, date=old)], window_days=30)
    assert res["standalone"] == []
