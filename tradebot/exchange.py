"""Exchange-anslutning via ccxt. Marknadsdata är alltid live; ordrar
skickas bara till exchangen i live-läge.

I futures-läge handlas USDT-perpetuals (t.ex. BTC/USDT:USDT på Bybit);
spot-symboler i konfigen mappas automatiskt."""

import logging

import ccxt
import pandas as pd

from .config import ExchangeConfig

log = logging.getLogger("tradebot.exchange")

MAX_CANDLES_PER_CALL = 1000  # de flesta exchanges (inkl. Bybit) taklar här


class Exchange:
    def __init__(self, cfg: ExchangeConfig, live: bool = False, futures: bool = False):
        self.live = live
        self.futures = futures
        klass = getattr(ccxt, cfg.id)
        params = {
            "enableRateLimit": True,
            # boten väljer uttryckligen marknadstyp — aldrig exchangens default
            "options": {"defaultType": "swap" if futures else "spot"},
        }
        if live:
            if not cfg.api_key or not cfg.api_secret:
                raise RuntimeError(
                    "Live-läge kräver EXCHANGE_API_KEY och EXCHANGE_API_SECRET i .env"
                )
            params.update({"apiKey": cfg.api_key, "secret": cfg.api_secret})
        self.client = klass(params)
        if live and cfg.testnet:
            self.client.set_sandbox_mode(True)
            log.info("Sandbox/testnet-läge aktivt på %s", cfg.id)

    def map_symbol(self, symbol: str) -> str:
        """BTC/USDT -> BTC/USDT:USDT i futures-läge (linjär USDT-perpetual)."""
        if self.futures and ":" not in symbol:
            quote = symbol.split("/")[1]
            return f"{symbol}:{quote}"
        return symbol

    # -- marknadsdata -----------------------------------------------------
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 300) -> pd.DataFrame:
        """Hämtar candles, paginerat om limit överstiger exchangens tak."""
        sym = self.map_symbol(symbol)
        if limit <= MAX_CANDLES_PER_CALL:
            raw = self.client.fetch_ohlcv(sym, timeframe=timeframe, limit=limit)
        else:
            tf_ms = self.client.parse_timeframe(timeframe) * 1000
            since = self.client.milliseconds() - limit * tf_ms
            raw = []
            while len(raw) < limit:
                batch = self.client.fetch_ohlcv(
                    sym, timeframe=timeframe, since=since, limit=MAX_CANDLES_PER_CALL
                )
                if not batch:
                    break
                # undvik dubblett av första candlen i nästa batch
                if raw and batch[0][0] <= raw[-1][0]:
                    batch = [c for c in batch if c[0] > raw[-1][0]]
                    if not batch:
                        break
                raw.extend(batch)
                since = raw[-1][0] + tf_ms
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df

    def fetch_price(self, symbol: str) -> float:
        return float(self.client.fetch_ticker(self.map_symbol(symbol))["last"])

    # -- hävstång ---------------------------------------------------------
    def set_leverage(self, symbol: str, leverage: float) -> None:
        if not (self.live and self.futures) or leverage <= 1:
            return
        try:
            self.client.set_leverage(int(leverage), self.map_symbol(symbol))
            log.info("Hävstång %sx satt för %s", int(leverage), symbol)
        except Exception as exc:  # Bybit svarar med fel om värdet redan är satt
            log.info("set_leverage %s: %s (ofta ofarligt: redan satt)", symbol, exc)

    # -- ordrar -----------------------------------------------------------
    def market_buy(self, symbol: str, amount: float, reduce_only: bool = False) -> dict:
        if not self.live:
            log.info("[PAPER] market buy %s %.8f", symbol, amount)
            return {"status": "paper"}
        sym = self.map_symbol(symbol)
        extra = {"reduceOnly": True} if (reduce_only and self.futures) else {}
        opts = self.client.options
        requires_price = opts.get("createMarketBuyOrderRequiresPrice")
        if requires_price is None:
            requires_price = (opts.get("createOrder") or {}).get(
                "createMarketBuyOrderRequiresPrice"
            )
        if requires_price and not self.futures:
            # vissa exchanges (t.ex. Bybit classic-konton) tar emot spot-marknadsköp
            # som kostnad i quote-valuta i stället för mängd basvaluta
            cost = amount * self.fetch_price(symbol)
            order = self.client.create_market_buy_order_with_cost(sym, cost)
        else:
            order = self.client.create_market_buy_order(sym, amount, params=extra)
        log.info("[LIVE] market buy %s %.8f -> id %s", symbol, amount, order.get("id"))
        return order

    def market_sell(self, symbol: str, amount: float, reduce_only: bool = False) -> dict:
        if not self.live:
            log.info("[PAPER] market sell %s %.8f", symbol, amount)
            return {"status": "paper"}
        sym = self.map_symbol(symbol)
        extra = {"reduceOnly": True} if (reduce_only and self.futures) else {}
        order = self.client.create_market_sell_order(sym, amount, params=extra)
        log.info("[LIVE] market sell %s %.8f -> id %s", symbol, amount, order.get("id"))
        return order

    def normalize_amount(self, symbol: str, amount: float) -> float:
        """Avrundar mängden till exchangens precision (live-läge)."""
        if not self.live:
            return amount
        self.client.load_markets()
        return float(self.client.amount_to_precision(self.map_symbol(symbol), amount))
