"""
beta2alpha — SYSTEMATIC STRATEGY SWEEP with out-of-sample validation.

Tests every combination of {timeframe x session x setup x filters x target} over 2y
Dukascopy gold, WITH costs, and splits each into IN-SAMPLE (first 65%) vs
OUT-OF-SAMPLE (last 35%). The ONLY configs we trust are those profitable in BOTH
segments with enough trades. Everything saved to data/sweep_results.csv.

This is the honest way to do a big search: brute force finds fake winners; the
out-of-sample gate is what separates a real edge from curve-fit luck.
"""
from __future__ import annotations
import os, datetime as dt
import numpy as np
import pandas as pd
from dukascopy_loader import load, load_all
from backtest_full import ema, _utc_naive, confirmed_swings, session_ist
from structures import displacement

RISK_USD = 25.0
USD_PER_PRICE_PER_LOT, SPREAD_PRICE, COMM = 100.0, 0.35, 5.0
MAX_HOLD = 150
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "sweep_results.csv")

SESSIONS = {
    "all": None,
    "asian": {"Asian"},
    "london": {"London-kill"},
    "ny": {"NY-kill"},
    "london+ny": {"London-kill", "NY-kill"},
}


# ----------------------------------------------------------------- feature precompute
def recent_price(df, swings_list, n):
    """array: price of most recent CONFIRMED swing (of given list) as of each candle."""
    arr = np.full(n, np.nan)
    sw = sorted(swings_list, key=lambda s: s["confirm"])
    p = 0
    for i in range(n):
        while p < len(sw) and sw[p]["confirm"] <= i:
            arr[i] = sw[p]["price"]; p += 1
        if i > 0 and np.isnan(arr[i]):
            arr[i] = arr[i - 1]
    return arr


def precompute(df, htf_list):
    n = len(df)
    c, h, l, o = df["close"].values, df["high"].values, df["low"].values, df["open"].values
    e50 = ema(df["close"], 50).values; e200 = ema(df["close"], 200).values
    rhi = pd.Series(h).rolling(50).max().values; rlo = pd.Series(l).rolling(50).min().values
    mid = (rhi + rlo) / 2
    sw = confirmed_swings(df, 3, 3)
    shs = [s for s in sw if s["kind"] == "high"]; sls = [s for s in sw if s["kind"] == "low"]
    rshi = recent_price(df, shs, n); rslo = recent_price(df, sls, n)
    # sweeps (pierce + reclaim) and MSS (body close beyond swing)
    sweepL = (l < rslo) & (c > rslo)        # sell-side grab -> long bias
    sweepS = (h > rshi) & (c < rshi)        # buy-side grab -> short bias
    mssL = c > rshi; mssS = c < rslo
    def win_any(b):  # True if any True in [i-8, i]
        s = pd.Series(b.astype(float)); return (s.rolling(9, min_periods=1).max() > 0).values
    feats = {
        "c": c, "h": h, "l": l, "o": o, "e50": e50, "e200": e200, "mid": mid,
        "swepL": win_any(sweepL), "swepS": win_any(sweepS),
        "mssL": win_any(mssL), "mssS": win_any(mssS),
        "sweepLpx": np.where(sweepL, l, np.nan), "sweepSpx": np.where(sweepS, h, np.nan),
        "sess": [session_ist(t) for t in df["time"]],
        "sh_px": sorted(s["price"] for s in shs), "sl_px": sorted(s["price"] for s in sls),
        "mtfL": np.all(htf_list, axis=0) if htf_list else np.ones(n, bool),
        "mtfS": np.all([~b for b in htf_list], axis=0) if htf_list else np.ones(n, bool),
        "time": df["time"].values,
    }
    return feats, shs, sls


# --------------------------------------------------------------------- event builders
def ev_ob(df):
    obs, n = [], len(df)
    c, o, h, l = df["close"].values, df["open"].values, df["high"].values, df["low"].values
    for d in displacement(df, 20, 1.5):
        i = d["idx"]; bull = d["dir"] == "up"; ob = None
        for j in range(i - 1, max(i - 6, 0), -1):
            down = c[j] < o[j]
            if bull and down: ob = j; break
            if not bull and not down: ob = j; break
        if ob is None: continue
        top, bot = float(h[ob]), float(l[ob])
        side = "long" if bull else "short"
        for k in range(i + 1, min(i + 300, n)):          # first tap
            if l[k] <= top and h[k] >= bot:
                obs.append({"idx": k, "side": side,
                            "entry": top if bull else bot, "stop": bot if bull else top}); break
    return obs


def ev_fvg(df):
    out, n = [], len(df)
    h, l = df["high"].values, df["low"].values
    for i in range(1, n - 1):
        if l[i + 1] > h[i - 1]:                            # bullish gap
            top, bot, side = float(l[i + 1]), float(h[i - 1]), "long"
        elif h[i + 1] < l[i - 1]:                          # bearish gap
            top, bot, side = float(l[i - 1]), float(h[i + 1]), "short"
        else:
            continue
        for k in range(i + 2, min(i + 200, n)):            # first return into gap
            if l[k] <= top and h[k] >= bot:
                out.append({"idx": k, "side": side,
                            "entry": top if side == "long" else bot,
                            "stop": bot if side == "long" else top}); break
    return out


def ev_sweep(df, shs, sls):
    out, n = [], len(df)
    c, h, l = df["close"].values, df["high"].values, df["low"].values
    rslo = recent_price(df, sls, n); rshi = recent_price(df, shs, n)
    for j in range(n):
        if not np.isnan(rslo[j]) and l[j] < rslo[j] and c[j] > rslo[j]:
            out.append({"idx": j, "side": "long", "entry": float(c[j]), "stop": float(l[j])})
        elif not np.isnan(rshi[j]) and h[j] > rshi[j] and c[j] < rshi[j]:
            out.append({"idx": j, "side": "short", "entry": float(c[j]), "stop": float(h[j])})
    return out


# --------------------------------------------------------------------------- backtest
def struct_tp(levels, entry, risk, side, min_rr=1.5, max_rr=12):
    if side == "long":
        for p in sorted(x for x in levels if x > entry):
            rr = (p - entry) / risk
            if rr >= min_rr: return min(p, entry + max_rr * risk)
    else:
        for p in sorted((x for x in levels if x < entry), reverse=True):
            rr = (entry - p) / risk
            if rr >= min_rr: return max(p, entry - max_rr * risk)
    return None


def simulate(df, feats, events, flt, target,
             spread=SPREAD_PRICE, comm=COMM, slip=0.0, min_risk=0.0, max_lot=None,
             confirm=False):
    h, l, c, o = feats["h"], feats["l"], feats["c"], feats["o"]
    n = len(df); last_exit = -1; trades = []
    for ev in events:
        i = ev["idx"]
        if i <= last_exit or i >= n - 2:
            continue
        side = ev["side"]
        if flt["sess"] and feats["sess"][i] not in flt["sess"]: continue
        if flt.get("bias") and not (feats["mtfL"][i] if side == "long" else feats["mtfS"][i]): continue
        if flt.get("pd"):
            if side == "long" and not (ev["entry"] < feats["mid"][i]): continue
            if side == "short" and not (ev["entry"] > feats["mid"][i]): continue
        if flt.get("sweep") and not (feats["swepL"][i] if side == "long" else feats["swepS"][i]): continue
        if flt.get("mss") and not (feats["mssL"][i] if side == "long" else feats["mssS"][i]): continue
        entry_idx = i
        if confirm:
            ci = i + 1
            if ci >= n - 1: continue
            # require the market to REACT: candle after tap closes back in our direction
            if side == "long" and not (c[ci] > o[ci]): continue
            if side == "short" and not (c[ci] < o[ci]): continue
            entry = float(c[ci]); entry_idx = ci
        else:
            entry = ev["entry"]
        stop = ev["stop"]
        # extend stop beyond the sweep wick if sweep filter active (protected)
        if flt.get("sweep"):
            spx = feats["sweepLpx"][i] if side == "long" else feats["sweepSpx"][i]
            if not np.isnan(spx):
                stop = min(stop, spx) if side == "long" else max(stop, spx)
        stop = stop * (1 - 0.0005) if side == "long" else stop * (1 + 0.0005)
        risk = entry - stop if side == "long" else stop - entry
        if risk <= 0 or risk < min_risk: continue          # reject unrealistically tight stops
        if target == "fix2":
            tp = entry + 2 * risk if side == "long" else entry - 2 * risk
        else:
            tp = struct_tp(feats["sh_px"] if side == "long" else feats["sl_px"], entry, risk, side)
            if tp is None: continue
        rr = (tp - entry) / risk if side == "long" else (entry - tp) / risk
        res, R = None, 0.0
        for k in range(entry_idx + 1, min(entry_idx + MAX_HOLD, n)):
            if side == "long":
                if l[k] <= stop: res, R = "loss", -1.0; break
                if h[k] >= tp: res, R = "win", rr; break
            else:
                if h[k] >= stop: res, R = "loss", -1.0; break
                if l[k] <= tp: res, R = "win", rr; break
        if res is None:
            k = min(i + MAX_HOLD, n) - 1
            R = ((c[k] - entry) if side == "long" else (entry - c[k])) / risk
            res = "win" if R > 0 else "loss"
        last_exit = k
        lot = RISK_USD / (risk * USD_PER_PRICE_PER_LOT)
        if max_lot: lot = min(lot, max_lot)
        # cost = spread + commission + slippage (slippage applied entry+exit)
        cost = (spread + 2 * slip) * USD_PER_PRICE_PER_LOT * lot + comm * lot
        pnl = R * (risk * USD_PER_PRICE_PER_LOT * lot)     # $ from R given this lot
        trades.append({"t": feats["time"][i], "R": R, "res": res, "net": pnl - cost})
    return pd.DataFrame(trades)


def seg_stats(tr):
    if tr.empty or len(tr) == 0:
        return dict(n=0, win=0, net=0, pf=0, dd=0)
    n = len(tr); win = (tr.res == "win").mean() * 100; net = tr.net.sum()
    gl = -tr.loc[tr.net < 0, "net"].sum()
    pf = (tr.loc[tr.net > 0, "net"].sum() / gl) if gl else float("inf")
    eq = tr.net.cumsum(); dd = (eq - eq.cummax()).min()
    return dict(n=n, win=win, net=net, pf=pf, dd=dd)


# ------------------------------------------------------------------------------- main
COMBOS = [
    ("ob", dict()), ("ob", dict(pd=1)), ("ob", dict(pd=1, bias=1)),
    ("ob", dict(pd=1, sweep=1)), ("ob", dict(pd=1, bias=1, sweep=1)),
    ("ob", dict(pd=1, bias=1, sweep=1, mss=1)),
    ("fvg", dict()), ("fvg", dict(bias=1)), ("fvg", dict(pd=1, bias=1)),
    ("sweep", dict()), ("sweep", dict(bias=1)), ("sweep", dict(bias=1, mss=1)),
]


def main():
    d = load_all(2.0)
    start = d["15m"]["time"].iloc[0]; end = d["15m"]["time"].iloc[-1]
    split = start + (end - start) * 0.65
    print(f"\nIn-sample: {start.date()} .. {split.date()} | Out-of-sample: {split.date()} .. {end.date()}")
    # data sanity
    for tf in ("5m", "15m", "1h"):
        x = d.get(tf) if tf in d else load(tf, dt.datetime(2024,6,21), dt.datetime(2026,6,21))
        d[tf] = x
        bad = ((x.high < x.low) | (x[["open","high","low","close"]] <= 0).any(axis=1)).sum()
        print(f"  data {tf}: {len(x)} candles | price {x.low.min():.0f}-{x.high.max():.0f} | bad rows: {bad}")

    rows = []
    for tf in ("5m", "15m", "1h"):
        df = d[tf].reset_index(drop=True)
        htfL = [_bias(df, d["1d"], 10, 30), _bias(df, d["1h"], 50, 200)]
        feats, shs, sls = precompute(df, htfL)
        evs = {"ob": ev_ob(df), "fvg": ev_fvg(df), "sweep": ev_sweep(df, shs, sls)}
        for setup, flt in COMBOS:
            for sname, sset in SESSIONS.items():
                for target in ("fix2", "struct"):
                    f = dict(flt); f["sess"] = sset
                    tr = simulate(df, feats, evs[setup], f, target)
                    if tr.empty: continue
                    tr["t"] = pd.to_datetime(tr["t"], utc=True)
                    iss = seg_stats(tr[tr.t < split]); oos = seg_stats(tr[tr.t >= split])
                    passed = (iss["n"] >= 20 and oos["n"] >= 20 and iss["net"] > 0 and oos["net"] > 0
                              and iss["pf"] >= 1.2 and oos["pf"] >= 1.2)
                    rows.append({"tf": tf, "session": sname, "setup": setup,
                                 "filters": "+".join(k for k in flt) or "raw", "target": target,
                                 "is_n": iss["n"], "is_win": round(iss["win"],1), "is_net": round(iss["net"]),
                                 "is_pf": round(iss["pf"],2),
                                 "oos_n": oos["n"], "oos_win": round(oos["win"],1), "oos_net": round(oos["net"]),
                                 "oos_pf": round(oos["pf"],2), "total_net": round(iss["net"]+oos["net"]),
                                 "PASS": passed})
    res = pd.DataFrame(rows).sort_values(["PASS", "oos_net"], ascending=[False, False])
    res.to_csv(OUT, index=False)
    print(f"\nTested {len(res)} combinations -> saved {OUT}")
    surv = res[res.PASS]
    print(f"\n=== SURVIVORS (profitable in BOTH in-sample AND out-of-sample) : {len(surv)} ===")
    if surv.empty:
        print("  NONE. No configuration held up out-of-sample.")
    cols = ["tf","session","setup","filters","target","is_n","is_win","is_pf","oos_n","oos_win","oos_pf","oos_net","total_net"]
    print((surv if not surv.empty else res).head(15).to_string(index=False, columns=cols))
    print("\n--- for contrast: top 8 by OUT-OF-SAMPLE net (PASS or not) ---")
    print(res.head(8).to_string(index=False, columns=cols))


def _bias(exec_df, htf, fast, slow):
    bull = (ema(htf["close"], fast) > ema(htf["close"], slow)).shift(1)
    right = pd.DataFrame({"time": _utc_naive(htf["time"]), "bull": bull.values}).dropna().sort_values("time")
    left = pd.DataFrame({"time": _utc_naive(exec_df["time"])}).sort_values("time")
    return pd.merge_asof(left, right, on="time", direction="backward")["bull"].fillna(False).astype(bool).values


if __name__ == "__main__":
    main()
