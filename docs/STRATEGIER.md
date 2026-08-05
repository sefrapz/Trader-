# Tradingguide: strategierna, hävstången och riskerna

Den här guiden förklarar vad botens tre strategier gör, varför just de är
valda, hur hävstång faktiskt fungerar, och hur du testar vad som fungerar —
i stället för att tro på det.

## Först: en ärlighetsdeklaration

Det finns ingen "hemlig teknik" som tjänat pengar de senaste två åren och
som fortsätter göra det bara för att man kopierar den. Det som skiljer
handlare som överlever från dem som blåser kontot är nästan aldrig
signalen — det är **positionsstorlek, stoppar och disciplin**. Botens
risklager (1 % risk per trade, dagligt förluststopp, likvidationsskydd)
är därför viktigare än valet av strategi. Läs det här dokumentet med det
i bakhuvudet.

## De tre strategityperna

Boten implementerar de tre klassiska strategifamiljer som historiskt
fungerat i krypto. De tjänar pengar i **olika marknadsklimat** — ingen
fungerar jämt.

### 1. Trendföljning — `ema_cross`

Köper när en snabb EMA (12) korsar upp genom en långsam (26), shortar vid
korsning ner. RSI-filtret hoppar över entries i redan överdrivna lägen.

- **Vinner när:** marknaden trendar kraftigt åt något håll. Kryptos stora
  bull- och bear-ben är precis den miljön — det är därför trendföljning är
  den mest robusta strategifamiljen på krypto historiskt.
- **Förlorar när:** marknaden går sidledes. Då ger korsningarna falska
  signaler på löpande band, och många små förluster äter kapitalet.
  Det var exakt det du såg i ditt första backtest.

### 2. Breakout — `donchian`

Turtle-klassikern: long när priset stänger över de senaste 20 candlarnas
högsta, short under de lägsta. Exit när priset stänger utanför motsatt
10-kanal.

- **Vinner när:** volatilitet exploderar ur ett intervall — vilket i krypto
  ofta är hur de stora rörelserna börjar. Fångar trender tidigare än
  EMA-korsningen.
- **Förlorar när:** utbrott är falska ("fakeouts"), vilket är vanligt i
  intervall med låg volym.

### 3. Mean reversion — `rsi_meanrev`

Köper skarpa dippar (RSI < 30) men **bara i upptrend** (pris över EMA200),
shortar överköpta studsar bara i nedtrend. Exit när RSI normaliserats.

- **Vinner när:** marknaden rör sig i vågor kring en trend — den vanligaste
  miljön mellan de stora benen. Hög vinstandel, många små vinster.
- **Förlorar när:** dippen inte är en dipp utan början på en krasch.
  Trendfiltret och ATR-stoppen finns just därför.

### Vilken är "bäst"?

Det beror helt på perioden — och det är därför boten har ett
jämförelseläge i stället för ett påstående från mig. Mät själv på riktiga
2 år av Bybit-data (4h-candles, ~4380 st):

```
python main.py backtest --candles 4400 --strategy all
```

Kör det på både 1h, 4h och 1d (ändra `timeframe` i `config.yaml`) innan du
drar slutsatser. Det du letar efter är inte högsta avkastning på en enda
körning, utan en strategi som är **stabilt hygglig över flera perioder och
timeframes** — det är den som har störst chans att fungera framåt.

## Hävstång — så fungerar det på riktigt

I futures-läget handlar boten USDT-perpetuals på Bybit. Med hävstång X
lånar du upp positionen: du sätter bara in `notional / X` som marginal.
Vinster och förluster räknas dock på **hela** positionen.

Konsekvensen: en motrörelse på ungefär `100 % / X` utplånar hela
marginalen — då **likvideras** positionen automatiskt av exchangen.

| Hävstång | Marginal för 10 000 USDT position | Rörelse mot dig till likvidation* |
|---|---|---|
| 1x | 10 000 | ~90 % |
| 2x | 5 000 | ~45 % |
| 3x | 3 333 | ~30 % |
| 5x | 2 000 | ~18 % |
| 10x | 1 000 | ~9 % |
| 25x | 400 | ~3,6 % |

*ungefärligt; exchangens underhållsmarginal gör att det sker något tidigare.

BTC rör sig regelbundet 5–10 % på en dag. Vid 25x är en helt normal dags-
rörelse en likvidation — därför **vägrar boten hävstång över 10, och 2–3x
är den förnuftiga nivån**. Poängen med måttlig hävstång är inte att riska
mer, utan kapitaleffektivitet: samma positionsstorlek med mindre låst
kapital. Botens positionsstorlek styrs alltid av stoppavståndet så att en
stoppad trade kostar ~1 % av kapitalet — oavsett hävstång. Hävstången
flyttar bara likvidationspriset närmare.

Två saker till om perpetuals:

- **Funding:** var 8:e timme betalar den ena sidan en avgift till den andra
  (oftast longs som betalar i bullmarknad, typiskt ~0,01 % per 8h men mer i
  heta lägen). Backtestet simulerar **inte** funding, så räkna med att
  verklig avkastning för positioner som hålls länge blir något sämre än
  backtestet visar — särskilt för långsamma strategier på long-sidan.
- **Avgifter:** backtestet räknar med taker-avgift 0,055 % per sida
  (Bybit-nivå), spot 0,10 %.

## Shorts — att tjäna på nedgång

I futures-läge kan boten shorta: den säljer först och köper tillbaka
billigare. Det gör att strategierna kan tjäna pengar i björnmarknad i
stället för att bara stå utanför. Riskbilden är spegelvänd men med en
viktig asymmetri: en short kan teoretiskt förlora obegränsat (priset kan
stiga hur mycket som helst), vilket är ännu ett skäl att ATR-stoppen och
likvidationsmodellen alltid är aktiva. Vill du stänga av shorts:
`allow_shorts: false`.

## Så testar du seriöst (walk-forward-tänk)

1. **Jämför brett:** `--strategy all` på 2 års data, flera timeframes.
2. **Se upp för överanpassning:** om du justerar parametrar tills en period
   ser fantastisk ut har du lärt dig periodens brus, inte marknaden.
   Ändra en parameter i taget och kräv att förbättringen håller på *andra*
   perioder än den du justerade på (testa t.ex. `--candles 2200` mot
   `--candles 4400` — olika fönster).
3. **Paper trading är riktiga testet:** backtest är facit i efterhand;
   paper-läget är framtidsdata. Kör vinnaren i paper i minst några veckor:
   `python main.py paper`.
4. **Live börjar på testnet:** `testnet: true` mot
   [testnet.bybit.com](https://testnet.bybit.com) med gratis låtsassaldo,
   sedan små belopp på riktigt.

## Riskregler som inte är förhandlingsbara

- Riska aldrig mer än 1–2 % av kapitalet per trade (`risk_per_trade_pct`).
- Hävstång 2–3x max i praktiken, även om boten tillåter upp till 10.
- Dagligt förluststopp (`max_daily_loss_pct`) finns för att en dålig dag
  inte ska bli en katastrofal — höj den inte för att "få vara med".
- Handla bara med pengar du har råd att förlora helt. Perpetuals med
  hävstång är det snabbaste sättet som finns att förlora dem.
- API-nycklar: aktivera bara handel, **aldrig uttag**, och lås dem till
  din IP om Bybit erbjuder det.
