import { useEffect, useState } from "react";
import { Share2, ExternalLink, ChevronDown, ShieldAlert, Eye, Check } from "lucide-react";
import { api, BlastIncident, Verdict } from "../api/client";

const VERDICT_STYLE: Record<Verdict, { label: string; cls: string; icon: React.ElementType }> = {
  INVESTIGATE: {
    label: "Investigate now",
    cls: "border-red-500/40 bg-red-500/15 text-red-300",
    icon: ShieldAlert,
  },
  MONITOR: {
    label: "Monitor",
    cls: "border-amber-500/40 bg-amber-500/15 text-amber-300",
    icon: Eye,
  },
  NO_ACTION: {
    label: "No action",
    cls: "border-slate-500/30 bg-slate-500/10 text-slate-400",
    icon: Check,
  },
};

function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const s = VERDICT_STYLE[verdict];
  const Icon = s.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wide ${s.cls}`}>
      <Icon className="h-3.5 w-3.5" />
      {s.label}
    </span>
  );
}

function IncidentCard({ incident }: { incident: BlastIncident }) {
  const [open, setOpen] = useState(false);
  const isCascade = incident.vendor_count >= 2;

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="truncate font-semibold text-white">{incident.title}</h3>
            {isCascade && (
              <span className="shrink-0 rounded-full bg-purple-500/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-purple-300">
                Cascade · {incident.vendor_count} vendors
              </span>
            )}
          </div>
          <p className="mt-1 text-sm leading-relaxed text-slate-300">{incident.recommendation}</p>
        </div>
        <VerdictBadge verdict={incident.verdict} />
      </div>

      {/* Connected vendors */}
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        {incident.affected_vendors.map((v, i) => (
          <span key={v} className="inline-flex items-center">
            {i > 0 && <Share2 className="mx-1 h-3 w-3 text-slate-600" />}
            <span className="rounded-md bg-blue-500/15 px-2 py-0.5 text-xs font-semibold text-blue-300">
              {v}
            </span>
          </span>
        ))}
      </div>

      {/* Connection terms */}
      {incident.link_terms.length > 0 && (
        <div className="mt-2 text-xs text-slate-500">
          Connected by:{" "}
          {incident.link_terms.slice(0, 6).map((t) => (
            <span key={t} className="mr-1 rounded bg-white/5 px-1.5 py-0.5 font-mono text-slate-400">
              {t}
            </span>
          ))}
        </div>
      )}

      {/* Expand evidence */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-slate-200"
      >
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
        {open ? "Hide" : "Show"} evidence ({incident.members.length} signals · {incident.last_seen})
      </button>

      {open && (
        <div className="mt-3 space-y-2 border-t border-white/5 pt-3">
          {incident.members.map((m, i) => (
            <div key={i} className="rounded-lg bg-white/[0.02] p-2.5">
              <div className="mb-1 flex items-center gap-2">
                <span className="text-xs font-semibold text-white">{m.vendor}</span>
                <span className="rounded bg-red-500/15 px-1.5 py-0.5 text-[10px] font-bold text-red-300">
                  SEV {m.severity}
                </span>
                <span className="ml-auto text-[10px] text-slate-500">{m.date_detected}</span>
              </div>
              <p className="text-xs leading-relaxed text-slate-300">{m.summary}</p>
              {m.source_url && (
                <a
                  href={m.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 inline-flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300"
                >
                  <ExternalLink className="h-3 w-3" />
                  Source
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function BlastRadiusPanel() {
  const [incidents, setIncidents] = useState<BlastIncident[]>([]);
  const [standalone, setStandalone] = useState<BlastIncident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getBlastRadius(30)
      .then((r) => {
        setIncidents(r.incidents);
        setStandalone(r.standalone.filter((s) => s.verdict !== "NO_ACTION"));
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const investigate = incidents.filter((i) => i.verdict === "INVESTIGATE").length;

  return (
    <div className="rounded-xl border border-purple-500/20 bg-gradient-to-b from-[#1c1830] to-[#1a1d2e] p-5">
      <div className="mb-1 flex items-center gap-2">
        <Share2 className="h-5 w-5 text-purple-400" />
        <h2 className="text-lg font-bold text-white">Blast Radius</h2>
        <span className="rounded-full bg-purple-500/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-purple-300">
          Cascade exposure
        </span>
        {investigate > 0 && (
          <span className="ml-auto rounded-full bg-red-500/20 px-2.5 py-1 text-xs font-bold text-red-300">
            {investigate} need investigation
          </span>
        )}
      </div>
      <p className="mb-4 text-xs text-slate-500">
        Recent security incidents that connect multiple of your vendors — and whether to act.
      </p>

      {loading ? (
        <div className="py-10 text-center text-sm text-slate-500">Mapping connections…</div>
      ) : incidents.length === 0 && standalone.length === 0 ? (
        <div className="py-10 text-center text-sm text-slate-500">
          No connected security incidents in the last 30 days.
        </div>
      ) : (
        <div className="space-y-3">
          {incidents.map((inc, i) => (
            <IncidentCard key={`c${i}`} incident={inc} />
          ))}
          {standalone.map((inc, i) => (
            <IncidentCard key={`s${i}`} incident={inc} />
          ))}
        </div>
      )}
    </div>
  );
}
