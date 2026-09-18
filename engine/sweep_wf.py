"""
beta2alpha — WALK-FORWARD sweep with realistic costs, markdown report output.

Upgrade over sweep.py:
  - realistic costs + slippage + minimum-stop BAKED IN (no idealized numbers)
  - WALK-FORWARD: 2y split into N folds; a config is ROBUST only if profitable in
    most folds (>= N-1) with positive total and enough trades. Surviving one lucky
    window is not enough.
  - outputs human-readable MARKDOWN tables to data/sweep_report.md (+ full CSV)

Run: .venv/bin/python engine/sweep_wf.py
"""
from __future__ import annotations
import os
import datetime as dt
import numpy as np
import pandas as pd
from dukascopy_loader import load_all, load
from sweep import (precompute, ev_ob, ev_fvg, ev_sweep, simulate, _bias, SESSIONS)

N_FOLDS = 6
# realistic execution
COST = dict(spread=0.45, comm=7.0, slip=0.10, min_risk=2.0)
REPORT = os.path.join(os.path.dirname(__file__), "..", "data", "sweep_report.md")
CSV = os.path.join(os.path.dirname(__file__), "..", "data", "sweep_wf_results.csv")

COMBOS = [
    ("ob", dict()), ("ob", dict(pd=1)), ("ob", dict(bias=1)), ("ob", dict(pd=1, bias=1)),
    ("ob", dict(pd=1, sweep=1)), ("ob", dict(pd=1, bias=1, sweep=1)),
    ("ob", dict(pd=1, bias=1, mss=1)), ("ob", dict(pd=1, bias=1, sweep=1, mss=1)),
    ("fvg", dict()), ("fvg", dict(bias=1)), ("fvg", dict(pd=1, bias=1)), ("fvg", dict(pd=1, bias=1, sweep=1)),
    ("sweep", dict()), ("sweep", dict(bias=1)), ("sweep", dict(bias=1, mss=1)),
]
TARGETS = ("fix2", "fix3", "struct")


def fold_stats(tr, edges):
    """net per fold + counts. tr has 't' (UTC) and 'net'."""
    nets, counts = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        seg = tr[(tr.t >= a) & (tr.t < b)]
        nets.append(round(seg.net.sum())); counts.append(len(seg))
    prof = sum(1 for x in nets if x > 0)
    return nets, counts, prof


def evaluate(df, feats, events, setup, flt, target, sess, edges):
    f = dict(flt); f["sess"] = SESSIONS[sess]
    tr = simulate(df, feats, events, f, target, **COST)
    if tr.empty:
        return None
    tr["t"] = pd.to_datetime(tr["t"], utc=True)
    n = len(tr); win = (tr.res == "win").mean() * 100; net = tr.net.sum()
    gl = -tr.loc[tr.net < 0, "net"].sum()
    pf = (tr.loc[tr.net > 0, "net"].sum() / gl) if gl else float("inf")
    eq = tr.net.cumsum(); dd = (eq - eq.cummax()).min()
    nets, counts, prof = fold_stats(tr, edges)
    robust = (prof >= N_FOLDS - 1) and net > 0 and n >= 40 and min(counts) >= 3
    return {
        "tf": None, "session": sess, "setup": setup,
        "filters": "+".join(k for k in flt) or "raw", "target": target,
        "trades": n, "win%": round(win, 1), "PF": round(pf, 2),
        "net$": round(net), "/mo@0.5%": round(net / 24),  # ~24 months
        "folds+": f"{prof}/{N_FOLDS}", "worst_fold$": min(nets),
        "fold_nets": nets, "robust": robust,
    }


def md_table(rows, cols):
    if not rows:
        return "_(none)_\n"
    head = "| " + " | ".join(cols) + " |\n"
    sep = "| " + " | ".join("---" for _ in cols) + " |\n"
    body = "".join("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |\n" for r in rows)
    return head + sep + body


def main():
    d = load_all(2.0)
    d["5m"] = load("5m", dt.datetime(2024, 6, 21), dt.datetime(2026, 6, 21))
    start = pd.Timestamp(d["15m"]["time"].iloc[0]).tz_convert("UTC")
    end = pd.Timestamp(d["15m"]["time"].iloc[-1]).tz_convert("UTC")
    edges = [start + (end - start) * k / N_FOLDS for k in range(N_FOLDS + 1)]

    all_rows = []
    for tf in ("5m", "15m", "1h"):
        df = d[tf].reset_index(drop=True)
        htfL = [_bias(df, d["1d"], 10, 30), _bias(df, d["1h"], 50, 200)]
        feats, shs, sls = precompute(df, htfL)
        evs = {"ob": ev_ob(df), "fvg": ev_fvg(df), "sweep": ev_sweep(df, shs, sls)}
        for setup, flt in COMBOS:
            for sess in SESSIONS:
                for target in TARGETS:
                    r = evaluate(df, feats, evs[setup], setup, flt, target, sess, edges)
                    if r:
                        r["tf"] = tf
                        all_rows.append(r)

    res = pd.DataFrame(all_rows)
    res = res.sort_values(["robust", "net$"], ascending=[False, False]).reset_index(drop=True)
    res.drop(columns=["fold_nets"]).to_csv(CSV, index=False)

    robust = res[res.robust]
    cols = ["tf", "session", "setup", "filters", "target", "trades", "win%", "PF", "net$", "/mo@0.5%", "folds+", "worst_fold$"]

    # dimension aggregates
    def agg(dim):
        g = res.groupby(dim).agg(configs=("robust", "size"), robust=("robust", "sum"),
                                 median_net=("net$", "median")).reset_index()
        return [{dim: r[dim], "configs": int(r["configs"]), "robust": int(r["robust"]),
                 "median_net$": round(r["median_net"])} for _, r in g.iterrows()]

    fold_edges_str = " | ".join(f"F{i+1}:{a.date()}→{b.date()}" for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])))

    md = []
    md.append("# beta2alpha — Walk-Forward Strategy Sweep\n")
    md.append(f"_2 years Dukascopy XAU/USD · realistic costs (spread {COST['spread']}, "
              f"slippage {COST['slip']}/side, commission ${COST['comm']}/lot, min-stop ${COST['min_risk']}) · "
              f"{N_FOLDS}-fold walk-forward · 0.5% risk ($25)/trade_\n")
    md.append(f"**Tested {len(res)} configurations. ROBUST (profitable in ≥{N_FOLDS-1}/{N_FOLDS} folds, "
              f"net>0, ≥40 trades): {len(robust)}.**\n")
    md.append(f"\n**Folds:** {fold_edges_str}\n")
    md.append("\n## 1. ROBUST configurations (survive walk-forward)\n")
    md.append(md_table(robust.to_dict("records"), cols))
    md.append("\n## 2. Per-fold net ($) for robust configs\n")
    fcols = ["tf", "session", "setup", "filters", "target"] + [f"F{i+1}" for i in range(N_FOLDS)]
    frows = []
    for _, r in robust.iterrows():
        row = {k: r[k] for k in ["tf", "session", "setup", "filters", "target"]}
        for i, v in enumerate(r["fold_nets"]):
            row[f"F{i+1}"] = v
        frows.append(row)
    md.append(md_table(frows, fcols))
    md.append("\n## 3. Top 25 by total net (robust or not — for context)\n")
    md.append(md_table(res.head(25).to_dict("records"), cols))
    md.append("\n## 4. Which dimensions tend to work?\n")
    md.append("\n**By setup:**\n"); md.append(md_table(agg("setup"), ["setup", "configs", "robust", "median_net$"]))
    md.append("\n**By session:**\n"); md.append(md_table(agg("session"), ["session", "configs", "robust", "median_net$"]))
    md.append("\n**By timeframe:**\n"); md.append(md_table(agg("tf"), ["tf", "configs", "robust", "median_net$"]))
    md.append("\n**By target:**\n"); md.append(md_table(agg("target"), ["target", "configs", "robust", "median_net$"]))

    with open(REPORT, "w") as fh:
        fh.write("\n".join(md))
    print(f"Tested {len(res)} configs | ROBUST: {len(robust)}")
    print(f"Markdown report -> {REPORT}")
    print(f"Full CSV        -> {CSV}\n")
    print("Top robust (or top overall if none):")
    print((robust if not robust.empty else res).head(12).to_string(
        index=False, columns=cols))


if __name__ == "__main__":
    main()
