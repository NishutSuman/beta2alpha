"""
beta2alpha — 5-YEAR extended history + PARAMETER SENSITIVITY validation.

Tests the surviving candidate (Order Block + HTF bias) for:
  1. ROBUSTNESS over ~5 years (10-fold walk-forward) — does the edge predate the
     2024-26 window, across different gold regimes?
  2. PARAMETER SENSITIVITY — vary bias EMAs, displacement multiple, target, min-stop,
     session, and ENTRY MODE (blind tap vs. reaction-confirmation). A real edge
     degrades gracefully across settings; a fluke only works on a knife-edge.

Reaction-confirmation (confirm=True) = only enter if the candle AFTER the tap closes
back in our direction (the market must REACT at our level), addressing the realism
question about how price behaves when it taps the execution zone.

Realistic costs always on. Output: data/validate_report.md
"""
from __future__ import annotations
import os, datetime as dt
import numpy as np
import pandas as pd
from dukascopy_loader import load_all
from sweep import precompute, simulate, _bias, SESSIONS
from structures import displacement

YEARS = 5.0
N_FOLDS = 10
COST = dict(spread=0.45, comm=7.0, slip=0.10, min_risk=2.0)
REPORT = os.path.join(os.path.dirname(__file__), "..", "data", "validate_report.md")

BIAS_SETS = {
    "d10/30·h50/200": ((10, 30), (50, 200)),   # original candidate
    "d20/50·h50/150": ((20, 50), (50, 150)),
    "d8/21·h21/55":   ((8, 21), (21, 55)),
}
MULTS = [1.3, 1.5, 2.0]
TARGETS = ["fix2", "fix3", "struct"]
MIN_STOPS = [2.0, 3.0]
ENTRIES = [("tap", False), ("confirm", True)]
SESS = ["all", "london+ny"]


def ev_ob_mult(df, mult):
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


def wf(tr, edges):
    if tr.empty: return 0, 0, []
    tr = tr.copy(); tr["t"] = pd.to_datetime(tr["t"], utc=True)
    nets = []
    for a, b in zip(edges[:-1], edges[1:]):
        nets.append(tr.loc[(tr.t >= a) & (tr.t < b), "net"].sum())
    prof = sum(1 for x in nets if x > 0)
    return prof, round(tr.net.sum()), [round(x) for x in nets]


def main():
    d = load_all(YEARS)
    df = d["15m"].reset_index(drop=True)
    span = (df["time"].iloc[-1] - df["time"].iloc[0]).days
    start = pd.Timestamp(df["time"].iloc[0]).tz_convert("UTC")
    end = pd.Timestamp(df["time"].iloc[-1]).tz_convert("UTC")
    edges = [start + (end - start) * k / N_FOLDS for k in range(N_FOLDS + 1)]

    feats, shs, sls = precompute(df, [])           # bias-independent base
    events_by_mult = {m: ev_ob_mult(df, m) for m in MULTS}
    bias_arrays = {}
    for name, ((df1, ds1), (h1f, h1s)) in BIAS_SETS.items():
        dL = _bias(df, d["1d"], df1, ds1); hL = _bias(df, d["1h"], h1f, h1s)
        bias_arrays[name] = (dL & hL, (~dL) & (~hL))

    rows = []
    for bname in BIAS_SETS:
        mtfL, mtfS = bias_arrays[bname]
        feats_b = {**feats, "mtfL": mtfL, "mtfS": mtfS}
        for mult in MULTS:
            evs = events_by_mult[mult]
            for target in TARGETS:
                for ms in MIN_STOPS:
                    for ename, conf in ENTRIES:
                        for sess in SESS:
                            flt = {"bias": 1, "sess": SESSIONS[sess]}
                            tr = simulate(df, feats_b, evs, flt, target,
                                          confirm=conf, **{**COST, "min_risk": ms})
                            if tr.empty or len(tr) < 30:
                                continue
                            prof, net, nets = wf(tr, edges)
                            n = len(tr); win = (tr.res == "win").mean() * 100
                            gl = -tr.loc[tr.net < 0, "net"].sum()
                            pf = (tr.loc[tr.net > 0, "net"].sum() / gl) if gl else 99
                            robust = prof >= 8 and net > 0 and n >= 60
                            rows.append({"bias": bname, "mult": mult, "target": target,
                                         "min_stop": ms, "entry": ename, "session": sess,
                                         "trades": n, "win%": round(win, 1), "PF": round(pf, 2),
                                         "net$": net, "/mo@0.5%": round(net / (span / 30)),
                                         "folds+": f"{prof}/{N_FOLDS}", "worst_fold": min(nets) if nets else 0,
                                         "robust": robust})
    res = pd.DataFrame(rows).sort_values(["robust", "net$"], ascending=[False, False]).reset_index(drop=True)
    robust = res[res.robust]

    def md(rws, cols):
        if len(rws) == 0: return "_(none)_\n"
        h = "| " + " | ".join(cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n"
        return h + "".join("| " + " | ".join(str(r[c]) for c in cols) + " |\n" for _, r in rws.iterrows())

    cols = ["bias", "mult", "target", "min_stop", "entry", "session", "trades", "win%", "PF", "net$", "/mo@0.5%", "folds+", "worst_fold"]
    out = []
    out.append("# beta2alpha — 5-Year + Parameter Sensitivity Validation\n")
    out.append(f"_Dukascopy 15m XAU/USD · {start.date()} → {end.date()} ({span} days) · "
               f"{N_FOLDS}-fold walk-forward · realistic costs · 0.5% risk_\n")
    out.append(f"\n**{len(res)} parameter combinations tested. ROBUST (≥8/{N_FOLDS} folds profitable, "
               f"net>0, ≥60 trades): {len(robust)} ({len(robust)*100//max(len(res),1)}%).**\n")
    out.append("\nA real edge should keep working as parameters change. If only a tiny fraction is "
               "robust, it's fragile/overfit; if a large fraction is robust, it's a genuine effect.\n")
    out.append("\n## Robust configurations\n"); out.append(md(robust, cols))
    out.append("\n## Sensitivity: robust-rate by each parameter\n")
    for dim in ["bias", "mult", "target", "min_stop", "entry", "session"]:
        g = res.groupby(dim)["robust"].agg(["size", "sum"]).reset_index()
        out.append(f"\n**{dim}:** " + " · ".join(f"{r[dim]}={int(r['sum'])}/{int(r['size'])}" for _, r in g.iterrows()))
    out.append("\n\n## All combinations (sorted)\n"); out.append(md(res.head(60), cols))

    with open(REPORT, "w") as fh:
        fh.write("\n".join(out))
    print(f"Tested {len(res)} combos | ROBUST: {len(robust)} ({len(robust)*100//max(len(res),1)}%)")
    print(f"Report -> {REPORT}\n")
    print("Robust-rate by parameter:")
    for dim in ["entry", "target", "session", "mult", "bias", "min_stop"]:
        g = res.groupby(dim)["robust"].agg(["size", "sum"])
        print(f"  {dim:9s}: " + " | ".join(f"{idx}={int(r['sum'])}/{int(r['size'])}" for idx, r in g.iterrows()))
    print("\nTop 10:")
    print((robust if not robust.empty else res).head(10).to_string(index=False, columns=cols))


if __name__ == "__main__":
    main()
