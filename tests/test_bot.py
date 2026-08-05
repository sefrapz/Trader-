"""Tester för strategi, risk och backtest — körs helt offline med syntetisk data."""

import numpy as np
import pandas as pd
import pytest

from tradebot.backtest import Backtester
from tradebot.config import Config, BotConfig, ExchangeConfig, MarketConfig, RiskConfig, StrategyConfig
from tradebot.portfolio import Portfolio
from tradebot.risk import RiskManager
from tradebot.strategy import EmaRsiStrategy


def make_config() -> Config:
    return Config(
        exchange=ExchangeConfig(),
        market=MarketConfig(),
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


def test_buy_signal_on_uptrend_cross():
    # nedgång följt av lugn uppgång ger EMA-korsning uppåt utan överköpt RSI
    rng = np.random.default_rng(7)
    down = np.linspace(104, 100, 50)
    up = np.linspace(100, 104, 40)
    closes = np.concatenate([down, up]) + rng.normal(0, 0.15, 90)
    strat = EmaRsiStrategy(StrategyConfig())
    df = make_ohlcv(closes)

    actions = []
    for i in range(strat.min_candles(), len(df) + 1):
        actions.append(strat.evaluate(df.iloc[:i]).action)
    assert "buy" in actions

    # kontrollera stop/take på ett köp
    idx = actions.index("buy") + strat.min_candles()
    sig = strat.evaluate(df.iloc[:idx])
    assert sig.stop_loss < sig.price < sig.take_profit


def test_hold_with_too_little_data():
    strat = EmaRsiStrategy(StrategyConfig())
    sig = strat.evaluate(make_ohlcv([100, 101, 102]))
    assert sig.action == "hold"


def test_position_sizing_risks_configured_pct():
    risk = RiskManager(RiskConfig(start_equity=10000, risk_per_trade_pct=1.0))
    pf = Portfolio(equity=10000)
    amount = risk.position_size(pf, {}, price=100.0, stop_loss=95.0)
    # risk = 1% av 10000 = 100; stoppavstånd 5 => 20 enheter
    assert amount == pytest.approx(20.0)
    # förlust vid stop == riskbeloppet
    assert amount * (100.0 - 95.0) == pytest.approx(100.0)


def test_position_sizing_rejects_bad_stop():
    risk = RiskManager(RiskConfig())
    pf = Portfolio(equity=10000)
    assert risk.position_size(pf, {}, price=100.0, stop_loss=100.0) == 0.0


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
    pf.open_position("ETH/USDT", 1.0, 2000.0, 1900.0, 2200.0)
    pf.save(path)

    loaded = Portfolio.load(path, start_equity=0)
    assert loaded.equity == pf.equity
    assert "ETH/USDT" in loaded.positions
    pnl = loaded.close_position("ETH/USDT", 2100.0)
    assert pnl == pytest.approx(100.0)


def test_backtest_runs_and_trades():
    # sågtandsmönster som tvingar fram flera korsningar
    closes = []
    for _ in range(6):
        closes += list(np.linspace(100, 90, 30)) + list(np.linspace(90, 110, 30))
    cfg = make_config()
    bt = Backtester(cfg)
    res = bt.run_symbol(make_ohlcv(closes), "TEST/USDT")
    assert res.trades > 0
    assert res.end_equity > 0
    assert 0.0 <= res.max_drawdown_pct <= 100.0
