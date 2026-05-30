import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Radio, AlertTriangle, ShieldCheck, Activity } from "lucide-react";
import { api, Vendor } from "../api/client";
import VendorTable from "../components/VendorTable";
import AlertFeed from "../components/AlertFeed";
import BlastRadiusPanel from "../components/BlastRadiusPanel";
import UnblockedProofPanel from "../components/UnblockedProofPanel";
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";

function StatCard({ label, value, sub, icon: Icon, color }: {
  label: string; value: string | number; sub?: string;
  icon: React.ElementType; color: string;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-[#1a1d2e] p-4">
      <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-wider text-slate-500">
        <Icon className={`h-3.5 w-3.5 ${color}`} />
        {label}
      </div>
      <div className="text-3xl font-bold text-white tabular-nums">{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanningAll, setScanningAll] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await api.getVendors();
      setVendors(data);
      setError("");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleScanAll = async () => {
    setScanningAll(true);
    try {
      await api.scanAll();
      setTimeout(load, 3000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setScanningAll(false);
    }
  };

  const scanned = vendors.filter((v) => v.score !== null);
  const critical = vendors.filter((v) => (v.score ?? 0) >= 75).length;
  const high = vendors.filter((v) => (v.score ?? 0) >= 50 && (v.score ?? 0) < 75).length;
  const totalSignals = vendors.reduce((acc, v) => acc + (v.signal_count ?? 0), 0);

  const radarData = scanned.slice(0, 8).map((v) => ({
    vendor: v.name.length > 10 ? v.name.slice(0, 10) : v.name,
    score: v.score ?? 0,
  }));

  return (
    <div className="min-h-screen bg-[#0f1117] px-6 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="h-6 w-6 text-blue-400" />
            <h1 className="text-2xl font-bold text-white">Third-Party Risk Radar</h1>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Continuous, cited vendor risk intelligence — powered by Bright Data
          </p>
        </div>
        <button
          onClick={handleScanAll}
          disabled={scanningAll}
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:opacity-60"
        >
          <RefreshCw className={`h-4 w-4 ${scanningAll ? "animate-spin" : ""}`} />
          {scanningAll ? "Scanning all vendors…" : "Scan All Vendors"}
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Stats Row */}
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Vendors Monitored" value={vendors.length} icon={ShieldCheck} color="text-blue-400" />
        <StatCard label="Critical Risk" value={critical} sub="score ≥ 75" icon={AlertTriangle} color="text-red-400" />
        <StatCard label="High Risk" value={high} sub="score 50–74" icon={AlertTriangle} color="text-orange-400" />
        <StatCard label="Total Signals" value={totalSignals} sub="across all vendors" icon={Activity} color="text-green-400" />
      </div>

      {/* Blast Radius — cascade exposure (headline feature) */}
      <div className="mb-6">
        <BlastRadiusPanel />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Vendor Table — 2 cols */}
        <div className="lg:col-span-2">
          {loading ? (
            <div className="rounded-xl border border-white/10 bg-[#1a1d2e] py-20 text-center text-slate-500">
              Loading vendors…
            </div>
          ) : (
            <VendorTable vendors={vendors} onRefresh={load} />
          )}
        </div>

        {/* Right sidebar */}
        <div className="flex flex-col gap-6">
          {/* Radar Chart */}
          {radarData.length > 0 && (
            <div className="rounded-xl border border-white/10 bg-[#1a1d2e] p-5">
              <h2 className="mb-3 text-sm font-semibold text-white">Risk Landscape</h2>
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#2d3148" />
                  <PolarAngleAxis dataKey="vendor" tick={{ fill: "#64748b", fontSize: 11 }} />
                  <Radar
                    dataKey="score"
                    stroke="#4f6ef7"
                    fill="#4f6ef7"
                    fillOpacity={0.25}
                    strokeWidth={1.5}
                  />
                  <Tooltip
                    contentStyle={{ background: "#1a1d2e", border: "1px solid #2d3148", borderRadius: 8 }}
                    labelStyle={{ color: "#e2e8f0" }}
                    itemStyle={{ color: "#4f6ef7" }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}

          <AlertFeed />
        </div>
      </div>

      {/* Unblockability proof */}
      <div className="mt-6">
        <UnblockedProofPanel />
      </div>
    </div>
  );
}
