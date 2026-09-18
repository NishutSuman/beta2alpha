"""
beta2alpha — ILDRE framework backtest: which condition-set actually works?

Tests the mentor's ILDRE conditions in combination on 2y Dukascopy gold, walk-forward
(8 folds) + realistic costs. Conditions tested as toggles on top of order-block entries:
  - bias   : trade only with Daily+1H HTF bias
  - pd     : only in correct premium/discount half
  - nested : 15m OB nested inside an active 1H OB (fractal confluence)
  - xsweep : EXTERNAL liquidity (PDH/PDL or major swing) swept & reclaimed before the OB (Rule 1)
  - fvg    : a fair value gap accompanies the OB
  - extreme: the extreme OB (lowest bull / highest bear) in the recent leg (Rule 2)
TP modes: fix2 (2R) | dest (draw to external liquidity: PDH/PDL/major swing, >=1.5R)
Run on 15m and 5m execution, kill-zones and all-hours.

Goal: find the most ROBUST condition-set to build the engine on.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from dukascopy_loader import load_all, load
import datetime as dt
from sweep import _bias, SESSIONS, struct_tp
from backtest_full import confirmed_swings, _utc_naive, session_ist
from structures import displacement
from validate_fractal import build_htf_obs

YEARS, N_FOLDS = 5.0, 10
COST = dict(spread=0.45, comm=7.0, slip=0.10, min_risk=2.0)
USD_PER_PRICE_PER_LOT, RISK_USD = 100.0, 25.0
REPORT = os.path.join(os.path.dirname(__file__), "..", "data", "ildre_report.md")


def pd_levels(exec_df, d1):
    """Previous-Day High/Low active for each intraday candle (causal)."""
    d = d1.copy()
    d["pdh"] = d["high"].shift(1); d["pdl"] = d["low"].shift(1)
    right = pd.DataFrame({"time": _utc_naive(d["time"]), "pdh": d["pdh"], "pdl": d["pdl"]}).dropna().sort_values("time")
    left = pd.DataFrame({"time": _utc_naive(exec_df["time"])}).sort_values("time")
    m = pd.merge_asof(left, right, on="time", direction="backward")
    return m["pdh"].values, m["pdl"].values


def ob_events(df, mult=1.5):
    out, n = [], len(df)
    c, o, h, l = df["close"].values, df["open"].values, df["high"].values, df["low"].values
    for d in displacement(df, 20, mult):
        i = d["idx"]; bull = d["dir"] == "up"; ob = None
        for j in range(i - 1, max(i - 6, 0), -1):
            down = c[j] < o[j]
            if bull and down: ob = j; break
            if not bull and not down: ob = j; break
        if ob is None: continue
        top, bot = float(h[ob]), float(l[ob]); mt = (top + bot) / 2
        for k in range(i + 1, min(i + 300, n)):           # realistic fill: price trades THROUGH the mean threshold
            if l[k] <= mt <= h[k]:
                out.append({"ob": ob, "confirm": i, "tap": k, "dir": "long" if bull else "short",
                            "top": top, "bot": bot, "mt": mt}); break
    return out


def fvgs_set(df):
    """indices that have an FVG immediately after (3-candle imbalance), by direction."""
    h, l = df["high"].values, df["low"].values
    bull, bear = set(), set()
    for i in range(1, len(df) - 1):
        if l[i + 1] > h[i - 1]: bull.add(i)
        elif h[i + 1] < l[i - 1]: bear.add(i)
    return bull, bear


def enrich(df, h1, d1, mult=1.5):
    """Build OB events with all ILDRE flags + chosen targets (causal)."""
    n = len(df); h, l, c = df["high"].values, df["low"].values, df["close"].values
    pdh, pdl = pd_levels(df, d1)
    htf = build_htf_obs(h1, 1.5)
    htf_ct = np.array([p["ct"] for p in htf]).astype("datetime64[ns]").astype("int64")
    htf_it = np.array([p["it"] for p in htf]).astype("datetime64[ns]").astype("int64")
    htf_top = np.array([p["top"] for p in htf]); htf_bot = np.array([p["bot"] for p in htf])
    htf_long = np.array([p["dir"] == "long" for p in htf])
    times_i8 = df["time"].values.astype("datetime64[ns]").astype("int64")
    sw = confirmed_swings(df, 5, 5)
    maj_hi = sorted(s["price"] for s in sw if s["kind"] == "high")
    maj_lo = sorted(s["price"] for s in sw if s["kind"] == "low")
    maj_lo_c = [(s["confirm"], s["price"]) for s in sw if s["kind"] == "low"]
    maj_hi_c = [(s["confirm"], s["price"]) for s in sw if s["kind"] == "high"]
    fvg_bull, fvg_bear = fvgs_set(df)
    evs = ob_events(df, mult)

    for e in evs:
        i, side = e["ob"], e["dir"]
        te = times_i8[e["confirm"]]
        # nested in active 1H OB
        want = htf_long if side == "long" else ~htf_long
        e["nested"] = bool((want & (htf_ct <= te) & (te < htf_it) &
                            (e["bot"] <= htf_top) & (e["top"] >= htf_bot)).any())
        # external sweep before OB (PDL/major-low for long; PDH/major-high for short), reclaimed
        xs = False
        w0 = max(e["confirm"] - 12, 1)
        for j in range(w0, e["confirm"] + 1):
            if side == "long":
                lvl = pdl[j]
                if not np.isnan(lvl) and l[j] < lvl and c[j] > lvl: xs = True; break
                for cf, p in maj_lo_c:
                    if cf < j and l[j] < p and c[j] > p: xs = True; break
            else:
                lvl = pdh[j]
                if not np.isnan(lvl) and h[j] > lvl and c[j] < lvl: xs = True; break
                for cf, p in maj_hi_c:
                    if cf < j and h[j] > p and c[j] < p: xs = True; break
            if xs: break
        e["xsweep"] = xs
        # fvg accompanies
        e["fvg"] = (e["confirm"] in fvg_bull) if side == "long" else (e["confirm"] in fvg_bear)
        # extreme OB in recent leg (lowest bull bottom / highest bear top in last 40 candles)
        ext = True
        for o2 in evs:
            if o2 is e or o2["dir"] != side or o2["confirm"] >= e["confirm"] or o2["confirm"] < e["confirm"] - 40:
                continue
            if side == "long" and o2["bot"] < e["bot"]: ext = False; break
            if side == "short" and o2["top"] > e["top"]: ext = False; break
        e["extreme"] = ext
        # external-liquidity destination target
        entry = e["mt"]; risk = (entry - e["bot"]) if side == "long" else (e["top"] - entry)
        e["dest"] = None
        if risk > 0:
            cf0 = e["confirm"]
            if side == "long":   # CAUSAL: only swings confirmed before this OB + current PDH
                pool = [p for cf, p in maj_hi_c if cf < cf0]
                if not np.isnan(pdh[i]): pool.append(pdh[i])
                for p in sorted(p for p in pool if p > entry):
                    if (p - entry) / risk >= 1.5: e["dest"] = p; break
            else:
                pool = [p for cf, p in maj_lo_c if cf < cf0]
                if not np.isnan(pdl[i]): pool.append(pdl[i])
                for p in sorted((p for p in pool if p < entry), reverse=True):
                    if (entry - p) / risk >= 1.5: e["dest"] = p; break
    return evs


def simulate(df, evs, flags, tp_mode, sessions, mtfL, mtfS, eq):
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    n = len(df); last = -1; trades = []
    for e in evs:
        k = e["tap"]
        if k <= last or k >= n - 2: continue
        side = e["dir"]
        # ILDRE base (ALWAYS): HTF bias + correct premium/discount half
        if not (mtfL[k] if side == "long" else mtfS[k]): continue
        if side == "long" and not (e["mt"] < eq[k]): continue
        if side == "short" and not (e["mt"] > eq[k]): continue
        if "nested" in flags and not e["nested"]: continue
        if "xsweep" in flags and not e["xsweep"]: continue
        if "fvg" in flags and not e["fvg"]: continue
        if "extreme" in flags and not e["extreme"]: continue
        if sessions and session_ist(df["time"].iloc[k]) not in sessions: continue
        entry = e["mt"]
        stop = e["bot"] * (1 - 0.0005) if side == "long" else e["top"] * (1 + 0.0005)
        risk = entry - stop if side == "long" else stop - entry
        if risk <= 0 or risk < COST["min_risk"]: continue
        if tp_mode == "dest":
            if not e["dest"]: continue
            tp = e["dest"]
        else:
            tp = entry + 2 * risk if side == "long" else entry - 2 * risk
        rr = abs(tp - entry) / risk
        res, R = None, 0.0
        for j in range(k, min(k + 200, n)):   # include fill candle (SL can hit same candle = conservative)
            if side == "long":
                if l[j] <= stop: res, R = "loss", -1.0; break
                if h[j] >= tp: res, R = "win", rr; break
            else:
                if h[j] >= stop: res, R = "loss", -1.0; break
                if l[j] <= tp: res, R = "win", rr; break
        if res is None: continue
        last = j
        lot = RISK_USD / (risk * USD_PER_PRICE_PER_LOT)
        cost = (COST["spread"] + 2 * COST["slip"]) * USD_PER_PRICE_PER_LOT * lot + COST["comm"] * lot
        trades.append({"t": df["time"].iloc[k], "R": R, "res": res, "net": R * RISK_USD - cost})
    return pd.DataFrame(trades)


def wf(tr, edges):
    if tr.empty: return 0, 0, 0
    tr = tr.copy(); tr["t"] = pd.to_datetime(tr["t"], utc=True)
    nets = [tr.loc[(tr.t >= a) & (tr.t < b), "net"].sum() for a, b in zip(edges[:-1], edges[1:])]
    return sum(1 for x in nets if x > 0), round(tr.net.sum()), round(min(nets) if nets else 0)


def main():
    d = load_all(YEARS)
    rows = []
    CONDS = [
        ("base (bias+pd)", set()),
        ("nested", {"nested"}),
        ("nested+xsweep", {"nested", "xsweep"}),
        ("nested+fvg", {"nested", "fvg"}),
        ("nested+extreme", {"nested", "extreme"}),
        ("nested+xsweep+fvg", {"nested", "xsweep", "fvg"}),
        ("nested+xsweep+extreme", {"nested", "xsweep", "extreme"}),
        ("nested+xsweep+fvg+extreme", {"nested", "xsweep", "fvg", "extreme"}),
        ("xsweep+fvg (no nest)", {"xsweep", "fvg"}),
    ]
    for tf in ("15m",):
        df = d[tf].reset_index(drop=True)
        span = (df["time"].iloc[-1] - df["time"].iloc[0]).days
        start = pd.Timestamp(df["time"].iloc[0]).tz_convert("UTC")
        end = pd.Timestamp(df["time"].iloc[-1]).tz_convert("UTC")
        edges = [start + (end - start) * k / N_FOLDS for k in range(N_FOLDS + 1)]
        evs = enrich(df, d["1h"], d["1d"])
        dL = _bias(df, d["1d"], 10, 30); hL = _bias(df, d["1h"], 50, 200)
        mtfL = dL & hL; mtfS = (~dL) & (~hL)
        rhi = df["high"].rolling(50).max(); rlo = df["low"].rolling(50).min()
        eq = ((rhi + rlo) / 2).values
        for cname, flags in CONDS:
            for tp_mode in ("fix2", "dest"):
                for sname in ("london+ny", "all"):
                    tr = simulate(df, evs, flags, tp_mode, SESSIONS[sname], mtfL, mtfS, eq)
                    if tr.empty or len(tr) < 40:
                        continue
                    prof, net, worst = wf(tr, edges)
                    win = (tr.res == "win").mean() * 100
                    gl = -tr.loc[tr.net < 0, "net"].sum()
                    pf = (tr.loc[tr.net > 0, "net"].sum() / gl) if gl else 99
                    rows.append({"tf": tf, "cond": cname, "tp": tp_mode, "sess": sname,
                                 "trades": len(tr), "win%": round(win, 1), "PF": round(pf, 2),
                                 "net$": net, "/mo": round(net / (span / 30)),
                                 "folds+": f"{prof}/{N_FOLDS}", "worst": worst,
                                 "robust": prof >= N_FOLDS - 1 and net > 0 and len(tr) >= 40})
    res = pd.DataFrame(rows).sort_values(["robust", "net$"], ascending=[False, False]).reset_index(drop=True)
    cols = ["tf", "cond", "tp", "sess", "trades", "win%", "PF", "net$", "/mo", "folds+", "worst", "robust"]
    res.to_csv(os.path.join(os.path.dirname(__file__), "..", "data", "ildre_results.csv"), index=False)
    md = ["# ILDRE condition backtest (2y, 8-fold walk-forward, costs)\n",
          f"\n**{len(res)} configs · {int(res['robust'].sum())} robust (>= {N_FOLDS-1}/{N_FOLDS} folds, net>0).**\n",
          "\n## Top results\n", "| " + " | ".join(cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n"]
    for _, r in res.head(40).iterrows():
        md.append("| " + " | ".join(str(r[c]) for c in cols) + " |\n")
    open(REPORT, "w").write("".join(md))
    print(f"{len(res)} configs | robust: {int(res['robust'].sum())} | report -> {REPORT}\n")
    print(res.head(15).to_string(index=False, columns=cols))


if __name__ == "__main__":
    main()
