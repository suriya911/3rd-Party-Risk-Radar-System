# Deploy — Third-Party Risk Radar

The whole app (FastAPI API **+** built React dashboard) ships as **one Docker
container** listening on port **7860**. The frontend talks to the API on the same
origin via relative paths, so there is no CORS config and no second web server.

- **Local / cloud VM:** `docker compose up --build`
- **Free public host:** Hugging Face Spaces (Docker SDK) — no credit card, stays
  live through the event.

---

## 1. Run locally (or on any VM with Docker)

```bash
docker compose up --build
# open http://localhost:7860
```

On first boot the container seeds realistic demo data (10 vendors, dramatic
scores) — **no API keys required**. The SQLite DB persists on the
`risk_radar_db` named volume across restarts.

To enable **live scans** (Bright Data + Claude), add credentials first:

```bash
cp .env.example .env
# edit .env — BRIGHTDATA_API_TOKEN, ANTHROPIC_API_KEY, zone names
docker compose up --build
```

> The `.env` is optional in compose (`required: false`, needs Docker Compose
> v2.24+). Seeded demo data works without it.

Deploying to a cloud VM (EC2 / DigitalOcean / etc.) is identical: install Docker,
`git clone`, `docker compose up -d --build`, open port 7860.

---

## 2. Free public deploy — Hugging Face Spaces (recommended)

Hugging Face Spaces hosts Docker containers for free, with no credit card, and
the Space stays awake during active use. The root `README.md` already carries the
required Space config (`sdk: docker`, `app_port: 7860`).

### Steps

1. Create an account at <https://huggingface.co> (free).
2. **New → Space**. Name it (e.g. `third-party-risk-radar`), choose
   **Docker** as the SDK, **Blank** template, visibility **Public**.
3. Push this repo to the Space's git remote:

   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/third-party-risk-radar
   git push space main
   ```

   (HF asks for your username + an access token as the password — create one at
   Settings → Access Tokens, "write" scope.)
4. HF builds the Dockerfile automatically. When it finishes, the dashboard is
   live at `https://<your-username>-third-party-risk-radar.hf.space` —
   pre-seeded with demo data.

### Enable live scans on the Space

Add your keys as **Space secrets** (Settings → *Variables and secrets*). They are
injected as environment variables and read by `backend/config.py`:

| Secret | Value |
|---|---|
| `BRIGHTDATA_API_TOKEN` | your Bright Data API token |
| `BRIGHTDATA_USERNAME` | Web Unlocker / proxy username |
| `BRIGHTDATA_PASSWORD` | Web Unlocker / proxy password |
| `BRIGHTDATA_SERP_ZONE` | your SERP zone name (default `serp`) |
| `BRIGHTDATA_UNLOCKER_ZONE` | your Unlocker zone (default `web_unlocker1`) |
| `LLM_API_KEY` | your AI/ML API key (aimlapi.com) — powers extraction |
| `LLM_MODEL` | optional; default `claude-sonnet-4-5` (or `openai/gpt-5-2`, etc.) |

After adding secrets, **Restart** the Space.

> **Note on data:** Space storage is ephemeral — on each rebuild/restart the demo
> data is re-seeded automatically, and any live-scan results since the last boot
> are cleared. That's fine for a demo. For durable storage, attach HF persistent
> storage (paid) and point `DATABASE_URL` at it, or move to Postgres.

---

## 3. The MCP server — now hosted online (SSE)

The MCP server is exposed over the network by the same FastAPI app, so a remote
Claude/agent can connect with no local install:

```
https://<your-space>.hf.space/mcp/sse
```

Tools available: `get_vendor_risk`, `list_high_risk_vendors`, `whats_new_since`,
and `check_exposure` (Blast Radius — *"which of my vendors are exposed through
each other?"*).

**Connect Claude Desktop to the hosted server** via the `mcp-remote` bridge in
`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "risk-radar": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://<your-space>.hf.space/mcp/sse"]
    }
  }
}
```

Restart Claude Desktop, then ask *"Am I exposed to any cascading breach this
week?"* — it calls `check_exposure` on the live server.

> The classic **local stdio** mode still works too:
> `python -m backend.mcp_server.server` (no path/URL needed).

---

## Sponsor credits ≠ hosting

Bright Data ($250 API credits), Speechmatics, AI/ML API, and Featherless provide
**data/AI APIs**, not app hosting. The free public host is Hugging Face Spaces;
the sponsor keys plug in as secrets above.
