"""
Data layer for beta2alpha trading engine.

Phase 1: free gold (XAU/USD) candles via yfinance to validate the engine.
  - GC=F  (COMEX gold futures) — best free intraday coverage, ~spot proxy
  - XAUUSD=X (spot) — daily only on yfinance
Phase 2 will add Dukascopy (deep historical intraday for backtest) and OANDA (live feed).

Canonical candle dataframe: columns [time, open, high, low, close, volume],
index 0..n-1, oldest first. Everything downstream consumes this shape.

yfinance intraday history limits (free): 1m≈7d, 5m/15m/30m≈60d, 1h≈730d, 1d≈full.
"""
from __future__ import annotations
import pandas as pd
import yfinance as yf

GOLD_FUTURES = "GC=F"
GOLD_SPOT = "XAUUSD=X"


def fetch(symbol: str = GOLD_FUTURES, interval: str = "1d", period: str = "6mo") -> pd.DataFrame:
    """Fetch OHLC candles via yfinance, normalized to the canonical shape.

    interval: 1m,5m,15m,30m,1h,1d,1wk,1mo   period: e.g. 7d,60d,6mo,2y,max
    """
    raw = yf.download(symbol, interval=interval, period=period,
                      progress=False, auto_adjust=False)
    if raw is None or raw.empty:
        raise RuntimeError(f"yfinance returned no data for {symbol} {interval}/{period}")
    # yfinance may return MultiIndex columns (Price, Ticker) for a single ticker
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw = raw.reset_index()
    raw.columns = [str(c).lower() for c in raw.columns]
    raw = raw.rename(columns={"date": "time", "datetime": "time", "index": "time"})
    cols = [c for c in ["time", "open", "high", "low", "close", "volume"] if c in raw.columns]
    df = raw[cols].copy()
    df["time"] = pd.to_datetime(df["time"])
    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
    return df


# Multi-timeframe pull used by the fractal engine
MTF = {
    "1d": "2y",
    "1h": "180d",
    "15m": "30d",
    "5m": "20d",
}


def fetch_mtf(symbol: str = GOLD_FUTURES) -> dict[str, pd.DataFrame]:
    """Fetch the standard fractal timeframe set (Daily, 1H, 15m, 5m)."""
    return {tf: fetch(symbol, interval=tf, period=per) for tf, per in MTF.items()}


if __name__ == "__main__":
    for tf in ["1d", "1h", "15m", "5m"]:
        per = MTF.get(tf, "60d")
        df = fetch(GOLD_FUTURES, interval=tf, period=per)
        print(f"{tf:>4} | {len(df):>5} candles | {df['time'].iloc[0]} -> {df['time'].iloc[-1]}")
