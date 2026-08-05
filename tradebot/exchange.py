"""Exchange-anslutning via ccxt. Marknadsdata är alltid live; ordrar
skickas bara till exchangen i live-läge."""

import logging

import ccxt
import pandas as pd

from .config import ExchangeConfig

log = logging.getLogger("tradebot.exchange")


class Exchange:
    def __init__(self, cfg: ExchangeConfig, live: bool = False):
        self.live = live
        klass = getattr(ccxt, cfg.id)
        params = {"enableRateLimit": True}
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

    # -- marknadsdata -----------------------------------------------------
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 300) -> pd.DataFrame:
        raw = self.client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df

    def fetch_price(self, symbol: str) -> float:
        return float(self.client.fetch_ticker(symbol)["last"])

    # -- ordrar -----------------------------------------------------------
    def market_buy(self, symbol: str, amount: float) -> dict:
        if not self.live:
            log.info("[PAPER] market buy %s %.8f", symbol, amount)
            return {"status": "paper"}
        order = self.client.create_market_buy_order(symbol, amount)
        log.info("[LIVE] market buy %s %.8f -> id %s", symbol, amount, order.get("id"))
        return order

    def market_sell(self, symbol: str, amount: float) -> dict:
        if not self.live:
            log.info("[PAPER] market sell %s %.8f", symbol, amount)
            return {"status": "paper"}
        order = self.client.create_market_sell_order(symbol, amount)
        log.info("[LIVE] market sell %s %.8f -> id %s", symbol, amount, order.get("id"))
        return order

    def normalize_amount(self, symbol: str, amount: float) -> float:
        """Avrundar mängden till exchangens precision (live-läge)."""
        if not self.live:
            return amount
        self.client.load_markets()
        return float(self.client.amount_to_precision(symbol, amount))
