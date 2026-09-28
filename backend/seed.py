"""Load the demo plant history into Hindsight.

Usage:
    python seed.py            # seed the bank (run once)
    python seed.py --fresh    # delete the bank first, then seed

Hindsight extracts facts from each record in the background, so give it a few
minutes after seeding before you run the demo.
"""
import asyncio
import sys

from app import ledger
from app.config import BANK_ID, HINDSIGHT_API_KEY, load_seed_records
from app.memory import get_memory


async def main():
    if not HINDSIGHT_API_KEY:
        print("HINDSIGHT_API_KEY is empty in backend/.env. Add it first (see README).")
        sys.exit(1)
    mem = get_memory()
    if "--fresh" in sys.argv:
        print(f"Deleting bank {BANK_ID} …")
        await mem.delete_bank()
    await mem.ensure_bank()
    records = load_seed_records()
    print(f"Retaining {len(records)} plant records into Hindsight bank '{BANK_ID}' …")
    for i in range(0, len(records), 8):
        chunk = records[i : i + 8]
        await mem.retain(chunk, wait=False)
        print(f"  queued {i + len(chunk)}/{len(records)}")
    ledger.reset()
    print("\nDone. Hindsight is processing the memories in the background.")
    print("Wait 3–5 minutes, then check https://ui.hindsight.vectorize.io → your bank → memories.")


if __name__ == "__main__":
    asyncio.run(main())
