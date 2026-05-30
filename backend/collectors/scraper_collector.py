"""Bright Data Web Scraper API — structured pulls from fixed, known sources."""
import asyncio
import logging
from typing import Optional

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

BRIGHTDATA_API = "https://api.brightdata.com/request"

# Structured fixed sources — vendor status pages, trust centers, CVE feeds
SOURCE_PATTERNS = {
    "status_page": "https://{domain}/status",
    "trust_center": "https://trust.{domain}",
    "cve_search": "https://www.cvedetails.com/google-search-results.php?q={vendor}",
    "crunchbase": "https://www.crunchbase.com/organization/{vendor_slug}",
}


def _vendor_slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace(".", "")


async def _scrape_url(client: httpx.AsyncClient, url: str, vendor: str) -> Optional[dict]:
    """Single Web Scraper API / Web Unlocker call returning structured text."""
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
        resp = await client.post(BRIGHTDATA_API, json=payload, headers=headers, timeout=40)
        resp.raise_for_status()
        return {"url": url, "html": resp.text, "vendor": vendor}
    except Exception as exc:
        logger.debug("Scraper skip %s: %s", url, exc)
        return None


async def collect_scraper(vendor_name: str, domain: str) -> list[dict]:
    """
    Fetch structured pages for a vendor: status page, trust center, CVE listings.
    Returns list of {url, html, vendor} for downstream extraction.
    """
    slug = _vendor_slug(vendor_name)
    urls = [
        SOURCE_PATTERNS["status_page"].format(domain=domain),
        SOURCE_PATTERNS["trust_center"].format(domain=domain),
        SOURCE_PATTERNS["cve_search"].format(vendor=vendor_name),
        SOURCE_PATTERNS["crunchbase"].format(vendor_slug=slug),
    ]

    async with httpx.AsyncClient(timeout=50) as client:
        tasks = [_scrape_url(client, u, vendor_name) for u in urls]
        results = await asyncio.gather(*tasks)

    collected = [r for r in results if r]
    logger.info("Scraper collected %d/%d pages for %s", len(collected), len(urls), vendor_name)
    return collected
