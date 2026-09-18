"""
Telegram alerts for confirmed setups.

Set env vars to enable (see app/README.md):
  TELEGRAM_BOT_TOKEN = from @BotFather
  TELEGRAM_CHAT_ID   = your chat id (from @userinfobot)

A background checker polls the signal each minute; when a NEW confirmed setup appears
in a kill zone, it sends one alert (deduped per setup per day).
"""
from __future__ import annotations
import os
import sys
import time
import threading
import requests
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine"))
import live_signal  # noqa: E402
import market_data  # noqa: E402
from backtest_full import session_ist  # noqa: E402

KILL = {"London-kill", "NY-kill"}

_sent = set()


def configured() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def send(text: str) -> bool:
    if not configured():
        return False
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": text,
                                "parse_mode": "Markdown"}, timeout=15)
        return r.ok
    except Exception:
        return False


def _format(a: dict) -> str:
    s = a["live_setup"]
    return (f"🎯 *beta2alpha — CONFIRMED {s['dir'].upper()}*  ({a['session_ist']})\n"
            f"{a['instrument']} @ {a['price']}\n"
            f"Entry: `{s['entry']}`\nSL: `{s['stop_loss']}`\nTP: `{s['take_profit']}`\n"
            f"R:R {s['risk_reward']} · lot {s['lot_size']} · risk ${s['risk_usd']}\n"
            f"_Bias {a['bias']['overall']} · {a['data_source']}_")


def check_once() -> bool:
    """Check current signal; send alert if a new confirmed setup. Returns True if sent."""
    try:
        a = live_signal.get_analysis()
    except Exception:
        return False
    s = a.get("live_setup") or {}
    if s.get("status") != "CONFIRMED":
        return False
    import datetime as dt
    key = f"{dt.date.today()}|{s['dir']}|{s['entry']}"
    if key in _sent:
        return False
    if send(_format(a)):
        _sent.add(key)
        return True
    return False


def start_background(interval: int = 60):
    if not configured():
        print("[telegram] not configured — alerts disabled (set TELEGRAM_BOT_TOKEN/CHAT_ID)")
        return

    def loop():
        print("[telegram] alert checker started (active in kill zones, or anytime MT5 is live)")
        while True:
            try:
                sess = session_ist(pd.Timestamp.now(tz="UTC"))
                # Only consume data during kill zones (saves Twelve Data quota when MT5 is off);
                # if MT5 is live the data is free, so we can check anytime.
                if sess in KILL or market_data.mt5_online():
                    if check_once():
                        print("[telegram] alert sent")
            except Exception as e:
                print("[telegram] checker error:", e)
            time.sleep(interval)

    threading.Thread(target=loop, daemon=True).start()
