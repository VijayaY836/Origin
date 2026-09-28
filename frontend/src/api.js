async function call(path, opts = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try { msg = (await res.json()).detail || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export const api = {
  health: () => call("/health"),
  plant: () => call("/plant"),
  loadToday: () => call("/demo/load-today", { method: "POST" }),
  createIncident: (body) => call("/incidents", { method: "POST", body }),
  investigate: (id, memory) => call(`/investigate/${id}?memory=${memory}`, { method: "POST" }),
  checkFix: (incident_id, proposed_fix) => call("/check-fix", { method: "POST", body: { incident_id, proposed_fix } }),
  confirm: (id, body) => call(`/confirm/${id}`, { method: "POST", body }),
  advance: () => call("/demo/advance", { method: "POST" }),
  reset: () => call("/demo/reset", { method: "POST" }),
};

export function fmtDate(ts, withTime = false) {
  const d = new Date(ts);
  const opts = { day: "numeric", month: "short", timeZone: "Asia/Kolkata" };
  if (withTime) Object.assign(opts, { hour: "2-digit", minute: "2-digit", hour12: false });
  return d.toLocaleString("en-IN", opts);
}

export function fmtINR(n) {
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(1)} crore`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(n % 1e5 === 0 ? 0 : 1)} lakh`;
  return `₹${n.toLocaleString("en-IN")}`;
}

export const GRADE = {
  confirmed: { name: "Confirmed root cause", cls: "bg-ok text-white" },
  strong: { name: "Strong recurring pattern", cls: "bg-warn text-white" },
  possible: { name: "Possible contributing factor", cls: "bg-mem-soft text-mem" },
  hypothesis: { name: "Hypothesis, needs investigation", cls: "border border-dashed border-ink-3 text-ink-2" },
  ruled_out: { name: "Ruled out, coincidental", cls: "bg-sunk text-ink-3" },
};

export const OUTCOME = {
  temporary: { name: "Temporary", cls: "bg-warn-soft text-warn" },
  ineffective: { name: "Ineffective", cls: "bg-fault-soft text-fault" },
  permanent: { name: "Permanent", cls: "bg-ok-soft text-ok" },
  unknown: { name: "Too early to tell", cls: "bg-sunk text-ink-3" },
};