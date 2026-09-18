"""
Twelve Data real-time XAU/USD feed (works from India, free, no broker account).

Get a free API key at https://twelvedata.com (free tier: 8 calls/min, 800/day).
Set:  TWELVE_DATA_API_KEY=your_key

market_data.py caches per-timeframe to stay well within the free limits.
"""
from __future__ import annotations
import os
import requests
import pandas as pd

SYMBOL = "XAU/USD"
INTERVAL = {"5m": "5min", "15m": "15min", "1h": "1h", "1d": "1day"}
URL = "https://api.twelvedata.com/time_series"


def configured() -> bool:
    return bool(os.environ.get("TWELVE_DATA_API_KEY"))


def fetch_candles(tf: str, count: int = 300) -> pd.DataFrame:
    key = os.environ["TWELVE_DATA_API_KEY"]
    params = {"symbol": SYMBOL, "interval": INTERVAL[tf], "outputsize": min(count, 5000),
              "apikey": key, "format": "JSON", "timezone": "UTC"}
    r = requests.get(URL, params=params, timeout=20)
    r.raise_for_status()
    js = r.json()
    if js.get("status") != "ok" or "values" not in js:
        raise RuntimeError(f"TwelveData error: {js.get('message', js)}")
    rows = js["values"][::-1]   # API returns newest-first -> make oldest-first
    df = pd.DataFrame([{
        "time": v["datetime"], "open": float(v["open"]), "high": float(v["high"]),
        "low": float(v["low"]), "close": float(v["close"]),
        "volume": float(v.get("volume", 0) or 0),
    } for v in rows])
    df["time"] = pd.to_datetime(df["time"], utc=True)
    return df


if __name__ == "__main__":
    if not configured():
        print("TwelveData not configured (set TWELVE_DATA_API_KEY)."); raise SystemExit
    d = fetch_candles("15m", 5)
    print(f"TwelveData XAU/USD 15m: {len(d)} candles, last {d['close'].iloc[-1]} @ {d['time'].iloc[-1]}")
