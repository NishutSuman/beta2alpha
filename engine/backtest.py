"""
beta2alpha — Phase-1 SMOKE backtest of the ICT/SMC method on real gold.

HONEST SCOPE:
  - Data: yfinance 15m gold (GC=F), ~last 60 days only (free-tier limit). Small sample.
  - Codes the OBJECTIVE core of the spec causally (no look-ahead):
      bias = EMA50 vs EMA200 trend state (proxy for HTF direction)
      setup = price pulls back into a VALID order block (last opposite candle before a
              displacement), on the correct side of equilibrium (discount=long/premium=short),
              still valid by the 0.5 mean-threshold body-close rule AT ENTRY TIME.
      entry = at OB edge, SL beyond OB, TP at fixed R multiple.
  - The discretionary parts of the method ("which POI is THE one", fake-structure) are
    approximated mechanically, so this is a FLOOR on quality, not the final word.
  - No look-ahead: every entry decision uses only candles up to that moment; only the
    trade OUTCOME looks forward (as it must).

Risk model: 0.5% ($25) risk per trade on a $5,000 account; one position at a time.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from data import fetch
from structures import displacement

ACCOUNT = 5000.0
RISK_PCT = 0.005                 # 0.5% per trade
RISK_USD = ACCOUNT * RISK_PCT    # $25
IST = "Asia/Kolkata"


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def session_ist(ts) -> str:
    t = ts.tz_convert(IST) if ts.tzinfo else ts.tz_localize("UTC").tz_convert(IST)
    h = t.hour + t.minute / 60
    if 12.5 <= h < 15.5:   return "London-kill"
    if 17.5 <= h < 20.5:   return "NY-kill"
    if 5.5 <= h < 12.5:    return "Asian"
    return "off-hours"


def build_obs(df):
    """Causal order blocks: (ob_idx, confirm_idx, dir, top, bottom, mt).
    Known/actionable only AFTER confirm_idx (the displacement candle)."""
    obs = []
    for d in displacement(df, lookback=20, mult=1.5):
        i = d["idx"]
        want_bull = d["dir"] == "up"
        ob_idx = None
        for j in range(i - 1, max(i - 6, 0), -1):
            is_down = df["close"].iloc[j] < df["open"].iloc[j]
            if want_bull and is_down: ob_idx = j; break
            if not want_bull and not is_down: ob_idx = j; break
        if ob_idx is None:
            continue
        top, bottom = float(df["high"].iloc[ob_idx]), float(df["low"].iloc[ob_idx])
        obs.append({"ob_idx": ob_idx, "confirm_idx": i, "dir": "bull" if want_bull else "bear",
                    "top": top, "bottom": bottom, "mt": (top + bottom) / 2, "tapped": False})
    return obs


def run(df, rr=2.0, buffer_frac=0.0005, allowed_sessions=None):
    c, h, l, o = df["close"], df["high"], df["low"], df["open"]
    ema50, ema200 = ema(c, 50), ema(c, 200)
    rng_hi = h.rolling(50).max(); rng_lo = l.rolling(50).min()
    obs = build_obs(df)
    trades = []
    in_trade = None
    warm = 200

    for i in range(warm, len(df)):
        # ---- manage open trade (outcome may look forward; that's legitimate) ----
        if in_trade:
            t = in_trade
            hit_sl = l.iloc[i] <= t["sl"] if t["side"] == "long" else h.iloc[i] >= t["sl"]
            hit_tp = h.iloc[i] >= t["tp"] if t["side"] == "long" else l.iloc[i] <= t["tp"]
            if hit_sl and hit_tp:        # ambiguous candle -> assume SL first (conservative)
                t["result"] = "loss"; t["R"] = -1.0
            elif hit_sl:
                t["result"] = "loss"; t["R"] = -1.0
            elif hit_tp:
                t["result"] = "win";  t["R"] = rr
            if t.get("result"):
                t["exit_idx"] = i; t["exit_time"] = df["time"].iloc[i]
                trades.append(t); in_trade = None
            else:
                continue   # stay in trade, don't look for new entries

        # ---- bias (causal trend state) ----
        bull = ema50.iloc[i] > ema200.iloc[i]
        bear = ema50.iloc[i] < ema200.iloc[i]
        mid = (rng_hi.iloc[i] + rng_lo.iloc[i]) / 2   # equilibrium of recent range

        # ---- look for an OB tap to enter ----
        for ob in obs:
            if ob["tapped"] or ob["confirm_idx"] >= i:
                continue
            zone_touched = (l.iloc[i] <= ob["top"]) and (h.iloc[i] >= ob["bottom"])
            if not zone_touched:
                continue
            ob["tapped"] = True   # retire on first touch regardless
            if allowed_sessions and session_ist(df["time"].iloc[i]) not in allowed_sessions:
                continue
            # causal validity: no body close beyond MT between confirm and now
            seg = df.iloc[ob["confirm_idx"] + 1:i]
            if ob["dir"] == "bull" and (seg["close"] < ob["mt"]).any(): continue
            if ob["dir"] == "bear" and (seg["close"] > ob["mt"]).any(): continue
            # pillar alignment: bias + equilibrium side
            if ob["dir"] == "bull" and bull and ob["top"] < mid:
                entry = ob["top"]; sl = ob["bottom"] * (1 - buffer_frac)
                risk = entry - sl
                if risk <= 0: continue
                in_trade = {"side": "long", "entry_idx": i, "entry_time": df["time"].iloc[i],
                            "entry": entry, "sl": sl, "tp": entry + rr * risk,
                            "session": session_ist(df["time"].iloc[i])}
                break
            if ob["dir"] == "bear" and bear and ob["bottom"] > mid:
                entry = ob["bottom"]; sl = ob["top"] * (1 + buffer_frac)
                risk = sl - entry
                if risk <= 0: continue
                in_trade = {"side": "short", "entry_idx": i, "entry_time": df["time"].iloc[i],
                            "entry": entry, "sl": sl, "tp": entry - rr * risk,
                            "session": session_ist(df["time"].iloc[i])}
                break
    return pd.DataFrame(trades)


def stats(tr, rr, days):
    if tr.empty:
        print(f"  RR 1:{rr:g} -> NO TRADES"); return
    n = len(tr); wins = (tr["result"] == "win").sum(); losses = n - wins
    wr = wins / n
    total_R = tr["R"].sum(); exp_R = tr["R"].mean()
    pnl = total_R * RISK_USD
    gross_win = wins * rr * RISK_USD; gross_loss = losses * RISK_USD
    pf = gross_win / gross_loss if gross_loss else float("inf")
    # equity curve / max drawdown in $
    eq = (tr["R"] * RISK_USD).cumsum(); peak = eq.cummax(); dd = (eq - peak).min()
    print(f"  RR 1:{rr:g} | trades {n} | win {wins}/{losses} = {wr*100:.1f}% | "
          f"expectancy {exp_R:+.3f}R (${exp_R*RISK_USD:+.2f}/trade) | PF {pf:.2f}")
    print(f"          | net {total_R:+.1f}R = ${pnl:+.0f} on $5k | maxDD ${dd:.0f} | "
          f"~{n/days:.2f} trades/day | ${pnl/days:+.2f}/day avg")
    # failure breakdown by session
    by = tr.groupby("session")["result"].agg(["count", lambda s: (s == "win").mean()])
    by.columns = ["trades", "winrate"]
    for sess, row in by.iterrows():
        print(f"            - {sess:12s}: {int(row.trades):3d} trades, {row.winrate*100:.0f}% win")


if __name__ == "__main__":
    df = fetch(interval="15m", period="60d")
    span_days = (df["time"].iloc[-1] - df["time"].iloc[0]).days or 1
    print(f"=== beta2alpha SMOKE backtest ===")
    print(f"Gold 15m | {len(df)} candles | {df['time'].iloc[0].date()} -> {df['time'].iloc[-1].date()} "
          f"({span_days} days) | risk ${RISK_USD:.0f}/trade (0.5% of $5k)\n")
    print("--- ALL HOURS ---")
    for rr in (1.5, 2.0, 3.0):
        stats(run(df, rr=rr), rr, span_days); print()

    print("--- KILL ZONES ONLY (London-kill + NY-kill) ---")
    for rr in (1.5, 2.0, 3.0):
        stats(run(df, rr=rr, allowed_sessions={"London-kill", "NY-kill"}), rr, span_days); print()

    print("--- NY KILL ZONE ONLY ---")
    for rr in (1.5, 2.0, 3.0):
        stats(run(df, rr=rr, allowed_sessions={"NY-kill"}), rr, span_days); print()
