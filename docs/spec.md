# ORIGIN — The Memory of Every Breakdown

> **Don't just fix today's breakdown. Remember enough about yesterday's to stop repeating it tomorrow.**

Build a polished, hackathon-ready web application called **ORIGIN** for **HackwithHyderabad 3.0 — AI Agents That Learn Using Hindsight**.

---

## 1. One-Line Pitch

ORIGIN is an AI maintenance investigator for factories. It remembers every machine breakdown, every fix technicians tried, and whether that fix actually worked, then connects breakdowns across months and machines to find the hidden root cause that nobody on the floor could see.

---

## 2. Why This Domain (Read This First)

Most teams in this hackathon are building DevOps incident agents. ORIGIN uses the same powerful idea, **Problem → Fix → Recurrence → Memory → Pattern → Root Cause**, but applies it to **factory maintenance**, where:

- The problem is physical, visual, and instantly understood by any judge ("the machine keeps overheating").
- The cost is concrete: every hour a production line stops costs lakhs of rupees.
- Knowledge loss is real: when a senior technician retires or changes shifts, their memory of "what we tried last time" leaves with them.
- Maintenance records are usually scattered across paper logbooks, WhatsApp messages, and Excel sheets, so no one sees patterns across time.

ORIGIN should feel like an **organizational detective for the factory floor**, not a chatbot.

---

## 3. The Problem ORIGIN Solves

Factories fix symptoms, not causes, because breakdowns happen weeks apart, on different shifts, and are handled by different people.

**Example (this is the actual demo storyline — see Section 9):**

| Date | Machine | Symptom | Fix Applied | Result |
|---|---|---|---|---|
| Mar 6 | Hydraulic Press HP-04 | Oil overheating, press slowing down | Replaced cooling fan | Worked… for 3 weeks |
| Apr 2 | Hydraulic Press HP-04 | Overheating again, pressure fluctuation | Flushed and refilled hydraulic oil | Worked… for 4 weeks |
| Apr 29 | Hydraulic Press HP-02 | Pressure drop, seal leak | Replaced seals | Worked… for 5 weeks |
| May 21 | Hydraulic Press HP-04 | Overheating, relief valve chattering | Replaced pressure relief valve | Worked… for 3 weeks |
| **Jun 12** | **Hydraulic Press HP-04** | **Overheating again** | **?** | |

A normal AI looks at June 12 alone and says: *"Check the cooling fan."* (Already done in March.)

ORIGIN asks: **"Have we seen this before?"**

It finds that every one of these breakdowns started after the plant switched to a new hydraulic oil supplier (**Vardhan Lubricants**) in February, and the oil delivered is a thinner viscosity grade than the presses need. Each fix treated a different symptom. The oil was the root cause the whole time, and it spans **two different machines**, which no single technician would notice.

ORIGIN tells the engineer:

> "This is the 4th overheating event on HP-04 since March, and HP-02 shows a related failure. All five events occurred after hydraulic oil deliveries from Vardhan Lubricants began (Feb 14). Three previous fixes (cooling fan, oil flush, relief valve) reduced symptoms temporarily, but the problem recurred every 3–5 weeks. **Strong recurring pattern:** hydraulic oil supply should be investigated as the likely underlying cause. Recommended check: verify the viscosity grade of the current oil batch against the press manufacturer's specification."

---

## 4. Core Principles

1. **Memory drives the intelligence.** ORIGIN must be visibly smarter *because* it remembers. Without memory, it's generic.
2. **Remember what humans tried, not just what happened.** Failed-fix memory is the #1 differentiator.
3. **Evidence over confidence.** ORIGIN never claims certainty it hasn't earned.
4. **It gets better over time.** Confirmed root causes make future investigations faster and more confident.
5. **Don't blame people.** ORIGIN investigates systems, parts, suppliers, and conditions, never individuals (see Decoy B in Section 9).

---

## 5. Evidence Grading (Mandatory)

Every finding ORIGIN shows must carry exactly one of these labels:

| Label | Meaning | Visual |
|---|---|---|
| **Confirmed Root Cause** | A human has verified this cause for this pattern before | Solid green badge |
| **Strong Recurring Pattern** | Factor appears across 3+ related incidents, and previous fixes did not stop recurrence | Amber badge |
| **Possible Contributing Factor** | Factor appears in some related incidents but not consistently | Grey badge |
| **Hypothesis — Needs Investigation** | Plausible, but weak evidence | Dashed outline badge |
| **Ruled Out / Coincidental** | Factor appears often but has an innocent explanation | Struck-through, muted |

ORIGIN must explain *why* each label was given, in one or two plain sentences.

---

## 6. Hero Feature: Failed-Fix Memory

ORIGIN remembers every intervention and classifies its outcome automatically from the timeline:

| Outcome | Rule |
|---|---|
| **Permanent** | No related recurrence on that machine within 60 days |
| **Temporary** | The same or a related symptom recurred within 60 days |
| **Ineffective** | Symptom persisted, or a second fix was needed within 48 hours |
| **Unknown** | Not enough time has passed (under 60 days) |

**Previously-Attempted Warning.** When a user types or selects a proposed fix that matches a past intervention, ORIGIN interrupts:

> ⚠️ **Previously attempted.** "Replace cooling fan" was tried on HP-04 on Mar 6. Symptoms returned after 3 weeks. Classified as **Temporary**. This fix addresses a symptom, not the pattern.

This warning must appear in the demo. It is the single most memorable moment.

---

## 7. The Learning Loop (Proves the Agent Improves)

After an investigation, the user can respond to the brief:

- ✅ **Confirm root cause** (e.g., "Oil tested: ISO VG 32 delivered, spec requires ISO VG 68. Confirmed.")
- ❌ **Reject** (with a reason)
- 🔍 **Still investigating**

When confirmed, ORIGIN stores the confirmed cause, the resolution, and the signals that pointed to it in Hindsight.

**Payoff:** the next time a *different* machine shows early warning signs linked to the same factor, ORIGIN recognizes it immediately:

> "HP-06 received oil from the same Vardhan Lubricants batch on Jun 18 and now shows a +9°C oil temperature rise. This matches a **Confirmed Root Cause** from Jun 12. Recommend draining and replacing the oil before failure."

First investigation: several steps and moderate confidence. Second investigation: instant, confirmed, and **preventive**. That is the learning curve judges want to see.

---

## 8. Amnesia Mode (Before/After Proof)

A toggle at the top of the screen: **Memory ON / Amnesia Mode**.

- **Amnesia Mode:** the same LLM analyzes the incident with no Hindsight recall. It gives a generic answer like "Check the cooling fan, inspect the relief valve, and verify oil levels," which recommends fixes that already failed.
- **Memory ON:** the full ORIGIN investigation.

Show both side-by-side or back-to-back in the demo. This is the clearest possible proof that Hindsight is central, which is worth 25% of the score.

---

## 9. Demo Dataset

### The Plant

**Sahyadri Precision Components**, a fictional auto-parts manufacturer in Chakan, Pune. It makes stamped and machined parts for two-wheeler brands and runs 3 shifts (A: 6am–2pm, B: 2pm–10pm, C: 10pm–6am).

### Machines (8)

| ID | Type | Line |
|---|---|---|
| HP-02 | 250-ton Hydraulic Press | Stamping Line 1 |
| HP-04 | 400-ton Hydraulic Press | Stamping Line 1 |
| HP-06 | 250-ton Hydraulic Press | Stamping Line 2 |
| CNC-11 | CNC Vertical Machining Center | Machining Bay |
| CNC-12 | CNC Vertical Machining Center | Machining Bay |
| IM-03 | Injection Molding Machine | Plastics |
| CV-01 | Main Conveyor | Assembly |
| AC-01 | Air Compressor | Utilities |

### People (for realism; ORIGIN must not blame them)

- Ramesh Patil — Shift C lead technician
- Sunita Kulkarni — Maintenance Manager
- Imran Shaikh — Shift A technician
- Deepak Jadhav — Senior technician (retired in April; his notes are in memory)
- Priya Deshmukh — Stores and procurement

### Timeline

**~40 incidents from Jan 1 to Jun 12.** Every incident includes:

```json
{
  "incident_id": "MX-0147",
  "timestamp": "2026-04-02T23:40:00+05:30",
  "machine_id": "HP-04",
  "line": "Stamping Line 1",
  "shift": "C",
  "reported_by": "Ramesh Patil",
  "symptoms": ["oil temperature 71°C (normal 45–55°C)", "cycle time +18%", "pressure fluctuation ±12 bar"],
  "error_codes": ["HYD-TEMP-HI", "PRS-FLUCT"],
  "downtime_minutes": 210,
  "production_loss_units": 1850,
  "fix_applied": "Flushed and refilled hydraulic oil",
  "parts_used": [{"part": "Hydraulic oil ISO VG 68", "qty_litres": 180, "supplier": "Vardhan Lubricants", "batch": "VL-2403-B"}],
  "technician_notes": "Oil looked darker than usual and slightly thin. Refilled from new stock.",
  "root_cause_recorded": "Oil degradation (suspected)",
  "follow_up": null
}
```

**Supporting records** (also stored in memory):

- **Procurement log:** supplier switch from *Indo Hydraulics Oils* to *Vardhan Lubricants* on Feb 14 ("cost saving 22%"), with batch numbers per delivery.
- **Deepak Jadhav's handover note (April):** "HP-04 running hot lately, not sure why. Fan was fine when I checked." A small clue a human would miss.
- **Technician notes** with hints: "oil looks thin," "smells burnt," "had to top up more than usual."

### The Hidden Pattern (the "true" story)

- The root cause is **Vardhan Lubricants oil batches labeled ISO VG 68 that are actually closer to ISO VG 32** (too thin). The oil overheats, degrades seals, and stresses valves.
- It affects **HP-04 (4 incidents)** and **HP-02 (1 incident)**, the two presses refilled from those batches.
- HP-06 was refilled from old Indo Hydraulics stock and **has no incidents**. This is an important contrast that ORIGIN should use as evidence.

### Decoys (ORIGIN must correctly handle these)

The pattern must be *discovered*, not handed over. Include:

- **Decoy A — Same machine, unrelated cause:** HP-04, Jan 22, overheating caused by a **plant-wide power fluctuation** (AC-01 and CV-01 also tripped the same hour). ORIGIN should exclude it: "Coincides with a plant-wide electrical event and predates the supplier change."
- **Decoy B — The technician coincidence:** Ramesh Patil reported 4 of the 5 pattern incidents. ORIGIN should mark him as **Ruled Out / Coincidental**: "Ramesh Patil leads Shift C, when presses run the longest continuous cycles and overheating is most likely to surface. Not a causal factor." This shows ORIGIN is fair and evidence-driven.
- **Decoy C — Similar symptom, different machine type:** CNC-11 spindle overheating (Mar, May), caused by a clogged coolant filter and fixed permanently in May. Similar words ("overheating"), different system. ORIGIN should not link it.
- **Background noise:** ~25 routine unrelated incidents (conveyor belt misalignment, compressor filter change, IM-03 mold flash, CNC tool wear, sensor recalibration) so the dataset feels like a real 6-month log.

### Seed Data Rules

- Store the dataset as JSON in `/data/seed/`, loaded into Hindsight by a `seed.py` script.
- Every incident must read like a real log. No "Machine broke. Fixed it."
- Use Indian context naturally: rupee costs (₹), IST timestamps, Indian names, a Pune plant.

---

## 10. Core User Flow

### Step 1 — Incident Arrives

The user logs a new incident (form or free text) or clicks **"Load today's incident"** in demo mode:

> HP-04, Shift C, Jun 12, 11:15pm. Oil temperature 74°C, cycle time up 20%, relief valve noise. Line 1 stopped.

### Step 2 — ORIGIN Investigates (animated, step-by-step)

```
Searching plant memory…
 → Recalling incidents on HP-04 and related hydraulic systems
 → Matching symptoms and error codes
 → Comparing previous interventions and their outcomes
 → Checking parts, suppliers, and batches across incidents
 → Excluding coincidental factors
 → Evaluating recurrence
```

### Step 3 — Timeline Appears

A vertical timeline of related incidents, with the passage of time made obvious (gaps labeled "3 weeks later," "4 weeks later"):

```
FEB 14  ● Supplier switched → Vardhan Lubricants        [procurement event]
          ⋮
MAR 6   ● MX-0112  HP-04  Replaced cooling fan          → Temporary
          ⋮  3 weeks
APR 2   ● MX-0147  HP-04  Oil flush + refill            → Temporary
          ⋮  4 weeks
APR 29  ● MX-0171  HP-02  Replaced seals                → Temporary
          ⋮  3 weeks
MAY 21  ● MX-0193  HP-04  Replaced relief valve         → Temporary
          ⋮  3 weeks
JUN 12  ◉ MX-0218  HP-04  TODAY
          ↓
   ORIGIN CONNECTS THE DOTS
```

Excluded incidents (Decoy A, Decoy C) appear greyed out with a one-line reason.

### Step 4 — Pattern Identified

**COMMON FACTOR — Strong Recurring Pattern**
Hydraulic oil from Vardhan Lubricants (batches VL-2402-A, VL-2403-B, VL-2405-A)

Why:
- Present in 5 of 5 related incidents, on 2 different machines
- All incidents occurred after the Feb 14 supplier switch; zero similar incidents in the 6 weeks before
- HP-06, filled with old supplier stock, has had zero incidents (control comparison)
- Technician notes mention "thin" or "dark" oil 3 times
- 3 different fixes, all temporary, recurring every 3–5 weeks

### Step 5 — Investigation Brief

| Field | Content |
|---|---|
| **Potential Root Cause** | Hydraulic oil supplied by Vardhan Lubricants since Feb 14 |
| **Evidence Grade** | Strong Recurring Pattern |
| **Confidence** | High (5 incidents, 2 machines, control comparison) |
| **Previous Fixes** | Cooling fan (Temporary), oil flush (Temporary), seals (Temporary), relief valve (Temporary) |
| **Ruled Out** | Operator/technician (coincidental: shift pattern), electrical (Decoy A predates the pattern) |
| **Recommended Next Step** | Lab-test the viscosity of the current oil batch against spec (ISO VG 68). Quarantine remaining Vardhan stock. Check HP-06 before refilling from new stock. |
| **Estimated Cost of Pattern** | Total downtime and production loss across the 5 incidents, in ₹ |

Always phrased as an **evidence-backed investigation lead**, never an unquestionable verdict.

### Step 6 — Previously-Attempted Warning

If the user starts typing "replace cooling fan" or "change relief valve" in the proposed-fix box, the warning from Section 6 appears.

### Step 7 — Confirm and Learn

The user clicks **Confirm Root Cause** and adds a note. ORIGIN stores it, then shows the HP-06 preventive alert from Section 7.

---

## 11. Hindsight Integration (Central, Not Decorative)

Hindsight is the **only** long-term memory store. No separate database for incident history. (A small local JSON or SQLite cache for UI state is fine.)

### Memory Bank

- One bank per plant: `origin-sahyadri-chakan`.
- Check the Hindsight docs (https://hindsight.vectorize.io/) for exact SDK method signatures, metadata options, and entity/tag features before implementing. Do not guess parameters.

### What Gets Retained

| Memory Type | Examples |
|---|---|
| Incidents | Symptoms, error codes, machine, shift, downtime, loss |
| Interventions | Fix applied, parts used, supplier, batch, technician notes |
| Outcomes | Computed fix classification (Permanent / Temporary / Ineffective / Unknown) |
| Plant events | Supplier changes, procurement deliveries, power events, handover notes |
| Confirmed causes | Human-verified root causes with the evidence that pointed to them |
| Rejections | Rejected hypotheses and why (so ORIGIN doesn't repeat them) |

### How the Operations Map to the Product

| Hindsight Operation | ORIGIN Use |
|---|---|
| **Retain** | Store every new incident, fix, outcome, plant event, and human confirmation |
| **Recall** | Retrieve related past incidents, interventions, and events for a new incident |
| **Reflect** | Synthesize patterns across recalled memories into the investigation brief |

### Pattern Detection: Hybrid, Not Pure LLM Magic

To keep results trustworthy and explainable:

1. **Recall** related memories from Hindsight (by machine, system type, symptoms, error codes).
2. **Deterministic analysis** in code over the recalled set:
   - Count how often each factor (supplier, batch, part, shift, technician, machine, error code) co-occurs across related incidents.
   - Compare against a baseline: how often the factor appears in *unrelated* incidents or in time periods before a change.
   - Compute recurrence intervals and fix outcomes from timestamps.
3. **LLM + Reflect** turns these computed facts into the narrative, evidence grade explanations, and the recommended next step.

The LLM **must not invent** incidents, dates, or numbers. Every claim in the brief links back to a real incident ID.

### Memory Trace Panel (Always Visible)

A narrow panel showing live Hindsight activity during an investigation:

```
RETAIN    MX-0218 stored (HP-04, Jun 12)
   ↓
RECALL    14 memories retrieved → 5 related incidents, 1 procurement event, 1 handover note
   ↓
CONNECT   Vardhan Lubricants oil present in 5/5 related incidents
   ↓
EXCLUDE   Ramesh Patil (shift coincidence), MX-0089 (power event)
   ↓
REFLECT   3 prior fixes classified Temporary
   ↓
INSIGHT   Strong Recurring Pattern: hydraulic oil supply
```

Each line is clickable and expands to show the actual recalled memory.

---

## 12. UI / UX

### Feel

A sophisticated **plant investigation console**: dark, professional, calm. Industrial accents (amber warnings, steel greys, one signal color for insights). Not a ChatGPT clone and not a dashboard full of meaningless charts.

### Main Screen Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  ORIGIN   Sahyadri Precision · Chakan      [ Memory ON | Amnesia ]   │
├───────────────┬──────────────────────────────────┬───────────────────┤
│ CURRENT       │ INVESTIGATION TIMELINE           │ ORIGIN ANALYSIS   │
│ INCIDENT      │                                  │                   │
│               │  Feb 14 ● supplier switch        │ Common factor     │
│ HP-04         │  Mar 6  ● fan → Temporary        │ Evidence grade    │
│ Shift C       │  Apr 2  ● oil flush → Temporary  │ Ruled out         │
│ 74°C oil      │  Apr 29 ● HP-02 seals → Temp.    │ Next step         │
│ Line stopped  │  May 21 ● valve → Temporary      │                   │
│               │  Jun 12 ◉ TODAY                  │ [Confirm][Reject] │
│ Proposed fix: │                                  │                   │
│ [__________]  │                                  │                   │
├───────────────┴──────────────────────────────────┴───────────────────┤
│ MEMORY TRACE  RETAIN → RECALL → CONNECT → EXCLUDE → REFLECT → INSIGHT│
└──────────────────────────────────────────────────────────────────────┘
```

### Screens

1. **Investigation Console** (main screen, above)
2. **Plant Memory**: a searchable history of all incidents, filterable by machine, supplier, and outcome, showing memory accumulating over time
3. **Machine Profile**: one machine's full history with a fix-outcome summary ("4 fixes, 0 permanent")

### Animations (Subtle, Meaningful)

- Timeline nodes appear one by one as ORIGIN recalls them.
- A connecting line draws through related incidents when the common factor is found.
- Decoy incidents fade to grey with their exclusion reason.
- The Previously-Attempted warning slides in with an amber pulse.

### Must Be Mobile-Readable

The judges' demo will be on a laptop, but the layout should collapse cleanly (panels stack vertically).

---

## 13. Tech Stack

| Layer | Choice |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | Python FastAPI |
| Memory | Hindsight Cloud (promo code MEMHACK99 for $50 credits, added in billing after registering) or self-hosted Hindsight |
| LLM | Groq, model `openai/gpt-oss-120b` (fallback: `qwen/qwen3-32b`) |
| Deployment | Frontend on Vercel, backend on Render or Railway |

**LLM robustness:** the hackathon docs warn to handle function-calling errors. Wrap every LLM call with retries, JSON validation (Pydantic), and a graceful fallback message. The demo must never crash on a bad LLM response.

**Secrets:** all API keys in `.env`, never committed, never sent to the browser.

---

## 14. API Endpoints (Backend)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/incidents` | Log a new incident (retains to Hindsight) |
| `POST` | `/investigate/{incident_id}` | Run the full investigation; returns timeline, pattern, brief, trace |
| `POST` | `/investigate/{incident_id}?memory=false` | Amnesia Mode analysis |
| `POST` | `/check-fix` | Check a proposed fix against failed-fix memory |
| `POST` | `/confirm/{incident_id}` | Confirm, reject, or mark a root cause as investigating |
| `GET` | `/machines/{machine_id}` | Machine profile and fix-outcome history |
| `GET` | `/memory` | Browse stored plant memory |
| `POST` | `/demo/reset` | Reset the bank and reseed (for repeatable demos) |

---

## 15. The 3-Minute Demo Script

**0:00–0:20 — The pain.**
"It's 11pm at an auto-parts plant in Pune. The main hydraulic press just stopped again. Every hour down costs ₹2 lakh. The night-shift technician has never seen this machine's history, and the senior technician who knew it retired in April."

**0:20–0:45 — Amnesia Mode.**
Load the incident with memory off. The AI says "check the cooling fan, inspect the relief valve." "Sounds reasonable. Except both were already tried, and both failed."

**0:45–1:40 — Memory ON.**
Run the investigation. The timeline builds. The Memory Trace fills. The decoys get excluded, including the technician. The common factor lights up: **the oil supplier switch in February**, spanning two machines, with the untouched HP-06 as proof.

**1:40–2:05 — The warning.**
Type "replace cooling fan" in the proposed-fix box. **Previously attempted. Temporary.** "ORIGIN doesn't just remember breakdowns. It remembers what didn't work."

**2:05–2:40 — It learns.**
Confirm the root cause. Jump to Jun 19: HP-06 gets oil from the same batch and its temperature starts rising. ORIGIN flags it instantly as a Confirmed Root Cause, **before** the breakdown. "First time: an investigation. Second time: prevention."

**2:40–3:00 — Close.**
"Five breakdowns, four fixes, one cause, and ₹X lakh lost because no one could see across time. ORIGIN is a factory's long-term memory of failure and recovery."

---

## 16. Scope

### Must Have (build first)

1. Seeded dataset with the hidden pattern and all decoys
2. Investigation flow: recall → deterministic analysis → brief
3. Investigation timeline with outcome labels
4. Failed-fix memory with the Previously-Attempted warning
5. Evidence grading, including Ruled Out / Coincidental
6. Memory Trace panel
7. Amnesia Mode toggle
8. Confirm root cause → HP-06 preventive alert
9. Demo reset endpoint

### Nice to Have (only if time remains)

- Plant Memory browse screen
- Machine Profile screen
- Relationship graph view (incidents ↔ suppliers ↔ machines)
- Cost-of-pattern calculator in ₹
- Voice input for technicians logging incidents

### Non-Goals

- No generic chatbot interface
- No real sensor or IoT integration
- No authentication beyond a simple demo user
- No charts that don't answer a question

---

## 17. Hackathon Submission Checklist

- [ ] GitHub repository: clean code, clear README, `.env.example`, setup steps, architecture diagram
- [ ] README section: **"How ORIGIN Uses Hindsight"**, covering what is retained, when recall and reflect happen, and a before/after example
- [ ] Demo video (under 3 minutes) following the script in Section 15
- [ ] Live demo ready, with `/demo/reset` tested so it runs identically every time
- [ ] Every team member: article, social media post, and video, per the official content guide

### How ORIGIN Maps to the Judging Criteria

| Criteria | Weight | How ORIGIN Scores |
|---|---|---|
| Innovation | 30% | Root-cause discovery across time and machines in manufacturing, a fresh domain; failed-fix memory; fair evidence grading |
| Use of Hindsight Memory | 25% | Memory is the product: Amnesia Mode comparison, live Memory Trace, learning loop with preventive alerts |
| Technical Implementation | 20% | Hybrid deterministic + LLM analysis, validated outputs, decoy handling, repeatable demo |
| User Experience | 15% | Investigation console, animated timeline, a demo that tells a story in 60 seconds |
| Real-world Impact | 10% | Downtime and lost production in ₹; knowledge loss when senior staff leave; clear buyer (plant maintenance heads) |

---

## 18. Future Vision

Today: **Breakdown → Root Cause.**

Next, ORIGIN ingests maintenance logbooks (photo → text), WhatsApp maintenance groups, procurement and supplier records, sensor data, and quality rejection reports.

Eventually, ORIGIN becomes every factory's **long-term memory of failure and recovery**, so that when an experienced technician retires, their knowledge stays.

> **Don't just fix today's breakdown. Remember enough about yesterday's to stop repeating it tomorrow.**
