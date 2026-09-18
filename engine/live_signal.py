"""
beta2alpha — live SIGNAL engine for the dashboard.

Turns the ONE validated edge into a current snapshot the React dashboard consumes:
  - HTF bias (Daily + 1H trend)
  - premium/discount of the recent range
  - "watch levels": valid 15m order blocks NESTED inside an active 1H order block,
    aligned with bias and on the right side of equilibrium
  - live setup: if price is tapping a watch level and the last 15m candle CONFIRMS
    (closes back in our direction) -> entry / SL / TP / lot (risk-managed)

Honest scope: this surfaces the validated setup (~2-4/week, ~47% win @1:2). It is NOT
a sure-shot. Data here is yfinance (delayed ~15m) for the MVP; swap to OANDA live later.
"""
from __future__ import annotations
import datetime as dt
import pandas as pd
import market_data
from structures import order_blocks, swings, fvgs, displacement
from backtest_full import session_ist

KILL = {"London-kill", "NY-kill"}
USD_PER_PRICE_PER_LOT = 100.0   # XAU/USD: 1.0 lot, $1 move = $100
IST = "Asia/Kolkata"


def _ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def _active_h1_obs(h1: pd.DataFrame, max_age: int = 600):
    """Valid 1H order blocks formed recently and not yet invalidated (parent zones)."""
    obs = order_blocks(h1)
    n = len(h1)
    return [o for o in obs if o["valid"] and (n - o["idx"]) <= max_age]


def _nested(child, parents):
    """child 15m OB overlaps an active same-direction 1H OB."""
    for p in parents:
        if p["dir"] != child["dir"]:
            continue
        if child["bottom"] <= p["top"] and child["top"] >= p["bot" if "bot" in p else "bottom"]:
            return True
    return False


def _plan(side, top, bottom, mt, account, risk_pct, tp_override=None, rr=2.0, buf=0.0005):
    """Pre-computed trade plan for a zone (leading: ready BEFORE price arrives).
    Entry at the mean threshold, SL beyond the far edge, TP at external liquidity if
    given (>=1.5R) else fixed 2R."""
    if side == "long":
        entry = mt; stop = bottom * (1 - buf); risk = entry - stop
    else:
        entry = mt; stop = top * (1 + buf); risk = stop - entry
    if risk <= 0:
        return None
    if tp_override and abs(tp_override - entry) / risk >= 1.5:
        tp = tp_override
    else:
        tp = entry + rr * risk if side == "long" else entry - rr * risk
    rr_actual = abs(tp - entry) / risk
    risk_usd = account * risk_pct / 100
    lot = round(risk_usd / (risk * USD_PER_PRICE_PER_LOT), 2)
    return {
        "entry": round(entry, 2), "stop_loss": round(stop, 2), "take_profit": round(tp, 2),
        "stop_distance": round(risk, 2), "risk_reward": f"1:{rr_actual:.1f}",
        "risk_usd": round(risk_usd, 2), "lot_size": lot,
    }


def _unfilled_fvgs(df, want, limit=4):
    """Recent unfilled fair value gaps, aligned with bias — for drawing + narrative."""
    out = []
    for f in fvgs(df):
        if f["filled"] or (len(df) - f["idx"]) > 250:
            continue
        side = "long" if f["dir"] == "bull" else "short"
        if want and side != want:
            continue
        out.append({"dir": side, "top": round(f["top"], 2), "bottom": round(f["bottom"], 2),
                    "start_time": int(pd.Timestamp(df["time"].iloc[f["idx"]]).timestamp())})
    return out[-limit:]


def _latest_mss(df):
    """Most recent Market Structure Shift: last confirmed swing broken by a body close."""
    sw = swings(df, 3, 3)
    highs = [s for s in sw if s["kind"] == "high"]; lows = [s for s in sw if s["kind"] == "low"]
    res = None
    if highs:
        sh = highs[-1]; after = df.iloc[sh["idx"] + 3:]
        br = after[after["close"] > sh["price"]]
        if len(br): res = ("bull", sh["price"], br.index[0])
    if lows:
        sl = lows[-1]; after = df.iloc[sl["idx"] + 3:]
        br = after[after["close"] < sl["price"]]
        if len(br) and (res is None or br.index[0] > res[2]):
            res = ("bear", sl["price"], br.index[0])
    if not res:
        return None
    d, lvl, bi = res
    return {"dir": d, "level": round(float(lvl), 2), "time": int(pd.Timestamp(df["time"].iloc[bi]).timestamp())}


def _latest_displacement(df):
    disp = displacement(df, 20, 1.5)
    if not disp:
        return None
    d = disp[-1]
    return {"dir": d["dir"], "strength": round(d["body"] / d["avg_body"], 1),
            "time": int(pd.Timestamp(df["time"].iloc[d["idx"]]).timestamp())}


def _resample_4h(h1):
    """Build 4H candles from 1H (Twelve Data/yfinance don't always serve 4H directly)."""
    s = h1.copy(); s["time"] = pd.to_datetime(s["time"], utc=True)
    r = (s.set_index("time").resample("4h")
         .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
         .dropna().reset_index())
    return r


def _anchor(m15, start, end, hi, lo):
    """Find the 15m candles (within [start,end)) that PRINTED the high and the low,
    so each level line can be drawn from the exact candle that made it."""
    t = pd.to_datetime(m15["time"], utc=True)
    seg = m15[(t >= start) & (t < end)]
    if seg.empty:
        return None, None
    ht = int(pd.Timestamp(seg.loc[seg["high"].idxmax(), "time"]).timestamp())
    lt = int(pd.Timestamp(seg.loc[seg["low"].idxmin(), "time"]).timestamp())
    return ht, lt


def _liquidity_levels(d1, m15, price, bias):
    """ILDRE Step 1 + 3: external liquidity (PDH/PDL, PWH/PWL) + delivery destination.
    Uses the previous COMPLETED daily/weekly candle (matches MT5) and anchors each level
    at the candle that printed it."""
    t = pd.to_datetime(d1["time"], utc=True)
    # previous completed day = second-to-last daily candle (last = current/forming day)
    pdr = d1.iloc[-2] if len(d1) >= 2 else d1.iloc[-1]
    pdh, pdl = float(pdr["high"]), float(pdr["low"])
    pd_start = pd.Timestamp(pdr["time"])           # already tz-aware (UTC)
    pd_end = pd.Timestamp(d1["time"].iloc[-1])
    pdh_t, pdl_t = _anchor(m15, pd_start, pd_end, pdh, pdl)

    # previous week via ISO week grouping (avoids resample week-end label misalignment)
    dd = d1.copy(); dd["t"] = t
    dd["yw"] = dd["t"].dt.strftime("%G-%V")
    weeks = list(dict.fromkeys(dd["yw"]))      # chronological unique weeks
    if len(weeks) >= 2:
        prev = dd[dd["yw"] == weeks[-2]]; cur = dd[dd["yw"] == weeks[-1]]
        pwh, pwl = float(prev["high"].max()), float(prev["low"].min())
        pw_start, pw_end = prev["t"].min(), cur["t"].min()
    else:
        pwh, pwl = float(dd["high"].max()), float(dd["low"].min())
        pw_start, pw_end = dd["t"].min(), pd.Timestamp.now(tz="UTC")
    pwh_t, pwl_t = _anchor(m15, pw_start, pw_end, pwh, pwl)

    lv = {"pdh": round(pdh, 2), "pdl": round(pdl, 2), "pwh": round(pwh, 2), "pwl": round(pwl, 2),
          "pdh_time": pdh_t, "pdl_time": pdl_t, "pwh_time": pwh_t, "pwl_time": pwl_t}
    target = None
    if bias == "bearish":
        below = [(p, lab) for p, lab in [(pdl, "PDL"), (pwl, "PWL")] if p < price]
        if below:
            p, lab = max(below); target = {"price": round(p, 2), "label": lab, "side": "sell-side"}
    elif bias == "bullish":
        above = [(p, lab) for p, lab in [(pdh, "PDH"), (pwh, "PWH")] if p > price]
        if above:
            p, lab = min(above); target = {"price": round(p, 2), "label": lab, "side": "buy-side"}
    lv["target"] = target
    return lv


def _grade_ob(o, df, minor_l, minor_h, major_l, major_h, price, mss_aligned=False, h4_aligned=False, pd_ok=False, fvg_all=None):
    """Score a nested OB by liquidity/structure confluence (internal & external liquidity,
    4H alignment, MSS). Returns (score 0-100, grade, reasons[], external_target_price|None)."""
    i = o["idx"]; side = "long" if o["dir"] == "bull" else "short"
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    reasons = ["Nested 15m OB inside an active 1H OB (fractal confluence)",
               f"Aligned with {('bullish' if side=='long' else 'bearish')} HTF bias",
               f"On the correct side of equilibrium ({'discount' if side=='long' else 'premium'})"]
    score = 40

    # OB + FVG = POI (mentor's core rule): an OB with an adjacent same-direction Fair Value
    # Gap is what the market actually respects. Bare OBs are lower conviction.
    has_fvg = False
    if fvg_all:
        for f in fvg_all:
            if f["dir"] == o["dir"] and (o["idx"] - 2) <= f["idx"] <= (o["idx"] + 5):
                has_fvg = True; break
    if has_fvg:
        score += 16
        reasons.append("Paired with a Fair Value Gap (OB + FVG = true POI — the market respects this)")
    else:
        reasons.append("No adjacent FVG (bare order block — lower conviction)")

    # PREMIUM/DISCOUNT: correct half of the recent range (scoring bonus, not a gate, so
    # nearby trend-continuation zones still surface in a strong trend)
    if pd_ok:
        score += 8
        reasons.append(f"In the {'discount' if side=='long' else 'premium'} half of the range")
    # FULL HTF ALIGNMENT: 4H agrees with the Daily/1H bias (Step 6 fractal alignment)
    if h4_aligned:
        score += 12
        reasons.append("4H timeframe agrees with the bias (full HTF fractal alignment)")
    # MARKET STRUCTURE SHIFT confirms the bias direction
    if mss_aligned:
        score += 12
        reasons.append("Market Structure Shift confirms the bias direction")

    # INTERNAL liquidity grab: near OB formation, did price sweep a recent minor swing then reclaim?
    internal = False
    pool = minor_l if side == "long" else minor_h
    for idx, p in pool:
        if idx >= i or idx < i - 25:
            continue
        for j in range(max(idx + 1, i - 6), min(i + 2, len(df))):
            if side == "long" and l[j] < p and c[j] > p:
                internal = True; break
            if side == "short" and h[j] > p and c[j] < p:
                internal = True; break
        if internal:
            break
    if internal:
        score += 14
        reasons.append("Internal liquidity was swept then reclaimed at the origin (smart-money grab)")

    # EXTERNAL liquidity target: a major swing beyond entry that gives good R:R (draw on liquidity)
    entry = o["mean_threshold"]
    risk = (entry - o["bottom"]) if side == "long" else (o["top"] - entry)
    ext = None
    if risk > 0:
        if side == "long":
            cands = sorted(p for _, p in major_h if p > entry)
            for p in cands:
                if (p - entry) / risk >= 1.5:
                    ext = p; break
        else:
            cands = sorted((p for _, p in major_l if p < entry), reverse=True)
            for p in cands:
                if (entry - p) / risk >= 1.5:
                    ext = p; break
    if ext:
        score += 14
        reasons.append(f"Clear external liquidity to target at {round(ext,2)} (draw on liquidity, >=1.5R)")
    else:
        reasons.append("No clean external liquidity target nearby — capped at 2R (lower conviction)")

    # FRESHNESS: zone not yet retapped since it formed
    fresh = True
    for j in range(i + 3, len(df)):
        if l[j] <= o["top"] and h[j] >= o["bottom"]:
            fresh = False; break
    if fresh:
        score += 8
        reasons.append("Fresh / unmitigated zone (not tapped yet)")
    else:
        reasons.append("Zone already tapped once (weaker)")

    score = min(score, 100)
    grade = "High" if score >= 76 else "Medium" if score >= 54 else "Low"
    return score, grade, reasons, ext, has_fvg


def get_analysis(account: float = 5000.0, risk_pct: float = 0.5) -> dict:
    m15 = market_data.fetch("15m")
    h1 = market_data.fetch("1h")
    d1 = market_data.fetch("1d")

    price = float(m15["close"].iloc[-1])
    last = m15.iloc[-1]
    now_sess = session_ist(pd.Timestamp.now(tz="UTC"))   # session from REAL clock, not the lagging last candle

    daily_bull = bool(_ema(d1["close"], 10).iloc[-1] > _ema(d1["close"], 30).iloc[-1])
    h1_bull = bool(_ema(h1["close"], 50).iloc[-1] > _ema(h1["close"], 200).iloc[-1])
    h4 = _resample_4h(h1)
    h4_bull = bool(_ema(h4["close"], 50).iloc[-1] > _ema(h4["close"], 200).iloc[-1]) if len(h4) > 60 else h1_bull
    if daily_bull and h1_bull:
        bias = "bullish"
    elif (not daily_bull) and (not h1_bull):
        bias = "bearish"
    else:
        bias = "mixed"

    hi = float(m15["high"].tail(50).max()); lo = float(m15["low"].tail(50).min())
    eq = (hi + lo) / 2
    zone = "premium" if price > eq else "discount"

    parents = _active_h1_obs(h1)
    m15_obs = [o for o in order_blocks(m15) if o["valid"] and (len(m15) - o["idx"]) <= 500]

    # swing pools for internal (minor) and external (major) liquidity scoring
    sw_minor = swings(m15, 2, 2); sw_major = swings(m15, 5, 5)
    minor_l = [(s["idx"], s["price"]) for s in sw_minor if s["kind"] == "low"]
    minor_h = [(s["idx"], s["price"]) for s in sw_minor if s["kind"] == "high"]
    major_l = [(s["idx"], s["price"]) for s in sw_major if s["kind"] == "low"]
    major_h = [(s["idx"], s["price"]) for s in sw_major if s["kind"] == "high"]
    fvg_all = fvgs(m15)   # for OB+FVG (POI) detection

    # 4H alignment + MSS direction (deeper structure, fed into OB scoring)
    h4_aligned = (h4_bull == daily_bull)
    mss = _latest_mss(m15)
    want = "bull" if bias == "bullish" else "bear" if bias == "bearish" else None
    mss_aligned = bool(mss and want and mss["dir"] == want)

    watch, seen = [], set()
    for o in m15_obs:
        if want and o["dir"] != want:
            continue
        # actionable continuation zone: a short must sit at/above price (price pulls UP into
        # it), a long at/below price. Drops zones price has already blown past.
        if o["dir"] == "bull" and not (o["bottom"] <= price * 1.001):
            continue
        if o["dir"] == "bear" and not (o["top"] >= price * 0.999):
            continue
        if not _nested(o, parents):
            continue
        key = (round(o["top"]), round(o["bottom"]))     # integer dedupe (merge near-identical)
        if key in seen:
            continue
        seen.add(key)
        pd_ok = (o["mean_threshold"] < eq) if o["dir"] == "bull" else (o["mean_threshold"] > eq)
        score, grade, reasons, ext, has_fvg = _grade_ob(
            o, m15, minor_l, minor_h, major_l, major_h, price,
            mss_aligned=mss_aligned, h4_aligned=h4_aligned, pd_ok=pd_ok, fvg_all=fvg_all)
        if grade == "Low":               # only show higher-probability setups
            continue
        side = "long" if o["dir"] == "bull" else "short"
        plan = _plan(side, o["top"], o["bottom"], o["mean_threshold"], account, risk_pct, tp_override=ext)
        zstatus = "in_zone" if (o["bottom"] <= price <= o["top"]) else "approaching"
        watch.append({
            "dir": side, "top": round(o["top"], 2), "bottom": round(o["bottom"], 2),
            "mean_threshold": round(o["mean_threshold"], 2),
            "distance_pct": round((o["mean_threshold"] - price) / price * 100, 2),
            "nested_in_1H": True, "status": zstatus, "has_fvg": has_fvg,
            "score": score, "grade": grade, "reasons": reasons,
            "start_time": int(pd.Timestamp(o["time"]).timestamp()),
            "plan": plan,
        })
    # POIs (OB+FVG) first, then nearest, then score — so the market-respected zones lead
    watch.sort(key=lambda w: (0 if w["has_fvg"] else 1, abs(w["distance_pct"]), -w["score"]))
    watch = watch[:5]

    # ILDRE narrative pieces: MSS (computed above), displacement, unfilled FVGs
    fvg_want = "long" if bias == "bullish" else "short" if bias == "bearish" else None
    disp = _latest_displacement(m15)
    ufvgs = _unfilled_fvgs(m15, fvg_want)
    sweep_ok = any("swept" in r for w in watch for r in w.get("reasons", []))
    disp_ok = bool(disp and want and ((disp["dir"] == "up") == (want == "bull")))
    narrative = {
        "sweep": sweep_ok, "mss": mss_aligned, "order_block": len(watch) > 0,
        "displacement": disp_ok, "fvg": len(ufvgs) > 0,
        "score": sum([sweep_ok, mss_aligned, len(watch) > 0, disp_ok, len(ufvgs) > 0]),
    }

    # live setup: price tapping a watch zone + last candle confirms reaction
    setup = _live_setup(watch, last, price, now_sess, account, risk_pct)
    # ILDRE Step 8: refine entry on 5M once price is in the zone (forming/confirmed)
    if setup.get("status") in {"forming", "CONFIRMED"} and setup.get("zone"):
        setup["refinement"] = _refine_5m(setup["zone"], account, risk_pct)

    return {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "instrument": "XAU/USD",
        "data_source": market_data.source_label(),
        "is_live": market_data.is_live(),
        "price": round(price, 2),
        "session_ist": now_sess,
        "in_kill_zone": now_sess in KILL,
        "ist_time": pd.Timestamp.now(tz=IST).strftime("%a %d %b · %I:%M %p IST"),
        "kill_zones": [{"name": "London", "ist": "12:30–15:30 IST"},
                       {"name": "New York", "ist": "17:30–20:30 IST"}],
        "bias": {"daily": "bull" if daily_bull else "bear",
                 "h4": "bull" if h4_bull else "bear",
                 "h1": "bull" if h1_bull else "bear", "overall": bias,
                 "full_aligned": bool(daily_bull == h4_bull == h1_bull)},
        "range": {"high": round(hi, 2), "low": round(lo, 2),
                  "equilibrium": round(eq, 2), "current_zone": zone},
        "liquidity": _liquidity_levels(d1, m15, price, bias),
        "mss": mss, "displacement": disp, "fvgs": ufvgs, "narrative": narrative,
        "watch_levels": watch[:6],
        "live_setup": setup,
        "note": ("Tradeable only in a kill zone with the trend. ~2-4 setups/week, "
                 "~47% win at 1:2. Not a sure-shot. Risk small, survive, compound."),
    }


def _live_setup(watch, last, price, sess, account, risk_pct):
    if sess not in KILL:
        return {"status": "stand_aside", "reason": "outside kill zone (London/NY)"}
    if not watch:
        return {"status": "no_setup", "reason": "no valid nested OB aligned with bias"}
    # find the highest-scored zone price is currently INSIDE (watch is already score-sorted)
    o = next((z for z in watch if z["bottom"] <= price <= z["top"]), None)
    if o is None:
        nearest = min(watch, key=lambda z: abs(z["mean_threshold"] - price))
        return {"status": "watching",
                "reason": f"price approaching {nearest['grade']} {nearest['dir']} zone "
                          f"({nearest['distance_pct']}% away)", "nearest": nearest}
    # confirmation candle: last 15m closes back in trade direction
    bullish_close = last["close"] > last["open"]
    confirmed = (o["dir"] == "long" and bullish_close) or (o["dir"] == "short" and not bullish_close)
    if not confirmed:
        return {"status": "forming",
                "reason": f"in {o['grade']} {o['dir']} zone — waiting for confirmation candle", "zone": o}
    entry = float(last["close"])
    if o["dir"] == "long":
        stop = o["bottom"] * (1 - 0.0005); risk = entry - stop; tp = entry + 2 * risk
    else:
        stop = o["top"] * (1 + 0.0005); risk = stop - entry; tp = entry - 2 * risk
    if risk <= 0:
        return {"status": "no_setup", "reason": "invalid risk geometry"}
    risk_usd = account * risk_pct / 100
    lot = round(risk_usd / (risk * USD_PER_PRICE_PER_LOT), 2)
    return {
        "status": "CONFIRMED", "dir": o["dir"],
        "entry": round(entry, 2), "stop_loss": round(stop, 2), "take_profit": round(tp, 2),
        "risk_reward": "1:2", "stop_distance": round(risk, 2),
        "risk_usd": round(risk_usd, 2), "lot_size": lot,
        "zone": o,
    }


def _refine_5m(zone, account, risk_pct, buf=0.0005):
    """ILDRE Step 8: refine the entry on 5M inside the active 15M zone.
    Finds the EXTREME 5M order block within the 15M zone (tighter entry/stop, better R:R);
    falls back to the 15M plan if no valid 5M PD array exists."""
    side, ztop, zbot = zone["dir"], zone["top"], zone["bottom"]
    plan15 = zone.get("plan") or {}
    fallback = {**plan15, "refined_on": "15M (no valid 5M PD array — fallback)", "ob5": None}
    try:
        m5 = market_data.fetch("5m")
    except Exception:
        return {**plan15, "refined_on": "15M (5M data unavailable)", "ob5": None}
    want = "bull" if side == "long" else "bear"
    inside = [o for o in order_blocks(m5)
              if o["valid"] and (len(m5) - o["idx"]) <= 300 and o["dir"] == want
              and o["bottom"] <= ztop and o["top"] >= zbot]
    if not inside:
        return fallback
    o5 = min(inside, key=lambda o: o["bottom"]) if side == "long" else max(inside, key=lambda o: o["top"])
    entry = o5["mean_threshold"]
    stop = o5["bottom"] * (1 - buf) if side == "long" else o5["top"] * (1 + buf)
    risk = entry - stop if side == "long" else stop - entry
    if risk <= 0:
        return fallback
    tp = plan15.get("take_profit")
    if not tp or (side == "long" and tp <= entry) or (side == "short" and tp >= entry):
        tp = entry + 2 * risk if side == "long" else entry - 2 * risk
    rr = abs(tp - entry) / risk
    risk_usd = account * risk_pct / 100
    return {
        "refined_on": "5M extreme OB", "entry": round(entry, 2), "stop_loss": round(stop, 2),
        "take_profit": round(tp, 2), "risk_reward": f"1:{rr:.1f}", "stop_distance": round(risk, 2),
        "risk_usd": round(risk_usd, 2), "lot_size": round(risk_usd / (risk * USD_PER_PRICE_PER_LOT), 2),
        "ob5": {"top": round(o5["top"], 2), "bottom": round(o5["bottom"], 2)},
    }


def get_candles(tf: str = "15m", count: int = 200) -> dict:
    """Recent candles for the chart (lightweight-charts wants UNIX-second time)."""
    df = market_data.fetch(tf).tail(count)
    candles = [{
        "time": int(pd.Timestamp(t).timestamp()),
        "open": round(float(o), 2), "high": round(float(h), 2),
        "low": round(float(l), 2), "close": round(float(c), 2),
    } for t, o, h, l, c in zip(df["time"], df["open"], df["high"], df["low"], df["close"])]
    return {"tf": tf, "source": market_data.source_label(), "candles": candles}


if __name__ == "__main__":
    import json
    print(json.dumps(get_analysis(), indent=2))
