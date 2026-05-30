"""
MCP Server — exposes vendor risk data to Claude as callable tools.

Tools:
  get_vendor_risk(vendor)          → score + latest signals with source URLs
  list_high_risk_vendors(threshold) → vendors above a risk score threshold
  whats_new_since(date)            → new signals detected since a given date

Run standalone: python -m backend.mcp_server.server
Claude Desktop config: add this server to claude_desktop_config.json
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure project root is on PYTHONPATH when run standalone
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from backend.db import database as db
from backend.scoring.risk_scorer import score_label, score_color

server = Server("third-party-risk-radar")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_vendor_risk",
            description=(
                "Get the current risk score and latest risk signals for a specific vendor. "
                "Returns score (0-100), risk level, and cited signals with source URLs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor": {
                        "type": "string",
                        "description": "Vendor name (e.g. 'Salesforce', 'Okta', 'AWS')",
                    }
                },
                "required": ["vendor"],
            },
        ),
        Tool(
            name="list_high_risk_vendors",
            description=(
                "List all vendors with a risk score above a given threshold. "
                "Useful for portfolio-level risk summaries."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "number",
                        "description": "Minimum risk score (0-100). Default: 50.",
                        "default": 50,
                    }
                },
            },
        ),
        Tool(
            name="whats_new_since",
            description=(
                "Return all NEW risk signals detected since a given date. "
                "Great for answering 'what changed this week?' with citations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "ISO date string YYYY-MM-DD. Defaults to 7 days ago.",
                    }
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    db.init_db()

    if name == "get_vendor_risk":
        vendor_name = arguments.get("vendor", "")
        vendor = db.get_vendor(vendor_name)
        if not vendor:
            return [TextContent(type="text", text=f"Vendor '{vendor_name}' not found in database.")]

        score_row = db.get_latest_score(vendor_name)
        signals = db.get_latest_signals(vendor_name, limit=20)

        score = score_row["score"] if score_row else None
        level = score_label(score) if score is not None else "Not scanned"

        lines = [
            f"## {vendor_name} Risk Report",
            f"**Risk Score:** {score:.1f}/100 ({level})" if score is not None else "**Risk Score:** Not scanned yet",
            f"**Stack Role:** {vendor['stack_role']}",
            f"**Criticality Weight:** {vendor['weight']}x",
            f"**Last Scanned:** {score_row['computed_at'] if score_row else 'Never'}",
            f"**Signals Found:** {len(signals)}",
            "",
        ]

        if signals:
            lines.append("### Risk Signals (with sources)")
            for s in signals[:10]:
                new_tag = " 🆕" if s["is_new"] else ""
                lines.append(
                    f"- **[{s['category']} / Severity {s['severity']}/5]{new_tag}** {s['summary']}\n"
                    f"  Source: {s['source_url']} (detected {s['date_detected']})"
                )
        else:
            lines.append("No risk signals found for this vendor.")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "list_high_risk_vendors":
        threshold = float(arguments.get("threshold", 50))
        all_scores = db.get_all_latest_scores()
        high_risk = [s for s in all_scores if s["score"] >= threshold]

        if not high_risk:
            return [TextContent(type="text", text=f"No vendors with risk score ≥ {threshold}.")]

        lines = [
            f"## High-Risk Vendors (score ≥ {threshold})",
            f"Found **{len(high_risk)}** vendors requiring attention:\n",
        ]
        for row in sorted(high_risk, key=lambda x: x["score"], reverse=True):
            level = score_label(row["score"])
            lines.append(
                f"- **{row['vendor']}** — Score: {row['score']:.1f}/100 ({level}), "
                f"Signals: {row['signal_count']}, Last scanned: {row['computed_at'][:10]}"
            )

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "whats_new_since":
        date_str = arguments.get("date")
        if not date_str:
            date_str = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

        signals = db.get_new_signals_since(date_str)

        if not signals:
            return [TextContent(type="text", text=f"No new risk signals since {date_str}.")]

        by_vendor: dict[str, list] = {}
        for s in signals:
            by_vendor.setdefault(s["vendor"], []).append(s)

        lines = [
            f"## New Risk Signals Since {date_str}",
            f"**{len(signals)} new signals** across **{len(by_vendor)} vendors**:\n",
        ]
        for vendor, vsignals in sorted(by_vendor.items(), key=lambda x: max(s["severity"] for s in x[1]), reverse=True):
            max_sev = max(s["severity"] for s in vsignals)
            lines.append(f"### {vendor} (max severity: {max_sev}/5, {len(vsignals)} signals)")
            for s in vsignals[:5]:
                lines.append(
                    f"- **[{s['category']} / {s['severity']}/5]** {s['summary']}\n"
                    f"  Source: {s['source_url']}"
                )

        return [TextContent(type="text", text="\n".join(lines))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
