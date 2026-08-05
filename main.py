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
    parser = argparse.ArgumentParser(description="Krypto-tradebot (trend/breakout/meanrev)")
    parser.add_argument("mode", choices=["backtest", "paper", "live", "analyze"])
    parser.add_argument("--source", choices=["paper", "backtest", "all"], default="all",
                        help="analyze: vilka journaler som analyseras (default: alla)")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--candles", type=int, default=1000,
                        help="antal candles i backtest (pagineras automatiskt)")
    parser.add_argument("--strategy", default=None,
                        help="strategi i backtest: ema_cross, donchian, rsi_meanrev "
                             "eller 'all' för att jämföra samtliga")
    parser.add_argument("--timeframe", default=None,
                        help="överstyr konfigens timeframe i backtest, t.ex. 1h, 4h, 1d")
    parser.add_argument("--adx-min", type=float, default=None,
                        help="överstyr regimfiltret i backtest (0 = av), för A/B-test")
    parser.add_argument("--trading-mode", choices=["spot", "futures"], default=None,
                        help="överstyr konfigens trading.mode i backtest")
    parser.add_argument("--max-atr", type=float, default=None,
                        help="överstyr volatilitetsfiltret i backtest: hoppa över "
                             "entries med ATR%% av pris över detta (0 = av)")
    parser.add_argument("--i-understand-the-risk", action="store_true",
                        help="krävs för live-läge")
    args = parser.parse_args()

    cfg = load_config(args.config,
                      trading_mode=args.trading_mode if args.mode == "backtest" else None)
    setup_logging(cfg.bot.log_file)
    log = logging.getLogger("tradebot")

    if args.mode == "analyze":
        from tradebot.analyze import run_analysis
        paths = []
        if args.source in ("paper", "all"):
            paths.append(cfg.bot.journal_file)
        if args.source in ("backtest", "all"):
            paths.append(cfg.bot.backtest_journal_file)
        report = run_analysis(paths, save_to=cfg.bot.analysis_file)
        print(report)
        print(f"\nRapporten är även sparad i {cfg.bot.analysis_file}")
        return 0

    if args.mode == "backtest":
        if args.timeframe:
            cfg.market.timeframe = args.timeframe
        if args.adx_min is not None:
            cfg.strategy.adx_min = args.adx_min
        if args.max_atr is not None:
            cfg.strategy.max_entry_atr_pct = args.max_atr
        results = Backtester(cfg).run(candle_limit=args.candles,
                                      strategy_name=args.strategy)
        print("\n=== Backtestresultat "
              f"({cfg.trading.mode}"
              f"{', ' + str(int(cfg.trading.leverage)) + 'x' if cfg.trading.mode == 'futures' else ''}"
              ") ===")
        for res in sorted(results, key=lambda r: -r.return_pct):
            print(res.summary())
        benchmarks = {r.symbol: r.benchmark_pct for r in results}
        print("\nKöp & behåll samma period (jämförelse):")
        for sym, pct in benchmarks.items():
            print(f"  {sym}: {pct:+.2f}%")
        print(
            "OBS: boten riskerar ~1% av kapitalet per trade — jämför "
            "riskjusterat (drawdown), inte bara rå avkastning."
        )
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
