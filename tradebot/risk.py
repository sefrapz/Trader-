"""Riskhantering: positionsstorlek, dagligt förluststopp och exit-regler."""

import logging

from .config import RiskConfig
from .portfolio import Portfolio, Position

log = logging.getLogger("tradebot.risk")


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
                      price: float, stop_loss: float) -> float:
        """Storlek så att förlusten vid stop loss ≈ risk_per_trade_pct av kapitalet."""
        stop_dist = price - stop_loss
        if stop_dist <= 0:
            return 0.0
        total = portfolio.total_value(prices)
        risk_amount = total * self.cfg.risk_per_trade_pct / 100.0
        amount = risk_amount / stop_dist
        cost = amount * price
        # begränsa till tillgängligt kapital
        if cost > portfolio.equity:
            amount = portfolio.equity / price * 0.99
            cost = amount * price
        if cost < self.cfg.min_order_quote:
            return 0.0
        return amount

    @staticmethod
    def exit_reason(pos: Position, price: float) -> str:
        if pos.stop_loss > 0 and price <= pos.stop_loss:
            return "stop_loss"
        if pos.take_profit > 0 and price >= pos.take_profit:
            return "take_profit"
        return ""
