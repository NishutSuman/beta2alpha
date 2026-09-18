#!/usr/bin/env node
/**
 * beta2alpha — the daily discipline ledger
 *
 * Not a habit app. A cage you built yourself, that you cannot lie to.
 * Win the morning. Keep the streak. Become the person who keeps promises.
 *
 * Usage:
 *   node b2a.js          → log today (the morning ritual, ~30 seconds)
 *   node b2a.js status   → see your streaks and the last 14 days
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const DATA_DIR = path.join(__dirname, 'data');
const LOG_FILE = path.join(DATA_DIR, 'log.json');

// The four daily promises. Rules, not outcomes.
const PROMISES = [
  { key: 'sleep',   label: 'Lights out on time last night (the keystone — won the night)' },
  { key: 'body',    label: 'Moved my body / workout done' },
  { key: 'skill',   label: '1 hour of deep work / upskilling done' },
  { key: 'trading', label: 'Followed my trading RULES today (not P&L — the rules)' },
];

const C = {
  reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m',
  green: '\x1b[32m', red: '\x1b[31m', yellow: '\x1b[33m', cyan: '\x1b[36m',
};

function today() {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD, local-ish, fine for daily
}

function load() {
  try {
    return JSON.parse(fs.readFileSync(LOG_FILE, 'utf8'));
  } catch {
    return {};
  }
}

function save(data) {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(LOG_FILE, JSON.stringify(data, null, 2));
}

function ask(rl, q) {
  return new Promise((res) => rl.question(q, (a) => res(a.trim())));
}

function yes(answer) {
  return /^(y|yes|1|done|d)$/i.test(answer);
}

async function log() {
  const data = load();
  const d = today();
  const existing = data[d];

  console.log(`\n${C.bold}${C.cyan}beta2alpha${C.reset} ${C.dim}— ${d}${C.reset}`);
  if (existing) console.log(`${C.dim}(updating today's entry)${C.reset}`);
  console.log('');

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const entry = { done: {} };

  for (const p of PROMISES) {
    const a = await ask(rl, `  ${p.label}? ${C.dim}(y/n)${C.reset} `);
    entry.done[p.key] = yes(a);
  }

  entry.regret = await ask(
    rl,
    `\n  ${C.yellow}One line — what will I regret tonight if I don't do it?${C.reset}\n  > `
  );

  rl.close();

  data[d] = entry;
  save(data);

  const kept = Object.values(entry.done).filter(Boolean).length;
  console.log(
    `\n  Logged. ${C.bold}${kept}/${PROMISES.length}${C.reset} promises kept today.`
  );
  if (kept === PROMISES.length) console.log(`  ${C.green}Full day. This is who you are now.${C.reset}`);
  else if (kept === 0) console.log(`  ${C.red}Zero. Tomorrow you don't break the chain twice.${C.reset}`);
  else console.log(`  ${C.yellow}Progress beats perfect. Go close the rest.${C.reset}`);
  console.log('');
  status();
}

function dateNDaysAgo(n) {
  const dt = new Date();
  dt.setDate(dt.getDate() - n);
  return dt.toISOString().slice(0, 10);
}

// A day "counts" toward the streak if at least one promise was kept (showed up).
function dayCounts(entry) {
  return entry && Object.values(entry.done || {}).some(Boolean);
}

function computeStreaks(data) {
  // Current streak: consecutive counting days ending today or yesterday.
  let current = 0;
  for (let i = 0; ; i++) {
    const d = dateNDaysAgo(i);
    if (dayCounts(data[d])) current++;
    else if (i === 0) continue; // today not logged yet — don't break the streak
    else break;
  }

  // Longest streak across all logged days.
  const days = Object.keys(data).sort();
  let longest = 0, run = 0, prev = null;
  for (const d of days) {
    if (!dayCounts(data[d])) { run = 0; prev = d; continue; }
    if (prev && (new Date(d) - new Date(prev)) === 86400000 && dayCounts(data[prev])) run++;
    else run = 1;
    longest = Math.max(longest, run);
    prev = d;
  }

  const regretsAvoided = days.filter((d) => dayCounts(data[d])).length;
  return { current, longest, regretsAvoided };
}

function status() {
  const data = load();
  const { current, longest, regretsAvoided } = computeStreaks(data);

  console.log(`${C.bold}${C.cyan}━━ beta2alpha status ━━${C.reset}`);
  console.log(`  🔥 Current streak : ${C.bold}${current}${C.reset} day(s)`);
  console.log(`  🏆 Longest streak : ${longest} day(s)`);
  console.log(`  ✊ Days you showed up: ${regretsAvoided}`);

  console.log(`\n  ${C.dim}Last 14 days  (sleep·body·skill·trading — green=all, yellow=some, red=none)${C.reset}`);
  let row = '  ';
  for (let i = 13; i >= 0; i--) {
    const d = dateNDaysAgo(i);
    const e = data[d];
    if (!e) row += `${C.dim}·${C.reset}`;
    else {
      const kept = Object.values(e.done).filter(Boolean).length;
      const mark = kept === PROMISES.length ? `${C.green}█${C.reset}`
        : kept > 0 ? `${C.yellow}▓${C.reset}`
        : `${C.red}░${C.reset}`;
      row += mark;
    }
  }
  console.log(row);

  const t = data[today()];
  if (!t) console.log(`\n  ${C.yellow}Today isn't logged yet. Run: node b2a.js${C.reset}\n`);
  else console.log('');
}

const cmd = process.argv[2];
if (cmd === 'status') status();
else log();
