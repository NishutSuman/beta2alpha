"""
Dukascopy historical loader for beta2alpha — deep, free XAU/USD history.

Fetches via dukascopy-python and caches to data/*.csv (canonical candle shape:
time, open, high, low, close, volume — UTC, oldest first). Re-runs read the cache.
"""
from __future__ import annotations
import os
import datetime as dt
import pandas as pd
import dukascopy_python as dk
from dukascopy_python import (
    INTERVAL_MIN_5, INTERVAL_MIN_15, INTERVAL_HOUR_1, INTERVAL_DAY_1, OFFER_SIDE_BID,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INSTR = "XAU/USD"
INTERVALS = {"5m": INTERVAL_MIN_5, "15m": INTERVAL_MIN_15,
             "1h": INTERVAL_HOUR_1, "1d": INTERVAL_DAY_1}


def _cache_path(tf, start, end):
    return os.path.join(DATA_DIR, f"xauusd_{tf}_{start:%Y%m%d}_{end:%Y%m%d}.csv")


def load(tf: str, start: dt.datetime, end: dt.datetime, refresh: bool = False) -> pd.DataFrame:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = _cache_path(tf, start, end)
    if os.path.exists(path) and not refresh:
        df = pd.read_csv(path, parse_dates=["time"])
        return df
    raw = dk.fetch(INSTR, INTERVALS[tf], OFFER_SIDE_BID, start, end)
    df = raw.reset_index().rename(columns={"timestamp": "time"})
    df.columns = [str(c).lower() for c in df.columns]
    df = df[["time", "open", "high", "low", "close", "volume"]].copy()
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
    df.to_csv(path, index=False)
    return df


def load_all(years: float = 2.0, end: dt.datetime | None = None) -> dict[str, pd.DataFrame]:
    end = end or dt.datetime(2026, 6, 21)
    start = end - dt.timedelta(days=int(365 * years))
    out = {}
    for tf in ("1d", "1h", "15m"):
        print(f"  fetching {tf} {start:%Y-%m-%d} -> {end:%Y-%m-%d} ...", flush=True)
        df = load(tf, start, end)
        out[tf] = df
        print(f"    {tf}: {len(df)} candles | {df['time'].iloc[0]} -> {df['time'].iloc[-1]}", flush=True)
    return out


if __name__ == "__main__":
    load_all(2.0)
