"""Turns structured plant records into memory items for Hindsight.

Each record becomes one Hindsight memory:
  * content      -> a plain-language narrative (what Hindsight extracts facts from)
  * document_id  -> the record id, so recalled facts point back to the exact record
  * metadata     -> the full structured record as JSON, so ORIGIN can reason over it
  * tags         -> machine / system / kind, used to scope recall
  * timestamp    -> when it happened, enabling Hindsight's temporal retrieval
"""
import json
from datetime import datetime

from .config import MACHINES


def record_id(r: dict) -> str:
    return r.get("confirmation_id") or r.get("event_id") or r.get("incident_id")


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def record_system(r: dict) -> str | None:
    if r.get("system"):
        return r["system"]
    m = r.get("machine_id")
    if m and m in MACHINES:
        return MACHINES[m]["system"]
    return None


def tags_for(r: dict) -> list[str]:
    tags = [f"kind:{r['kind']}"]
    machines = [r["machine_id"]] if r.get("machine_id") else list(r.get("machines_affected", []))
    tags += [f"machine:{m}" for m in machines]
    systems = {MACHINES[m]["system"] for m in machines if m in MACHINES}
    if r.get("system"):
        systems.add(r["system"])
    if r["kind"] in ("supplier_change", "plant_note", "handover_note"):
        systems.add("hydraulic")  # these plant records concern the press fleet
    tags += [f"system:{s}" for s in sorted(systems)]
    tags.append("plant")
    return tags


def narrative(r: dict) -> str:
    k = r["kind"]
    when = parse_ts(r["timestamp"]).strftime("%d %b %Y, %H:%M")
    if k == "incident":
        parts = "; ".join(
            f"{p['part']}" + (f" ({p.get('qty_litres')}L, supplier {p['supplier']}, batch {p['batch']})" if p.get("batch") else f" from {p.get('supplier')}")
            for p in r.get("parts_used", [])
        )
        lines = [
            f"Maintenance incident {r['incident_id']} on {r['machine_id']} ({MACHINES.get(r['machine_id'], {}).get('type', '')}, {r['line']}) at {when}, Shift {r['shift']}, reported by {r['reported_by']}.",
            f"Symptoms: {', '.join(r['symptoms'])}. Error codes: {', '.join(r['error_codes'])}.",
        ]
        if r.get("fix_applied"):
            lines.append(f"Fix applied: {r['fix_applied']}." + (f" Parts used: {parts}." if parts else ""))
            lines.append(f"Downtime {r['downtime_minutes']} minutes, {r['production_loss_units']} units of production lost.")
        else:
            lines.append("Status: open, under investigation.")
        if r.get("technician_notes"):
            lines.append(f"Technician notes: {r['technician_notes']}")
        if r.get("root_cause_recorded"):
            lines.append(f"Root cause recorded at the time: {r['root_cause_recorded']}.")
        return " ".join(lines)
    if k == "oil_fill":
        return f"Hydraulic oil added to {r['machine_id']} on {when}: {r['qty_litres']} litres from {r['supplier']}, batch {r['batch']}. {r.get('note', '')}"
    if k == "supplier_change":
        return f"Procurement change on {when}: {r['material']} supplier switched from {r['from_supplier']} to {r['to_supplier']}. {r['note']}"
    if k == "power_event":
        return f"Plant-wide electrical event on {when}: {r['note']}"
    if k in ("handover_note", "plant_note"):
        return f"Note by {r['author']} on {when}: {r['note']}"
    if k == "confirmation":
        return (
            f"Root cause decision on {when} for incident {r['incident_id']} ({r['machine_id']}): {r['decision'].upper()}. "
            f"Factor: {r['factor_label']}. Engineer note: {r.get('note') or 'none'}."
        )
    return json.dumps(r)


def to_memory_item(r: dict) -> dict:
    return {
        "content": narrative(r),
        "timestamp": parse_ts(r["timestamp"]),
        "context": f"ORIGIN plant maintenance memory: {r['kind']}",
        "document_id": record_id(r),
        "metadata": {"record_id": record_id(r), "kind": r["kind"], "record_json": json.dumps(r, ensure_ascii=False)},
        "tags": tags_for(r),
    }
