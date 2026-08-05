"""Huvudloopen: hämtar data, utvärderar strategin och lägger ordrar.

Samma kod driver paper- och live-läge — skillnaden är bara om ordrarna
skickas till exchangen eller simuleras mot livepriser.
"""

import logging
import time

from .config import Config
from .exchange import Exchange
from .portfolio import Portfolio
from .risk import RiskManager
from .strategy import EmaRsiStrategy

log = logging.getLogger("tradebot.bot")


class TradeBot:
    def __init__(self, cfg: Config, live: bool = False):
        self.cfg = cfg
        self.live = live
        self.exchange = Exchange(cfg.exchange, live=live)
        self.strategy = EmaRsiStrategy(cfg.strategy)
        self.risk = RiskManager(cfg.risk)
        self.portfolio = Portfolio.load(cfg.bot.state_file, cfg.risk.start_equity)

    # -- en analysrunda ---------------------------------------------------
    def step(self) -> None:
        prices = {}
        for symbol in self.cfg.market.symbols:
            try:
                df = self.exchange.fetch_ohlcv(
                    symbol, self.cfg.market.timeframe, self.cfg.market.candle_limit
                )
            except Exception:
                log.exception("Kunde inte hämta data för %s", symbol)
                continue
            price = float(df["close"].iloc[-1])
            prices[symbol] = price

            self._check_exits(symbol, price)
            self._check_entry(symbol, df, prices)

        total = self.portfolio.total_value(prices)
        log.info(
            "Portföljvärde: %.2f | kassa: %.2f | positioner: %s | dagens PnL: %.2f",
            total, self.portfolio.equity,
            list(self.portfolio.positions) or "inga", self.portfolio.daily_pnl,
        )
        self.portfolio.save(self.cfg.bot.state_file)

    def _check_exits(self, symbol: str, price: float) -> None:
        pos = self.portfolio.positions.get(symbol)
        if not pos:
            return
        reason = self.risk.exit_reason(pos, price)
        if reason:
            self._sell(symbol, price, reason)

    def _check_entry(self, symbol: str, df, prices: dict) -> None:
        signal = self.strategy.evaluate(df)
        has_pos = symbol in self.portfolio.positions

        if signal.action == "sell" and has_pos:
            self._sell(symbol, signal.price, signal.reason)
        elif signal.action == "buy" and not has_pos:
            if not self.risk.can_open(self.portfolio, prices):
                log.info("%s: köpsignal men risklagret säger nej (%s)", symbol, signal.reason)
                return
            amount = self.risk.position_size(
                self.portfolio, prices, signal.price, signal.stop_loss
            )
            if amount <= 0:
                log.info("%s: köpsignal men för liten position, hoppar över", symbol)
                return
            amount = self.exchange.normalize_amount(symbol, amount)
            self.exchange.market_buy(symbol, amount)
            self.portfolio.open_position(
                symbol, amount, signal.price, signal.stop_loss, signal.take_profit
            )
            log.info(
                "KÖP %s: %.8f @ %.2f (stop %.2f, take %.2f) — %s",
                symbol, amount, signal.price, signal.stop_loss,
                signal.take_profit, signal.reason,
            )

    def _sell(self, symbol: str, price: float, reason: str) -> None:
        pos = self.portfolio.positions[symbol]
        self.exchange.market_sell(symbol, pos.amount)
        pnl = self.portfolio.close_position(symbol, price, reason)
        log.info("SÄLJ %s: %.8f @ %.2f | PnL %.2f | %s", symbol, pos.amount, price, pnl, reason)

    # -- körning ----------------------------------------------------------
    def run(self) -> None:
        mode = "LIVE" if self.live else "PAPER"
        log.info(
            "Startar tradebot i %s-läge | symboler: %s | timeframe: %s",
            mode, self.cfg.market.symbols, self.cfg.market.timeframe,
        )
        if self.live:
            log.warning("LIVE-läge: riktiga ordrar kommer att läggas!")
        while True:
            try:
                self.step()
            except KeyboardInterrupt:
                log.info("Avslutar på användarens begäran.")
                break
            except Exception:
                log.exception("Fel i huvudloopen, försöker igen.")
            time.sleep(self.cfg.bot.poll_seconds)
