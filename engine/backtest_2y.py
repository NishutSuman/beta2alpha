"""
beta2alpha — 2-YEAR validation on Dukascopy 15m gold, WITH trading costs.

Same full-confluence engine as backtest_full.py, but:
  - data = 2y Dukascopy (47k 15m candles) + 2y Dukascopy 1H/Daily for bias
  - realistic costs: spread + commission subtracted per trade
  - per-year breakdown to check the edge holds across regimes (not one lucky window)
"""
from __future__ import annotations
import pandas as pd
from dukascopy_loader import load_all
from backtest_full import run, confirmed_swings, ema, _utc_naive

ACCOUNT, RISK_USD = 5000.0, 25.0
# XAU/USD economics + costs (conservative)
USD_PER_PRICE_PER_LOT = 100.0     # 1.00 lot, $1 move = $100
SPREAD_PRICE = 0.35               # round-trip spread in price ($)
COMMISSION_PER_LOT = 5.0          # round-turn commission per lot


def bias_map(df15, htf, fast, slow):
    bull = (ema(htf["close"], fast) > ema(htf["close"], slow)).shift(1)
    right = pd.DataFrame({"time": _utc_naive(htf["time"]), "bull": bull.values}).dropna().sort_values("time")
    left = pd.DataFrame({"time": _utc_naive(df15["time"])}).sort_values("time")
    m = pd.merge_asof(left, right, on="time", direction="backward")
    return m["bull"].fillna(False).astype(bool).values


def apply_costs(tr):
    if tr.empty:
        return tr
    tr = tr.copy()
    stop_dist = (tr["entry"] - tr["sl"]).abs()
    tr["lot"] = RISK_USD / (stop_dist * USD_PER_PRICE_PER_LOT)
    tr["cost"] = SPREAD_PRICE * USD_PER_PRICE_PER_LOT * tr["lot"] + COMMISSION_PER_LOT * tr["lot"]
    tr["gross"] = tr["R"] * RISK_USD
    tr["net"] = tr["gross"] - tr["cost"]
    return tr


def summary(label, tr, days, rr):
    if tr.empty:
        print(f"  {label:36s}|   0 trades"); return
    tr = apply_costs(tr)
    n = len(tr); w = int((tr["result"] == "win").sum()); wr = w / n
    gross, net, cost = tr["gross"].sum(), tr["net"].sum(), tr["cost"].sum()
    pf_net = tr.loc[tr.net > 0, "net"].sum() / -tr.loc[tr.net < 0, "net"].sum() if (tr.net < 0).any() else float("inf")
    eq = tr["net"].cumsum(); dd = (eq - eq.cummax()).min()
    print(f"  {label:36s}| {n:4d} tr | win {wr*100:4.1f}% | PF {pf_net:4.2f} | "
          f"gross ${gross:+6.0f} | cost ${cost:5.0f} | NET ${net:+6.0f} | DD ${dd:5.0f} | "
          f"{n/days*30:4.1f}/mo | ${net/days*30:+5.0f}/mo")


def per_year(label, tr):
    if tr.empty:
        return
    tr = apply_costs(tr); tr["yr"] = pd.to_datetime(tr["time"], utc=True).dt.year
    parts = []
    for y, g in tr.groupby("yr"):
        wr = (g.result == "win").mean() * 100
        parts.append(f"{y}: {len(g)}tr {wr:.0f}%win ${g.net.sum():+.0f}")
    print(f"     {label} by year -> " + " | ".join(parts))


if __name__ == "__main__":
    d = load_all(2.0)
    df, h1, d1 = d["15m"], d["1h"], d["1d"]
    days = (df["time"].iloc[-1] - df["time"].iloc[0]).days
    daily_bull = bias_map(df, d1, 10, 30)
    h1_bull = bias_map(df, h1, 50, 200)
    shs = [s for s in confirmed_swings(df, 3, 3) if s["kind"] == "high"]
    sls = [s for s in confirmed_swings(df, 3, 3) if s["kind"] == "low"]
    print(f"\n=== 2-YEAR validation | Dukascopy 15m gold | {len(df)} candles | {days} days | "
          f"kill zones only | costs ON ===\n")
    ladder = [
        ("1. base (kill+OB+discount)",       set()),
        ("2. +MTF bias (Daily&1H)",          {"mtf"}),
        ("3. +liquidity sweep (protected)",  {"mtf", "sweep"}),
        ("4. +MSS (FULL system)",            {"mtf", "sweep", "mss"}),
    ]
    for rr in (2.0, 3.0):
        print(f"--- fixed R:R 1:{rr:g} ---")
        for label, f in ladder:
            tr = run(df, f, rr=rr, daily_bull=daily_bull, h1_bull=h1_bull, sh=shs, sl=sls)
            summary(label, tr, days, rr)
        # robustness: per-year for the two strongest configs
        print()
        per_year("sweep", run(df, {"mtf", "sweep"}, rr=rr, daily_bull=daily_bull, h1_bull=h1_bull, sh=shs, sl=sls))
        per_year("FULL ", run(df, {"mtf", "sweep", "mss"}, rr=rr, daily_bull=daily_bull, h1_bull=h1_bull, sh=shs, sl=sls))
        print()
