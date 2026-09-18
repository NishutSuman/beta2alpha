async function J(r) {
  if (!r.ok) {
    let detail;
    try { detail = (await r.json()).detail; } catch { /* ignore */ }
    throw new Error(detail || `HTTP ${r.status}`);
  }
  return r.json();
}

export const api = {
  analysis: (account = 5000, riskPct = 0.5) =>
    fetch(`/api/analysis?account=${account}&risk_pct=${riskPct}`).then(J),
  config: () => fetch("/api/config").then(J),
  candles: (tf = "15m", count = 200) => fetch(`/api/candles?tf=${tf}&count=${count}`).then(J),
  testAlert: () => fetch("/api/test-alert", { method: "POST" }).then(J),
  trades: () => fetch("/api/trades").then(J),
  createTrade: (body) =>
    fetch("/api/trades", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(J),
  closeTrade: (id, body) =>
    fetch(`/api/trades/${id}/close`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(J),
  ledger: () => fetch("/api/ledger").then(J),
  saveLedger: (body) =>
    fetch("/api/ledger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(J),
};
