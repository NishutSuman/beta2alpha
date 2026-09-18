# beta2alpha — Trading Desk (Phase 3 MVP)

A dashboard that surfaces the ONE validated edge live, with confirmation candle,
entry/SL/TP, and risk-managed lot sizing — plus a demo trade journal and the
discipline ledger. Honest scope: ~2–4 setups/week, ~47% win at 1:2. **Not a sure-shot.**

```
React (Vite) ──/api proxy──> FastAPI ──> Python engine (validated edge)
                                 └──> Postgres / SQLite (journal + ledger)
```

## Run it

**1. Backend** (from repo root):
```bash
cd app/backend
../../.venv/bin/uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```
Uses SQLite by default (zero setup). To use Postgres:
```bash
createdb beta2alpha
export DATABASE_URL="postgresql+psycopg2://$(whoami)@localhost:5432/beta2alpha"
# then start uvicorn as above
```

**2. Frontend** (separate terminal):
```bash
cd app/frontend
npm install      # first time only
npm run dev      # http://localhost:5173
```

## What the dashboard shows
- **Bias & Zone** — Daily + 1H trend, range equilibrium, premium/discount
- **Live Setup** — stand-aside / watching / forming / CONFIRMED (entry, SL, TP, lot, risk)
- **Watch Levels** — 15m order blocks nested inside 1H order blocks, aligned with bias
- **Trade Journal** — log demo trades from the live setup, close as win/loss, see win-rate / net P&L / rule-adherence
- **Discipline Ledger** — daily sleep/body/skill/trading-rules + streak

## API
- `GET  /api/analysis?account=5000&risk_pct=0.5` — live signal snapshot (cached 60s)
- `GET/POST /api/trades`, `PATCH /api/trades/{id}/close` — demo journal
- `GET/POST /api/ledger` — discipline ledger

## Going REAL-TIME — needs your free data key
Without this it runs on yfinance (~15min delayed).

**Twelve Data (recommended — works from India, free, no broker account):**
1. Sign up free at https://twelvedata.com → copy your **API key** (free tier: 8 calls/min, 800/day).
2. Set env var, restart backend:
```bash
export TWELVE_DATA_API_KEY="your_key"
```
The data-source chip flips to "● LIVE DATA · Twelve Data · real-time". Caching keeps us
within the free limits (15m fetched ≤1/min, 1h ≤1/5min, daily ≤1/hr).

**OANDA practice (alternative, NOT available in India):** set `OANDA_API_TOKEN`,
`OANDA_ACCOUNT_ID`, `OANDA_ENV=practice`.

**Future: exact broker data from your the5ers MT5** — a small MT5 script can export live
prices to our backend so signals use the same feed you trade on (no third-party). Bigger
build; do later if Twelve Data's gold feed differs from your broker's.

## Telegram alerts — needs your bot token + chat id
1. In Telegram, message **@BotFather** → `/newbot` → copy the **bot token**.
2. Message **@userinfobot** → copy your numeric **chat id**.
3. Set env vars and restart the backend:
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-..."
export TELEGRAM_CHAT_ID="123456789"
```
A background checker polls every 60s and sends one alert per confirmed kill-zone setup.
Test it from the UI ("send test alert") or `curl -XPOST localhost:8011/api/test-alert`.

## Data source (summary)
Live snapshot: OANDA (if token set) else yfinance (~15m delayed). Backtest/validation
data is Dukascopy (see `../engine`).

## Honest reminders (baked into the UI)
Trade only in a kill zone, with the trend, after a confirmation candle. Risk small —
lot size is survival, not speed. Career is the recovery lever; this is a slow supplement.
