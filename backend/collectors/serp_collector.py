"""Bright Data SERP API collector — discovery and freshness engine."""
import asyncio
import logging
from typing import Optional

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

BRIGHTDATA_API = "https://api.brightdata.com/request"

# Search query templates per risk category
QUERY_TEMPLATES = [
    '"{vendor}" data breach',
    '"{vendor}" security incident',
    '"{vendor}" lawsuit OR regulatory',
    '"{vendor}" CVE OR vulnerability',
    '"{vendor}" acquisition OR layoffs OR bankrupt',
    '"{vendor}" outage OR downtime site:status.{domain}',
]


async def _serp_request(client: httpx.AsyncClient, url: str) -> Optional[dict]:
    """Single SERP API call returning parsed JSON result."""
    headers = {
        "Authorization": f"Bearer {settings.brightdata_api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "zone": settings.brightdata_serp_zone,
        "url": url,
        "format": "raw",  # body is the parsed SERP JSON (via brd_json=1 in the URL)
    }
    try:
        resp = await client.post(BRIGHTDATA_API, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("SERP request failed for %s: %s", url, exc)
        return None


def _build_google_news_url(query: str) -> str:
    from urllib.parse import urlencode
    # brd_json=1 → Bright Data returns parsed SERP JSON instead of raw HTML.
    params = urlencode({"q": query, "tbm": "nws", "tbs": "qdr:m", "brd_json": "1"})
    return f"https://www.google.com/search?{params}"


def _extract_organic_results(serp_data: dict) -> list[dict]:
    """Pull title, url, snippet from SERP JSON response."""
    results = []
    # News queries (tbm=nws) return a "news" array; web queries return "organic".
    organic = (
        serp_data.get("organic")
        or serp_data.get("news")
        or serp_data.get("results", [])
    )
    for item in organic[:8]:
        url = item.get("url") or item.get("link", "")
        title = item.get("title", "")
        snippet = item.get("description") or item.get("snippet", "")
        if url and title:
            results.append({"title": title, "url": url, "snippet": snippet})
    return results


async def collect_serp(vendor_name: str, domain: str) -> list[dict]:
    """
    Run parallel SERP queries for a vendor, return a flat list of
    {title, url, snippet, query} items with real source URLs.
    """
    queries = [t.replace("{vendor}", vendor_name).replace("{domain}", domain)
               for t in QUERY_TEMPLATES]
    urls = [_build_google_news_url(q) for q in queries]

    collected: list[dict] = []

    async with httpx.AsyncClient(verify=True) as client:
        tasks = [_serp_request(client, u) for u in urls]
        results = await asyncio.gather(*tasks)

    for query, data in zip(queries, results):
        if data:
            items = _extract_organic_results(data)
            for item in items:
                item["query"] = query
                item["vendor"] = vendor_name
            collected.extend(items)

    logger.info("SERP collected %d results for %s", len(collected), vendor_name)
    return collected
