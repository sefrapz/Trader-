"""Laddar konfiguration från config.yaml och hemligheter från .env."""

import os
from dataclasses import dataclass, field

import yaml
from dotenv import load_dotenv


@dataclass
class ExchangeConfig:
    id: str = "binance"
    testnet: bool = True
    api_key: str = ""
    api_secret: str = ""


@dataclass
class MarketConfig:
    symbols: list = field(default_factory=lambda: ["BTC/USDT"])
    timeframe: str = "1h"
    candle_limit: int = 300


@dataclass
class StrategyConfig:
    ema_fast: int = 12
    ema_slow: int = 26
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    atr_period: int = 14
    atr_stop_mult: float = 2.0
    atr_take_mult: float = 3.0
    donchian_entry: int = 20
    donchian_exit: int = 10
    meanrev_trend_ema: int = 200
    meanrev_exit_rsi: float = 50.0


@dataclass
class TradingConfig:
    mode: str = "spot"          # "spot" eller "futures"
    strategy: str = "ema_cross"
    leverage: float = 1.0       # endast futures; 1 = ingen hävstång
    allow_shorts: bool = True   # endast futures


@dataclass
class RiskConfig:
    start_equity: float = 10000.0
    risk_per_trade_pct: float = 1.0
    max_positions: int = 2
    max_daily_loss_pct: float = 5.0
    min_order_quote: float = 10.0


@dataclass
class BotConfig:
    poll_seconds: int = 60
    state_file: str = "state/portfolio.json"
    log_file: str = "tradebot.log"


@dataclass
class Config:
    exchange: ExchangeConfig
    market: MarketConfig
    trading: TradingConfig
    strategy: StrategyConfig
    risk: RiskConfig
    bot: BotConfig


def _build(cls, data: dict):
    fields = {f for f in cls.__dataclass_fields__}
    return cls(**{k: v for k, v in (data or {}).items() if k in fields})


def load_config(path: str = "config.yaml") -> Config:
    load_dotenv()
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    exchange = _build(ExchangeConfig, raw.get("exchange"))
    exchange.api_key = os.getenv("EXCHANGE_API_KEY", "")
    exchange.api_secret = os.getenv("EXCHANGE_API_SECRET", "")

    trading = _build(TradingConfig, raw.get("trading"))
    if trading.mode not in ("spot", "futures"):
        raise ValueError(f"trading.mode måste vara 'spot' eller 'futures', inte '{trading.mode}'")
    if trading.mode == "spot":
        trading.leverage = 1.0
        trading.allow_shorts = False
    if trading.leverage < 1:
        raise ValueError("trading.leverage måste vara minst 1")
    if trading.leverage > 10:
        raise ValueError(
            "trading.leverage över 10 tillåts inte av boten — likvidationsrisken "
            "blir orimlig. Se docs/STRATEGIER.md."
        )

    return Config(
        exchange=exchange,
        market=_build(MarketConfig, raw.get("market")),
        trading=trading,
        strategy=_build(StrategyConfig, raw.get("strategy")),
        risk=_build(RiskConfig, raw.get("risk")),
        bot=_build(BotConfig, raw.get("bot")),
    )
