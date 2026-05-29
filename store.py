# -*- coding: utf-8 -*-
"""
store.py — varanlegt safn allra frétta (archive.json).
Ekkert eyðist sjálfkrafa: safnið hleðst upp dag frá degi.
Geymt sem { lykill: færsla } og vistað aftur í git eftir hverja keyrslu.
"""
import json
import hashlib
import os
from datetime import datetime, timezone, timedelta

import config as C

ARCHIVE_FILE = os.path.join(os.path.dirname(__file__), "archive.json")


def _key(record: dict) -> str:
    base = (record.get("url") or record.get("title", "")).strip().lower()
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def load() -> dict:
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save(archive: dict) -> None:
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=1)


def merge(archive: dict, records: list) -> list:
    """Bætir nýjum fréttum í safnið. Skilar lista yfir þær sem voru NÝJAR.
    Eldri fréttir halda upprunalegu 'first_seen' og er ekki breytt."""
    now = datetime.now(tz=timezone.utc).isoformat()
    new = []
    for r in records:
        k = _key(r)
        if k in archive:
            r["first_seen"] = archive[k].get("first_seen", now)
            # höldum eldri færslu óbreyttri (varðveitum fyrstu skráningu)
        else:
            r["first_seen"] = now
            archive[k] = r
            new.append(r)
    return new


def to_list(archive: dict) -> list:
    recs = list(archive.values())
    recs.sort(key=lambda r: (r.get("first_seen", ""), r.get("date", "")), reverse=True)
    return recs


def prune(archive: dict) -> dict:
    """Eyðir engu nema ARCHIVE_KEEP_DAYS sé sett (sjálfgefið None = aldrei eyða)."""
    days = getattr(C, "ARCHIVE_KEEP_DAYS", None)
    if not days:
        return archive
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    kept = {}
    for k, v in archive.items():
        try:
            if datetime.fromisoformat(v["first_seen"]) >= cutoff:
                kept[k] = v
        except Exception:  # noqa: BLE001
            kept[k] = v
    return kept
