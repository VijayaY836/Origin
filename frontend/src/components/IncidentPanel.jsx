import { useEffect, useRef, useState } from "react";
import { api, fmtDate, OUTCOME } from "../api";

const MACHINES = ["HP-02", "HP-04", "HP-06", "CNC-11", "CNC-12", "IM-03", "CV-01", "AC-01"];

function NewIncidentForm({ onCreated, onCancel }) {
  const [machine, setMachine] = useState("HP-04");
  const [symptoms, setSymptoms] = useState("");
  const [codes, setCodes] = useState("");
  const [notes, setNotes] = useState("");
  const [err, setErr] = useState("");
  const submit = async () => {
    const s = symptoms.split(",").map((x) => x.trim()).filter(Boolean);
    if (!s.length) return setErr("Add at least one symptom, separated by commas.");
    try {
      onCreated(await api.createIncident({
        machine_id: machine, symptoms: s, technician_notes: notes,
        error_codes: codes.split(",").map((x) => x.trim().toUpperCase()).filter(Boolean),
      }));
    } catch (e) { setErr(e.message); }
  };
  return (
    <div className="space-y-2.5">
      <label className="block text-xs font-semibold text-ink-2">Machine
        <select value={machine} onChange={(e) => setMachine(e.target.value)} className="field mt-1">
          {MACHINES.map((m) => <option key={m}>{m}</option>)}
        </select>
      </label>
      <label className="block text-xs font-semibold text-ink-2">Symptoms
        <input className="field mt-1" value={symptoms} onChange={(e) => setSymptoms(e.target.value)} placeholder="oil temperature 72°C, cycle time +15%" />
      </label>
      <label className="block text-xs font-semibold text-ink-2">Error codes
        <input className="field mt-1" value={codes} onChange={(e) => setCodes(e.target.value)} placeholder="HYD-TEMP-HI, PRV-NOISE" />
      </label>
      <label className="block text-xs font-semibold text-ink-2">Technician notes
        <textarea className="field mt-1" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </label>
      {err && <p className="text-xs text-fault">{err}</p>}
      <div className="flex gap-2">
        <button className="btn-primary" onClick={submit}>Log breakdown</button>
        <button className="btn-ghost" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}

function FixCheck({ incident, enabled }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [checking, setChecking] = useState(false);
  const timer = useRef();
  useEffect(() => { setText(""); setResult(null); }, [incident?.incident_id]);
  useEffect(() => {
    clearTimeout(timer.current);
    if (!enabled || text.trim().length < 3) { setResult(null); return; }
    timer.current = setTimeout(async () => {
      setChecking(true);
      try { setResult(await api.checkFix(incident.incident_id, text)); } catch { setResult(null); }
      setChecking(false);
    }, 550);
    return () => clearTimeout(timer.current);
  }, [text, enabled, incident?.incident_id]);

  const w = result?.warnings?.[0];
  return (
    <div className="border-t border-line pt-2.5">
      <label htmlFor="fix" className="h-label">Proposed fix</label>
      <input id="fix" className="field mt-1.5" value={text} onChange={(e) => setText(e.target.value)}
        placeholder={enabled ? "What are you about to try?" : "Turn memory on to check fixes"} disabled={!enabled} />
      {checking && <p className="mt-1.5 text-xs text-ink-3">Checking what the plant tried before…</p>}
      {w && (
        <div className="anim-warn mt-2 rounded border border-warn-mid bg-warn-soft p-2.5 text-[13px]">
          <p className="font-semibold text-warn">Previously attempted</p>
          <p className="mt-0.5 leading-snug text-ink">
            “{w.fix}”, {w.machine_id}, {fmtDate(w.date)}.{" "}
            {w.outcome.label === "temporary" && <>Came back after {w.outcome.days_until_recurrence} days.</>}
            {w.outcome.label === "unknown" && <>Too early to know if it held.</>}
            {w.outcome.label === "ineffective" && <>It did not stop the problem.</>}
          </p>
          <p className="mt-1 text-xs text-ink-2">
            <span className={`chip mr-1 ${OUTCOME[w.outcome.label].cls}`}>{OUTCOME[w.outcome.label].name}</span>
            Treats a symptom, not the pattern.
            {result.warnings.length > 1 && ` Tried ${result.warnings.length} times in total.`}
          </p>
        </div>
      )}
      {result && !w && !checking && <p className="mt-1.5 text-xs text-ok">Not tried on this pattern before.</p>}
    </div>
  );
}

export default function IncidentPanel({ incident, memoryOn, onLoadToday, onCreated, onInvestigate, busy, investigated }) {
  const [logging, setLogging] = useState(false);

  if (!incident) {
    return (
      <section className="panel flex min-h-0 flex-col" aria-label="Current incident">
        <div className="panel-head"><h2 className="h-label">Current incident</h2></div>
        <div className="scroll-y flex-1 p-4">
          {logging ? (
            <NewIncidentForm onCreated={(i) => { setLogging(false); onCreated(i); }} onCancel={() => setLogging(false)} />
          ) : (
            <div className="space-y-3">
              <p className="text-sm leading-relaxed text-ink-2">No breakdown open. Load tonight's call from Stamping Line 1, or log a new one.</p>
              <button className="btn-primary w-full" onClick={onLoadToday} disabled={busy}>Load tonight's breakdown</button>
              <button className="btn-ghost w-full" onClick={() => setLogging(true)} disabled={busy}>Log a breakdown</button>
            </div>
          )}
        </div>
      </section>
    );
  }

  const warningOnly = incident.error_codes?.some((c) => c.endsWith("WARN"));
  return (
    <section className="panel flex min-h-0 flex-col" aria-label="Current incident">
      <div className="panel-head">
        <h2 className="h-label">Current incident</h2>
        <span className="text-xs text-ink-3">{incident.incident_id}</span>
      </div>
      <div className="scroll-y flex-1 space-y-2.5 p-3.5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-display text-[40px] font-bold leading-none">{incident.machine_id}</p>
            <p className="mt-1 text-xs text-ink-2">{incident.line}, Shift {incident.shift}</p>
            <p className="text-xs text-ink-2">{fmtDate(incident.timestamp, true)}</p>
          </div>
          <span className={`chip mt-1 ${warningOnly ? "bg-warn-soft text-warn" : "bg-fault text-white"}`}>
            {warningOnly ? "Early warning" : "Line stopped"}
          </span>
        </div>
        <ul className={`space-y-0.5 rounded border-l-[3px] py-1.5 pl-2.5 text-[13px] leading-snug ${warningOnly ? "border-warn bg-warn-soft" : "border-fault bg-fault-soft"}`}>
          {incident.symptoms.map((s) => <li key={s}>{s}</li>)}
          <li className="pt-0.5 text-[11px] text-ink-2">{incident.error_codes.join(", ")}</li>
        </ul>
        {incident.technician_notes && <p className="line-clamp-2 text-[13px] italic leading-snug text-ink-2">“{incident.technician_notes}”</p>}

        <button className={`w-full ${memoryOn ? "btn-primary" : "btn bg-fault text-white hover:bg-[#b82a3f]"}`} onClick={onInvestigate} disabled={busy}>
          {busy ? "Working…" : memoryOn ? (investigated ? "Investigate again" : "Investigate with plant memory") : "Analyze without memory"}
        </button>

        <FixCheck incident={incident} enabled={memoryOn} />
      </div>
    </section>
  );
}