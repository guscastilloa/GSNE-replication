# etl/config.py
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("ETL_DATA_DIR", "./data"))
LINKS = DATA_DIR / "harvested_links.json"
RAW = DATA_DIR / "raw.jsonl"
FAILED = DATA_DIR / "failed.txt"

def require(name):
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"{name} not set — see .env.example")
    return v