# Beslutslogg

Varje regeländring i systemet dokumenteras här med sitt bevisunderlag.
Metoden: journalanalys/idé → hypotes → A/B-backtest på minst två
tidsfönster → beslut. Mönster utan mekanism eller utan stabilitet över
fönster blir inte regler.

## 2026-08-05 — Volatilitetsfilter PÅ (`max_entry_atr_pct: 4`)

- **Hypotes från:** journalanalys, 239 trades över 4 år: entries vid
  ATR >4 % av pris gav PF 0.64 (−2488), mellanvol 2–4 % gav PF 1.25 (+1454).
- **Mekanism:** hög ATR → breda stoppar → sämre risk/reward; breakouts i
  panikvolatilitet är oftare falska.
- **A/B, donchian futures 2x 1d:**
  - 4-årsfönstret: BTC +5,22 % → +11,71 % (dd oförändrad), ETH −6,14 % → +0,56 %
  - 2-årsfönstret (validering): BTC +1,53 % → +5,63 %, ETH −2,82 % → −1,57 %
- **Beslut:** PÅ. Förbättring i samtliga celler, båda fönstren.
- **Bieffekt:** ETH handlas nästan inte alls med filtret (dess volatilitet
  ligger oftast över tröskeln) — självreglerande, ETH behålls som symbol.

## 2026-08-05 — ADX-regimfilter AV (`adx_min: 0`)

- **Hypotes:** trendstrategier bör bara handla när ADX ≥ 20.
- **A/B, donchian 1d spot, 2-årsfönstret:** BTC +0,12 % → −3,14 %,
  ETH −5,43 % → −5,97 %. Sämre på båda.
- **Beslut:** AV. ADX släpar — donchian-entries sker i trendens födelse
  när ADX ännu är lågt, så filtret klippte bort tidiga vinnare.
- **Efternot:** journalanalysen visade senare att ADX-sambandet är
  icke-linjärt (20–30 lönsamt, >30 förlust) — ett bandfilter är en möjlig
  framtida hypotes, ännu otestad.

## 2026-08-05 — Standardstrategi `donchian`, timeframe `1d`, futures 2x

- **Underlag:** strategijämförelser på 1h/4h/1d över 1–4 år.
  1h: −13 till −36 % (avgifter/brus). 4h: −1 till −14 %. 1d: bäst.
  donchian enda strategin med plus över 4 år; ema_cross minus i varje
  konfiguration; rsi_meanrev för få trades för bedömning.
  Futures med shorts förbättrade BTC (+1,79 % → +4,12 % före vol-filter)
  med lägre drawdown.
- **Beslut:** donchian + 1d + futures 2x + shorts är standarduppsättningen.
