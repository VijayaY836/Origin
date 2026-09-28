import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import Header from "./components/Header";
import IncidentPanel from "./components/IncidentPanel";
import Timeline from "./components/Timeline";
import AnalysisPanel from "./components/AnalysisPanel";
import TracePanel from "./components/TracePanel";

const STEP_MS = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 700;

export default function App() {
  const [plant, setPlant] = useState(null);
  const [health, setHealth] = useState(null);
  const [memoryOn, setMemoryOn] = useState(true);
  const [incident, setIncident] = useState(null);
  const [result, setResult] = useState(null);
  const [revealed, setRevealed] = useState(0);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [decided, setDecided] = useState(null);
  const [advanced, setAdvanced] = useState(false);
  const [error, setError] = useState("");
  const timer = useRef();

  useEffect(() => {
    api.plant().then(setPlant).catch(() => setError("Cannot reach the ORIGIN backend on port 8000. Is it running?"));
    api.health().then(setHealth).catch(() => {});
  }, []);

  useEffect(() => {
    clearInterval(timer.current);
    if (result?.mode !== "memory") return;
    if (!STEP_MS) { setRevealed(result.trace.length); return; }
    setRevealed(1);
    timer.current = setInterval(() => {
      setRevealed((r) => {
        if (r >= result.trace.length) { clearInterval(timer.current); return r; }
        return r + 1;
      });
    }, STEP_MS);
    return () => clearInterval(timer.current);
  }, [result]);

  const shown = new Set(result?.mode === "memory" ? result.trace.slice(0, revealed).map((t) => t.op) : []);

  const guard = async (fn) => {
    setError(""); setBusy(true);
    try { await fn(); } catch (e) { setError(e.message); }
    setBusy(false);
  };

  const investigate = (inc = incident, mem = memoryOn) => guard(async () => {
    setLoading(true); setResult(null); setRevealed(0);
    try { setResult(await api.investigate(inc.incident_id, mem)); }
    finally { setLoading(false); }
  });

  const loadToday = () => guard(async () => {
    const inc = await api.loadToday();
    setIncident(inc); setResult(null); setDecided(null); setAdvanced(false);
  });

  const onCreated = (inc) => { setIncident(inc); setResult(null); setDecided(null); };

  const onConfirm = (body) => guard(async () => setDecided(await api.confirm(incident.incident_id, body)));

  const onAdvance = () => guard(async () => {
    const inc = await api.advance();
    setIncident(inc); setDecided(null); setAdvanced(true); setMemoryOn(true);
    setLoading(true); setResult(null); setRevealed(0);
    try { setResult(await api.investigate(inc.incident_id, true)); } finally { setLoading(false); }
  });

  const onReset = () => guard(async () => {
    await api.reset();
    setIncident(null); setResult(null); setDecided(null); setAdvanced(false); setMemoryOn(true);
  });

  const toggleMemory = (on) => {
    setMemoryOn(on);
    setResult(null); setRevealed(0);
  };

  return (
    <div className="flex min-h-screen flex-col lg:h-screen lg:overflow-hidden">
      <Header plant={plant} health={health} memoryOn={memoryOn} setMemoryOn={toggleMemory} onReset={onReset} busy={busy} />
      {error && <p role="alert" className="shrink-0 border-b border-fault-mid bg-fault-soft px-4 py-1.5 text-sm text-fault">{error}</p>}
      <main className="grid min-h-0 flex-1 grid-cols-1 gap-3 p-3 pb-0 lg:grid-cols-[290px_minmax(0,1fr)_380px] [&>*]:min-h-[360px] lg:[&>*]:min-h-0">
        <IncidentPanel incident={incident} memoryOn={memoryOn} onLoadToday={loadToday} onCreated={onCreated}
          onInvestigate={() => investigate()} busy={busy} investigated={!!result} />
        <Timeline result={result} shown={shown} loading={loading} />
        <AnalysisPanel result={result} shown={shown} loading={loading} onConfirm={onConfirm} decided={decided}
          onAdvance={onAdvance} busy={busy} canAdvance={!advanced} />
      </main>
      <div className="shrink-0 p-3">
        <TracePanel result={result} revealed={revealed} backend={health?.memory_backend} />
      </div>
    </div>
  );
}