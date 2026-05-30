"""Unit tests for the extraction layer's pure helpers (no API calls)."""
from backend.extraction import claude_extractor as ext


# ── _strip_html ─────────────────────────────────────────────────────────────

def test_strip_html_removes_scripts_and_tags():
    html = "<html><body><script>alert(1)</script><p>Real breach text</p></body></html>"
    text = ext._strip_html(html)
    assert "Real breach text" in text
    assert "alert" not in text


def test_strip_html_truncates():
    html = "<p>" + ("x" * 10000) + "</p>"
    assert len(ext._strip_html(html, max_chars=500)) <= 500


# ── _validate_signal ────────────────────────────────────────────────────────

def _base():
    return {
        "vendor": "Okta",
        "category": "Security",
        "severity": 4,
        "summary": "Credential breach disclosed",
        "source_url": "https://example.com/x",
        "date_detected": "2026-05-25",
    }


def test_valid_signal_passes():
    assert ext._validate_signal(_base(), "Okta") is not None


def test_missing_field_rejected():
    s = _base()
    del s["summary"]
    assert ext._validate_signal(s, "Okta") is None


def test_non_http_url_rejected():
    s = _base()
    s["source_url"] = "not-a-url"
    assert ext._validate_signal(s, "Okta") is None


def test_bad_category_defaults_to_security():
    s = _base()
    s["category"] = "Aliens"
    assert ext._validate_signal(s, "Okta")["category"] == "Security"


def test_high_severity_clamped_to_five():
    s = _base()
    s["severity"] = 99
    assert ext._validate_signal(s, "Okta")["severity"] == 5


def test_zero_severity_rejected():
    # severity 0 is falsy → treated as a missing field and dropped (defensive).
    s = _base()
    s["severity"] = 0
    assert ext._validate_signal(s, "Okta") is None


def test_vendor_is_overridden_with_target():
    s = _base()
    s["vendor"] = "WrongName"
    assert ext._validate_signal(s, "Okta")["vendor"] == "Okta"
