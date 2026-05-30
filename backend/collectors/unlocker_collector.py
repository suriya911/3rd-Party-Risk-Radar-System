"""Bright Data Web Unlocker — fetches bot-walled pages that naive requests cannot reach."""
import logging
from typing import Optional

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

BRIGHTDATA_API = "https://api.brightdata.com/request"

# Fixed sources that are typically bot-protected
FIXED_SOURCES = [
    "https://haveibeenpwned.com/",
    "https://www.sec.gov/cgi-bin/browse-edgar",
    "https://pacer.uscourts.gov/",
]


async def fetch_unblocked(url: str, vendor_context: str = "") -> Optional[dict]:
    """
    Fetch a URL through Bright Data Web Unlocker.
    Returns {"url": str, "html": str, "status": int} or None on failure.

    Demo note: This call proves 403→200 — the key hackathon differentiator.
    """
    headers = {
        "Authorization": f"Bearer {settings.brightdata_api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "zone": settings.brightdata_unlocker_zone,
        "url": url,
        "format": "raw",
    }

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(BRIGHTDATA_API, json=payload, headers=headers)
            logger.info(
                "Web Unlocker %s → HTTP %d (vendor: %s)", url, resp.status_code, vendor_context
            )
            resp.raise_for_status()
            return {"url": url, "html": resp.text, "status": resp.status_code}
    except Exception as exc:
        logger.warning("Web Unlocker failed for %s: %s", url, exc)
        return None


async def fetch_naive(url: str) -> dict:
    """
    Naive direct fetch (no proxy) — used for the side-by-side 403-vs-200 demo proof point.
    Returns {"url": str, "status": int, "blocked": bool}.
    """
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            blocked = resp.status_code in (403, 429, 503) or "captcha" in resp.text.lower()
            return {"url": url, "status": resp.status_code, "blocked": blocked}
    except Exception as exc:
        return {"url": url, "status": 0, "blocked": True, "error": str(exc)}


async def collect_unlocker(vendor_name: str, urls: list[str]) -> list[dict]:
    """
    Fetch a list of URLs through the Web Unlocker and return raw HTML items.
    Each item: {url, html, status, vendor}.
    """
    import asyncio
    tasks = [fetch_unblocked(u, vendor_context=vendor_name) for u in urls]
    results = await asyncio.gather(*tasks)
    collected = []
    for result in results:
        if result:
            result["vendor"] = vendor_name
            collected.append(result)
    logger.info("Web Unlocker fetched %d/%d pages for %s", len(collected), len(urls), vendor_name)
    return collected
