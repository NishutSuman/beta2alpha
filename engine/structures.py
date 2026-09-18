"""
Core ICT/SMC structure detectors for beta2alpha — Phase 1.

Implements the objective, codeable primitives from STRATEGY-SPEC.md:
  - swings (fractal highs/lows)
  - displacement (institutional momentum candle)
  - FVG (fair value gap)  + filled/unfilled tracking
  - order blocks (last opposite-colour candle before displacement) + mean threshold (0.5)
  - premium / discount (fib equilibrium of a leg)
  - body-close break helper

All functions take the canonical candle df (time, open, high, low, close[, volume])
and return plain dicts/lists so they're easy to serialize to the dashboard / Telegram.

NOTE: these are the OBJECTIVE primitives. "Which POI is the main one" / "is this fake
structure" stay human (per the spec's codeability verdict).
"""
from __future__ import annotations
import pandas as pd


# ----------------------------------------------------------------------------- swings
def swings(df: pd.DataFrame, left: int = 2, right: int = 2) -> list[dict]:
    """Fractal swing points. A swing high = strictly highest high over `left` bars
    before and `right` bars after (mirror for low). Returns chronological list of
    {idx, time, price, kind} with kind in {'high','low'}."""
    out: list[dict] = []
    highs, lows = df["high"].values, df["low"].values
    n = len(df)
    for i in range(left, n - right):
        win_h = highs[i - left:i + right + 1]
        win_l = lows[i - left:i + right + 1]
        if highs[i] == win_h.max() and (win_h == highs[i]).sum() == 1:
            out.append({"idx": i, "time": df["time"].iloc[i], "price": float(highs[i]), "kind": "high"})
        elif lows[i] == win_l.min() and (win_l == lows[i]).sum() == 1:
            out.append({"idx": i, "time": df["time"].iloc[i], "price": float(lows[i]), "kind": "low"})
    return out


# ----------------------------------------------------------------------- displacement
def displacement(df: pd.DataFrame, lookback: int = 20, mult: float = 1.5) -> list[dict]:
    """Momentum candles: body > `mult` x average body of the prior `lookback` candles.
    Displacement = proof big players entered (spec §4). Returns list of
    {idx, time, dir, body, avg_body}."""
    body = (df["close"] - df["open"]).abs()
    avg = body.rolling(lookback).mean()
    out: list[dict] = []
    for i in range(lookback, len(df)):
        if avg.iloc[i] > 0 and body.iloc[i] > mult * avg.iloc[i]:
            out.append({
                "idx": i, "time": df["time"].iloc[i],
                "dir": "up" if df["close"].iloc[i] > df["open"].iloc[i] else "down",
                "body": float(body.iloc[i]), "avg_body": float(avg.iloc[i]),
            })
    return out


# -------------------------------------------------------------------------------- FVG
def fvgs(df: pd.DataFrame) -> list[dict]:
    """Fair Value Gaps (3-candle imbalance).
    Bullish FVG: low[i+1] > high[i-1]  (gap between candle i-1 high and i+1 low)
    Bearish FVG: high[i+1] < low[i-1]
    Returns {idx, time, dir, top, bottom, mid, filled} — mid is the 0.5 of the gap."""
    out: list[dict] = []
    h, l = df["high"].values, df["low"].values
    for i in range(1, len(df) - 1):
        if l[i + 1] > h[i - 1]:
            top, bottom = float(l[i + 1]), float(h[i - 1])
            out.append(_fvg(df, i, "bull", top, bottom))
        elif h[i + 1] < l[i - 1]:
            top, bottom = float(l[i - 1]), float(h[i + 1])
            out.append(_fvg(df, i, "bear", top, bottom))
    return out


def _fvg(df, i, direction, top, bottom):
    # mark filled if any later candle traded back through the mid (mean threshold)
    mid = (top + bottom) / 2
    later = df.iloc[i + 2:]
    filled = bool(((later["low"] <= mid) & (later["high"] >= mid)).any())
    return {"idx": i, "time": df["time"].iloc[i], "dir": direction,
            "top": top, "bottom": bottom, "mid": mid, "filled": filled}


# ----------------------------------------------------------------------- order blocks
def order_blocks(df: pd.DataFrame, disp: list[dict] | None = None,
                 lookback: int = 20, mult: float = 1.5) -> list[dict]:
    """Order block = the last opposite-colour candle immediately before a displacement
    (spec §5: to BUY mark last selling candle; to SELL mark last buying candle).
    mean_threshold = 0.5 of the OB candle range. Returns
    {idx, time, dir, top, bottom, mean_threshold, valid}."""
    disp = disp if disp is not None else displacement(df, lookback, mult)
    out: list[dict] = []
    for d in disp:
        i = d["idx"]
        want_bull = d["dir"] == "up"          # bullish OB feeds an up displacement
        ob_idx = None
        for j in range(i - 1, max(i - 6, 0), -1):     # search up to 5 candles back
            is_down = df["close"].iloc[j] < df["open"].iloc[j]
            if want_bull and is_down:
                ob_idx = j; break
            if not want_bull and not is_down:
                ob_idx = j; break
        if ob_idx is None:
            continue
        top = float(max(df["open"].iloc[ob_idx], df["close"].iloc[ob_idx], df["high"].iloc[ob_idx]))
        bottom = float(min(df["open"].iloc[ob_idx], df["close"].iloc[ob_idx], df["low"].iloc[ob_idx]))
        # use candle high/low as the zone; mean threshold = midpoint
        top = float(df["high"].iloc[ob_idx]); bottom = float(df["low"].iloc[ob_idx])
        mt = (top + bottom) / 2
        out.append({
            "idx": ob_idx, "time": df["time"].iloc[ob_idx],
            "dir": "bull" if want_bull else "bear",
            "top": top, "bottom": bottom, "mean_threshold": mt,
            "valid": _ob_valid(df, ob_idx, "bull" if want_bull else "bear", mt),
        })
    return out


def _ob_valid(df, ob_idx, direction, mt) -> bool:
    """Spec §5 validity: block is valid while NO candle BODY closes beyond its mean
    threshold (0.5). For a bull OB, a body close below MT invalidates; for bear, above."""
    later = df.iloc[ob_idx + 1:]
    if direction == "bull":
        return not bool((later[["open", "close"]].max(axis=1) < mt).any() and (later["close"] < mt).any())
    return not bool((later["close"] > mt).any())


# ------------------------------------------------------------------ premium / discount
def premium_discount(low: float, high: float) -> dict:
    """Fib equilibrium of a leg (spec §5): only 0 / 0.5 / 1.
    Buy only in discount (<0.5), sell only in premium (>0.5)."""
    eq = (low + high) / 2
    return {"low": low, "high": high, "equilibrium": eq,
            "discount_top": eq, "premium_bottom": eq}


def zone_of(price: float, low: float, high: float) -> str:
    """Return 'premium' | 'discount' | 'equilibrium' for a price within a leg."""
    eq = (low + high) / 2
    if price > eq:
        return "premium"
    if price < eq:
        return "discount"
    return "equilibrium"


# --------------------------------------------------------------------- break helper
def body_close_broke(df: pd.DataFrame, level: float, above: bool, after_idx: int) -> bool:
    """Spec §3: a structural break needs a BODY CLOSE beyond the level (not a wick)."""
    later = df.iloc[after_idx + 1:]
    return bool((later["close"] > level).any()) if above else bool((later["close"] < level).any())


if __name__ == "__main__":
    from data import fetch
    df = fetch(interval="1h", period="60d")
    sw = swings(df); disp = displacement(df); fv = fvgs(df); ob = order_blocks(df, disp)
    print(f"1H gold, {len(df)} candles ({df['time'].iloc[0].date()} -> {df['time'].iloc[-1].date()})")
    print(f"  swings:        {len(sw)}  (last: {sw[-1]['kind']} @ {sw[-1]['price']:.1f})")
    print(f"  displacements: {len(disp)} (last: {disp[-1]['dir']} body {disp[-1]['body']:.1f} vs avg {disp[-1]['avg_body']:.1f})")
    print(f"  FVGs:          {len(fv)}  (unfilled: {sum(not f['filled'] for f in fv)})")
    print(f"  order blocks:  {len(ob)} (valid: {sum(o['valid'] for o in ob)})")
    last_ob = [o for o in ob if o["valid"]][-1]
    print(f"  last valid OB: {last_ob['dir']} zone {last_ob['bottom']:.1f}-{last_ob['top']:.1f} MT {last_ob['mean_threshold']:.1f}")
