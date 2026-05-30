# Project Status — Third-Party Risk Radar

**Date:** 2026-05-30  
**Hackathon:** Web Data UNLOCKED — Enterprise AI, Bright Data (San Francisco)

---

## What's Done

### Backend — fully implemented

| File | Status | Notes |
|---|---|---|
| `backend/config.py` | Done | Pydantic settings, reads `.env` |
| `backend/db/database.py` | Done | SQLite schema, all CRUD ops (vendors, signals, runs, scores) |
| `backend/collectors/serp_collector.py` | Done | Bright Data SERP API, 6 parallel news queries per vendor |
| `backend/collectors/unlocker_collector.py` | Done | Web Unlocker fetch + naive fetch side-by-side for 403→200 proof |
| `backend/collectors/scraper_collector.py` | Done | Structured pulls from status pages, CVE feeds, trust centers |
| `backend/extraction/claude_extractor.py` | Done | Claude extraction with locked JSON schema; drops signals with no URL |
| `backend/scoring/risk_scorer.py` | Done | `score = sum(severity × decay) × weight`, delta flagging |
| `backend/main.py` | Done | FastAPI: 7 endpoints covering vendors, scan, alerts, proof, import |
| `backend/mcp_server/server.py` | Done | MCP server with 3 tools: `get_vendor_risk`, `list_high_risk_vendors`, `whats_new_since` |

### Frontend — fully implemented

| File | Status | Notes |
|---|---|---|
| `frontend/src/pages/Dashboard.tsx` | Done | Stat cards, vendor table, radar chart, alert feed, proof panel |
| `frontend/src/pages/VendorPage.tsx` | Done | Drill-down: score, signals, category filter, live scan button |
| `frontend/src/components/VendorTable.tsx` | Done | Sortable table, color-coded scores, per-vendor scan trigger |
| `frontend/src/components/AlertFeed.tsx` | Done | Date-filtered new signal feed with source links |
| `frontend/src/components/UnblockedProofPanel.tsx` | Done | 403 vs 200 side-by-side UI for demo unblockability proof |
| `frontend/src/components/RiskBadge.tsx` | Done | Score badge + bar (Critical/High/Medium/Low/Clear) |
| `frontend/src/components/CategoryBadge.tsx` | Done | Color-coded category tags |
| `frontend/src/components/SeverityBadge.tsx` | Done | Severity 1–5 badges |
| `frontend/src/api/client.ts` | Done | Typed API client for all backend endpoints |

### Config & tooling

| File | Status | Notes |
|---|---|---|
| `vendors.csv` | Done | 10 demo vendors (AWS, Okta, Snowflake, Salesforce, etc.) |
| `requirements.txt` | Done | All Python deps pinned |
| `.env.example` | Done | Template for all API keys and config |
| `seed_demo.py` | Done | Seeds realistic incidents with real source URLs; no API keys needed |
| `run.py` | Done | `python run.py` starts FastAPI on :8000 |
| `claude_desktop_config.json` | Done | MCP config snippet for Claude Desktop |
| `README.md` | Done | Full setup guide, API reference, score formula |

### Verified working (no API keys)

- SQLite init, vendor load, signal insert, score compute — all passing
- TypeScript: zero type errors (`tsc --noEmit` clean)
- Demo seed produces dramatic, realistic scores:
  - Okta 94.8 Critical, Salesforce 90.8 Critical, Snowflake 76.0 Critical
  - CrowdStrike 69.1 High, Cloudflare 57.0 High, GitHub 52.4 High
  - Datadog 0.0 Clear (proves engine won't invent risk)

---

## What Still Needs to Be Done

### Must-have before demo

- [ ] **Add API keys to `.env`** — `BRIGHTDATA_API_TOKEN`, `BRIGHTDATA_USERNAME`, `BRIGHTDATA_PASSWORD`, `ANTHROPIC_API_KEY`. Nothing works without these.
- [ ] **End-to-end live scan test** — run `POST /vendors/Okta/scan` with real credentials and verify signals come back from the live web.
- [ ] **Verify SERP zone name** — confirm your Bright Data zone is called `serp` (not `serp_api` or similar). Update `.env` `BRIGHTDATA_SERP_ZONE` if different.
- [ ] **Verify Web Unlocker zone name** — confirm the zone name in your Bright Data account matches `web_unlocker1`. Update `.env` `BRIGHTDATA_UNLOCKER_ZONE`.
- [ ] **Test the 403→200 proof** — hit `GET /proof/unblocked?url=https://haveibeenpwned.com/` and confirm `naive_blocked=true`, `unlocker_success=true`. This is the single most persuasive demo moment.
- [ ] **Connect Claude Desktop to MCP server** — copy the config snippet from `claude_desktop_config.json`, set the absolute path, restart Claude Desktop. Ask: *"Which vendors had a new security issue this week?"*

### Should-have before demo

- [ ] **Live scan end-to-end smoke test for all 10 vendors** — trigger `/scan/all` and monitor logs. Make sure no vendor crashes the pipeline.
- [ ] **Error handling for quota exhaustion** — Bright Data gives $250 credits; add a guard in `main.py` that catches `httpx.HTTPStatusError` 429/402 and surfaces a clear message rather than a 500.
- [ ] **Loading/streaming UX for scan** — the `POST /vendors/{name}/scan` call can take 30–60 seconds (Bright Data + Claude). Consider a polling endpoint or SSE stream so the UI shows progress instead of a spinner that looks frozen.
- [ ] **Run the frontend for real** — `cd frontend && npm run dev`, open http://localhost:5173, verify the dashboard renders with seeded data.
- [ ] **Favicon/brand polish** — add a `radar.svg` icon to `frontend/public/` (referenced in `index.html`). Small detail but visible.

### Nice-to-have (if time permits)

- [ ] **Docker Compose** — single `docker compose up` to start backend + frontend. Reduces demo setup risk on unfamiliar hardware.
- [ ] **`POST /scan/all` real-time progress** — WebSocket or SSE endpoint so the dashboard shows which vendor is currently being scanned.
- [ ] **Score history chart on VendorPage** — Recharts line chart showing score over time across runs. Data is already in SQLite (`vendor_scores` table).
- [ ] **CSV import UI** — the `POST /vendors/import` endpoint exists but there's no upload button in the dashboard. Easy to add.
- [ ] **Risk score trend arrow** — compare latest score to the previous run and show ↑/↓ trend indicator in the vendor table.
- [ ] **Slack/email alert webhook** — on delta signal detection, POST to a webhook. Completes the "monitoring system" arrow in the architecture diagram.

### Known limitations / tech debt

- `score_and_persist` in `risk_scorer.py` is `async` but calls synchronous SQLite functions via `database.py` (which uses the synchronous `sqlite3` driver). This works fine single-threaded but will block the event loop under concurrent scans. Replace `sqlite3` with `aiosqlite` calls if concurrent scanning becomes a bottleneck.
- `GET /scan/all` runs vendors sequentially in a background task. Could be parallelised with `asyncio.gather` — fine for 10 vendors, worth fixing for 100+.
- Claude extraction prompt currently sends up to ~24KB of text (6 SERP items × 6 queries + 4 pages × 6,000 chars). If context overflows, add a `max_tokens` guard and chunk the input.
- No authentication on the API. Fine for a hackathon demo; add an API key header before any real deployment.

---

## How to Run

```bash
# 1. Set credentials
cp .env.example .env
# edit .env — add BRIGHTDATA_API_TOKEN and ANTHROPIC_API_KEY

# 2. Backend (with seeded demo data)
pip install -r requirements.txt
python seed_demo.py     # loads demo signals, no API keys needed
python run.py           # http://localhost:8000

# 3. Frontend
cd frontend
npm install
npm run dev             # http://localhost:5173

# 4. MCP (Claude Desktop)
python -m backend.mcp_server.server
```

## File Count

- Python backend: 11 files
- React/TypeScript frontend: 10 files
- Config/tooling: 8 files
- **Total: 29 files**, zero placeholder stubs
