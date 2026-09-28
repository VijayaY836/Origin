"""Memory layer. Hindsight is the real memory; LocalMemory only exists so the
app can start before you add a key (the UI shows a loud warning in that mode)."""
import asyncio
import json
import logging
import re

from . import ledger
from .config import BANK_ID, HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL
from .records import record_id, to_memory_item

log = logging.getLogger("origin.memory")

BANK_MISSION = (
    "You are the long-term maintenance memory of Sahyadri Precision Components, an auto-parts plant in Chakan, Pune. "
    "Remember every machine breakdown, symptom, fix, part, oil supplier and batch, and what happened afterwards, "
    "so that recurring root causes can be found across months, shifts and machines."
)
REFLECT_MISSION = (
    "Act as a careful reliability engineer. Only state what the plant's memory supports. Distinguish confirmed causes, "
    "strong recurring patterns, possible factors and hypotheses. Never blame individual people; investigate systems, parts, "
    "suppliers and conditions. Always cite incident IDs."
)


class Hit(dict):
    """{document_id, text, record}"""


class HindsightMemory:
    mode = "hindsight"

    def __init__(self):
        from hindsight_client import Hindsight

        self.client = Hindsight(base_url=HINDSIGHT_BASE_URL, api_key=HINDSIGHT_API_KEY, timeout=120.0)

    async def ensure_bank(self):
        try:
            await self.client.acreate_bank(
                BANK_ID,
                name="ORIGIN — Sahyadri Precision Components",
                mission=BANK_MISSION,
                reflect_mission=REFLECT_MISSION,
                disposition_skepticism=5,
                disposition_literalism=4,
                disposition_empathy=2,
            )
        except Exception as e:  # bank already exists, or config not supported on this plan
            log.info("create_bank: %s", str(e)[:160])

    async def retain(self, records: list[dict], wait: bool = True):
        items = [to_memory_item(r) for r in records]
        for i in range(0, len(items), 8):
            await self.client.aretain_batch(BANK_ID, items[i : i + 8], retain_async=not wait)

    async def recall(self, query: str, tags: list[str] | None = None, budget: str = "mid", max_tokens: int = 4096) -> list[Hit]:
        kwargs = dict(query=query, budget=budget, max_tokens=max_tokens)
        if tags:
            kwargs.update(tags=tags, tags_match="any")
        resp = await self.client.arecall(BANK_ID, **kwargs)
        hits = []
        for res in resp.results or []:
            rec = None
            meta = res.metadata or {}
            if meta.get("record_json"):
                try:
                    rec = json.loads(meta["record_json"])
                except Exception:
                    rec = None
            doc_id = res.document_id or meta.get("record_id")
            if rec is None and doc_id:
                rec = ledger.get(doc_id)
            hits.append(Hit(document_id=doc_id, text=res.text, record=rec))
        return hits

    async def reflect(self, query: str, context: str, tags: list[str] | None = None) -> str | None:
        kwargs = dict(query=query, context=context, budget="low", max_tokens=700)
        if tags:
            kwargs.update(tags=tags, tags_match="any")
        resp = await self.client.areflect(BANK_ID, **kwargs)
        return (resp.text or "").strip() or None

    async def delete(self, doc_ids: list[str]):
        for d in doc_ids:
            try:
                await self.client.documents.delete_document(BANK_ID, d)
            except Exception as e:
                log.info("delete %s: %s", d, str(e)[:120])

    async def delete_bank(self):
        try:
            await self.client.adelete_bank(BANK_ID)
        except Exception as e:
            log.info("delete_bank: %s", str(e)[:120])


class LocalMemory:
    """Keyword recall over the ledger. For development only."""

    mode = "local"

    async def ensure_bank(self):
        pass

    async def retain(self, records, wait=True):
        pass  # ledger already holds them

    async def recall(self, query, tags=None, budget="mid", max_tokens=4096):
        from .records import narrative, tags_for

        words = {w for w in re.findall(r"[a-z0-9\-]+", query.lower()) if len(w) > 2}
        scored = []
        for r in ledger.all_records():
            if tags and not set(tags) & set(tags_for(r)):
                continue
            text = narrative(r)
            score = sum(1 for w in words if w in text.lower())
            if score:
                scored.append((score, r, text))
        scored.sort(key=lambda x: -x[0])
        limit = max(6, max_tokens // 250)
        return [Hit(document_id=record_id(r), text=t, record=r) for _, r, t in scored[:limit]]

    async def reflect(self, query, context, tags=None):
        return None

    async def delete(self, doc_ids):
        pass

    async def delete_bank(self):
        pass


_memory = None


def get_memory():
    global _memory
    if _memory is None:
        _memory = HindsightMemory() if HINDSIGHT_API_KEY else LocalMemory()
    return _memory


async def safe(coro, default=None, timeout: float = 60.0):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except Exception as e:
        log.warning("memory call failed: %s", str(e)[:200])
        return default
