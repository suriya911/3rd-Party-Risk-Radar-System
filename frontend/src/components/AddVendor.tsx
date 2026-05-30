import { useState } from "react";
import { Plus, Loader2, Check } from "lucide-react";
import { api } from "../api/client";

export default function AddVendor({ onAdded }: { onAdded?: () => void }) {
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [role, setRole] = useState("");
  const [weight, setWeight] = useState("1.0");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState("");
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !domain.trim()) {
      setError("Name and domain are required.");
      return;
    }
    setBusy(true);
    setError("");
    setDone("");
    try {
      await api.addVendor({
        name: name.trim(),
        domain: domain.trim(),
        stack_role: role.trim(),
        weight: parseFloat(weight) || 1.0,
      });
      setDone(`Added ${name.trim()} to monitoring.`);
      setName("");
      setDomain("");
      setRole("");
      setWeight("1.0");
      onAdded?.();
    } catch (err: any) {
      setError(err.message || "Failed to add vendor.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-xl border border-white/10 bg-[#1a1d2e] p-5">
      <div className="mb-1 flex items-center gap-2">
        <Plus className="h-4 w-4 text-blue-400" />
        <h2 className="font-semibold text-white">Add a custom vendor</h2>
      </div>
      <p className="mb-4 text-xs text-slate-500">
        Drop in any third party you depend on — it's added to the radar and included in the next scan.
      </p>

      <form onSubmit={submit} className="grid grid-cols-1 gap-3 sm:grid-cols-12">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Vendor name (e.g. Stripe)"
          className="sm:col-span-4 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500/50 focus:outline-none"
        />
        <input
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          placeholder="Domain (e.g. stripe.com)"
          className="sm:col-span-3 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500/50 focus:outline-none"
        />
        <input
          value={role}
          onChange={(e) => setRole(e.target.value)}
          placeholder="Role (e.g. Payments)"
          className="sm:col-span-3 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500/50 focus:outline-none"
        />
        <button
          type="submit"
          disabled={busy}
          className="sm:col-span-2 flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:opacity-60"
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Add
        </button>
      </form>

      {done && (
        <div className="mt-3 flex items-center gap-1.5 text-xs text-green-400">
          <Check className="h-3.5 w-3.5" />
          {done}
        </div>
      )}
      {error && <div className="mt-3 text-xs text-red-400">{error}</div>}
    </div>
  );
}
