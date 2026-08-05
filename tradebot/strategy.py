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

    _OHLCV = {"timestamp", "open", "high", "low", "close", "volume"}

    def entry_context(self, df: pd.DataFrame) -> dict:
        """Indikatorvärden på senaste candlen — sparas i journalen vid entry."""
        ind = self.add_indicators(df)
        row = ind.iloc[-1]
        out = {}
        for col in ind.columns:
            if col in self._OHLCV:
                continue
            try:
                val = float(row[col])
            except (TypeError, ValueError):
                continue
            if pd.notna(val):
                out[col] = round(val, 6)
        return out

    def _trending(self, row) -> bool:
        """Regimfilter: entries tillåts bara när ADX visar mätbar trendstyrka."""
        if self.cfg.adx_min <= 0:
            return True
        return float(row["adx"]) >= self.cfg.adx_min

    def _vol_ok(self, row) -> bool:
        """Volatilitetsfilter: hoppa över entries när ATR% av pris är för hög."""
        if self.cfg.max_entry_atr_pct <= 0:
            return True
        atr_pct = float(row["atr"]) / float(row["close"]) * 100.0
        return atr_pct <= self.cfg.max_entry_atr_pct


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
            if not self._vol_ok(cur):
                return Signal("close", price, reason="korsning upp men för hög volatilitet")
            if cur["rsi"] < self.cfg.rsi_overbought:
                stop, take = self._levels(price, float(cur["atr"]), "long")
                return Signal("long", price, stop, take,
                              f"EMA-korsning upp, RSI {cur['rsi']:.1f}, ADX {cur['adx']:.0f}")
            return Signal("close", price, reason="EMA-korsning upp men överköpt RSI")

        if crossed_down:
            if not self._trending(cur):
                return Signal("close", price,
                              reason=f"korsning ner men svag trend (ADX {cur['adx']:.0f})")
            if not self._vol_ok(cur):
                return Signal("close", price, reason="korsning ner men för hög volatilitet")
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

        if price > float(cur["dc_high"]) and self._trending(cur) and self._vol_ok(cur):
            stop, take = self._levels(price, float(cur["atr"]), "long")
            return Signal("long", price, stop, take,
                          f"breakout över {self.cfg.donchian_entry}-kanalen, "
                          f"ADX {cur['adx']:.0f}")
        if price < float(cur["dc_low"]) and self._trending(cur) and self._vol_ok(cur):
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

        if (rsi_val < self.cfg.rsi_oversold and price > float(cur["trend_ema"])
                and self._vol_ok(cur)):
            stop, take = self._levels(price, float(cur["atr"]), "long")
            return Signal("long", price, stop, take,
                          f"översåld dipp i upptrend, RSI {rsi_val:.1f}")
        if (rsi_val > self.cfg.rsi_overbought and price < float(cur["trend_ema"])
                and self._vol_ok(cur)):
            stop, take = self._levels(price, float(cur["atr"]), "short")
            return Signal("short", price, stop, take,
                          f"överköpt topp i nedtrend, RSI {rsi_val:.1f}")

        return Signal("hold", price)


class IntradayMomentumStrategy(BaseStrategy):
    """Daytrading: volymbekräftat breakout + återtest, i riktning med
    dagens VWAP och 15-minutersstrukturen.

    Long kräver att ALLT stämmer:
      1. pris tydligt över dagens VWAP (minst vwap_min_atr_dist * ATR)
      2. 15m-struktur uppåt (pris över stigande EMA)
      3. stängning över senaste breakout_lookback-candlarnas högsta,
         med volym >= vol_mult * normalvolymen
      4. återtest av nivån som håller (ingen stängning tydligt under)
      5. entry när priset vänder upp igen (stängning över föregående high)
    Stop under återtestets botten (minst ~1 ATR), take profit vid day_rr_take R.
    Short är spegelvänt. Designad för 5m-candles.
    """

    name = "intraday_momentum"

    def min_candles(self) -> int:
        return max(300, self.cfg.breakout_lookback + self.cfg.vol_sma
                   + self.cfg.retest_window + 5)

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["atr"] = atr(out, self.cfg.atr_period)

        # dagsförankrad VWAP (nollställs vid UTC-midnatt)
        day = out["timestamp"].dt.floor("D")
        tp = (out["high"] + out["low"] + out["close"]) / 3.0
        pv = (tp * out["volume"]).groupby(day).cumsum()
        vv = out["volume"].groupby(day).cumsum().replace(0.0, 1e-12)
        out["vwap"] = pv / vv

        # 15m-riktningsstruktur via resampling
        idx = out.set_index("timestamp")
        m15 = idx["close"].resample("15min").last().dropna()
        e15 = ema(m15, self.cfg.structure_ema)
        rising = e15 > e15.shift(self.cfg.structure_slope_bars)
        falling = e15 < e15.shift(self.cfg.structure_slope_bars)
        up15 = (m15 > e15) & rising
        down15 = (m15 < e15) & falling
        out["structure_up"] = (up15.reindex(idx.index, method="ffill")
                               .fillna(False).astype(bool).to_numpy())
        out["structure_down"] = (down15.reindex(idx.index, method="ffill")
                                 .fillna(False).astype(bool).to_numpy())

        # breakout-nivåer och volymspik
        bl = self.cfg.breakout_lookback
        out["level_high"] = out["high"].rolling(bl).max().shift(1)
        out["level_low"] = out["low"].rolling(bl).min().shift(1)
        norm_vol = out["volume"].rolling(self.cfg.vol_sma).mean().shift(1)
        out["vol_spike"] = out["volume"] >= self.cfg.vol_mult * norm_vol

        dist = self.cfg.vwap_min_atr_dist * out["atr"]
        out["bo_up"] = ((out["close"] > out["level_high"]) & out["vol_spike"]
                        & out["structure_up"] & (out["close"] > out["vwap"] + dist))
        out["bo_down"] = ((out["close"] < out["level_low"]) & out["vol_spike"]
                          & out["structure_down"] & (out["close"] < out["vwap"] - dist))
        return out

    def signal_row(self, ind: pd.DataFrame, i: int, side: str = "") -> Signal:
        cur = ind.iloc[i]
        price = float(cur["close"])
        atr_val = float(cur["atr"])
        dist = self.cfg.vwap_min_atr_dist * atr_val

        # exits: struktur/VWAP tappad (stop/take sköts av risklagret)
        if side == "long" and price < float(cur["vwap"]) - dist:
            return Signal("close", price, reason="tappade VWAP")
        if side == "short" and price > float(cur["vwap"]) + dist:
            return Signal("close", price, reason="återtog VWAP")
        if side:
            return Signal("hold", price)

        # leta breakout i närtid, kräv återtest som hållit + återupptagning nu
        earliest = max(1, i - self.cfg.retest_window - 1)
        prev_high = float(ind["high"].iloc[i - 1])
        prev_low = float(ind["low"].iloc[i - 1])
        for j in range(i - 2, earliest - 1, -1):
            row_j = ind.iloc[j]
            between = ind.iloc[j + 1:i]  # candlarna mellan breakout och nu
            if between.empty:
                continue

            if bool(row_j["bo_up"]):
                level = float(row_j["level_high"])
                tol = level * self.cfg.retest_tol_pct / 100.0
                if (between["close"] < level - tol).any():
                    continue  # nivån gav vika — setup ogiltig
                if not (between["low"] <= level + tol).any():
                    continue  # inget återtest ännu
                if price > prev_high and price > level:
                    stop = float(between["low"].min())
                    if price - stop < 0.3 * atr_val:
                        stop = price - atr_val
                    take = price + self.cfg.day_rr_take * (price - stop)
                    return Signal("long", price, stop, take,
                                  reason=f"breakout+återtest över {level:.2f}")

            if bool(row_j["bo_down"]):
                level = float(row_j["level_low"])
                tol = level * self.cfg.retest_tol_pct / 100.0
                if (between["close"] > level + tol).any():
                    continue
                if not (between["high"] >= level - tol).any():
                    continue
                if price < prev_low and price < level:
                    stop = float(between["high"].max())
                    if stop - price < 0.3 * atr_val:
                        stop = price + atr_val
                    take = price - self.cfg.day_rr_take * (stop - price)
                    return Signal("short", price, stop, take,
                                  reason=f"breakout+återtest under {level:.2f}")

        return Signal("hold", price)


STRATEGIES = {
    EmaCrossStrategy.name: EmaCrossStrategy,
    DonchianStrategy.name: DonchianStrategy,
    RsiMeanRevStrategy.name: RsiMeanRevStrategy,
    IntradayMomentumStrategy.name: IntradayMomentumStrategy,
}


def get_strategy(name: str, cfg: StrategyConfig) -> BaseStrategy:
    if name not in STRATEGIES:
        raise ValueError(f"Okänd strategi '{name}'. Välj bland: {', '.join(STRATEGIES)}")
    return STRATEGIES[name](cfg)
