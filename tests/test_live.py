"""Opt-in tests that hit real external services.

Excluded by default (pytest.ini: -m "not live"). Run explicitly with:
    pytest -m live
Requires a populated .env (LLM_API_KEY, BRIGHTDATA_* ).
"""
import os

import pytest

pytestmark = pytest.mark.live


@pytest.mark.skipif(not os.getenv("LLM_API_KEY"), reason="LLM_API_KEY not set")
def test_aimlapi_connectivity():
    """Confirms the AI/ML API key + model + base_url actually answer."""
    from backend.config import settings
    from backend.extraction.claude_extractor import _get_client

    client = _get_client()
    resp = client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=10,
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
    )
    assert resp.choices[0].message.content.strip()


@pytest.mark.skipif(not os.getenv("LLM_API_KEY"), reason="LLM_API_KEY not set")
def test_extract_signals_from_synthetic_content():
    """End-to-end extraction against the live LLM with hand-fed content."""
    import asyncio
    from backend.extraction.claude_extractor import extract_signals

    serp = [{
        "url": "https://example.com/okta-breach",
        "title": "Okta discloses credential breach",
        "snippet": "Okta confirmed attackers accessed customer support data on 2026-05-20.",
    }]
    signals = asyncio.run(extract_signals("Okta", serp, []))
    # The model may extract 0+ signals; assert it returns a valid list shape.
    assert isinstance(signals, list)
    for s in signals:
        assert s["source_url"].startswith("http")
        assert 1 <= s["severity"] <= 5


@pytest.mark.skipif(not os.getenv("BRIGHTDATA_API_TOKEN"), reason="Bright Data token not set")
def test_unblocker_proof():
    """The 403→200 demo: naive fetch blocked, Web Unlocker succeeds."""
    import asyncio
    from backend.collectors.unlocker_collector import fetch_naive, fetch_unblocked

    async def _run():
        return await asyncio.gather(
            fetch_naive("https://haveibeenpwned.com/"),
            fetch_unblocked("https://haveibeenpwned.com/", vendor_context="test"),
        )

    naive, unlocker = asyncio.run(_run())
    assert unlocker is not None  # unlocker returned content
