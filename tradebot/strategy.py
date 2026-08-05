"""Strategibibliotek.

Alla strategier producerar en Signal per candle:
  "long"  — öppna lång position (stop/take medföljer)
  "short" — öppna kort position (kräver futures-läge)
  "close" — stäng nuvarande position
  "hold"  — gör ingenting

Strategin får veta nuvarande positionssida (side) så att den kan skilja
på "stäng min long" och "öppna en short".

Tillgängliga strategier:
  ema_cross   — trendföljning: EMA 12/26-korsning med RSI-filter
  donchian    — breakout: Donchian-kanal (turtle-stil)
  rsi_meanrev — mean reversion: RSI-extremer med EMA200-trendfilter
"""

from dataclasses import dataclass

import pandas as pd

from .config import StrategyConfig
from .indicators import adx, atr, ema, rsi


@dataclass
class Signal:
    action: str          # "long", "short", "close" eller "hold"
    price: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    reason: str = ""


class BaseStrategy:
    name = "base"

    def __init__(self, cfg: StrategyConfig):
        self.cfg = cfg

    def min_candles(self) -> int:
        raise NotImplementedError

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def signal_row(self, ind: pd.DataFrame, i: int, side: str = "") -> Signal:
        """Signal för rad i. ind är resultatet av add_indicators."""
        raise NotImplementedError

    def evaluate(self, df: pd.DataFrame, side: str = "") -> Signal:
        """Utvärderar senast stängda candle på rå OHLCV-data."""
        if len(df) < self.min_candles():
            return Signal("hold", float(df["close"].iloc[-1]), reason="för lite data")
        ind = self.add_indicators(df)
        return self.signal_row(ind, len(ind) - 1, side)

    def _levels(self, price: float, atr_val: float, side: str) -> tuple:
        stop_d = self.cfg.atr_stop_mult * atr_val
        take_d = self.cfg.atr_take_mult * atr_val
        if side == "long":
            return price - stop_d, price + take_d
        return price + stop_d, price - take_d

    def _trending(self, row) -> bool:
        """Regimfilter: entries tillåts bara när ADX visar mätbar trendstyrka."""
        if self.cfg.adx_min <= 0:
            return True
        return float(row["adx"]) >= self.cfg.adx_min


class EmaCrossStrategy(BaseStrategy):
    """Trendföljning: EMA-korsning med RSI-filter. Long vid korsning upp,
    short vid korsning ner (i futures-läge)."""

    name = "ema_cross"

    def min_candles(self) -> int:
        return max(self.cfg.ema_slow, self.cfg.rsi_period, self.cfg.atr_period,
                   2 * self.cfg.adx_period) + 2

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["ema_fast"] = ema(out["close"], self.cfg.ema_fast)
        out["ema_slow"] = ema(out["close"], self.cfg.ema_slow)
        out["rsi"] = rsi(out["close"], self.cfg.rsi_period)
        out["atr"] = atr(out, self.cfg.atr_period)
        out["adx"] = adx(out, self.cfg.adx_period)
        return out

    def signal_row(self, ind: pd.DataFrame, i: int, side: str = "") -> Signal:
        cur, prev = ind.iloc[i], ind.iloc[i - 1]
        price = float(cur["close"])

        crossed_up = prev["ema_fast"] <= prev["ema_slow"] and cur["ema_fast"] > cur["ema_slow"]
        crossed_down = prev["ema_fast"] >= prev["ema_slow"] and cur["ema_fast"] < cur["ema_slow"]

        if crossed_up:
            if not self._trending(cur):
                # korsning i trendlös marknad: lämna ev. short men öppna inget nytt
                return Signal("close", price,
                              reason=f"korsning upp men svag trend (ADX {cur['adx']:.0f})")
            if cur["rsi"] < self.cfg.rsi_overbought:
                stop, take = self._levels(price, float(cur["atr"]), "long")
                return Signal("long", price, stop, take,
                              f"EMA-korsning upp, RSI {cur['rsi']:.1f}, ADX {cur['adx']:.0f}")
            return Signal("close", price, reason="EMA-korsning upp men överköpt RSI")

        if crossed_down:
            if not self._trending(cur):
                return Signal("close", price,
                              reason=f"korsning ner men svag trend (ADX {cur['adx']:.0f})")
            if cur["rsi"] > self.cfg.rsi_oversold:
                stop, take = self._levels(price, float(cur["atr"]), "short")
                return Signal("short", price, stop, take,
                              f"EMA-korsning ner, RSI {cur['rsi']:.1f}, ADX {cur['adx']:.0f}")
            return Signal("close", price, reason="EMA-korsning ner men översåld RSI")

        return Signal("hold", price)


class DonchianStrategy(BaseStrategy):
    """Breakout: long när priset stänger över högsta högsta de senaste N
    candlarna, short under lägsta lägsta. Exit på motsatt kortare kanal
    (klassisk turtle-uppställning)."""

    name = "donchian"

    def min_candles(self) -> int:
        return max(self.cfg.donchian_entry, self.cfg.donchian_exit,
                   self.cfg.atr_period, 2 * self.cfg.adx_period) + 2

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        n_in, n_out = self.cfg.donchian_entry, self.cfg.donchian_exit
        # shift(1): dagens candle får inte ingå i sin egen kanal
        out["dc_high"] = out["high"].rolling(n_in).max().shift(1)
        out["dc_low"] = out["low"].rolling(n_in).min().shift(1)
        out["dx_high"] = out["high"].rolling(n_out).max().shift(1)
        out["dx_low"] = out["low"].rolling(n_out).min().shift(1)
        out["atr"] = atr(out, self.cfg.atr_period)
        out["adx"] = adx(out, self.cfg.adx_period)
        return out

    def signal_row(self, ind: pd.DataFrame, i: int, side: str = "") -> Signal:
        cur = ind.iloc[i]
        price = float(cur["close"])

        if side == "long" and price < float(cur["dx_low"]):
            return Signal("close", price, reason="stängde under exitkanalen")
        if side == "short" and price > float(cur["dx_high"]):
            return Signal("close", price, reason="stängde över exitkanalen")

        if price > float(cur["dc_high"]) and self._trending(cur):
            stop, take = self._levels(price, float(cur["atr"]), "long")
            return Signal("long", price, stop, take,
                          f"breakout över {self.cfg.donchian_entry}-kanalen, "
                          f"ADX {cur['adx']:.0f}")
        if price < float(cur["dc_low"]) and self._trending(cur):
            stop, take = self._levels(price, float(cur["atr"]), "short")
            return Signal("short", price, stop, take,
                          f"breakout under {self.cfg.donchian_entry}-kanalen, "
                          f"ADX {cur['adx']:.0f}")

        return Signal("hold", price)


class RsiMeanRevStrategy(BaseStrategy):
    """Mean reversion: köp översålda dippar i upptrend (RSI lågt, pris över
    EMA200), shorta överköpta toppar i nedtrend. Exit när RSI normaliserats."""

    name = "rsi_meanrev"

    def min_candles(self) -> int:
        return max(self.cfg.meanrev_trend_ema, self.cfg.rsi_period, self.cfg.atr_period) + 2

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["trend_ema"] = ema(out["close"], self.cfg.meanrev_trend_ema)
        out["rsi"] = rsi(out["close"], self.cfg.rsi_period)
        out["atr"] = atr(out, self.cfg.atr_period)
        return out

    def signal_row(self, ind: pd.DataFrame, i: int, side: str = "") -> Signal:
        cur = ind.iloc[i]
        price = float(cur["close"])
        rsi_val = float(cur["rsi"])
        exit_rsi = self.cfg.meanrev_exit_rsi

        if side == "long" and rsi_val >= exit_rsi:
            return Signal("close", price, reason=f"RSI normaliserad ({rsi_val:.1f})")
        if side == "short" and rsi_val <= 100 - exit_rsi:
            return Signal("close", price, reason=f"RSI normaliserad ({rsi_val:.1f})")

        if rsi_val < self.cfg.rsi_oversold and price > float(cur["trend_ema"]):
            stop, take = self._levels(price, float(cur["atr"]), "long")
            return Signal("long", price, stop, take,
                          f"översåld dipp i upptrend, RSI {rsi_val:.1f}")
        if rsi_val > self.cfg.rsi_overbought and price < float(cur["trend_ema"]):
            stop, take = self._levels(price, float(cur["atr"]), "short")
            return Signal("short", price, stop, take,
                          f"överköpt topp i nedtrend, RSI {rsi_val:.1f}")

        return Signal("hold", price)


STRATEGIES = {
    EmaCrossStrategy.name: EmaCrossStrategy,
    DonchianStrategy.name: DonchianStrategy,
    RsiMeanRevStrategy.name: RsiMeanRevStrategy,
}


def get_strategy(name: str, cfg: StrategyConfig) -> BaseStrategy:
    if name not in STRATEGIES:
        raise ValueError(f"Okänd strategi '{name}'. Välj bland: {', '.join(STRATEGIES)}")
    return STRATEGIES[name](cfg)
