"""Trade-journal: en rad JSON per avslutad trade, med marknadskontext.

Journalen är botens läro-minne. Varje stängd trade sparas med den
indikatorkontext som rådde vid entry, så att analyze-kommandot kan svara
på frågor som "förlorar vi mest i hög eller låg volatilitet?".
"""

import json
import os


class Journal:
    def __init__(self, path: str):
        self.path = path

    def record(self, rec: dict) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def write_all(self, records: list) -> None:
        """Skriver om hela filen (används av backtest som gör en hel körning)."""
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    @staticmethod
    def load(paths) -> list:
        records = []
        for path in paths:
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        return records


def make_record(*, mode: str, strategy: str, timeframe: str, symbol: str,
                side: str, leverage: float, amount: float, entry_price: float,
                exit_price: float, pnl: float, margin: float, reason: str,
                opened_at: str, closed_at: str, context: dict) -> dict:
    return {
        "mode": mode,                      # backtest / paper / live
        "strategy": strategy,
        "timeframe": timeframe,
        "symbol": symbol,
        "side": side,
        "leverage": leverage,
        "amount": amount,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "pnl": pnl,
        "pnl_pct_of_margin": (pnl / margin * 100.0) if margin > 0 else 0.0,
        "reason": reason,
        "opened_at": opened_at,
        "closed_at": closed_at,
        "context": context or {},          # indikatorvärden vid entry
    }
