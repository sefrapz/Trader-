"""Analys av trade-journalen: var tjänar och förlorar vi pengar?

Bryter ner resultatet per strategi, symbol, sida, exit-orsak och
marknadsregim (ADX, volatilitet, RSI). Grupper med litet urval markeras —
dra inga slutsatser av dem.
"""

import pandas as pd

from .journal import Journal

MIN_SAMPLE = 10  # under detta antal trades markeras gruppen som osäker


def load_records(paths) -> pd.DataFrame:
    records = Journal.load(paths)
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    # platta ut kontexten till egna kolumner (ctx_adx, ctx_rsi, ...)
    ctx = pd.json_normalize(df.get("context", pd.Series([{}] * len(df)))).add_prefix("ctx_")
    df = pd.concat([df.drop(columns=["context"], errors="ignore"), ctx], axis=1)

    if "ctx_atr" in df.columns:
        df["atr_pct"] = df["ctx_atr"] / df["entry_price"] * 100.0
    for col in ("opened_at", "closed_at"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True, format="mixed")
    if "opened_at" in df.columns and "closed_at" in df.columns:
        df["holding_hours"] = (df["closed_at"] - df["opened_at"]).dt.total_seconds() / 3600.0
        df["weekday"] = df["opened_at"].dt.day_name()
    return df


def _stats(group: pd.DataFrame) -> dict:
    n = len(group)
    wins = (group["pnl"] > 0).sum()
    gross_win = group.loc[group["pnl"] > 0, "pnl"].sum()
    gross_loss = -group.loc[group["pnl"] <= 0, "pnl"].sum()
    return {
        "n": n,
        "winrate": wins / n * 100.0 if n else 0.0,
        "pnl": group["pnl"].sum(),
        "avg": group["pnl"].mean() if n else 0.0,
        "profit_factor": gross_win / gross_loss if gross_loss > 0 else float("inf"),
    }


def _fmt_row(label: str, s: dict) -> str:
    pf = "inf" if s["profit_factor"] == float("inf") else f"{s['profit_factor']:.2f}"
    note = "  (litet urval!)" if s["n"] < MIN_SAMPLE else ""
    return (f"  {label:<22} {s['n']:>4} trades | vinst {s['winrate']:>4.0f}% | "
            f"PnL {s['pnl']:>+10.2f} | snitt {s['avg']:>+8.2f} | PF {pf}{note}")


def _section(df: pd.DataFrame, col: str, title: str, order=None) -> str:
    if col not in df.columns or df[col].dropna().empty:
        return ""
    lines = [f"\n{title}"]
    groups = df.groupby(col, dropna=True, observed=True)
    keys = order if order else sorted(groups.groups, key=lambda k: -_stats(groups.get_group(k))["pnl"])
    for key in keys:
        if key not in groups.groups:
            continue
        lines.append(_fmt_row(str(key), _stats(groups.get_group(key))))
    return "\n".join(lines)


def _bucketize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "ctx_adx" in out.columns:
        out["adx_läge"] = pd.cut(
            out["ctx_adx"], bins=[0, 20, 30, 100],
            labels=["svag trend (<20)", "måttlig trend (20-30)", "stark trend (>30)"],
        )
    if "atr_pct" in out.columns:
        out["volatilitet"] = pd.cut(
            out["atr_pct"], bins=[0, 2, 4, 100],
            labels=["låg vol (<2%)", "mellan vol (2-4%)", "hög vol (>4%)"],
        )
    if "ctx_rsi" in out.columns:
        out["rsi_läge"] = pd.cut(
            out["ctx_rsi"], bins=[0, 30, 70, 100],
            labels=["översåld (<30)", "neutral (30-70)", "överköpt (>70)"],
        )
    return out


def build_report(df: pd.DataFrame) -> str:
    if df.empty:
        return ("Journalen är tom. Kör ett backtest eller låt paper-läget rulla "
                "så fylls den på.")

    df = _bucketize(df)
    total = _stats(df)
    lines = [
        "=" * 78,
        "TRADE-ANALYS",
        "=" * 78,
        _fmt_row("TOTALT", total),
    ]
    if "holding_hours" in df.columns and df["holding_hours"].notna().any():
        lines.append(f"  snitt-innehavstid: {df['holding_hours'].mean():.1f} h")

    lines.append(_section(df, "mode", "Per läge (backtest/paper/live):"))
    lines.append(_section(df, "strategy", "Per strategi:"))
    lines.append(_section(df, "symbol", "Per symbol:"))
    lines.append(_section(df, "side", "Per sida (long/short):"))
    lines.append(_section(df, "reason", "Per exit-orsak:"))
    lines.append(_section(df, "adx_läge", "Per trendstyrka vid entry (ADX):",
                          order=["svag trend (<20)", "måttlig trend (20-30)", "stark trend (>30)"]))
    lines.append(_section(df, "volatilitet", "Per volatilitet vid entry (ATR % av pris):",
                          order=["låg vol (<2%)", "mellan vol (2-4%)", "hög vol (>4%)"]))
    lines.append(_section(df, "rsi_läge", "Per RSI-läge vid entry:",
                          order=["översåld (<30)", "neutral (30-70)", "överköpt (>70)"]))
    lines.append(_section(df, "weekday", "Per veckodag (entry):"))

    # automatiska observationer: bästa/sämsta grupp med tillräckligt urval
    lines.append("\nObservationer (endast grupper med >= "
                 f"{MIN_SAMPLE} trades):")
    findings = []
    for col in ("side", "reason", "adx_läge", "volatilitet", "rsi_läge", "symbol"):
        if col not in df.columns:
            continue
        for key, group in df.groupby(col, dropna=True, observed=True):
            s = _stats(group)
            if s["n"] >= MIN_SAMPLE:
                findings.append((s["pnl"], f"{col}={key}", s))
    if findings:
        findings.sort()
        worst, best = findings[0], findings[-1]
        lines.append(f"  Starkast:  {best[1]} ({best[2]['n']} trades, "
                     f"PnL {best[2]['pnl']:+.2f}, vinst {best[2]['winrate']:.0f}%)")
        lines.append(f"  Svagast:   {worst[1]} ({worst[2]['n']} trades, "
                     f"PnL {worst[2]['pnl']:+.2f}, vinst {worst[2]['winrate']:.0f}%)")
        lines.append("  OBS: mönster är hypoteser — verifiera med A/B-backtest "
                     "innan de blir regler.")
    else:
        lines.append("  För få trades ännu för säkra mönster — låt datan växa.")

    lines.append("=" * 78)
    return "\n".join(line for line in lines if line)


def run_analysis(paths, save_to: str = None) -> str:
    report = build_report(load_records(paths))
    if save_to:
        import os
        os.makedirs(os.path.dirname(save_to) or ".", exist_ok=True)
        with open(save_to, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
    return report
