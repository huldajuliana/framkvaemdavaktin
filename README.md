# Framkvæmdavaktin

Sjálfvirkur safnari sem les fréttatilkynningar um framkvæmdir á Íslandi —
íbúðauppbyggingu, innviði og atvinnuframkvæmdir — flokkar þær eftir
**landshluta, tegund, verktaka, stöðu og stærðargráðu**, birtir á vefsíðu og
sendir daglegt yfirlit í tölvupósti kl. 12:00.

Engin þörf á netþjóni: GitHub keyrir þetta frítt einu sinni á dag.

---

## Hvernig þetta virkar

```
sources.yaml  →  collector.py  →  classify.py  →  store.py  →  report.py  →  docs/index.html
   (RSS)          (sækir)          (síar+merkir+      (varanlegt    (byggir vef    + tölvupóstur
                                    les dagsetningar)   safn)         + tímalínu)     (mailer.py)
```

1. **collector.py** les RSS-strauma (og einfaldar HTML-síður þar sem ekki er RSS).
2. **classify.py** heldur eftir framkvæmdafréttum og merkir hverja: landshluta,
   tegund, verktaka, stöðu, stærðargráðu — og les **dagsetningar** úr textanum
   (útboð, upphaf framkvæmda og verklok) fyrir tímalínuna.
3. **store.py** geymir allt í **varanlegu safni** (`archive.json`). Ekkert eyðist:
   safnið byggist upp dag frá degi. Tvítekningar eru síaðar út eftir vefslóð.
4. **report.py** skrifar vefsíðuna (`docs/index.html`) með tveimur yfirlitum —
   **eftir landshluta** og **tímalínu** — og býr til póst-HTML.
5. **mailer.py** sendir póstinn (ef SMTP-stillingar eru til staðar) — aðeins með
   því sem er **nýtt** frá síðustu keyrslu.
6. **GitHub Actions** keyrir `main.py` daglega kl. 12:00 og vistar uppfærsluna
   (bæði `docs/index.html` og `archive.json`) aftur í geymsluna.
7. **backfill.py** (einu sinni) fyllir safnið aftur í tímann — sjá kafla neðar.

> Vefurinn man allt: hver ný keyrsla bætir við, fjarlægir aldrei. Þú getur síað
> eftir ári til að rýna í eldri verk, eða skipt yfir í tímalínu til að sjá röð
> útboða, framkvæmda og verkloka.

> Allir útdrættir koma úr efnisstraumum miðlanna sjálfra og hver frétt tengir
> beint á upprunann — við endurbirtum ekki greinar í heild.

---

## Uppsetning á GitHub (einu sinni)

### 1. Búðu til geymslu (repository)
Stofnaðu nýja geymslu (t.d. `framkvaemdavaktin`) og hladdu upp öllum skránum
úr þessum pakka (dragðu þær inn í „Add file → Upload files", eða `git push`).

### 2. Kveiktu á GitHub Pages
**Settings → Pages → Source: „Deploy from a branch" → Branch: `main`, mappa: `/docs` → Save.**
Eftir fyrstu keyrslu birtist vefurinn á
`https://<notandanafn>.github.io/framkvaemdavaktin/`.

### 3. Settu inn póststillingar (leynilyklar)
**Settings → Secrets and variables → Actions → „New repository secret".**
Búðu til þessa lykla (gildin sjást aldrei í kóðanum):

| Lykill | Dæmi um gildi | Skýring |
|--------|---------------|---------|
| `SMTP_HOST` | `smtp.office365.com` | póstþjónn |
| `SMTP_PORT` | `587` | gátt (STARTTLS) |
| `SMTP_USER` | `hulda@byko.is` | innskráning |
| `SMTP_PASS` | *(app-lykilorð)* | lykilorð / app-lykilorð |
| `EMAIL_FROM` | `hulda@byko.is` | sendandi |
| `EMAIL_TO` | `hulda@byko.is` | viðtakandi (má vera nokkrir, aðgreindir með kommu) |

> **BYKO notar líklega Microsoft 365.** Þá er `smtp.office365.com:587`. Stundum
> þarf IT-deildin að leyfa „SMTP AUTH" og þú þarft app-lykilorð (ekki venjulega
> lykilorðið) ef tveggja-þátta auðkenning er virk. Ef það er ekki í boði er
> einfaldast að nota fría þjónustu eins og **SendGrid** eða **Mailgun**:
> `SMTP_HOST=smtp.sendgrid.net`, `SMTP_USER=apikey`, `SMTP_PASS=<API-lykill>`.
>
> Ef póststillingar vantar keyrir vefurinn samt — bara án pósts.

### 4. Prófaðu strax
**Actions → „Framkvæmdavaktin – dagleg keyrsla" → „Run workflow".**
Þetta keyrir handvirkt svo þú þarft ekki að bíða til kl. 12. Skoðaðu logginn,
vefinn og pósthólfið.

Eftir það keyrir hún sjálf alla daga kl. 12:00 (íslenskur tími = UTC).

---

## Keyra á eigin vél (valfrjálst, til að prófa)

```bash
pip install -r requirements.txt
python main.py                # skrifar docs/index.html, reynir að senda póst
```

Til að prófa póst líka:
```bash
export SMTP_HOST=smtp.office365.com SMTP_PORT=587 \
       SMTP_USER=hulda@byko.is SMTP_PASS='...' \
       EMAIL_FROM=hulda@byko.is EMAIL_TO=hulda@byko.is
python main.py
```

---

## Bakfylling — saga aftur í tímann (einu sinni)

Til að safnið byrji ekki autt keyrirðu `backfill.py` einu sinni:

```bash
python backfill.py            # eins langt aftur og kemst (~3 ár)
python backfill.py --years 2  # eða takmarka við 2 ár
```

Það gerir tvennt:

1. **Hleður völdum lykilverkefnum** úr `backfill_seed.json` — handvalin, staðfest
   verkefni með réttum slóðum. Bættu við þau að vild (sama snið og fréttirnar).
2. **Reynir að ganga aftur í tímann** í opnum, síðuskiptum söfnum þeirra heimilda
   sem skilgreina `archive:` í `sources.yaml` (sjá dæmi neðst í skránni — afvirkt
   sjálfgefið). Vegagerðin og Stjórnarráðið eru líklegust til að virka.

Þetta þarf bara að keyra einu sinni; eftir það sér daglega keyrslan um framhaldið.

---

## Aðlögun — það sem þú breytir oftast

Allt er í **`config.py`**, vel merkt í köflum:

- **Leitarorð** (`KEYWORDS`) — hvað telst framkvæmdafrétt.
- **Landshlutar** (`REGION_KEYWORDS`) — bættu við sveitarfélögum/staðanöfnum.
- **Verktakar** (`CONTRACTORS`, `BUILDER_HINTS`) — bættu við fyrirtækjum til að
  sía eftir. Nafn þekkts verktaka eitt og sér dugar til að frétt komist inn.
- **Staða framkvæmda** (`STATUS_RULES`) — orð sem ákveða Skipulag / Útboð /
  Hafnar / Í byggingu / Verklok.
- **Stærðargráða** (`SCALE_THRESHOLDS`) — mörkin í íbúðafjölda og ma.kr.

Heimildir bætast við í **`sources.yaml`** (RSS helst; HTML-fallback fyrir síður
án RSS).

Útlit vefsins er í **`templates/page_template.html`** (sami stíll og prótótýpan).

---

## Heiðarlegir fyrirvarar

- **RSS-slóðir.** mbl.is-straumarnir eru staðfestir. Sumar hinna (t.d. Vísis,
  RÚV, Stjórnarráðsins) gætu þurft smá lagfæringu — keyrðu handvirkt og skoðaðu
  logginn; heimild sem svarar ekki er einfaldlega sleppt og hinar keyra áfram.
- **HTML-fallback** (HMS, Vegagerðin, sveitarfélög) er grófari en RSS; ef útlit
  síðu breytist gæti þurft að stilla `item_selector` í `sources.yaml`.
- **GitHub Actions keyrir frá Azure-vistföngum.** Örfáir vefir loka á slík
  vistföng. Ef tiltekin heimild bregst þannig má (a) keyra safnarann frekar af
  eigin vél/litlum netþjóni með `cron`, eða (b) sleppa þeirri heimild.
- **Sjálfvirk merking** (landshluti, verktaki, staða, stærð) er *besta mat* út
  frá texta — ekki fullkomin. Þú lagar reglurnar auðveldlega í `config.py`, og
  hver frétt tengir alltaf á upprunann svo hægt sé að sannreyna.
- **Dagsetningar á tímalínu** (útboð / framkvæmdir / verklok) eru lesnar úr texta
  fréttarinnar þegar þær finnast þar. Vanti dagsetningu í textann birtist fréttin
  í landshluta-yfirlitinu en ekki á tímalínunni.
- **Bakfylling.** Lykilverkefnin í `backfill_seed.json` eru áreiðanleg. Dýpri
  bakfylling úr opinberu söfnunum er *best-effort*: RSS geymir aðeins nýlegt efni,
  og mbl.is/Vísir hleypa hvorki að safni né bjóða eldra efni án áskriftar. Mesta
  sögulega dýptin fæst því úr opnu söfnunum (Vegagerðin, Stjórnarráðið, HMS,
  sveitarfélög) og safnast annars upp jafnt og þétt eftir því sem dögunum fjölgar.
- **Áskriftarefni.** Fyrir læstar greinar fæst aðeins útdrátturinn úr
  straumnum, ekki fullur texti — sem dugar fyrir yfirlitið.
