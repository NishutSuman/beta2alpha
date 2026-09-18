"""
beta2alpha — FINAL validations on the winning nested setup (15m OB inside 1H OB,
bias + premium/discount, London+NY kill zones).

  1. PARAMETER SENSITIVITY: vary bias EMAs, exec displacement mult, HTF displacement
     mult, min-stop, target. A real edge stays robust across most settings.
  2. MONTE CARLO: shuffle trade order (worst-case drawdown) + bootstrap resample
     (return distribution) to size the realistic pain before any real money.

5y Dukascopy, 10-fold walk-forward, realistic costs, 0.5% risk.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from dukascopy_loader import load_all
from sweep import precompute, _bias, SESSIONS, struct_tp
from backtest_full import confirmed_swings
from structures import displacement
from validate_fractal import ev_ob_mult, build_htf_obs, simulate_fractal, wf

YEARS, N_FOLDS, ACCOUNT = 5.0, 10, 5000.0
REPORT = os.path.join(os.path.dirname(__file__), "..", "data", "validate_final_report.md")
np.random.seed(42)

BIAS_SETS = {"d10/30·h50/200": ((10, 30), (50, 200)),
             "d20/50·h50/150": ((20, 50), (50, 150)),
             "d8/21·h21/55": ((8, 21), (21, 55))}


def htf_arrays(h, mult):
    obs = build_htf_obs(h, mult)
    return {"ct": np.array([p["ct"] for p in obs]).astype("datetime64[ns]").astype("int64"),
            "it": np.array([p["it"] for p in obs]).astype("datetime64[ns]").astype("int64"),
            "top": np.array([p["top"] for p in obs]),
            "bot": np.array([p["bot"] for p in obs]),
            "long": np.array([p["dir"] == "long" for p in obs])}


def mark_nested_fast(events, feats, ha):
    ti = feats["time"].astype("datetime64[ns]").astype("int64")
    ct, it, top, bot, isL = ha["ct"], ha["it"], ha["top"], ha["bot"], ha["long"]
    for ev in events:
        te = ti[ev["idx"]]
        cb, ctp = (ev["stop"], ev["entry"]) if ev["side"] == "long" else (ev["entry"], ev["stop"])
        want = isL if ev["side"] == "long" else ~isL
        active = want & (ct <= te) & (te < it) & (cb <= top) & (ctp >= bot)
        ev["nested"] = bool(active.any())
    return events


def maxdd(net_seq):
    eq = np.cumsum(net_seq); peak = np.maximum.accumulate(eq)
    return float((eq - peak).min())


def main():
    d = load_all(YEARS)
    ex = d["15m"].reset_index(drop=True); h1 = d["1h"]
    start = pd.Timestamp(ex["time"].iloc[0]).tz_convert("UTC")
    end = pd.Timestamp(ex["time"].iloc[-1]).tz_convert("UTC")
    span = (ex["time"].iloc[-1] - ex["time"].iloc[0]).days
    edges = [start + (end - start) * k / N_FOLDS for k in range(N_FOLDS + 1)]
    feats, _, _ = precompute(ex, [])
    hsw = confirmed_swings(h1, 3, 3)
    erl_hi = sorted(s["price"] for s in hsw if s["kind"] == "high")
    erl_lo = sorted(s["price"] for s in hsw if s["kind"] == "low")

    # ---------- 1. PARAMETER SENSITIVITY (London+NY, nest required) ----------
    bias_cache = {name: (lambda dL, hL: (dL & hL, (~dL) & (~hL)))(
        _bias(ex, d["1d"], *p[0]), _bias(ex, h1, *p[1])) for name, p in BIAS_SETS.items()}
    events_cache = {m: ev_ob_mult(ex, m) for m in (1.3, 1.5, 2.0)}
    ha_cache = {m: htf_arrays(h1, m) for m in (1.5, 2.0)}

    rows = []
    for bname in BIAS_SETS:
        mtfL, mtfS = bias_cache[bname]
        fb = {**feats, "mtfL": mtfL, "mtfS": mtfS}
        for em in (1.3, 1.5, 2.0):
            evs = events_cache[em]
            for hm in (1.5, 2.0):
                mark_nested_fast(evs, feats, ha_cache[hm])
                for ms in (2.0, 3.0):
                    for tgt in ("fix2", "erl"):
                        flt = {"nest": 1, "sess": SESSIONS["london+ny"]}
                        tr = simulate_fractal(ex, fb, evs, flt, erl_hi, erl_lo, tgt)
                        if tr.empty or len(tr) < 60:
                            continue
                        prof, net, nets = wf(tr, edges)
                        win = (tr.res == "win").mean() * 100
                        gl = -tr.loc[tr.net < 0, "net"].sum()
                        pf = (tr.loc[tr.net > 0, "net"].sum() / gl) if gl else 99
                        rows.append({"bias": bname, "exec_mult": em, "htf_mult": hm,
                                     "min_stop": ms, "target": tgt, "trades": len(tr),
                                     "win%": round(win, 1), "PF": round(pf, 2), "net$": net,
                                     "/mo": round(net / (span / 30)), "folds+": prof,
                                     "robust": prof >= 8 and net > 0})
    res = pd.DataFrame(rows)
    rrate = res["robust"].mean() * 100 if len(res) else 0

    # ---------- 2. MONTE CARLO on the canonical winner ----------
    mtfL, mtfS = bias_cache["d10/30·h50/200"]
    fb = {**feats, "mtfL": mtfL, "mtfS": mtfS}
    evs = events_cache[1.5]; mark_nested_fast(evs, feats, ha_cache[1.5])
    win_tr = simulate_fractal(ex, fb, evs, {"nest": 1, "sess": SESSIONS["london+ny"]},
                              erl_hi, erl_lo, "fix2").sort_values("t")
    nets = win_tr["net"].values
    actual_net = nets.sum(); actual_dd = maxdd(nets)
    N = 3000
    dds = np.empty(N); tots = np.empty(N)
    for i in range(N):
        perm = np.random.permutation(nets); dds[i] = maxdd(perm)          # order shuffle -> DD
        boot = np.random.choice(nets, size=len(nets), replace=True); tots[i] = boot.sum()  # bootstrap -> return
    dd_med, dd_95, dd_worst = np.percentile(dds, 50), np.percentile(dds, 5), dds.min()
    tot_med, tot_5, tot_95 = np.percentile(tots, 50), np.percentile(tots, 5), np.percentile(tots, 95)
    p_loss = (tots < 0).mean() * 100

    # ---------- report ----------
    md = []
    md.append("# beta2alpha — Final Validation (Sensitivity + Monte Carlo)\n")
    md.append(f"_Winning setup: 15m OB nested in 1H OB + bias + premium/discount · London+NY · "
              f"5y ({span}d) · 10-fold WF · realistic costs · 0.5% risk ($25)_\n")
    md.append("\n## 1. Parameter sensitivity (does the edge survive setting changes?)\n")
    md.append(f"\n**{len(res)} parameter combos tested · {res['robust'].sum()} robust "
              f"({rrate:.0f}%).** A high robust-rate = genuine effect, not knife-edge.\n")
    for dim in ["bias", "exec_mult", "htf_mult", "min_stop", "target"]:
        g = res.groupby(dim)["robust"].agg(["size", "sum"])
        md.append(f"\n- **{dim}:** " + " · ".join(f"{i}={int(r['sum'])}/{int(r['size'])}" for i, r in g.iterrows()))
    cols = ["bias", "exec_mult", "htf_mult", "min_stop", "target", "trades", "win%", "PF", "net$", "/mo", "folds+", "robust"]
    md.append("\n\n### All sensitivity combos\n")
    md.append("| " + " | ".join(cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n")
    for _, r in res.sort_values("net$", ascending=False).iterrows():
        md.append("| " + " | ".join(str(r[c]) for c in cols) + " |\n")
    md.append("\n## 2. Monte Carlo (3000 sims) on the canonical winner\n")
    md.append(f"\n- Trades: {len(nets)} · actual net **${actual_net:,.0f}** over {span}d "
              f"(~${actual_net/(span/30):.0f}/mo @0.5% risk)\n")
    md.append(f"- **Max drawdown** (order-shuffle): median **${dd_med:,.0f}** ({dd_med/ACCOUNT*100:.1f}%), "
              f"95th-pctile **${dd_95:,.0f}** ({dd_95/ACCOUNT*100:.1f}%), worst **${dd_worst:,.0f}** "
              f"({dd_worst/ACCOUNT*100:.1f}%)\n")
    md.append(f"- **Total return** (bootstrap): median ${tot_med:,.0f}, 5th-pctile ${tot_5:,.0f}, "
              f"95th ${tot_95:,.0f} · probability of net loss over 5y: **{p_loss:.1f}%**\n")
    with open(REPORT, "w") as fh:
        fh.write("".join(md))

    print(f"PARAM SENSITIVITY: {len(res)} combos, {res['robust'].sum()} robust ({rrate:.0f}%)")
    for dim in ["bias", "exec_mult", "htf_mult", "min_stop", "target"]:
        g = res.groupby(dim)["robust"].agg(["size", "sum"])
        print(f"  {dim:10s}: " + " | ".join(f"{i}={int(r['sum'])}/{int(r['size'])}" for i, r in g.iterrows()))
    print(f"\nMONTE CARLO (winner, {len(nets)} trades, net ${actual_net:,.0f} = ${actual_net/(span/30):.0f}/mo):")
    print(f"  max drawdown : median ${dd_med:,.0f} ({dd_med/ACCOUNT*100:.1f}%) | "
          f"95%ile ${dd_95:,.0f} ({dd_95/ACCOUNT*100:.1f}%) | worst ${dd_worst:,.0f} ({dd_worst/ACCOUNT*100:.1f}%)")
    print(f"  5y return    : median ${tot_med:,.0f} | 5th ${tot_5:,.0f} | 95th ${tot_95:,.0f} | P(loss) {p_loss:.1f}%")
    print(f"\nReport -> {REPORT}")


if __name__ == "__main__":
    main()
