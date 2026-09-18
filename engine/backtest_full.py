"""
beta2alpha — FULL confluence backtest (Phase 1b).

Stacks the whole method, causally (no look-ahead), and shows a CONFLUENCE LADDER:
each filter added, and what it does to win-rate vs trade-count. This is how we
honestly test the mentor's "80-90% win rate, 1-2 trades/day" claim.

Pillars coded (long side; short is the mirror):
  bias (MTF/fractal) : Daily trend AND 1H trend must agree with the trade
  liquidity sweep    : a prior swing low is taken out then RECLAIMED (sell-side grab)
  displacement       : a momentum candle confirms big players entered after the sweep
  MSS                : a BODY CLOSE breaks a recent swing high (structure shift up)
  order block + 0.5  : pullback into a valid OB (no body close beyond mean threshold)
  premium/discount   : longs only in discount of the recent range
  protected stop     : SL below the SWEEP low -> the liquidity grab hits others, not us
  kill zones only    : London + NY (Asian/off-hours excluded; they don't work)

Risk: 0.5% ($25) per trade on $5,000; one position at a time; fixed 1:2 R by default.
"""
from __future__ import annotations
import pandas as pd
from data import fetch
from structures import displacement, swings

ACCOUNT, RISK_USD, IST = 5000.0, 25.0, "Asia/Kolkata"
KILL = {"London-kill", "NY-kill"}
K = 8  # confluence look-back window (candles) ~2h on 15m


def ema(s, n): return s.ewm(span=n, adjust=False).mean()


def session_ist(ts):
    t = ts.tz_convert(IST) if ts.tzinfo else ts.tz_localize("UTC").tz_convert(IST)
    h = t.hour + t.minute / 60
    if 12.5 <= h < 15.5: return "London-kill"
    if 17.5 <= h < 20.5: return "NY-kill"
    if 5.5 <= h < 12.5:  return "Asian"
    return "off-hours"


def _utc_naive(s):
    s = pd.to_datetime(s)
    try:
        if s.dt.tz is not None:
            s = s.dt.tz_convert("UTC").dt.tz_localize(None)
    except (AttributeError, TypeError):
        pass
    return s.astype("datetime64[us]")   # normalize resolution (cached=ms vs fresh=us)


def htf_bias_map(df15, interval, period, fast, slow):
    """Causal HTF trend mapped onto 15m times via backward as-of join (uses only the
    last CLOSED HTF bar). Times normalized to UTC-naive for the join."""
    h = fetch(interval=interval, period=period)
    bull = (ema(h["close"], fast) > ema(h["close"], slow)).shift(1)   # completed bars only
    right = pd.DataFrame({"time": _utc_naive(h["time"]), "bull": bull.values}).dropna().sort_values("time")
    left = pd.DataFrame({"time": _utc_naive(df15["time"])}).sort_values("time")
    m = pd.merge_asof(left, right, on="time", direction="backward")
    return m["bull"].fillna(False).astype(bool).values


def confirmed_swings(df, left, right):
    """swings with the index at which they become known (idx+right)."""
    sw = swings(df, left, right)
    for s in sw:
        s["confirm"] = s["idx"] + right
    return sw


def build_obs(df):
    obs = []
    for d in displacement(df, lookback=20, mult=1.5):
        i = d["idx"]; want_bull = d["dir"] == "up"
        ob = None
        for j in range(i - 1, max(i - 6, 0), -1):
            down = df["close"].iloc[j] < df["open"].iloc[j]
            if want_bull and down: ob = j; break
            if not want_bull and not down: ob = j; break
        if ob is None: continue
        top, bot = float(df["high"].iloc[ob]), float(df["low"].iloc[ob])
        obs.append({"ob": ob, "confirm": i, "dir": "bull" if want_bull else "bear",
                    "top": top, "bot": bot, "mt": (top + bot) / 2, "tapped": False})
    return obs


def run(df, filters, rr=2.0, buf=0.0005,
        daily_bull=None, h1_bull=None, sh=None, sl=None):
    c, h, l, o = df["close"], df["high"], df["low"], df["open"]
    e50, e200 = ema(c, 50), ema(c, 200)
    rhi, rlo = h.rolling(50).max(), l.rolling(50).min()
    obs = build_obs(df)
    sh = sh if sh is not None else [s for s in confirmed_swings(df, 3, 3) if s["kind"] == "high"]
    sl = sl if sl is not None else [s for s in confirmed_swings(df, 3, 3) if s["kind"] == "low"]
    trades, pos = [], None

    def swept_low(i):
        """most recent sell-side sweep in window: prior swing low taken & reclaimed.
        returns the sweep wick low (for protected SL) or None."""
        lo = None
        for s in sl:
            if s["confirm"] >= i or s["idx"] < i - 40: continue
            P = s["price"]
            for j in range(max(s["confirm"], i - K), i + 1):
                if l.iloc[j] < P and c.iloc[j] > P:
                    lo = min(lo, float(l.iloc[j])) if lo else float(l.iloc[j])
        return lo

    def swept_high(i):
        hi = None
        for s in sh:
            if s["confirm"] >= i or s["idx"] < i - 40: continue
            P = s["price"]
            for j in range(max(s["confirm"], i - K), i + 1):
                if h.iloc[j] > P and c.iloc[j] < P:
                    hi = max(hi, float(h.iloc[j])) if hi else float(h.iloc[j])
        return hi

    def mss_up(i):
        cand = [s for s in sh if s["confirm"] < i and s["idx"] >= i - 30]
        if not cand: return False
        P = cand[-1]["price"]
        return bool((c.iloc[max(i - K, 0):i + 1] > P).any())

    def mss_down(i):
        cand = [s for s in sl if s["confirm"] < i and s["idx"] >= i - 30]
        if not cand: return False
        P = cand[-1]["price"]
        return bool((c.iloc[max(i - K, 0):i + 1] < P).any())

    for i in range(200, len(df)):
        if pos:
            t = pos
            sl_hit = l.iloc[i] <= t["sl"] if t["side"] == "long" else h.iloc[i] >= t["sl"]
            tp_hit = h.iloc[i] >= t["tp"] if t["side"] == "long" else l.iloc[i] <= t["tp"]
            if sl_hit:   t["R"] = -1.0; t["result"] = "loss"
            elif tp_hit: t["R"] = rr;   t["result"] = "win"
            if t.get("result"):
                trades.append(t); pos = None
            else:
                continue

        sess = session_ist(df["time"].iloc[i])
        if sess not in KILL:
            continue
        mid = (rhi.iloc[i] + rlo.iloc[i]) / 2
        for ob in obs:
            if ob["tapped"] or ob["confirm"] >= i: continue
            if not ((l.iloc[i] <= ob["top"]) and (h.iloc[i] >= ob["bot"])): continue
            ob["tapped"] = True
            seg = df.iloc[ob["confirm"] + 1:i]
            if ob["dir"] == "bull":
                if (seg["close"] < ob["mt"]).any(): continue
                if not (e50.iloc[i] > e200.iloc[i]): continue            # base bias
                if "mtf" in filters and not (daily_bull[i] and h1_bull[i]): continue
                if ob["top"] >= mid: continue                            # discount only
                sweep = swept_low(i)
                if "sweep" in filters and sweep is None: continue
                if "mss" in filters and not mss_up(i): continue
                entry = ob["top"]
                stop = (min(ob["bot"], sweep) if (sweep and "sweep" in filters) else ob["bot"]) * (1 - buf)
                risk = entry - stop
                if risk <= 0: continue
                pos = {"side": "long", "i": i, "time": df["time"].iloc[i], "session": sess,
                       "entry": entry, "sl": stop, "tp": entry + rr * risk}
                break
            else:
                if (seg["close"] > ob["mt"]).any(): continue
                if not (e50.iloc[i] < e200.iloc[i]): continue
                if "mtf" in filters and not ((not daily_bull[i]) and (not h1_bull[i])): continue
                if ob["bot"] <= mid: continue                            # premium only
                sweep = swept_high(i)
                if "sweep" in filters and sweep is None: continue
                if "mss" in filters and not mss_down(i): continue
                entry = ob["bot"]
                stop = (max(ob["top"], sweep) if (sweep and "sweep" in filters) else ob["top"]) * (1 + buf)
                risk = stop - entry
                if risk <= 0: continue
                pos = {"side": "short", "i": i, "time": df["time"].iloc[i], "session": sess,
                       "entry": entry, "sl": stop, "tp": entry - rr * risk}
                break
    return pd.DataFrame(trades)


def line(label, tr, days, rr):
    if tr.empty:
        print(f"  {label:38s}|  0 trades"); return
    n = len(tr); w = int((tr['result'] == 'win').sum()); wr = w / n
    netR = tr['R'].sum(); pnl = netR * RISK_USD
    pf = (w * rr) / ((n - w) or 1)
    eq = (tr['R'] * RISK_USD).cumsum(); dd = (eq - eq.cummax()).min()
    print(f"  {label:38s}| {n:3d} trades | win {wr*100:4.1f}% | PF {pf:4.2f} | "
          f"{netR:+5.1f}R=${pnl:+5.0f} | DD ${dd:4.0f} | {n/days:.2f}/day | ${pnl/days*30:+.0f}/mo")


if __name__ == "__main__":
    df = fetch(interval="15m", period="60d")
    days = (df["time"].iloc[-1] - df["time"].iloc[0]).days or 1
    daily_bull = htf_bias_map(df, "1d", "1y", 10, 30)
    h1_bull = htf_bias_map(df, "1h", "60d", 50, 200)
    shs = [s for s in confirmed_swings(df, 3, 3) if s["kind"] == "high"]
    sls = [s for s in confirmed_swings(df, 3, 3) if s["kind"] == "low"]
    print(f"=== FULL confluence backtest | gold 15m | {len(df)} candles | {days} days | kill zones only ===\n")
    ladder = [
        ("1. kill zone + OB + discount (base)", set()),
        ("2. + MTF bias (Daily & 1H agree)",     {"mtf"}),
        ("3. + liquidity sweep (protected SL)",  {"mtf", "sweep"}),
        ("4. + MSS confirmation (FULL system)",  {"mtf", "sweep", "mss"}),
    ]
    for rr in (2.0, 3.0):
        print(f"--- fixed R:R 1:{rr:g} ---")
        for label, f in ladder:
            line(label, run(df, f, rr=rr, daily_bull=daily_bull, h1_bull=h1_bull, sh=shs, sl=sls), days, rr)
        print()
