# MT5 live data feed — setup (free, exact broker data)

The script `beta2alpha_feed.mq5` runs inside your MetaTrader 5 and pushes live XAU/USD
candles (5m, 15m, 1h, 1d) to the beta2alpha backend. It **places no trades** — it only
reads prices and sends them. The dashboard then uses your *exact broker feed*, with deep
history, in real time and at zero cost.

> ⚠️ Confirm with the5ers that a **data-only script** (no trading) is allowed before running it.

## One-time setup

1. **Copy the script in:**
   - In MT5: **File → Open Data Folder** → open `MQL5` → `Experts`.
   - Copy `beta2alpha_feed.mq5` (from this folder) into that `Experts` folder.

2. **Compile it:**
   - Open **MetaEditor** (in MT5: Tools → MetaQuotes Language Editor), find `beta2alpha_feed`
     in the Navigator, open it, press **Compile (F7)**. It should say "0 errors".

3. **Allow the backend URL:**
   - MT5 → **Tools → Options → Expert Advisors**
   - Tick **"Allow WebRequest for listed URL"** and add:  `http://127.0.0.1:8011`

4. **Turn on Algo Trading:**
   - Click the **Algo Trading** button in the MT5 toolbar (it does NOT trade — MT5 just
     requires this for EAs to run).

5. **Attach to a gold chart:**
   - Open an **XAUUSD** chart (any timeframe).
   - Drag `beta2alpha_feed` from the Navigator onto the chart.
   - In the dialog, tick **"Allow Algo Trading"** → OK.
   - If your broker's gold symbol isn't `XAUUSD`, just attach it to whatever gold chart you
     use — the script defaults to the chart's symbol. (Or set the `FeedSymbol` input.)

You'll see a smiley face ☺ on the chart (EA running). The app's data chip flips to
**"● LIVE DATA · MetaTrader 5 · live (your broker)"** within ~10 seconds.

## Requirements
- The beta2alpha **backend must be running** on the same Mac (port 8011).
- **MT5 must stay open** for live data to flow. When it's closed, the app falls back to
  Twelve Data / yfinance automatically (no breakage).

## Inputs (optional, in the EA dialog)
- `FeedSymbol` — blank = use chart symbol; or set e.g. `XAUUSD`
- `HistoryBars` — candles per timeframe to send (default 1500)
- `PushSeconds` — push interval (default 10s)

## Troubleshooting
- **"WebRequest failed err=4060/5203"** in the Experts log → the URL isn't allowed; redo
  step 3 (must be exactly `http://127.0.0.1:8011`).
- **No data in app** → check the Experts/Journal tab in MT5 for errors; confirm the backend
  is running (`curl http://127.0.0.1:8011/api/health`).
- **Wrong prices** → make sure you attached to the correct gold symbol.
