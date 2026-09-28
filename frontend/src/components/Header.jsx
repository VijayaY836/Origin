function Mark() {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true">
      <circle cx="13" cy="13" r="11" fill="none" stroke="#2458E6" strokeWidth="2.5" />
      <circle cx="13" cy="13" r="4.5" fill="#C76A00" />
      <circle cx="13" cy="2.5" r="2.5" fill="#0B8A5F" />
    </svg>
  );
}

export default function Header({ plant, health, memoryOn, setMemoryOn, onReset, busy }) {
  const backend = health?.memory_backend;
  return (
    <header className="shrink-0 border-b border-line bg-surface">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 px-4 py-2">
        <div className="flex items-center gap-2.5">
          <Mark />
          <span className="font-display text-[22px] font-bold tracking-[0.06em]">ORIGIN</span>
          <span className="hidden border-l border-line pl-3 text-sm text-ink-2 md:inline">
            {plant ? `${plant.plant_name}, ${plant.location}` : "Loading plant…"}
          </span>
        </div>

        <div className="ml-auto flex flex-wrap items-center gap-3">
          <span className={`chip gap-1.5 ${backend === "hindsight" ? "bg-hs-soft text-hs" : backend === "local" ? "bg-fault-soft text-fault" : "bg-sunk text-ink-3"}`}
            title={health ? `Bank: ${health.bank_id}, LLM: ${health.llm}` : ""}>
            <span className={`h-1.5 w-1.5 rounded-full ${backend === "hindsight" ? "bg-hs" : backend === "local" ? "bg-fault" : "bg-ink-3"}`} />
            {backend === "hindsight" ? "Hindsight memory connected" : backend === "local" ? "Local fallback memory" : "Connecting"}
          </span>

          <div role="group" aria-label="Memory mode" className="flex rounded border border-line bg-sunk p-0.5 text-sm">
            <button onClick={() => setMemoryOn(true)} aria-pressed={memoryOn} disabled={busy}
              className={`rounded-sm px-3 py-1 font-semibold ${memoryOn ? "bg-mem text-white shadow-panel" : "text-ink-2 hover:text-ink"}`}>
              Memory on
            </button>
            <button onClick={() => setMemoryOn(false)} aria-pressed={!memoryOn} disabled={busy}
              className={`rounded-sm px-3 py-1 font-semibold ${!memoryOn ? "bg-fault text-white shadow-panel" : "text-ink-2 hover:text-ink"}`}>
              Amnesia mode
            </button>
          </div>

          <button onClick={onReset} disabled={busy} className="text-xs font-semibold text-ink-3 hover:text-ink">Reset demo</button>
        </div>
      </div>
      {backend === "local" && (
        <p className="border-t border-fault-mid bg-fault-soft px-4 py-1.5 text-xs text-fault">
          Hindsight is not connected, so ORIGIN is using a local keyword index. Add HINDSIGHT_API_KEY to backend/.env and restart the backend.
        </p>
      )}
    </header>
  );
}