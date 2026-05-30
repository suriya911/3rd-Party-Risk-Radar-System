import { useEffect, useState } from "react";
import { ExternalLink, BellRing } from "lucide-react";
import { api, Signal } from "../api/client";
import SeverityBadge from "./SeverityBadge";
import CategoryBadge from "./CategoryBadge";

export default function AlertFeed() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [since, setSince] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split("T")[0];
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getAlerts(since)
      .then((r) => setSignals(r.signals))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [since]);

  return (
    <div className="rounded-xl border border-white/10 bg-[#1a1d2e] p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BellRing className="h-4 w-4 text-amber-400" />
          <h2 className="font-semibold text-white">New Signals</h2>
          {signals.length > 0 && (
            <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-xs font-bold text-amber-400">
              {signals.length}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          Since:
          <input
            type="date"
            value={since}
            onChange={(e) => setSince(e.target.value)}
            className="rounded border border-white/10 bg-white/5 px-2 py-1 text-slate-300 focus:outline-none"
          />
        </div>
      </div>

      {loading && (
        <div className="py-8 text-center text-slate-500 text-sm">Loading…</div>
      )}

      {!loading && signals.length === 0 && (
        <div className="py-8 text-center text-slate-500 text-sm">
          No new signals since {since}
        </div>
      )}

      <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
        {signals.map((s) => (
          <div
            key={s.id}
            className="rounded-lg border border-white/5 bg-white/[0.03] p-3 hover:bg-white/5 transition-colors"
          >
            <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
              <span className="font-semibold text-white text-xs">{s.vendor}</span>
              <CategoryBadge category={s.category} />
              <SeverityBadge severity={s.severity} />
              <span className="ml-auto text-xs text-slate-500">{s.date_detected}</span>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">{s.summary}</p>
            <a
              href={s.source_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="mt-1.5 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
            >
              <ExternalLink className="h-3 w-3" />
              View source
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
