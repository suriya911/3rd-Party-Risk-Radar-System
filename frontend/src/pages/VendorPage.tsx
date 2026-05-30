import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, RefreshCw, ExternalLink, Radio } from "lucide-react";
import { api, VendorDetail } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import SeverityBadge from "../components/SeverityBadge";
import CategoryBadge from "../components/CategoryBadge";
import clsx from "clsx";

export default function VendorPage() {
  const { name } = useParams<{ name: string }>();
  const [data, setData] = useState<VendorDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const load = async () => {
    if (!name) return;
    try {
      const d = await api.getVendor(decodeURIComponent(name));
      setData(d);
      setError("");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [name]);

  const handleScan = async () => {
    if (!name) return;
    setScanning(true);
    try {
      await api.scanVendor(decodeURIComponent(name));
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setScanning(false);
    }
  };

  const categories = data
    ? [...new Set(data.signals.map((s) => s.category))]
    : [];

  const filteredSignals = data
    ? activeCategory
      ? data.signals.filter((s) => s.category === activeCategory)
      : data.signals
    : [];

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0f1117] text-slate-500">
        Loading…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#0f1117] gap-4">
        <p className="text-red-400">{error || "Vendor not found"}</p>
        <Link to="/" className="text-blue-400 hover:underline">← Back to Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f1117] px-6 py-8">
      {/* Back */}
      <Link to="/" className="mb-6 inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300">
        <ArrowLeft className="h-4 w-4" />
        Dashboard
      </Link>

      {/* Header */}
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <Radio className="h-5 w-5 text-blue-400" />
            <h1 className="text-2xl font-bold text-white">{data.vendor.name}</h1>
            <span className="rounded bg-white/5 px-2 py-0.5 text-xs text-slate-400">
              {data.vendor.stack_role}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-3">
            <RiskBadge score={data.score} label={data.score_label} size="lg" />
            <span className="text-xs text-slate-500">
              Weight: {data.vendor.weight}x · Domain: {data.vendor.domain}
            </span>
          </div>
          {data.last_scanned && (
            <p className="mt-1 text-xs text-slate-600">
              Last scanned: {new Date(data.last_scanned).toLocaleString()}
            </p>
          )}
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-60 transition"
        >
          <RefreshCw className={clsx("h-4 w-4", scanning && "animate-spin")} />
          {scanning ? "Scanning live…" : "Run Live Scan"}
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Stats */}
      <div className="mb-6 grid grid-cols-3 gap-4">
        <div className="rounded-xl border border-white/10 bg-[#1a1d2e] p-4">
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-1">Risk Score</div>
          <div className="text-3xl font-bold text-white">{data.score?.toFixed(0) ?? "—"}<span className="text-lg text-slate-500">/100</span></div>
        </div>
        <div className="rounded-xl border border-white/10 bg-[#1a1d2e] p-4">
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-1">Total Signals</div>
          <div className="text-3xl font-bold text-white">{data.signal_count}</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-[#1a1d2e] p-4">
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-1">New This Run</div>
          <div className="text-3xl font-bold text-white">
            {data.signals.filter((s) => s.is_new).length}
          </div>
        </div>
      </div>

      {/* Category filter */}
      {categories.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={clsx(
              "rounded-full px-3 py-1 text-xs font-medium transition",
              !activeCategory
                ? "bg-blue-600 text-white"
                : "bg-white/5 text-slate-400 hover:bg-white/10"
            )}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat === activeCategory ? null : cat)}
              className={clsx(
                "rounded-full px-3 py-1 text-xs font-medium transition",
                activeCategory === cat
                  ? "bg-blue-600 text-white"
                  : "bg-white/5 text-slate-400 hover:bg-white/10"
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {/* Signal list */}
      {filteredSignals.length === 0 ? (
        <div className="rounded-xl border border-white/10 bg-[#1a1d2e] py-16 text-center text-slate-500">
          No signals found. Run a live scan to collect data.
        </div>
      ) : (
        <div className="space-y-3">
          {filteredSignals.map((s) => (
            <div
              key={s.id}
              className={clsx(
                "rounded-xl border p-4 transition-colors",
                s.is_new
                  ? "border-blue-500/30 bg-blue-500/5"
                  : "border-white/10 bg-[#1a1d2e]"
              )}
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                {s.is_new === 1 && (
                  <span className="rounded bg-blue-500/20 px-1.5 py-0.5 text-xs font-bold text-blue-400">
                    NEW
                  </span>
                )}
                <CategoryBadge category={s.category} />
                <SeverityBadge severity={s.severity} />
                <span className="ml-auto text-xs text-slate-500">{s.date_detected}</span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed">{s.summary}</p>
              <a
                href={s.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 break-all"
              >
                <ExternalLink className="h-3 w-3 flex-shrink-0" />
                {s.source_url}
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
