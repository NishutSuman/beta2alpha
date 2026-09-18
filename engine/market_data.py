"""
Unified market-data source for the live app, with per-timeframe caching.

Priority:  MetaTrader 5 live push (your broker)  >  Twelve Data (real-time fallback).
No delayed sources. Twelve Data usage kept lean so the free cap (8/min, 800/day) lasts
through a session when MT5 is closed (mainly for Telegram alerts while you're away).
"""
from __future__ import annotations
import time
import pandas as pd
import twelvedata
import oanda

OANDA_COUNT = {"5m": 600, "15m": 600, "1h": 800, "1d": 365}
TD_COUNT = {"5m": 600, "15m": 600, "1h": 800, "1d": 365}   # leaner calls for the free-tier fallback
# cache seconds per timeframe. 15m kept short for responsiveness; higher TFs change
# slowly so they're cached long (this is what keeps us under Twelve Data's free cap).
# TTL only governs Twelve-Data fallback calls (MT5 pushes bypass the cache). Kept high so a
# session on the free tier stays well under 800/day: ~90s × (5m+15m) ≈ 80 calls/hr.
TTL = {"5m": 90, "15m": 90, "1h": 900, "1d": 3600}

_cache = {}      # tf -> (fetched_at, df)
_src = "starting…"   # actual source last used (reflects fallback)
_mt5 = {}        # tf -> (received_at, df)   pushed live from MetaTrader 5
MT5_FRESH = 360  # seconds: MT5 data considered live if pushed within this window
                 # (wider window smooths over occasional slow 5m pushes)


def push_mt5(tf: str, candles: list) -> int:
    """Receive live candles pushed from the MT5 feed script (your exact broker data)."""
    df = pd.DataFrame(candles)
    if df.empty:
        return 0
    df["time"] = pd.to_datetime(df["time"].astype("int64"), unit="s", utc=True)
    for col in ("open", "high", "low", "close"):
        df[col] = df[col].astype(float)
    if "volume" not in df:
        df["volume"] = 0.0
    df = df.drop_duplicates("time").sort_values("time").reset_index(drop=True)
    _mt5[tf] = (time.time(), _clean(df, tf))
    return len(_mt5[tf][1])


def mt5_fresh(tf: str) -> bool:
    return tf in _mt5 and (time.time() - _mt5[tf][0]) < MT5_FRESH


def mt5_online() -> bool:
    """MT5 is connected if ANY timeframe was pushed recently."""
    now = time.time()
    return any((now - ts) < MT5_FRESH for ts, _ in _mt5.values())


def is_live() -> bool:
    return ("real-time" in _src) or ("MetaTrader" in _src)


def source_label() -> str:
    return _src


def _in_market(ts):
    """Gold trades ~Sun 22:00 UTC -> Fri 21:00 UTC. Drop weekend candles (the feed fills
    them with flat near-zero-range bars that junk up the chart + structure)."""
    wd, h = ts.weekday(), ts.hour     # Mon=0 .. Sun=6 ; ts is UTC
    if wd == 5:                       # Saturday: closed all day
        return False
    if wd == 6 and h < 22:           # Sunday before 22:00 UTC open
        return False
    if wd == 4 and h >= 21:          # Friday after 21:00 UTC close
        return False
    return True


def _clean(df, tf):
    df = df[df["high"] > df["low"]]                       # drop exact-flat bars
    if tf != "1d":                                        # weekend filter = intraday only
        df = df[df["time"].apply(_in_market)]
    return df.reset_index(drop=True)


def _fetch_raw(tf: str):
    """Real-time fallback when MT5 is offline: Twelve Data (or OANDA). NO delayed sources."""
    global _src
    if twelvedata.configured():
        df = twelvedata.fetch_candles(tf, TD_COUNT.get(tf, 300))
        _src = "Twelve Data · real-time"
        return _clean(df, tf)
    if oanda.configured():
        df = oanda.fetch_candles(tf, OANDA_COUNT.get(tf, 300))
        _src = "OANDA · real-time"
        return _clean(df, tf)
    raise RuntimeError("no real-time data source available (open MT5 or set TWELVE_DATA_API_KEY)")


def fetch(tf: str):
    global _src
    # MT5 live push takes priority — exact broker feed, deep history.
    # If MT5 is CONNECTED at all, serve every timeframe from it (even if one tf's push
    # lagged) so the analysis is never a mix of MT5 + Twelve Data.
    if mt5_fresh(tf) or (mt5_online() and tf in _mt5):
        _src = "MetaTrader 5 · live (your broker)"
        return _mt5[tf][1]
    now = time.time()
    hit = _cache.get(tf)
    if hit and (now - hit[0]) < TTL.get(tf, 60):
        return hit[1]
    try:
        df = _fetch_raw(tf)
        _cache[tf] = (now, df)
        return df
    except Exception:
        if hit:
            return hit[1]                 # transient blip -> last good Twelve Data
        if tf in _mt5:
            _src = "MetaTrader 5 · last known"
            return _mt5[tf][1]            # last resort: stale MT5 rather than nothing
        raise
