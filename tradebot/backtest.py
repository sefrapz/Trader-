"""Backtest av strategin på historisk data från exchangen.

Kör alltid backtest (och paper trading) innan du ens överväger live-läge.
"""

import logging
from dataclasses import dataclass, field

import pandas as pd

from .config import Config
from .exchange import Exchange
from .strategy import EmaRsiStrategy

log = logging.getLogger("tradebot.backtest")


@dataclass
class BacktestResult:
    symbol: str
    start_equity: float
    end_equity: float
    trades: int = 0
    wins: int = 0
    max_drawdown_pct: float = 0.0
    trade_log: list = field(default_factory=list)

    @property
    def return_pct(self) -> float:
        return (self.end_equity / self.start_equity - 1.0) * 100.0

    @property
    def win_rate(self) -> float:
        return self.wins / self.trades * 100.0 if self.trades else 0.0

    def summary(self) -> str:
        return (
            f"{self.symbol}: {self.trades} trades | vinstandel {self.win_rate:.0f}% | "
            f"avkastning {self.return_pct:+.2f}% | max drawdown {self.max_drawdown_pct:.2f}%"
        )


class Backtester:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.strategy = EmaRsiStrategy(cfg.strategy)

    def run_symbol(self, df: pd.DataFrame, symbol: str,
                   fee_pct: float = 0.1) -> BacktestResult:
        scfg = self.cfg.strategy
        equity = self.cfg.risk.start_equity
        result = BacktestResult(symbol, equity, equity)

        ind = self.strategy.add_indicators(df)
        fee = fee_pct / 100.0
        peak = equity
        amount = 0.0
        entry = stop = take = 0.0

        for i in range(self.strategy.min_candles(), len(ind)):
            cur, prev = ind.iloc[i], ind.iloc[i - 1]
            price = float(cur["close"])

            if amount > 0:
                # kolla stop/take mot candlens high/low, annars EMA-exit
                exit_price = None
                if float(cur["low"]) <= stop:
                    exit_price = stop
                elif float(cur["high"]) >= take:
                    exit_price = take
                elif prev["ema_fast"] >= prev["ema_slow"] and cur["ema_fast"] < cur["ema_slow"]:
                    exit_price = price
                if exit_price is not None:
                    proceeds = amount * exit_price * (1 - fee)
                    pnl = proceeds - amount * entry
                    equity += proceeds
                    result.trades += 1
                    if pnl > 0:
                        result.wins += 1
                    result.trade_log.append(
                        {"time": str(cur["timestamp"]), "side": "sell",
                         "price": exit_price, "pnl": pnl}
                    )
                    amount = 0.0
            else:
                crossed_up = (
                    prev["ema_fast"] <= prev["ema_slow"]
                    and cur["ema_fast"] > cur["ema_slow"]
                    and cur["rsi"] < scfg.rsi_overbought
                )
                if crossed_up:
                    stop = price - scfg.atr_stop_mult * float(cur["atr"])
                    take = price + scfg.atr_take_mult * float(cur["atr"])
                    stop_dist = price - stop
                    if stop_dist <= 0:
                        continue
                    risk_amount = equity * self.cfg.risk.risk_per_trade_pct / 100.0
                    amount = min(risk_amount / stop_dist, equity / price)
                    cost = amount * price * (1 + fee)
                    if cost > equity:
                        amount = equity / (price * (1 + fee))
                        cost = amount * price * (1 + fee)
                    equity -= cost
                    entry = price
                    result.trade_log.append(
                        {"time": str(cur["timestamp"]), "side": "buy", "price": price}
                    )

            value = equity + amount * price
            peak = max(peak, value)
            dd = (peak - value) / peak * 100.0
            result.max_drawdown_pct = max(result.max_drawdown_pct, dd)

        # stäng ev. öppen position på sista candlen
        if amount > 0:
            last = float(ind["close"].iloc[-1])
            proceeds = amount * last * (1 - fee)
            pnl = proceeds - amount * entry
            equity += proceeds
            result.trades += 1
            if pnl > 0:
                result.wins += 1

        result.end_equity = equity
        return result

    def run(self, candle_limit: int = 1000) -> list:
        exchange = Exchange(self.cfg.exchange, live=False)
        results = []
        for symbol in self.cfg.market.symbols:
            df = exchange.fetch_ohlcv(symbol, self.cfg.market.timeframe, candle_limit)
            res = self.run_symbol(df, symbol)
            log.info(res.summary())
            results.append(res)
        return results
