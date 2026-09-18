"""
Reality stress-test of the sweep's top configs.

The sweep found huge numbers (esp. 5m FVG). This checks whether they survive
realistic execution: wider spread, slippage, commission, and a MINIMUM STOP
DISTANCE (tiny-stop trades aren't executable and inflate lot size to fantasy).

If an 'edge' evaporates under realism, it was never an edge.
"""
from __future__ import annotations
import datetime as dt
import pandas as pd
from dukascopy_loader import load_all, load
from sweep import precompute, ev_ob, ev_fvg, ev_sweep, simulate, seg_stats, _bias, SESSIONS


def show(tag, df, feats, events, flt, target, split, **costs):
    tr = simulate(df, feats, events, flt, target, **costs)
    if tr.empty:
        print(f"  {tag:48s}| 0 trades"); return
    tr["t"] = pd.to_datetime(tr["t"], utc=True)
    a = seg_stats(tr[tr.t < split]); b = seg_stats(tr[tr.t >= split])
    print(f"  {tag:48s}| IS ${a['net']:+7.0f} (PF {a['pf']:.2f}) | "
          f"OOS ${b['net']:+7.0f} (PF {b['pf']:.2f}) | trades {a['n']+b['n']}")


if __name__ == "__main__":
    d = load_all(2.0)
    d["5m"] = load("5m", dt.datetime(2024, 6, 21), dt.datetime(2026, 6, 21))
    start = d["15m"]["time"].iloc[0]; end = d["15m"]["time"].iloc[-1]
    split = (start + (end - start) * 0.65)
    split = pd.Timestamp(split).tz_convert("UTC")

    for tf in ("5m", "15m"):
        df = d[tf].reset_index(drop=True)
        htfL = [_bias(df, d["1d"], 10, 30), _bias(df, d["1h"], 50, 200)]
        feats, shs, sls = precompute(df, htfL)
        evs = {"ob": ev_ob(df), "fvg": ev_fvg(df), "sweep": ev_sweep(df, shs, sls)}
        print(f"\n================  {tf}  ================")
        configs = [
            ("fvg", dict(bias=1), "fix2", "all"),
            ("fvg", dict(), "fix2", "london+ny"),
            ("ob", dict(pd=1, bias=1), "fix2", "all"),
            ("ob", dict(pd=1, bias=1, sweep=1), "struct", "london+ny"),
        ]
        for setup, flt, target, sess in configs:
            f = dict(flt); f["sess"] = SESSIONS[sess]
            name = f"{setup}/{'+'.join(flt) or 'raw'}/{target}/{sess}"
            print(f"\n {name}")
            show("  IDEALIZED (spread .35, no slip, no min-stop)", df, feats, evs[setup], f, target, split,
                 spread=0.35, comm=5.0, slip=0.0, min_risk=0.0)
            show("  REALISTIC (spread .45, slip .10/side, comm 7)", df, feats, evs[setup], f, target, split,
                 spread=0.45, comm=7.0, slip=0.10, min_risk=0.0)
            show("  + min stop $2 (executable sizing)", df, feats, evs[setup], f, target, split,
                 spread=0.45, comm=7.0, slip=0.10, min_risk=2.0)
            show("  + min stop $3 (conservative)", df, feats, evs[setup], f, target, split,
                 spread=0.45, comm=7.0, slip=0.10, min_risk=3.0)
