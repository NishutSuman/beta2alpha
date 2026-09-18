"""
beta2alpha — rigorous experiment round (does ANY mechanical edge survive 2y + costs?).

Changes vs backtest_2y:
  - STRUCTURE-BASED targets: TP = nearest swing-liquidity beyond entry giving >= min_rr
    (faithful to the method) instead of a fixed R multiple.
  - TIMEFRAME flexible: test 1H execution (fewer trades -> less cost drag) vs 15m.
  - quality knob: displacement multiple; session filter toggle.
Costs always ON. Per-year shown so we only trust cross-regime results.
"""
from __future__ import annotations
import pandas as pd
from dukascopy_loader import load_all
from backtest_full import ema, _utc_naive, confirmed_swings, session_ist
from structures import displacement

RISK_USD = 25.0
USD_PER_PRICE_PER_LOT, SPREAD_PRICE, COMM = 100.0, 0.35, 5.0
KILL = {"London-kill", "NY-kill"}


def resample(df, rule):
    s = df.set_index("time")
    o = s["open"].resample(rule).first(); h = s["high"].resample(rule).max()
    l = s["low"].resample(rule).min(); c = s["close"].resample(rule).last()
    v = s["volume"].resample(rule).sum()
    out = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}).dropna().reset_index()
    return out


def bias_map(exec_df, htf, fast, slow):
    bull = (ema(htf["close"], fast) > ema(htf["close"], slow)).shift(1)
    right = pd.DataFrame({"time": _utc_naive(htf["time"]), "bull": bull.values}).dropna().sort_values("time")
    left = pd.DataFrame({"time": _utc_naive(exec_df["time"])}).sort_values("time")
    return pd.merge_asof(left, right, on="time", direction="backward")["bull"].fillna(False).astype(bool).values


def build_obs(df, mult):
    obs = []
    for d in displacement(df, lookback=20, mult=mult):
        i = d["idx"]; bull = d["dir"] == "up"; ob = None
        for j in range(i - 1, max(i - 6, 0), -1):
            down = df["close"].iloc[j] < df["open"].iloc[j]
            if bull and down: ob = j; break
            if not bull and not down: ob = j; break
        if ob is None: continue
        top, bot = float(df["high"].iloc[ob]), float(df["low"].iloc[ob])
        obs.append({"ob": ob, "confirm": i, "dir": "bull" if bull else "bear",
                    "top": top, "bot": bot, "mt": (top + bot) / 2, "tapped": False})
    return obs


def struct_tp(price_levels, entry, risk, side, min_rr, max_rr=12):
    """nearest swing liquidity beyond entry giving >= min_rr; None if none qualifies."""
    if side == "long":
        cands = sorted(p for p in price_levels if p > entry)
        for p in cands:
            rr = (p - entry) / risk
            if rr >= min_rr: return p if rr <= max_rr else entry + max_rr * risk
    else:
        cands = sorted((p for p in price_levels if p < entry), reverse=True)
        for p in cands:
            rr = (entry - p) / risk
            if rr >= min_rr: return p if rr <= max_rr else entry - max_rr * risk
    return None


def run(df, htf_biases, sh, sl, filters, min_rr=2.0, mult=1.5, sessions=KILL):
    c, h, l = df["close"], df["high"], df["low"]
    e50, e200 = ema(c, 50), ema(c, 200)
    rhi, rlo = h.rolling(50).max(), l.rolling(50).min()
    obs = build_obs(df, mult)
    sh_px = [s["price"] for s in sh]; sl_px = [s["price"] for s in sl]
    sh_conf = [(s["confirm"], s["price"]) for s in sh]
    sl_conf = [(s["confirm"], s["price"]) for s in sl]
    trades, pos = [], None

    def swept(i, side):
        arr = sl_conf if side == "long" else sh_conf
        hit = None
        for conf, P in arr:
            if conf >= i or conf < i - 40: continue
            for j in range(max(conf, i - 8), i + 1):
                if side == "long" and l.iloc[j] < P and c.iloc[j] > P:
                    hit = min(hit, float(l.iloc[j])) if hit else float(l.iloc[j])
                if side == "short" and h.iloc[j] > P and c.iloc[j] < P:
                    hit = max(hit, float(h.iloc[j])) if hit else float(h.iloc[j])
        return hit

    def mss(i, side):
        arr = [(cf, P) for cf, P in (sh_conf if side == "long" else sl_conf) if cf < i and cf >= i - 30]
        if not arr: return False
        P = arr[-1][1]
        seg = c.iloc[max(i - 8, 0):i + 1]
        return bool((seg > P).any()) if side == "long" else bool((seg < P).any())

    for i in range(200, len(df)):
        if pos:
            t = pos
            slh = l.iloc[i] <= t["sl"] if t["side"] == "long" else h.iloc[i] >= t["sl"]
            tph = h.iloc[i] >= t["tp"] if t["side"] == "long" else l.iloc[i] <= t["tp"]
            if slh: t["R"] = -1.0; t["result"] = "loss"
            elif tph: t["R"] = t["rr"]; t["result"] = "win"
            if t.get("result"): trades.append(t); pos = None
            else: continue
        if sessions and session_ist(df["time"].iloc[i]) not in sessions: continue
        mid = (rhi.iloc[i] + rlo.iloc[i]) / 2
        for ob in obs:
            if ob["tapped"] or ob["confirm"] >= i: continue
            if not ((l.iloc[i] <= ob["top"]) and (h.iloc[i] >= ob["bot"])): continue
            ob["tapped"] = True
            seg = df.iloc[ob["confirm"] + 1:i]
            side = "long" if ob["dir"] == "bull" else "short"
            if side == "long":
                if (seg["close"] < ob["mt"]).any() or not (e50.iloc[i] > e200.iloc[i]): continue
                if "mtf" in filters and not all(b[i] for b in htf_biases): continue
                if ob["top"] >= mid: continue
                sw = swept(i, "long")
                if "sweep" in filters and sw is None: continue
                if "mss" in filters and not mss(i, "long"): continue
                entry = ob["top"]; stop = (min(ob["bot"], sw) if sw else ob["bot"]) * (1 - 0.0005)
                risk = entry - stop
                if risk <= 0: continue
                tp = struct_tp(sh_px, entry, risk, "long", min_rr)
                if tp is None: continue
                pos = {"side": "long", "time": df["time"].iloc[i], "entry": entry, "sl": stop,
                       "tp": tp, "rr": (tp - entry) / risk}
                break
            else:
                if (seg["close"] > ob["mt"]).any() or not (e50.iloc[i] < e200.iloc[i]): continue
                if "mtf" in filters and not all(not b[i] for b in htf_biases): continue
                if ob["bot"] <= mid: continue
                sw = swept(i, "short")
                if "sweep" in filters and sw is None: continue
                if "mss" in filters and not mss(i, "short"): continue
                entry = ob["bot"]; stop = (max(ob["top"], sw) if sw else ob["top"]) * (1 + 0.0005)
                risk = stop - entry
                if risk <= 0: continue
                tp = struct_tp(sl_px, entry, risk, "short", min_rr)
                if tp is None: continue
                pos = {"side": "short", "time": df["time"].iloc[i], "entry": entry, "sl": stop,
                       "tp": tp, "rr": (entry - tp) / risk}
                break
    return pd.DataFrame(trades)


def report(label, tr, days):
    if tr.empty:
        print(f"  {label:34s}|   0 trades"); return
    tr = tr.copy()
    sd = (tr["entry"] - tr["sl"]).abs()
    tr["lot"] = RISK_USD / (sd * USD_PER_PRICE_PER_LOT)
    tr["cost"] = SPREAD_PRICE * USD_PER_PRICE_PER_LOT * tr["lot"] + COMM * tr["lot"]
    tr["net"] = tr["R"] * RISK_USD - tr["cost"]
    n = len(tr); w = (tr.result == "win").mean()
    net = tr["net"].sum(); avg_rr = tr.loc[tr.result == "win", "rr"].mean()
    pf = tr.loc[tr.net > 0, "net"].sum() / (-tr.loc[tr.net < 0, "net"].sum() or 1)
    eq = tr["net"].cumsum(); dd = (eq - eq.cummax()).min()
    tr["yr"] = pd.to_datetime(tr["time"], utc=True).dt.year
    yrs = " | ".join(f"{y}:{(g.result=='win').mean()*100:.0f}%/${g.net.sum():+.0f}" for y, g in tr.groupby("yr"))
    print(f"  {label:34s}| {n:4d}tr | win {w*100:4.1f}% | avgWinR {avg_rr:3.1f} | PF {pf:4.2f} | "
          f"NET ${net:+6.0f} | DD ${dd:5.0f} | ${net/days*30:+5.0f}/mo")
    print(f"       └─ by year: {yrs}")


if __name__ == "__main__":
    d = load_all(2.0)
    m15, h1, d1 = d["15m"], d["1h"], d["1d"]
    h4 = resample(h1, "4h")
    days = (m15["time"].iloc[-1] - m15["time"].iloc[0]).days
    print(f"\n=== RIGOROUS ROUND | structure targets | costs ON | 2y ({days}d) ===\n")

    # ---- 15m execution, structure targets ----
    print("[15m execution | kill zones]")
    db15 = bias_map(m15, d1, 10, 30); hb15 = bias_map(m15, h1, 50, 200)
    sh15 = [s for s in confirmed_swings(m15, 3, 3) if s["kind"] == "high"]
    sl15 = [s for s in confirmed_swings(m15, 3, 3) if s["kind"] == "low"]
    for lab, f in [("MTF+sweep", {"mtf", "sweep"}), ("FULL (+MSS)", {"mtf", "sweep", "mss"})]:
        report(lab, run(m15, [db15, hb15], sh15, sl15, f, min_rr=2.0), days)

    # ---- 1H execution, structure targets (fewer trades, less cost drag) ----
    print("\n[1H execution | kill zones]")
    db1 = bias_map(h1, d1, 10, 30); h4b = bias_map(h1, h4, 10, 30)
    sh1 = [s for s in confirmed_swings(h1, 3, 3) if s["kind"] == "high"]
    sl1 = [s for s in confirmed_swings(h1, 3, 3) if s["kind"] == "low"]
    for lab, f in [("MTF+sweep", {"mtf", "sweep"}), ("FULL (+MSS)", {"mtf", "sweep", "mss"})]:
        report(lab, run(h1, [db1, h4b], sh1, sl1, f, min_rr=2.0), days)

    print("\n[1H execution | ALL hours]")
    for lab, f in [("MTF+sweep", {"mtf", "sweep"}), ("FULL (+MSS)", {"mtf", "sweep", "mss"})]:
        report(lab, run(h1, [db1, h4b], sh1, sl1, f, min_rr=2.0, sessions=None), days)

    print("\n[1H execution | kill zones | higher quality disp x2.5, min_rr 3]")
    for lab, f in [("FULL (+MSS)", {"mtf", "sweep", "mss"})]:
        report(lab, run(h1, [db1, h4b], sh1, sl1, f, min_rr=3.0, mult=2.5), days)
