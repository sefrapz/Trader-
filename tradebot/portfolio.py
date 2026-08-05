"""Portfölj- och positionshantering med persistens till JSON.

Används både i paper-läge (simulerade fills) och live-läge (spegel av
faktiska ordrar). All PnL räknas i quote-valutan (t.ex. USDT).
"""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone


@dataclass
class Position:
    symbol: str
    amount: float          # mängd bas-valuta (t.ex. BTC)
    entry_price: float
    stop_loss: float
    take_profit: float
    opened_at: str = ""


@dataclass
class Portfolio:
    equity: float
    positions: dict = field(default_factory=dict)   # symbol -> Position
    daily_pnl: float = 0.0
    daily_pnl_date: str = ""
    trade_log: list = field(default_factory=list)

    # -- persistens -------------------------------------------------------
    @classmethod
    def load(cls, path: str, start_equity: float) -> "Portfolio":
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            pf = cls(
                equity=raw["equity"],
                daily_pnl=raw.get("daily_pnl", 0.0),
                daily_pnl_date=raw.get("daily_pnl_date", ""),
                trade_log=raw.get("trade_log", []),
            )
            for sym, p in raw.get("positions", {}).items():
                pf.positions[sym] = Position(**p)
            return pf
        return cls(equity=start_equity)

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        data = {
            "equity": self.equity,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_date": self.daily_pnl_date,
            "positions": {s: asdict(p) for s, p in self.positions.items()},
            "trade_log": self.trade_log[-500:],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    # -- daglig PnL -------------------------------------------------------
    def roll_day(self) -> None:
        today = date.today().isoformat()
        if self.daily_pnl_date != today:
            self.daily_pnl_date = today
            self.daily_pnl = 0.0

    # -- handel -----------------------------------------------------------
    def open_position(self, symbol: str, amount: float, price: float,
                      stop_loss: float, take_profit: float) -> Position:
        pos = Position(
            symbol=symbol, amount=amount, entry_price=price,
            stop_loss=stop_loss, take_profit=take_profit,
            opened_at=datetime.now(timezone.utc).isoformat(),
        )
        self.positions[symbol] = pos
        self.equity -= amount * price
        self.trade_log.append({
            "time": pos.opened_at, "symbol": symbol, "side": "buy",
            "amount": amount, "price": price,
        })
        return pos

    def close_position(self, symbol: str, price: float, reason: str = "") -> float:
        pos = self.positions.pop(symbol)
        proceeds = pos.amount * price
        pnl = proceeds - pos.amount * pos.entry_price
        self.equity += proceeds
        self.roll_day()
        self.daily_pnl += pnl
        self.trade_log.append({
            "time": datetime.now(timezone.utc).isoformat(), "symbol": symbol,
            "side": "sell", "amount": pos.amount, "price": price,
            "pnl": pnl, "reason": reason,
        })
        return pnl

    def total_value(self, prices: dict) -> float:
        value = self.equity
        for sym, pos in self.positions.items():
            value += pos.amount * prices.get(sym, pos.entry_price)
        return value
