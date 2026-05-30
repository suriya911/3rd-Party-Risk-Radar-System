"""
Blast Radius — cross-vendor cascade exposure detection.

The unsolved part of third-party risk: a breach in ONE vendor cascades to the
others you're connected to (shared OAuth token, shared identity provider,
shared attacker campaign). This module looks at recent SECURITY signals across
all vendors, finds the incidents that link two or more of them, and emits an
action verdict per incident:

    INVESTIGATE  — a live cross-vendor cascade or a high-severity fresh hit
    MONITOR      — a moderate, single-vendor security issue worth watching
    NO_ACTION    — low severity / stale; no exposure action needed

Connections are discovered automatically from the signal text: shared salient
entities (capitalized names like "Salesloft", "Drift", "Okta") and known
attack-mechanism keywords (OAuth, CVE, ransomware, ...). A term that appears in
signals belonging to two *different* vendors is a connection between them.
"""
import re
from datetime import datetime, timedelta
from typing import Optional

# Distinctive attack-mechanism keywords that imply a shared vector. Deliberately
# excludes near-universal words (breach, credentials, vulnerability, token) which
# appear in almost every security signal and would create false connections.
MECHANISM_TERMS = {
    "oauth", "cve", "ransomware", "bgp", "bsod", "phishing",
    "backdoor", "exfiltration",
}

# Common capitalized words that are NOT useful connection entities.
STOPWORDS = {
    "the", "this", "that", "a", "an", "and", "or", "of", "to", "in", "on",
    "for", "with", "via", "by", "from", "at", "as", "is", "are", "was", "were",
    "third", "major", "two", "years", "new", "us", "eu", "uk", "api", "apis",
    "it", "ai", "data", "security", "customer", "customers", "company",
    "companies", "enterprise", "internal", "global", "multiple", "source",
    "code", "report", "study", "survey", "named", "recent", "market",
    "analysis", "concerns", "potential", "questions", "serious", "raises",
}

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9.\-]{2,}")


def _link_terms(summary: str, own_vendor: str) -> set[str]:
    """Extract connection terms from one signal: salient capitalized entities
    plus mechanism keywords. The signal's own vendor name is excluded so we
    only capture links to *other* things."""
    own = own_vendor.lower()
    terms: set[str] = set()
    for raw in _TOKEN_RE.findall(summary):
        # Consider the whole token AND its hyphen-separated parts, so a compound
        # campaign name like "Salesloft-Drift" also yields "salesloft" + "drift"
        # and connects to vendors that mention only one part.
        parts = [raw] + (raw.split("-") if "-" in raw else [])
        for p in parts:
            low = p.lower().strip(".-")
            if len(low) < 3 or low == own:
                continue
            if low in MECHANISM_TERMS:
                terms.add(low)
            elif p[:1].isupper() and low not in STOPWORDS:
                # A capitalized, non-trivial entity (Salesloft, Drift, GitHub, ...)
                terms.add(low)
    return terms


def _parse_date(d: str) -> Optional[datetime]:
    try:
        return datetime.strptime(d, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _verdict(vendor_count: int, max_sev: int, days_old: int) -> tuple[str, str]:
    """Return (verdict, one-line recommendation)."""
    fresh = days_old <= 14
    if vendor_count >= 2 and fresh:
        return (
            "INVESTIGATE",
            f"Cross-vendor cascade touching {vendor_count} of your vendors — "
            "rotate shared tokens/credentials and audit the integrations now.",
        )
    if max_sev >= 4 and fresh:
        return (
            "INVESTIGATE",
            "High-severity security incident detected in the last 14 days — "
            "confirm blast radius and your exposure immediately.",
        )
    if max_sev >= 3:
        return ("MONITOR", "Moderate security issue — watch for escalation or new connections.")
    return ("NO_ACTION", "Low severity or stale — no exposure action needed right now.")


def _title(link_terms: list[str], vendors: list[str]) -> str:
    """Human-readable incident title from its strongest connection terms."""
    # Prefer the most distinctive proper-noun campaign term; fall back to vendors.
    salient = sorted([t for t in link_terms if t not in MECHANISM_TERMS], key=len, reverse=True)
    if salient:
        label = salient[0].replace("-", " ").title()
        return f"{label} incident"
    return f"Security incident affecting {', '.join(vendors[:3])}"


def detect_blast_radius(signals: list[dict], window_days: int = 30) -> dict:
    """
    Build the cascade view from a flat list of signal dicts (each with
    vendor, category, severity, summary, source_url, date_detected).

    Returns {generated_at, window_days, incidents:[...], standalone:[...]}.
    `incidents` are multi-signal clusters (cascades surface here); `standalone`
    are single recent security issues that still warrant a verdict.
    """
    today = datetime.utcnow()
    cutoff = today - timedelta(days=window_days)

    # Keep recent security signals only.
    recent = []
    for s in signals:
        if str(s.get("category", "")).lower() != "security":
            continue
        d = _parse_date(s.get("date_detected", ""))
        if d is None or d < cutoff:
            continue
        recent.append({**s, "_terms": _link_terms(s.get("summary", ""), s.get("vendor", "")), "_date": d})

    # Inverted index: term -> set of vendors mentioning it. A term shared by two
    # different vendors is a real connection.
    term_vendors: dict[str, set[str]] = {}
    for s in recent:
        for t in s["_terms"]:
            term_vendors.setdefault(t, set()).add(s["vendor"])
    connecting_terms = {t for t, vs in term_vendors.items() if len(vs) >= 2}

    # Union-find over signals that share any connecting term.
    parent: dict[int, int] = {i: i for i in range(len(recent))}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int):
        parent[find(a)] = find(b)

    # Link signals that share a connecting term.
    by_term: dict[str, list[int]] = {}
    for i, s in enumerate(recent):
        for t in s["_terms"] & connecting_terms:
            by_term.setdefault(t, []).append(i)
    for idxs in by_term.values():
        for j in range(1, len(idxs)):
            union(idxs[0], idxs[j])

    # Gather clusters.
    clusters: dict[int, list[int]] = {}
    for i in range(len(recent)):
        clusters.setdefault(find(i), []).append(i)

    incidents, standalone = [], []
    for members_idx in clusters.values():
        members = [recent[i] for i in members_idx]
        vendors = sorted({m["vendor"] for m in members})
        max_sev = max((int(m.get("severity", 0)) for m in members), default=0)
        dates = [m["_date"] for m in members]
        last_seen = max(dates)
        days_old = (today - last_seen).days
        verdict, rec = _verdict(len(vendors), max_sev, days_old)
        # Connection terms actually shared across vendors in this cluster.
        shared = sorted(
            {t for m in members for t in m["_terms"] & connecting_terms}
        )
        entry = {
            "title": _title(shared, vendors),
            "affected_vendors": vendors,
            "vendor_count": len(vendors),
            "max_severity": max_sev,
            "link_terms": shared,
            "first_seen": min(dates).strftime("%Y-%m-%d"),
            "last_seen": last_seen.strftime("%Y-%m-%d"),
            "verdict": verdict,
            "recommendation": rec,
            "members": sorted(
                [
                    {
                        "vendor": m["vendor"],
                        "severity": int(m.get("severity", 0)),
                        "summary": m.get("summary", ""),
                        "source_url": m.get("source_url", ""),
                        "date_detected": m.get("date_detected", ""),
                    }
                    for m in members
                ],
                key=lambda x: x["severity"],
                reverse=True,
            ),
            "citations": sorted({m.get("source_url", "") for m in members if m.get("source_url")}),
        }
        if len(vendors) >= 2:
            incidents.append(entry)
        else:
            standalone.append(entry)

    # Cascades first, then by severity and breadth.
    incidents.sort(key=lambda e: (e["vendor_count"], e["max_severity"]), reverse=True)
    standalone.sort(key=lambda e: (e["max_severity"], e["last_seen"]), reverse=True)

    return {
        "generated_at": today.isoformat(),
        "window_days": window_days,
        "incident_count": len(incidents),
        "incidents": incidents,
        "standalone": standalone,
    }
