# -*- coding: utf-8 -*-
"""
store.py — varanlegt safn allra frétta (archive.json).
Ekkert eyðist sjálfkrafa: safnið hleðst upp dag frá degi.
Geymt sem { lykill: færsla } og vistað aftur í git eftir hverja keyrslu.
"""
import json
import hashlib
import os
import re
from datetime import datetime, timezone, timedelta

import config as C

ARCHIVE_FILE = os.path.join(os.path.dirname(__file__), "archive.json")


def _key(record: dict) -> str:
    base = (record.get("url") or record.get("title", "")).strip().lower()
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


# Algeng orð + "umgjörðar-sagnir" sem greina ekki fréttir í sundur og eiga því
# ekki að telja með þegar borið er saman hvort tvær fréttir fjalli um sama atburð.
_STOP = {
    "og", "í", "á", "um", "sem", "að", "er", "við", "til", "af", "með", "fyrir",
    "en", "eða", "þó", "þá", "nú", "hér", "þar", "frá", "inn", "út", "upp", "niður",
    "yfir", "undir", "gegn", "eftir", "milli", "ný", "nýr", "nýtt", "nýja", "nýjar",
    "nýir", "hlýtur", "hlaut", "fær", "fékk", "verður", "verði", "var", "vera",
    "hefur", "hafa", "mun", "munu", "ekki", "þessi", "þetta", "þessa", "sinn",
    "sitt", "sín", "ohf", "hf", "ehf", "the", "segja", "segir", "vilja", "vill",
}


def _sig_seq(title: str) -> list:
    """Einkennisorð úr titli í RÖÐ: lágstafir, algeng orð fjarlægð, létt stofnun
    (6 stafir) svo beygingarmyndir falli saman. Röðin varðveitir nálægð orða (eftir
    að algeng orð eins og 'og' eru fjarlægð) svo hægt sé að skoða orðapör."""
    words = re.findall(r"[a-záðéíóúýþæö]+", (title or "").lower())
    return [w[:6] for w in words if len(w) >= 3 and w not in _STOP]


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

    # Fella saman sömu frétt frá ólíkum miðlum (ólíkar slóðir OG ólíkir titlar, svo
    # _key nær þeim ekki). Aðferð: para aðeins ef fréttir deila SÉRKENNILEGU
    # ORÐAPARI Í RÖÐ (t.d. "göng brú") þar sem BÆÐI orðin eru sjaldgæf í safninu.
    # Þannig valda hvorki almenn útboðsorðapör ("lægsta tilboð", "hafnað gatnagerð")
    # né stök staðaheiti (Suðurlandsbraut, Landspítali) pörun — það þarf sérkennilega
    # samsetningu sem einkennir tiltekinn atburð/verk. Íhaldssamt með ásetningi:
    # betra að sýna stöku tvírit en að fela ólíkar, raunverulegar fréttir.
    sets = [set(_sig_seq(r.get("title", ""))) for r in recs]
    df = {}
    for s in sets:
        for tok in s:
            df[tok] = df.get(tok, 0) + 1
    n = len(recs) or 1
    rare_cap = max(3, int(0.02 * n))  # "sjaldgæft" = í mesta lagi ~2% frétta

    def _same_story(a: set, b: set) -> bool:
        if not a or not b:
            return False
        inter = a & b
        if len(inter) < 2:
            return False
        # há heildarskörun titlanna (líkir titlar, ekki bara stök sameiginleg orð)
        if len(inter) / len(a | b) < 0.6:
            return False
        # OG a.m.k. eitt sameiginlegt orð sé sérkennilegt (sérnafn/verkheiti) — svo
        # titlar sem deila aðeins almennum orðum (framkvæmdir, haust, tilboð) renni
        # ekki saman þótt skörun sé há.
        return any(df.get(t, 0) <= rare_cap for t in inter)

    out = []
    kept_sets = []  # einkennisorð þeirra frétta sem þegar eru birtar
    for r, s in zip(recs, sets):
        if any(_same_story(s, ks) for ks in kept_sets):
            continue
        kept_sets.append(s)
        out.append(r)
    return out


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
