"""
OANDA v20 real-time data layer (practice account) for beta2alpha.

Set these env vars to go live (see app/README.md for how to get them):
  OANDA_API_TOKEN   = your practice API token
  OANDA_ACCOUNT_ID  = your practice account id (optional for candles)
  OANDA_ENV         = practice (default) | live

Falls back silently (configured() == False) when no token is set, so the app still
runs on delayed data until you paste your token.
"""
from __future__ import annotations
import os
import requests
import pandas as pd

INSTRUMENT = "XAU_USD"
GRAN = {"5m": "M5", "15m": "M15", "1h": "H1", "1d": "D"}


def _base():
    env = os.environ.get("OANDA_ENV", "practice")
    return ("https://api-fxtrade.oanda.com" if env == "live"
            else "https://api-fxpractice.oanda.com")


def configured() -> bool:
    return bool(os.environ.get("OANDA_API_TOKEN"))


def fetch_candles(tf: str, count: int = 300) -> pd.DataFrame:
    """Real-time OHLC candles from OANDA -> canonical df (time UTC, ohlc, volume).
    Includes the still-forming last candle so 'price' is current."""
    token = os.environ["OANDA_API_TOKEN"]
    url = f"{_base()}/v3/instruments/{INSTRUMENT}/candles"
    params = {"granularity": GRAN[tf], "count": count, "price": "M"}
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    r.raise_for_status()
    rows = []
    for c in r.json()["candles"]:
        m = c["mid"]
        rows.append({"time": c["time"], "open": float(m["o"]), "high": float(m["h"]),
                     "low": float(m["l"]), "close": float(m["c"]),
                     "volume": float(c.get("volume", 0)), "complete": c.get("complete", True)})
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    return df


if __name__ == "__main__":
    if not configured():
        print("OANDA not configured (set OANDA_API_TOKEN)."); raise SystemExit
    d = fetch_candles("15m", 5)
    print(f"OANDA live XAU_USD 15m: {len(d)} candles, last close {d['close'].iloc[-1]} "
          f"@ {d['time'].iloc[-1]} (complete={d['complete'].iloc[-1]})")
