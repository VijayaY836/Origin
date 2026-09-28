"""Write-through index of the records live in the current demo run.

Hindsight is the memory ORIGIN reasons from. This small JSON index mirrors
what was retained so the UI can list records instantly and so demo resets are
clean (records from an old run are ignored even if Hindsight still returns them).
"""
import json
import threading

from .config import LEDGER_PATH, load_seed_records
from .records import record_id

_lock = threading.Lock()


def _read() -> dict:
    if not LEDGER_PATH.exists():
        return reset()
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def reset() -> dict:
    data = {"records": {record_id(r): r for r in load_seed_records()}, "demo_ids": []}
    with _lock:
        LEDGER_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def upsert(r: dict, demo: bool = True) -> None:
    with _lock:
        data = _read()
        rid = record_id(r)
        data["records"][rid] = r
        if demo and rid not in data["demo_ids"]:
            data["demo_ids"].append(rid)
        LEDGER_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def get(rid: str) -> dict | None:
    return _read()["records"].get(rid)


def all_records() -> list[dict]:
    return list(_read()["records"].values())


def demo_ids() -> list[str]:
    return list(_read()["demo_ids"])


def known_ids() -> set[str]:
    return set(_read()["records"].keys())
