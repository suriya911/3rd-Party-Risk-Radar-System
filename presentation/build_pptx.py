"""Generate the Vendor Radar Risk pitch deck as a .pptx (dark theme)."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Palette
BG = RGBColor(0x0F, 0x11, 0x17)
CARD = RGBColor(0x1A, 0x1D, 0x2E)
INK = RGBColor(0xE7, 0xEC, 0xF3)
MUT = RGBColor(0x9A, 0xA4, 0xB5)
DIM = RGBColor(0x5B, 0x65, 0x77)
BLUE = RGBColor(0x5B, 0x8C, 0xFF)
PURPLE = RGBColor(0xA7, 0x8B, 0xFA)
RED = RGBColor(0xFF, 0x6B, 0x6B)
GREEN = RGBColor(0x46, 0xD3, 0x9A)
LINE = RGBColor(0x2A, 0x2F, 0x42)
BLUEBG = RGBColor(0x15, 0x20, 0x38)
PURPBG = RGBColor(0x20, 0x1A, 0x33)
REDBG = RGBColor(0x2C, 0x17, 0x1B)

FONT = "Segoe UI"
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def new_slide():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    return s


def text(slide, l, t, w, h, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line=1.0, space=0):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, runs in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line
        if space:
            p.space_after = Pt(space)
        for (txt, size, color, *rest) in runs:
            r = p.add_run()
            r.text = txt
            r.font.size = Pt(size)
            r.font.name = FONT
            r.font.color.rgb = color
            r.font.bold = rest[0] if len(rest) > 0 else False
            r.font.italic = rest[1] if len(rest) > 1 else False
    return tf


def card(slide, l, t, w, h, fill=CARD, line=LINE, radius=0.07):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = line
    sh.line.width = Pt(1)
    sh.shadow.inherit = False
    try:
        sh.adjustments[0] = radius
    except Exception:
        pass
    return sh


def info_card(slide, l, t, w, h, head, body, head_color=BLUE, fill=CARD, line=LINE):
    card(slide, l, t, w, h, fill=fill, line=line)
    tf = slide.shapes.add_textbox(Inches(l + 0.22), Inches(t + 0.16), Inches(w - 0.44), Inches(h - 0.32)).text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = head.upper(); r.font.size = Pt(11.5); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = head_color
    p2 = tf.add_paragraph(); p2.space_before = Pt(7); p2.line_spacing = 1.05
    r2 = p2.add_run(); r2.text = body; r2.font.size = Pt(12.5); r2.font.name = FONT; r2.font.color.rgb = MUT


def stat_card(slide, l, t, w, h, stat, color, label):
    card(slide, l, t, w, h)
    tf = slide.shapes.add_textbox(Inches(l + 0.2), Inches(t + 0.22), Inches(w - 0.4), Inches(h - 0.4)).text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = stat; r.font.size = Pt(34); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = color
    p2 = tf.add_paragraph(); p2.space_before = Pt(6); p2.line_spacing = 1.05
    r2 = p2.add_run(); r2.text = label; r2.font.size = Pt(12); r2.font.name = FONT; r2.font.color.rgb = MUT


def node(slide, l, t, w, h, title_txt, sub, line=LINE):
    card(slide, l, t, w, h, line=line)
    tf = slide.shapes.add_textbox(Inches(l + 0.12), Inches(t + 0.12), Inches(w - 0.24), Inches(h - 0.24)).text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = title_txt; r.font.size = Pt(12); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = INK
    p2 = tf.add_paragraph(); p2.space_before = Pt(3); p2.line_spacing = 1.0
    r2 = p2.add_run(); r2.text = sub; r2.font.size = Pt(9.5); r2.font.name = FONT; r2.font.color.rgb = MUT


def arrow(slide, l, t, w=0.4, h=0.9, ch="→"):
    text(slide, l, t, w, h, [[(ch, 18, DIM)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def pill(slide, l, t, txt, fg, bg):
    w = 0.105 * len(txt) + 0.45
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(0.4))
    sh.fill.solid(); sh.fill.fore_color.rgb = bg
    sh.line.color.rgb = fg; sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    sh.adjustments[0] = 0.5
    tf = sh.text_frame; tf.word_wrap = False; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_top = Pt(1); tf.margin_bottom = Pt(1)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = txt; r.font.size = Pt(11); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = fg
    return w


def pill_row(slide, l, t, items):
    x = l
    for txt, fg, bg in items:
        x += pill(slide, x, t, txt, fg, bg) + 0.12


def kicker(slide, txt):
    text(slide, 0.9, 0.62, 11.5, 0.4, [[(txt.upper(), 12, BLUE, True)]])


def title(slide, parts, top=1.15, size=33):
    text(slide, 0.9, top, 11.6, 1.6, [[(t, size, c, True) for (t, c) in parts]], line=1.06)


def footer(slide, n):
    text(slide, 0.9, 6.98, 6, 0.4, [[("Vendor Radar Risk", 10, DIM)]])
    text(slide, 7.3, 6.98, 5.1, 0.4, [[(f"{n} / 12", 10, DIM)]], align=PP_ALIGN.RIGHT)


# ───────────────────────── 1 · TITLE ─────────────────────────
s = new_slide()
kicker(s, "Web Data UNLOCKED · Bright Data × Enterprise AI")
text(s, 0.9, 1.7, 11.5, 2.0, [[("Vendor ", 60, INK, True), ("Radar ", 60, PURPLE, True), ("Risk", 60, INK, True)]], line=1.0)
text(s, 0.9, 3.55, 9.8, 1.4, [[
    ("Continuous, cited vendor-risk intelligence from the live web — with ", 19, MUT),
    ("Blast Radius", 19, INK, True),
    (" cascade detection that tells you which connected vendors to investigate, and when.", 19, MUT),
]], line=1.2)
pill_row(s, 0.9, 5.25, [
    ("Bright Data SERP", BLUE, BLUEBG), ("Web Unlocker", BLUE, BLUEBG),
    ("AI/ML API · Claude", PURPLE, PURPBG), ("Hosted MCP", PURPLE, PURPBG),
])
text(s, 0.9, 6.98, 11.5, 0.4, [[("Team bigbros  ·  suriya911-third-party-risk-radar.hf.space", 10, DIM)]])

# ───────────────────────── 2 · PROBLEM ─────────────────────────
s = new_slide()
kicker(s, "The Problem")
title(s, [("You learn your vendor was breached ", INK), ("from the news", PURPLE), (" — weeks late.", INK)])
bullets = [
    "Enterprises depend on dozens of third parties — identity, CRM, data, CDN.",
    "Worse: breaches cascade. One stolen OAuth token or compromised identity provider spreads to every connected vendor.",
    "Companies have a vendor list — but zero visibility into the connections between vendors.",
    "So they can't answer the only question that matters: “Which of my other vendors are now exposed, and do I act today?”",
]
paras = [[("▸  ", 16, PURPLE), (b, 17, INK)] for b in bullets]
text(s, 0.9, 2.7, 11.4, 3.6, paras, line=1.15, space=14)
footer(s, 2)

# ───────────────────────── 3 · WHY NOW ─────────────────────────
s = new_slide()
kicker(s, "Why now")
title(s, [("The 2024–2026 breach story is ", INK), ("connection risk", PURPLE), (".", INK)])
info_card(s, 0.9, 2.6, 3.66, 2.0, "Salesloft-Drift", "One OAuth token cascade reached 700+ orgs — Salesforce, GitHub, CrowdStrike, Slack.")
info_card(s, 4.83, 2.6, 3.66, 2.0, "Okta → Cloudflare", "Stolen Okta credentials pivoted into Cloudflare's internal Atlassian.")
info_card(s, 8.76, 2.6, 3.66, 2.0, "Snowflake", "Third-party integrator tokens exposed downstream customer data.")
text(s, 0.9, 4.95, 11.4, 1.0, [[("Vendor scores in isolation miss this entirely. The risk lives ", 18, MUT), ("between", 18, INK, True), (" vendors.", 18, MUT)]], line=1.2)
footer(s, 3)

# ───────────────────────── 4 · SOLUTION ─────────────────────────
s = new_slide()
kicker(s, "Our Solution")
title(s, [("Turn the ", INK), ("live web", PURPLE), (" into continuous, cited risk intelligence.", INK)])
info_card(s, 0.9, 2.7, 5.6, 1.6, "Discover", "Real-time sweep of Google News, breach trackers, CVE feeds, status pages & regulatory portals — per vendor.")
info_card(s, 6.73, 2.7, 5.6, 1.6, "Extract", "AI converts raw pages into structured risk signals. Every signal needs a real source URL — never invented.")
info_card(s, 0.9, 4.5, 5.6, 1.6, "Score", "Transparent 0–100 risk score with recency decay and vendor-criticality weighting.")
info_card(s, 6.73, 4.5, 5.6, 1.6, "Act", "Alerts on new signals + Blast Radius verdicts on cross-vendor cascades.")
footer(s, 4)

# ───────────────────────── 5 · DIFFERENTIATOR ─────────────────────────
s = new_slide()
kicker(s, "The Differentiator")
title(s, [("Blast Radius", PURPLE), (" — cascade exposure detection", INK)])
text(s, 0.9, 2.25, 11.4, 1.3, [[
    ("Reads recent security incidents across all vendors, auto-discovers the connections (shared attacker, OAuth token, identity provider, cross-vendor mention), clusters them, and issues a verdict per incident.", 16.5, MUT)
]], line=1.2)
card(s, 0.9, 3.75, 11.43, 2.15, fill=RGBColor(0x1C, 0x18, 0x30), line=RGBColor(0x44, 0x33, 0x66))
pill(s, 1.15, 4.0, "⚠  INVESTIGATE NOW", RED, REDBG)
text(s, 3.6, 4.02, 8.5, 0.5, [[("Salesloft-Drift incident · connected by ", 13, MUT), ("salesloft · drift · oauth", 13, RED, True)]], anchor=MSO_ANCHOR.MIDDLE)
pill_row(s, 1.15, 4.62, [(v, RGBColor(0xCF, 0xE0, 0xFF), BLUEBG) for v in ["CrowdStrike", "GitHub", "Salesforce", "Slack"]])
text(s, 1.15, 5.2, 11, 0.5, [[("→ Rotate shared tokens and audit the integrations now.  ", 13.5, MUT), ("(4 cited sources)", 13.5, GREEN, True)]])
text(s, 0.9, 6.1, 11.4, 0.6, [[("Correctly separates the 4-vendor OAuth cascade from the Okta–Cloudflare identity incident.", 13, DIM, False, True)]])
footer(s, 5)

# ───────────────────────── 6 · ARCHITECTURE ─────────────────────────
s = new_slide()
kicker(s, "Architecture")
title(s, [("One pipeline, fully ", INK), ("cited", PURPLE), (", end to end", INK)])
y1 = 2.7
nodes1 = [
    ("Bright Data SERP", "news discovery, 6 queries/vendor", RGBColor(0x2A, 0x3A, 0x5E)),
    ("Web Unlocker", "403→200 on blocked pages", RGBColor(0x2A, 0x3A, 0x5E)),
    ("AI/ML API · Claude", "structured extraction", RGBColor(0x3A, 0x2E, 0x55)),
    ("Risk Scorer", "0–100, recency decay", LINE),
    ("Blast Radius", "cascade graph + verdicts", RGBColor(0x2A, 0x4A, 0x3C)),
]
x = 0.9
nw = 1.97
for i, (tt, sub, ln) in enumerate(nodes1):
    node(s, x, y1, nw, 1.25, tt, sub, line=ln)
    x += nw
    if i < len(nodes1) - 1:
        arrow(s, x, y1, 0.34, 1.25)
        x += 0.34
y2 = 4.55
node(s, 0.9, y2, 3.4, 1.2, "FastAPI + SQLite", "REST API · persistence")
arrow(s, 4.35, y2, 0.45, 1.2)
node(s, 4.85, y2, 3.7, 1.2, "React dashboard", "scores · alerts · proof · Blast Radius")
arrow(s, 8.6, y2, 0.45, 1.2, ch="+")
node(s, 9.1, y2, 3.33, 1.2, "Hosted MCP (SSE)", "ask any AI agent: “am I exposed?”", line=RGBColor(0x2A, 0x4A, 0x3C))
footer(s, 6)

# ───────────────────────── 7 · TECH ─────────────────────────
s = new_slide()
kicker(s, "Technologies — meaningful Bright Data use")
title(s, [("3 Bright Data products + AI + MCP", INK)])
info_card(s, 0.9, 2.6, 3.66, 1.95, "Bright Data SERP API", "Live Google News discovery — the freshness engine. 6 risk-category queries per vendor.")
info_card(s, 4.83, 2.6, 3.66, 1.95, "Bright Data Web Unlocker", "Bypasses bot protection on breach trackers & trust centers. Provable 403→200.")
info_card(s, 8.76, 2.6, 3.66, 1.95, "MCP Server (hosted)", "Our own MCP server, online over SSE — agent-native risk tools.")
pill_row(s, 0.9, 4.95, [
    ("AI/ML API · Claude", PURPLE, PURPBG), ("FastAPI", INK, CARD), ("React + TypeScript", INK, CARD),
])
pill_row(s, 0.9, 5.5, [
    ("SQLite", INK, CARD), ("Docker", INK, CARD), ("Hugging Face Spaces", INK, CARD),
    ("GitHub Actions CI", INK, CARD), ("Pytest ×50", INK, CARD),
])
footer(s, 7)

# ───────────────────────── 8 · DEMO ─────────────────────────
s = new_slide()
kicker(s, "Live Demo — what we'll show")
title(s, [("It's ", INK), ("live", PURPLE), (", not slideware", INK)])
demo = [
    ("Dashboard", " — 10 vendors, color-coded scores, risk-landscape radar."),
    ("Blast Radius", " — the Salesloft cascade with INVESTIGATE verdict + citations."),
    ("403 → 200 proof", " — naive fetch blocked, Web Unlocker succeeds, side by side."),
    ("Live scan", " — click Scan; ~40s later fresh, dated, cited signals appear."),
    ("Hosted MCP", " — ask Claude “Am I exposed to a cascading breach this week?”"),
]
paras = [[("▸  ", 16, PURPLE), (h, 17, INK, True), (b, 17, MUT)] for h, b in demo]
text(s, 0.9, 2.6, 11.5, 3.2, paras, line=1.15, space=12)
text(s, 0.9, 6.2, 11.5, 0.4, [[("suriya911-third-party-risk-radar.hf.space", 14, BLUE, True)]])
footer(s, 8)

# ───────────────────────── 9 · OUTCOMES ─────────────────────────
s = new_slide()
kicker(s, "Outcomes — verified in production")
title(s, [("Real data, real cascades, ", INK), ("shipped", GREEN), (".", INK)])
stat_card(s, 0.9, 2.6, 2.73, 1.7, "94.8", RED, "Okta — Critical, from cited incidents")
stat_card(s, 3.83, 2.6, 2.73, 1.7, "2", PURPLE, "distinct cascades auto-detected")
stat_card(s, 6.76, 2.6, 2.73, 1.7, "68→87", GREEN, "Salesforce live-scan score jump")
stat_card(s, 9.69, 2.6, 2.73, 1.7, "50", BLUE, "tests passing · CI green")
paras = [
    [("▸  ", 16, PURPLE), ("Live scan verified on the hosted Space — fresh sources (securityweek, cybernews), never mocked.", 16, INK)],
    [("▸  ", 16, PURPLE), ("Deployed as one Docker container on Hugging Face Spaces; MCP online over SSE.", 16, INK)],
]
text(s, 0.9, 4.7, 11.5, 1.5, paras, line=1.15, space=12)
footer(s, 9)

# ───────────────────────── 10 · WHY WE WIN ─────────────────────────
s = new_slide()
kicker(s, "Why it wins")
title(s, [("Solves the ", INK), ("unsolved", PURPLE), (" part of vendor risk", INK)])
info_card(s, 0.9, 2.7, 5.6, 1.6, "Real problem", "Cascade breaches are THE 2024–2026 enterprise security story. We address it head-on.")
info_card(s, 6.73, 2.7, 5.6, 1.6, "Novel", "Everyone scores vendors in isolation. Nobody auto-maps the live connection graph.")
info_card(s, 0.9, 4.5, 5.6, 1.6, "Deep Bright Data use", "SERP + Web Unlocker are core to the product, not bolted on.")
info_card(s, 6.73, 4.5, 5.6, 1.6, "Agent-native", "Hosted MCP makes the whole system usable by any AI agent.")
footer(s, 10)

# ───────────────────────── 11 · NEXT ─────────────────────────
s = new_slide()
kicker(s, "What's next")
title(s, [("From hackathon to ", INK), ("product", PURPLE)])
nxt = [
    "Continuous scheduled scans + Slack/email cascade alerts.",
    "Deeper connection graph: shared sub-processors & 4th-party dependencies.",
    "Score-history trends and exposure-over-time per cascade.",
    "CSV/SSO vendor import for real enterprise portfolios.",
]
paras = [[("▸  ", 16, PURPLE), (b, 17, INK)] for b in nxt]
text(s, 0.9, 2.7, 11.4, 3.0, paras, line=1.15, space=14)
footer(s, 11)

# ───────────────────────── 12 · CLOSE ─────────────────────────
s = new_slide()
kicker(s, "Thank you")
text(s, 0.9, 1.7, 11.5, 1.9, [[("Know ", 52, INK, True), ("first", 52, PURPLE, True), (". Not from the news.", 52, INK, True)]], line=1.0)
links = [
    [("Live demo   ", 16, INK, True), ("suriya911-third-party-risk-radar.hf.space", 16, BLUE)],
    [("Code        ", 16, INK, True), ("github.com/suriya911/3rd-Party-Risk-Radar-System", 16, BLUE)],
    [("MCP         ", 16, INK, True), ("…hf.space/mcp/sse", 16, BLUE)],
]
text(s, 0.9, 3.6, 11.5, 1.6, links, line=1.4)
pill_row(s, 0.9, 5.5, [
    ("Bright Data SERP", BLUE, BLUEBG), ("Web Unlocker", BLUE, BLUEBG),
    ("AI/ML API", PURPLE, PURPBG), ("MCP", PURPLE, PURPBG),
])
text(s, 0.9, 6.98, 11.5, 0.4, [[("Team bigbros · Vendor Radar Risk", 10, DIM)]])

out = "presentation/Vendor-Radar-Risk.pptx"
prs.save(out)
print("Saved", out, "with", len(prs.slides._sldIdLst), "slides")
