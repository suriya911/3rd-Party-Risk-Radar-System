"""Claude API extraction layer — converts raw web content into structured risk signals."""
import json
import logging
from datetime import datetime
from typing import Optional

from openai import OpenAI
from bs4 import BeautifulSoup

from backend.config import settings

logger = logging.getLogger(__name__)


def _get_client() -> OpenAI:
    """Build the LLM client lazily — avoids an import-time crash when no key is
    set (seeded demo mode). Targets any OpenAI-compatible endpoint (AI/ML API)."""
    return OpenAI(api_key=settings.effective_llm_key, base_url=settings.llm_base_url)

SIGNAL_SCHEMA = {
    "type": "object",
    "properties": {
        "signals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "vendor":        {"type": "string"},
                    "category":      {"type": "string", "enum": ["Security", "Financial", "Operational", "Regulatory", "Reputational"]},
                    "severity":      {"type": "integer", "minimum": 1, "maximum": 5},
                    "summary":       {"type": "string"},
                    "source_url":    {"type": "string"},
                    "date_detected": {"type": "string"},
                },
                "required": ["vendor", "category", "severity", "summary", "source_url", "date_detected"],
            },
        }
    },
    "required": ["signals"],
}

EXTRACTION_PROMPT = """You are a third-party risk intelligence analyst. Extract risk signals from the raw web content below.

Rules:
1. ONLY extract signals that are explicitly mentioned in the content — no inference, no invented facts.
2. EVERY signal MUST have a real source URL from the content. If no URL exists, drop the signal.
3. Severity scale: 1=low/informational, 2=minor, 3=moderate, 4=high, 5=critical.
4. Categories: Security (breach/CVE/attack), Financial (bankruptcy/loss), Operational (outage/downtime), Regulatory (fine/lawsuit/compliance), Reputational (scandal/leadership).
5. Date format: YYYY-MM-DD. Use today ({today}) if no date is found.
6. Be conservative — a vendor with no signals is fine. Do NOT invent risk.

Vendor being assessed: {vendor}

Content sources:
{content}

Return a JSON object matching this schema:
{schema}
"""


def _strip_html(html: str, max_chars: int = 6000) -> str:
    """Extract readable text from HTML, trimmed to max_chars."""
    try:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:max_chars]
    except Exception:
        return html[:max_chars]


def _format_serp_items(items: list[dict]) -> str:
    """Format SERP results into readable content blocks."""
    blocks = []
    for item in items[:15]:
        url = item.get("url", "")
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        if url:
            blocks.append(f"SOURCE: {url}\nTITLE: {title}\nSNIPPET: {snippet}\n")
    return "\n".join(blocks)


def _format_html_pages(pages: list[dict]) -> str:
    """Format fetched HTML pages into readable content blocks."""
    blocks = []
    for page in pages[:4]:
        url = page.get("url", "")
        html = page.get("html", "")
        text = _strip_html(html)
        if url and text:
            blocks.append(f"SOURCE: {url}\n{text}\n")
    return "\n".join(blocks)


def _validate_signal(signal: dict, vendor: str) -> Optional[dict]:
    """Validate and normalise one extracted signal. Returns None if invalid."""
    required = ["vendor", "category", "severity", "summary", "source_url", "date_detected"]
    for field in required:
        if not signal.get(field):
            return None

    if not signal["source_url"].startswith("http"):
        return None

    valid_categories = {"Security", "Financial", "Operational", "Regulatory", "Reputational"}
    if signal["category"] not in valid_categories:
        signal["category"] = "Security"

    try:
        signal["severity"] = max(1, min(5, int(signal["severity"])))
    except (ValueError, TypeError):
        return None

    signal["vendor"] = vendor
    return signal


async def extract_signals(
    vendor_name: str,
    serp_items: list[dict],
    html_pages: list[dict],
) -> list[dict]:
    """
    Call Claude to extract risk signals from collected web content.
    Returns a list of validated signal dicts.
    """
    content_blocks = []
    if serp_items:
        content_blocks.append("=== SEARCH RESULTS ===\n" + _format_serp_items(serp_items))
    if html_pages:
        content_blocks.append("=== FETCHED PAGES ===\n" + _format_html_pages(html_pages))

    if not content_blocks:
        return []

    content = "\n\n".join(content_blocks)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    prompt = EXTRACTION_PROMPT.format(
        vendor=vendor_name,
        today=today,
        content=content,
        schema=json.dumps(SIGNAL_SCHEMA, indent=2),
    )

    try:
        client = _get_client()
        message = client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (message.choices[0].message.content or "").strip()

        # Extract JSON from response (models sometimes wrap in ```json)
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw)
        raw_signals = parsed.get("signals", [])

        validated = []
        for s in raw_signals:
            valid = _validate_signal(s, vendor_name)
            if valid:
                valid["date_detected"] = today if not valid.get("date_detected") else valid["date_detected"]
                validated.append(valid)

        logger.info("LLM extracted %d valid signals for %s", len(validated), vendor_name)
        return validated

    except json.JSONDecodeError as e:
        logger.error("LLM JSON parse error for %s: %s", vendor_name, e)
        return []
    except Exception as e:
        logger.error("LLM API error for %s: %s", vendor_name, e)
        return []
