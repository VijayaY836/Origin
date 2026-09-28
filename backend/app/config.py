"""Settings and static plant data."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
LEDGER_PATH = DATA_DIR / "ledger.json"

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "").strip()
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "qwen/qwen3-32b").strip()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()  # groq | openrouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b").strip()
OPENROUTER_FALLBACK_MODEL = os.getenv("OPENROUTER_FALLBACK_MODEL", "qwen/qwen3-32b").strip()
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").strip()

PLANT = json.loads((SEED_DIR / "plant.json").read_text(encoding="utf-8"))
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", PLANT["bank_id"]).strip()
MACHINES = {m["id"]: m for m in PLANT["machines"]}
DEMO = json.loads((DATA_DIR / "demo.json").read_text(encoding="utf-8"))

# Fix outcome rules (spec section 6)
RECURRENCE_WINDOW_DAYS = 60
INEFFECTIVE_WINDOW_HOURS = 48


def load_seed_records() -> list[dict]:
    incidents = json.loads((SEED_DIR / "incidents.json").read_text(encoding="utf-8"))
    events = json.loads((SEED_DIR / "events.json").read_text(encoding="utf-8"))
    return incidents + events