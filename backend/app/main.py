"""ORIGIN API."""
import logging
import uuid
from datetime import datetime, timedelta

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import investigate, ledger, llm
from .config import BANK_ID, DEMO, FRONTEND_ORIGIN, MACHINES, PLANT
from .memory import get_memory, safe
from .records import narrative, record_id

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("origin")

app = FastAPI(title="ORIGIN — The Memory of Every Breakdown")
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    if not ledger.LEDGER_PATH.exists():
        ledger.reset()
    mem = get_memory()
    await safe(mem.ensure_bank(), timeout=30)
    if mem.mode == "local":
        log.warning("HINDSIGHT_API_KEY not set: running on LOCAL fallback memory. Add your key to backend/.env for the real demo.")


async def retain(records: list[dict], wait: bool = True):
    ok = await safe(get_memory().retain(records, wait=wait), default="fail", timeout=120)
    if ok == "fail":
        log.warning("Retain failed for %s", [record_id(r) for r in records])


# ---------- read ----------
@app.get("/health")
async def health():
    return {"memory_backend": get_memory().mode, "bank_id": BANK_ID, "llm": llm.provider() if llm.enabled() else "fallback"}


@app.get("/plant")
async def plant():
    return PLANT


@app.get("/incidents")
async def incidents():
    items = [r for r in ledger.all_records() if r["kind"] == "incident"]
    return sorted(items, key=lambda r: r["timestamp"], reverse=True)


@app.get("/memory")
async def memory():
    items = sorted(ledger.all_records(), key=lambda r: r["timestamp"], reverse=True)
    return [{"id": record_id(r), "kind": r["kind"], "timestamp": r["timestamp"], "text": narrative(r)} for r in items]


@app.get("/machines/{machine_id}")
async def machine(machine_id: str):
    if machine_id not in MACHINES:
        raise HTTPException(404, "Unknown machine")
    recs = [r for r in ledger.all_records() if r.get("machine_id") == machine_id or machine_id in r.get("machines_affected", [])]
    return {"machine": MACHINES[machine_id], "records": sorted(recs, key=lambda r: r["timestamp"])}


# ---------- write ----------
class NewIncident(BaseModel):
    machine_id: str
    symptoms: list[str] = Field(min_length=1)
    error_codes: list[str] = []
    technician_notes: str = ""
    reported_by: str = "Ramesh Patil"
    timestamp: str | None = None


@app.post("/incidents")
async def create_incident(body: NewIncident, bg: BackgroundTasks):
    if body.machine_id not in MACHINES:
        raise HTTPException(400, "Unknown machine")
    m = MACHINES[body.machine_id]
    ts = body.timestamp or f"{PLANT['demo_date']}T23:30:00+05:30"
    hour = int(ts[11:13])
    inc = {
        "incident_id": f"MX-{uuid.uuid4().hex[:4].upper()}", "kind": "incident", "timestamp": ts,
        "machine_id": body.machine_id, "line": m["line"], "system": m["system"],
        "shift": "A" if 6 <= hour < 14 else ("B" if 14 <= hour < 22 else "C"),
        "reported_by": body.reported_by, "symptoms": body.symptoms, "error_codes": body.error_codes,
        "downtime_minutes": 0, "production_loss_units": 0, "fix_applied": None, "fix_category": None,
        "parts_used": [], "technician_notes": body.technician_notes, "root_cause_recorded": None,
    }
    ledger.upsert(inc)
    bg.add_task(retain, [inc], True)
    return inc


@app.post("/demo/load-today")
async def load_today(bg: BackgroundTasks):
    inc = DEMO["today_incident"]
    ledger.upsert(inc)
    bg.add_task(retain, [inc], True)
    return inc


@app.post("/investigate/{incident_id}")
async def run_investigation(incident_id: str, memory: bool = True):
    try:
        return await investigate.run(incident_id, use_memory=memory)
    except KeyError:
        raise HTTPException(404, "Incident not found. Load it first.")


class FixCheck(BaseModel):
    incident_id: str
    proposed_fix: str


@app.post("/check-fix")
async def check_fix(body: FixCheck):
    if len(body.proposed_fix.strip()) < 3:
        return {"proposed": body.proposed_fix, "warnings": [], "recalled": 0}
    try:
        return await investigate.fix_check(body.incident_id, body.proposed_fix)
    except KeyError:
        raise HTTPException(404, "Incident not found")


class Decision(BaseModel):
    decision: str  # confirmed | rejected | investigating
    factor_key: str
    factor_label: str
    note: str = ""


@app.post("/confirm/{incident_id}")
async def confirm(incident_id: str, body: Decision):
    inc = ledger.get(incident_id)
    if not inc:
        raise HTTPException(404, "Incident not found")
    if body.decision not in ("confirmed", "rejected", "investigating"):
        raise HTTPException(400, "decision must be confirmed, rejected or investigating")
    ts = (datetime.fromisoformat(inc["timestamp"]) + timedelta(hours=11)).isoformat()
    rec = {
        "confirmation_id": f"CONF-{uuid.uuid4().hex[:6].upper()}", "kind": "confirmation", "timestamp": ts,
        "incident_id": incident_id, "machine_id": inc["machine_id"], "decision": body.decision,
        "factor_key": body.factor_key, "factor_label": body.factor_label, "note": body.note,
    }
    ledger.upsert(rec)
    await retain([rec], wait=True)
    investigate.clear_cache()
    return rec


@app.post("/demo/advance")
async def advance():
    """Jump to Jun 19: HP-06 gets oil from the new supplier and starts warming up."""
    fill, inc = DEMO["followup_oil_fill"], DEMO["followup_incident"]
    ledger.upsert(fill)
    ledger.upsert(inc)
    await retain([fill, inc], wait=True)
    investigate.clear_cache()
    return inc


@app.post("/demo/reset")
async def reset():
    ids = ledger.demo_ids()
    await safe(get_memory().delete(ids), timeout=60)
    ledger.reset()
    investigate.clear_cache()
    return {"reset": True, "removed": ids}