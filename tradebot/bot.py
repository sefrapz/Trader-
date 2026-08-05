"""Huvudloopen: hämtar data, utvärderar strategin och lägger ordrar.

Samma kod driver paper- och live-läge — skillnaden är bara om ordrarna
skickas till exchangen eller simuleras mot livepriser. I futures-läge
kan boten gå både lång och kort, med konfigurerad hävstång.
"""

import logging
import time

from datetime import datetime, timezone

from .analyze import run_analysis
from .config import Config
from .exchange import Exchange
from .journal import Journal, make_record
from .portfolio import Portfolio
from .risk import RiskManager
from .strategy import get_strategy

log = logging.getLogger("tradebot.bot")


class TradeBot:
    def __init__(self, cfg: Config, live: bool = False):
        self.cfg = cfg
        self.live = live
        self.futures = cfg.trading.mode == "futures"
        self.leverage = cfg.trading.leverage if self.futures else 1.0
        self.exchange = Exchange(cfg.exchange, live=live, futures=self.futures)
        self.strategy = get_strategy(cfg.trading.strategy, cfg.strategy)
        self.risk = RiskManager(cfg.risk)
        self.portfolio = Portfolio.load(cfg.bot.state_file, cfg.risk.start_equity)
        self.journal = Journal(cfg.bot.journal_file)

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

            # stop/take/likvidation reagerar på senaste pris (pågående candle) ...
            self._check_exits(symbol, price)
            # ... men signaler beräknas bara på stängda candles, precis som i
            # backtestet — annars flimrar signalerna intradag
            closed = df.iloc[:-1] if len(df) > 1 else df
            self._handle_signal(symbol, closed, prices)

        total = self.portfolio.total_value(prices)
        pos_desc = [f"{s} ({p.side} {p.leverage:.0f}x)"
                    for s, p in self.portfolio.positions.items()]
        log.info(
            "Portföljvärde: %.2f | fri kassa: %.2f | positioner: %s | dagens PnL: %.2f",
            total, self.portfolio.equity, pos_desc or "inga", self.portfolio.daily_pnl,
        )
        self.portfolio.save(self.cfg.bot.state_file)

    def _check_exits(self, symbol: str, price: float) -> None:
        pos = self.portfolio.positions.get(symbol)
        if not pos:
            return
        reason = self.risk.exit_reason(pos, price)
        if reason:
            if reason == "liquidation":
                log.warning("%s: LIKVIDATION vid %.2f — hela marginalen förlorad", symbol, price)
            self._close(symbol, price, reason)

    def _handle_signal(self, symbol: str, df, prices: dict) -> None:
        pos = self.portfolio.positions.get(symbol)
        side = pos.side if pos else ""
        signal = self.strategy.evaluate(df, side=side)

        if signal.action == "hold":
            return

        if signal.action == "close":
            if pos:
                self._close(symbol, signal.price, signal.reason)
            return

        # signal.action är "long" eller "short"
        want = signal.action
        if want == "short" and not (self.futures and self.cfg.trading.allow_shorts):
            # utan shorts tolkas kort signal som "lämna marknaden"
            if pos and pos.side == "long":
                self._close(symbol, signal.price, signal.reason)
            return

        if pos:
            if pos.side == want:
                return  # redan rätt håll
            self._close(symbol, signal.price, f"vänder till {want}")

        if not self.risk.can_open(self.portfolio, prices):
            log.info("%s: %s-signal men risklagret säger nej (%s)",
                     symbol, want, signal.reason)
            return
        amount = self.risk.position_size(
            self.portfolio, prices, signal.price, signal.stop_loss, self.leverage
        )
        if amount <= 0:
            log.info("%s: %s-signal men för liten position, hoppar över", symbol, want)
            return
        amount = self.exchange.normalize_amount(symbol, amount)
        if want == "long":
            self.exchange.market_buy(symbol, amount)
        else:
            self.exchange.market_sell(symbol, amount)
        self.portfolio.open_position(
            symbol, amount, signal.price, signal.stop_loss, signal.take_profit,
            side=want, leverage=self.leverage,
            context=self.strategy.entry_context(df),
        )
        log.info(
            "ÖPPNA %s %s: %.8f @ %.2f, %sx (stop %.2f, take %.2f) — %s",
            want.upper(), symbol, amount, signal.price, int(self.leverage),
            signal.stop_loss, signal.take_profit, signal.reason,
        )

    def _close(self, symbol: str, price: float, reason: str) -> None:
        pos = self.portfolio.positions[symbol]
        if pos.side == "long":
            self.exchange.market_sell(symbol, pos.amount, reduce_only=True)
        else:
            self.exchange.market_buy(symbol, pos.amount, reduce_only=True)
        pnl = self.portfolio.close_position(symbol, price, reason)
        log.info("STÄNG %s %s: %.8f @ %.2f | PnL %.2f | %s",
                 pos.side.upper(), symbol, pos.amount, price, pnl, reason)
        self.journal.record(make_record(
            mode="live" if self.live else "paper",
            strategy=self.strategy.name,
            timeframe=self.cfg.market.timeframe,
            symbol=symbol, side=pos.side, leverage=pos.leverage,
            amount=pos.amount, entry_price=pos.entry_price, exit_price=price,
            pnl=pnl, margin=pos.margin, reason=reason,
            opened_at=pos.opened_at,
            closed_at=datetime.now(timezone.utc).isoformat(),
            context=pos.context,
        ))
        self._refresh_analysis()

    def _refresh_analysis(self) -> None:
        """Automatisk analys: uppdateras efter varje stängd trade."""
        try:
            run_analysis([self.cfg.bot.journal_file],
                         save_to=self.cfg.bot.analysis_file)
            log.info("Analys uppdaterad: %s", self.cfg.bot.analysis_file)
        except Exception:
            log.exception("Kunde inte uppdatera analysen")

    # -- körning ----------------------------------------------------------
    def run(self) -> None:
        mode = "LIVE" if self.live else "PAPER"
        log.info(
            "Startar tradebot i %s-läge | %s | strategi: %s | symboler: %s | timeframe: %s%s",
            mode, self.cfg.trading.mode, self.strategy.name,
            self.cfg.market.symbols, self.cfg.market.timeframe,
            f" | hävstång {int(self.leverage)}x" if self.futures else "",
        )
        if self.live:
            log.warning("LIVE-läge: riktiga ordrar kommer att läggas!")
            for symbol in self.cfg.market.symbols:
                self.exchange.set_leverage(symbol, self.leverage)
        while True:
            try:
                self.step()
            except KeyboardInterrupt:
                log.info("Avslutar på användarens begäran.")
                break
            except Exception:
                log.exception("Fel i huvudloopen, försöker igen.")
            time.sleep(self.cfg.bot.poll_seconds)
