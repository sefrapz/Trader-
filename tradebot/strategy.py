"""EMA-korsning med RSI-filter och ATR-baserade stop/take-nivåer.

Köpsignal: snabb EMA korsar upp genom långsam EMA och RSI är inte överköpt.
Säljsignal: snabb EMA korsar ner genom långsam EMA.
Exits sköts även av stop loss / take profit i risklagret.
"""

from dataclasses import dataclass

import pandas as pd

from .config import StrategyConfig
from .indicators import atr, ema, rsi


@dataclass
class Signal:
    action: str          # "buy", "sell" eller "hold"
    price: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    reason: str = ""


class EmaRsiStrategy:
    def __init__(self, cfg: StrategyConfig):
        self.cfg = cfg

    def min_candles(self) -> int:
        return max(self.cfg.ema_slow, self.cfg.rsi_period, self.cfg.atr_period) + 2

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["ema_fast"] = ema(out["close"], self.cfg.ema_fast)
        out["ema_slow"] = ema(out["close"], self.cfg.ema_slow)
        out["rsi"] = rsi(out["close"], self.cfg.rsi_period)
        out["atr"] = atr(out, self.cfg.atr_period)
        return out

    def evaluate(self, df: pd.DataFrame) -> Signal:
        """Utvärderar senast stängda candle. df ska vara rå OHLCV."""
        if len(df) < self.min_candles():
            return Signal("hold", float(df["close"].iloc[-1]), reason="för lite data")

        ind = self.add_indicators(df)
        cur, prev = ind.iloc[-1], ind.iloc[-2]
        price = float(cur["close"])

        crossed_up = prev["ema_fast"] <= prev["ema_slow"] and cur["ema_fast"] > cur["ema_slow"]
        crossed_down = prev["ema_fast"] >= prev["ema_slow"] and cur["ema_fast"] < cur["ema_slow"]

        if crossed_up and cur["rsi"] < self.cfg.rsi_overbought:
            stop = price - self.cfg.atr_stop_mult * float(cur["atr"])
            take = price + self.cfg.atr_take_mult * float(cur["atr"])
            return Signal(
                "buy", price, stop_loss=stop, take_profit=take,
                reason=f"EMA-korsning upp, RSI {cur['rsi']:.1f}",
            )

        if crossed_down:
            return Signal("sell", price, reason=f"EMA-korsning ner, RSI {cur['rsi']:.1f}")

        return Signal("hold", price)
