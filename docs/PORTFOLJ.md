# Portföljunderlag

Arbetsunderlag för analysen av depån. Uppdateras när nya siffror hämtas via
Montrose-kopplingen. Se [MONTROSE.md](MONTROSE.md) för hur kopplingen sätts upp.

## Mål

| | |
|---|---|
| Målbelopp | 500 000 kr |
| Månadsinsättning | 10 000–15 000 kr |
| Nettolön | 40 000+ kr/mån |

Tid till målet vid 8 % antagen årsavkastning:

| Insättning/månad | Tid till 500 000 kr |
|---:|---:|
| 10 000 kr | ~3 år 6 mån |
| 12 500 kr | ~2 år 11 mån |
| 15 000 kr | ~2 år 6 mån |

**Nyckeltal:** vid 15 000 kr/mån i 30 månader är ~465 000 kr av slutsumman egna
insättningar. Avkastningen står för ~9 % av resultatet, insättningarna för ~91 %.
Urvalet av innehav har alltså begränsad hävstång på den här horisonten —
disciplinen i insättningarna avgör.

## Snapshot 2026-08-13

ISK 2684066. Totalt värde **15 604 kr**, varav **32,55 kr** i kassa.

| Innehav | Antal | Värde | Andel | Orealiserat |
|---|---:|---:|---:|---:|
| Montrose Global Monthly Dividend ETF (MONTDIV) | 75 | 7 593 kr | 48,8 % | +323 kr (+4,4 %) |
| SpaceX (SPCX) | 2 | 2 697 kr | 17,3 % | +460 kr (+20,5 %) |
| Montrose Global Leverage 125 (MONTLEV) | 19 | 2 524 kr | 16,2 % | +125 kr (+5,2 %) |
| MicroStrategy STRC (preferens) | 2 | 1 834 kr | 11,8 % | +93 kr (+5,3 %) |
| Handelsbanken B (SHB B) | 4 | 930 kr | 6,0 % | +2 kr (+0,3 %) |

Orealiserat totalt: **+1 003 kr (~+6,9 %)**. USD-exponering: **~29 %**.

## Avgiftsjämförelse — samma index, olika pris

| Produkt | Följer | Total avgift |
|---|---|---:|
| **MONTDIV** (innehav) | MSCI World | **0,44 %** |
| Montrose Global (samma leverantör, fond) | MSCI World | **0,09 %** |
| Avanza Global | Bred global | 0,08 % |
| Länsförsäkringar Global Index | MSCI World | 0,20 % |

MONTDIV kostar ~5x mot samma leverantörs vanliga globalfond. Skillnaden är
månadsutdelningen. **I ett ISK schablonbeskattas kapitalet oavsett**, så
utdelningen ger ingen skattefördel — den flyttar pengar till kassan som måste
återinvesteras manuellt. Vid 500 000 kr är prisskillnaden ~1 750 kr/år.

## Faktablad per innehav

### MONTDIV — Montrose Global Monthly Dividend
ISIN IE000DMPF2D5. MSCI World, ~1 500 bolag i 23 utvecklade marknader.
Avgift 0,39 % löpande + 0,05 % transaktion. Risknivå 6/7. Utdelning ~0,5 %/mån.

### MONTLEV — Montrose Global Leverage 125
Samma MSCI World med 1,25x hävstång. Förvaltning 0,41 % **plus
hävstångskostnad ~0,74 %** ≈ **1,15 %/år** all-in. Handelsstart april 2025,
kort historik. Risknivå 5/7. Hävstången lönar sig endast om marknadens
avkastning överstiger lånekostnaden; kostnaden dras oavsett riktning.

### SPCX — SpaceX
Noterad på Nasdaq **12 juni 2026**. Nu ordinarie listad amerikansk aktie.
**Bevaka:** lock-up för nynoteringar löper typiskt ut efter ~180 dagar, alltså
runt **december 2026**. Känt utbudstryck — ett datum att ha i kalendern, inte
en prognos.

### STRC — MicroStrategy Variable Rate Series A Perpetual Stretch Preferred
**11,5 % direktavkastning, betald månadsvis.** Nominellt 100 USD, emitterad
juli 2025 till 90 USD. **Evig löptid** — ingen förfallodag, ingen inlösen till
nominellt belopp. Rörlig ränta.
Detta är ett **kreditinstrument**, inte en tillväxtaktie: avkastningen är
räntan, inte kursuppgång. Strategys balansräkning är bitcoin, så betalförmågan
hänger på bitcoinpriset. 11,5 % är marknadens pris på den risken.

### SHB B — Handelsbanken B
930 kr, 6 % av portföljen. För liten position för att påverka utfallet.

## Strukturella observationer

- **Dubbelköpt index:** MONTDIV och MONTLEV följer båda MSCI World. ~65 % av
  portföljen är samma underliggande exponering i två förpackningar med olika
  prislapp. Det är inte diversifiering.
- **Koncentration:** 49 % i ett innehav.
- **Valuta:** ~29 % USD-noterat.
- **Kort horisont, hög risk:** 2,5–3,5 år till målet med 100 % aktier, varav en
  del med hävstång. Ett fall på 30–40 % är normalt och skulle på den här
  horisonten vara svårt att sitta ut. Öppen fråga: är 500 000 kr **ett datum
  eller ett belopp?**
- **Kassabuffert:** inte utrett om sådan finns vid sidan av depån.

## Kvar att göra

- [ ] Genomsökning av Montrose fulla utbud på avgift och innehåll
  (`search_instruments` via kopplingen)
- [ ] Överlappsanalys — vilka bolag som återkommer i flera innehav
- [ ] Målspårare: verkligt depåvärde mot plan, inklusive scenario med −30 %
- [ ] STRC-prospektet hos SEC — villkoren för den rörliga räntan
- [ ] Bekräfta insättningsbelopp (10 000, 12 500 eller 15 000 kr/mån)

---

*Inte finansiell rådgivning. Underlag för egna beslut.*
