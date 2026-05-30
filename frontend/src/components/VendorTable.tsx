import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, ExternalLink, ChevronUp, ChevronDown } from "lucide-react";
import { api, Vendor } from "../api/client";
import RiskBadge from "./RiskBadge";
import clsx from "clsx";

interface Props {
  vendors: Vendor[];
  onRefresh: () => void;
}

type SortKey = "score" | "name" | "signal_count";

export default function VendorTable({ vendors, onRefresh }: Props) {
  const navigate = useNavigate();
  const [scanning, setScanning] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = [...vendors].sort((a, b) => {
    const av = a[sortKey] ?? -1;
    const bv = b[sortKey] ?? -1;
    if (av < bv) return sortAsc ? -1 : 1;
    if (av > bv) return sortAsc ? 1 : -1;
    return 0;
  });

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  const handleScan = async (e: React.MouseEvent, name: string) => {
    e.stopPropagation();
    setScanning(name);
    try {
      await api.scanVendor(name);
      onRefresh();
    } catch (err) {
      console.error(err);
    } finally {
      setScanning(null);
    }
  };

  const SortIcon = ({ k }: { k: SortKey }) =>
    sortKey === k ? (
      sortAsc ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
    ) : null;

  return (
    <div className="overflow-hidden rounded-xl border border-white/10 bg-[#1a1d2e]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-xs uppercase tracking-wider text-slate-500">
            <th
              className="cursor-pointer px-5 py-3 text-left hover:text-slate-300"
              onClick={() => handleSort("name")}
            >
              <span className="flex items-center gap-1">Vendor <SortIcon k="name" /></span>
            </th>
            <th className="px-5 py-3 text-left">Stack Role</th>
            <th
              className="cursor-pointer px-5 py-3 text-left hover:text-slate-300"
              onClick={() => handleSort("score")}
            >
              <span className="flex items-center gap-1">Risk Score <SortIcon k="score" /></span>
            </th>
            <th
              className="cursor-pointer px-5 py-3 text-right hover:text-slate-300"
              onClick={() => handleSort("signal_count")}
            >
              <span className="flex items-center justify-end gap-1">Signals <SortIcon k="signal_count" /></span>
            </th>
            <th className="px-5 py-3 text-right">Last Scanned</th>
            <th className="px-5 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((v, i) => (
            <tr
              key={v.name}
              onClick={() => navigate(`/vendor/${encodeURIComponent(v.name)}`)}
              className={clsx(
                "cursor-pointer border-b border-white/5 transition-colors hover:bg-white/5",
                i % 2 === 0 ? "" : "bg-white/[0.02]"
              )}
            >
              <td className="px-5 py-3.5 font-semibold text-white">{v.name}</td>
              <td className="px-5 py-3.5 text-slate-400">{v.stack_role}</td>
              <td className="px-5 py-3.5">
                <RiskBadge score={v.score} label={v.score_label} />
              </td>
              <td className="px-5 py-3.5 text-right tabular-nums text-slate-300">
                {v.signal_count ?? "—"}
              </td>
              <td className="px-5 py-3.5 text-right text-slate-500 text-xs">
                {v.last_scanned ? new Date(v.last_scanned).toLocaleDateString() : "Never"}
              </td>
              <td className="px-5 py-3.5 text-right">
                <button
                  onClick={(e) => handleScan(e, v.name)}
                  disabled={scanning === v.name}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/10 disabled:opacity-50"
                >
                  <RefreshCw className={clsx("h-3 w-3", scanning === v.name && "animate-spin")} />
                  {scanning === v.name ? "Scanning…" : "Scan"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {vendors.length === 0 && (
        <div className="py-16 text-center text-slate-500">No vendors loaded yet.</div>
      )}
    </div>
  );
}
