import { useEffect, useState } from "react";
import { fmtINR, GRADE } from "../api";

function Shell({ title, children, footer }) {
  return (
    <section className="panel flex min-h-0 flex-col" aria-label="ORIGIN analysis">
      <div className="panel-head"><h2 className="h-label">{title}</h2></div>
      <div className="flex min-h-0 flex-1 flex-col">{children}</div>
      {footer}
    </section>
  );
}

function Amnesia({ answer }) {
  return (
    <div className="scroll-y anim-rise flex-1 space-y-4 p-4">
      <div className="rounded border-l-[3px] border-fault bg-fault-soft px-3 py-2">
        <p className="text-sm font-semibold text-fault">No plant history</p>
        <p className="mt-0.5 text-sm leading-snug text-ink">{answer.summary}</p>
      </div>
      <div>
        <h3 className="text-xs font-semibold text-ink-2">Likely causes</h3>
        <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm">{answer.likely_causes.map((c) => <li key={c}>{c}</li>)}</ul>
      </div>
      <div>
        <h3 className="text-xs font-semibold text-ink-2">Suggested fixes</h3>
        <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm">{answer.suggested_fixes.map((c) => <li key={c}>{c}</li>)}</ul>
      </div>
      <p className="border-t border-line pt-3 text-xs leading-relaxed text-ink-3">
        Reasonable advice for any press. Turn memory on to see which of these this plant has already tried.
      </p>
    </div>
  );
}

function Decision({ primary, onConfirm, decided, onAdvance, busy, canAdvance }) {
  const [note, setNote] = useState("Lab test: oil sold as ISO VG 68 measured close to ISO VG 32, too thin for the presses.");
  if (decided) {
    return (
      <div className="anim-rise border-t border-ok-mid bg-ok-soft px-4 py-3">
        <p className="text-sm font-semibold text-ok">
          {decided.decision === "confirmed" ? "Root cause confirmed and saved to plant memory"
            : decided.decision === "rejected" ? "Rejection saved to plant memory" : "Marked as still investigating"}
        </p>
        <p className="text-xs text-ink-2">{decided.confirmation_id}. Every future investigation will use this decision.</p>
        {canAdvance && decided.decision === "confirmed" && (
          <button className="btn-primary mt-2 w-full" onClick={onAdvance} disabled={busy}>Jump ahead to 19 June</button>
        )}
      </div>
    );
  }
  const send = (decision) => onConfirm({ decision, factor_key: primary.key, factor_label: primary.label, note });
  return (
    <div className="anim-rise space-y-1.5 border-t border-line bg-sunk px-4 py-2.5">
      <label htmlFor="note" className="text-xs font-semibold text-ink-2">Engineer decision</label>
      <input id="note" className="field py-1.5 text-xs" value={note} onChange={(e) => setNote(e.target.value)} />
      <div className="flex gap-2">
        <button className="btn flex-1 bg-ok text-white hover:bg-[#08744f]" disabled={busy} onClick={() => send("confirmed")}>Confirm root cause</button>
        <button className="btn-ghost" disabled={busy} onClick={() => send("rejected")}>Reject</button>
        <button className="btn-ghost" disabled={busy} onClick={() => send("investigating")} title="Still investigating">Later</button>
      </div>
    </div>
  );
}

function Stat({ value, label, tone }) {
  return (
    <div className="rounded bg-sunk px-2 py-1.5">
      <p className={`font-display text-lg font-bold leading-none ${tone}`}>{value}</p>
      <p className="mt-0.5 text-[11px] leading-tight text-ink-2">{label}</p>
    </div>
  );
}

export default function AnalysisPanel({ result, shown, loading, onConfirm, decided, onAdvance, busy, canAdvance }) {
  const [tab, setTab] = useState("evidence");
  useEffect(() => setTab("evidence"), [result]);

  if (loading || !result) {
    return (
      <Shell title="ORIGIN analysis">
        <p className="p-4 text-sm leading-relaxed text-ink-3">
          {loading ? "Reading the plant's history…" : "Run an investigation to see the likely root cause, the evidence behind it and what not to try again."}
        </p>
      </Shell>
    );
  }
  if (result.mode === "amnesia") return <Shell title="Analysis without memory"><Amnesia answer={result.answer} /></Shell>;

  const ev = result.evidence;
  const p = ev.primary;
  const ruled = ev.factors.filter((f) => f.grade === "ruled_out");
  const connected = shown.has("CONNECT");
  const excluded = shown.has("EXCLUDE");
  const insight = shown.has("INSIGHT");
  const temp = ev.fix_history.filter((f) => ["temporary", "ineffective"].includes(f.outcome.label)).length;

  const tabs = [
    { id: "evidence", label: "Evidence", ready: connected },
    { id: "ruled", label: `Ruled out${excluded ? ` (${ruled.length + ev.excluded.length})` : ""}`, ready: excluded },
    { id: "brief", label: "Brief", ready: insight, dot: insight && tab !== "brief" },
  ];

  const footer = insight && p && p.grade !== "confirmed"
    ? <Decision primary={p} onConfirm={onConfirm} decided={decided} onAdvance={onAdvance} busy={busy} canAdvance={canAdvance} />
    : null;

  return (
    <Shell title="ORIGIN analysis" footer={footer}>
      {!connected && <p className="p-4 text-sm text-ink-3">Connecting related breakdowns…</p>}
      {connected && !p && <p className="p-4 text-sm text-ink-2">No factor recurs strongly enough yet. ORIGIN keeps this breakdown in memory and will learn from its outcome.</p>}
      {connected && p && (
        <>
          <div className="anim-rise space-y-1.5 px-4 pt-3">
            <div className="flex flex-wrap gap-1.5">
              <span className={`chip ${GRADE[p.grade].cls}`}>{GRADE[p.grade].name}</span>
              {ev.preventive && <span className="chip bg-ok-soft text-ok">Caught before a breakdown</span>}
            </div>
            <p className="font-display text-[22px] font-bold leading-tight">{p.label}</p>
            <p className="text-[13px] leading-snug text-ink-2">{p.why}</p>
            <div className="grid grid-cols-3 gap-1.5 pt-1">
              <Stat value={`${p.count}/${p.total}`} label={`breakdowns, ${p.machines.length} machines`} tone="text-mem" />
              <Stat value={temp} label="earlier fixes only temporary" tone="text-warn" />
              <Stat value={ev.cost.inr ? fmtINR(ev.cost.inr).replace(" lakh", "L") : "₹0"} label="downtime cost so far" tone="text-fault" />
            </div>
          </div>

          <div role="tablist" className="mt-2.5 flex gap-4 border-b border-line px-4">
            {tabs.map((t) => (
              <button key={t.id} role="tab" aria-selected={tab === t.id} disabled={!t.ready} onClick={() => setTab(t.id)}
                className={`relative -mb-px border-b-2 pb-1.5 text-sm font-semibold disabled:text-ink-3/60 ${tab === t.id ? "border-mem text-mem" : "border-transparent text-ink-2 hover:text-ink"}`}>
                {t.label}
                {t.dot && <span className="absolute -right-2 top-0 h-1.5 w-1.5 rounded-full bg-warn" />}
              </button>
            ))}
          </div>

          <div className="scroll-y min-h-0 flex-1 px-4 py-3">
            {tab === "evidence" && (
              <ul className="space-y-2 text-[13px] leading-snug">
                {p.evidence.map((e) => <li key={e} className="border-l-2 border-mem pl-2.5">{e}</li>)}
                {p.batches?.length > 0 && <li className="text-xs text-ink-3">Batches: {p.batches.join(", ")}</li>}
              </ul>
            )}
            {tab === "ruled" && (
              <ul className="space-y-2.5 text-[13px] leading-snug">
                {ruled.map((f) => (
                  <li key={f.key}>
                    <p><span className="font-semibold text-ink-2 line-through">{f.label}</span> <span className="chip bg-sunk text-ink-3">{f.count} of {f.total}, coincidental</span></p>
                    <p className="mt-0.5 text-xs text-ink-2">{f.why}</p>
                  </li>
                ))}
                {ev.excluded.map((e) => (
                  <li key={e.incident_id}>
                    <p><span className="font-semibold text-ink-2 line-through">{e.incident_id} on {e.machine_id}</span></p>
                    <p className="mt-0.5 text-xs text-ink-2">{e.reason}</p>
                  </li>
                ))}
              </ul>
            )}
            {tab === "brief" && (
              <div className="space-y-2.5 text-[13px] leading-snug">
                <p className="text-sm font-semibold">{result.brief.headline}</p>
                <p className="text-ink-2">{result.brief.summary}</p>
                <ol className="list-decimal space-y-1 pl-5">{result.brief.next_steps.map((s) => <li key={s}>{s}</li>)}</ol>
                {ev.cost.downtime_minutes > 0 && (
                  <p className="text-ink-2">So far: {Math.round(ev.cost.downtime_minutes / 60)} hours of downtime, {ev.cost.units_lost.toLocaleString("en-IN")} parts not made, {fmtINR(ev.cost.inr)}.</p>
                )}
                {result.reflection && (
                  <details className="rounded bg-hs-soft px-2.5 py-2">
                    <summary className="cursor-pointer text-xs font-semibold text-hs">Hindsight reflection</summary>
                    <p className="mt-1.5 whitespace-pre-line text-xs text-ink">{result.reflection}</p>
                  </details>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </Shell>
  );
}