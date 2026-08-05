# Trader — live-tradebot för krypto

En tradingbot i Python som handlar krypto via [ccxt](https://github.com/ccxt/ccxt)
(Binance som standard, men vilket ccxt-stött exchange som helst fungerar).

Strategin är en klassisk trendföljare: **EMA-korsning (12/26) med RSI-filter**,
och riskhanteringen är ATR-baserad med stop loss, take profit, positionsstorlek
efter risk per trade samt ett dagligt förluststopp.

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

### 2. Paper trading (ingen API-nyckel behövs)

Handlar med låtsaspengar mot **riktiga livepriser** — det bästa sättet att se
hur boten beter sig innan riktiga pengar är inblandade:

```bash
python main.py paper
```

Portföljen sparas i `state/portfolio.json` och överlever omstarter.

### 3. Live trading

1. Kopiera `.env.example` till `.env` och fyll i dina API-nycklar
   (skapa nycklar **utan uttagsrättigheter** på exchangen).
2. Låt `exchange.testnet: true` stå kvar i `config.yaml` och testa mot
   exchangens testnet först.
3. När du är redo på riktigt: sätt `testnet: false` och kör

```bash
python main.py live --i-understand-the-risk
```

## Konfiguration

Allt ställs in i [`config.yaml`](config.yaml): symboler, timeframe,
strategiparametrar (EMA/RSI/ATR) och riskregler (risk per trade, max antal
positioner, dagligt förluststopp). API-nycklar läses enbart från `.env`.

## Arkitektur

| Fil | Ansvar |
|---|---|
| `tradebot/strategy.py` | EMA/RSI-signaler med ATR-nivåer |
| `tradebot/risk.py` | positionsstorlek, dagligt förluststopp, exit-regler |
| `tradebot/portfolio.py` | positioner, PnL och persistens |
| `tradebot/exchange.py` | ccxt-anslutning, marknadsdata och ordrar |
| `tradebot/bot.py` | huvudloopen (paper + live) |
| `tradebot/backtest.py` | backtest på historisk data |
| `main.py` | CLI: `backtest` / `paper` / `live` |

## Tester

```bash
pip install pytest
pytest
```

Testerna körs helt offline med syntetisk data.
