import { useEffect, useRef } from "react";
import { fmtDate, OUTCOME } from "../api";

const SEARCH_STEPS = [
  "Recalling this machine and its sibling presses",
  "Matching symptoms and error codes",
  "Comparing earlier fixes and what happened after",
  "Checking parts, oil suppliers and batches",
  "Excluding coincidences",
  "Evaluating recurrence",
];

const daysBetween = (a, b) => Math.floor((new Date(b) - new Date(a)) / 86400000);

function Searching() {
  return (
    <div className="p-5">
      <p className="font-display text-lg font-semibold text-mem">Searching plant memory…</p>
      <ol className="mt-3 space-y-1.5">
        {SEARCH_STEPS.map((s, i) => (
          <li key={s} className="anim-rise text-sm text-ink-2" style={{ animationDelay: `${i * 0.3}s` }}>
            <span className="mr-2 text-ink-3">{i + 1}.</span>{s}
          </li>
        ))}
      </ol>
    </div>
  );
}

function Shell({ children, right, footer, bodyRef }) {
  return (
    <section className="panel flex min-h-0 flex-col" aria-label="Investigation timeline">
      <div className="panel-head">
        <h2 className="h-label">Investigation timeline</h2>
        {right}
      </div>
      <div ref={bodyRef} className="scroll-y min-h-0 flex-1">{children}</div>
      {footer}
    </section>
  );
}

export default function Timeline({ result, shown, loading }) {
  const bodyRef = useRef(null);
  const connectedNow = shown.has("CONNECT");
  useEffect(() => {
    // Once the pattern is connected, bring today's breakdown into view.
    const el = bodyRef.current;
    if (connectedNow && el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [connectedNow]);
  if (loading) return <Shell><Searching /></Shell>;
  if (!result || result.mode !== "memory") {
    return (
      <Shell>
        <div className="flex h-full items-center justify-center p-8">
          <p className="max-w-xs text-center text-sm leading-relaxed text-ink-3">
            {result?.mode === "amnesia"
              ? "Amnesia mode has no history to show. Every breakdown looks like the first one."
              : "Related breakdowns from the plant's memory will line up here, oldest first, with what was tried each time."}
          </p>
        </div>
      </Shell>
    );
  }

  const ev = result.evidence;
  const connected = shown.has("CONNECT");
  const excludedShown = shown.has("EXCLUDE");
  const reflected = shown.has("REFLECT");
  const visible = shown.has("RECALL");
  const primary = ev.primary;
  const inPattern = (n) => n.type === "incident" || n.type === "current" || (n.type === "event" && primary?.supplier_change?.event_id === n.id);
  let lastPatternDate = null;

  const legend = visible && (
    <div className="flex items-center gap-3 text-[11px] text-ink-3">
      <span>{ev.related_ids.length} related, {ev.excluded.length} set aside</span>
      <span className="hidden items-center gap-1 lg:flex"><span className="h-2 w-2 rounded-full bg-mem" />pattern</span>
      <span className="hidden items-center gap-1 lg:flex"><span className="h-2 w-2 rounded-full bg-ink-3/40" />set aside</span>
    </div>
  );

  const footer = connected && primary && (
    <div className="anim-rise border-t border-mem-mid bg-mem-soft px-4 py-2.5">
      <p className="font-display text-[17px] font-semibold leading-tight text-mem">
        ORIGIN connects the dots: {primary.label}, present in {primary.count} of {primary.total} breakdowns.
      </p>
    </div>
  );

  return (
    <Shell right={legend} footer={footer} bodyRef={bodyRef}>
      {!visible ? <Searching /> : (
        <ol className="px-4 py-2.5">
          {ev.timeline.map((n, i) => {
            const pat = inPattern(n);
            const isInc = n.type === "incident" || n.type === "current";
            const gap = pat && isInc && lastPatternDate ? daysBetween(lastPatternDate, n.date) : null;
            if (pat && isInc) lastPatternDate = n.date;
            const lit = connected && pat;
            const dim = n.type === "excluded" && excludedShown;
            const oilMatch = connected && primary && n.oil && n.oil.supplier === primary.short;
            const current = n.type === "current";
            return (
              <li key={n.id} className="anim-rise grid grid-cols-[56px_14px_1fr] gap-x-2.5" style={{ animationDelay: `${i * 0.06}s` }}>
                <div className="pt-1 text-right leading-none">
                  <p className={`whitespace-nowrap font-display text-[15px] font-semibold ${dim ? "text-ink-3" : "text-ink"}`}>{fmtDate(n.date)}</p>
                  {gap > 0 && <p className={`mt-0.5 text-[10px] ${lit ? "text-mem" : "text-ink-3"}`}>+{gap}d</p>}
                </div>
                <div className="relative flex justify-center">
                  <span className={`absolute inset-y-0 w-[2px] ${lit ? "anim-draw bg-mem" : "bg-line"}`} />
                  <span className={`relative mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-surface ${
                    current ? (n.warning_only ? "bg-warn" : "bg-fault") :
                    n.type === "event" ? (lit ? "bg-mem" : "bg-ink-3") :
                    n.type === "note" ? "bg-hs" :
                    dim ? "bg-line" : lit ? "bg-mem" : "bg-ink-3"}`} />
                </div>

                <div className={`min-w-0 pb-1.5 ${dim ? "opacity-60" : ""}`}>
                  {n.type === "event" && (
                    <div className={`rounded border px-2.5 py-1 ${lit ? "border-mem-mid bg-mem-soft" : "border-line bg-sunk"}`}>
                      <p className={`text-sm font-semibold ${lit ? "text-mem" : "text-ink"}`}>{n.title}</p>
                      <p className="truncate text-xs text-ink-2" title={n.detail}>{n.detail}</p>
                    </div>
                  )}
                  {n.type === "note" && (
                    <p className="truncate py-0.5 text-xs italic text-hs" title={n.detail}>{n.title}: “{n.detail}”</p>
                  )}
                  {n.type === "excluded" && (
                    <div className="flex min-w-0 items-baseline gap-2 rounded border border-line bg-surface px-2.5 py-1" title={n.reason}>
                      <span className="shrink-0 font-display text-[14px] font-bold">{n.machine_id}</span>
                      <span className="shrink-0 text-[11px] text-ink-3">{n.id}</span>
                      <span className={`truncate text-xs ${dim ? "line-through text-ink-2" : "text-ink-2"}`}>{n.symptoms[0]}</span>
                      {dim && (
                        <span className="chip ml-auto shrink-0 bg-sunk text-ink-2">
                          {n.kind === "explained_by_event" ? "Set aside: power event" : "Set aside: different system"}
                        </span>
                      )}
                    </div>
                  )}
                  {isInc && (
                    <div className={`rounded border px-2.5 py-1 ${
                      current ? (n.warning_only ? "border-warn-mid bg-warn-soft" : "border-fault-mid bg-fault-soft") : "border-line bg-surface"}`}>
                      <div className="flex min-w-0 items-baseline gap-2">
                        <span className="shrink-0 font-display text-[15px] font-bold">{n.machine_id}</span>
                        <span className="shrink-0 text-[11px] text-ink-3">{n.id}</span>
                        {current
                          ? <span className={`truncate text-xs font-semibold ${n.warning_only ? "text-warn" : "text-fault"}`}>Today: {n.symptoms[0]}</span>
                          : <span className="truncate text-sm" title={n.title}>{n.title}</span>}
                      </div>
                      <div className="mt-0.5 flex flex-wrap gap-1">
                        {n.oil && (
                          <span className={`chip ${oilMatch ? "bg-mem text-white" : "bg-sunk text-ink-2"}`}>Oil: {n.oil.supplier}, {n.oil.batch}</span>
                        )}
                        {reflected && n.outcome && (
                          <span className={`chip ${OUTCOME[n.outcome.label].cls}`}>
                            {OUTCOME[n.outcome.label].name}
                            {n.outcome.days_until_recurrence != null && `, back in ${n.outcome.days_until_recurrence} days`}
                            {n.outcome.label === "unknown" && n.outcome.days_observed != null && `, ${n.outcome.days_observed} days observed`}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </Shell>
  );
}