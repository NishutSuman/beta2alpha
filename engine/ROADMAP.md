# beta2alpha trading engine — build roadmap

Powers the live dashboard (at-desk) + Telegram alerts (away). One brain, two faces.
Strategy source of truth: `../strategy/STRATEGY-SPEC.md`.

## Phase 1 — engine core  ▸ IN PROGRESS
- [x] `data.py` — free gold data via yfinance (Daily/1H/15m/5m), normalized candles
- [x] `structures.py` — swings, displacement, FVG (filled/unfilled), order blocks +
      0.5 mean-threshold validity, premium/discount, body-close break
- [ ] `bias.py` — daily grab+close engine, OHLC pattern (O-L-H-C / O-H-L-C), dealing range
- [ ] `marketstructure.py` — ITH/ITL/STH/STL, MSS (3-candle swing, 1H), swing failure
- [ ] `fractal.py` — multi-timeframe alignment (Daily→1H→15m→5m agree?)
- [ ] `setup.py` — combine the 4 pillars → a scored setup (entry/SL/TP + lot size)

## Phase 2 — backtest & validate  ▸ NEXT
- [ ] Dukascopy deep historical intraday loader (replace yfinance limits)
- [ ] backtester over 1–2y XAU/USD → win-rate, expectancy, profit factor, max drawdown
- [ ] risk model: 0.5% risk/trade, min 1:2 R:R, $30–50/day target, $50/day max loss, ≤2 trades/day
- [ ] GATE: only proceed to live if the edge survives this honestly

## Phase 3 — delivery  ▸ AFTER PHASE 2 PASSES
- [ ] OANDA demo live feed
- [ ] Morning Brief generator (bias + levels + which kill-zone to watch)
- [ ] Local live dashboard (chart + OB/FVG zones + fractal MTF panel + setup highlight + sound)
- [ ] Telegram bot (lightweight alerts when away)
- [ ] the5ers written-approval email for a self-owned, alert-only, manual-execution tool

## Session windows (XAU/USD, IST, summer)
- London kill zone ≈ 12:30–3:30 PM IST   |   NY kill zone ≈ 5:30–8:30 PM IST
- IST morning = quiet (Asian) → for PREP + life, not execution
- Design: morning brief (you, 20 min) → agent watches kill zones → alert → 2-min manual execute

## Run it
    .venv/bin/python engine/data.py        # show multi-timeframe gold pulls
    .venv/bin/python engine/structures.py  # detectors on live 1H gold
