"""LLM calls (Groq or OpenRouter) with retries, JSON validation and deterministic fallbacks.
The demo must never crash because a model returned something odd."""
import asyncio
import json
import logging
import re

from .config import (GROQ_API_KEY, GROQ_FALLBACK_MODEL, GROQ_MODEL, LLM_PROVIDER, OPENROUTER_API_KEY,
                     OPENROUTER_FALLBACK_MODEL, OPENROUTER_MODEL)

log = logging.getLogger("origin.llm")
_client = None


USE_OPENROUTER = LLM_PROVIDER == "openrouter"
MODEL = OPENROUTER_MODEL if USE_OPENROUTER else GROQ_MODEL
FALLBACK_MODEL = OPENROUTER_FALLBACK_MODEL if USE_OPENROUTER else GROQ_FALLBACK_MODEL


def enabled() -> bool:
    return bool(OPENROUTER_API_KEY if USE_OPENROUTER else GROQ_API_KEY)


def provider() -> str:
    return "openrouter" if USE_OPENROUTER else "groq"


def _get():
    global _client
    if _client is None:
        if USE_OPENROUTER:
            from openai import AsyncOpenAI  # OpenRouter speaks the OpenAI API

            _client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1",
                                  max_retries=1, timeout=30.0,
                                  default_headers={"X-Title": "ORIGIN - HackwithHyderabad 3.0"})
        else:
            from groq import AsyncGroq

            _client = AsyncGroq(api_key=GROQ_API_KEY, max_retries=1, timeout=30.0)
    return _client


def _parse(text: str) -> dict | None:
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


async def chat_json(system: str, user: str, required: list[str]) -> dict | None:
    if not enabled():
        return None
    attempts = [(MODEL, True), (MODEL, False), (FALLBACK_MODEL, False)]
    for model, json_mode in attempts:
        try:
            kwargs = dict(
                model=model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.2,
                max_tokens=2000,
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = await asyncio.wait_for(_get().chat.completions.create(**kwargs), timeout=35)
            data = _parse(resp.choices[0].message.content or "")
            if data and all(k in data for k in required):
                return data
            log.warning("LLM output missing keys from %s", model)
        except Exception as e:
            log.warning("LLM call failed (%s, json=%s): %s", model, json_mode, str(e)[:200])
    return None


# ---------------- Amnesia Mode ----------------
AMNESIA_SYSTEM = (
    "You are a helpful factory maintenance assistant. You have NO access to any maintenance history. "
    "Given one breakdown report, suggest likely causes and the fixes a technician should try. "
    'Respond ONLY with JSON: {"summary": str, "likely_causes": [str], "suggested_fixes": [str]}. '
    "Keep each list to 3-4 short items."
)


async def amnesia(incident: dict) -> dict:
    user = json.dumps({k: incident.get(k) for k in ("machine_id", "line", "symptoms", "error_codes", "technician_notes")}, ensure_ascii=False)
    data = await chat_json(AMNESIA_SYSTEM, user, ["summary", "likely_causes", "suggested_fixes"])
    if data:
        return {**data, "source": "groq"}
    return {
        "summary": f"{incident['machine_id']} is overheating. Typical causes for a hydraulic press are poor cooling, worn valves or degraded oil.",
        "likely_causes": ["Cooling fan or oil cooler not working", "Pressure relief valve worn or stuck", "Low or degraded hydraulic oil"],
        "suggested_fixes": ["Check and replace the cooling fan", "Inspect and replace the relief valve", "Top up or change the hydraulic oil"],
        "source": "fallback",
    }


# ---------------- Investigation brief ----------------
BRIEF_SYSTEM = (
    "You are ORIGIN, a plant reliability investigator. You are given COMPUTED EVIDENCE from the plant's memory. "
    "Write a short investigation brief for a maintenance engineer. Rules: use only facts in the evidence; never invent "
    "incident IDs, dates, numbers or suppliers; cite incident IDs; match the certainty to the grade "
    "(confirmed / strong recurring pattern / possible / hypothesis) and never claim more; never blame people. "
    "Plain, direct English for a factory floor. "
    'Respond ONLY with JSON: {"headline": str (max 14 words), "summary": str (2-3 sentences), '
    '"next_steps": [str] (2-3 concrete checks)}'
)


def _fallback_brief(ev: dict) -> dict:
    p = ev["primary"]
    cur = ev["current"]
    if not p:
        return {
            "headline": f"No recurring pattern found for {cur['machine_id']} yet",
            "summary": "Plant memory has no strong recurring factor for this breakdown. Treat it as a new issue and record the fix and outcome so ORIGIN can learn from it.",
            "next_steps": ["Diagnose from symptoms as usual", "Record the fix and what happens in the next 60 days"],
        }
    temp = [f for f in ev["fix_history"] if f["outcome"]["label"] == "temporary"]
    if p["grade"] == "confirmed":
        return {
            "headline": f"Matches a confirmed root cause: {p['label']}",
            "summary": f"{cur['machine_id']} shows the same early signs as the confirmed pattern ({p['confirmation_id']}). "
                       f"The same oil is now in service on this machine. Acting now can prevent a breakdown.",
            "next_steps": [f"Drain and replace the oil in {cur['machine_id']} with in-spec oil", "Quarantine remaining stock from the same supplier", "Log the result so ORIGIN can close the pattern"],
        }
    fixes = ", ".join(f"{f['fix'].lower()} ({f['incident_id']})" for f in temp)
    return {
        "headline": f"Recurring pattern: {p['label']}",
        "summary": f"This is part of a pattern of {p['total']} related incidents across {', '.join(p['machines'])}. "
                   f"{p['label']} was in service in {p['count']} of {p['total']}. Earlier fixes ({fixes}) only helped temporarily.",
        "next_steps": ["Lab-test the viscosity of the current oil batch against ISO VG 68", "Quarantine remaining stock from this supplier", "Check sibling presses before refilling them"],
    }


async def brief(ev: dict) -> dict:
    p = ev["primary"]
    compact = {
        "current_incident": {k: ev["current"].get(k) for k in ("incident_id", "machine_id", "timestamp", "symptoms")},
        "preventive_early_warning": ev["preventive"],
        "primary_factor": p and {k: p.get(k) for k in ("label", "grade", "why", "count", "total", "machines", "batches", "evidence", "incident_ids")},
        "ruled_out": [{"label": f["label"], "why": f["why"]} for f in ev["factors"] if f["grade"] == "ruled_out"],
        "fix_history": [{"incident_id": f["incident_id"], "machine": f["machine_id"], "fix": f["fix"], "outcome": f["outcome"]["label"],
                         "days_until_recurrence": f["outcome"].get("days_until_recurrence")} for f in ev["fix_history"]],
        "excluded": ev["excluded"],
        "cost": ev["cost"],
    }
    data = await chat_json(BRIEF_SYSTEM, json.dumps(compact, ensure_ascii=False), ["headline", "summary", "next_steps"])
    if data and isinstance(data.get("next_steps"), list):
        return {**data, "source": "groq"}
    return {**_fallback_brief(ev), "source": "fallback"}