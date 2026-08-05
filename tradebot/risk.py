"""Riskhantering: positionsstorlek, dagligt förluststopp och exit-regler.

Positionsstorleken beräknas alltid utifrån stoppavståndet så att en
stoppad trade kostar ungefär risk_per_trade_pct av kapitalet — hävstången
ändrar inte risken per trade, bara hur mycket marginal som låses och var
likvidationspriset hamnar.
"""

import logging

from .config import RiskConfig
from .portfolio import Portfolio, Position

log = logging.getLogger("tradebot.risk")

# Likvidation sker i praktiken något före 100 % marginalförlust
# (underhållsmarginal); 0.9 är en medvetet konservativ approximation.
LIQ_BUFFER = 0.9


def liquidation_price(pos: Position) -> float:
    """Ungefärligt likvidationspris för en position. 0 = ingen (spot/1x long)."""
    if pos.leverage <= 1 and pos.side == "long":
        return 0.0
    move = LIQ_BUFFER / pos.leverage
    if pos.side == "long":
        return pos.entry_price * (1 - move)
    return pos.entry_price * (1 + move)


class RiskManager:
    def __init__(self, cfg: RiskConfig):
        self.cfg = cfg

    def daily_loss_hit(self, portfolio: Portfolio, prices: dict) -> bool:
        portfolio.roll_day()
        total = portfolio.total_value(prices)
        if total <= 0:
            return True
        loss_pct = -portfolio.daily_pnl / total * 100.0
        if loss_pct >= self.cfg.max_daily_loss_pct:
            log.warning(
                "Dagligt förluststopp: %.2f%% (gräns %.2f%%) — ingen ny handel idag.",
                loss_pct, self.cfg.max_daily_loss_pct,
            )
            return True
        return False

    def can_open(self, portfolio: Portfolio, prices: dict) -> bool:
        if len(portfolio.positions) >= self.cfg.max_positions:
            return False
        return not self.daily_loss_hit(portfolio, prices)

    def position_size(self, portfolio: Portfolio, prices: dict,
                      price: float, stop_loss: float,
                      leverage: float = 1.0) -> float:
        """Storlek så att förlusten vid stop loss ≈ risk_per_trade_pct av kapitalet."""
        stop_dist = abs(price - stop_loss)
        if stop_dist <= 0:
            return 0.0
        total = portfolio.total_value(prices)
        risk_amount = total * self.cfg.risk_per_trade_pct / 100.0
        amount = risk_amount / stop_dist
        # marginalen (notional/hävstång) får inte överstiga fri kassa
        margin = amount * price / leverage
        if margin > portfolio.equity:
            amount = portfolio.equity * leverage / price * 0.99
        if amount * price < self.cfg.min_order_quote:
            return 0.0
        return amount

    @staticmethod
    def exit_reason(pos: Position, price: float) -> str:
        liq = liquidation_price(pos)
        if pos.side == "long":
            if liq > 0 and price <= liq:
                return "liquidation"
            if pos.stop_loss > 0 and price <= pos.stop_loss:
                return "stop_loss"
            if pos.take_profit > 0 and price >= pos.take_profit:
                return "take_profit"
        else:
            if liq > 0 and price >= liq:
                return "liquidation"
            if pos.stop_loss > 0 and price >= pos.stop_loss:
                return "stop_loss"
            if pos.take_profit > 0 and price <= pos.take_profit:
                return "take_profit"
        return ""
