"""The investigation pipeline: RETAIN -> RECALL -> CONNECT -> EXCLUDE -> REFLECT -> INSIGHT."""
import asyncio
import json
import time

from . import ledger, llm
from .analysis import analyze, check_fix, fmt_date
from .config import MACHINES
from .memory import get_memory, safe
from .records import record_id

_memset_cache: dict[str, list[dict]] = {}


async def gather_memory(current: dict) -> tuple[list[dict], list[dict]]:
    """Recall everything relevant from Hindsight. Returns (records, trace_steps)."""
    mem = get_memory()
    system = current["system"]
    siblings = [m for m, info in MACHINES.items() if info["system"] == system]
    symptoms = ", ".join(current["symptoms"] + current["error_codes"])

    queries = [(f"Breakdowns, fixes, parts and hydraulic oil added on {m}", [f"machine:{m}"], f"{m} history") for m in siblings]
    queries += [
        (f"Incidents with symptoms like: {symptoms}", None, "similar symptoms, any machine"),
        (f"{system} supplier changes, procurement, handover notes and plant notes", [f"system:{system}", "kind:supplier_change", "kind:plant_note"], "plant events"),
        ("Shift patterns, operating conditions and handover notes for these machines", ["kind:plant_note", "kind:handover_note"], "plant notes"),
        (f"Engineer root cause decisions for {system} problems", ["kind:confirmation"], "past root-cause decisions"),
    ]
    t0 = time.time()
    results = await asyncio.gather(*[safe(mem.recall(q, tags=t), default=[], timeout=40) for q, t, _ in queries])
    ms = int((time.time() - t0) * 1000)

    known = ledger.known_ids()
    records: dict[str, dict] = {}
    raw_hits = 0
    per_query = []
    for (q, t, label), hits in zip(queries, results):
        raw_hits += len(hits)
        ids = []
        for h in hits:
            r = h.get("record")
            if r and record_id(r) in known:
                records[record_id(r)] = r
                ids.append(record_id(r))
        per_query.append({"label": label, "query": q, "tags": t, "memories": len(hits), "records": sorted(set(ids))})

    # Records retained seconds ago may still be indexing inside Hindsight.
    backfilled = []
    for rid in ledger.demo_ids():
        if rid not in records and rid != record_id(current):
            r = ledger.get(rid)
            if r and r["kind"] in ("confirmation", "oil_fill"):
                records[rid] = r
                backfilled.append(rid)

    recs = list(records.values())
    inc = [r for r in recs if r["kind"] == "incident"]
    other = [r for r in recs if r["kind"] != "incident"]
    step = {
        "op": "RECALL",
        "text": f"{raw_hits} memories retrieved from {len(queries)} queries in {ms} ms, pointing to {len(inc)} incidents and {len(other)} plant records",
        "detail": per_query,
    }
    if backfilled:
        step["note"] = f"{', '.join(backfilled)} retained moments ago; still indexing in Hindsight, read from the write-through index."
    return recs, [step]


async def run(incident_id: str, use_memory: bool = True) -> dict:
    current = ledger.get(incident_id)
    if not current:
        raise KeyError(incident_id)
    mem = get_memory()

    if not use_memory:
        answer = await llm.amnesia(current)
        return {"mode": "amnesia", "incident": current, "answer": answer}

    trace = [{"op": "RETAIN", "text": f"{incident_id} stored ({current['machine_id']}, {fmt_date(current['timestamp'])})"}]
    records, steps = await gather_memory(current)
    trace += steps
    _memset_cache[incident_id] = records

    ev = analyze(current, records)
    p = ev["primary"]

    if p:
        trace.append({"op": "CONNECT", "text": f"{p['label']} present in {p['count']}/{p['total']} related incidents on {', '.join(p['machines'])}",
                      "detail": p["evidence"]})
    else:
        trace.append({"op": "CONNECT", "text": f"{len(ev['related_ids'])} related incidents found; no common factor strong enough yet"})
    ruled = [f for f in ev["factors"] if f["grade"] == "ruled_out"]
    excl_text = [f"{f['short']} (coincidental)" for f in ruled] + [f"{e['incident_id']} ({'power event' if e['kind'] == 'explained_by_event' else 'different system'})" for e in ev["excluded"]]
    if excl_text:
        trace.append({"op": "EXCLUDE", "text": ", ".join(excl_text), "detail": [f["why"] for f in ruled] + [e["reason"] for e in ev["excluded"]]})

    temp = [f for f in ev["fix_history"] if f["outcome"]["label"] in ("temporary", "ineffective")]

    reflect_q = (f"Why does {current['machine_id']} keep having this problem ({', '.join(current['symptoms'])})? "
                 f"What has been tried before, did it work, and what do the incidents have in common?")
    reflect_ctx = json.dumps({"computed_evidence": p and p["evidence"], "fix_outcomes": [(f["incident_id"], f["fix"], f["outcome"]["label"]) for f in ev["fix_history"]]}, ensure_ascii=False)
    reflection, brief = await asyncio.gather(
        safe(mem.reflect(reflect_q, reflect_ctx, tags=[f"system:{current['system']}"]), default=None, timeout=45),
        llm.brief(ev),
    )
    trace.append({"op": "REFLECT", "text": f"{len(temp)} prior fix{'es' if len(temp) != 1 else ''} classified temporary"
                  + ("; Hindsight reflection complete" if reflection else ""),
                  "detail": ([reflection] if reflection else []) + [f"{f['incident_id']}: {f['fix']} → {f['outcome']['label']}" for f in ev["fix_history"]]})
    if p:
        grade_name = {"confirmed": "Confirmed root cause", "strong": "Strong recurring pattern", "possible": "Possible contributing factor", "hypothesis": "Hypothesis"}[p["grade"]]
        trace.append({"op": "INSIGHT", "text": f"{grade_name}: {p['label']}" + (" (preventive alert)" if ev["preventive"] else "")})
    else:
        trace.append({"op": "INSIGHT", "text": "No recurring root cause yet; recording this incident for future learning"})

    return {"mode": "memory", "memory_backend": mem.mode, "evidence": ev, "brief": brief, "reflection": reflection, "trace": trace}


async def fix_check(incident_id: str, proposed: str) -> dict:
    current = ledger.get(incident_id)
    if not current:
        raise KeyError(incident_id)
    records = _memset_cache.get(incident_id)
    if records is None:
        records, _ = await gather_memory(current)
        _memset_cache[incident_id] = records
    # One targeted recall so the check reflects what Hindsight holds about this fix.
    mem = get_memory()
    hits = await safe(mem.recall(f"Fix attempted: {proposed} on {current['machine_id']}", tags=[f"system:{current['system']}"], budget="low", max_tokens=2048), default=[], timeout=20)
    known = ledger.known_ids()
    extra = {record_id(h["record"]): h["record"] for h in hits if h.get("record") and record_id(h["record"]) in known}
    merged = {record_id(r): r for r in records}
    merged.update(extra)
    warnings = check_fix(proposed, current, list(merged.values()))
    return {"proposed": proposed, "warnings": warnings, "recalled": len(hits)}


def clear_cache():
    _memset_cache.clear()
