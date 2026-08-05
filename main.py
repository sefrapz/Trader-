#!/usr/bin/env python3
"""Startpunkt för tradeboten.

    python main.py backtest            # testa strategin på historisk data
    python main.py paper               # handla med låtsaspengar mot livepriser
    python main.py live --i-understand-the-risk   # riktiga pengar!
"""

import argparse
import logging
import sys

from tradebot.backtest import Backtester
from tradebot.bot import TradeBot
from tradebot.config import load_config


def setup_logging(log_file: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Krypto-tradebot (EMA/RSI + ATR-risk)")
    parser.add_argument("mode", choices=["backtest", "paper", "live"])
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--candles", type=int, default=1000,
                        help="antal candles i backtest")
    parser.add_argument("--i-understand-the-risk", action="store_true",
                        help="krävs för live-läge")
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(cfg.bot.log_file)
    log = logging.getLogger("tradebot")

    if args.mode == "backtest":
        results = Backtester(cfg).run(candle_limit=args.candles)
        print("\n=== Backtestresultat ===")
        for res in results:
            print(res.summary())
        print(
            "\nOBS: historisk avkastning säger inget säkert om framtiden. "
            "Kör paper-läget en längre period innan live."
        )
        return 0

    if args.mode == "live":
        if not args.i_understand_the_risk:
            print(
                "Live-läge handlar med riktiga pengar och kan förlora hela beloppet.\n"
                "Starta med: python main.py live --i-understand-the-risk\n"
                "Kör gärna 'paper'-läget en längre tid först."
            )
            return 1
        log.warning("Startar i LIVE-läge — riktiga ordrar läggs på exchangen.")

    bot = TradeBot(cfg, live=(args.mode == "live"))
    bot.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
