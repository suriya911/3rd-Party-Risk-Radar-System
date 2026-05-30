import { useState } from "react";
import { ShieldCheck, ShieldX, Zap } from "lucide-react";
import { api, BlockedProof } from "../api/client";
import clsx from "clsx";

export default function UnblockedProofPanel() {
  const [url, setUrl] = useState("https://haveibeenpwned.com/");
  const [result, setResult] = useState<BlockedProof | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleTest = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await api.getUnblockedProof(url);
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-white/10 bg-[#1a1d2e] p-5">
      <div className="mb-4 flex items-center gap-2">
        <Zap className="h-4 w-4 text-yellow-400" />
        <h2 className="font-semibold text-white">Unblockability Proof</h2>
        <span className="rounded bg-yellow-500/10 px-1.5 py-0.5 text-xs text-yellow-400">
          403 → 200
        </span>
      </div>

      <p className="mb-4 text-xs text-slate-400">
        Side-by-side: naive fetch vs Bright Data Web Unlocker. Shows why the infrastructure is load-bearing.
      </p>

      <div className="mb-3 flex gap-2">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
          placeholder="https://..."
        />
        <button
          onClick={handleTest}
          disabled={loading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:opacity-50"
        >
          {loading ? "Testing…" : "Test"}
        </button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {result && (
        <div className="mt-4 grid grid-cols-2 gap-3">
          {/* Naive */}
          <div
            className={clsx(
              "rounded-lg border p-4",
              result.naive_blocked
                ? "border-red-500/30 bg-red-500/5"
                : "border-green-500/30 bg-green-500/5"
            )}
          >
            <div className="mb-2 flex items-center gap-2">
              {result.naive_blocked ? (
                <ShieldX className="h-4 w-4 text-red-400" />
              ) : (
                <ShieldCheck className="h-4 w-4 text-green-400" />
              )}
              <span className="text-xs font-semibold text-slate-300">Naive Fetch</span>
            </div>
            <div
              className={clsx(
                "text-3xl font-bold tabular-nums",
                result.naive_blocked ? "text-red-400" : "text-green-400"
              )}
            >
              {result.naive_status || "ERR"}
            </div>
            <div className="mt-1 text-xs text-slate-500">
              {result.naive_blocked ? "BLOCKED / CAPTCHA" : "OK"}
            </div>
          </div>

          {/* Web Unlocker */}
          <div
            className={clsx(
              "rounded-lg border p-4",
              result.unlocker_success
                ? "border-green-500/30 bg-green-500/5"
                : "border-red-500/30 bg-red-500/5"
            )}
          >
            <div className="mb-2 flex items-center gap-2">
              <ShieldCheck className={clsx("h-4 w-4", result.unlocker_success ? "text-green-400" : "text-red-400")} />
              <span className="text-xs font-semibold text-slate-300">Web Unlocker</span>
            </div>
            <div
              className={clsx(
                "text-3xl font-bold tabular-nums",
                result.unlocker_success ? "text-green-400" : "text-red-400"
              )}
            >
              {result.unlocker_status || "ERR"}
            </div>
            <div className="mt-1 text-xs text-slate-500">
              {result.unlocker_success ? "SUCCESS" : "FAILED"}
            </div>
          </div>

          <div className="col-span-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-300">
            {result.proof}
          </div>
        </div>
      )}
    </div>
  );
}
