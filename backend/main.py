"""FastAPI backend — orchestrates the full pipeline and exposes REST API."""
import asyncio
import csv
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import settings
from backend.db import database as db
from backend.collectors.serp_collector import collect_serp
from backend.collectors.unlocker_collector import collect_unlocker, fetch_naive, fetch_unblocked
from backend.collectors.scraper_collector import collect_scraper
from backend.extraction.claude_extractor import extract_signals
from backend.scoring.risk_scorer import score_and_persist, score_label, score_color

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    _load_default_vendors()
    yield


app = FastAPI(
    title="Third-Party Risk Radar",
    description="Continuous, cited vendor risk intelligence on Bright Data live web infrastructure",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup helpers ────────────────────────────────────────────────────────

def _load_default_vendors():
    csv_path = Path(settings.vendors_csv)
    if not csv_path.exists():
        return
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.upsert_vendor(
                name=row["name"],
                domain=row["domain"],
                weight=float(row.get("weight", 1.0)),
                stack_role=row.get("stack_role", ""),
            )
    logger.info("Loaded vendors from %s", csv_path)


# ── Background pipeline ────────────────────────────────────────────────────

async def run_vendor_pipeline(vendor_name: str, domain: str) -> dict:
    """Full scan pipeline for one vendor. Returns score + signal count."""
    run_id = db.create_run(vendor_name)
    try:
        # Stage 2: Collection (parallel)
        serp_task = collect_serp(vendor_name, domain)
        scraper_task = collect_scraper(vendor_name, domain)
        serp_items, scraped_pages = await asyncio.gather(serp_task, scraper_task)

        # Fetch top SERP URLs through Web Unlocker for depth
        top_urls = [item["url"] for item in serp_items[:4]]
        unlocker_pages = await collect_unlocker(vendor_name, top_urls)

        all_pages = scraped_pages + unlocker_pages

        # Stage 3: Extraction
        signals = await extract_signals(vendor_name, serp_items, all_pages)

        # Stage 4: Scoring + persist
        score = await score_and_persist(vendor_name, domain, signals, run_id)
        db.complete_run(run_id)

        return {"vendor": vendor_name, "score": score, "signals": len(signals), "run_id": run_id}

    except Exception as exc:
        logger.error("Pipeline error for %s: %s", vendor_name, exc)
        db.complete_run(run_id, status="error")
        raise


# ── Response models ────────────────────────────────────────────────────────

class VendorOut(BaseModel):
    name: str
    domain: str
    weight: float
    stack_role: str
    score: Optional[float] = None
    score_label: Optional[str] = None
    score_color: Optional[str] = None
    signal_count: Optional[int] = None
    last_scanned: Optional[str] = None


class SignalOut(BaseModel):
    id: int
    vendor: str
    category: str
    severity: int
    summary: str
    source_url: str
    date_detected: str
    is_new: int


class ScanResult(BaseModel):
    vendor: str
    score: float
    signals: int
    run_id: int
    message: str = "Scan complete"


class BlockedProof(BaseModel):
    url: str
    naive_status: int
    naive_blocked: bool
    unlocker_status: int
    unlocker_success: bool
    proof: str


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/vendors", response_model=list[VendorOut], tags=["vendors"])
async def list_vendors():
    """Return all vendors with their latest risk scores."""
    vendors = db.get_all_vendors()
    scores = {s["vendor"]: s for s in db.get_all_latest_scores()}
    result = []
    for v in vendors:
        score_row = scores.get(v["name"])
        result.append(VendorOut(
            name=v["name"],
            domain=v["domain"],
            weight=v["weight"],
            stack_role=v["stack_role"] or "",
            score=score_row["score"] if score_row else None,
            score_label=score_label(score_row["score"]) if score_row else None,
            score_color=score_color(score_row["score"]) if score_row else None,
            signal_count=score_row["signal_count"] if score_row else None,
            last_scanned=score_row["computed_at"] if score_row else None,
        ))
    result.sort(key=lambda v: v.score or 0, reverse=True)
    return result


@app.get("/vendors/{vendor_name}", tags=["vendors"])
async def get_vendor(vendor_name: str):
    """Return vendor detail with full signal list."""
    vendor = db.get_vendor(vendor_name)
    if not vendor:
        raise HTTPException(404, f"Vendor '{vendor_name}' not found")

    signals = db.get_latest_signals(vendor_name, limit=50)
    score_row = db.get_latest_score(vendor_name)

    return {
        "vendor": vendor,
        "score": score_row["score"] if score_row else None,
        "score_label": score_label(score_row["score"]) if score_row else None,
        "score_color": score_color(score_row["score"]) if score_row else None,
        "signal_count": score_row["signal_count"] if score_row else 0,
        "last_scanned": score_row["computed_at"] if score_row else None,
        "signals": signals,
    }


@app.post("/vendors/{vendor_name}/scan", response_model=ScanResult, tags=["scan"])
async def scan_vendor(vendor_name: str, background_tasks: BackgroundTasks):
    """
    Trigger a live scan for a vendor.
    Runs the full Bright Data → Claude → Score pipeline.
    """
    vendor = db.get_vendor(vendor_name)
    if not vendor:
        raise HTTPException(404, f"Vendor '{vendor_name}' not found")

    result = await run_vendor_pipeline(vendor["name"], vendor["domain"])
    return ScanResult(**result)


@app.post("/scan/all", tags=["scan"])
async def scan_all_vendors(background_tasks: BackgroundTasks):
    """Trigger a scan for ALL vendors (runs in background)."""
    vendors = db.get_all_vendors()

    async def _run_all():
        for v in vendors:
            try:
                await run_vendor_pipeline(v["name"], v["domain"])
            except Exception as e:
                logger.error("Scan failed for %s: %s", v["name"], e)

    background_tasks.add_task(_run_all)
    return {"message": f"Scan triggered for {len(vendors)} vendors", "vendors": [v["name"] for v in vendors]}


@app.get("/alerts", tags=["alerts"])
async def get_alerts(since: Optional[str] = None):
    """
    Return new risk signals since a given date (YYYY-MM-DD).
    Defaults to the last 7 days.
    """
    if not since:
        from datetime import timedelta
        since = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    signals = db.get_new_signals_since(since)
    return {"since": since, "count": len(signals), "signals": signals}


@app.get("/proof/unblocked", response_model=BlockedProof, tags=["demo"])
async def unblocked_proof(url: str = "https://haveibeenpwned.com/"):
    """
    Side-by-side demo: naive fetch vs Web Unlocker.
    This is the key hackathon differentiator — proves 403→200.
    """
    naive, unlocker = await asyncio.gather(
        fetch_naive(url),
        fetch_unblocked(url, vendor_context="demo"),
    )
    return BlockedProof(
        url=url,
        naive_status=naive["status"],
        naive_blocked=naive["blocked"],
        unlocker_status=unlocker["status"] if unlocker else 0,
        unlocker_success=unlocker is not None,
        proof=(
            "Web Unlocker bypassed bot protection (403→200)"
            if (naive["blocked"] and unlocker)
            else "Direct fetch succeeded (no blocking detected)"
        ),
    )


@app.post("/vendors/import", tags=["vendors"])
async def import_vendors(file: UploadFile = File(...)):
    """Import vendors from an uploaded CSV file (name, domain, weight, stack_role)."""
    content = await file.read()
    reader = csv.DictReader(StringIO(content.decode("utf-8")))
    count = 0
    for row in reader:
        if "name" in row and "domain" in row:
            db.upsert_vendor(
                name=row["name"],
                domain=row["domain"],
                weight=float(row.get("weight", 1.0)),
                stack_role=row.get("stack_role", ""),
            )
            count += 1
    return {"imported": count}


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
