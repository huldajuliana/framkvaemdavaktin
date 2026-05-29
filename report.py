# -*- coding: utf-8 -*-
"""
report.py — býr til (1) vefsíðuna (docs/index.html) úr sniðmáti og
(2) HTML fyrir daglega tölvupóstinn (statískt, þar sem póstforrit keyra ekki JS).
"""
import os
import json
import html as _html
from datetime import datetime

HERE = os.path.dirname(__file__)
TEMPLATE = os.path.join(HERE, "templates", "page_template.html")
OUT_PAGE = os.path.join(HERE, "docs", "index.html")

REGION_ORDER = [
    "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
    "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland",
    "Landið allt",
]
SCALE_LABEL = {"Risa": "Risaframkvæmd", "Stór": "Stór",
               "Miðlungs": "Miðlungs", "Lítil": "Lítil"}

# BYKO litir
BLUE = "#0a4ea0"
YELLOW = "#ffcb05"
INK = "#16140f"
PAPER = "#f2ede2"


def write_page(records: list) -> str:
    """Skrifar docs/index.html með gögnunum innfelldum sem JS-fylki."""
    # id reitur fyrir hverja færslu (sniðmátið notar hann ekki en gott að hafa)
    for i, r in enumerate(records):
        r.setdefault("id", i + 1)
    data_json = json.dumps(records, ensure_ascii=False)
    tpl = open(TEMPLATE, encoding="utf-8").read()
    page = tpl.replace("__DATA__", data_json)
    os.makedirs(os.path.dirname(OUT_PAGE), exist_ok=True)
    with open(OUT_PAGE, "w", encoding="utf-8") as f:
        f.write(page)
    return OUT_PAGE


def _esc(s: str) -> str:
    return _html.escape(s or "")


def build_email(new_records: list, total_on_page: int) -> str:
    """Statískt HTML fyrir póstinn — nýjar fréttir frá síðustu keyrslu."""
    today = datetime.now().strftime("%d.%m.%Y")
    rows = ""
    if not new_records:
        rows = (f'<tr><td style="padding:24px;color:#8c8475;font-style:italic;'
                f'font-family:Georgia,serif">Engar nýjar framkvæmdafréttir frá '
                f'síðustu keyrslu.</td></tr>')
    else:
        by_region = {}
        for r in new_records:
            by_region.setdefault(r["region"], []).append(r)
        for region in REGION_ORDER:
            items = by_region.get(region)
            if not items:
                continue
            rows += (f'<tr><td style="padding:22px 0 8px;border-bottom:2px solid {INK};">'
                     f'<span style="font-family:Georgia,serif;font-size:19px;font-weight:bold;'
                     f'color:{INK}">{_esc(region)}</span> '
                     f'<span style="font-family:monospace;font-size:11px;color:#8c8475">'
                     f'{len(items)} {"frétt" if len(items)==1 else "fréttir"}</span></td></tr>')
            for r in items:
                verk = " · ".join(_esc(v) for v in r["verk"])
                parts = []
                if r.get("tender"): parts.append("Útboð: " + _esc(r["tender"]))
                if r.get("start"):  parts.append("Framkvæmdir: " + _esc(r["start"]))
                if r.get("end"):    parts.append("Verklok: " + _esc(r["end"]))
                date_line = (f'<div style="font-family:monospace;font-size:11px;'
                             f'color:#5b6f3f;margin-top:5px">{" · ".join(parts)}</div>'
                             ) if parts else ""
                rows += (
                    f'<tr><td style="padding:14px 0;border-bottom:1px solid #e0d8c6">'
                    f'<a href="{_esc(r["url"])}" style="font-family:Georgia,serif;font-size:16px;'
                    f'color:{INK};text-decoration:none;font-weight:bold">{_esc(r["title"])}</a>'
                    f'<div style="font-family:Arial,sans-serif;font-size:13px;color:#46423a;'
                    f'margin:6px 0 8px;line-height:1.5">{_esc(r["sum"])}</div>'
                    f'<div style="font-family:monospace;font-size:11px;color:{BLUE}">'
                    f'<span style="background:#eef3fa;border:1px solid #cdddf0;border-radius:3px;'
                    f'padding:2px 6px">{_esc(r["type"])}</span> '
                    f'<span style="background:#eef3fa;border:1px solid #cdddf0;border-radius:3px;'
                    f'padding:2px 6px">{_esc(r["status"])}</span> '
                    f'<span style="background:#eef3fa;border:1px solid #cdddf0;border-radius:3px;'
                    f'padding:2px 6px">{_esc(SCALE_LABEL.get(r["scale"], r["scale"]))}'
                    f'{(" · " + _esc(r["scaleFig"])) if r.get("scaleFig") not in ("", "—") else ""}</span> '
                    f'<span style="color:#8c8475">{verk}</span> '
                    f'<span style="color:#8c8475">| {_esc(r["src"])}</span></div>{date_line}</td></tr>'
                )

    return f"""<!DOCTYPE html><html lang="is"><body style="margin:0;background:{PAPER};padding:0">
<table width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER}"><tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="max-width:620px;background:#fbf8f1;
  margin:20px;border:1px solid #d6cdb9;border-radius:8px">
  <tr><td style="height:8px;background:repeating-linear-gradient(135deg,{BLUE} 0 14px,{YELLOW} 14px 28px)"></td></tr>
  <tr><td style="padding:26px 28px 4px">
    <div style="font-family:monospace;font-size:11px;letter-spacing:3px;color:{BLUE};text-transform:uppercase">
      Daglegt yfirlit framkvæmda · {today}</div>
    <div style="font-family:Georgia,serif;font-size:34px;font-weight:bold;color:{INK};margin-top:6px">
      Framkvæmda<span style="color:{YELLOW};-webkit-text-stroke:1px {BLUE};text-shadow:0 0 1px {BLUE}">vaktin</span></div>
    <div style="font-family:Arial,sans-serif;font-size:13px;color:#46423a;margin-top:8px">
      {len(new_records)} nýjar fréttir frá síðustu keyrslu · {total_on_page} fréttir á vefnum þessa dagana.</div>
  </td></tr>
  <tr><td style="padding:8px 28px 24px">
    <table width="100%" cellpadding="0" cellspacing="0">{rows}</table>
  </td></tr>
  <tr><td style="padding:18px 28px;border-top:2px solid {INK};font-family:monospace;font-size:11px;color:#8c8475">
    Sjálfvirkt yfirlit · heimildir: mbl.is, Vísir, RÚV, HMS, Vegagerðin, Stjórnarráðið, sveitarfélög.
  </td></tr>
</table></td></tr></table></body></html>"""
