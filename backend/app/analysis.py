"""Deterministic evidence engine.

The LLM never decides what the evidence is. This module computes it from the
records recalled from Hindsight: which incidents are related, which are
coincidental, how every past fix turned out, which factors recur, and how
strongly. The LLM only writes the explanation on top.
"""
import re
from collections import Counter
from datetime import timedelta

from .config import INEFFECTIVE_WINDOW_HOURS, MACHINES, PLANT, RECURRENCE_WINDOW_DAYS
from .records import parse_ts, record_id

SYMPTOM_FAMILIES = {
    "overheating": {"HYD-TEMP-HI", "HYD-TEMP-WARN", "SPN-TEMP-HI"},
    "pressure": {"PRS-FLUCT", "PRS-LOW", "PRV-NOISE"},
}

FIX_LABELS = {
    "cooling_fan": "Replace cooling fan",
    "oil_change": "Flush and refill hydraulic oil",
    "relief_valve": "Replace pressure relief valve",
    "seals": "Replace cylinder seals",
    "drive_reset": "Reset motor drive",
    "coolant_filter": "Clean / replace coolant filter",
}

GRADES = ["confirmed", "strong", "possible", "hypothesis", "ruled_out"]


def families(inc: dict) -> set[str]:
    codes = set(inc.get("error_codes", []))
    return {f for f, fam in SYMPTOM_FAMILIES.items() if codes & fam}


def fmt_date(ts: str) -> str:
    return parse_ts(ts).strftime("%d %b").lstrip("0")


def oil_in_service(machine: str, ts: str, fills: list[dict]) -> dict | None:
    t = parse_ts(ts)
    prior = [f for f in fills if f.get("machine_id") == machine and parse_ts(f["timestamp"]) <= t]
    if not prior:
        return None
    prior.sort(key=lambda f: f["timestamp"])
    return prior[-1]


def classify_outcome(inc: dict, later_related: list[dict], now) -> dict:
    t = parse_ts(inc["timestamp"])
    nxt = next((x for x in later_related if x["machine_id"] == inc["machine_id"] and parse_ts(x["timestamp"]) > t), None)
    if nxt:
        delta = parse_ts(nxt["timestamp"]) - t
        if delta <= timedelta(hours=INEFFECTIVE_WINDOW_HOURS):
            label = "ineffective"
        elif delta <= timedelta(days=RECURRENCE_WINDOW_DAYS):
            label = "temporary"
        else:
            label = "permanent"
        return {"label": label, "days_until_recurrence": delta.days, "recurred_as": record_id(nxt)}
    if now - t >= timedelta(days=RECURRENCE_WINDOW_DAYS):
        return {"label": "permanent", "days_until_recurrence": None, "recurred_as": None}
    return {"label": "unknown", "days_until_recurrence": None, "recurred_as": None, "days_observed": (now - t).days}


def analyze(current: dict, memory: list[dict]) -> dict:
    now = parse_ts(current["timestamp"])
    system = current["system"]
    cur_fam = families(current)
    incidents = [r for r in memory if r["kind"] == "incident" and record_id(r) != record_id(current) and parse_ts(r["timestamp"]) < now]
    fills = [r for r in memory if r["kind"] == "oil_fill"]
    power = [r for r in memory if r["kind"] == "power_event"]
    supplier_changes = [r for r in memory if r["kind"] == "supplier_change"]
    notes = [r for r in memory if r["kind"] in ("plant_note", "handover_note")]
    confirmations = [r for r in memory if r["kind"] == "confirmation"]

    related, excluded = [], []
    for inc in sorted(incidents, key=lambda x: x["timestamp"]):
        fam = families(inc)
        if not (fam & cur_fam):
            continue
        if inc.get("system") != system:
            excluded.append({
                "incident": inc,
                "reason": f"Similar symptom, different system ({inc.get('system')} on {inc['machine_id']}). "
                          f"Recorded cause: {inc.get('root_cause_recorded') or 'unknown'}.",
                "kind": "different_system",
            })
            continue
        t = parse_ts(inc["timestamp"])
        pe = next((p for p in power if inc["machine_id"] in p.get("machines_affected", [])
                   and abs(parse_ts(p["timestamp"]) - t) <= timedelta(hours=3)), None)
        if pe:
            excluded.append({
                "incident": inc,
                "reason": f"Happened during a plant-wide electrical event ({record_id(pe)}): "
                          f"{len(pe['machines_affected'])} machines tripped in the same hour.",
                "kind": "explained_by_event",
                "event_id": record_id(pe),
            })
            continue
        related.append(inc)

    pattern = related + [current]
    n = len(pattern)

    # ---- fix history (failed-fix memory) ----
    fix_history = []
    for inc in related:
        if not inc.get("fix_applied"):
            continue
        later = [x for x in pattern if parse_ts(x["timestamp"]) > parse_ts(inc["timestamp"])]
        outcome = classify_outcome(inc, later, now)
        fix_history.append({
            "incident_id": record_id(inc), "machine_id": inc["machine_id"], "date": inc["timestamp"],
            "fix": inc["fix_applied"], "fix_category": inc.get("fix_category"), "outcome": outcome,
        })
    temp_fixes = [f for f in fix_history if f["outcome"]["label"] in ("temporary", "ineffective")]

    # ---- oil in service per incident ----
    oil_by_inc = {}
    for inc in pattern:
        o = oil_in_service(inc["machine_id"], inc["timestamp"], fills)
        oil_by_inc[record_id(inc)] = o

    factors = []

    # Oil supplier factor
    sup_counts = Counter(o["supplier"] for o in oil_by_inc.values() if o)
    for sup, cnt in sup_counts.most_common():
        ids = [i for i, o in oil_by_inc.items() if o and o["supplier"] == sup]
        batches = sorted({oil_by_inc[i]["batch"] for i in ids})
        machines = sorted({next(p["machine_id"] for p in pattern if record_id(p) == i) for i in ids})
        coverage = cnt / n
        evidence = [f"Oil from {sup} was in service in {cnt} of {n} related incidents, across {len(machines)} machine{'s' if len(machines) > 1 else ''} ({', '.join(machines)})."]

        change = next((c for c in supplier_changes if c.get("to_supplier") == sup), None)
        change_info = None
        if change:
            ct = parse_ts(change["timestamp"])
            before = [p for p in related if parse_ts(p["timestamp"]) < ct]
            after = [p for p in pattern if parse_ts(p["timestamp"]) >= ct]
            excl_before = [e for e in excluded if e["kind"] == "explained_by_event" and parse_ts(e["incident"]["timestamp"]) < ct]
            change_info = {"event_id": record_id(change), "date": change["timestamp"], "from": change["from_supplier"],
                           "before": len(before), "after": len(after), "excluded_before": len(excl_before)}
            evidence.append(
                f"Procurement switched to {sup} on {fmt_date(change['timestamp'])}. Related incidents since then: {len(after)}. "
                f"Before the switch: {len(before)}" + (f" (the only earlier one is explained by a power event)." if excl_before and not before else ".")
            )
            for e in excl_before:
                e["reason"] += " It also predates the supplier change."

        # control comparison: sibling machines of same system with no related incidents
        control = []
        pattern_machines = {p["machine_id"] for p in pattern}
        for mid, m in MACHINES.items():
            if m["system"] != system or mid in pattern_machines:
                continue
            m_fills = [f for f in fills if f.get("machine_id") == mid and parse_ts(f["timestamp"]) <= now]
            sups = sorted({f["supplier"] for f in m_fills})
            control.append({"machine_id": mid, "suppliers": sups, "related_incidents": 0})
            if m_fills and sup not in sups:
                evidence.append(f"{mid} runs on oil from {', '.join(sups)} and has had no similar incidents (control comparison).")

        cues = [p for p in pattern if re.search(r"\b(thin|dark|darker|burnt)\b", (p.get("technician_notes") or "").lower())]
        if cues:
            evidence.append(f"Technicians described the oil as thin, dark or burnt in {len(cues)} incident notes ({', '.join(record_id(c) for c in cues)}).")
        if temp_fixes:
            evidence.append(f"{len(temp_fixes)} earlier fixes on these machines only helped temporarily; the problem came back each time.")

        key = f"oil_supplier:{sup}"
        confirmed = next((c for c in confirmations if c.get("factor_key") == key and c.get("decision") == "confirmed"), None)
        rejected = next((c for c in confirmations if c.get("factor_key") == key and c.get("decision") == "rejected"), None)
        if confirmed:
            grade, why = "confirmed", f"An engineer confirmed this cause on {fmt_date(confirmed['timestamp'])} ({record_id(confirmed)}): {(confirmed.get('note') or 'no note').rstrip('.')}."
        elif rejected:
            grade, why = "ruled_out", f"An engineer rejected this cause on {fmt_date(rejected['timestamp'])}: {rejected.get('note') or 'no reason given'}."
        elif coverage >= 0.8 and cnt >= 3 and len(temp_fixes) >= 2:
            grade, why = "strong", f"Present in {cnt}/{n} related incidents on {len(machines)} machines, and {len(temp_fixes)} different fixes failed to stop recurrence."
        elif coverage >= 0.4:
            grade, why = "possible", f"Present in {cnt}/{n} related incidents, not consistently."
        else:
            grade, why = "hypothesis", f"Present in only {cnt}/{n} related incidents."
        factors.append({
            "key": key, "type": "oil_supplier", "label": f"Hydraulic oil from {sup}", "short": sup,
            "grade": grade, "why": why, "count": cnt, "total": n, "coverage": round(coverage, 2),
            "incident_ids": ids, "batches": batches, "machines": machines, "evidence": evidence,
            "supplier_change": change_info, "control": control,
            "confirmation_id": record_id(confirmed) if confirmed else None,
        })

    # Shift factor (context, not cause)
    shift_counts = Counter(p["shift"] for p in pattern)
    if shift_counts:
        s, cnt = shift_counts.most_common(1)[0]
        if cnt / n >= 0.6 and n >= 3:
            note = next((x for x in notes if f"Shift {s}" in x["note"]), None)
            reason = (f"{note['note']} ({record_id(note)}) Overheating shows up when presses run longest, so the shift explains when it appears, not why."
                      if note else "The shift explains when the problem is noticed, not why it happens.")
            factors.append({"key": f"shift:{s}", "type": "shift", "label": f"Shift {s} ({PLANT['shifts'][s]})", "short": f"Shift {s}",
                            "grade": "ruled_out", "why": reason, "count": cnt, "total": n, "coverage": round(cnt / n, 2),
                            "incident_ids": [record_id(p) for p in pattern if p["shift"] == s], "evidence": []})

    # People are never treated as causes
    rep_counts = Counter(p["reported_by"] for p in pattern)
    if rep_counts:
        name, cnt = rep_counts.most_common(1)[0]
        if cnt / n >= 0.5 and n >= 3:
            role = PLANT["people"].get(name, "technician")
            top_shift = shift_counts.most_common(1)[0][0]
            factors.append({"key": f"person:{name}", "type": "person", "label": name, "short": name, "grade": "ruled_out",
                            "why": f"{name} is the {role}. {cnt} of {n} incidents were reported by them because they happened on Shift {top_shift}. "
                                   f"Reporting a breakdown is not causing it; ORIGIN does not treat people as root causes.",
                            "count": cnt, "total": n, "coverage": round(cnt / n, 2),
                            "incident_ids": [record_id(p) for p in pattern if p["reported_by"] == name], "evidence": []})

    factors.sort(key=lambda f: (GRADES.index(f["grade"]), -f["coverage"]))
    primary = next((f for f in factors if f["grade"] in ("confirmed", "strong", "possible")), None)

    intervals = []
    by_machine = {}
    for p in pattern:
        by_machine.setdefault(p["machine_id"], []).append(parse_ts(p["timestamp"]))
    for ts in by_machine.values():
        ts.sort()
        intervals += [(b - a).days for a, b in zip(ts, ts[1:])]

    downtime = sum(p.get("downtime_minutes", 0) for p in related)
    units = sum(p.get("production_loss_units", 0) for p in related)
    inr = round(downtime / 60 * PLANT["downtime_cost_per_hour_inr"])

    evidence_notes = [n_ for n_ in notes if n_["kind"] == "handover_note" and any(m in n_["note"] for m in {p["machine_id"] for p in pattern})]

    timeline = []
    for c in supplier_changes:
        if parse_ts(c["timestamp"]) < now:
            timeline.append({"type": "event", "id": record_id(c), "date": c["timestamp"], "title": f"Supplier switched to {c['to_supplier']}", "detail": c["note"]})
    for e in evidence_notes:
        timeline.append({"type": "note", "id": record_id(e), "date": e["timestamp"], "title": f"Handover note: {e['author']}", "detail": e["note"]})
    outcome_by_id = {f["incident_id"]: f["outcome"] for f in fix_history}
    decided_by_inc = {c["incident_id"]: c for c in confirmations}
    for p in related:
        o = oil_by_inc.get(record_id(p))
        timeline.append({"type": "incident", "id": record_id(p), "date": p["timestamp"], "machine_id": p["machine_id"],
                         "title": p.get("fix_applied") or (f"Root cause {decided_by_inc[record_id(p)]['decision']}: {decided_by_inc[record_id(p)]['factor_label']} ({record_id(decided_by_inc[record_id(p)])})" if record_id(p) in decided_by_inc else "No fix recorded"), "symptoms": p["symptoms"],
                         "outcome": outcome_by_id.get(record_id(p)), "oil": o and {"supplier": o["supplier"], "batch": o["batch"]},
                         "shift": p["shift"], "downtime_minutes": p.get("downtime_minutes", 0)})
    for e in excluded:
        timeline.append({"type": "excluded", "id": record_id(e["incident"]), "date": e["incident"]["timestamp"],
                         "machine_id": e["incident"]["machine_id"], "title": e["incident"].get("fix_applied") or "",
                         "symptoms": e["incident"]["symptoms"], "reason": e["reason"], "kind": e["kind"]})
    o = oil_by_inc.get(record_id(current))
    preventive_flag = current.get("downtime_minutes", 0) == 0 and any(c.endswith("WARN") for c in current.get("error_codes", []))
    timeline.append({"type": "current", "id": record_id(current), "date": current["timestamp"], "machine_id": current["machine_id"],
                     "title": "Today", "symptoms": current["symptoms"], "warning_only": preventive_flag, "oil": o and {"supplier": o["supplier"], "batch": o["batch"]}})
    timeline.sort(key=lambda x: x["date"])

    preventive = current.get("downtime_minutes", 0) == 0 and any(c.endswith("WARN") for c in current.get("error_codes", []))

    return {
        "current": current,
        "related_ids": [record_id(p) for p in related],
        "excluded": [{"incident_id": record_id(e["incident"]), "machine_id": e["incident"]["machine_id"], "reason": e["reason"], "kind": e["kind"]} for e in excluded],
        "fix_history": fix_history,
        "factors": factors,
        "primary": primary,
        "timeline": timeline,
        "intervals_days": intervals,
        "cost": {"downtime_minutes": downtime, "units_lost": units, "inr": inr},
        "preventive": preventive,
        "machines_span": sorted(by_machine.keys()),
    }


# ---------- failed-fix check ----------
FIX_KEYWORDS = {
    "cooling_fan": ["fan"],
    "oil_change": ["flush", "refill", "oil change", "change oil", "change the oil", "replace oil", "replace the oil", "new oil", "top up", "top-up"],
    "relief_valve": ["relief", "valve", "prv"],
    "seals": ["seal", "gland"],
    "drive_reset": ["reset", "drive", "restart"],
    "coolant_filter": ["coolant filter"],
}


def categorize_fix(text: str) -> list[str]:
    t = text.lower()
    cats = [c for c, kws in FIX_KEYWORDS.items() if any(k in t for k in kws)]
    return cats


def check_fix(proposed: str, current: dict, memory: list[dict]) -> list[dict]:
    cats = categorize_fix(proposed)
    if not cats:
        return []
    result = analyze(current, memory)
    warnings = []
    for f in result["fix_history"]:
        if f["fix_category"] in cats:
            warnings.append({**f, "same_machine": f["machine_id"] == current["machine_id"]})
    warnings.sort(key=lambda w: (not w["same_machine"], w["date"]))
    return warnings