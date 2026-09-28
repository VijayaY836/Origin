import { useEffect, useState } from "react";

export default function TracePanel({ result, revealed, backend }) {
  const [open, setOpen] = useState(null);
  useEffect(() => setOpen(null), [result]);
  const trace = result?.mode === "memory" ? result.trace : [];
  const step = open !== null ? trace[open] : null;

  return (
    <section className="panel relative shrink-0" aria-label="Memory trace">
      <div className="flex items-stretch gap-3 px-3 py-2">
        <div className="flex w-[118px] shrink-0 flex-col justify-center">
          <h2 className="h-label leading-tight">Memory trace</h2>
          <p className="text-[11px] leading-tight text-ink-3">{backend === "hindsight" ? "Live Hindsight calls" : "Local fallback"}</p>
        </div>
        {!trace.length ? (
          <p className="self-center text-sm text-ink-3">
            {result?.mode === "amnesia" ? "Amnesia mode made no memory calls." : "Each step ORIGIN takes through the plant's memory appears here. Click a step for details."}
          </p>
        ) : (
          <ol className="grid min-w-0 flex-1 grid-cols-3 gap-1.5 md:grid-cols-6">
            {trace.map((t, i) => {
              const on = i < revealed;
              return (
                <li key={t.op + i} className="min-w-0">
                  <button disabled={!on} onClick={() => setOpen(open === i ? null : i)} aria-expanded={open === i}
                    className={`h-full w-full rounded border px-2 py-1.5 text-left transition-colors ${
                      !on ? "border-dashed border-line bg-surface" :
                      open === i ? "border-hs bg-hs-soft" : "border-line bg-sunk hover:border-hs"}`}>
                    <span className={`block font-display text-[13px] font-bold tracking-wide ${!on ? "text-ink-3/50" : t.op === "INSIGHT" ? "text-warn" : "text-hs"}`}>
                      {i + 1}. {t.op}
                    </span>
                    <span className={`line-clamp-2 text-[11px] leading-snug ${on ? "text-ink-2" : "text-transparent"}`}>{t.text}</span>
                  </button>
                </li>
              );
            })}
          </ol>
        )}
      </div>

      {step && (
        <div className="anim-rise absolute bottom-full left-0 right-0 z-20 mb-2 max-h-[45vh] overflow-y-auto rounded-md border border-hs/40 bg-surface p-4 text-xs text-ink shadow-lg">
          <div className="mb-2 flex items-center justify-between">
            <p className="font-display text-sm font-bold text-hs">{step.op}: {step.text}</p>
            <button onClick={() => setOpen(null)} className="text-ink-3 hover:text-ink" aria-label="Close details">Close</button>
          </div>
          {step.note && <p className="mb-2 text-warn">{step.note}</p>}
          {step.op === "RECALL" ? (
            <table className="w-full text-left">
              <thead className="text-ink-3"><tr><th className="py-1 pr-4 font-semibold">Query</th><th className="pr-4 font-semibold">Scope</th><th className="pr-4 font-semibold">Memories</th><th className="font-semibold">Records</th></tr></thead>
              <tbody>
                {step.detail.map((q) => (
                  <tr key={q.label} className="border-t border-line align-top">
                    <td className="py-1 pr-4">{q.query}</td>
                    <td className="pr-4 text-ink-2">{q.tags ? q.tags.join(", ") : "whole plant"}</td>
                    <td className="pr-4 font-semibold text-hs">{q.memories}</td>
                    <td className="text-ink-2">{q.records.join(", ") || "none"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <ul className="space-y-1">{(step.detail || [step.text]).map((d, j) => <li key={j} className="whitespace-pre-line">{d}</li>)}</ul>
          )}
        </div>
      )}
    </section>
  );
}