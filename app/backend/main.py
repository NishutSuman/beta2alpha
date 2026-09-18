"""
beta2alpha API — bridges the Python signal engine + Postgres journal to the React app.

Run:  cd app/backend && ../../.venv/bin/uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
import os
import sys
import datetime as dt
from typing import Optional


def _load_dotenv():
    """Minimal .env loader (no extra dependency) — reads KEY=VALUE lines into os.environ."""
    path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(path):
        return
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

# make the engine importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine"))
import live_signal  # noqa: E402
import market_data  # noqa: E402
import telegram_notify  # noqa: E402
from db import init_db, get_session, Trade, LedgerEntry  # noqa: E402

app = FastAPI(title="beta2alpha API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

_cache = {"at": None, "data": None}

init_db()   # create tables at import (Postgres or SQLite fallback)
telegram_notify.start_background(60)   # alert checker (no-op until Telegram is configured)


@app.get("/api/health")
def health():
    return {"ok": True, "time": dt.datetime.now(dt.UTC).isoformat()}


@app.get("/api/config")
def config():
    """Tells the UI what's wired: live data source + telegram status."""
    return {
        "data_source": market_data.source_label(),
        "is_live": market_data.is_live(),
        "telegram_enabled": telegram_notify.configured(),
    }


class Mt5Push(BaseModel):
    tf: str
    candles: list


@app.post("/api/mt5/candles")
def mt5_candles(p: Mt5Push):
    """Receive live candles pushed from the MT5 feed script (beta2alpha_feed.mq5)."""
    try:
        n = market_data.push_mt5(p.tf, p.candles)
        return {"ok": True, "tf": p.tf, "stored": n}
    except Exception as e:
        raise HTTPException(400, f"mt5 push error: {e}")


@app.get("/api/candles")
def candles(tf: str = "15m", count: int = 200):
    try:
        return live_signal.get_candles(tf=tf, count=count)
    except Exception as e:
        raise HTTPException(503, f"candles error: {e}")


@app.post("/api/test-alert")
def test_alert():
    """Send a test Telegram message to confirm your bot token + chat id work."""
    ok = telegram_notify.send("✅ beta2alpha test alert — your Telegram is wired up.")
    return {"sent": ok, "configured": telegram_notify.configured()}


@app.get("/api/analysis")
def analysis(account: float = 5000.0, risk_pct: float = 0.5, refresh: bool = False):
    """Live signal snapshot. Cached 60s to avoid hammering the data source."""
    now = dt.datetime.now(dt.UTC)
    if (not refresh and _cache["data"] and _cache["at"]
            and (now - _cache["at"]).total_seconds() < 30):
        return _cache["data"]
    try:
        data = live_signal.get_analysis(account=account, risk_pct=risk_pct)
    except Exception as e:  # data source hiccup -> clear error for the UI
        raise HTTPException(503, f"signal engine error: {e}")
    _cache.update(at=now, data=data)
    return data


# ----------------------------------------------------------------- trade journal
class TradeIn(BaseModel):
    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    lot_size: float
    risk_usd: float = 0
    session: str = ""
    rule_followed: bool = True
    is_demo: bool = True
    notes: str = ""


class TradeClose(BaseModel):
    status: str       # win / loss / be
    pnl_usd: float


@app.get("/api/trades")
def list_trades(db: Session = Depends(get_session)):
    rows = db.scalars(select(Trade).order_by(Trade.opened_at.desc())).all()
    trades = [t.__dict__ | {} for t in rows]
    for t in trades:
        t.pop("_sa_instance_state", None)
    # quick stats for the dashboard
    closed = [t for t in trades if t["status"] in ("win", "loss", "be")]
    wins = [t for t in closed if t["status"] == "win"]
    stats = {
        "total": len(trades), "closed": len(closed), "open": len(trades) - len(closed),
        "wins": len(wins), "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else 0,
        "net_pnl": round(sum(t["pnl_usd"] for t in closed), 2),
        "rule_adherence": round(sum(t["rule_followed"] for t in trades) / len(trades) * 100, 1) if trades else 0,
    }
    return {"trades": trades, "stats": stats}


@app.post("/api/trades")
def create_trade(t: TradeIn, db: Session = Depends(get_session)):
    row = Trade(**t.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id}


@app.patch("/api/trades/{trade_id}/close")
def close_trade(trade_id: int, c: TradeClose, db: Session = Depends(get_session)):
    row = db.get(Trade, trade_id)
    if not row:
        raise HTTPException(404, "trade not found")
    row.status = c.status; row.pnl_usd = c.pnl_usd
    db.commit()
    return {"ok": True}


# ----------------------------------------------------------------- discipline ledger
class LedgerIn(BaseModel):
    day: Optional[dt.date] = None
    sleep: bool = False
    body: bool = False
    skill: bool = False
    trading_rules: bool = False
    regret_note: str = ""


@app.get("/api/ledger")
def get_ledger(db: Session = Depends(get_session)):
    rows = db.scalars(select(LedgerEntry).order_by(LedgerEntry.day.desc()).limit(30)).all()
    out = []
    for r in rows:
        d = r.__dict__.copy(); d.pop("_sa_instance_state", None); out.append(d)
    # current streak (a day counts if any box is true)
    streak = 0
    for r in rows:
        if r.sleep or r.body or r.skill or r.trading_rules:
            streak += 1
        else:
            break
    return {"entries": out, "streak": streak}


@app.post("/api/ledger")
def upsert_ledger(e: LedgerIn, db: Session = Depends(get_session)):
    day = e.day or dt.date.today()
    row = db.scalar(select(LedgerEntry).where(LedgerEntry.day == day))
    if not row:
        row = LedgerEntry(day=day); db.add(row)
    row.sleep, row.body, row.skill = e.sleep, e.body, e.skill
    row.trading_rules, row.regret_note = e.trading_rules, e.regret_note
    db.commit()
    return {"ok": True, "day": str(day)}
