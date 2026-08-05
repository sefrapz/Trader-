"""Backtest av strategierna på historisk data från exchangen.

Motorn stödjer långa/korta positioner, hävstång med likvidationsmodell
och avgifter per ordersida. Finansieringsavgifter (funding) på perpetuals
simuleras INTE — se docs/STRATEGIER.md.

Kör alltid backtest (och paper trading) innan du ens överväger live-läge.
"""

import logging
from dataclasses import dataclass, field

import pandas as pd

from .config import Config
from .exchange import Exchange
from .risk import LIQ_BUFFER
from .strategy import STRATEGIES, BaseStrategy, get_strategy

log = logging.getLogger("tradebot.backtest")

SPOT_FEE_PCT = 0.10     # taker-avgift spot (Bybit/Binance-nivå)
FUTURES_FEE_PCT = 0.055  # taker-avgift USDT-perpetuals på Bybit


@dataclass
class BacktestResult:
    symbol: str
    strategy: str
    start_equity: float
    end_equity: float
    trades: int = 0
    wins: int = 0
    liquidations: int = 0
    max_drawdown_pct: float = 0.0
    trade_log: list = field(default_factory=list)

    @property
    def return_pct(self) -> float:
        return (self.end_equity / self.start_equity - 1.0) * 100.0

    @property
    def win_rate(self) -> float:
        return self.wins / self.trades * 100.0 if self.trades else 0.0

    def summary(self) -> str:
        liq = f" | {self.liquidations} likvidationer" if self.liquidations else ""
        return (
            f"{self.symbol} [{self.strategy}]: {self.trades} trades | "
            f"vinstandel {self.win_rate:.0f}% | avkastning {self.return_pct:+.2f}% | "
            f"max drawdown {self.max_drawdown_pct:.2f}%{liq}"
        )


class Backtester:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.futures = cfg.trading.mode == "futures"
        self.leverage = cfg.trading.leverage if self.futures else 1.0
        self.allow_shorts = self.futures and cfg.trading.allow_shorts

    def _default_fee(self) -> float:
        return FUTURES_FEE_PCT if self.futures else SPOT_FEE_PCT

    def run_symbol(self, df: pd.DataFrame, symbol: str, strategy: BaseStrategy,
                   fee_pct: float = None) -> BacktestResult:
        fee = (self._default_fee() if fee_pct is None else fee_pct) / 100.0
        lev = self.leverage
        equity = self.cfg.risk.start_equity
        result = BacktestResult(symbol, strategy.name, equity, equity)

        ind = strategy.add_indicators(df)
        peak = equity

        side = ""          # "", "long" eller "short"
        amount = entry = stop = take = margin = 0.0

        def open_pos(want: str, price: float, sl: float, tp: float):
            nonlocal side, amount, entry, stop, take, margin, equity
            stop_dist = abs(price - sl)
            if stop_dist <= 0:
                return
            risk_amount = equity * self.cfg.risk.risk_per_trade_pct / 100.0
            amt = risk_amount / stop_dist
            m = amt * price / lev
            if m > equity:
                amt = equity * lev / price * 0.99
                m = amt * price / lev
            if amt * price < self.cfg.risk.min_order_quote:
                return
            equity -= m + amt * price * fee
            side, amount, entry, stop, take, margin = want, amt, price, sl, tp, m

        def close_pos(price: float, reason: str, ts):
            nonlocal side, amount, margin, equity
            raw = amount * (price - entry) if side == "long" else amount * (entry - price)
            pnl = max(raw, -margin)  # likvidationsgolv: mer än marginalen kan inte förloras
            equity += margin + pnl - amount * price * fee
            result.trades += 1
            if pnl > 0:
                result.wins += 1
            if reason == "liquidation":
                result.liquidations += 1
            result.trade_log.append(
                {"time": str(ts), "action": f"close_{side}", "price": price,
                 "pnl": pnl, "reason": reason}
            )
            side, amount, margin = "", 0.0, 0.0

        liq_move = LIQ_BUFFER / lev

        for i in range(strategy.min_candles(), len(ind)):
            cur = ind.iloc[i]
            price = float(cur["close"])
            high, low, ts = float(cur["high"]), float(cur["low"]), cur["timestamp"]

            # 1) intracandle-exits: likvidation värst, sedan stop, sedan take
            if side == "long":
                liq = entry * (1 - liq_move) if lev > 1 else 0.0
                if liq > 0 and low <= liq:
                    close_pos(liq, "liquidation", ts)
                elif low <= stop:
                    close_pos(stop, "stop_loss", ts)
                elif high >= take:
                    close_pos(take, "take_profit", ts)
            elif side == "short":
                liq = entry * (1 + liq_move) if lev > 1 else float("inf")
                if high >= liq:
                    close_pos(liq, "liquidation", ts)
                elif high >= stop:
                    close_pos(stop, "stop_loss", ts)
                elif low <= take:
                    close_pos(take, "take_profit", ts)

            # 2) strategisignal på candlens stängning
            sig = strategy.signal_row(ind, i, side)
            if sig.action == "close" and side:
                close_pos(price, sig.reason or "signal", ts)
            elif sig.action in ("long", "short"):
                want = sig.action
                if want == "short" and not self.allow_shorts:
                    if side == "long":
                        close_pos(price, sig.reason or "kort signal", ts)
                elif side != want:
                    if side:
                        close_pos(price, f"vänder till {want}", ts)
                    open_pos(want, price, sig.stop_loss, sig.take_profit)
                    if side:
                        result.trade_log.append(
                            {"time": str(ts), "action": f"open_{side}", "price": price}
                        )

            value = equity + (margin + max(
                amount * (price - entry) if side == "long" else amount * (entry - price),
                -margin,
            ) if side else 0.0)
            peak = max(peak, value)
            dd = (peak - value) / peak * 100.0 if peak > 0 else 0.0
            result.max_drawdown_pct = max(result.max_drawdown_pct, dd)

        if side:
            close_pos(float(ind["close"].iloc[-1]), "backtest_slut", ind["timestamp"].iloc[-1])

        result.end_equity = equity
        return result

    def run(self, candle_limit: int = 1000, strategy_name: str = None) -> list:
        """Kör backtest. strategy_name=None använder konfigens strategi,
        'all' jämför samtliga strategier på samma data."""
        exchange = Exchange(self.cfg.exchange, live=False, futures=self.futures)
        names = (list(STRATEGIES) if strategy_name == "all"
                 else [strategy_name or self.cfg.trading.strategy])
        results = []
        for symbol in self.cfg.market.symbols:
            df = exchange.fetch_ohlcv(symbol, self.cfg.market.timeframe, candle_limit)
            log.info("%s: %d candles (%s – %s)", symbol, len(df),
                     df["timestamp"].iloc[0], df["timestamp"].iloc[-1])
            for name in names:
                res = self.run_symbol(df, symbol, get_strategy(name, self.cfg.strategy))
                log.info(res.summary())
                results.append(res)
        return results
