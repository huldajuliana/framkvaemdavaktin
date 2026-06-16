# -*- coding: utf-8 -*-
"""
main.py — daglega keyrslan. Tengir saman alla hlutana:
  1) les heimildir,  2) sækir fréttir,  3) síar + flokkar (m.a. dagsetningar),
  4) bætir í varanlegt safn,  5) skrifar vefsíðu,  6) sendir póst um nýtt.
"""
import logging
from datetime import datetime

import yaml

import collector
import classify
import store
import report
import mailer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


def load_sources(path="sources.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["sources"]


def main():
    sources = load_sources()

    raw = collector.collect(sources)
    records = classify.classify_all(raw)
    log.info("%d af %d fréttum töldust framkvæmdafréttir", len(records), len(raw))

    archive = store.load()
    # Sjálfhreinsun: endurmeta allt safnið með NÚVERANDI síu og fjarlægja efni sem
    # stenst hana ekki lengur (t.d. eldra rusl sem komst inn með lausari síu).
    # Aðeins ranglega flokkað efni fer út; raunverulegar fréttir haldast.
    _before = len(archive)
    archive = classify.refilter_archive(archive)
    if len(archive) != _before:
        log.info("Sjálfhreinsun: fjarlægði %d ranglega flokkaðar færslur (%d eftir)",
                 _before - len(archive), len(archive))
    new = store.merge(archive, records)
    # Afritahreinsun: sama frétt frá fleiri en einum miðli (t.d. miðill sem
    # endurbirtir fyrirsögn annars) birtist aðeins einu sinni. Keyrt EFTIR merge
    # svo nýjar tvítekningar náist strax. Heldur þeirri sem sást fyrst.
    _before_dd = len(archive)
    archive = classify.dedupe_archive(archive)
    if len(archive) != _before_dd:
        log.info("Afritahreinsun: fjarlægði %d tvítekningar (%d eftir)",
                 _before_dd - len(archive), len(archive))
        new = [r for r in new if store._key(r) in archive]
    log.info("%d nýjar fréttir bættust í safnið (%d alls)", len(new), len(archive))

    # Vefurinn sýnir ALLT safnið, nýjast efst
    page_records = store.to_list(archive)
    out = report.write_page(page_records)
    log.info("Vefsíða skrifuð: %s (%d fréttir í safni)", out, len(page_records))

    # Póstur: aðeins nýjar fréttir frá síðustu keyrslu
    subject = f"Framkvæmdavaktin · {datetime.now():%d.%m.%Y} · {len(new)} nýjar fréttir"
    email_html = report.build_email(new, len(page_records))
    mailer.send(subject, email_html)

    store.save(store.prune(archive))
    log.info("Lokið.")


if __name__ == "__main__":
    main()
