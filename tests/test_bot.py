"""Tester för strategier, risk, portfölj och backtest — körs helt offline."""

import numpy as np
import pandas as pd
import pytest

from tradebot.backtest import Backtester
from tradebot.config import (
    BotConfig, Config, ExchangeConfig, MarketConfig, RiskConfig,
    StrategyConfig, TradingConfig,
)
from tradebot.portfolio import Portfolio
from tradebot.risk import RiskManager, liquidation_price
from tradebot.strategy import (
    DonchianStrategy, EmaCrossStrategy, RsiMeanRevStrategy, get_strategy,
)


def make_config(**trading_kwargs) -> Config:
    return Config(
        exchange=ExchangeConfig(),
        market=MarketConfig(),
        trading=TradingConfig(**trading_kwargs),
        strategy=StrategyConfig(),
        risk=RiskConfig(),
        bot=BotConfig(),
    )


def make_ohlcv(closes) -> pd.DataFrame:
    closes = np.asarray(closes, dtype=float)
    ts = pd.date_range("2024-01-01", periods=len(closes), freq="h", tz="UTC")
    return pd.DataFrame({
        "timestamp": ts,
        "open": closes,
        "high": closes * 1.005,
        "low": closes * 0.995,
        "close": closes,
        "volume": np.ones(len(closes)),
    })


# -- strategier -----------------------------------------------------------

def test_ema_long_signal_on_uptrend_cross():
    # nedgång följt av lugn uppgång ger EMA-korsning uppåt utan överköpt RSI
    rng = np.random.default_rng(7)
    down = np.linspace(104, 100, 50)
    up = np.linspace(100, 104, 40)
    closes = np.concatenate([down, up]) + rng.normal(0, 0.15, 90)
    strat = EmaCrossStrategy(StrategyConfig())
    df = make_ohlcv(closes)

    actions = [strat.evaluate(df.iloc[:i]).action
               for i in range(strat.min_candles(), len(df) + 1)]
    assert "long" in actions

    idx = actions.index("long") + strat.min_candles()
    sig = strat.evaluate(df.iloc[:idx])
    assert sig.stop_loss < sig.price < sig.take_profit


def test_ema_short_signal_on_downtrend_cross():
    rng = np.random.default_rng(3)
    up = np.linspace(100, 104, 50)
    down = np.linspace(104, 100, 40)
    closes = np.concatenate([up, down]) + rng.normal(0, 0.15, 90)
    strat = EmaCrossStrategy(StrategyConfig())
    df = make_ohlcv(closes)

    actions = [strat.evaluate(df.iloc[:i]).action
               for i in range(strat.min_candles(), len(df) + 1)]
    assert "short" in actions

    idx = actions.index("short") + strat.min_candles()
    sig = strat.evaluate(df.iloc[:idx])
    # för en short ligger stoppen ovanför och take profit under priset
    assert sig.take_profit < sig.price < sig.stop_loss


def test_donchian_breakout_long():
    # platt intervall följt av tydligt utbrott uppåt
    closes = [100 + (i % 5) * 0.1 for i in range(40)] + [103, 104, 105]
    strat = DonchianStrategy(StrategyConfig())
    sig = strat.evaluate(make_ohlcv(closes))
    assert sig.action == "long"


def test_donchian_exit_when_long():
    # utbrott uppåt följt av skarpt fall under exitkanalen
    closes = [100 + (i % 5) * 0.1 for i in range(40)] + [104, 105, 97]
    strat = DonchianStrategy(StrategyConfig())
    sig = strat.evaluate(make_ohlcv(closes), side="long")
    assert sig.action == "close"


def test_meanrev_long_on_oversold_dip_in_uptrend():
    # lång upptrend med en dipp som är skarp men stannar över EMA200
    closes = list(np.linspace(100, 160, 260)) + [155, 150, 147, 145]
    strat = RsiMeanRevStrategy(StrategyConfig())
    sig = strat.evaluate(make_ohlcv(closes))
    assert sig.action == "long"


def test_adx_separates_trend_from_noise():
    from tradebot.indicators import adx
    rng = np.random.default_rng(7)
    trend = np.concatenate([np.linspace(104, 100, 50), np.linspace(100, 104, 40)])
    noise = 100 + rng.normal(0, 0.3, 90)
    adx_trend = float(adx(make_ohlcv(trend), 14).iloc[-1])
    adx_noise = float(adx(make_ohlcv(noise), 14).iloc[-1])
    assert adx_trend > 25
    assert adx_noise < 15
    assert adx_trend > adx_noise


def test_adx_filter_blocks_entries_in_choppy_market():
    # slumpbrus utan trend: korsningar sker, men filtret ska stoppa entries
    rng = np.random.default_rng(11)
    noise = 100 + rng.normal(0, 0.3, 200)
    df = make_ohlcv(noise)

    filtered = EmaCrossStrategy(StrategyConfig(adx_min=20.0))
    unfiltered = EmaCrossStrategy(StrategyConfig(adx_min=0.0))

    def entries(strat):
        return sum(strat.evaluate(df.iloc[:i]).action in ("long", "short")
                   for i in range(strat.min_candles(), len(df) + 1))

    assert entries(unfiltered) > 0, "utan filter ska bruset ge entries"
    assert entries(filtered) == 0, "med filter ska trendlöst brus ge noll entries"


def test_get_strategy_rejects_unknown_name():
    with pytest.raises(ValueError):
        get_strategy("hemlig_vinnarstrategi", StrategyConfig())


def test_hold_with_too_little_data():
    strat = EmaCrossStrategy(StrategyConfig())
    assert strat.evaluate(make_ohlcv([100, 101, 102])).action == "hold"


# -- risk & portfölj ------------------------------------------------------

def test_position_sizing_risks_configured_pct():
    risk = RiskManager(RiskConfig(start_equity=10000, risk_per_trade_pct=1.0))
    pf = Portfolio(equity=10000)
    amount = risk.position_size(pf, {}, price=100.0, stop_loss=95.0)
    # risk = 1% av 10000 = 100; stoppavstånd 5 => 20 enheter
    assert amount == pytest.approx(20.0)
    assert amount * (100.0 - 95.0) == pytest.approx(100.0)


def test_position_sizing_same_risk_with_leverage():
    # hävstången ändrar inte risken per trade, bara marginalbehovet
    risk = RiskManager(RiskConfig(start_equity=10000, risk_per_trade_pct=1.0))
    pf = Portfolio(equity=10000)
    amount = risk.position_size(pf, {}, price=100.0, stop_loss=95.0, leverage=5.0)
    assert amount == pytest.approx(20.0)


def test_short_position_pnl():
    pf = Portfolio(equity=10000)
    pf.open_position("BTC/USDT", 1.0, 100.0, 110.0, 80.0, side="short", leverage=2.0)
    assert pf.equity == pytest.approx(10000 - 50.0)  # marginal = 100/2
    pnl = pf.close_position("BTC/USDT", 90.0)        # pris ner 10 => +10 för short
    assert pnl == pytest.approx(10.0)
    assert pf.equity == pytest.approx(10010.0)


def test_loss_capped_at_margin():
    pf = Portfolio(equity=10000)
    pf.open_position("BTC/USDT", 1.0, 100.0, 0.0, 0.0, side="long", leverage=5.0)
    # pris kraschar långt under likvidationsnivån — förlust max = marginalen (20)
    pnl = pf.close_position("BTC/USDT", 1.0)
    assert pnl == pytest.approx(-20.0)
    assert pf.equity == pytest.approx(9980.0)


def test_liquidation_price_and_exit_reason():
    pf = Portfolio(equity=10000)
    pos = pf.open_position("BTC/USDT", 1.0, 100.0, 0.0, 0.0, side="long", leverage=5.0)
    liq = liquidation_price(pos)
    assert liq == pytest.approx(100.0 * (1 - 0.9 / 5))
    assert RiskManager.exit_reason(pos, liq - 0.01) == "liquidation"

    pos_s = pf.open_position("ETH/USDT", 1.0, 100.0, 0.0, 0.0, side="short", leverage=4.0)
    assert RiskManager.exit_reason(pos_s, liquidation_price(pos_s) + 0.01) == "liquidation"


def test_max_positions_blocks_new_entries():
    risk = RiskManager(RiskConfig(max_positions=1))
    pf = Portfolio(equity=10000)
    pf.open_position("BTC/USDT", 0.1, 100.0, 90.0, 120.0)
    assert not risk.can_open(pf, {"BTC/USDT": 100.0})


def test_daily_loss_stop():
    risk = RiskManager(RiskConfig(max_daily_loss_pct=5.0))
    pf = Portfolio(equity=10000)
    pf.roll_day()
    pf.daily_pnl = -600.0  # -6% av 10000
    assert risk.daily_loss_hit(pf, {})


def test_portfolio_roundtrip(tmp_path):
    path = str(tmp_path / "pf.json")
    pf = Portfolio(equity=5000)
    pf.open_position("ETH/USDT", 1.0, 2000.0, 1900.0, 2200.0, side="short", leverage=3.0)
    pf.save(path)

    loaded = Portfolio.load(path, start_equity=0)
    assert loaded.equity == pf.equity
    assert loaded.positions["ETH/USDT"].side == "short"
    pnl = loaded.close_position("ETH/USDT", 1900.0)
    assert pnl == pytest.approx(100.0)


# -- backtest -------------------------------------------------------------

def sawtooth(rounds: int = 6):
    closes = []
    for _ in range(rounds):
        closes += list(np.linspace(100, 90, 30)) + list(np.linspace(90, 110, 30))
    return closes


def test_backtest_spot_runs_and_trades():
    cfg = make_config(mode="spot")
    bt = Backtester(cfg)
    strat = EmaCrossStrategy(cfg.strategy)
    res = bt.run_symbol(make_ohlcv(sawtooth()), "TEST/USDT", strat)
    assert res.trades > 0
    assert res.end_equity > 0
    assert res.liquidations == 0
    assert 0.0 <= res.max_drawdown_pct <= 100.0


def test_backtest_futures_with_leverage_and_shorts():
    cfg = make_config(mode="futures", leverage=3.0, allow_shorts=True)
    bt = Backtester(cfg)
    strat = EmaCrossStrategy(cfg.strategy)
    res = bt.run_symbol(make_ohlcv(sawtooth()), "TEST/USDT", strat)
    assert res.trades > 0
    assert res.end_equity > 0
    shorts = [t for t in res.trade_log if t["action"] == "close_short"]
    assert shorts, "futures-läget ska ha handlat kort någon gång"


def test_backtest_writes_journal_with_context():
    cfg = make_config(mode="futures", leverage=2.0)
    bt = Backtester(cfg)
    strat = EmaCrossStrategy(cfg.strategy)
    records = []
    res = bt.run_symbol(make_ohlcv(sawtooth()), "TEST/USDT", strat,
                        journal_records=records)
    assert len(records) == res.trades
    rec = records[0]
    assert rec["mode"] == "backtest"
    assert rec["strategy"] == "ema_cross"
    assert rec["side"] in ("long", "short")
    assert "rsi" in rec["context"] and "atr" in rec["context"]
    assert rec["pnl_pct_of_margin"] != 0


def test_journal_roundtrip_and_analysis(tmp_path):
    from tradebot.journal import Journal, make_record
    from tradebot.analyze import load_records, build_report

    path = str(tmp_path / "journal.jsonl")
    j = Journal(path)
    for i in range(12):
        j.record(make_record(
            mode="paper", strategy="donchian", timeframe="1d", symbol="BTC/USDT",
            side="long" if i % 2 == 0 else "short", leverage=2.0, amount=0.1,
            entry_price=100.0, exit_price=110.0 if i % 3 else 95.0,
            pnl=1.0 if i % 3 else -0.5, margin=5.0,
            reason="take_profit" if i % 3 else "stop_loss",
            opened_at="2026-01-01T00:00:00+00:00",
            closed_at="2026-01-02T00:00:00+00:00",
            context={"adx": 25.0 + i, "atr": 3.0, "rsi": 55.0},
        ))

    df = load_records([path])
    assert len(df) == 12
    assert "ctx_adx" in df.columns
    report = build_report(df)
    assert "TRADE-ANALYS" in report
    assert "Per sida" in report
    assert "Per exit-orsak" in report
    assert "Per trendstyrka" in report


def test_analysis_empty_journal():
    from tradebot.analyze import build_report, load_records
    report = build_report(load_records(["/nonexistent/journal.jsonl"]))
    assert "tom" in report.lower()


def test_backtest_all_strategies_run():
    cfg = make_config(mode="futures", leverage=2.0)
    bt = Backtester(cfg)
    df = make_ohlcv(sawtooth(8))
    for name in ("ema_cross", "donchian", "rsi_meanrev"):
        res = bt.run_symbol(df, "TEST/USDT", get_strategy(name, cfg.strategy))
        assert res.end_equity > 0, name
