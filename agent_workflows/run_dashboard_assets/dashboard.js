/* runsdash (97i0ao): drill-down run analytics dashboard. Offline, dependency free. */
(function () {
  'use strict';

  // ---------------------------------------------------------------- data
  const RAW = JSON.parse(document.getElementById('dash-data').textContent);
  const COLS = RAW.columns || {};
  const N = RAW.n || 0;
  const TOOL_NAMES = RAW.tool_names || [];
  const TOOL_CAT = RAW.tool_categories || {};
  const CATS = ['read', 'edit', 'write', 'shell', 'search', 'todo', 'wait', 'subagent', 'web', 'other'];
  const SHELL = ['test', 'git', 'aw', 'inspect', 'python', 'lint', 'other'];
  const SHELL_LABEL = { test: 'tests', git: 'git', aw: 'aw CLI', inspect: 'inspect (cat/ls/rg...)', python: 'python', lint: 'lint', other: 'other' };

  function weekOf(d) {
    if (!d) return '';
    const t = new Date(d + 'T00:00:00Z');
    if (isNaN(t)) return '';
    t.setUTCDate(t.getUTCDate() - ((t.getUTCDay() + 6) % 7));
    return t.toISOString().slice(0, 10);
  }

  const ROWS = [];
  for (let i = 0; i < N; i++) {
    const r = { _i: i };
    for (const k in COLS) r[k] = COLS[k][i];
    const sp = (RAW.tools && RAW.tools[i]) || [];
    r._tools = {};
    r._terr = {};
    for (let j = 0; j + 2 < sp.length; j += 3) {
      const nm = TOOL_NAMES[sp[j]];
      if (nm === undefined) continue;
      r._tools[nm] = sp[j + 1];
      if (sp[j + 2]) r._terr[nm] = sp[j + 2];
    }
    r.stage = r.role === 'main' ? (r.action || 'unknown') : r.role;
    r.restart = r.recovery ? 'recovery' : (r.attempt > 1 ? 'retry' : 'first attempt');
    r.week = weekOf(r.date);
    r.month = r.date ? r.date.slice(0, 7) : '';
    r.sessions = 1;
    ['set', 'id6', 'kind', 'model', 'host', 'disposition', 'verification', 'item_status', 'action', 'role'].forEach((k) => {
      if (r[k] === null || r[k] === undefined || r[k] === '') r[k] = '(none)';
    });
    ROWS.push(r);
  }

  // ---------------------------------------------------------------- dimensions
  const DIMS = {
    stage: { label: 'Stage', help: 'review / execute turn, or the verify, gate-answer and defect re-ask sessions around it' },
    model: { label: 'Model' },
    host: { label: 'Host' },
    outcome: { label: 'Outcome', help: 'success / partial / failed, collapsed from the driver disposition or verifier verdict' },
    restart: { label: 'Attempt type', help: 'first attempt, a retry (attempt 2+), or a recovery turn' },
    disposition: { label: 'Disposition' },
    action: { label: 'Queue action' },
    role: { label: 'Session role' },
    set: { label: 'Set' },
    id6: { label: 'Plan' },
    kind: { label: 'Plan kind' },
    token_source: { label: 'Token source' },
    verification: { label: 'Verifier verdict' },
    month: { label: 'Month' },
    week: { label: 'Week' },
    date: { label: 'Day' },
    run: { label: 'Run' },
  };
  const FACETS = ['stage', 'host', 'model', 'outcome', 'restart', 'disposition', 'set', 'token_source'];
  const GROUPABLE = ['model', 'host', 'stage', 'outcome', 'restart', 'disposition', 'action', 'role', 'set', 'kind', 'verification', 'token_source', 'month', 'week', 'id6', 'run'];

  // ---------------------------------------------------------------- metrics
  const HAS_TOK = (r) => r.token_source !== 'none';
  const HAS_LOG = (r) => !!r.has_log;
  const MET = {};
  const MET_ORDER = [];
  function metric(k, label, fmt, valid, group, extra) {
    const m = Object.assign({ k: k, label: label, fmt: fmt, valid: valid, group: group }, extra || {});
    if (!m.get) m.get = (r) => (m.valid(r) ? num(r[k]) : null);
    MET[k] = m;
    MET_ORDER.push(k);
  }
  function ratio(k, label, fmt, a, b, valid, group, scale) {
    metric(k, label, fmt, valid, group, {
      ratio: [a, b],
      scale: scale || 1,
      get: (r) => {
        if (!valid(r)) return null;
        const d = num(r[b]);
        return d ? (num(r[a]) / d) * (scale || 1) : null;
      },
    });
  }
  function num(v) { return typeof v === 'number' && isFinite(v) ? v : 0; }

  metric('total_tokens', 'Total tokens (incl. cache reads)', 'tok', HAS_TOK, 'Tokens');
  metric('fresh_tokens', 'Fresh tokens (input + output)', 'tok', HAS_TOK, 'Tokens');
  metric('input', 'Input tokens (uncached)', 'tok', HAS_TOK, 'Tokens');
  metric('output', 'Output tokens', 'tok', HAS_TOK, 'Tokens');
  metric('reasoning', 'Reasoning tokens', 'tok', HAS_TOK, 'Tokens');
  metric('cache_read', 'Cache-read tokens', 'tok', HAS_TOK, 'Tokens');
  ratio('cache_share', 'Cache-read share of tokens', 'pct', 'cache_read', 'total_tokens', HAS_TOK, 'Tokens');
  ratio('tokens_per_step', 'Tokens per LLM step', 'tok', 'total_tokens', 'steps', (r) => HAS_TOK(r) && HAS_LOG(r), 'Tokens');
  metric('cost', 'Cost, USD (host-recorded)', 'usd', (r) => r.cost !== null && r.cost !== undefined, 'Cost and time');
  ratio('usd_per_mtok', 'Cost per million tokens', 'usd', 'cost', 'total_tokens', (r) => r.cost !== null && r.cost !== undefined && HAS_TOK(r), 'Cost and time', 1e6);
  metric('wall', 'Wall time', 'dur', (r) => r.wall !== null && r.wall !== undefined, 'Cost and time');
  metric('tool_seconds', 'Time inside tools', 'dur', HAS_LOG, 'Cost and time');
  metric('steps', 'LLM steps (turns)', 'num', HAS_LOG, 'Activity');
  metric('tool_calls', 'Tool calls', 'num', HAS_LOG, 'Activity');
  ratio('tools_per_step', 'Tool calls per LLM step', 'num2', 'tool_calls', 'steps', HAS_LOG, 'Activity');
  metric('tool_errors', 'Tool errors', 'num', HAS_LOG, 'Activity');
  ratio('error_rate', 'Tool error rate', 'pct', 'tool_errors', 'tool_calls', HAS_LOG, 'Activity');
  metric('files_read', 'Distinct files read', 'num', HAS_LOG, 'Activity');
  metric('files_edited', 'Distinct files edited or written', 'num', HAS_LOG, 'Activity');
  CATS.forEach((c) => metric('t_' + c, 'Tool calls: ' + c, 'num', HAS_LOG, 'Tool mix'));
  SHELL.forEach((c) => metric('sh_' + c, 'Shell commands: ' + SHELL_LABEL[c], 'num', HAS_LOG, 'Shell mix'));
  metric('sessions', 'Sessions (count)', 'num', () => true, 'Activity');

  const STATS = { median: 'Median', mean: 'Mean', p90: 'p90', sum: 'Total', count: 'Count' };

  // ---------------------------------------------------------------- formatting
  function esc(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  function trunc(s, n) { s = String(s); return s.length > n ? s.slice(0, n - 1) + '\u2026' : s; }
  function fmt(v, kind) {
    if (v === null || v === undefined || !isFinite(v)) return '-';
    const a = Math.abs(v);
    switch (kind) {
      case 'tok':
        if (a >= 1e9) return (v / 1e9).toFixed(2) + 'B';
        if (a >= 1e6) return (v / 1e6).toFixed(a >= 1e8 ? 0 : 1) + 'M';
        if (a >= 1e3) return (v / 1e3).toFixed(a >= 1e5 ? 0 : 1) + 'k';
        return Math.round(v).toString();
      case 'usd':
        if (a >= 1000) return '$' + Math.round(v).toLocaleString();
        if (a >= 10) return '$' + v.toFixed(1);
        if (a >= 1) return '$' + v.toFixed(2);
        return '$' + v.toFixed(3);
      case 'dur': {
        if (a < 60) return v.toFixed(a < 10 ? 1 : 0) + 's';
        if (a < 3600) return Math.floor(v / 60) + 'm ' + String(Math.round(v % 60)).padStart(2, '0') + 's';
        return Math.floor(v / 3600) + 'h ' + String(Math.round((v % 3600) / 60)).padStart(2, '0') + 'm';
      }
      case 'pct': return (v * 100).toFixed(a < 0.1 ? 1 : 0) + '%';
      case 'num2': return v.toFixed(2);
      default:
        if (a >= 1e6) return (v / 1e6).toFixed(1) + 'M';
        if (a >= 1e4) return (v / 1e3).toFixed(1) + 'k';
        if (a < 100 && !Number.isInteger(v)) return v.toFixed(1);
        return Math.round(v).toLocaleString();
    }
  }
  function fmtM(v, mk, stat) { return stat === 'count' ? fmt(v, 'num') : fmt(v, MET[mk].fmt); }

  // ---------------------------------------------------------------- colors
  const PAL = ['#3b6fd8', '#e0822d', '#2e9e6a', '#c9463d', '#8a5cc7', '#1ea4b8', '#c0a12a', '#d65c9e', '#6b7a8f', '#5b8c2a', '#9a6b3f', '#4b5bd1', '#b0413e', '#2f7f7a'];
  const FIXED = {
    outcome: { success: '#2e9e6a', partial: '#d19a1c', failed: '#d1453b', unknown: '#98a2b3' },
    restart: { 'first attempt': '#3b6fd8', retry: '#e0822d', recovery: '#c9463d' },
    host: { oc: '#3b6fd8', agy: '#e0822d', unknown: '#98a2b3' },
  };
  const CAT_COLOR = { read: '#3b6fd8', edit: '#e0822d', write: '#c9463d', shell: '#2e9e6a', search: '#8a5cc7', todo: '#c0a12a', wait: '#98a2b3', subagent: '#1ea4b8', web: '#d65c9e', other: '#6b7a8f' };
  const RANK = {};
  function rankFor(dim) {
    if (RANK[dim]) return RANK[dim];
    const c = {};
    ROWS.forEach((r) => { const v = String(r[dim]); c[v] = (c[v] || 0) + 1; });
    const order = Object.keys(c).sort((a, b) => c[b] - c[a]);
    const m = {};
    order.forEach((v, i) => { m[v] = i; });
    RANK[dim] = m;
    return m;
  }
  function colorFor(dim, val) {
    val = String(val);
    if (FIXED[dim] && FIXED[dim][val]) return FIXED[dim][val];
    if (val === 'other' || val === '(other)') return '#b8bfca';
    const r = rankFor(dim)[val];
    return PAL[(r === undefined ? 0 : r) % PAL.length];
  }

  // ---------------------------------------------------------------- statistics
  function quantile(sorted, q) {
    if (!sorted.length) return null;
    const p = (sorted.length - 1) * q;
    const lo = Math.floor(p), hi = Math.ceil(p);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (p - lo);
  }
  function agg(rows, mk, stat) {
    const m = MET[mk];
    if (stat === 'count') return { v: rows.length, n: rows.length };
    if (m.ratio && stat === 'sum') {
      let a = 0, b = 0, n = 0;
      rows.forEach((r) => { if (m.valid(r)) { a += num(r[m.ratio[0]]); b += num(r[m.ratio[1]]); n++; } });
      return { v: b ? (a / b) * m.scale : null, n: n };
    }
    const vals = [];
    rows.forEach((r) => { const x = m.get(r); if (x !== null && isFinite(x)) vals.push(x); });
    if (!vals.length) return { v: null, n: 0 };
    let s = 0;
    vals.forEach((x) => { s += x; });
    if (stat === 'sum') return { v: s, n: vals.length };
    if (stat === 'mean') return { v: s / vals.length, n: vals.length };
    vals.sort((a, b) => a - b);
    if (stat === 'p90') return { v: quantile(vals, 0.9), n: vals.length };
    return { v: quantile(vals, 0.5), lo: quantile(vals, 0.25), hi: quantile(vals, 0.75), n: vals.length };
  }
  function share(rows, pred) {
    if (!rows.length) return null;
    let k = 0;
    rows.forEach((r) => { if (pred(r)) k++; });
    return k / rows.length;
  }
  function groupBy(rows, dim) {
    const g = new Map();
    rows.forEach((r) => {
      const v = String(r[dim] === undefined || r[dim] === null || r[dim] === '' ? '(none)' : r[dim]);
      if (!g.has(v)) g.set(v, []);
      g.get(v).push(r);
    });
    return g;
  }
  function sumOf(rows, k) { let s = 0; rows.forEach((r) => { s += num(r[k]); }); return s; }

  // ---------------------------------------------------------------- units of analysis
  const SUMS = ['input', 'output', 'reasoning', 'cache_read', 'cache_write', 'fresh_tokens', 'total_tokens', 'steps',
    'tool_calls', 'tool_errors', 'tool_seconds', 'files_read', 'files_edited', 'sessions']
    .concat(CATS.map((c) => 't_' + c)).concat(SHELL.map((c) => 'sh_' + c));
  const GRAINS = {
    session: 'Session (one agent conversation)',
    attempt: 'Plan attempt (turn + its verify / gate sessions)',
    plan: 'Plan in a run (all attempts and verification)',
  };
  function combine(list, grain) {
    let main = null;
    list.forEach((r) => {
      if (r.role === 'main' && (!main || r.attempt >= main.attempt)) main = r;
    });
    main = main || list[0];
    const o = Object.assign({}, main);
    o._members = list.map((r) => r._i);
    o._tools = {};
    o._terr = {};
    SUMS.forEach((k) => { o[k] = 0; });
    let cost = null, wall = null, start = null, anyLog = false, src = 'none', maxAtt = 0, anyRecovery = false;
    list.forEach((r) => {
      SUMS.forEach((k) => { o[k] += num(r[k]); });
      if (r.cost !== null && r.cost !== undefined) cost = (cost || 0) + r.cost;
      if (r.wall !== null && r.wall !== undefined) wall = (wall || 0) + r.wall;
      if (r.start && (!start || r.start < start)) start = r.start;
      if (r.has_log) anyLog = true;
      if (r.token_source === 'log' || (r.token_source === 'state' && src === 'none')) src = r.token_source;
      if (r.attempt > maxAtt) maxAtt = r.attempt;
      if (r.recovery) anyRecovery = true;
      for (const t in r._tools) o._tools[t] = (o._tools[t] || 0) + r._tools[t];
      for (const t in r._terr) o._terr[t] = (o._terr[t] || 0) + r._terr[t];
    });
    o.cost = cost; o.wall = wall; o.start = start; o.has_log = anyLog; o.token_source = src;
    o.attempt = maxAtt;
    o.restart = anyRecovery ? 'recovery' : (maxAtt > 1 ? 'retry' : 'first attempt');
    o.stage = main.action || main.stage;
    o.role = grain;
    const v = list.filter((r) => r.role === 'verify');
    o.verification = v.length ? v[v.length - 1].verification : o.verification;
    return o;
  }
  function regrain(rows, grain) {
    if (grain === 'session') return rows;
    const g = new Map();
    rows.forEach((r) => {
      const k = grain === 'plan' ? r.run + '|' + r.id6 : r.run + '|' + r.id6 + '|' + r.attempt;
      if (!g.has(k)) g.set(k, []);
      g.get(k).push(r);
    });
    const out = [];
    g.forEach((list) => out.push(combine(list, grain)));
    return out;
  }

  // ---------------------------------------------------------------- state (kept in the URL hash)
  const DEFAULT = {
    tab: 'overview',
    grain: 'session',
    f: {},
    q: '',
    from: '',
    to: '',
    cmp: { by: 'model', split: 'stage', metric: 'total_tokens', stat: 'median', log: true, cols: ['total_tokens', 'output', 'cost', 'wall', 'steps', 'tool_calls', 't_read', 't_edit', 't_shell', 'error_rate'] },
    tr: { x: 'week', by: 'model', metric: 'total_tokens', stat: 'sum' },
    sc: { x: 'tool_calls', y: 'total_tokens', color: 'model', logx: true, logy: true },
    tl: { by: 'model', norm: true },
    rk: { by: 'model' },
    tb: { sort: 'start', dir: -1, page: 0 },
  };
  let S = clone(DEFAULT);
  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  function loadHash() {
    try {
      const h = decodeURIComponent(location.hash.slice(1));
      if (!h) return;
      const o = JSON.parse(h);
      S = Object.assign(clone(DEFAULT), o);
      ['cmp', 'tr', 'sc', 'tl', 'rk', 'tb'].forEach((k) => { S[k] = Object.assign(clone(DEFAULT[k]), o[k] || {}); });
      S.f = o.f || {};
    } catch (e) { S = clone(DEFAULT); }
  }
  function saveHash() {
    const s = JSON.stringify(S);
    history.replaceState(null, '', '#' + encodeURIComponent(s));
  }

  // ---------------------------------------------------------------- filtering
  function passes(r, skip) {
    for (const d in S.f) {
      if (d === skip) continue;
      const vals = S.f[d];
      if (vals && vals.length && vals.indexOf(String(r[d])) < 0) return false;
    }
    if (S.from && (!r.date || r.date < S.from)) return false;
    if (S.to && (!r.date || r.date > S.to)) return false;
    if (S.q) {
      const q = S.q.toLowerCase();
      const hay = (r.run + ' ' + r.set + ' ' + r.id6 + ' ' + r.model + ' ' + r.disposition + ' ' + r.stage).toLowerCase();
      if (hay.indexOf(q) < 0) return false;
    }
    return true;
  }
  let CUR = [];
  let CUR_SESS = [];
  function recompute() {
    CUR_SESS = ROWS.filter((r) => passes(r, null));
    CUR = regrain(CUR_SESS, S.grain);
  }
  function addFilter(dim, val) {
    if (val === '(other)') return;
    if (['week', 'month', 'date'].indexOf(dim) >= 0) {
      if (dim === 'date') { S.from = val; S.to = val; }
      else if (dim === 'week') { S.from = val; const t = new Date(val + 'T00:00:00Z'); t.setUTCDate(t.getUTCDate() + 6); S.to = t.toISOString().slice(0, 10); }
      else if (dim === 'month') { S.from = val + '-01'; S.to = val + '-31'; }
      render();
      return;
    }
    if (!DIMS[dim]) return;
    S.f[dim] = [String(val)];
    render();
  }

  // ---------------------------------------------------------------- tiny DOM helpers
  const $ = (sel, root) => (root || document).querySelector(sel);
  function h(tag, attrs, html) {
    const e = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      if (k === 'class') e.className = attrs[k];
      else if (k.slice(0, 2) === 'on') e.addEventListener(k.slice(2), attrs[k]);
      else e.setAttribute(k, attrs[k]);
    }
    if (html !== undefined) e.innerHTML = html;
    return e;
  }
  function sel(label, value, options, onchange, help) {
    const w = h('label', { class: 'ctl' });
    w.appendChild(document.createTextNode(label));
    const s = h('select');
    options.forEach((o) => {
      const opt = h('option', { value: o[0] }, esc(o[1]));
      if (String(o[0]) === String(value)) opt.selected = true;
      s.appendChild(opt);
    });
    s.addEventListener('change', () => onchange(s.value));
    if (help) w.title = help;
    w.appendChild(s);
    return w;
  }
  function chk(label, value, onchange) {
    const w = h('label', { class: 'ctl' });
    w.appendChild(document.createTextNode(label));
    const c = h('input', { type: 'checkbox' });
    c.checked = !!value;
    c.addEventListener('change', () => onchange(c.checked));
    w.appendChild(c);
    return w;
  }
  function metricOptions(filterFn) {
    const out = [];
    const groups = {};
    MET_ORDER.forEach((k) => {
      if (filterFn && !filterFn(MET[k])) return;
      (groups[MET[k].group] = groups[MET[k].group] || []).push(k);
    });
    return groups;
  }
  function metricSel(label, value, onchange) {
    const w = h('label', { class: 'ctl' });
    w.appendChild(document.createTextNode(label));
    const s = h('select');
    const g = metricOptions();
    for (const name in g) {
      const og = h('optgroup', { label: name });
      g[name].forEach((k) => {
        const o = h('option', { value: k }, esc(MET[k].label));
        if (k === value) o.selected = true;
        og.appendChild(o);
      });
      s.appendChild(og);
    }
    s.addEventListener('change', () => onchange(s.value));
    w.appendChild(s);
    return w;
  }
  const dimOpts = (extra) => (extra || []).concat(GROUPABLE.map((d) => [d, DIMS[d].label]));
  const statOpts = Object.keys(STATS).map((k) => [k, STATS[k]]);
  const grainOpts = Object.keys(GRAINS).map((k) => [k, GRAINS[k]]);
  function panel(title, hint) {
    const p = h('section', { class: 'panel' });
    if (title) p.appendChild(h('h2', null, esc(title)));
    if (hint) p.appendChild(h('p', { class: 'hint' }, hint));
    return p;
  }

  // ---------------------------------------------------------------- tooltip
  const TIP = h('div', { class: 'tip' });
  document.body.appendChild(TIP);
  document.addEventListener('mousemove', (ev) => {
    const t = ev.target.closest ? ev.target.closest('[data-tip]') : null;
    if (!t) { TIP.style.display = 'none'; return; }
    TIP.textContent = t.getAttribute('data-tip');
    TIP.style.display = 'block';
    const x = Math.min(ev.clientX + 14, window.innerWidth - TIP.offsetWidth - 8);
    const y = Math.min(ev.clientY + 14, window.innerHeight - TIP.offsetHeight - 8);
    TIP.style.left = x + 'px';
    TIP.style.top = y + 'px';
  });
  document.addEventListener('click', (ev) => {
    const t = ev.target.closest ? ev.target.closest('[data-f]') : null;
    if (t) {
      ev.preventDefault();
      addFilter(t.getAttribute('data-f'), t.getAttribute('data-v'));
      return;
    }
    const o = ev.target.closest ? ev.target.closest('[data-open]') : null;
    if (o) { ev.preventDefault(); openDrawer(o.getAttribute('data-open')); }
  });

  // ---------------------------------------------------------------- scales and axes
  function niceTicks(lo, hi, n) {
    if (!(hi > lo)) { hi = lo + 1; }
    const span = hi - lo;
    const step0 = Math.pow(10, Math.floor(Math.log10(span / n)));
    const err = (span / n) / step0;
    const step = step0 * (err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1);
    const t = [];
    for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) t.push(+v.toPrecision(12));
    return t;
  }
  function scale(lo, hi, a, b, log) {
    if (log) {
      lo = Math.max(lo, 1e-9); hi = Math.max(hi, lo * 10);
      const L = Math.log10(lo), H = Math.log10(hi);
      const f = (v) => a + ((Math.log10(Math.max(v, lo)) - L) / (H - L)) * (b - a);
      f.ticks = () => {
        const t = [];
        for (let e = Math.floor(L); e <= Math.ceil(H); e++) { const v = Math.pow(10, e); if (v >= lo * 0.999 && v <= hi * 1.001) t.push(v); }
        if (t.length < 3) { for (let e = Math.floor(L); e <= Math.ceil(H); e++) [2, 5].forEach((m) => { const v = m * Math.pow(10, e); if (v > lo && v < hi) t.push(v); }); t.sort((x, y) => x - y); }
        return t;
      };
      f.lo = lo; f.hi = hi;
      return f;
    }
    const f = (v) => a + ((v - lo) / (hi - lo || 1)) * (b - a);
    f.ticks = () => niceTicks(lo, hi, 5);
    f.lo = lo; f.hi = hi;
    return f;
  }
  function svgWrap(w, hgt, body) {
    return '<svg viewBox="0 0 ' + w + ' ' + hgt + '" preserveAspectRatio="xMinYMin meet" role="img">' + body + '</svg>';
  }

  // Horizontal distribution chart: one row per group; box (p25..p75), whisker (p10..p90), median tick,
  // mean dot; or a plain bar for sum/count/mean/p90.
  function hbars(groups, mk, stat, log, dim) {
    const W = 900, LW = 210, RW = 90, rowH = 26, top = 8;
    const H = top + groups.length * rowH + 28;
    const box = stat === 'median';
    let hi = 0, lo = Infinity;
    groups.forEach((g) => {
      const top_ = box ? g.p90 : g.v;
      if (top_ !== null && top_ > hi) hi = top_;
      const low_ = box ? g.p10 : g.v;
      if (low_ !== null && low_ > 0 && low_ < lo) lo = low_;
    });
    if (!isFinite(lo)) lo = 1;
    const x = scale(log ? lo * 0.8 : 0, hi * 1.05 || 1, LW, W - RW, log);
    let s = '<g class="grid">';
    x.ticks().forEach((t) => { s += '<line x1="' + x(t) + '" x2="' + x(t) + '" y1="' + top + '" y2="' + (H - 22) + '"/>'; });
    s += '</g><g class="lbl">';
    x.ticks().forEach((t) => { s += '<text x="' + x(t) + '" y="' + (H - 8) + '" text-anchor="middle">' + esc(fmtM(t, mk, stat)) + '</text>'; });
    s += '</g>';
    groups.forEach((g, i) => {
      const y = top + i * rowH;
      const c = colorFor(dim, g.key);
      const tip = g.key + '\n' + 'n = ' + g.n + (box
        ? '\nmedian ' + fmtM(g.v, mk, stat) + '\nIQR ' + fmtM(g.lo, mk, stat) + ' .. ' + fmtM(g.hi, mk, stat) + '\np10..p90 ' + fmtM(g.p10, mk, stat) + ' .. ' + fmtM(g.p90, mk, stat) + '\nmean ' + fmtM(g.mean, mk, stat)
        : '\n' + STATS[stat] + ' ' + fmtM(g.v, mk, stat)) + '\n(click to filter)';
      s += '<g class="hit" data-f="' + esc(dim) + '" data-v="' + esc(g.key) + '" data-tip="' + esc(tip) + '">';
      s += '<rect x="0" y="' + y + '" width="' + W + '" height="' + rowH + '" fill="transparent"/>';
      s += '<text x="' + (LW - 8) + '" y="' + (y + rowH / 2 + 4) + '" text-anchor="end">' + esc(trunc(g.key, 30)) + '</text>';
      if (g.v === null) {
        s += '<text x="' + (LW + 4) + '" y="' + (y + rowH / 2 + 4) + '" class="lbl">no data</text></g>';
        return;
      }
      if (box) {
        const cy = y + rowH / 2;
        s += '<line x1="' + x(g.p10) + '" x2="' + x(g.p90) + '" y1="' + cy + '" y2="' + cy + '" stroke="' + c + '" stroke-width="1.5"/>';
        s += '<rect x="' + x(g.lo) + '" y="' + (y + 5) + '" width="' + Math.max(2, x(g.hi) - x(g.lo)) + '" height="' + (rowH - 10) + '" fill="' + c + '" fill-opacity=".28" stroke="' + c + '" rx="3"/>';
        s += '<line x1="' + x(g.v) + '" x2="' + x(g.v) + '" y1="' + (y + 3) + '" y2="' + (y + rowH - 3) + '" stroke="' + c + '" stroke-width="3"/>';
        if (g.mean !== null) s += '<circle cx="' + x(g.mean) + '" cy="' + cy + '" r="3" fill="var(--panel)" stroke="' + c + '" stroke-width="1.5"/>';
      } else {
        s += '<rect x="' + LW + '" y="' + (y + 5) + '" width="' + Math.max(1, x(g.v) - LW) + '" height="' + (rowH - 10) + '" fill="' + c + '" rx="3"/>';
      }
      s += '<text x="' + (W - RW + 8) + '" y="' + (y + rowH / 2 + 4) + '">' + esc(fmtM(g.v, mk, stat)) + '</text>';
      s += '<text x="' + (W - 4) + '" y="' + (y + rowH / 2 + 4) + '" text-anchor="end" class="lbl">n=' + g.n + '</text>';
      s += '</g>';
    });
    return svgWrap(W, H, s);
  }

  function distOf(rows, mk, stat) {
    const m = MET[mk];
    const vals = [];
    rows.forEach((r) => { const v = m.get(r); if (v !== null && isFinite(v)) vals.push(v); });
    vals.sort((a, b) => a - b);
    const a = agg(rows, mk, stat);
    let mean = null;
    if (vals.length) { let s = 0; vals.forEach((v) => { s += v; }); mean = s / vals.length; }
    return {
      v: a.v, n: a.n, lo: quantile(vals, 0.25), hi: quantile(vals, 0.75),
      p10: quantile(vals, 0.1), p90: quantile(vals, 0.9), mean: mean,
    };
  }

  // Top-K grouping with the tail folded into "(other)".
  function topGroups(rows, dim, k, sortFn) {
    const g = groupBy(rows, dim);
    let keys = Array.from(g.keys());
    const timeDim = ['date', 'week', 'month'].indexOf(dim) >= 0;
    if (timeDim) keys.sort();
    else keys.sort((a, b) => g.get(b).length - g.get(a).length);
    if (!timeDim && k && keys.length > k) {
      const keep = keys.slice(0, k);
      const other = [];
      keys.slice(k).forEach((kk) => { g.get(kk).forEach((r) => other.push(r)); });
      const m = new Map();
      keep.forEach((kk) => m.set(kk, g.get(kk)));
      m.set('(other)', other);
      return m;
    }
    if (sortFn) keys.sort(sortFn);
    const m = new Map();
    keys.forEach((kk) => m.set(kk, g.get(kk)));
    return m;
  }

  // Stacked 100% (or absolute) horizontal bars: parts is [{key, label, color}], value(rows, part) -> number.
  function stacked(groups, parts, valueFn, norm, fmtFn, dim) {
    const W = 900, LW = 210, RW = 70, rowH = 24, top = 8;
    const H = top + groups.length * rowH + 26;
    let max = 0;
    const totals = groups.map((g) => {
      let t = 0;
      parts.forEach((p) => { t += valueFn(g.rows, p); });
      if (t > max) max = t;
      return t;
    });
    let s = '';
    groups.forEach((g, i) => {
      const y = top + i * rowH;
      const tot = totals[i];
      s += '<g>';
      s += '<text x="' + (LW - 8) + '" y="' + (y + rowH / 2 + 4) + '" text-anchor="end" class="hit" data-f="' + esc(dim) + '" data-v="' + esc(g.key) + '" data-tip="' + esc(g.key + '\n(click to filter)') + '">' + esc(trunc(g.key, 30)) + '</text>';
      let x = LW;
      const span = W - RW - LW;
      parts.forEach((p) => {
        const v = valueFn(g.rows, p);
        if (!v) return;
        const w = norm ? (tot ? (v / tot) * span : 0) : (max ? (v / max) * span : 0);
        const tip = g.key + ' / ' + p.label + '\n' + fmtFn(v) + (tot ? ' (' + ((v / tot) * 100).toFixed(1) + '%)' : '');
        s += '<rect x="' + x + '" y="' + (y + 4) + '" width="' + Math.max(0, w) + '" height="' + (rowH - 8) + '" fill="' + p.color + '" data-tip="' + esc(tip) + '"/>';
        if (w > 34 && norm) s += '<text x="' + (x + w / 2) + '" y="' + (y + rowH / 2 + 4) + '" text-anchor="middle" fill="#fff" style="fill:#fff;pointer-events:none">' + Math.round((v / tot) * 100) + '%</text>';
        x += w;
      });
      s += '<text x="' + (W - 4) + '" y="' + (y + rowH / 2 + 4) + '" text-anchor="end" class="lbl">' + esc(fmtFn(tot)) + '</text>';
      s += '</g>';
    });
    return svgWrap(W, H, s);
  }
  function legend(parts) {
    return '<div class="legend">' + parts.map((p) => '<span><i style="background:' + p.color + '"></i>' + esc(p.label) + '</span>').join('') + '</div>';
  }

  // ---------------------------------------------------------------- shell: header, tabs, sidebar
  const TABS = [
    ['overview', 'Overview'],
    ['compare', 'Compare'],
    ['waste', 'Retries and failures'],
    ['trend', 'Trends'],
    ['scatter', 'Scatter'],
    ['tools', 'Tool use'],
    ['table', 'Sessions'],
  ];
  const APP = $('#app');
  APP.innerHTML = '';
  const TOP = h('header', { class: 'top' });
  const TABBAR = h('nav', { class: 'tabs' });
  const LAYOUT = h('div', { class: 'layout' });
  const SIDE = h('aside', { class: 'side' });
  const MAIN = h('main', { class: 'main' });
  const DRAWER = h('div', { class: 'drawer', role: 'dialog', 'aria-label': 'Session detail' });
  LAYOUT.appendChild(SIDE);
  LAYOUT.appendChild(MAIN);
  APP.appendChild(TOP);
  APP.appendChild(TABBAR);
  APP.appendChild(LAYOUT);
  document.body.appendChild(DRAWER);

  function renderTop() {
    const info = RAW.info || {};
    TOP.innerHTML =
      '<h1>Run analytics</h1><span class="meta">' + esc(N.toLocaleString()) + ' sessions from ' +
      esc(String(info.runs || 0)) + ' runs' + (RAW.generated_at ? ', generated ' + esc(RAW.generated_at) : '') +
      '</span><span class="spacer"></span>';
    TOP.appendChild(sel('Unit', S.grain, grainOpts, (v) => { S.grain = v; render(); },
      'What one row means. Session: a single agent conversation. Attempt: a plan turn plus its verify / gate / re-ask sessions. Plan: every attempt of one plan in one run.'));
    const r = h('button', { class: 'btn', type: 'button' }, 'Reset');
    r.addEventListener('click', () => { S = clone(DEFAULT); render(); });
    TOP.appendChild(r);
    const c = h('a', { class: 'btn', href: 'report.html', style: 'text-decoration:none' }, 'Classic report');
    TOP.appendChild(c);
  }
  function renderTabs() {
    TABBAR.innerHTML = '';
    TABS.forEach((t) => {
      const b = h('button', { type: 'button', class: S.tab === t[0] ? 'on' : '' }, esc(t[1]));
      b.addEventListener('click', () => { S.tab = t[0]; render(); window.scrollTo(0, 0); });
      TABBAR.appendChild(b);
    });
  }
  const facetOpen = {};
  function renderSide() {
    SIDE.innerHTML = '';
    const search = h('div', { class: 'facet' });
    search.innerHTML = '<div class="fh">Search</div>';
    const si = h('input', { type: 'search', placeholder: 'run, set, plan id, model...' });
    si.value = S.q;
    si.addEventListener('input', () => { S.q = si.value; clearTimeout(si._t); si._t = setTimeout(() => render(true), 180); });
    search.appendChild(si);
    SIDE.appendChild(search);

    const dates = h('div', { class: 'facet' });
    dates.innerHTML = '<div class="fh">Date range</div>';
    const dw = h('div', { class: 'dates' });
    const f = h('input', { type: 'date', value: S.from || '' });
    const t = h('input', { type: 'date', value: S.to || '' });
    f.addEventListener('change', () => { S.from = f.value; render(); });
    t.addEventListener('change', () => { S.to = t.value; render(); });
    dw.appendChild(f); dw.appendChild(t);
    dates.appendChild(dw);
    SIDE.appendChild(dates);

    FACETS.forEach((dim) => {
      const counts = {};
      const avail = {};
      ROWS.forEach((r) => { counts[String(r[dim])] = 0; });
      ROWS.forEach((r) => { if (passes(r, dim)) avail[String(r[dim])] = (avail[String(r[dim])] || 0) + 1; });
      const keys = Object.keys(counts).sort((a, b) => (avail[b] || 0) - (avail[a] || 0) || a.localeCompare(b));
      const cur = S.f[dim] || [];
      const box = h('div', { class: 'facet' });
      const head = h('div', { class: 'fh' });
      head.innerHTML = '<span>' + esc(DIMS[dim].label) + '</span>';
      if (cur.length) {
        const clr = h('button', { type: 'button' }, 'clear');
        clr.addEventListener('click', () => { delete S.f[dim]; render(); });
        head.appendChild(clr);
      }
      box.appendChild(head);
      const opts = h('div', { class: 'opts' });
      const limit = facetOpen[dim] ? keys.length : 8;
      keys.slice(0, limit).forEach((k) => {
        const lab = h('label', { class: avail[k] ? '' : 'zero', title: k });
        const cb = h('input', { type: 'checkbox' });
        cb.checked = cur.indexOf(k) >= 0;
        cb.addEventListener('change', () => {
          const list = (S.f[dim] || []).slice();
          const at = list.indexOf(k);
          if (cb.checked && at < 0) list.push(k);
          if (!cb.checked && at >= 0) list.splice(at, 1);
          if (list.length) S.f[dim] = list; else delete S.f[dim];
          render();
        });
        lab.appendChild(cb);
        lab.appendChild(h('span', { class: 'v' }, esc(k)));
        lab.appendChild(h('span', { class: 'c' }, String(avail[k] || 0)));
        opts.appendChild(lab);
      });
      box.appendChild(opts);
      if (keys.length > 8) {
        const more = h('button', { type: 'button', class: 'more' }, facetOpen[dim] ? 'show fewer' : 'show all ' + keys.length);
        more.addEventListener('click', () => { facetOpen[dim] = !facetOpen[dim]; renderSide(); });
        box.appendChild(more);
      }
      SIDE.appendChild(box);
    });
    const n = h('div', { class: 'note' },
      'Model is <b>(unrecorded, host)</b> for runs whose state never recorded one; it is not guessed. ' +
      'Antigravity does not report cost, so cost figures cover OpenCode sessions only; compare hosts on tokens. ' +
      'Token source <b>none</b> means the session log was missing and no totals were recorded.');
    SIDE.appendChild(n);
  }
  function chipsBar() {
    const bar = h('div', { class: 'chips' });
    const unit = S.grain === 'session' ? 'sessions' : S.grain === 'attempt' ? 'attempts' : 'plan runs';
    bar.appendChild(h('span', { class: 'count' }, '<b>' + CUR.length.toLocaleString() + '</b> ' + unit + ' match'));
    const add = (label, onx) => {
      const c = h('span', { class: 'chip' }, esc(label));
      const x = h('button', { type: 'button', 'aria-label': 'remove filter' }, '\u00d7');
      x.addEventListener('click', onx);
      c.appendChild(x);
      bar.appendChild(c);
    };
    for (const d in S.f) {
      if (!S.f[d] || !S.f[d].length) continue;
      add(DIMS[d].label + ': ' + S.f[d].join(', '), () => { delete S.f[d]; render(); });
    }
    if (S.from || S.to) add('Dates: ' + (S.from || '...') + ' to ' + (S.to || '...'), () => { S.from = ''; S.to = ''; render(); });
    if (S.q) add('Search: ' + S.q, () => { S.q = ''; render(); });
    return bar;
  }

  // ---------------------------------------------------------------- KPI strip
  function kpis(rows) {
    const w = h('div', { class: 'kpis' });
    const succ = share(rows.filter((r) => r.outcome !== 'unknown'), (r) => r.outcome === 'success');
    const costed = rows.filter((r) => r.cost !== null && r.cost !== undefined);
    const items = [
      ['Total tokens', fmt(sumOf(rows.filter(HAS_TOK), 'total_tokens'), 'tok'), 'median ' + fmt(agg(rows, 'total_tokens', 'median').v, 'tok') + ' per row'],
      ['Output tokens', fmt(sumOf(rows.filter(HAS_TOK), 'output'), 'tok'), 'median ' + fmt(agg(rows, 'output', 'median').v, 'tok')],
      ['Recorded cost', fmt(sumOf(costed, 'cost'), 'usd'), costed.length + ' of ' + rows.length + ' rows priced'],
      ['Agent time', fmt(sumOf(rows.filter((r) => r.wall), 'wall'), 'dur'), 'median ' + fmt(agg(rows, 'wall', 'median').v, 'dur')],
      ['Tool calls', fmt(sumOf(rows, 'tool_calls'), 'num'), fmt(agg(rows, 'tools_per_step', 'sum').v, 'num2') + ' per LLM step'],
      ['Tool errors', fmt(sumOf(rows, 'tool_errors'), 'num'), fmt(agg(rows, 'error_rate', 'sum').v, 'pct') + ' of calls'],
      ['Success rate', succ === null ? '-' : fmt(succ, 'pct'), 'of rows with a known outcome'],
      ['Retries / recoveries', String(rows.filter((r) => r.restart !== 'first attempt').length), 'rows beyond a first attempt'],
    ];
    items.forEach((it) => {
      const k = h('div', { class: 'kpi' });
      k.innerHTML = '<div class="k">' + esc(it[0]) + '</div><div class="v">' + esc(it[1]) + '</div><div class="s">' + esc(it[2]) + '</div>';
      w.appendChild(k);
    });
    return w;
  }

  // ---------------------------------------------------------------- comparison matrix
  const MATRIX_COLS = [
    ['n', 'n'], ['success', 'Success'], ['total_tokens', 'Tokens (median)'], ['output', 'Output (median)'],
    ['cost', 'Cost (median)'], ['usd_per_mtok', '$/Mtok'], ['wall', 'Time (median)'], ['steps', 'Steps (median)'],
    ['tool_calls', 'Tools (median)'], ['t_read', 'Reads'], ['t_edit', 'Edits'], ['t_shell', 'Shell'],
    ['error_rate', 'Tool err %'], ['cost_sum', 'Total cost'], ['tok_sum', 'Total tokens'],
  ];
  function matrix(rows, dim, limit) {
    const g = topGroups(rows, dim, limit || 30);
    const data = [];
    g.forEach((list, key) => {
      const known = list.filter((r) => r.outcome !== 'unknown');
      data.push({
        key: key, rows: list, n: list.length,
        success: known.length ? share(known, (r) => r.outcome === 'success') : null,
        total_tokens: agg(list, 'total_tokens', 'median').v,
        output: agg(list, 'output', 'median').v,
        cost: agg(list, 'cost', 'median').v,
        usd_per_mtok: agg(list, 'usd_per_mtok', 'sum').v,
        wall: agg(list, 'wall', 'median').v,
        steps: agg(list, 'steps', 'median').v,
        tool_calls: agg(list, 'tool_calls', 'median').v,
        t_read: agg(list, 't_read', 'median').v,
        t_edit: agg(list, 't_edit', 'median').v,
        t_shell: agg(list, 't_shell', 'median').v,
        error_rate: agg(list, 'error_rate', 'sum').v,
        cost_sum: agg(list, 'cost', 'sum').v,
        tok_sum: agg(list, 'total_tokens', 'sum').v,
      });
    });
    const fmts = { n: 'num', success: 'pct', total_tokens: 'tok', output: 'tok', cost: 'usd', usd_per_mtok: 'usd', wall: 'dur', steps: 'num', tool_calls: 'num', t_read: 'num', t_edit: 'num', t_shell: 'num', error_rate: 'pct', cost_sum: 'usd', tok_sum: 'tok' };
    const max = {};
    MATRIX_COLS.forEach((c) => { max[c[0]] = Math.max.apply(null, data.map((d) => d[c[0]] || 0).concat([0])); });
    const t = h('table', { class: 't' });
    let hd = '<thead><tr><th>' + esc(DIMS[dim] ? DIMS[dim].label : dim) + '</th>';
    MATRIX_COLS.forEach((c) => { hd += '<th class="num">' + esc(c[1]) + '</th>'; });
    hd += '</tr></thead><tbody>';
    data.forEach((d) => {
      hd += '<tr class="click" data-f="' + esc(dim) + '" data-v="' + esc(d.key) + '" data-tip="click to filter to ' + esc(d.key) + '">';
      hd += '<td><i style="display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px;background:' + colorFor(dim, d.key) + '"></i>' + esc(trunc(d.key, 44)) + '</td>';
      MATRIX_COLS.forEach((c) => {
        const v = d[c[0]];
        const pct = max[c[0]] ? Math.max(0, Math.min(100, ((v || 0) / max[c[0]]) * 100)) : 0;
        hd += '<td class="num cellbar"><div class="b" style="width:' + pct.toFixed(1) + '%"></div><span>' + esc(fmt(v, fmts[c[0]])) + '</span></td>';
      });
      hd += '</tr>';
    });
    hd += '</tbody>';
    t.innerHTML = hd;
    const w = h('div', { class: 'tablewrap' });
    w.appendChild(t);
    return w;
  }

  // ---------------------------------------------------------------- views
  const VIEWS = {};

  VIEWS.overview = function () {
    MAIN.appendChild(kpis(CUR));
    const p1 = panel('Model by stage', 'Each row is a model; medians per ' + (S.grain === 'session' ? 'session' : S.grain) + '. Bars inside cells are relative to the column maximum. Click a row to filter to it.');
    p1.appendChild(matrix(CUR, 'model'));
    MAIN.appendChild(p1);
    const g = h('div', { class: 'grid2' });
    const p2 = panel('Where the tokens go, by stage', 'Total tokens per stage, split by model.');
    const stages = topGroups(CUR, 'stage', 10);
    const models = Array.from(topGroups(CUR, 'model', 8).keys());
    const parts = models.map((m) => ({ key: m, label: m, color: colorFor('model', m) }));
    const groups = [];
    stages.forEach((rows, key) => groups.push({ key: key, rows: rows }));
    p2.appendChild(h('div', { class: 'chart' }, stacked(groups, parts, (rows, p) => {
      let s = 0;
      rows.forEach((r) => { if (HAS_TOK(r) && (String(r.model) === p.key || (p.key === '(other)' && models.indexOf(String(r.model)) < 0))) s += num(r.total_tokens); });
      return s;
    }, false, (v) => fmt(v, 'tok'), 'stage')));
    p2.appendChild(h('div', null, legend(parts)));
    g.appendChild(p2);
    const p3 = panel('Outcomes by stage', 'Share of rows that succeeded, partly succeeded or failed.');
    const oparts = ['success', 'partial', 'failed', 'unknown'].map((o) => ({ key: o, label: o, color: colorFor('outcome', o) }));
    p3.appendChild(h('div', { class: 'chart' }, stacked(groups, oparts, (rows, p) => rows.filter((r) => r.outcome === p.key).length, true, (v) => fmt(v, 'num'), 'stage')));
    p3.appendChild(h('div', null, legend(oparts)));
    g.appendChild(p3);
    MAIN.appendChild(g);
    const p4 = panel('Stage summary');
    p4.appendChild(matrix(CUR, 'stage'));
    MAIN.appendChild(p4);
  };

  VIEWS.compare = function () {
    const c = S.cmp;
    const p = panel('Compare groups', 'Pick what to compare and the metric. <b>Median</b> draws a box (middle 50%), whiskers (10th to 90th percentile), a thick median tick and a hollow mean dot. Ratios (per step, rates, $/Mtok) use pooled totals under <b>Total</b>. Click a group to filter to it.');
    const row = h('div', { class: 'row' });
    row.appendChild(sel('Compare', c.by, dimOpts(), (v) => { c.by = v; render(); }));
    row.appendChild(sel('Split each by', c.split, dimOpts([['', '(no split)']]), (v) => { c.split = v; render(); }));
    row.appendChild(metricSel('Metric', c.metric, (v) => { c.metric = v; render(); }));
    row.appendChild(sel('Statistic', c.stat, statOpts, (v) => { c.stat = v; render(); }));
    row.appendChild(chk('Log scale', c.log, (v) => { c.log = v; render(); }));
    p.appendChild(row);
    const g = topGroups(CUR, c.by, 20);
    const outer = h('div');
    const renderGroupSet = (rows, title) => {
      const gs = [];
      const inner = c.split && c.split !== c.by ? topGroups(rows, c.split, 12) : null;
      if (inner) {
        inner.forEach((list, key) => { const d = distOf(list, c.metric, c.stat); d.key = key; gs.push(d); });
      } else {
        topGroups(rows, c.by, 20).forEach((list, key) => { const d = distOf(list, c.metric, c.stat); d.key = key; gs.push(d); });
      }
      if (title) outer.appendChild(h('h3', null, esc(DIMS[c.by].label + ': ' + title) + ' <span class="muted">(n=' + rows.length + ')</span>'));
      outer.appendChild(h('div', { class: 'chart' }, hbars(gs, c.metric, c.stat, c.log && c.stat !== 'count', inner ? c.split : c.by)));
    };
    if (c.split && c.split !== c.by) {
      g.forEach((rows, key) => renderGroupSet(rows, key));
    } else {
      renderGroupSet(CUR, null);
    }
    p.appendChild(outer);
    MAIN.appendChild(p);
    const p2 = panel('Side by side', 'Every headline metric for the "Compare" grouping.');
    p2.appendChild(matrix(CUR, c.by));
    MAIN.appendChild(p2);
  };

  VIEWS.waste = function () {
    const rows = CUR;
    const p = panel('What retries and failures cost', 'Spend on rows that did not succeed, and on attempts beyond the first. Verify sessions count as failed when the verifier did not verify. Tokens are the only measure every host reports; cost covers priced rows only.');
    const byOut = groupBy(rows, 'outcome');
    const byRes = groupBy(rows, 'restart');
    const tot = { tok: sumOf(rows.filter(HAS_TOK), 'total_tokens'), cost: sumOf(rows.filter((r) => r.cost), 'cost'), wall: sumOf(rows.filter((r) => r.wall), 'wall') };
    const kp = h('div', { class: 'kpis' });
    const card = (label, list) => {
      list = list || [];
      const tk = sumOf(list.filter(HAS_TOK), 'total_tokens');
      const cs = sumOf(list.filter((r) => r.cost), 'cost');
      const wl = sumOf(list.filter((r) => r.wall), 'wall');
      const k = h('div', { class: 'kpi' });
      k.innerHTML = '<div class="k">' + esc(label) + '</div><div class="v">' + fmt(tot.tok ? tk / tot.tok : null, 'pct') + '</div><div class="s">' +
        esc(list.length + ' rows, ' + fmt(tk, 'tok') + ' tok, ' + fmt(cs, 'usd') + ', ' + fmt(wl, 'dur')) + '</div>';
      kp.appendChild(k);
    };
    card('Tokens on failed rows', byOut.get('failed'));
    card('Tokens on partial rows', byOut.get('partial'));
    card('Tokens on repeat attempts', rows.filter((r) => r.restart !== 'first attempt'));
    card('Tokens on verification', rows.filter((r) => r.role === 'verify' || r.stage === 'verify'));
    p.appendChild(kp);
    MAIN.appendChild(p);

    const g = h('div', { class: 'grid2' });
    const models = Array.from(topGroups(rows, 'model', 10).keys());
    const oparts = ['success', 'partial', 'failed', 'unknown'].map((o) => ({ key: o, label: o, color: colorFor('outcome', o) }));
    const mg = [];
    topGroups(rows, 'model', 10).forEach((list, key) => mg.push({ key: key, rows: list }));
    const p2 = panel('Token spend by outcome, per model', 'Share of each model\'s tokens that went to successful versus failed work.');
    p2.appendChild(h('div', { class: 'chart' }, stacked(mg, oparts, (list, pp) => sumOf(list.filter((r) => HAS_TOK(r) && r.outcome === pp.key), 'total_tokens'), true, (v) => fmt(v, 'tok'), 'model')));
    p2.appendChild(h('div', null, legend(oparts)));
    g.appendChild(p2);
    const rparts = ['first attempt', 'retry', 'recovery'].map((o) => ({ key: o, label: o, color: colorFor('restart', o) }));
    const p3 = panel('Token spend by attempt type, per model', 'How much of each model\'s spend was a second (or later) try.');
    p3.appendChild(h('div', { class: 'chart' }, stacked(mg, rparts, (list, pp) => sumOf(list.filter((r) => HAS_TOK(r) && r.restart === pp.key), 'total_tokens'), true, (v) => fmt(v, 'tok'), 'model')));
    p3.appendChild(h('div', null, legend(rparts)));
    g.appendChild(p3);
    MAIN.appendChild(g);

    const p4 = panel('Failure modes', 'Dispositions of rows that did not succeed, with what they consumed. Click a row to filter.');
    const bad = rows.filter((r) => r.outcome === 'failed' || r.outcome === 'partial');
    p4.appendChild(matrix(bad, 'disposition'));
    MAIN.appendChild(p4);

    const p5 = panel('Plans that needed the most attempts', 'Per plan and run: attempts, and everything those attempts consumed. Click to open the plan\'s sessions.');
    const plans = regrain(CUR_SESS, 'plan').filter((r) => r.attempt > 1 || r.restart !== 'first attempt');
    plans.sort((a, b) => (b.attempt - a.attempt) || (num(b.total_tokens) - num(a.total_tokens)));
    const t = h('table', { class: 't' });
    let s = '<thead><tr><th>Plan</th><th>Set</th><th>Run</th><th>Model</th><th class="num">Attempts</th><th>Final</th><th class="num">Tokens</th><th class="num">Cost</th><th class="num">Time</th><th class="num">Tool calls</th></tr></thead><tbody>';
    plans.slice(0, 60).forEach((r) => {
      s += '<tr class="click" data-f="id6" data-v="' + esc(r.id6) + '"><td class="mono">' + esc(r.id6) + '</td><td>' + esc(r.set) + '</td><td class="mono">' + esc(r.run) + '</td><td>' + esc(r.model) + '</td><td class="num">' + r.attempt +
        '</td><td><span class="pill ' + esc(r.outcome) + '">' + esc(r.disposition) + '</span></td><td class="num">' + fmt(r.total_tokens, 'tok') + '</td><td class="num">' + fmt(r.cost, 'usd') + '</td><td class="num">' + fmt(r.wall, 'dur') + '</td><td class="num">' + fmt(r.tool_calls, 'num') + '</td></tr>';
    });
    if (!plans.length) s += '<tr><td colspan="10" class="empty">No plan needed more than one attempt in this selection.</td></tr>';
    t.innerHTML = s + '</tbody>';
    const w = h('div', { class: 'tablewrap' });
    w.appendChild(t);
    p5.appendChild(w);
    MAIN.appendChild(p5);
  };

  VIEWS.trend = function () {
    const c = S.tr;
    const p = panel('Over time', 'A metric per period, stacked by a dimension. Totals show volume; medians show typical per-row behavior. Click a period to filter to it.');
    const row = h('div', { class: 'row' });
    row.appendChild(sel('Period', c.x, [['date', 'Day'], ['week', 'Week'], ['month', 'Month']], (v) => { c.x = v; render(); }));
    row.appendChild(sel('Stack by', c.by, dimOpts([['', '(none)']]), (v) => { c.by = v; render(); }));
    row.appendChild(metricSel('Metric', c.metric, (v) => { c.metric = v; render(); }));
    row.appendChild(sel('Statistic', c.stat, statOpts, (v) => { c.stat = v; render(); }));
    p.appendChild(row);
    const periods = Array.from(groupBy(CUR.filter((r) => r[c.x]), c.x).keys()).sort();
    const series = c.by ? Array.from(topGroups(CUR, c.by, 8).keys()) : ['all'];
    const stack = c.stat === 'sum' || c.stat === 'count';
    const byP = groupBy(CUR, c.x);
    const vals = periods.map((pp) => {
      const list = byP.get(pp) || [];
      const sg = c.by ? groupBy(list, c.by) : new Map([['all', list]]);
      return series.map((sk) => {
        let l = sg.get(sk) || [];
        if (sk === '(other)') { l = []; sg.forEach((v, k) => { if (series.indexOf(k) < 0) l = l.concat(v); }); }
        return l.length ? agg(l, c.metric, c.stat).v : null;
      });
    });
    const W = 900, H = 320, L = 70, R = 10, T = 10, B = 50;
    let max = 0;
    vals.forEach((vs) => {
      const t = stack ? vs.reduce((a, b) => a + (b || 0), 0) : Math.max.apply(null, vs.map((x) => x || 0));
      if (t > max) max = t;
    });
    const y = scale(0, max * 1.05 || 1, H - B, T, false);
    const bw = (W - L - R) / Math.max(1, periods.length);
    let s = '<g class="grid">';
    y.ticks().forEach((t) => { s += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(t) + '" y2="' + y(t) + '"/>'; });
    s += '</g><g class="lbl">';
    y.ticks().forEach((t) => { s += '<text x="' + (L - 6) + '" y="' + (y(t) + 4) + '" text-anchor="end">' + esc(fmtM(t, c.metric, c.stat)) + '</text>'; });
    const every = Math.ceil(periods.length / 14);
    periods.forEach((pp, i) => { if (i % every === 0) s += '<text x="' + (L + i * bw + bw / 2) + '" y="' + (H - B + 16) + '" text-anchor="middle">' + esc(c.x === 'month' ? pp : pp.slice(5)) + '</text>'; });
    s += '</g>';
    if (stack) {
      periods.forEach((pp, i) => {
        let acc = 0;
        series.forEach((sk, j) => {
          const v = vals[i][j] || 0;
          if (!v) return;
          const y0 = y(acc), y1 = y(acc + v);
          acc += v;
          s += '<rect class="hit" data-f="' + esc(c.x) + '" data-v="' + esc(pp) + '" data-tip="' + esc(pp + '\n' + sk + ': ' + fmtM(v, c.metric, c.stat)) + '" x="' + (L + i * bw + 1) + '" y="' + y1 + '" width="' + Math.max(1, bw - 2) + '" height="' + Math.max(0, y0 - y1) + '" fill="' + (c.by ? colorFor(c.by, sk) : PAL[0]) + '"/>';
        });
      });
    } else {
      series.forEach((sk, j) => {
        let d = '';
        periods.forEach((pp, i) => {
          const v = vals[i][j];
          if (v === null) return;
          d += (d ? 'L' : 'M') + (L + i * bw + bw / 2).toFixed(1) + ',' + y(v).toFixed(1);
        });
        const col = c.by ? colorFor(c.by, sk) : PAL[0];
        s += '<path d="' + d + '" fill="none" stroke="' + col + '" stroke-width="2"/>';
        periods.forEach((pp, i) => {
          const v = vals[i][j];
          if (v === null) return;
          s += '<circle class="hit" data-f="' + esc(c.x) + '" data-v="' + esc(pp) + '" data-tip="' + esc(pp + '\n' + sk + ': ' + fmtM(v, c.metric, c.stat)) + '" cx="' + (L + i * bw + bw / 2) + '" cy="' + y(v) + '" r="3.5" fill="' + col + '"/>';
        });
      });
    }
    p.appendChild(h('div', { class: 'chart' }, svgWrap(W, H, s)));
    if (c.by) p.appendChild(h('div', null, legend(series.map((sk) => ({ label: sk, color: colorFor(c.by, sk) })))));
    MAIN.appendChild(p);
  };

  VIEWS.scatter = function () {
    const c = S.sc;
    const p = panel('Scatter', 'One point per row. Look for clusters and outliers, for example sessions with many tool calls but few tokens, or long wall time with little activity. Click a point to open it.');
    const row = h('div', { class: 'row' });
    row.appendChild(metricSel('X', c.x, (v) => { c.x = v; render(); }));
    row.appendChild(metricSel('Y', c.y, (v) => { c.y = v; render(); }));
    row.appendChild(sel('Color by', c.color, dimOpts(), (v) => { c.color = v; render(); }));
    row.appendChild(chk('Log X', c.logx, (v) => { c.logx = v; render(); }));
    row.appendChild(chk('Log Y', c.logy, (v) => { c.logy = v; render(); }));
    p.appendChild(row);
    const mx = MET[c.x], my = MET[c.y];
    const pts = [];
    CUR.forEach((r) => {
      const a = mx.get(r), b = my.get(r);
      if (a === null || b === null) return;
      if ((c.logx && a <= 0) || (c.logy && b <= 0)) return;
      pts.push([a, b, r]);
    });
    const W = 900, H = 460, L = 70, R = 14, T = 10, B = 40;
    if (!pts.length) { p.appendChild(h('div', { class: 'empty' }, 'No rows have both metrics.')); MAIN.appendChild(p); return; }
    const xs = pts.map((q) => q[0]), ys = pts.map((q) => q[1]);
    const x = scale(c.logx ? Math.min.apply(null, xs) : 0, Math.max.apply(null, xs) * 1.05, L, W - R, c.logx);
    const y = scale(c.logy ? Math.min.apply(null, ys) : 0, Math.max.apply(null, ys) * 1.05, H - B, T, c.logy);
    let s = '<g class="grid">';
    x.ticks().forEach((t) => { s += '<line x1="' + x(t) + '" x2="' + x(t) + '" y1="' + T + '" y2="' + (H - B) + '"/>'; });
    y.ticks().forEach((t) => { s += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(t) + '" y2="' + y(t) + '"/>'; });
    s += '</g><g class="lbl">';
    x.ticks().forEach((t) => { s += '<text x="' + x(t) + '" y="' + (H - B + 16) + '" text-anchor="middle">' + esc(fmt(t, mx.fmt)) + '</text>'; });
    y.ticks().forEach((t) => { s += '<text x="' + (L - 6) + '" y="' + (y(t) + 4) + '" text-anchor="end">' + esc(fmt(t, my.fmt)) + '</text>'; });
    s += '<text x="' + ((L + W) / 2) + '" y="' + (H - 6) + '" text-anchor="middle">' + esc(mx.label) + '</text>';
    s += '</g>';
    const keys = Array.from(topGroups(CUR, c.color, 10).keys());
    pts.forEach((q) => {
      const r = q[2];
      const key = keys.indexOf(String(r[c.color])) >= 0 ? String(r[c.color]) : '(other)';
      const tip = (r.id6 || '?') + ' ' + r.stage + ' attempt ' + r.attempt + '\n' + r.model + ' / ' + r.host + '\n' + mx.label + ': ' + fmt(q[0], mx.fmt) + '\n' + my.label + ': ' + fmt(q[1], my.fmt) + '\n' + r.outcome + ' (' + r.disposition + ')';
      s += '<circle class="hit" data-open="' + r._i + '" data-tip="' + esc(tip) + '" cx="' + x(q[0]).toFixed(1) + '" cy="' + y(q[1]).toFixed(1) + '" r="3.2" fill="' + colorFor(c.color, key) + '" fill-opacity=".62"/>';
    });
    p.appendChild(h('div', { class: 'chart' }, svgWrap(W, H, s)));
    p.appendChild(h('div', { class: 'hint' }, esc(my.label) + ' (vertical) against ' + esc(mx.label) + ' (horizontal); ' + pts.length + ' points.'));
    p.appendChild(h('div', null, legend(keys.map((k) => ({ label: k, color: colorFor(c.color, k) })))));
    MAIN.appendChild(p);
  };

  VIEWS.tools = function () {
    const c = S.tl;
    const p = panel('Tool mix', 'What agents spend their tool calls on. Normalized bars show the mix; switch off normalization to compare volume.');
    const row = h('div', { class: 'row' });
    row.appendChild(sel('Group by', c.by, dimOpts(), (v) => { c.by = v; render(); }));
    row.appendChild(chk('Normalize to 100%', c.norm, (v) => { c.norm = v; render(); }));
    p.appendChild(row);
    const gs = [];
    topGroups(CUR, c.by, 16).forEach((list, key) => gs.push({ key: key, rows: list }));
    const parts = CATS.map((k) => ({ key: k, label: k, color: CAT_COLOR[k] }));
    p.appendChild(h('div', { class: 'chart' }, stacked(gs, parts, (rows, pp) => sumOf(rows, 't_' + pp.key), c.norm, (v) => fmt(v, 'num'), c.by)));
    p.appendChild(h('div', null, legend(parts)));
    MAIN.appendChild(p);

    const p2 = panel('Shell commands by kind', 'Classified from the command text: running tests, git, the aw CLI, inspecting files (cat, ls, rg...), python and lint.');
    const sparts = SHELL.map((k, i) => ({ key: k, label: SHELL_LABEL[k], color: PAL[i % PAL.length] }));
    p2.appendChild(h('div', { class: 'chart' }, stacked(gs, sparts, (rows, pp) => sumOf(rows, 'sh_' + pp.key), c.norm, (v) => fmt(v, 'num'), c.by)));
    p2.appendChild(h('div', null, legend(sparts)));
    MAIN.appendChild(p2);

    const p3 = panel('Per-tool detail', 'Every tool name seen in the selection, with its call count, error count and rate.');
    const tally = {}, errs = {}, users = {};
    CUR.forEach((r) => {
      for (const t in r._tools) { tally[t] = (tally[t] || 0) + r._tools[t]; users[t] = (users[t] || 0) + 1; }
      for (const t in r._terr) errs[t] = (errs[t] || 0) + r._terr[t];
    });
    const names = Object.keys(tally).sort((a, b) => tally[b] - tally[a]);
    const top = tally[names[0]] || 1;
    const t = h('table', { class: 't' });
    let s = '<thead><tr><th>Tool</th><th>Category</th><th class="num">Calls</th><th class="num">Rows using it</th><th class="num">Calls per using row</th><th class="num">Errors</th><th class="num">Error rate</th></tr></thead><tbody>';
    names.forEach((n) => {
      s += '<tr><td class="mono">' + esc(n) + '</td><td>' + esc(TOOL_CAT[n] || 'other') + '</td><td class="num cellbar"><div class="b" style="width:' + ((tally[n] / top) * 100).toFixed(1) + '%"></div><span>' + tally[n].toLocaleString() + '</span></td><td class="num">' + users[n] +
        '</td><td class="num">' + (tally[n] / users[n]).toFixed(1) + '</td><td class="num">' + (errs[n] || 0) + '</td><td class="num">' + fmt((errs[n] || 0) / tally[n], 'pct') + '</td></tr>';
    });
    t.innerHTML = s + '</tbody>';
    const w = h('div', { class: 'tablewrap' });
    w.appendChild(t);
    p3.appendChild(w);
    MAIN.appendChild(p3);
  };

  // ---------------------------------------------------------------- the row table
  const TABLE_COLS = [
    ['date', 'Date', 'txt'], ['run', 'Run', 'mono'], ['set', 'Set', 'txt'], ['id6', 'Plan', 'mono'], ['stage', 'Stage', 'txt'],
    ['attempt', 'Att.', 'num'], ['model', 'Model', 'txt'], ['host', 'Host', 'txt'], ['outcome', 'Outcome', 'pill'],
    ['disposition', 'Disposition', 'txt'], ['total_tokens', 'Tokens', 'tok'], ['output', 'Output', 'tok'], ['cost', 'Cost', 'usd'],
    ['wall', 'Time', 'dur'], ['steps', 'Steps', 'num'], ['tool_calls', 'Tools', 'num'], ['t_read', 'Reads', 'num'],
    ['t_edit', 'Edits', 'num'], ['t_shell', 'Shell', 'num'], ['tool_errors', 'Errors', 'num'],
  ];
  const PAGE = 100;
  VIEWS.table = function () {
    const c = S.tb;
    const p = panel(null);
    const hdr = h('div', { class: 'row' });
    hdr.appendChild(h('h2', { style: 'margin:0;flex:1' }, esc(S.grain === 'session' ? 'Sessions' : S.grain === 'attempt' ? 'Attempts' : 'Plan runs')));
    const csv = h('button', { type: 'button', class: 'btn' }, 'Download CSV');
    csv.addEventListener('click', downloadCsv);
    hdr.appendChild(csv);
    p.appendChild(hdr);
    const rows = CUR.slice();
    const col = TABLE_COLS.find((x) => x[0] === c.sort) ? c.sort : 'start';
    rows.sort((a, b) => {
      const x = a[col], y = b[col];
      if (x === y) return 0;
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      return (x < y ? -1 : 1) * c.dir;
    });
    const pages = Math.max(1, Math.ceil(rows.length / PAGE));
    if (c.page >= pages) c.page = pages - 1;
    const slice = rows.slice(c.page * PAGE, (c.page + 1) * PAGE);
    const t = h('table', { class: 't' });
    let s = '<thead><tr>';
    TABLE_COLS.forEach((k) => {
      const numc = ['num', 'tok', 'usd', 'dur'].indexOf(k[2]) >= 0;
      s += '<th data-sort="' + k[0] + '" class="' + (numc ? 'num ' : '') + (c.sort === k[0] ? 'sorted' + (c.dir > 0 ? ' asc' : '') : '') + '">' + esc(k[1]) + '</th>';
    });
    s += '</tr></thead><tbody>';
    slice.forEach((r) => {
      s += '<tr class="click" data-open="' + r._i + '">';
      TABLE_COLS.forEach((k) => {
        const v = r[k[0]];
        if (k[2] === 'pill') s += '<td><span class="pill ' + esc(v) + '">' + esc(v) + '</span></td>';
        else if (k[2] === 'mono') s += '<td class="mono">' + esc(k[0] === 'run' ? String(v).replace(/^run-/, '') : v) + '</td>';
        else if (k[2] === 'txt') s += '<td>' + esc(trunc(v, 34)) + '</td>';
        else s += '<td class="num">' + esc(k[0] === 'attempt' ? v : fmt(v, k[2])) + '</td>';
      });
      s += '</tr>';
    });
    if (!slice.length) s += '<tr><td colspan="' + TABLE_COLS.length + '" class="empty">Nothing matches the current filters.</td></tr>';
    t.innerHTML = s + '</tbody>';
    t.querySelectorAll('th[data-sort]').forEach((th) => th.addEventListener('click', () => {
      const k = th.getAttribute('data-sort');
      if (c.sort === k) c.dir = -c.dir; else { c.sort = k; c.dir = -1; }
      c.page = 0;
      render();
    }));
    const w = h('div', { class: 'tablewrap' });
    w.appendChild(t);
    p.appendChild(w);
    const pg = h('div', { class: 'pager' });
    const prev = h('button', { type: 'button', class: 'btn' }, 'Previous');
    const next = h('button', { type: 'button', class: 'btn' }, 'Next');
    prev.disabled = c.page <= 0;
    next.disabled = c.page >= pages - 1;
    prev.addEventListener('click', () => { c.page--; render(); });
    next.addEventListener('click', () => { c.page++; render(); });
    pg.appendChild(prev);
    pg.appendChild(h('span', null, 'Page ' + (c.page + 1) + ' of ' + pages + ' (' + rows.length.toLocaleString() + ' rows)'));
    pg.appendChild(next);
    p.appendChild(pg);
    MAIN.appendChild(p);
  };

  function downloadCsv() {
    const cols = ['run', 'set', 'id6', 'kind', 'stage', 'action', 'role', 'attempt', 'restart', 'model', 'host', 'outcome', 'disposition', 'verification', 'date',
      'total_tokens', 'input', 'output', 'reasoning', 'cache_read', 'cost', 'wall', 'steps', 'tool_calls', 'tool_errors', 'tool_seconds', 'files_read', 'files_edited', 'token_source']
      .concat(CATS.map((c) => 't_' + c)).concat(SHELL.map((c) => 'sh_' + c));
    const q = (v) => { v = v === null || v === undefined ? '' : String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    const lines = [cols.join(',')];
    CUR.forEach((r) => lines.push(cols.map((c) => q(r[c])).join(',')));
    const blob = new Blob([lines.join('\n') + '\n'], { type: 'text/csv' });
    const a = h('a', { href: URL.createObjectURL(blob), download: 'run-analytics-' + S.grain + '.csv' });
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 0);
  }

  // ---------------------------------------------------------------- detail drawer
  function openDrawer(idx) {
    const base = ROWS[+idx];
    if (!base) return;
    const siblings = ROWS.filter((r) => r.run === base.run && r.id6 === base.id6);
    siblings.sort((a, b) => (a.attempt - b.attempt) || String(a.role).localeCompare(String(b.role)));
    let s = '<button type="button" class="btn close">Close</button>';
    s += '<h2>' + esc(base.id6 || '(no plan)') + ' <span class="muted">' + esc(base.set) + '</span></h2>';
    s += '<p class="hint mono">' + esc(base.run) + '</p>';
    s += '<dl>';
    const kv = [['Stage', base.stage], ['Attempt', base.attempt + ' of ' + base.attempts_total + (base.recovery ? ' (recovery)' : '')], ['Model', base.model + (base.model_source ? ' (from ' + base.model_source + ')' : '')],
      ['Host', base.host], ['Outcome', base.outcome], ['Disposition', base.disposition], ['Verifier', base.verification || '-'], ['Item status', base.item_status], ['Date', base.date],
      ['Tokens', fmt(base.total_tokens, 'tok') + ' total; ' + fmt(base.input, 'tok') + ' in, ' + fmt(base.output, 'tok') + ' out, ' + fmt(base.reasoning, 'tok') + ' reasoning, ' + fmt(base.cache_read, 'tok') + ' cache read'],
      ['Token source', base.token_source], ['Cost', fmt(base.cost, 'usd')], ['Wall time', fmt(base.wall, 'dur')], ['Time in tools', fmt(base.tool_seconds, 'dur')],
      ['LLM steps', base.steps], ['Tool calls', base.tool_calls + ' (' + base.tool_errors + ' errors)'], ['Files read / edited', base.files_read + ' / ' + base.files_edited]];
    kv.forEach((x) => { s += '<dt>' + esc(x[0]) + '</dt><dd>' + esc(x[1]) + '</dd>'; });
    s += '</dl>';
    const tools = Object.keys(base._tools).sort((a, b) => base._tools[b] - base._tools[a]);
    if (tools.length) {
      s += '<h3>Tools used</h3><table class="t"><tbody>';
      const mx = base._tools[tools[0]];
      tools.forEach((t) => {
        s += '<tr><td class="mono">' + esc(t) + '</td><td class="num cellbar" style="width:60%"><div class="b" style="width:' + ((base._tools[t] / mx) * 100).toFixed(1) + '%"></div><span>' + base._tools[t] + (base._terr[t] ? ' (' + base._terr[t] + ' err)' : '') + '</span></td></tr>';
      });
      s += '</tbody></table>';
    }
    s += '<h3>All sessions for this plan in this run</h3><table class="t"><thead><tr><th>Att.</th><th>Role</th><th>Outcome</th><th class="num">Tokens</th><th class="num">Cost</th><th class="num">Time</th><th class="num">Tools</th></tr></thead><tbody>';
    siblings.forEach((r) => {
      s += '<tr class="click" data-open="' + r._i + '"' + (r._i === base._i ? ' style="font-weight:600"' : '') + '><td>' + r.attempt + '</td><td>' + esc(r.role) + '</td><td><span class="pill ' + esc(r.outcome) + '">' + esc(r.outcome) + '</span></td><td class="num">' + fmt(r.total_tokens, 'tok') + '</td><td class="num">' + fmt(r.cost, 'usd') + '</td><td class="num">' + fmt(r.wall, 'dur') + '</td><td class="num">' + r.tool_calls + '</td></tr>';
    });
    s += '</tbody></table>';
    s += '<p class="hint">Inspect the full transcript with <span class="mono">aw runs ' + esc(base.run) + '</span>.</p>';
    DRAWER.innerHTML = s;
    DRAWER.querySelector('.close').addEventListener('click', closeDrawer);
    DRAWER.classList.add('open');
  }
  function closeDrawer() { DRAWER.classList.remove('open'); }
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDrawer(); });

  // ---------------------------------------------------------------- render loop
  function render(keepSide) {
    recompute();
    saveHash();
    renderTop();
    renderTabs();
    if (!keepSide) renderSide();
    MAIN.innerHTML = '';
    MAIN.appendChild(chipsBar());
    if (!ROWS.length) {
      MAIN.appendChild(h('div', { class: 'panel empty' }, 'No sessions were found. Run <span class="mono">aw runs analyze</span> after a driver run.'));
      return;
    }
    if (!CUR.length) {
      MAIN.appendChild(h('div', { class: 'panel empty' }, 'Nothing matches the current filters.'));
      return;
    }
    (VIEWS[S.tab] || VIEWS.overview)();
  }
  window.addEventListener('hashchange', () => { loadHash(); render(); });
  loadHash();
  render();
})();
