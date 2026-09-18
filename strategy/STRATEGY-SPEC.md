# Strategy Spec — Nilesh's 4-Pillar ICT/SMC Method (XAU/USD)

> Source: 3 YouTube lectures by mentor **Nilesh** (handle "Gwaidier", ~500k subs):
> - **Lec #11 "Fractal Nature"** (5h) — multi-timeframe / fractal logic
> - **Lec #9 "Bias"** (~2h) — direction + target engine
> - **Lec #7 "Market Structure"** (~1.5h) — swings, blocks, break confirmation
>
> Captions pulled via yt-dlp, cleaned, and rule-extracted. This is the consolidated,
> codeable spec. Method applies to Gold, US30, DAX, forex, BTC (mentor's own words).

---

## THE THESIS — 4 interdependent pillars
**Fractal Nature → Bias → Market Structure → Liquidity.** All four must align or the
trade fails. The edge isn't one setup — it's reading the same picture across timeframes
until all four agree. ~90% of order blocks are fake; the confluence filtering is the point.

---

## 1. TIMEFRAME ROLES (the skeleton)
| Tier | Timeframes | Job |
|------|-----------|-----|
| **HTF** | Monthly / Weekly / Daily | Bias & direction, main POI, External Range Liquidity (ERL) target |
| **Mid** | 4H + 1H | Trade point, structure mapping (ITH/ITL), MSS, pullback/continuation zones |
| **LTF** | 1m–15m (≤30m) | Internal Range Liquidity (IRL) build, execution / entry |

- **Always analyze HTF → LTF** (Monthly→Daily→…→1m). Never drift LTF→HTF — that's the #1 cause of wrong bias and unexplained losses.
- A Daily POI is *executed* on the 1H/LTF, not traded on Daily itself. Not every TF is tradeable.
- A POI on 5m with nothing behind it on Daily/4H/1H = **fake (trap)**.
- **Fractal FVG chain:** 1m runs → 5m FVG → 15m → 30m/1H → 4H/Daily. Same pattern recurs at every scale (a 15m W-pattern has a smaller W on 1m in the same zone).

---

## 2. PILLAR — BIAS (direction + how far)
Bias = which direction price goes **and how far (the target)**. It's the master filter:
once known, you only hunt entries in that direction. Built from **3 components combined**:

### 2a. Time & Price Theory (the OHLC candle engine)
Every Daily/Weekly/Monthly candle prints one of two patterns (open → fake momentum → real momentum → close):
- **Bullish candle = O-L-H-C** (open, fake LOW, expand UP, close). → **buy below the open, sell at the high.**
- **Bearish candle = O-H-L-C** (open, fake HIGH, expand DOWN, close). → **sell above the open, book at the low.**

### 2b. Daily Bias (the "grab + close" engine — most concrete, codeable rule)
- Grab **previous-day LOW** liquidity **& close UP** → next day **bullish** (gap-up, or if flat it hunts the previous-day HIGH).
- Grab **previous-day HIGH** liquidity **& close DOWN** → next day **bearish** (gap-down, or hunts previous-day LOW).
- **Continuation vs reversal:** close *beyond* a level in the *same* direction without a clean grab-and-reverse = **continuation** (bias continues). Grab + close on the *opposite* side = **reversal** (bias flips).
- **Gap detection:** no order block between price and target → expect **gap-up/down**. Order block present → **flat open**, price comes to tap it first.

### 2c. Dealing Range (mentor calls it the single most powerful ICT tool)
- Forms after liquidity on **both sides** is hunted (sell-side then buy-side, or vice-versa). The leg between the two hunts = the **dealing range**.
- Apply premium/discount inside it: **buy at discount → target range HIGH; sell at premium → target range LOW.**
- Gives bias for the **next 2–4 weeks** at once. New range confirmed by a **3-candle formation**.

### Bias change / flip
Overall bias flips only when (on 1H/4H): **ITL breaks → DOWN; ITH breaks → UP**, OR an opposite-direction **order block** forms + **MSS** (swing break) + close beyond prev high/low. STL/STH breaks = **temporary** (pullback, ~50/50) — not a flip.

### Pullback vs reversal
While the HTF (e.g. monthly) target is unmet, counter-moves are **just corrections** — even an 800-pt drop. Counter-direction bias is **weak**; trading it = trap. A real reversal needs the swing break / MSS confirmation above.

---

## 3. PILLAR — MARKET STRUCTURE
- **Swing Failure (= functional CHoCH / trend flip):** price breaks the prior **high** but fails to break the prior **higher-low**, then goes up → bias now **UP** (mirror for down). This is the first confirmation before a Mitigation Block.
- **ITH/ITL:** a swing with a swing on its **left AND right** legs, mid swing highest (ITH) / lowest (ITL). Confirmed only when both legs exist. HTF STL/STH automatically become **15m ITH/ITL**; intermediate IT points in between = traps.
- **MSS (Market Structure Shift):** a **3-candle swing** taken against the prior trend. **Read on 1H** (5m/15m give false shifts that trap twice). MSS alone ≠ reversal — needs HTF POI rejection + post-MSS structure.
- **Break confirmation = BODY CLOSE** beyond the level (not a wick).
- **IDM / Inducement:** the small pullback/liquidity pocket just inside structure created to trap retail. In a downtrend it sits above the OB used for sells; after IDM is taken, price is "induced" to the OB. May be invisible on current TF — drop a TF to see it.

---

## 4. PILLAR — LIQUIDITY
- **Liquidity = clustered stop-losses.** Fractal — exists on every timeframe.
- **ERL (External):** HTF swings + **Previous-Day High / Previous-Day Low** (also prev-week/month H/L). Marked both sides; only **one** side breaks per bias.
- **IRL (Internal):** LTF (1m–30m) liquidity inside the HTF range.
- **Hard rule: price never takes external liquidity without first taking internal liquidity.**
- **Types to mark:** equal/clean highs & lows, swing liquidity, trendline liquidity (retail trap), liquidity pools (trendline + swing + pool coincide = major → strong move).
- **Trigger sequence:** liquidity grab → **displacement** (proof big players entered) → displacement leaves an OB/FVG → tap → spike. **No displacement after a grab = no trade.**
- **A POI with no liquidity in front of it is worthless** — it will break.

---

## 5. POI / ORDER BLOCKS / FVG — marking & validity
- **POI = Order Block + FVG** (strongest when both coincide, and across 15m/30m/4H).
- **Order Block = the last opposite-color candle-run before the move:** to **sell**, mark the last **buying** candle(s); to **buy**, the last **selling** candle(s). Can be 1 to 5+ consecutive same-color candles. Inside bars inherit the mother candle's type.
- **Mean Threshold (MT) = 0.5 of the order block.** Entry refines to the MT.
- **Validity rule (the load-bearing filter):** a block is valid only if **no body closes beyond its mean threshold (50%)**. Body close beyond 50% = **trap (~90% fail)**; body stays within MT = **~99% works**. It's the **wick** that matters, not candle color.
- **Premium/Discount (fib = only 0, 0.5, 1):** above 0.5 = Premium (sell zone), below = Discount (buy zone), 0.5 = Equilibrium. **Buy only in discount, sell only in premium — in bias direction.** A perfect OB on the wrong side of equilibrium still fails.
- **Block types:**
  - **Mitigation Block** — takes ONE liquidity side, taps, continues (continuation).
  - **Breaker Block** — takes BSL (high) then SSL (low), then reverses; entry = last opposite candle; SL above/below block.
  - **Rejection Block** — wick-based; needs **≥2 wicks on LTF (1m–3m)**, **1 wick enough on HTF (≥30m)**; tight SL; counter-trend = small TP only.
  - **Reclaim Block** — needs HTF POI tap → **MSS + displacement** → works **sequentially** (multiple tradeable blocks; example gave 4 trades). Body must close above prior swing to activate next.
- **Unicorn / overlap (highest probability):** when an OB **wick overlaps an unfilled FVG**, use **only that wick** as the zone. If the FVG is already filled, use the full OB + its 50%.
- **Double confirmation** (e.g. Mitigation Block + FVG, or OB + FVG) = strong POI → take it; otherwise skip.
- **Every block needs an HTF reason** (HTF POI or a PDH/PDL/weekly/monthly liquidity grab). No reason → no trade.

---

## 6. THE ENTRY SEQUENCE (assembled master checklist)
1. **HTF bias** defined (OHLC pattern + daily grab/close + dealing range; direction *and* target). Analyze HTF→LTF.
2. Identify the **HTF POI / ERL target** in the bias direction; pick the **LAST POI** (skip ones with no rejection/support — price runs straight through them to the deeper one).
3. **Liquidity grab** confirmed at the POI (internal liquidity hunted first).
4. **Displacement** after the grab → leaves OB/FVG (big-player proof).
5. **MSS** confirmation on 1H; **body close** beyond the broken level.
6. **Pullback** to the last POI (located on 1H/4H) — you must know the **pullback END** before entering. No end = no entry.
7. **Drop to LTF (5m/1m)**, confirm OB/FVG validity (no body close beyond MT; ≥2 wicks if rejection block) → **execute**. Refine entry to the MT / overlapping wick.
8. **Stop loss:** behind structure — above the ITH / OB (shorts), below the ITL / OB (longs). Rejection blocks = tight SL. Worked example used **previous-day low/high** as SL.
9. **Take profit:** spike trade → **next-higher-TF POI** (enter 5m→target 15m; 15m→30m/1H). Positional → HTF ERL / opposite POI / dealing-range boundary. **With-trend = big TP; counter-trend = small TP.**
10. **Reset** the fractal system at each reset point before hunting the next trade.

---

## 7. NO-TRADE FILTERS (stand aside when…)
- All timeframes in **range** (Daily ranging → everything ranges → only SLs get hit).
- POI with **no liquidity** in front of it / **no displacement** after a grab.
- Trading **against HTF bias**, or trading **internal / mid-pullback** structure.
- Wrong side of **equilibrium** (buy in premium / sell in discount).
- Block invalid: **body closed beyond the 50% mean threshold**.
- **Fake structure / inducement:** weak overlapping candles (each ≥~50% of prior), "no power."
- Entering a pullback **without knowing its end point**.
- Re-trying same direction after the target zone is **done** (reset instead).
- Small reward-to-risk setups (e.g. 100–150 pt target with a large SL) — skip.

---

## 8. CODEABILITY VERDICT (engine vs human)
**Objective → fully codeable detection+alert engine:**
- Swing detection; ITH/ITL/STH/STL labeling; swing failure
- MSS / BOS detection (3-candle swing break, **body-close** confirmation) on 1H
- FVG detection (+ 1m→5m→15m→1H chain); order block detection (last opposite-candle run, inside-bar handling)
- Mean-threshold (0.5) validity test (body-close-beyond filter)
- Equal highs/lows, trendline liquidity, liquidity pools, PDH/PDL
- Liquidity sweep/grab + displacement (momentum candle) detection
- Premium/Discount (fib equilibrium) zoning
- Daily-bias grab+close engine; dealing-range construction; gap-up/down prediction
- Multi-timeframe alignment check

**Subjective → assist, human confirms:**
- *Which* POI is "the last/main" one (engine ranks 2–3 candidates)
- Is displacement / rejection "strong enough"
- Real structure vs. deliberately-built fake (inducement)
- Significance of a given liquidity pool

**Conclusion:** Build a tool that does the objective heavy-lifting across timeframes and
**alerts** when all 4 pillars align. Final discretionary call stays with Nishut — which is
also exactly what keeps us inside the5ers' rules (analysis + alert, manual execution).

---

## 9. NOTES & OPEN ITEMS FOR XAU/USD
- Mentor's examples are often Indian indices (Bank Nifty) with a 6h session + premium decay; but he **also trades forex/gold** (forex live stream daily 6 PM IST = NY session). His logic is market-agnostic by his own statement.
- For XAU/USD specifically we should add: a **session filter** (London / NY kill-zones), and define our own **fixed risk model** (he gives no fixed R:R; cites 1:3–1:5 with-trend, small counter-trend).
- Deferred topics he references for later: Draw-on-Liquidity, Judas swing, full Accumulation-Manipulation-Distribution, Swing/Fib projection. Not required for v1.
</content>
