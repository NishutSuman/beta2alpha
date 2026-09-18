// Fractal Nature + ILDRE Institutional Trading Framework (v1.0) — full mentor methodology.
// Rendered as collapsible sections in the Playbook tab. Source: strategy/ILDRE-FRAMEWORK.md
// block types: p | list | flow | sub | check

export const FRAMEWORK_META = {
  title: "Fractal Nature + ILDRE Framework",
  version: "v1.0",
  subtitle: "Institutional Liquidity Delivery & Re-Entry Execution",
};

export const SECTIONS = [
  { id: "philosophy", title: "Core Philosophy", tag: "foundation", open: true, blocks: [
    { type: "p", text: "The market is fractal — the same institutional delivery algorithm repeats across every timeframe. HTF defines the narrative; LTF provides execution precision." },
    { type: "list", title: "The objective is to identify:", items: [
      "The institutional narrative", "The intended liquidity destination",
      "The path price is likely to follow", "The highest-probability execution point"] },
    { type: "flow", title: "Delivery model", steps: ["Liquidity", "Mitigation", "Displacement", "Consolidation", "Continuation", "Liquidity Delivery"] },
  ]},
  { id: "principles", title: "Core Principles", tag: "foundation", open: true, blocks: [
    { type: "list", items: [
      "Trade with the HTF narrative",
      "Every trade must have a defined liquidity destination",
      "Institutions move price from one liquidity pool to another",
      "LTFs refine execution, not bias — bias alone is never an entry",
      "If the narrative becomes invalid, restart the analysis",
      "Preserve capital over forcing trades"] },
  ]},
  { id: "step1", title: "Step 1 — Map External Liquidity", tag: "analysis", blocks: [
    { type: "sub", title: "Weekly", items: ["PWH → Buy-Side Liquidity (BSL)", "PWL → Sell-Side Liquidity (SSL)"] },
    { type: "sub", title: "Daily", items: ["PDH → Buy-Side Liquidity", "PDL → Sell-Side Liquidity"] },
    { type: "sub", title: "Liquidity hierarchy (priority)", items: [
      "1. Previous Week High / Low", "2. Previous Day High / Low", "3. Major Swing High / Low",
      "4. Session High / Low", "5. Internal Liquidity"] },
  ]},
  { id: "step2", title: "Step 2 — Determine HTF Bias", tag: "analysis", blocks: [
    { type: "p", text: "Never search for entries before determining the narrative. Is price reacting from a Daily OB / FVG / Breaker / Mitigation block?" },
    { type: "list", title: "Ask:", items: [
      "Is price respecting or rejecting the PD Array?", "Is displacement supporting the reaction?",
      "Does market structure agree?", "Is the reaction supported by liquidity?"] },
    { type: "p", text: "Only set a bias when MULTIPLE factors agree. Never on one signal alone." },
  ]},
  { id: "step3", title: "Step 3 — Identify the Market Destination", tag: "analysis", blocks: [
    { type: "list", items: [
      "Which liquidity pool is price seeking?", "Which HTF OB / FVG may terminate the move?",
      "Is the destination internal or external liquidity?"] },
    { type: "p", text: "This defines direction, target, and expected reversal area. Never look for entries until the destination is known." },
  ]},
  { id: "step4", title: "Step 4 — Build the Intraday Narrative", tag: "analysis", blocks: [
    { type: "p", text: "Daily → 4H → 1H → 15M → 5M. Every timeframe should support the same story." },
    { type: "sub", title: "Bullish narrative", items: ["SSL sweep", "Bullish MSS", "Bullish Order Block", "Bullish FVG", "Bullish displacement"] },
    { type: "sub", title: "Bearish narrative", items: ["BSL sweep", "Bearish MSS", "Bearish Order Block", "Bearish FVG", "Bearish displacement"] },
    { type: "p", text: "Temporary pullbacks are fine if they realign. Never let a 5M chart override the Daily narrative." },
  ]},
  { id: "step5", title: "Step 5 — Validate the Order Block", tag: "validation", blocks: [
    { type: "flow", title: "Rule 1 — Liquidity first (preferred sequence)", steps: ["Liquidity Sweep", "Order Block", "Displacement", "Fair Value Gap"] },
    { type: "sub", title: "Rule 2 — Extreme Order Blocks", items: ["Bullish bias → lowest bullish OB", "Bearish bias → highest bearish OB"] },
    { type: "sub", title: "Rule 3 — Institutional confirmation (more = higher prob.)", items: ["Engineers liquidity", "Produces displacement", "Leaves imbalance", "Respects HTF bias"] },
    { type: "p", text: "Rule 4 — FVG strengthens an OB but isn't absolute; a valid OB can exist without a textbook FVG if HTF confluence + strong displacement + intact narrative." },
    { type: "p", text: "Rule 5 — Inside-bar exception: extend the zone to include imbalance; valid only with institutional confirmation, else ignore." },
  ]},
  { id: "step6", title: "Step 6 — Multi-Timeframe Fractal Alignment", tag: "validation", blocks: [
    { type: "flow", title: "Alignment order", steps: ["Daily", "4H", "1H", "15M", "5M", "Execution"] },
    { type: "list", title: "Every timeframe should confirm:", items: ["Liquidity Sweep", "MSS", "Order Block", "Fair Value Gap", "Displacement", "Liquidity Target"] },
    { type: "p", text: "LTFs refine execution. They never replace the HTF narrative." },
  ]},
  { id: "ildre", title: "Step 7 — ILDRE: Delivery Path", tag: "execution", blocks: [
    { type: "p", text: "Institutions engineer liquidity, mitigate, trap, then continue. ILDRE = understand the delivery path, don't chase price." },
    { type: "sub", title: "7.1 Intermediate rejection zones", items: ["HTF OBs, FVGs, breaker & mitigation blocks become pullback / temporary-rejection / mitigation areas before the final target"] },
    { type: "flow", title: "7.2 Liquidity engineering", steps: ["Create liquidity", "Sweep", "Mitigate", "Induce retail", "Resume trend"] },
    { type: "p", text: "7.3 Continuation structure: after rejection price often consolidates; liquidity builds both sides; find the next supporting OB aligned with HTF = the Continuation Zone." },
    { type: "flow", title: "7.4 Liquidity hunt before continuation (wait for the sweep first)", steps: ["Consolidation", "Liquidity build-up", "Sweep", "Mitigate supporting PD array", "Continuation"] },
    { type: "sub", title: "7.5 Behaviour at the continuation zone", items: ["Immediate consolidation", "Small displacement then consolidation", "Immediate continuation (rare, strong momentum)"] },
    { type: "list", title: "7.6 Confirmation before execution:", items: ["Consolidation breakout", "Full 15M candle close", "Breakout in HTF direction", "No immediate rejection back inside"] },
  ]},
  { id: "step8", title: "Step 8 — Entry Refinement", tag: "execution", blocks: [
    { type: "list", title: "After 15M confirmation, drop to 5M and find:", items: ["Extreme Order Block", "Fair Value Gap", "MSS", "Supporting Liquidity"] },
    { type: "p", text: "8.1 Fallback: if no valid 5M PD array, return to a valid 15M extreme OB + FVG + structure." },
    { type: "sub", title: "Execution priority", items: ["1. Extreme 5M OB + FVG", "2. Valid 15M OB + FVG", "3. No valid zone → NO TRADE. Bias is never an entry."] },
  ]},
  { id: "step9", title: "Step 9 — Trade Execution", tag: "execution", blocks: [
    { type: "p", text: "Entry: only from a validated PD Array, in HTF direction, confirmed institutional continuation." },
    { type: "p", text: "Stop Loss: beyond the extreme OB / liquidity sweep / structural invalidation — the point where the idea is wrong. Never random." },
    { type: "sub", title: "Take Profit (priority)", items: ["1. HTF liquidity target", "2. Next HTF rejection zone", "3. Swing High / Low", "4. PDH / PDL", "5. PWH / PWL", "Partials allowed"] },
  ]},
  { id: "invalidation", title: "Narrative Invalidation", tag: "risk", blocks: [
    { type: "list", title: "Discard immediately & restart from Step 1 if:", items: [
      "Daily MSS changes direction", "HTF OB decisively violated", "Liquidity target reached before entry",
      "Major news flips sentiment", "LTFs continuously fail to align"] },
  ]},
  { id: "risk", title: "Risk Management", tag: "risk", blocks: [
    { type: "list", items: [
      "Never exceed your max daily loss", "Never increase risk after a loss", "No revenge trading",
      "Never move SL further away", "Never widen risk to 'save' a trade", "Never enter late after displacement",
      "Capital preservation is the first responsibility"] },
  ]},
  { id: "filter", title: "Market Condition Filter", tag: "risk", blocks: [
    { type: "list", title: "Best in directional markets. AVOID when:", items: [
      "HTF bias is unclear", "Price trapped in a large range", "No clear liquidity destination",
      "Major news imminent", "LTFs constantly contradict HTF"] },
    { type: "p", text: "No setup is better than a poor setup." },
  ]},
  { id: "fundamentals", title: "Fundamental & Geopolitical Confluence", tag: "context", blocks: [
    { type: "list", items: ["Rate decisions", "CPI", "PPI", "NFP", "FOMC", "Central-bank speeches", "Geopolitics", "Risk-on / risk-off", "Currency strength"] },
    { type: "p", text: "Fundamentals add confidence — they don't replace technicals." },
  ]},
  { id: "flow", title: "Complete Trade Flow (16 steps)", tag: "process", blocks: [
    { type: "flow", steps: ["Weekly liquidity", "Daily liquidity", "Daily bias", "Destination", "Intermediate rejection zones",
      "Validate HTF PD arrays", "Align 4H→1H→15M→5M", "Wait for sweep", "Validate OB", "Confirm displacement",
      "Confirm FVG (if present)", "15M confirmation", "Refine on 5M (or 15M fallback)", "Execute", "Manage risk", "Exit at target / invalidation"] },
  ]},
  { id: "checklist", title: "Master Checklist", tag: "process", blocks: [
    { type: "check", items: [
      "Weekly liquidity marked", "Daily liquidity marked", "HTF bias confirmed", "Market destination identified",
      "Intermediate rejection zones identified", "HTF PD array valid", "Lower timeframes aligned", "Liquidity sweep complete",
      "Order block validated", "Displacement confirmed", "FVG present (preferred)", "Fractal alignment complete",
      "15M confirmation complete", "5M entry available (or valid 15M)", "Risk acceptable", "Stop loss defined",
      "Take profit defined", "Economic calendar checked", "Position size calculated"] },
  ]},
  { id: "golden", title: "Golden & Final Principles", tag: "foundation", blocks: [
    { type: "list", items: [
      "Never predict — follow price delivery", "Never trade without a destination", "HTF always wins; LTF only precision",
      "Don't force an OB; don't force an FVG", "Every trade needs objective confluence", "Protect capital before profit",
      "Best trades need the least interpretation", "If rules aren't met, do nothing",
      "Missing a trade is OK; a low-quality trade is not", "Consistency = a repeatable process"] },
  ]},
  { id: "engine", title: "⚙️ Engine coverage (what beta2alpha automates today)", tag: "build", open: true, blocks: [
    { type: "sub", title: "✅ Automated now", items: [
      "HTF bias (Daily + 1H), premium/discount, equilibrium",
      "Order-block detection + nesting (15m inside 1H) + mean-threshold validity",
      "Liquidity scoring: internal sweep + external target + freshness → High/Medium grade",
      "Kill-zone gating, confirmation candle, entry/SL/TP/lot, demo journal"] },
    { type: "sub", title: "⏳ To build toward full ILDRE", items: [
      "PWH/PWL & PDH/PDL mapping + explicit destination targeting",
      "4H layer + MSS detection + displacement→FVG sequence per timeframe",
      "Extreme-OB selection + 5M entry refinement with 15M fallback",
      "Economic-calendar filter + interactive master checklist"] },
  ]},
];
