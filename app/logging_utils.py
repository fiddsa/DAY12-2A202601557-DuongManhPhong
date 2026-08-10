"""Structured JSON logging utilities."""
from __future__ import annotations
import json
from datetime import datetime, timezone

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def log_event(event: str, level: str = 'info', **fields) -> str:
    payload = {'event': event, 'level': level.lower(), 'timestamp': utc_now_iso(), **fields}
    raw = json.dumps(payload, ensure_ascii=False)
    print(raw)
    return raw
