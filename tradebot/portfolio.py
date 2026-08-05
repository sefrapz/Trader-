"""Portfölj- och positionshantering med persistens till JSON.

Stödjer långa och korta positioner med hävstång. Kapitalmodellen är
marginalbaserad: när en position öppnas låses marginalen
(notional / hävstång) från kassan, och vid stängning återförs marginalen
plus/minus PnL. Förlusten i en position kan aldrig överstiga marginalen
(likvidationsmodell). All PnL räknas i quote-valutan (t.ex. USDT).
"""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone


@dataclass
class Position:
    symbol: str
    side: str              # "long" eller "short"
    amount: float          # mängd bas-valuta (t.ex. BTC)
    entry_price: float
    stop_loss: float
    take_profit: float
    leverage: float = 1.0
    margin: float = 0.0    # låst kapital i quote-valuta
    opened_at: str = ""
    context: dict = field(default_factory=dict)  # indikatorvärden vid entry

    def unrealized_pnl(self, price: float) -> float:
        if self.side == "long":
            pnl = self.amount * (price - self.entry_price)
        else:
            pnl = self.amount * (self.entry_price - price)
        return max(pnl, -self.margin)  # förlust begränsad av marginalen


@dataclass
class Portfolio:
    equity: float                                    # fri kassa (quote)
    positions: dict = field(default_factory=dict)    # symbol -> Position
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
                # bakåtkompatibilitet med tidigare spot-format utan marginalfält
                p.setdefault("side", "long")
                p.setdefault("leverage", 1.0)
                p.setdefault("margin", p["amount"] * p["entry_price"])
                p.setdefault("context", {})
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
                      stop_loss: float, take_profit: float,
                      side: str = "long", leverage: float = 1.0,
                      context: dict = None) -> Position:
        margin = amount * price / leverage
        pos = Position(
            symbol=symbol, side=side, amount=amount, entry_price=price,
            stop_loss=stop_loss, take_profit=take_profit,
            leverage=leverage, margin=margin,
            opened_at=datetime.now(timezone.utc).isoformat(),
            context=context or {},
        )
        self.positions[symbol] = pos
        self.equity -= margin
        self.trade_log.append({
            "time": pos.opened_at, "symbol": symbol, "action": f"open_{side}",
            "amount": amount, "price": price, "leverage": leverage,
        })
        return pos

    def close_position(self, symbol: str, price: float, reason: str = "") -> float:
        pos = self.positions.pop(symbol)
        pnl = pos.unrealized_pnl(price)
        self.equity += pos.margin + pnl
        self.roll_day()
        self.daily_pnl += pnl
        self.trade_log.append({
            "time": datetime.now(timezone.utc).isoformat(), "symbol": symbol,
            "action": f"close_{pos.side}", "amount": pos.amount, "price": price,
            "pnl": pnl, "reason": reason,
        })
        return pnl

    def total_value(self, prices: dict) -> float:
        value = self.equity
        for sym, pos in self.positions.items():
            price = prices.get(sym, pos.entry_price)
            value += pos.margin + pos.unrealized_pnl(price)
        return value
