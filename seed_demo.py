"""Seed realistic demo data into SQLite for dashboard preview."""
from backend.db.database import (
    init_db, create_run, complete_run,
    insert_signals, upsert_score, get_all_latest_scores, get_vendor,
)
from backend.scoring.risk_scorer import compute_score, score_label

init_db()

vendor_signals = {
    "Okta": [
        {"vendor": "Okta", "category": "Security", "severity": 5,
         "summary": "Source code stolen via GitHub; stolen credentials used to compromise Cloudflare Atlassian instance",
         "source_url": "https://sec.okta.com/articles/2023/11/okta-october-2023-security-incident",
         "date_detected": "2026-05-25", "is_new": 1},
        {"vendor": "Okta", "category": "Reputational", "severity": 4,
         "summary": "Third major breach in two years raises serious questions about Okta security posture",
         "source_url": "https://techcrunch.com/2023/11/03/okta-admits-hackers-accessed-all-customer-support-data/",
         "date_detected": "2026-05-22", "is_new": 1},
        {"vendor": "Okta", "category": "Regulatory", "severity": 3,
         "summary": "SEC disclosure obligations triggered; potential liability for delayed customer notification",
         "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=okta",
         "date_detected": "2026-05-20", "is_new": 0},
    ],
    "Snowflake": [
        {"vendor": "Snowflake", "category": "Security", "severity": 5,
         "summary": "Anodot integrator token breach exposed customer data via compromised third-party access tokens",
         "source_url": "https://www.anodot.com/blog/security-incident-notice/",
         "date_detected": "2026-05-24", "is_new": 1},
        {"vendor": "Snowflake", "category": "Regulatory", "severity": 4,
         "summary": "FTC investigation opens into data handling practices following breach disclosures",
         "source_url": "https://www.ftc.gov/business-guidance/blog/2023/09/ftc-safeguards-rule",
         "date_detected": "2026-05-18", "is_new": 1},
        {"vendor": "Snowflake", "category": "Reputational", "severity": 3,
         "summary": "Multiple enterprise customers suspend Snowflake integrations pending security review",
         "source_url": "https://www.theregister.com/2024/06/03/snowflake_breach/",
         "date_detected": "2026-05-15", "is_new": 0},
    ],
    "Salesforce": [
        {"vendor": "Salesforce", "category": "Security", "severity": 4,
         "summary": "Salesloft-Drift OAuth token cascade reached 700+ orgs including Salesforce-connected instances",
         "source_url": "https://www.bleepingcomputer.com/news/security/salesloft-drift-attack/",
         "date_detected": "2026-05-28", "is_new": 1},
        {"vendor": "Salesforce", "category": "Security", "severity": 4,
         "summary": "Gainsight OAuth credentials implicated in broader SaaS integration supply chain attack via Salesforce APIs",
         "source_url": "https://techcrunch.com/2026/05/saas-supply-chain/",
         "date_detected": "2026-05-27", "is_new": 1},
        {"vendor": "Salesforce", "category": "Reputational", "severity": 3,
         "summary": "Enterprise customers demand emergency OAuth token rotation following cascade disclosure",
         "source_url": "https://www.csoonline.com/article/salesforce-oauth/",
         "date_detected": "2026-05-29", "is_new": 1},
    ],
    "Cloudflare": [
        {"vendor": "Cloudflare", "category": "Operational", "severity": 4,
         "summary": "BYOIP/BGP route leak caused 6h07m global CDN outage affecting millions of downstream sites",
         "source_url": "https://blog.cloudflare.com/cloudflare-incident-on-february-2026/",
         "date_detected": "2026-05-23", "is_new": 1},
        {"vendor": "Cloudflare", "category": "Security", "severity": 4,
         "summary": "Atlassian instance compromised via Okta stolen credentials; internal source code accessed",
         "source_url": "https://blog.cloudflare.com/thanksgiving-2023-security-incident/",
         "date_detected": "2026-05-20", "is_new": 0},
    ],
    "GitHub": [
        {"vendor": "GitHub", "category": "Security", "severity": 4,
         "summary": "Salesloft attack chain traced back to GitHub repository tokens; lateral movement to AWS detected",
         "source_url": "https://github.blog/security/vulnerability-research/",
         "date_detected": "2026-05-28", "is_new": 1},
        {"vendor": "GitHub", "category": "Security", "severity": 3,
         "summary": "Supply chain attackers used compromised GitHub Actions secrets to exfiltrate CI/CD credentials",
         "source_url": "https://www.wired.com/story/github-actions-supply-chain/",
         "date_detected": "2026-05-26", "is_new": 1},
    ],
    "CrowdStrike": [
        {"vendor": "CrowdStrike", "category": "Operational", "severity": 5,
         "summary": "Faulty Falcon sensor update causes 8.5M Windows BSODs globally — largest IT outage in history",
         "source_url": "https://www.crowdstrike.com/blog/falcon-update-for-windows-hosts-technical-details/",
         "date_detected": "2026-05-19", "is_new": 0},
        {"vendor": "CrowdStrike", "category": "Security", "severity": 3,
         "summary": "Named among firms affected by Salesloft-Drift OAuth token cascade; endpoint data potentially exposed",
         "source_url": "https://www.bleepingcomputer.com/news/security/salesloft-drift-attack/",
         "date_detected": "2026-05-28", "is_new": 1},
        {"vendor": "CrowdStrike", "category": "Regulatory", "severity": 3,
         "summary": "SEC and FTC investigations opened into disclosure timeline and QA process failures",
         "source_url": "https://www.reuters.com/technology/crowdstrike-sec-investigation/",
         "date_detected": "2026-05-10", "is_new": 0},
    ],
    "Slack": [
        {"vendor": "Slack", "category": "Security", "severity": 3,
         "summary": "OAuth integration tokens targeted in Salesloft cascade — connected workspace data at risk",
         "source_url": "https://slack.com/intl/en-gb/blog/news/slack-security-update",
         "date_detected": "2026-05-29", "is_new": 1},
    ],
    "Workday": [
        {"vendor": "Workday", "category": "Regulatory", "severity": 4,
         "summary": "GDPR enforcement action — EUR 2.7M fine for employee data retention practices in EU operations",
         "source_url": "https://edpb.europa.eu/news/national-news/2024/irish-dpc-fines",
         "date_detected": "2026-05-21", "is_new": 1},
        {"vendor": "Workday", "category": "Security", "severity": 3,
         "summary": "Security researchers disclose API endpoint leaking employee PII without proper authentication",
         "source_url": "https://www.darkreading.com/vulnerabilities-threats/workday-api/",
         "date_detected": "2026-05-15", "is_new": 1},
    ],
    "AWS": [
        {"vendor": "AWS", "category": "Operational", "severity": 2,
         "summary": "us-east-1 partial EC2/RDS degradation, 45-minute impact on availability across multiple AZs",
         "source_url": "https://health.aws.amazon.com/health/status",
         "date_detected": "2026-05-25", "is_new": 1},
    ],
    "Datadog": [],  # control — no signals, proves engine won't invent risk
}

for vendor_name, signals in vendor_signals.items():
    run_id = create_run(vendor_name)
    if signals:
        insert_signals(run_id, signals)
    v = get_vendor(vendor_name)
    w = v["weight"] if v else 1.0
    score = compute_score(signals, w)
    upsert_score(run_id, vendor_name, score, len(signals))
    complete_run(run_id)

scores = get_all_latest_scores()
print("Demo-ready vendor scores:")
for s in scores:
    print(
        f"  {s['vendor']:15} {s['score']:5.1f}  "
        f"{score_label(s['score']):10}  signals={s['signal_count']}"
    )
print("\nDemo data seeded successfully.")
