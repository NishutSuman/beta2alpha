"""
beta2alpha — FULL FRACTAL / LIQUIDITY-AWARE validation (Option A).

The faithful version of the mentor's method, tested causally over ~5 years:
  - FRACTAL NESTING: an execution-TF (15m) order block is valid only if it sits INSIDE
    an active higher-TF (1H) order block of the same direction (a 15m OB nested in a 1H
    POI). This is the "fractal nature" confluence.
  - INTERNAL -> EXTERNAL LIQUIDITY: require an internal liquidity sweep (IRL) before
    entry; target EXTERNAL liquidity (1H swing highs/lows) for the exit.
  - REACTION: the OB itself is formed by a displacement (proof of reaction at the level).
  - + HTF bias + premium/discount, realistic costs, 10-fold walk-forward.

We compare baseline vs +nest vs +irl vs +both, in ALL hours and in his KILL ZONES,
to see whether full fractal confluence finds a kill-zone edge the proxy missed.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from dukascopy_loader import load_all
from sweep import precompute, _bias, SESSIONS, struct_tp
from backtest_full import confirmed_swings
from structures import displacement

YEARS = 5.0
N_FOLDS = 10
USD_PER_PRICE_PER_LOT, RISK_USD = 100.0, 25.0
COST = dict(spread=0.45, comm=7.0, slip=0.10, min_risk=2.0)
REPORT = os.path.join(os.path.dirname(__file__), "..", "data", "validate_fractal_report.md")


def ev_ob_mult(df, mult=1.5):
    out, n = [], len(df)
    c, o, h, l = df["close"].values, df["open"].values, df["high"].values, df["low"].values
    for d in displacement(df, 20, mult):
        i = d["idx"]; bull = d["dir"] == "up"; ob = None
        for j in range(i - 1, max(i - 6, 0), -1):
            down = c[j] < o[j]
            if bull and down: ob = j; break
            if not bull and not down: ob = j; break
        if ob is None: continue
        top, bot = float(h[ob]), float(l[ob]); side = "long" if bull else "short"
        for k in range(i + 1, min(i + 300, n)):
            if l[k] <= top and h[k] >= bot:
                out.append({"idx": k, "side": side,
                            "entry": top if bull else bot, "stop": bot if bull else top}); break
    return out


def build_htf_obs(h, mult=1.5):
    """HTF (1H) order blocks as parent zones, with confirm/invalidation TIMES (causal)."""
    obs, n = [], len(h)
    c, o, hi, lo = h["close"].values, h["open"].values, h["high"].values, h["low"].values
    t = h["time"].values
    for d in displacement(h, 20, mult):
        i = d["idx"]; bull = d["dir"] == "up"; ob = None
        for j in range(i - 1, max(i - 6, 0), -1):
            down = c[j] < o[j]
            if bull and down: ob = j; break
            if not bull and not down: ob = j; break
        if ob is None: continue
        top, bot = float(hi[ob]), float(lo[ob]); mt = (top + bot) / 2
        inv = t[-1]
        for k in range(i + 1, n):                 # first body close beyond MT invalidates
            if (bull and c[k] < mt) or (not bull and c[k] > mt):
                inv = t[k]; break
        obs.append({"dir": "long" if bull else "short", "ct": t[i], "it": inv,
                    "top": top, "bot": bot})
    return obs


def mark_nested(events, feats, htf_obs):
    """Set ev['nested'] = does this exec OB sit inside an ACTIVE same-dir HTF OB?"""
    times = feats["time"]
    for ev in events:
        te = times[ev["idx"]]
        cb, ct = min(ev["entry"], ev["stop"]), max(ev["entry"], ev["stop"])
        nested = False
        for p in htf_obs:
            if p["dir"] != ev["side"]: continue
            if not (p["ct"] <= te < p["it"]): continue
            if cb <= p["top"] and ct >= p["bot"]:   # zone overlap
                nested = True; break
        ev["nested"] = nested
    return events


def simulate_fractal(df, feats, events, flt, erl_hi, erl_lo, target):
    h, l, c = feats["h"], feats["l"], feats["c"]
    n = len(df); last_exit = -1; trades = []
    for ev in events:
        i = ev["idx"]
        if i <= last_exit or i >= n - 2: continue
        side = ev["side"]
        if flt["sess"] and feats["sess"][i] not in flt["sess"]: continue
        if not (feats["mtfL"][i] if side == "long" else feats["mtfS"][i]): continue   # bias
        if side == "long" and not (ev["entry"] < feats["mid"][i]): continue           # discount
        if side == "short" and not (ev["entry"] > feats["mid"][i]): continue          # premium
        if flt.get("nest") and not ev["nested"]: continue
        if flt.get("irl") and not (feats["swepL"][i] if side == "long" else feats["swepS"][i]): continue
        entry, stop = ev["entry"], ev["stop"]
        if flt.get("irl"):
            spx = feats["sweepLpx"][i] if side == "long" else feats["sweepSpx"][i]
            if not np.isnan(spx): stop = min(stop, spx) if side == "long" else max(stop, spx)
        stop = stop * (1 - 0.0005) if side == "long" else stop * (1 + 0.0005)
        risk = entry - stop if side == "long" else stop - entry
        if risk <= 0 or risk < COST["min_risk"]: continue
        if target == "erl":      # external liquidity = HTF swing levels
            tp = struct_tp(erl_hi if side == "long" else erl_lo, entry, risk, side, min_rr=1.5)
            if tp is None: continue
        else:
            tp = entry + 2 * risk if side == "long" else entry - 2 * risk
        rr = (tp - entry) / risk if side == "long" else (entry - tp) / risk
        res, R = None, 0.0
        for k in range(i + 1, min(i + 150, n)):
            if side == "long":
                if l[k] <= stop: res, R = "loss", -1.0; break
                if h[k] >= tp: res, R = "win", rr; break
            else:
                if h[k] >= stop: res, R = "loss", -1.0; break
                if l[k] <= tp: res, R = "win", rr; break
        if res is None:
            k = min(i + 150, n) - 1
            R = ((c[k] - entry) if side == "long" else (entry - c[k])) / risk
            res = "win" if R > 0 else "loss"
        last_exit = k
        lot = RISK_USD / (risk * USD_PER_PRICE_PER_LOT)
        cost = (COST["spread"] + 2 * COST["slip"]) * USD_PER_PRICE_PER_LOT * lot + COST["comm"] * lot
        trades.append({"t": feats["time"][i], "res": res, "net": R * RISK_USD - cost})
    return pd.DataFrame(trades)


def wf(tr, edges):
    if tr.empty: return 0, 0, []
    tr = tr.copy(); tr["t"] = pd.to_datetime(tr["t"], utc=True)
    nets = [tr.loc[(tr.t >= a) & (tr.t < b), "net"].sum() for a, b in zip(edges[:-1], edges[1:])]
    return sum(1 for x in nets if x > 0), round(tr.net.sum()), [round(x) for x in nets]


def main():
    d = load_all(YEARS)
    exec_df = d["15m"].reset_index(drop=True); h1 = d["1h"]
    span = (exec_df["time"].iloc[-1] - exec_df["time"].iloc[0]).days
    start = pd.Timestamp(exec_df["time"].iloc[0]).tz_convert("UTC")
    end = pd.Timestamp(exec_df["time"].iloc[-1]).tz_convert("UTC")
    edges = [start + (end - start) * k / N_FOLDS for k in range(N_FOLDS + 1)]

    dL = _bias(exec_df, d["1d"], 10, 30); hL = _bias(exec_df, h1, 50, 200)
    feats, _, _ = precompute(exec_df, [])
    feats["mtfL"] = dL & hL; feats["mtfS"] = (~dL) & (~hL)
    events = ev_ob_mult(exec_df, 1.5)
    htf_obs = build_htf_obs(h1, 1.5)
    events = mark_nested(events, feats, htf_obs)
    hsw = confirmed_swings(h1, 3, 3)
    erl_hi = sorted(s["price"] for s in hsw if s["kind"] == "high")
    erl_lo = sorted(s["price"] for s in hsw if s["kind"] == "low")
    nest_rate = sum(e["nested"] for e in events) / max(len(events), 1)
    print(f"15m exec | {len(exec_df)} candles | {span}d | {len(events)} OB events "
          f"({nest_rate*100:.0f}% nested in 1H OB) | {len(htf_obs)} HTF OBs")

    setups = [("baseline (bias+PD)", {}), ("+nest", {"nest": 1}),
              ("+irl", {"irl": 1}), ("+nest+irl (FULL fractal)", {"nest": 1, "irl": 1})]
    rows = []
    for sname, base in setups:
        for sess in ("all", "london+ny"):
            for target in ("erl", "fix2"):
                flt = {**base, "sess": SESSIONS[sess]}
                tr = simulate_fractal(exec_df, feats, events, flt, erl_hi, erl_lo, target)
                if tr.empty or len(tr) < 20:
                    rows.append({"setup": sname, "session": sess, "target": target,
                                 "trades": len(tr), "win%": "-", "PF": "-", "net$": "-",
                                 "folds+": "-", "robust": False}); continue
                prof, net, nets = wf(tr, edges)
                win = (tr.res == "win").mean() * 100
                gl = -tr.loc[tr.net < 0, "net"].sum()
                pf = (tr.loc[tr.net > 0, "net"].sum() / gl) if gl else 99
                robust = prof >= 8 and net > 0 and len(tr) >= 60
                rows.append({"setup": sname, "session": sess, "target": target,
                             "trades": len(tr), "win%": round(win, 1), "PF": round(pf, 2),
                             "net$": net, "/mo@0.5%": round(net / (span / 30)),
                             "folds+": f"{prof}/{N_FOLDS}", "worst_fold": min(nets) if nets else 0,
                             "robust": robust})
    res = pd.DataFrame(rows)
    cols = ["setup", "session", "target", "trades", "win%", "PF", "net$", "/mo@0.5%", "folds+", "worst_fold", "robust"]

    md = ["# beta2alpha — Full Fractal / Liquidity Validation (Option A)\n",
          f"_15m exec nested in 1H OBs · IRL→ERL · Dukascopy {start.date()}→{end.date()} "
          f"({span}d) · {N_FOLDS}-fold WF · realistic costs · 0.5% risk_\n",
          f"\nOB events nested inside a 1H OB: **{nest_rate*100:.0f}%**\n",
          "\n| " + " | ".join(cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n"]
    for _, r in res.iterrows():
        md.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |\n")
    with open(REPORT, "w") as fh:
        fh.write("".join(md))
    print(f"\nReport -> {REPORT}\n")
    print(res.to_string(index=False, columns=cols))
    kz = res[(res.session == "london+ny") & (res.robust)]
    print("\n" + ("*** ROBUST KILL-ZONE EDGE FOUND ***" if len(kz)
                  else "No robust kill-zone (london+ny) edge even with full fractal confluence."))


if __name__ == "__main__":
    main()
