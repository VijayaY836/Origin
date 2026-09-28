# ORIGIN — The Memory of Every Breakdown

**HackwithHyderabad 3.0 · AI Agents That Learn Using Hindsight**

ORIGIN is an AI maintenance investigator for factories. It remembers every machine breakdown, every fix technicians tried, and whether that fix actually worked. When a machine fails again, ORIGIN connects breakdowns across months and machines to find the root cause nobody on the floor could see, and warns you before you repeat a fix that already failed.

> Don't just fix today's breakdown. Remember enough about yesterday's to stop repeating it tomorrow.

## The demo story

Sahyadri Precision Components (Chakan, Pune). Hydraulic press HP-04 keeps overheating. Technicians replaced the cooling fan, flushed the oil, replaced the relief valve. Each fix worked for 3–7 weeks, then the problem came back. HP-02 had a related failure too.

ORIGIN recalls the plant's history from Hindsight and finds what every breakdown shares: all of them started after procurement switched hydraulic oil to a cheaper supplier on 14 Feb. HP-06, still running on the old supplier's oil, had no problems. ORIGIN rules out coincidences (a power-cut breakdown, a CNC with similar symptoms, and the night-shift technician who reported most of them) and grades its finding as a **strong recurring pattern**, not a certainty.

After an engineer confirms the cause, ORIGIN remembers it. Six days later, HP-06 gets oil from the same supplier and warms up by 9°C. ORIGIN flags it instantly as a **confirmed root cause**, before a breakdown.

## Stack

| Layer | Tech |
|---|---|
| Memory | **Hindsight** (Vectorize) via the official `hindsight-client` SDK |
| LLM | **Groq** or **OpenRouter** (set `LLM_PROVIDER`), `openai/gpt-oss-120b` (fallback `qwen/qwen3-32b`) |
| Backend | Python, FastAPI |
| Frontend | React, Vite, Tailwind CSS |

## Run it locally

You need **Python 3.10+** and **Node.js 18+**.

### 1. Keys

```bash
cd backend
cp .env.example .env      # Windows: copy .env.example .env
```

Open `backend/.env` and fill in:

- `HINDSIGHT_API_KEY`: sign up at https://ui.hindsight.vectorize.io, create an API key, and add promo code `MEMHACK99` under Billing for $50 credit.
- `GROQ_API_KEY`: free at https://console.groq.com/keys
- Or use OpenRouter instead: set `LLM_PROVIDER=openrouter` and fill `OPENROUTER_API_KEY` (https://openrouter.ai/keys)

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python seed.py            # loads 41 plant records into Hindsight (run once)
uvicorn app.main:app --reload --port 8000
```

After seeding, **wait 3–5 minutes** so Hindsight can finish extracting facts in the background. You can watch the memories appear in the Hindsight dashboard.

### 3. Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The header should say **Hindsight memory connected**.

## Demo flow (3 minutes)

1. **Load tonight's breakdown.**
2. Switch to **Amnesia mode**, click **Analyze without memory**. The AI suggests the cooling fan and relief valve, both already tried.
3. Switch to **Memory on**, click **Investigate with plant memory**. Watch the memory trace, the timeline and the common factor appear.
4. Type `replace cooling fan` in **Proposed fix**. The previously-attempted warning appears.
5. Click **Confirm root cause**, then **Jump ahead to 19 June**. ORIGIN catches HP-06 before it breaks.
6. **Reset demo** before the next run.

## How ORIGIN uses Hindsight

Hindsight is ORIGIN's long-term memory, not a side database.

**Retain.** Every plant record is retained as its own memory: breakdowns (symptoms, fix, parts, supplier, batch, technician notes), oil deliveries, supplier changes, power events, handover notes, and engineers' root-cause decisions. Each memory carries its real timestamp (so Hindsight can reason over time), `machine:`, `system:` and `kind:` tags, a `document_id` pointing back to the record, and the structured record in metadata.

**Recall.** For a new breakdown, ORIGIN runs parallel recalls: one per sibling machine (scoped by tag), one for similar symptoms anywhere in the plant, one for plant events, one for plant notes, and one for past root-cause decisions. The memory trace panel shows each query, how many memories came back, and which records they point to.

**Reflect.** ORIGIN asks Hindsight to reflect over the plant's memory ("why does HP-04 keep having this problem, and what has been tried?"), using a reflect mission that forbids blaming people and requires citing incident IDs. The reflection is shown in the brief.

**Learning loop.** When an engineer confirms or rejects a cause, that decision is retained. The next investigation recalls it, so a confirmed cause upgrades future findings to **Confirmed root cause** and turns a repeat breakdown into a preventive alert.

### Why the reasoning is trustworthy

The LLM does not decide what the evidence is. `backend/app/analysis.py` computes it deterministically from the recalled records: which incidents are related, which are coincidental, how each past fix turned out (temporary if the problem returned within 60 days), which factors recur and against what baseline, and a control comparison with sibling machines. Groq only writes the plain-English brief on top of those computed facts, and every call has a validated fallback so the demo never breaks.

## Project layout

```
backend/
  app/
    main.py          API endpoints
    investigate.py   RETAIN → RECALL → CONNECT → EXCLUDE → REFLECT → INSIGHT pipeline
    analysis.py      deterministic evidence engine + failed-fix check
    memory.py        Hindsight integration (retain / recall / reflect)
    records.py       turns plant records into Hindsight memories
    llm.py           Groq calls, JSON validation, fallbacks
    ledger.py        write-through index for instant UI listing and clean resets
  data/seed/         the plant's 6-month history (incidents, events, plant config)
  data/demo.json     tonight's breakdown and the 19 June follow-up
  seed.py            loads the history into Hindsight
frontend/src/        React UI
docs/spec.md         product spec
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Memory backend and LLM status |
| POST | `/demo/load-today` | Load tonight's HP-04 breakdown |
| POST | `/incidents` | Log a new breakdown |
| POST | `/investigate/{id}?memory=true` | Full investigation (`memory=false` for Amnesia mode) |
| POST | `/check-fix` | Check a proposed fix against failed-fix memory |
| POST | `/confirm/{id}` | Confirm, reject, or mark a root cause as investigating |
| POST | `/demo/advance` | Jump to 19 June (HP-06 early warning) |
| POST | `/demo/reset` | Remove demo records and reset |
| GET | `/memory`, `/machines/{id}` | Browse plant memory |