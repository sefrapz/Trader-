# Trader — live-tradebot för krypto

En tradingbot i Python som handlar krypto via [ccxt](https://github.com/ccxt/ccxt)
(Bybit som standard, men vilket ccxt-stött exchange som helst fungerar).

Tre strategier ingår — trendföljning (`ema_cross`), breakout (`donchian`)
och mean reversion (`rsi_meanrev`) — och boten kan handla **spot** eller
**futures (USDT-perpetuals) med hävstång och shorts**. Riskhanteringen är
ATR-baserad med stop loss, take profit, positionsstorlek efter risk per
trade, dagligt förluststopp och en likvidationsmodell för hävstång.

**Läs [docs/STRATEGIER.md](docs/STRATEGIER.md)** — den förklarar strategierna,
hävstångens risker och hur du testar seriöst.

> ⚠️ **Viktigt:** Ingen bot kan garantera vinst. Trading — särskilt krypto — kan
> leda till att du förlorar hela ditt kapital. Historisk avkastning i backtest
> säger inget säkert om framtiden. Kör backtest och paper trading länge innan du
> ens överväger live-läge, och handla aldrig med pengar du inte har råd att förlora.

## Kom igång

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 1. Backtest (ingen API-nyckel behövs)

Testar strategin på historisk data direkt från exchangen:

```bash
python main.py backtest --candles 1000
```

Jämför alla tre strategierna på ~2 år av 4h-data:

```bash
python main.py backtest --candles 4400 --strategy all
```

### 2. Paper trading (ingen API-nyckel behövs)

Handlar med låtsaspengar mot **riktiga livepriser** — det bästa sättet att se
hur boten beter sig innan riktiga pengar är inblandade:

```bash
python main.py paper
```

Portföljen sparas i `state/portfolio.json` och överlever omstarter.

### 3. Analysera dina trades

Varje avslutad trade journalförs med marknadskontext (ADX, ATR, RSI m.m.
vid entry) — backtest skriver till `state/journal_backtest.jsonl` och
paper/live till `state/journal.jsonl`. I paper/live uppdateras dessutom
`state/analysis.txt` automatiskt efter varje stängd trade.

```bash
python main.py analyze                    # analysera allt
python main.py analyze --source backtest  # bara senaste backtesten
python main.py analyze --source paper     # bara paper/live-trades
```

Rapporten visar var pengarna tjänas och förloras: per strategi, sida
(long/short), exit-orsak, trendstyrka, volatilitet och veckodag. Grupper
med färre än 10 trades markeras — dra inga slutsatser av dem, och
behandla mönster som hypoteser att A/B-testa i backtest, inte som regler.

### 4. Live trading

1. Kopiera `.env.example` till `.env` och fyll i dina API-nycklar
   (skapa nycklar **utan uttagsrättigheter** på exchangen).
2. Låt `exchange.testnet: true` stå kvar i `config.yaml` och testa mot
   exchangens testnet först.
3. När du är redo på riktigt: sätt `testnet: false` och kör

```bash
python main.py live --i-understand-the-risk
```

## Konfiguration

Allt ställs in i [`config.yaml`](config.yaml): exchange, symboler, timeframe,
handelsläge (`trading.mode: spot|futures`, `leverage`, `allow_shorts`,
`strategy`), strategiparametrar och riskregler. API-nycklar läses enbart
från `.env`.

Futures med 2x hävstång och shorts:

```yaml
trading:
  mode: futures
  strategy: ema_cross
  leverage: 2
  allow_shorts: true
```

Hävstång över 10 vägrar boten starta med — se
[docs/STRATEGIER.md](docs/STRATEGIER.md) för varför.

## Montrose-koppling

Vill du att Claude ska kunna läsa din Montrose-portfölj vid sidan av boten,
se [docs/MONTROSE.md](docs/MONTROSE.md). `.mcp.json` i repo-roten är förberedd
och läser kopplingslänken från `MONTROSE_MCP_URL` i `.env`.

## Arkitektur

| Fil | Ansvar |
|---|---|
| `tradebot/strategy.py` | strategibibliotek: ema_cross, donchian, rsi_meanrev |
| `tradebot/risk.py` | positionsstorlek, förluststopp, stop/take/likvidation |
| `tradebot/portfolio.py` | positioner (long/short, marginal), PnL, persistens |
| `tradebot/exchange.py` | ccxt-anslutning, spot/futures, data och ordrar |
| `tradebot/bot.py` | huvudloopen (paper + live) |
| `tradebot/backtest.py` | backtest-motor med hävstång, shorts, avgifter |
| `main.py` | CLI: `backtest` / `paper` / `live` |

## Tester

```bash
pip install pytest
pytest
```

Testerna körs helt offline med syntetisk data.
