# -*- coding: utf-8 -*-
"""
classify.py — síar framkvæmdafréttir og merkir þær:
landshluti, tegund, verktaki/-ar, staða og stærðargráða.
"""
import re
import config as C


def _text(item: dict) -> str:
    # Fjarlægja mjúk bandstrik (U+00AD) sem sumir miðlar setja inni í orð í
    # fyrirsögnum (t.d. "Hag\u00adnýt", "hval\u00adveiðum") — þau brjóta orðaleit.
    return (item["title"] + " " + item.get("summary", "")).replace("\u00ad", "").lower()


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

# Þekktir mælingaaðilar (skoðanakannanir). Notað til að þekkja "[aðili] framkvæmdi
# könnun" — sögnin að framkvæma, ekki bygging. ("prósent" eitt og sér er sleppt
# því það er líka hundraðshluti; mælum frekar á aðila-nöfnum.)
_POLLSTERS = ["maskín", "gallup", "félagsvísindastofnun", "mmr", "prósent ehf"]


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
    # Erlend frétt: nefnir erlent land/þjóðerni og hefur ekkert íslenskt akkeri.
    # Vefurinn er eingöngu um íslenskar framkvæmdir.
    if _is_foreign(t):
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
    t_kw = t.replace("framkvæmdastjór", " ").replace("framkvæmdarstjór", " ").replace("framkvæmdavald", " ")
    # "háskólabrú" (aðfaranám, t.d. hjá Keili) er NÁMSLEIÐ, ekki samgöngubrú — má
    # ekki kveikja á lykilorðinu "brú ". Hreinsum áður en lykilorð eru metin.
    t_kw = t_kw.replace("háskólabrú", " ")
    # mánuðurinn "febrúar" inniheldur "brúar" — má ekki kveikja á brúar-lykilorðinu.
    t_kw = t_kw.replace("febrúar", " ")
    # "framkvæmd stefnu/laga/áætlunar/skólastefnu" = INNLEIÐING stefnu/laga, ekki
    # bygging — látum slíkt ekki kveikja á "framkvæmd". (Heldur "Framkvæmdir hefjast
    # við ..." óbreyttu, því þar fylgir ekki stefnu-/laga-orð.)
    t_kw = re.sub(
        r"framkvæmd\w*\s+(stefn|skólastefn|menntastefn|lag|áætlun|fjárlag|samning|regln|sáttmál|kosning|farsæld)\w*",
        " ", t_kw)
    # Kannanir: "[mælingaaðili] framkvæmdi könnun" / "könnun ... framkvæmd var fyrir
    # X" — sögnin að framkvæma, ekki bygging. Ef könnun er nefnd ÁSAMT þekktum
    # mælingaaðila, leyfum við "framkvæmd" ekki að vera eina byggingar-merkið.
    # (Snertir EKKI "jarðvegskönnun við framkvæmdir" — þar er enginn mælingaaðili.)
    if "könnun" in t_kw and any(ps in t_kw for ps in _POLLSTERS):
        t_kw = re.sub(r"framkvæmd\w*", " ", t_kw)
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
    # viðskipti / markaðs-samkeppni — t.d. "beita bolabrögðum í samkeppni um
    # þjónustu". (Höfnum EKKI á "samkeppni" — það grípur gildar hönnunar-/
    # skipulagssamkeppnir.)
    "bolabrögð", "samkeppniseftirlit",
    # sakamál / dómsmál
    "líkamsárás", "fangelsi", "ákær", "saksókn", "héraðsdóm", "hæstirétt",
    "landsrétt", "kynferðis", "nauðgun", "manndráp", "fíkniefn", "ofbeldi",
    # þjófnaður / innbrot / rán (t.d. innbrot í íbúðir aldraðra — kveikir á "íbúðir").
    # Ekki "lögregl" — "lögreglustöð byggð" er gild framkvæmd.
    "þjóf", "innbrot", "brotist inn", "stolið", "rán ", "handtek",
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
    # (Erlend lönd / þjóðerni: sjá _FOREIGN_TERMS + _iceland_anchor hér að neðan.
    # Þau hafna frétt aðeins ef ekkert íslenskt akkeri finnst í textanum.)
    # þingfundir / þingsköp — frétt um þingfundinn SJÁLFAN (slit, fundarhald,
    # gagnrýni á boðun) er ekki byggingarfrétt þótt rætt sé um innviðafrumvörp.
    "þingfund",
    # flokkapólitík / innanflokksmál — t.d. "Ráðleggur Miðflokksmönnum að breyta
    # um tón" (kveikir á "uppbygging" úr "uppbyggingarstarf í flokknum"). Höfnum
    # AÐEINS á ávarpi flokksmanna — EKKI á flokksheitunum sjálfum, því innviðafréttir
    # nefna oft flokka (bæjarstjórnir sem deila um framkvæmdir).
    "miðflokksmönn",
    # ferjusiglingar / áætlunarferðir — rekstur farþegaferja er ekki framkvæmd.
    # (Vegagerðin nefnd sem útgerðaraðili ferju má ekki kveikja á "vegagerð".)
    "áætlunarferð",
    # skemmdarverk á fornminjum/friðlýstu — frétt um spjöll er ekki framkvæmd þótt
    # "mannvirki" komi fyrir. (Höfnum EKKI á "fornleif" — gild frétt er t.d.
    # "fornleifar fundust við framkvæmdir, verki frestað".)
    "spellvirki",
    # sakamál: skotárásir o.fl. — "árásin framkvæmd" (sögnin að framkvæma) er ekki
    # bygging.
    "skotárás",
    # sjálfsvíg / sjálfsskaði — viðkvæmar fréttir sem mega ALDREI birtast á vaktinni
    # þótt orð eins og "brú"/"hús" komi fyrir (t.d. "kasta sér fram af brú").
    "sjálfsvíg", "sjálfsskað", "svipta sig líf", "kasta sér fram", "eigið líf",
    # slys og dauðsföll — umferðar-/bíl-/vinnu-/bana-slys o.fl. eru ekki
    # framkvæmdafréttir þótt staðsetning nefni "gatnamót"/"brú"/"hús". Stofninn
    # "slys" nær banaslys/umferðarslys/bílslys/vinnuslys; "lést"/"fórst"/"lét lífið"
    # ná dauðsföllum. ("andlát" er þegar á listanum hér að ofan.)
    "slys", "lést", "fórst", "lét lífið", "drukkn",
    # viðskipti / ráðningar — starfsmanna- og fyrirtækjafréttir ("uppbygging"
    # fyrirtækis/félags er ekki mannvirkjagerð), t.d. "ráðin í starf markaðsstjóra"
    # eða "nýtt endurskoðunar- og ráðgjafarfyrirtæki".
    "markaðsstjór", "ráðgjafarfyrirtæki",
    # skoðanakannanir / dánaraðstoð — "könnun ... framkvæmd[i]" (sögnin að
    # framkvæma). "dánaraðstoð" er líknardráps-umræða, aldrei framkvæmd.
    "skoðanakönnun", "dánaraðstoð",
    # sjávarútvegur / hvalveiðar
    "hvalveið",
    # félagsþjónusta — deilur ríkis/sveitarfélaga um þjónustu (kveikir á "framkvæmd
    # ... þjónustu"), t.d. þjónusta við börn með fjölþættan vanda.
    "fjölþættan vanda",
    # menningarumræða — abstrakt umfjöllun um "menningarinnviði" (leikhús/söfn) er
    # ekki framkvæmdafrétt; raunveruleg menningarhús-bygging notar "tónlistarhús" o.þ.h.
    "menningarinnvið",
    # auglýsingar / ráðgjafarefni — t.d. "Hagnýt ráð frá múrarameistara" (herferð).
    "hagnýt ráð",
    # lokun/viðhald lauga vegna skemmda (flögnun) — rekstrarfrétt, ekki framkvæmd.
    "flögnun", "flagna",
]

# --- Erlendar fréttir ------------------------------------------------------
# Vefurinn er EINGÖNGU um íslenskar framkvæmdir. Erlendar byggingar-/innviðafréttir
# kveikja oft á "uppbygging"/"framkvæmd"/"höfn"/"mannvirki". Því höfnum við frétt
# sem nefnir erlent land/þjóðerni — NEMA hún hafi líka íslenskt akkeri (íslenskt
# staðanafn eða "ísland/íslensk"), svo innlend frétt sem nefnir útlönd haldist inni
# (t.d. "norskt verktakafyrirtæki vann útboð í Reykjavík").
#
# Athugið: listinn er ekki tæmandi og beygingar/stofnar eru valdir til að rekast
# EKKI á íslensk orð/staðanöfn — t.d. "dönsk" (ekki "dansk" sem leynist í
# "danskennsla"), "noreg/norsk" (ekki "norð" sem er í "norðurland"), "austurrík"
# (ekki "austurland"), "spænsk/spánverj" (ekki "spán" sem er í "spánnýr").
_FOREIGN_TERMS = [
    # Mið-Austurlönd / svæði sem hafa birst á vaktinni
    "ísrael", "palestín", "vesturbakka", "gaza", "gasaströnd",
    "persaflóa", "mið-austurl", "íran", "íransk", "írönsk", "írak",
    "sýrland", "líbanon", "líbýa", "jemen", "sádi-arab", "katar", "dúbaí", "emírat",
    "afganistan", "afgansk",
    # Evrópa
    "alban", "ítalí", "ítölsk", "la spezia",
    "noreg", "norsk",
    "svíþjóð", "sænsk", "svíar",
    "danmörk", "dönsk", "danir",
    "finnland", "finnsk",
    "þýskaland", "þýsk", "þjóðverj",
    "frakkland", "frönsk", "fransk",
    "spánverj", "spænsk",
    "portúgal", "portúgalsk", "holland", "hollensk", "belgí", "sviss", "svissnesk",
    "austurrík", "austurrísk", "pólland", "pólverj",
    "rússland", "rússnesk", "rússar", "úkraín",
    "bretland", "bresk", "england", "englend", "skotland", "skosk",
    "írland", "írsk", "grikkland", "grísk",
    # Ameríka / Asía / Afríka
    "bandarík", "kanada", "kanadísk", "mexíkó", "brasilí", "argentín",
    "kína", "kínversk", "kínverj", "japan", "japansk",
    "indland", "indversk", "tyrkland", "tyrknesk", "afrík",
    # erlendir aðilar / fyrirtæki sem hafa birst (t.d. Kushner/Trump-paradís í
    # Albaníu; SpaceX-hlutafjárútboð — "útboð" þýðir bæði verkútboð og hlutafjárútboð)
    "kushner", "spacex",
]

# Íslensk akkeri: staðanöfn úr REGION_KEYWORDS auk almennra íslenskra vísana.
# Ef eitthvert þeirra finnst telst fréttin tengd Íslandi og fer EKKI í gegnum
# erlendu síuna. (Sleppum "vegagerð" sem akkeri — það er almennt orð sem getur
# átt við vegagerð erlendis líka.)
_ICELAND_ANCHORS = [
    "ísland", "íslensk", "íslend", "alþing", "sveitarfél",
    "sundabraut", "borgarlína", "hringveg", "þjóðveg",
    # Landshlutaheiti — REGION_KEYWORDS geymir bæjanöfn en EKKI landshlutaheitin
    # sjálf. ("austurland" með -a- rekst ekki á erlenda orðið "mið-austurlönd"
    # með -ö-.) "vestf"/"austf" ná Vestfjörðum/Austfjörðum og beygingum.
    "höfuðborgarsvæð", "suðurnes", "vesturland", "vestf", "norðurland",
    "austurland", "austf", "suðurland", "ísafjar",
] + [kw for kws in C.REGION_KEYWORDS.values() for kw in kws]


def _iceland_anchor(t: str) -> bool:
    # Gengisumreikningur ("... íslenskra króna") er EKKI vísbending um íslenska
    # frétt — algengt í erlendum fjármálafréttum. Fjarlægjum áður en akkeri metin.
    t = re.sub(r"íslensk\w*\s+krón\w*", " ", t)
    return any(a in t for a in _ICELAND_ANCHORS)


def _is_foreign(t: str) -> bool:
    """Satt ef erlent land/þjóðerni er nefnt OG ekkert íslenskt akkeri finnst."""
    return any(f in t for f in _FOREIGN_TERMS) and not _iceland_anchor(t)



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
# Afritahreinsun: sama frétt frá fleiri en einum miðli
# ---------------------------------------------------------------------------
def _dedup_signature(title: str) -> str:
    """Einkenni fréttar til að þekkja tvítekningar. Sami titill frá tveimur
    miðlum gefur sama einkenni: lágstafir, án dagsetningarforskeytis sem sumir
    miðlar setja fremst (t.d. "22.06.2026 ..."), og án greinarmerkja."""
    t = (title or "").lower().strip()
    t = re.sub(r"^\s*\d{1,2}\.\s*\d{1,2}\.\s*\d{2,4}\s*", "", t)  # dagsetningarforskeyti
    t = re.sub(r"[^0-9a-záéíóúýðþæö ]+", " ", t)                   # aðeins bók-/tölustafir
    return re.sub(r"\s+", " ", t).strip()


def _title_tokens(title: str):
    """Orðmengi titils (án dagsetningarforskeytis/greinarmerkja) til líkindamats."""
    s = re.sub(r"^\s*\d{1,2}\.\s*\d{1,2}\.\s*\d{2,4}\s*", "", (title or "").lower())
    s = re.sub(r"[^0-9a-záéíóúýðþæö ]+", " ", s)
    return frozenset(w for w in s.split() if len(w) > 2)


# Titlar sem deila a.m.k. þetta hlutfall orða teljast sama frétt (endurorðuð
# nær-eins fyrirsögn, t.d. "... til að byggja þjóðarhöll" vs "... til að hanna og
# byggja þjóðarhöll"). Hærra en þetta til að sameina ALDREI ólík útboð með
# formúlukenndum titlum ("X býður út Y").
_DEDUP_TITLE_SIM = 0.72


def dedupe_archive(archive: dict) -> dict:
    """Fjarlægir tvítekningar úr safninu: sömu frétt frá fleiri en einum miðli.
    Tvítekning = nákvæmlega samræmdur titill (óháð dagsetningarforskeyti/
    greinarmerkjum) EÐA mjög lík fyrirsögn (orðalíkindi >= _DEDUP_TITLE_SIM).
    Heldur þeirri færslu sem sást FYRST (elsta 'first_seen') svo röðun og saga
    haldist stöðug. Ólíkar fréttir með aðeins svipaða titla haldast óbreyttar."""
    seen = {}        # einkenni -> lykill sem haldið er
    kept = []        # [(tokenset, lykill)] til líkindasamanburðar
    drop = set()
    # elsta 'first_seen' fyrst -> sú færsla verður haldið, seinni tvítekningum sleppt
    for k, r in sorted(archive.items(), key=lambda kv: kv[1].get("first_seen", "")):
        title = r.get("title", "")
        sig = _dedup_signature(title)
        if not sig:
            continue
        toks = _title_tokens(title)
        is_dup = sig in seen
        if not is_dup and toks:
            for toks2, _ in kept:
                if toks2 and len(toks & toks2) / len(toks | toks2) >= _DEDUP_TITLE_SIM:
                    is_dup = True
                    break
        if is_dup:
            drop.add(k)
        else:
            seen[sig] = k
            kept.append((toks, k))
    if not drop:
        return archive
    return {k: r for k, r in archive.items() if k not in drop}


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
