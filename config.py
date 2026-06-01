# -*- coding: utf-8 -*-
"""
config.py — allar reglur fyrir síun og flokkun á einum stað.
Þetta er skráin sem þú breytir oftast: bætir við leitarorðum, verktökum,
sveitarfélögum o.s.frv. Ekkert annað í kóðanum þarf að snerta.
"""

# ---------------------------------------------------------------------------
# 1) HVAÐ TELST FRAMKVÆMDAFRÉTT?
# Frétt kemst inn ef titill eða útdráttur inniheldur EITTHVERT þessara orða.
# ---------------------------------------------------------------------------
KEYWORDS = [
    "framkvæmd", "framkvæmdir", "uppbygging", "íbúðauppbygging",
    "íbúðir", "íbúð ", "fjölbýli", "fjölbýlishús", "raðhús", "einbýli",
    "nýbygging", "byggingarleyfi", "byggingaráform", "byggingarframkvæmd",
    "deiliskipulag", "aðalskipulag", "skipulagsbreyting", "niðurrif",
    "innviðir", "innviðauppbygging", "vegagerð", "vegaframkvæmd", "vegabætur",
    "gatnagerð", "gatnamót", "brú ", "brúar", "jarðgöng", "göng ",
    "höfn", "hafnargerð", "stálþil", "borgarlína",
    "atvinnuhúsnæði", "skrifstofuhúsnæði", "verslunarhúsnæði",
    "gagnaver", "verksmiðja", "iðnaðarhúsnæði", "virkjun", "hótel",
    "útboð", "alútboð", "verktaki", "verktakar", "mannvirki", "mannvirkjagerð",
    "skóflustunga", "fokhelt", "reisugilli",
    # Hönnunar-/skipulagsstig: arkitektasamkeppnir og tillögur (SKIPULAG)
    "arkitekt", "samkeppni um", "hönnunarsamkeppni", "skipulagssamkeppni",
    "arkitektasamkeppni", "rammaskipulag", "vinningstillag", "vinningstillög",
    "skipulagstillag", "deiliskipulagstillag", "skipulagslýsing",
]

# Orð sem útiloka frétt (draga úr ruslfréttum). Notað varlega.
NEGATIVE_KEYWORDS = [
    "leikrit", "kvikmynd", "tónleikar",  # menningar-"uppbygging" o.þ.h.
]

# ---------------------------------------------------------------------------
# 2) LANDSHLUTAR
# Staður/sveitarfélag -> landshluti. Lykilorð leitað í titli + útdrætti.
# Fyrsta sem finnst ræður. Ef ekkert finnst -> "Landið allt".
# ---------------------------------------------------------------------------
REGION_ORDER = [
    "Höfuðborgarsvæðið", "Suðurnes", "Vesturland", "Vestfirðir",
    "Norðurland vestra", "Norðurland eystra", "Austurland", "Suðurland",
    "Landið allt",
]

REGION_KEYWORDS = {
    "Höfuðborgarsvæðið": [
        "reykjavík", "reykjavik", "kópavog", "hafnarfir", "hafnarfjör",
        "garðabæ", "garðabær", "mosfellsbæ", "mosfellsbær", "seltjarnarnes",
        "kjalarnes", "vogabyggð", "úlfarsárdal", "grafarvog", "grafarholt",
        "breiðholt", "vesturbæ", "miðborg", "straumsvík",
        "hringbraut", "landspítal", "elliðaár", "ártúnshöfða",
    ],
    "Suðurnes": [
        "reykjanesbæ", "reykjanesbær", "keflavík", "njarðvík", "grindavík",
        "suðurnesjabæ", "sandgerði", "garður", "vogar", "reykjanes",
        "ásbrú", "keflavíkurflugvöll",
    ],
    "Vesturland": [
        "akranes", "akranesi", "borgarnes", "borgarbyggð", "stykkishólm",
        "grundarfjör", "ólafsvík", "snæfellsnes", "hvalfjar", "dalabyggð",
        "búðardal",
    ],
    "Vestfirðir": [
        "ísafjör", "ísafirð", "bolungarvík", "patreksfjör", "tálknafjör",
        "bíldudal", "þingeyri", "súðavík", "vesturbyggð", "gufudalssveit",
        "djúpafjör", "gufufjör", "dýrafjar", "dynjandisheiði",
    ],
    "Norðurland vestra": [
        "sauðárkrók", "skagafjör", "blönduós", "skagaströnd", "hvammstanga",
        "húnaþing", "hofsós", "varmahlíð",
    ],
    "Norðurland eystra": [
        "akureyri", "akureyrar", "húsavík", "norðurþing", "dalvík",
        "ólafsfjör", "siglufjör", "fjallabyggð", "mývatn", "þingeyjarsveit",
        "grenivík", "skjálfandafljót", "hlíðarvell",
    ],
    "Austurland": [
        "egilsstað", "fljótsdalshérað", "múlaþing", "fjarðabyggð",
        "neskaupstað", "eskifjör", "reyðarfjör", "seyðisfjör", "vopnafjör",
        "djúpavog", "höfn í hornafir", "hornafjör", "fáskrúðsfjör",
    ],
    "Suðurland": [
        "selfoss", "árborg", "hveragerði", "ölfus", "þorlákshöfn",
        "vestmannaeyj", "hvolsvöll", "hella", "rangárþing", "vík í mýrdal",
        "mýrdal", "flúðir", "laugarvatn", "bláskógabyggð", "ölfusá",
        "skaftárhrepp", "kirkjubæjarklaustur", "þjórsárdal", "hvammsvirkjun",
    ],
}

DEFAULT_REGION = "Landið allt"

# ---------------------------------------------------------------------------
# 3) TEGUND  (Íbúðir / Innviðir / Atvinna)
# Forgangsröð: fyrsta sem passar ræður. Annars "Innviðir".
# ---------------------------------------------------------------------------
TYPE_RULES = [
    ("Íbúðir", [
        "íbúð", "fjölbýli", "raðhús", "einbýli", "íbúðauppbygging",
        "íbúðarhúsnæði", "húsnæðisuppbygging", "leiguíbúð", "búseturétt",
    ]),
    ("Atvinna", [
        "atvinnuhúsnæði", "skrifstofuhúsnæði", "verslunarhúsnæði", "gagnaver",
        "verksmiðja", "iðnaðarhúsnæði", "hótel", "atvinnuframkvæmd",
    ]),
    ("Innviðir", [
        "vegagerð", "vegaframkvæmd", "vegabætur", "gatnagerð", "gatnamót",
        "brú", "jarðgöng", "göng", "höfn", "stálþil", "borgarlína",
        "virkjun", "veitukerfi", "lagnir", "innviðir", "samgöngu",
        "spítal", "skóli", "leikskóli", "íþróttahús",
    ]),
]
DEFAULT_TYPE = "Innviðir"

# ---------------------------------------------------------------------------
# 4) VERKTAKAR / NEFNDIR AÐILAR
# Listi yfir fyrirtæki/aðila sem leitað er að í texta. Bættu við að vild.
# (key = það sem leitað er að í lágstöfum, value = það sem birtist sem merki)
# ---------------------------------------------------------------------------
CONTRACTORS = {
    "íav": "ÍAV",
    "íslenskir aðalverktakar": "ÍAV",
    "ístak": "Ístak",
    "þg verk": "ÞG verk",
    "jáverk": "Jáverk",
    "já verk": "Jáverk",
    "eykt": "Eykt",
    "munck": "Munck",
    "lns saga": "LNS Saga",
    "suðurverk": "Suðurverk",
    "loftorka": "Loftorka",
    "ósafl": "Ósafl",
    "vegagerðin": "Vegagerðin (verkkaupi)",
    "veitur": "Veitur (verkkaupi)",
    "reykjavíkurborg": "Reykjavíkurborg (verkkaupi)",
    "kanon arkitekt": "Kanon arkitektar (hönnun)",
    "ask arkitekt": "ASK arkitektar (hönnun)",
    "basalt arkitekt": "Basalt arkitektar (hönnun)",
    "yrki arkitekt": "Yrki arkitektar (hönnun)",
    "arkís": "Arkís arkitektar (hönnun)",
    "batteríið": "Batteríið arkitektar (hönnun)",
}
DEFAULT_CONTRACTOR = "Óútboðið"

# Hrein verktakafyrirtæki — ef nafn þeirra kemur fyrir telst fréttin
# framkvæmdatengd, jafnvel þótt almennt "framkvæmda"-orð vanti í textann.
BUILDER_HINTS = [
    "íav", "íslenskir aðalverktakar", "ístak", "þg verk", "jáverk",
    "já verk", "eykt", "munck", "lns saga", "suðurverk", "loftorka", "ósafl",
]

# ---------------------------------------------------------------------------
# 5) STAÐA FRAMKVÆMDA
# Forgangsröð frá "lengst komið" niður í "byrjunarreit": fyrsta sem passar ræður.
# (Þannig ræður "verklok" frekar en "útboð" ef bæði orð koma fyrir.)
# ---------------------------------------------------------------------------
STATUS_RULES = [
    ("Verklok", ["verklok", "lokið", "vígt", "vígð", "opnað", "tekið í notkun",
                 "tekin í notkun", "fullbúin"]),
    ("Í byggingu", ["í byggingu", "í fullum gangi", "rís", "rísa", "fokhelt",
                    "reisugilli", "í virkri", "steypa", "burðarvirki"]),
    ("Hafnar", ["skóflustunga", "framkvæmdir hafnar", "framkvæmdir hófust",
                "framkvæmdir hefjast", "jarðvinna", "gröftur"]),
    ("Útboð", ["útboð", "boðið út", "boðin út", "boðnir út", "býður út",
               "bjóða út", "bauð út", "auglýs", "tilboð", "alútboð",
               "rammasamning"]),
    ("Skipulag", ["deiliskipulag", "aðalskipulag", "skipulagsbreyting",
                  "rammaskipulag", "skipulagslýsing", "umhverfismat",
                  "viljayfirlýsing", "áform", "fyrirhuga",
                  "samkeppni um", "hönnunarsamkeppni", "skipulagssamkeppni",
                  "arkitektasamkeppni", "vinningstillag", "vinningstillög",
                  "skipulagstillag", "tillaga", "kynnt tillög", "arkitekt"]),
]
DEFAULT_STATUS = "Skipulag"

# ---------------------------------------------------------------------------
# 6) STÆRÐARGRÁÐA
# Reynt að lesa tölur úr texta (íbúðir, ma.kr., m², km). Mappað í flokk.
# ---------------------------------------------------------------------------
# Flokkar í lækkandi röð. (lágmark_ibudir, lágmark_milljardar) -> flokkur
SCALE_THRESHOLDS = [
    ("Risa",     {"ibudir": 400, "milljardar": 15}),
    ("Stór",     {"ibudir": 100, "milljardar": 5}),
    ("Miðlungs", {"ibudir": 20,  "milljardar": 1}),
    ("Lítil",    {"ibudir": 0,   "milljardar": 0}),
]
DEFAULT_SCALE = "Miðlungs"   # ef engar tölur finnast

# ---------------------------------------------------------------------------
# 8) MÁNUÐIR OG ÁRSTÍÐIR — fyrir lestur dagsetninga (útboð / framkvæmdir / verklok)
# ---------------------------------------------------------------------------
MONTHS = {
    "janúar": 1, "febrúar": 2, "mars": 3, "apríl": 4, "maí": 5, "júní": 6,
    "júlí": 7, "ágúst": 8, "september": 9, "október": 10, "nóvember": 11,
    "desember": 12,
}
SEASONS = {"vor": 4, "sumar": 7, "haust": 10, "vetur": 1}

# ---------------------------------------------------------------------------
# 9) Hve marga daga geymir safnið? (0 eða None = aldrei eyða — allt hleðst upp)
# ---------------------------------------------------------------------------
ARCHIVE_KEEP_DAYS = None

