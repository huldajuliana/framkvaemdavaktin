# -*- coding: utf-8 -*-
"""
collector.py — sækir hráar fréttir úr heimildum (RSS eða HTML).
Skilar lista af dict: {title, link, summary, published (datetime), source}.
Þolir að einstakar heimildir svari ekki — skráir og heldur áfram.
"""
import time
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
import feedparser
from bs4 import BeautifulSoup

log = logging.getLogger("collector")

# Kurteist User-Agent — við segjum hver við erum og tengjum á upprunann.
HEADERS = {
    "User-Agent": "Framkvaemdavaktin/1.0 (frettasafnari; +https://github.com/)"
}
TIMEOUT = 25


def _clean(html_text: str) -> str:
    """Fjarlægir HTML-tög úr útdrætti og styttir."""
    if not html_text:
        return ""
    text = BeautifulSoup(html_text, "html.parser").get_text(" ", strip=True)
    return " ".join(text.split())


def _parse_date(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed"):
        val = entry.get(key)
        if val:
            return datetime.fromtimestamp(time.mktime(val), tz=timezone.utc)
    return datetime.now(tz=timezone.utc)


def fetch_rss(source: dict) -> list:
    items = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        for e in feed.entries:
            items.append({
                "title": _clean(e.get("title", "")),
                "link": e.get("link", "").strip(),
                "summary": _clean(e.get("summary", e.get("description", ""))),
                "published": _parse_date(e),
                "source": source["name"],
            })
        log.info("RSS %s -> %d færslur", source["name"], len(items))
    except Exception as exc:  # noqa: BLE001
        log.warning("RSS %s mistókst: %s", source["name"], exc)
    return items


def fetch_html(source: dict) -> list:
    """Einfaldur fallback fyrir síður án RSS: les hlekki af fréttalista.
    Ekki eins nákvæmt og RSS — titill er texti hlekksins, engin dagsetning.
    """
    items = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        base = source.get("base", source["url"])
        seen_links = set()
        for a in soup.select(source.get("item_selector", "a")):
            href = a.get("href", "")
            title = " ".join(a.get_text(" ", strip=True).split())
            if not href or len(title) < 25:        # sleppum stuttum/tómum hlekkjum
                continue
            link = urljoin(base, href)
            if link in seen_links:
                continue
            seen_links.add(link)
            items.append({
                "title": title,
                "link": link,
                "summary": "",
                "published": datetime.now(tz=timezone.utc),
                "source": source["name"],
            })
        log.info("HTML %s -> %d hlekkir", source["name"], len(items))
    except Exception as exc:  # noqa: BLE001
        log.warning("HTML %s mistókst: %s", source["name"], exc)
    return items


def collect(sources: list) -> list:
    all_items = []
    for src in sources:
        if src.get("type") == "html":
            all_items.extend(fetch_html(src))
        else:
            all_items.extend(fetch_rss(src))
    log.info("Samtals %d hráar færslur úr %d heimildum", len(all_items), len(sources))
    return all_items
