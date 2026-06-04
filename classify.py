# -*- coding: utf-8 -*-
"""
classify.py — síar framkvæmdafréttir og merkir þær:
landshluti, tegund, verktaki/-ar, staða og stærðargráða.
"""
import re
import config as C


def _text(item: dict) -> str:
    return (item["title"] + " " + item.get("summary", "")).lower()


# Markaðs-/talningarefni um húsnæði — íbúðamarkaður, leigumarkaður, talningar HMS o.fl.
# Þetta telst framkvæmdatengt enda lýsir það framboði og uppbyggingu íbúða.
_HOUSING_MARKET = [
    "íbúðamarkað", "húsnæðismarkað", "leigumarkað", "fasteignamarkað",
    "íbúðatalning", "talningar á íbúð", "talning á íbúð", "fullbúnar íbúðir",
    "íbúðum fjölgar", "framboð íbúða", "íbúðir í byggingu", "íbúðauppbygging",
    "mánaðarskýrsla hms", "íbúðaþörf", "húsnæðisþörf",
]

# Veik lykilorð: húsgerðir sem birtast oft í ÓSKYLDUM fréttum (brunar, slys,
# stríð, viðburðir). Þau duga EKKI ein og sér — það þarf framkvæmda-samhengi með.
_WEAK_TYPES = [
    "einbýli", "fjölbýli", "fjölbýlishús", "raðhús", "hótel",
    "atvinnuhúsnæði", "skrifstofuhúsnæði", "verslunarhúsnæði", "iðnaðarhúsnæði",
]

# Samhengisorð sem staðfesta að um framkvæmd/byggingu sé að ræða. Eitt þeirra
# þarf að fylgja veiku lykilorði til að fréttin teljist framkvæmdafrétt.
_CONTEXT = [
    "framkvæmd", "bygging", "byggja", "byggð", "byggt", "byggður", "byggi",
    "reisa", "rís", "reist", "útboð", "skipulag", "byggingarlóð", "lóðaúthlut",
    "niðurrif", "nýbygg",
    "fokhelt", "skóflustung", "verktak", "uppbygg", "áform", "fyrirhug", "hófst",
]


def _builder_in(t: str) -> bool:
    """Satt ef verktakanafn finnst í texta — en aðeins í UPPHAFI orðs, svo
    undirstrengir valdi ekki ruslfréttum (t.d. "Já verk" má ekki passa við
    "sjá verk", né "Eykt" við "reykt"). Beygingar í enda leyfast ("Ístaks")."""
    return any(re.search(r"(?<!\w)" + re.escape(b), t) for b in C.BUILDER_HINTS)


def is_relevant(item: dict) -> bool:
    t = _text(item)
    # Afdráttarlaus höfnun á augljóslega ótengdum flokkum (sakamál, dómsmál,
    # menning, íþróttir, andlát). Þessi orð koma nær aldrei fyrir í alvöru
    # framkvæmdafréttum, svo ef eitthvert þeirra finnst er fréttinni hafnað.
    if any(neg in t for neg in C.NEGATIVE_KEYWORDS) or any(neg in t for neg in _HARD_NEGATIVES):
        return False
    # Traust heimild: HMS (Húsnæðis- og mannvirkjastofnun) fjallar nær eingöngu um
    # húsnæði, mannvirki og íbúðamarkað — treystum efni þaðan (t.d. mánaðarskýrslum
    # og talningum á íbúðamarkaði), nema það hafi lent í hörðu útilokuninni að ofan.
    if "hms.is" in item.get("link", "").lower() or "hms" in item.get("source", "").lower():
        return True
    # Nafn verktaka (í upphafi orðs) -> telst framkvæmdatengt.
    if _builder_in(t):
        return True
    # Annars þarf framkvæmdaorð. Sleppum of almennum orðum sem valda ruslfréttum:
    # "íbúð " (hvaða íbúð sem er) og "höfn" (passar við hafnarbæi eins og
    # Reykjavíkurhöfn). Raunverulegar hafnarframkvæmdir nota "stálþil"/"hafnargerð".
    # Markaðs-/talningarefni um húsnæði telst líka framkvæmdatengt (óháð heimild).
    if any(k in t for k in _HOUSING_MARKET):
        return True
    # Hreinsum "false friends": "framkvæmdastjóri"/"framkvæmdastjórn" (starfsheiti)
    # og "framkvæmdavald" (stjórnmál) mega ekki kveikja á lykilorðinu "framkvæmd".
    t_kw = t.replace("framkvæmdastjór", " ").replace("framkvæmdavald", " ")
    # "háskólabrú" (aðfaranám, t.d. hjá Keili) er NÁMSLEIÐ, ekki samgöngubrú — má
    # ekki kveikja á lykilorðinu "brú ". Hreinsum áður en lykilorð eru metin.
    t_kw = t_kw.replace("háskólabrú", " ")
    # "framkvæmd stefnu/laga/áætlunar/skólastefnu" = INNLEIÐING stefnu/laga, ekki
    # bygging — látum slíkt ekki kveikja á "framkvæmd". (Heldur "Framkvæmdir hefjast
    # við ..." óbreyttu, því þar fylgir ekki stefnu-/laga-orð.)
    t_kw = re.sub(
        r"framkvæmd\w*\s+(stefn|skólastefn|menntastefn|lag|áætlun|fjárlag|samning|regln|sáttmál)\w*",
        " ", t_kw)
    # Sterk lykilorð (ótvíræð framkvæmdaorð) duga ein og sér.
    if any(k in t_kw for k in C.KEYWORDS if k not in _WEAK_TYPES and k not in ("íbúð ", "höfn")):
        return True
    # Veik lykilorð (húsgerðir) hleypa frétt aðeins inn EF framkvæmda-samhengi fylgir
    # — annars er t.d. brunafrétt um "einbýlishús" ekki framkvæmdafrétt.
    if any(w in t_kw for w in _WEAK_TYPES) and any(c in t_kw for c in _CONTEXT):
        return True
    return False


# Sterk útilokunarorð — fréttir sem innihalda þessi eru ekki framkvæmdafréttir.
_HARD_NEGATIVES = [
    # sakamál / dómsmál
    "líkamsárás", "fangelsi", "ákær", "saksókn", "héraðsdóm", "hæstirétt",
    "landsrétt", "kynferðis", "nauðgun", "manndráp", "fíkniefn", "ofbeldi",
    # menning / fólk
    "listamaður", "listamenn", "bæjarlistamaður", "tónleikar", "hljómsveit",
    "leikrit", "kvikmynd", "leikari", "leikkona", "söngvar", "rithöfundur",
    "leiksýning",
    # íþróttir
    "landslið", "deildarmeistar", "íslandsmeistar", "leikmaður", "leikmenn",
    # stjórnmál / utanríkismál (orðið "framkvæmd" á líka við um framkvæmd samninga)
    "utanríkisráðherra", "ees-samning", "evrópska efnahagssvæð", "evrópusamband",
    "þjóðaratkvæð", "sendiherra", "aðalræðismaður", "fullveldi", "alþjóðasamning",
    # sjávarútvegur (hvalveiði, vertíð o.fl. — "höfn" á við hafnarbæi)
    "hvalveiði", "hvalbát", "vertíð", "loðnu", "makríl", "fiskveiði", "þorskveiði",
    # annað
    "andlát", "minningarorð",
    # stríð / hernaður (byggingarorð eins og "uppbygging"/"fjölbýlishús" mega
    # ekki kveikja á hernaðar- eða stríðsfréttum)
    "hernað", "dróna", "dróni", "drónum", "loftárás", "innrás", "vopnabúna", "eldflaug",
    # eldsvoðar / slys / útkall (ekki byggingarfréttir þótt hús komi við sögu)
    "eldsvoð", "kviknaði", "bruna", "brunavörn", "slökkvilið", "sjúkrabíl", "reykeitrun",
    # félög / afmæli / hátíðahöld (t.d. "Hótel X" sem veislustaður)
    "ungmennafélag", "íþróttafélag", "afmæli",
    # menntastefna (ekki bygging skóla)
    "skólakerfi",
    # minniháttar viðhald — malbikun bílastæða/gatna, aðgangstilkynningar
    "malbikun",
    # fjármál / hlutabréfamarkaður ("útboð" á líka við um hlutafjárútboð á markaði)
    "hlutabréf", "frumútboð", "kauphöll", "skuldabréf", "verðbréf", "hlutafjárútboð",
    # sprengingar / stórslys (ekki framkvæmd þótt "verksmiðja"/"hús" komi við sögu)
    "sprakk", "höggbylgja", "í loft upp", "sprengju", "eldur kom upp",
    # þingnefndir / rannsóknarskýrslur (aldrei byggingarfréttir, þótt orð eins og
    # "uppbygging"/"framkvæmd" komi fyrir aftarlega í löngum texta) og menntastefna
    "rannsóknarnefnd", "skólastefn",
    # erlendar framkvæmdir (vefurinn er EINGÖNGU um íslenskar framkvæmdir) — t.d.
    # stórframkvæmdir Kushner/Trump í Albaníu. Stofninn "alban" nær öllum
    # beygingum (Albanir/Albanía/Albaníu/albanskur).
    "alban", "kushner",
]


def region_of(item: dict) -> str:
    t = _text(item)
    for region in C.REGION_ORDER:
        for kw in C.REGION_KEYWORDS.get(region, []):
            if kw in t:
                return region
    return C.DEFAULT_REGION


def type_of(item: dict) -> str:
    t = _text(item)
    for type_name, kws in C.TYPE_RULES:
        if any(kw in t for kw in kws):
            return type_name
    return C.DEFAULT_TYPE


def contractors_of(item: dict) -> list:
    t = _text(item)
    found = []
    for needle, label in C.CONTRACTORS.items():
        if needle in t and label not in found:
            found.append(label)
    return found or [C.DEFAULT_CONTRACTOR]


def status_of(item: dict) -> str:
    t = _text(item)
    for status_name, kws in C.STATUS_RULES:
        if any(kw in t for kw in kws):
            return status_name
    return C.DEFAULT_STATUS


# --- Stærðargráða: reynum að lesa tölur úr texta -------------------------
_NUM = r"(\d[\d.,\u00a0 ]*\d|\d)"

def _to_int(s: str) -> int:
    return int(re.sub(r"[^\d]", "", s) or 0)

def _to_float(s: str) -> float:
    s = re.sub(r"[^\d,.]", "", s).replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def scale_of(item: dict) -> tuple:
    """Skilar (flokkur, lýsing) t.d. ('Stór', '112 íbúðir')."""
    t = _text(item)
    ibudir = 0
    milljardar = 0.0
    fig = ""

    m = re.search(_NUM + r"\s*íbúð", t)
    if m:
        ibudir = _to_int(m.group(1))
        fig = f"{ibudir} íbúðir"

    m = re.search(_NUM + r"\s*(?:ma\.?kr|milljar)", t)
    if m:
        milljardar = _to_float(m.group(1))
        fig = fig or f"{m.group(1).strip()} ma.kr."

    if not fig:
        m = re.search(_NUM + r"\s*(?:m²|fermetr|ferm\.)", t)
        if m:
            fig = f"{m.group(1).strip()} m²"
        else:
            m = re.search(_NUM + r"\s*km\b", t)
            if m:
                fig = f"{m.group(1).strip()} km"

    for scale_name, th in C.SCALE_THRESHOLDS:
        if ibudir >= th["ibudir"] and ibudir > 0:
            return scale_name, fig
        if milljardar >= th["milljardar"] and milljardar > 0:
            return scale_name, fig

    return C.DEFAULT_SCALE, fig


def classify(item: dict) -> dict:
    scale, fig = scale_of(item)
    dates = extract_dates(item)
    return {
        "region": region_of(item),
        "type": type_of(item),
        "scale": scale,
        "scaleFig": fig or "—",
        "verk": contractors_of(item),
        "status": status_of(item),
        "src": item["source"],
        "date": item["published"].strftime("%Y-%m-%d"),
        "url": item["link"],
        "title": item["title"],
        "sum": (item.get("summary") or item["title"])[:240],
        "tender": dates["tender"],
        "start": dates["start"],
        "end": dates["end"],
        "tsort": dates["tsort"],
    }


def classify_all(items: list) -> list:
    # Dæmum relevans á SAMA stytta útdrætti og verður geymdur (sbr. 'sum'[:240] í
    # classify) svo söfnun og sjálfhreinsun séu samkvæmar. Annars getur frétt með
    # lykilorð aftarlega í löngum texta sloppið inn við söfnun en fallið við
    # hreinsun (af því geymslan klippir textann) — og hringrásast inn/út endalaust.
    out = []
    for it in items:
        probe = dict(it)
        probe["summary"] = (it.get("summary") or it.get("title", "") or "")[:240]
        if is_relevant(probe):
            out.append(classify(it))
    return out


def refilter_archive(archive: dict) -> dict:
    """Endurmetur allt vistað safn með NÚVERANDI is_relevant og skilar aðeins
    færslum sem standast. Notað til sjálfhreinsunar svo eldra rusl (sem komst inn
    með lausari síu) hverfi sjálfkrafa. Aðeins ranglega flokkað efni fer út.

    Öryggishemill: ef sían myndi henda meira en 60% safnsins er það líklega villa
    í síunni — þá skilum við safninu ÓBREYTTU frekar en að tapa raunverulegum
    fréttum."""
    kept = {
        k: r for k, r in archive.items()
        if is_relevant({
            "title": r.get("title", ""),
            "summary": r.get("sum", ""),
            "link": r.get("url", ""),
            "source": r.get("src", ""),
        })
    }
    if archive and len(kept) < len(archive) * 0.4:
        return archive
    return kept


# ---------------------------------------------------------------------------
# Dagsetningar: útboð, framkvæmdir hefjast, verklok
# ---------------------------------------------------------------------------
_MON = "|".join(sorted(C.MONTHS, key=len, reverse=True))
_RE_DMY = re.compile(r"(\d{1,2})\.\s*(" + _MON + r")\.?\s*(\d{4})", re.I)
_RE_MY = re.compile(r"\b(" + _MON + r")\.?\s*(\d{4})", re.I)
_RE_LOK = re.compile(r"(?:í\s+)?(?:lok\s+árs|árslok|lok)\s+(\d{4})", re.I)
_RE_SEAS = re.compile(r"\b(vor|sumar|haust|vetur)(?:ið|i)?\s+(\d{4})", re.I)
_RE_YEAR = re.compile(r"\b(20[2-4]\d)\b")
_RE_RANGE = re.compile(r"\b(20[2-4]\d)\s*(?:–|—|-|til|og)\s*(20[2-4]\d)\b", re.I)


def _ym(year, month) -> str:
    return f"{year}-{int(month):02d}"


def _parse_one(text: str):
    """Skilar (birtingartexti, röðunarlykill 'YYYY-MM') fyrir fyrstu dagsetningu."""
    m = _RE_DMY.search(text)
    if m:
        return f"{m.group(1)}. {m.group(2).lower()} {m.group(3)}", _ym(m.group(3), C.MONTHS[m.group(2).lower()])
    m = _RE_MY.search(text)
    if m:
        return f"{m.group(1).lower()} {m.group(2)}", _ym(m.group(2), C.MONTHS[m.group(1).lower()])
    m = _RE_LOK.search(text)
    if m:
        return f"lok {m.group(1)}", _ym(m.group(1), 12)
    m = _RE_SEAS.search(text)
    if m:
        return f"{m.group(1).lower()} {m.group(2)}", _ym(m.group(2), C.SEASONS.get(m.group(1).lower(), 1))
    m = _RE_YEAR.search(text)
    if m:
        return m.group(1), _ym(m.group(1), 1)
    return None


def _date_near(text: str, keywords, window: int = 75):
    low = text.lower()
    for kw in keywords:
        i = low.find(kw)
        if i >= 0:
            frag = text[i:i + len(kw) + window]
            d = _parse_one(frag)
            if d:
                return d
    return None


def extract_dates(item: dict) -> dict:
    t = item["title"] + " " + item.get("summary", "")
    out = {"tender": "", "start": "", "end": "", "tsort": ""}

    td = _date_near(t, ["útboð", "boðið út", "boðin út", "býður út", "bjóða út",
                        "tilboð", "auglýs", "rammasamning"], window=55)
    if td:
        out["tender"] = td[0]

    sd = _date_near(t, ["framkvæmdir hefjast", "framkvæmdir hefjist", "framkvæmdir hófust",
                        "verktími", "hefjast í", "hófust í", "skóflustunga",
                        "fara á fullt", "framkvæmdir eiga"])
    if sd:
        out["start"] = sd[0]

    ed = _date_near(t, ["verklok", "verkloka", "verki lýkur", "tilbúin",
                        "verður lokið", "verktíma"])
    if ed:
        out["end"] = ed[0]

    rng = _RE_RANGE.search(t)
    if rng:
        if not out["start"]:
            out["start"] = rng.group(1)
        if not out["end"]:
            out["end"] = rng.group(2)

    # Útboðsdagur á ekki að vera sami og verklok/upphaf (of gráðug gluggaleit)
    if out["tender"] and out["tender"] in (out["end"], out["start"]):
        out["tender"] = ""

    for key in ("tender", "start", "end"):
        if out[key]:
            p = _parse_one(out[key])
            if p:
                out["tsort"] = p[1]
                break
    return out
