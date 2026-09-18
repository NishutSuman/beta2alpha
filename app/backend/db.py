"""Database layer — Postgres (via DATABASE_URL) with a SQLite fallback so it runs today."""
import os
import datetime as dt
from sqlalchemy import create_engine, String, Float, Integer, DateTime, Date, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# Set DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/beta2alpha to use Postgres.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(os.path.dirname(__file__), "beta2alpha.db"),
)

engine = create_engine(DATABASE_URL, echo=False,
                       connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


class Trade(Base):
    """A demo (or live) trade taken on the validated edge — the forward-test journal."""
    __tablename__ = "trades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opened_at: Mapped[dt.datetime] = mapped_column(DateTime, default=lambda: dt.datetime.now(dt.UTC))
    instrument: Mapped[str] = mapped_column(String(16), default="XAU/USD")
    direction: Mapped[str] = mapped_column(String(8))            # long / short
    session: Mapped[str] = mapped_column(String(16), default="")  # London-kill / NY-kill
    entry: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit: Mapped[float] = mapped_column(Float)
    lot_size: Mapped[float] = mapped_column(Float)
    risk_usd: Mapped[float] = mapped_column(Float, default=0)
    rule_followed: Mapped[bool] = mapped_column(Boolean, default=True)  # did I follow the system?
    status: Mapped[str] = mapped_column(String(12), default="open")     # open / win / loss / be
    pnl_usd: Mapped[float] = mapped_column(Float, default=0)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class LedgerEntry(Base):
    """Daily discipline ledger (sleep/body/skill/trading-rules) — the beta2alpha keystone."""
    __tablename__ = "ledger"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[dt.date] = mapped_column(Date, unique=True)
    sleep: Mapped[bool] = mapped_column(Boolean, default=False)
    body: Mapped[bool] = mapped_column(Boolean, default=False)
    skill: Mapped[bool] = mapped_column(Boolean, default=False)
    trading_rules: Mapped[bool] = mapped_column(Boolean, default=False)
    regret_note: Mapped[str] = mapped_column(Text, default="")


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
