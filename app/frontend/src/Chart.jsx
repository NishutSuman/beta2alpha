import { useEffect, useRef, useState, useMemo } from "react";
import { createChart, CrosshairMode, LineStyle } from "lightweight-charts";

// lightweight-charts renders UNIX timestamps in UTC. Shift by IST offset so the axis,
// crosshair, and OB-box anchors all display in IST (Asia/Kolkata = UTC+5:30).
const IST_OFFSET = 5.5 * 3600;
const TF_COUNT = { "5m": 500, "15m": 1500, "1h": 1000 };   // candles to load per timeframe

// Live 15m chart. Candles auto-refresh. Each marking (OB zones + equilibrium + a confirmed
// setup) can be shown/hidden from the side panel, which also shows each zone's formation time.
export default function Chart({ analysis, hidden, toggleMark }) {
  const elRef = useRef(null);
  const overlayRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const linesRef = useRef([]);
  const zonesRef = useRef([]);
  const [tf, setTf] = useState("15m");   // chart view timeframe (analysis stays on 15m)
  const tfRef = useRef(tf);
  tfRef.current = tf;                     // keep current tf available inside syncBands

  // build the list of markings from the latest analysis
  const markings = useMemo(() => {
    if (!analysis) return [];
    const out = [];
    if (analysis.range?.equilibrium)
      out.push({ id: "eq", kind: "eq", label: "Equilibrium", price: analysis.range.equilibrium });
    // external liquidity (ILDRE): PWH/PWL, PDH/PDL — destination highlighted
    const liq = analysis.liquidity || {};
    const tgt = liq.target;
    [["pwh", "PWH", "pw", "pwh_time"], ["pwl", "PWL", "pw", "pwl_time"],
     ["pdh", "PDH", "pd", "pdh_time"], ["pdl", "PDL", "pd", "pdl_time"]].forEach(([k, lab, grp, tk]) => {
      if (liq[k]) out.push({ id: k, kind: "liq", label: lab, price: liq[k], grp,
        top: liq[k], bottom: liq[k], startTime: liq[tk], isTarget: tgt && tgt.label === lab });
    });
    (analysis.watch_levels || []).slice(0, 5).forEach((w) => {
      out.push({
        id: `${w.dir}-${w.start_time}-${w.top}`, kind: "zone", dir: w.dir,
        top: w.top, bottom: w.bottom, startTime: w.start_time,
        label: `${w.dir === "long" ? "▲" : "▼"} OB ${w.bottom}–${w.top}`,
      });
    });
    // unfilled FVGs (imbalance)
    (analysis.fvgs || []).forEach((f) => {
      out.push({ id: `fvg-${f.start_time}-${f.top}`, kind: "fvg", dir: f.dir,
        top: f.top, bottom: f.bottom, startTime: f.start_time, label: `FVG ${f.bottom}–${f.top}` });
    });
    // market structure shift
    if (analysis.mss)
      out.push({ id: "mss", kind: "mss", label: `MSS ${analysis.mss.dir} ${analysis.mss.level}`,
        price: analysis.mss.level, dir: analysis.mss.dir });
    const s = analysis.live_setup;
    if (s && s.status === "CONFIRMED")
      out.push({ id: "setup", kind: "setup", label: `Setup ${s.dir} (E/SL/TP)`,
                 entry: s.entry, sl: s.stop_loss, tp: s.take_profit });
    return out;
  }, [analysis]);

  // create chart once + auto-refresh candles + band-sync loop
  useEffect(() => {
    const chart = createChart(elRef.current, {
      layout: { background: { color: "#0e1320" }, textColor: "#9aa4b8", fontSize: 11 },
      grid: { vertLines: { color: "#171d2b" }, horzLines: { color: "#171d2b" } },
      crosshair: { mode: CrosshairMode.Normal },
      timeScale: { timeVisible: true, secondsVisible: false, borderColor: "#232a3a" },
      rightPriceScale: { borderColor: "#232a3a" },
      height: 400, autoSize: true,
    });
    const series = chart.addCandlestickSeries({
      upColor: "#2ecc71", downColor: "#ff5d5d", borderVisible: false,
      wickUpColor: "#2ecc71", wickDownColor: "#ff5d5d",
    });
    chartRef.current = chart; seriesRef.current = series;
    const bandTimer = setInterval(() => syncBands(), 200);
    return () => { clearInterval(bandTimer); chart.remove(); };
  }, []);

  // load candles for the selected timeframe (re-runs on TF switch); analysis/markings
  // stay computed on 15m, so switching TF is a pure fractal VIEW.
  useEffect(() => {
    const series = seriesRef.current, chart = chartRef.current;
    if (!series) return;
    let first = true;
    const load = () =>
      fetch(`/api/candles?tf=${tf}&count=${TF_COUNT[tf]}`).then((r) => r.json())
        .then((d) => {
          if (!d.candles) return;
          series.setData(d.candles.map((c) => ({ ...c, time: c.time + IST_OFFSET })));
          if (first) { chart.timeScale().fitContent(); first = false; }
        }).catch(() => {});
    load();
    const candleTimer = setInterval(load, 15000);
    return () => clearInterval(candleTimer);
  }, [tf]);

  // redraw price lines + refresh visible-zone list whenever markings or visibility change
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;
    zonesRef.current = markings.filter((m) => ["zone", "fvg", "liq"].includes(m.kind) && !hidden[m.id]);
    linesRef.current.forEach((l) => series.removePriceLine(l));
    linesRef.current = [];
    const line = (price, color, title, style = LineStyle.Solid, width = 1) =>
      linesRef.current.push(series.createPriceLine({ price, color, lineWidth: width, lineStyle: style, axisLabelVisible: true, title }));
    for (const m of markings) {
      if (hidden[m.id]) continue;
      if (m.kind === "eq") line(m.price, "#f0b429", "EQ", LineStyle.Dashed);
      if (m.kind === "mss") line(m.price, "#22d3ee", "MSS", LineStyle.Dashed);
      if (m.kind === "setup") {
        line(m.entry, "#4c8dff", "ENTRY");
        line(m.sl, "#ff5d5d", "SL");
        line(m.tp, "#2ecc71", "TP");
      }
    }
    syncBands();
  }, [markings, hidden]);

  // draw OB boxes anchored at their formation candle
  function syncBands() {
    const overlay = overlayRef.current, series = seriesRef.current, chart = chartRef.current;
    if (!overlay || !series || !chart) return;
    overlay.innerHTML = "";
    const ts = chart.timeScale();
    for (const z of zonesRef.current) {
      const yTop = series.priceToCoordinate(z.top);
      const yBot = series.priceToCoordinate(z.bottom);
      if (yTop == null || yBot == null) continue;
      // snap the anchor down to the displayed timeframe's candle so it always lands on a
      // real bar (fixes 1H anchoring for levels whose high/low formed off the hour)
      let xLeft = null;
      if (z.startTime) {
        const tfSec = { "5m": 300, "15m": 900, "1h": 3600 }[tfRef.current] || 900;
        const snapped = Math.floor(z.startTime / tfSec) * tfSec;
        xLeft = ts.timeToCoordinate(snapped + IST_OFFSET);
      }
      if (xLeft == null || xLeft < 0) xLeft = 0;
      const box = document.createElement("div");
      let cls;
      if (z.kind === "fvg") cls = "fvg";
      else if (z.kind === "liq") cls = z.isTarget ? "liq-target" : (z.grp === "pw" ? "liq-pw" : "liq-pd");
      else cls = z.dir;
      box.className = "zone-band " + cls;
      const minH = z.kind === "liq" ? 2 : 3;
      box.style.top = Math.min(yTop, yBot) + "px";
      box.style.height = Math.max(minH, Math.abs(yBot - yTop)) + "px";
      box.style.left = xLeft + "px";
      box.style.right = "64px";
      const tag = document.createElement("span");
      tag.className = "zone-tag"; tag.textContent = z.label;
      box.appendChild(tag);
      overlay.appendChild(box);
    }
  }

  const fmt = (t) => t ? new Date(t * 1000).toLocaleString([], { weekday: "short", hour: "2-digit", minute: "2-digit" }) : "";
  // bottom bar = dynamic markings only (OB zones, FVG, MSS, setup). The constant levels
  // (EQ, PDH/PDL, PWH/PWL) are toggled from the Bias & Zone strip above the chart.
  const dynamic = markings.filter((m) => !["eq", "liq"].includes(m.kind));

  return (
    <section className="card wide chart-card">
      <h3>Live Chart
        <span className="tf-switch">
          {["5m", "15m", "1h"].map((x) => (
            <button key={x} className={tf === x ? "on" : ""} onClick={() => setTf(x)}>{x}</button>
          ))}
        </span>
        <em className="muted small"> · markings are 15m-derived (fractal view) · auto-updating</em>
      </h3>
      <div className="chart-wrap">
        <div ref={elRef} className="chart" />
        <div ref={overlayRef} className="chart-overlay" />
      </div>
      <div className="zone-toggles">
        <span className="zt-head">Markings:</span>
        {dynamic.length === 0 && <span className="muted small">none right now</span>}
        {dynamic.map((m) => (
          <button key={m.id} className={"zt-row " + (hidden[m.id] ? "off" : "on") + " " + (m.dir || m.kind)}
            onClick={() => toggleMark(m.id)} title={hidden[m.id] ? "Show" : "Hide"}>
            <span className="zt-eye">{hidden[m.id] ? "🙈" : "👁"}</span>
            <span className="zt-body">
              <span className="zt-label">{m.label}</span>
              {(m.kind === "zone" || m.kind === "fvg") && <span className="zt-time">{fmt(m.startTime)}</span>}
              {m.kind === "mss" && <span className="zt-time">{m.price}</span>}
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
