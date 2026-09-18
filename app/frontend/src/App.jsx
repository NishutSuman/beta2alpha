import { useEffect, useState, useCallback } from "react";
import { api } from "./api.js";
import Chart from "./Chart.jsx";
import { FRAMEWORK_META, SECTIONS } from "./playbook.js";

export default function App() {
  const [tab, setTab] = useState("desk");
  const [a, setA] = useState(null);
  const [err, setErr] = useState(null);
  const [cfg, setCfg] = useState({});
  const [trades, setTrades] = useState({ trades: [], stats: {} });
  const [ledger, setLedger] = useState({ entries: [], streak: 0 });
  const [updated, setUpdated] = useState(null);
  const [chk, setChk] = useState(() => loadChk());
  useEffect(() => { localStorage.setItem(chkKey(), JSON.stringify(chk)); }, [chk]);
  const chkDone = !!a && CHECKLIST.every((c) => (c.auto ? c.auto(a) : chk[c.id]));
  // chart-marking visibility (shared by the bias strip + the chart), persisted
  const [hidden, setHidden] = useState(loadHidden);
  useEffect(() => { localStorage.setItem("b2a_hidden", JSON.stringify(hidden)); }, [hidden]);
  const toggleMark = (id) => setHidden((h) => ({ ...h, [id]: !h[id] }));

  const load = useCallback(() => {
    api.analysis().then((d) => { setA(d); setUpdated(new Date()); setErr(null); }).catch((e) => setErr(String(e)));
    api.config().then(setCfg).catch(() => {});
    api.trades().then(setTrades).catch(() => {});
    api.ledger().then(setLedger).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    let timer;
    const tick = () => { timer = setTimeout(() => { load(); tick(); }, a?.in_kill_zone ? 15000 : 60000); };
    tick();
    return () => clearTimeout(timer);
  }, [load, a?.in_kill_zone]);

  return (
    <div className="wrap">
      <header className="navbar"><div className="brand">beta<span>2</span>alpha</div></header>

      <div className="layout">
        <main className="main">
          {err && (
            <div className="err">
              <b>No live data right now.</b> {String(err).includes("429") || String(err).includes("Too Many")
                ? "Twelve Data's daily limit is used up — open MT5 (its feed bypasses the limit), or wait for the quota to reset (UTC midnight)."
                : "Open MT5 so the feed pushes, or check the backend on :8011."}
              <div className="muted small">({String(err)})</div>
            </div>
          )}
          {!a && !err && <div className="muted">Loading live analysis…</div>}

          {tab === "desk" && a && (
            <>
              <BiasStrip a={a} hidden={hidden} toggleMark={toggleMark} />
              <Chart analysis={a} hidden={hidden} toggleMark={toggleMark} />
              <Narrative a={a} />
              <SignalCard a={a} onLogged={load} gateOpen={chkDone} />
              <PreTradeChecklist chk={chk} setChk={setChk} a={a} />
              <PotentialTrades a={a} />
              <Journal trades={trades} onChange={load} />
              <Honesty />
            </>
          )}
          {tab === "play" && <Playbook />}
          {tab === "me" && <Discipline ledger={ledger} onChange={load} />}
        </main>

        <Sidebar tab={tab} setTab={setTab} cfg={cfg} a={a} updated={updated} />
      </div>
    </div>
  );
}

function Sidebar({ tab, setTab, cfg, a, updated }) {
  const live = cfg.is_live;
  const fast = a?.in_kill_zone;
  return (
    <aside className="sidebar">
      <nav className="snav">
        {[["desk", "📈 Trading Desk"], ["play", "📖 Playbook"], ["me", "🎯 Discipline"]].map(([k, l]) => (
          <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>
        ))}
      </nav>

      <section className="card sb-card">
        <div className="sb-row"><span>Instrument</span><b>{a?.instrument || "XAU/USD"}</b></div>
        <div className="sb-row"><span>Price</span><b className="px">${a?.price ?? "…"}</b></div>
        <div className="sb-row"><span>Session</span>
          <b className={a?.in_kill_zone ? "up" : "muted"}>{a?.session_ist || "…"}</b></div>
        <div className="sb-time">{a?.ist_time || ""}</div>
      </section>

      <section className="card sb-card">
        <div className="sb-head">Kill Zones (IST)</div>
        {(a?.kill_zones || []).map((k, i) => (
          <div className="sb-row" key={i}><span>{k.name}</span><b className="small">{k.ist}</b></div>
        ))}
        <div className="sb-note">{fast ? "● In a kill zone — refresh 15s" : "○ Off-hours — refresh 60s"}</div>
      </section>

      <section className="card sb-card">
        <span className={"chip " + (live ? "good" : "warn")}>
          {live ? "● LIVE" : "● DELAYED"} · {(cfg.data_source || "").split(" · ")[0]}
        </span>
        <span className={"chip " + (cfg.telegram_enabled ? "good" : "off")}>
          {cfg.telegram_enabled ? "🔔 Telegram ON" : "🔕 Telegram off"}
        </span>
        {updated && <div className="sb-note">updated {updated.toLocaleTimeString()}</div>}
        {cfg.telegram_enabled && (
          <button className="mini" onClick={() => api.testAlert().then((r) =>
            alert(r.sent ? "Test alert sent ✅" : "Failed — check token/chat id"))}>send test alert</button>
        )}
      </section>
    </aside>
  );
}

function Narrative({ a }) {
  const n = a.narrative || {};
  const steps = [
    ["sweep", "Liquidity Sweep", n.sweep],
    ["mss", "Market Structure Shift", n.mss],
    ["ob", "Order Block", n.order_block],
    ["disp", "Displacement", n.displacement],
    ["fvg", "Fair Value Gap", n.fvg],
  ];
  return (
    <section className="card">
      <h3>ILDRE Narrative
        <span className={"nar-score " + (n.score >= 4 ? "up" : n.score >= 3 ? "mid" : "dn")}> {n.score ?? 0}/5</span>
        <em className="muted small"> · how complete is the institutional delivery sequence</em>
      </h3>
      <div className="nar-flow">
        {steps.map(([k, label, ok], i) => (
          <span key={k} className="nar-step">
            <span className={"nar-dot " + (ok ? "on" : "off")}>{ok ? "✓" : "○"}</span>
            <span className={ok ? "" : "muted"}>{label}</span>
            {i < steps.length - 1 && <i className="nar-arrow">→</i>}
          </span>
        ))}
      </div>
      <p className="muted small">
        {a.mss ? `Last MSS: ${a.mss.dir} @ ${a.mss.level}. ` : "No recent MSS. "}
        {a.displacement ? `Displacement ${a.displacement.dir} (${a.displacement.strength}×). ` : ""}
        A higher score = a cleaner institutional setup (sweep → MSS → OB → displacement → FVG).
      </p>
    </section>
  );
}

function BiasStrip({ a, hidden, toggleMark }) {
  const b = a.bias;
  const t = a.liquidity?.target;
  const L = a.liquidity || {};
  const item = (k, v, cls) => <div className="bs-item"><span>{k}</span><b className={cls}>{v}</b></div>;
  // a toggle-able chart-marking level: value + eye button (these are the constant markings)
  const lvl = (label, id, value, color) => (
    <div className={"bs-item lvl " + (hidden[id] ? "off" : "")}>
      <span>{label}</span>
      <span className="lvl-row">
        <b style={{ color }}>{value}</b>
        <button className="eye" title={hidden[id] ? "Show on chart" : "Hide on chart"}
          onClick={() => toggleMark(id)}>{hidden[id] ? "🙈" : "👁"}</button>
      </span>
    </div>
  );
  return (
    <section className="card bias-strip">
      {item("Daily", b.daily.toUpperCase(), b.daily === "bull" ? "up" : "dn")}
      {item("4H", (b.h4 || "—").toUpperCase(), b.h4 === "bull" ? "up" : "dn")}
      {item("1H", b.h1.toUpperCase(), b.h1 === "bull" ? "up" : "dn")}
      {item("Overall", b.overall.toUpperCase() + (b.full_aligned ? " ✓" : ""), b.overall === "bullish" ? "up" : b.overall === "bearish" ? "dn" : "mid")}
      {item("Zone", a.range.current_zone, a.range.current_zone === "discount" ? "up" : "dn")}
      {item("🎯 Destination", t ? `${t.label} ${t.price}` : "—", t ? "mid" : "muted")}
      <div className="bs-sep" />
      {lvl("Equilibrium", "eq", a.range.equilibrium, "#f0b429")}
      {L.pdh != null && lvl("PDH", "pdh", L.pdh, "#4c8dff")}
      {L.pdl != null && lvl("PDL", "pdl", L.pdl, "#4c8dff")}
      {L.pwh != null && lvl("PWH", "pwh", L.pwh, "#a855f7")}
      {L.pwl != null && lvl("PWL", "pwl", L.pwl, "#a855f7")}
    </section>
  );
}

function SignalCard({ a, onLogged, gateOpen }) {
  const s = a.live_setup || {};
  const r = s.refinement;
  const confirmed = s.status === "CONFIRMED";
  const use5m = r && r.refined_on && r.refined_on.startsWith("5M");
  const exec = use5m ? r : s;   // ILDRE: execute the 5M-refined entry when available
  const log = async () => {
    await api.createTrade({ direction: s.dir, entry: exec.entry, stop_loss: exec.stop_loss, take_profit: exec.take_profit,
      lot_size: exec.lot_size, risk_usd: exec.risk_usd, session: a.session_ist, is_demo: true,
      notes: "logged · " + (use5m ? "5M refined" : "15M") });
    onLogged();
  };
  return (
    <section className={"card signal " + (confirmed ? "live" : "")}>
      <h3>Live Setup <span className="muted small">— execute only on this</span></h3>
      <div className={"status " + (s.status || "").toLowerCase()}>{(s.status || "—").replace("_", " ")}</div>
      <p className="muted small">{s.reason || ""}</p>
      {confirmed && (
        <div className="setup-grid">
          <Kv k="Direction" v={s.dir} cls={s.dir === "long" ? "up" : "dn"} />
          <Kv k="15M Entry" v={s.entry} /><Kv k="Stop loss" v={s.stop_loss} cls="dn" />
          <Kv k="Take profit" v={s.take_profit} cls="up" /><Kv k="R:R" v={s.risk_reward} />
          <Kv k="Lot size" v={s.lot_size} /><Kv k="Risk" v={"$" + s.risk_usd} /><Kv k="Stop dist" v={s.stop_distance} />
        </div>
      )}
      {r && (
        <div className="refine">
          <div className="refine-head">🎯 5M Refined Entry <span className="muted small">· {r.refined_on}</span></div>
          {r.ob5 ? (
            <div className="setup-grid">
              <Kv k="Entry" v={r.entry} /><Kv k="Stop loss" v={r.stop_loss} cls="dn" />
              <Kv k="Take profit" v={r.take_profit} cls="up" /><Kv k="R:R" v={r.risk_reward} cls="up" />
              <Kv k="Lot size" v={r.lot_size} /><Kv k="Risk" v={"$" + r.risk_usd} />
              <Kv k="5M OB" v={`${r.ob5.bottom}–${r.ob5.top}`} /><Kv k="Stop dist" v={r.stop_distance} />
            </div>
          ) : <p className="muted small">No valid 5M PD array — execute from the 15M zone (fallback).</p>}
        </div>
      )}
      {confirmed && (
        <button className="btn" onClick={log} disabled={!gateOpen}>
          {gateOpen ? `Log this trade (demo · ${use5m ? "5M refined" : "15M"})` : "🔒 Complete the pre-trade checklist first"}
        </button>
      )}
    </section>
  );
}

// ---- pre-trade checklist gate (forces discipline before logging a trade) ----
// auto: (analysis) => bool  → engine-verified item; null → manual (human judgment)
const CHECKLIST = [
  { id: "wk", text: "Weekly + Daily liquidity marked (PWH/PWL, PDH/PDL)", auto: (a) => !!a.liquidity },
  { id: "bias", text: "HTF bias confirmed (Daily + 1H agree)", auto: (a) => a.bias.overall !== "mixed" },
  { id: "align", text: "Full HTF alignment (Daily + 4H + 1H)", auto: (a) => !!a.bias.full_aligned },
  { id: "dest", text: "Market destination / liquidity target identified", auto: (a) => !!(a.liquidity && a.liquidity.target) },
  { id: "pda", text: "HTF PD array valid (nested order block)", auto: (a) => (a.watch_levels || []).length > 0 },
  { id: "sweep", text: "Liquidity sweep complete", auto: (a) => !!(a.narrative && a.narrative.sweep) },
  { id: "ob", text: "Order block validated (high/medium grade)", auto: (a) => (a.watch_levels || []).length > 0 },
  { id: "kz", text: "In a kill zone (London / NY)", auto: (a) => !!a.in_kill_zone },
  { id: "confirm", text: "15M confirmation candle closed", auto: (a) => a.live_setup && a.live_setup.status === "CONFIRMED" },
  { id: "risk", text: "Risk ≤ 0.5% · SL & TP defined", auto: (a) => a.live_setup && a.live_setup.status === "CONFIRMED" },
  { id: "news", text: "Economic calendar checked", auto: null },
  { id: "self", text: "I am calm — not tired, sick, or emotional", auto: null },
];
function chkKey() { return "b2a_chk_" + new Date().toISOString().slice(0, 10); }
function loadChk() { try { return JSON.parse(localStorage.getItem(chkKey()) || "{}"); } catch { return {}; } }
function loadHidden() { try { return JSON.parse(localStorage.getItem("b2a_hidden") || "{}"); } catch { return {}; } }

function PreTradeChecklist({ chk, setChk, a }) {
  const val = (c) => (c.auto ? !!(a && c.auto(a)) : !!chk[c.id]);
  const done = CHECKLIST.filter(val).length;
  const pct = Math.round((done / CHECKLIST.length) * 100);
  const ok = done === CHECKLIST.length;
  return (
    <section className="card">
      <h3>Pre-Trade Checklist
        <span className={"chk-count " + (ok ? "up" : "mid")}> {done}/{CHECKLIST.length}{ok ? " ✓ cleared" : ""}</span>
        <button className="mini" style={{ float: "right" }} onClick={() => setChk({})}>reset manual</button>
      </h3>
      <div className="prog"><div className={"prog-bar " + (ok ? "ok" : "")} style={{ width: pct + "%" }} /></div>
      {CHECKLIST.map((c) => {
        const checked = val(c);
        return (
          <label key={c.id} className={"check " + (c.auto ? "auto" : "")}>
            <input type="checkbox" checked={checked} disabled={!!c.auto}
              onChange={() => !c.auto && setChk((s) => ({ ...s, [c.id]: !s[c.id] }))} />
            {c.text}
            {c.auto ? <span className={"auto-tag " + (checked ? "on" : "off")}>{checked ? "auto ✓" : "auto ✗"}</span>
              : <span className="manual-tag">manual</span>}
          </label>
        );
      })}
      <p className="muted small">Engine auto-verifies most items live; you manually confirm news &amp; your own state.
        The "Log trade" button unlocks only when all 12 are green.</p>
    </section>
  );
}

function Kv({ k, v, cls }) { return <div className="kv"><span>{k}</span><b className={cls}>{v}</b></div>; }

function PotentialTrades({ a }) {
  const zones = a.watch_levels || [];
  const [open, setOpen] = useState({});
  return (
    <section className="card">
      <h3>Potential Trades
        <em className="muted small"> · planned ahead (leading) · only setups scoring above the bar · execute on confirmation in a kill zone</em>
      </h3>
      {!zones.length && <p className="muted">No high-probability zones aligned with bias right now — stand aside.</p>}
      {zones.map((z, i) => (
        <div className="ptrade" key={i}>
          <div className="pt-head">
            <span className={"grade " + z.grade.toLowerCase()}>{z.grade} · {z.score}</span>
            <span className={"poi-tag " + (z.has_fvg ? "on" : "off")}>{z.has_fvg ? "POI · OB+FVG" : "bare OB"}</span>
            <span className={"tag " + (z.dir === "long" ? "up" : "dn")}>{z.dir}</span>
            <span className={"pt-status " + z.status}>
              {z.status === "in_zone" ? "● IN ZONE — watch for confirmation" : `○ approaching · ${z.distance_pct}% away`}
            </span>
            <span className="muted small">zone {z.bottom} – {z.top}</span>
            <button className="why" onClick={() => setOpen((o) => ({ ...o, [i]: !o[i] }))}>
              {open[i] ? "▾ why" : "ⓘ why"}
            </button>
          </div>
          {z.plan && (
            <div className="pt-grid">
              <Kv k="Entry" v={z.plan.entry} /><Kv k="Stop loss" v={z.plan.stop_loss} cls="dn" />
              <Kv k="Take profit" v={z.plan.take_profit} cls="up" /><Kv k="R:R" v={z.plan.risk_reward} />
              <Kv k="Lot" v={z.plan.lot_size} /><Kv k="Risk" v={"$" + z.plan.risk_usd} />
            </div>
          )}
          {open[i] && (
            <ul className="reasons">
              {z.reasons?.map((r, j) => <li key={j}>{r}</li>)}
              <li className="muted">Score is a confluence heuristic, not a guaranteed probability. Validated baseline ≈47% win at 1:2.</li>
            </ul>
          )}
        </div>
      ))}
    </section>
  );
}

function Journal({ trades, onChange }) {
  const st = trades.stats || {};
  const close = async (id, status) => {
    const pnl = Number(prompt(`Close as ${status} — P&L in $?`, status === "win" ? "50" : "-25"));
    if (Number.isNaN(pnl)) return;
    await api.closeTrade(id, { status, pnl_usd: pnl }); onChange();
  };
  return (
    <section className="card">
      <h3>Trade Journal <em className="muted small">(demo forward-test)</em></h3>
      <div className="stats">
        <Stat k="Trades" v={st.total ?? 0} /><Stat k="Win rate" v={(st.win_rate ?? 0) + "%"} />
        <Stat k="Net P&L" v={"$" + (st.net_pnl ?? 0)} cls={(st.net_pnl ?? 0) >= 0 ? "up" : "dn"} />
        <Stat k="Rule adherence" v={(st.rule_adherence ?? 0) + "%"} />
      </div>
      <table>
        <thead><tr><th>Dir</th><th>Entry</th><th>SL</th><th>TP</th><th>Lot</th><th>Status</th><th>P&L</th><th></th></tr></thead>
        <tbody>
          {trades.trades?.map((t) => (
            <tr key={t.id}>
              <td className={t.direction === "long" ? "up" : "dn"}>{t.direction}</td>
              <td>{t.entry}</td><td>{t.stop_loss}</td><td>{t.take_profit}</td><td>{t.lot_size}</td>
              <td><span className={"tag " + t.status}>{t.status}</span></td>
              <td className={t.pnl_usd >= 0 ? "up" : "dn"}>{t.pnl_usd}</td>
              <td>{t.status === "open" && (<span className="acts">
                <a onClick={() => close(t.id, "win")}>win</a><a onClick={() => close(t.id, "loss")}>loss</a></span>)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function Stat({ k, v, cls }) { return <div className="stat"><span>{k}</span><b className={cls}>{v}</b></div>; }

function Honesty() {
  return (
    <section className="card muted small note">
      <h3>The honest rules</h3>
      <ul>
        <li>Leading = zones + plans shown ahead of time; you still execute only on a confirmation candle.</li>
        <li>Kill zone only, with the trend. Risk ≤0.5%. Lot size is survival, not speed.</li>
        <li>Scores are confluence heuristics, not guaranteed probabilities. ~47% win at 1:2 is the validated baseline.</li>
      </ul>
    </section>
  );
}

function PlaybookBlock({ b }) {
  if (b.type === "p") return <p className="pb-p">{b.text}</p>;
  if (b.type === "flow")
    return (
      <div className="pb-block">
        {b.title && <div className="pb-bt">{b.title}</div>}
        <div className="pb-flow">{b.steps.map((s, i) => (
          <span key={i} className="pb-step">{s}{i < b.steps.length - 1 && <i className="pb-arrow">→</i>}</span>
        ))}</div>
      </div>
    );
  if (b.type === "sub")
    return (
      <div className="pb-block">
        <div className="pb-bt">{b.title}</div>
        <ul className="pb-list">{b.items.map((x, i) => <li key={i}>{x}</li>)}</ul>
      </div>
    );
  if (b.type === "check")
    return (
      <ul className="pb-check">{b.items.map((x, i) => <li key={i}><span className="cbox">☐</span>{x}</li>)}</ul>
    );
  return (
    <div className="pb-block">
      {b.title && <div className="pb-bt">{b.title}</div>}
      <ul className="pb-list">{b.items.map((x, i) => <li key={i}>{x}</li>)}</ul>
    </div>
  );
}

function PlaybookSection({ s }) {
  const [open, setOpen] = useState(!!s.open);
  return (
    <section className={"card pb-sec " + (s.tag === "build" ? "signal live" : "")}>
      <button className="pb-head" onClick={() => setOpen(!open)}>
        <span className="pb-caret">{open ? "▾" : "▸"}</span>
        <span className="pb-title">{s.title}</span>
        <span className={"tag pb-tag " + s.tag}>{s.tag}</span>
      </button>
      {open && <div className="pb-body">{s.blocks.map((b, i) => <PlaybookBlock key={i} b={b} />)}</div>}
    </section>
  );
}

function Playbook() {
  return (
    <>
      <section className="card pb-intro">
        <h3>{FRAMEWORK_META.title} <span className="tag win">{FRAMEWORK_META.version}</span></h3>
        <p className="muted small">{FRAMEWORK_META.subtitle} · the full mentor methodology · the engine automates a subset (see ⚙️)</p>
      </section>
      {SECTIONS.map((s) => <PlaybookSection key={s.id} s={s} />)}
    </>
  );
}

function Discipline({ ledger, onChange }) {
  const today = ledger.entries?.[0];
  const [f, setF] = useState({ sleep: false, body: false, skill: false, trading_rules: false });
  useEffect(() => {
    if (today) setF({ sleep: today.sleep, body: today.body, skill: today.skill, trading_rules: today.trading_rules });
  }, [ledger]);
  const toggle = async (k) => { const next = { ...f, [k]: !f[k] }; setF(next); await api.saveLedger(next); onChange(); };
  const boxes = [["sleep", "🌙 Slept on time (keystone)"], ["body", "💪 Moved my body"],
    ["skill", "📚 Upskilled 1 hour"], ["trading_rules", "🎯 Followed my trading rules"]];
  return (
    <>
      <section className="card">
        <h3>Today's Discipline <span className="streak">🔥 {ledger.streak}d streak</span></h3>
        {boxes.map(([k, label]) => (
          <label key={k} className="check"><input type="checkbox" checked={!!f[k]} onChange={() => toggle(k)} /> {label}</label>
        ))}
      </section>
      <section className="card">
        <h3>Last 30 days</h3>
        <div className="grid-days">
          {(ledger.entries || []).map((e) => {
            const kept = [e.sleep, e.body, e.skill, e.trading_rules].filter(Boolean).length;
            return <span key={e.id} className={"day " + (kept === 4 ? "full" : kept > 0 ? "some" : "none")} title={`${e.day}: ${kept}/4`} />;
          })}
        </div>
        <p className="muted small">Green = all 4 · amber = some · red = none. Never break the chain twice.</p>
      </section>
    </>
  );
}
