const BASE = "";  // proxied by vite to http://localhost:8000

export interface Vendor {
  name: string;
  domain: string;
  weight: number;
  stack_role: string;
  score: number | null;
  score_label: string | null;
  score_color: string | null;
  signal_count: number | null;
  last_scanned: string | null;
}

export interface Signal {
  id: number;
  vendor: string;
  category: string;
  severity: number;
  summary: string;
  source_url: string;
  date_detected: string;
  is_new: number;
}

export interface VendorDetail {
  vendor: Vendor;
  score: number | null;
  score_label: string | null;
  score_color: string | null;
  signal_count: number;
  last_scanned: string | null;
  signals: Signal[];
}

export interface AlertsResponse {
  since: string;
  count: number;
  signals: Signal[];
}

export interface BlockedProof {
  url: string;
  naive_status: number;
  naive_blocked: boolean;
  unlocker_status: number;
  unlocker_success: boolean;
  proof: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export const api = {
  getVendors: () => request<Vendor[]>("/vendors"),

  getVendor: (name: string) =>
    request<VendorDetail>(`/vendors/${encodeURIComponent(name)}`),

  scanVendor: (name: string) =>
    request<{ vendor: string; score: number; signals: number; run_id: number }>(
      `/vendors/${encodeURIComponent(name)}/scan`,
      { method: "POST" }
    ),

  scanAll: () =>
    request<{ message: string; vendors: string[] }>("/scan/all", { method: "POST" }),

  getAlerts: (since?: string) => {
    const qs = since ? `?since=${since}` : "";
    return request<AlertsResponse>(`/alerts${qs}`);
  },

  getUnblockedProof: (url?: string) => {
    const qs = url ? `?url=${encodeURIComponent(url)}` : "";
    return request<BlockedProof>(`/proof/unblocked${qs}`);
  },
};
