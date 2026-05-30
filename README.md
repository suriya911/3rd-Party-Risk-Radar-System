---
title: Third-Party Risk Radar
emoji: 📡
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Third-Party Risk Radar

**Continuous, cited vendor risk intelligence — built on Bright Data live web infrastructure**

> Hackathon: Web Data UNLOCKED — Enterprise AI, Bright Data (San Francisco)

---

## What it does

Enterprises learn their vendors are compromised from the news. **We learn first.**

The system continuously collects, extracts, scores, and alerts on third-party vendor risk signals using:
- **Bright Data SERP API** — discovery and freshness (live Google News queries)
- **Bright Data Web Unlocker** — bypasses bot-protected breach trackers, regulatory portals, status pages
- **Bright Data Web Scraper API** — structured pulls from trust centers, CVE feeds, status pages
- **Claude API** — strict JSON extraction with no invented facts, every signal must have a source URL
- **SQLite** — versioned run snapshots with delta alerting (only new signals surface)
- **MCP Server** — Claude can query risk data live with citations via tool calls

## Architecture

```
vendors.csv → SERP API + Web Unlocker + Scraper API → Claude extraction → SQLite + scoring → Dashboard + MCP
```

Five layers:
1. **Input** — CSV of vendors (name, domain, criticality weight)
2. **Collection** — Async parallel Bright Data collectors per vendor
3. **Extraction** — Claude with locked JSON schema, no invented facts
4. **Scoring + State** — `score = sum(severity × recency_decay) × weight`, 0-100, delta alerts
5. **Interface** — React dashboard + MCP server for agent-native queries

## Demo Proof Points

| Proof | What it shows |
|---|---|
| **Freshness** | Click vendor → live scan → signals stream in with today's date and clickable sources |
| **Unblockability** | Side-by-side: naive fetch 403, Web Unlocker 200 — infrastructure is load-bearing |
| **Auditability** | Every signal has a real, clickable source URL — judges can verify |
| **Agent-native** | Claude + MCP answers "What's new this week?" with citations live |

## Quick Start

### 1. Environment

```bash
cp .env.example .env
# Fill in BRIGHTDATA_API_TOKEN, ANTHROPIC_API_KEY
```

### 2. Backend

```bash
pip install -r requirements.txt
python seed_demo.py        # seed demo data (no API keys needed)
python run.py              # FastAPI on http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                # React on http://localhost:5173
```

### 4. MCP Server (Claude Desktop)

```bash
python -m backend.mcp_server.server
```

Add to your Claude Desktop `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "third-party-risk-radar": {
      "command": "python",
      "args": ["-m", "backend.mcp_server.server"],
      "cwd": "/path/to/3rd-Party-Risk-Radar-System"
    }
  }
}
```

Then ask Claude: *"Which vendors had a new security issue this week, and should I worry?"*

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /vendors` | All vendors with latest risk scores |
| `GET /vendors/{name}` | Vendor detail with full signal list |
| `POST /vendors/{name}/scan` | Trigger live scan (Bright Data → Claude → score) |
| `POST /scan/all` | Scan all vendors in background |
| `GET /alerts?since=YYYY-MM-DD` | New signals since date |
| `GET /proof/unblocked?url=...` | 403 vs 200 side-by-side proof |

## MCP Tools

| Tool | Description |
|---|---|
| `get_vendor_risk(vendor)` | Score + signals with source URLs for one vendor |
| `list_high_risk_vendors(threshold)` | All vendors above a risk score |
| `whats_new_since(date)` | Delta signals since a date |

## Tech Stack

- **Backend**: Python 3.11, FastAPI, asyncio
- **Web data**: Bright Data SERP API, Web Unlocker, Web Scraper API
- **LLM**: Anthropic Claude (claude-sonnet-4-6)
- **Storage**: SQLite
- **MCP**: `mcp` Python SDK
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Recharts

## Risk Score Formula

```
score = min(
  sum(severity_i × 0.5^(days_i / 30)) / (3 × 5) × 100 × vendor_weight,
  100
)
```

- **Recency decay**: half-life of 30 days — fresh signals score higher
- **Vendor weight**: critical vendors (Okta=1.4x, AWS=1.5x) score higher for same severity
- **Delta alerting**: each run diffs against prior summaries — only NEW signals are flagged
