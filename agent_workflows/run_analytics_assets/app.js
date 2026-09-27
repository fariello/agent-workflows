(function () {
  "use strict";

  var RAW = (document.getElementById('embedded-data') || {}).textContent || '';
  RAW = RAW.trim();
  var MODEL_EL = document.getElementById('view-model');
  var MODEL = MODEL_EL ? JSON.parse(MODEL_EL.textContent) : {};
  var PAGE = MODEL.raw_view_page_size || 100;

  var METRICS = {
    'time': { col: 'wall_seconds', label: 'Wall time', unit: 's' },
    'cost': { col: 'cost_usd', label: 'Cost (USD)', unit: '$' },
    'input tokens': { col: 'input_tokens', label: 'Input tokens', unit: 'tokens' },
    'output tokens': { col: 'output_tokens', label: 'Output tokens', unit: 'tokens' },
    'cache tokens': { col: 'cache_tokens', label: 'Cache tokens', unit: 'tokens' },
    'total tokens': { col: 'total_tokens', label: 'Total tokens', unit: 'tokens' }
  };

  function inflate(b64) {
    if (!b64) { return null; }
    var bin = atob(b64), bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) { bytes[i] = bin.charCodeAt(i); }
    if (typeof DecompressionStream === 'undefined') { return null; }
    return new Response(
      new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))
    ).text().then(JSON.parse);
  }

  function rowsFromColumnar(payload) {
    if (!payload || !payload.data) { return []; }
    var cols = payload.columns || Object.keys(payload.data);
    var count = payload.row_count || 0;
    var rows = [];
    for (var i = 0; i < count; i++) {
      var row = {};
      for (var j = 0; j < cols.length; j++) {
        var col = cols[j];
        var arr = payload.data[col];
        row[col] = arr ? arr[i] : null;
      }
      rows.push(row);
    }
    return rows;
  }

  var state = {
    page: 0,
    data: null,
    rows: [],
    filteredRows: [],
    metric: 'cost',
    phase: 'aggregate',
    dimensions: {}
  };

  function setPressed(group, value) {
    var buttons = document.querySelectorAll('[data-group="' + group + '"]');
    for (var i = 0; i < buttons.length; i++) {
      var pressed = buttons[i].getAttribute('data-value') === value;
      buttons[i].setAttribute('aria-pressed', pressed ? 'true' : 'false');
    }
  }

  function formatValue(val, metricKey) {
    if (val === null || val === undefined || isNaN(val)) { return '—'; }
    var conf = METRICS[metricKey] || {};
    if (conf.unit === '$') {
      return '$' + val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    if (conf.unit === 's') {
      if (val < 60) { return val.toFixed(1) + 's'; }
      if (val < 3600) {
        var mins = Math.floor(val / 60);
        var rem = (val % 60).toFixed(0);
        return mins + 'm ' + rem + 's (' + val.toFixed(1) + 's)';
      }
      return (val / 3600).toFixed(1) + 'h (' + Math.round(val) + 's)';
    }
    if (conf.unit === 'tokens') {
      return Math.round(val).toLocaleString();
    }
    return typeof val === 'number' ? val.toLocaleString() : String(val);
  }

  function binSeries(numbers, bins) {
    bins = bins || 40;
    var vals = [];
    for (var i = 0; i < numbers.length; i++) {
      var n = numbers[i];
      if (n !== null && n !== undefined && typeof n === 'number' && !isNaN(n) && isFinite(n)) {
        vals.push(n);
      }
    }
    if (!vals.length) {
      return { source_row_count: 0, bin_count: 0, counts: [], min: null, max: null };
    }
    var low = vals[0], high = vals[0];
    for (var i = 1; i < vals.length; i++) {
      if (vals[i] < low) { low = vals[i]; }
      if (vals[i] > high) { high = vals[i]; }
    }
    if (high === low) {
      return { source_row_count: vals.length, bin_count: 1, counts: [vals.length], min: low, max: high };
    }
    var count = Math.min(bins, 40);
    var width = (high - low) / count;
    var counts = new Array(count);
    for (var i = 0; i < count; i++) { counts[i] = 0; }
    for (var i = 0; i < vals.length; i++) {
      var idx = Math.floor((vals[i] - low) / width);
      if (idx >= count) { idx = count - 1; }
      counts[idx]++;
    }
    return { source_row_count: vals.length, bin_count: count, counts: counts, min: low, max: high };
  }

  function seriesPathData(counts, width, height) {
    width = width || 640;
    height = height || 200;
    if (!counts || !counts.length) { return ''; }
    var peak = 0;
    for (var i = 0; i < counts.length; i++) {
      if (counts[i] > peak) { peak = counts[i]; }
    }
    if (peak === 0) { peak = 1; }
    if (counts.length === 1) {
      var y = (height - (counts[0] / peak) * height).toFixed(2);
      return 'M 0.00 ' + y + ' L ' + width.toFixed(2) + ' ' + y;
    }
    var step = width / (counts.length - 1);
    var points = [];
    for (var i = 0; i < counts.length; i++) {
      var x = (step * i).toFixed(2);
      var y = (height - (counts[i] / peak) * height).toFixed(2);
      points.push(x + ' ' + y);
    }
    return 'M ' + points.join(' L ');
  }

  function quantile(sorted, q) {
    if (!sorted.length) { return 0; }
    var pos = (sorted.length - 1) * q;
    var base = Math.floor(pos);
    var rest = pos - base;
    if (sorted[base + 1] !== undefined) {
      return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
    }
    return sorted[base];
  }

  function calcStats(numbers) {
    if (!numbers.length) { return null; }
    var sorted = numbers.slice().sort(function (a, b) { return a - b; });
    var sum = 0;
    for (var i = 0; i < sorted.length; i++) { sum += sorted[i]; }
    var mean = sum / sorted.length;
    var sqDiffSum = 0;
    for (var i = 0; i < sorted.length; i++) {
      var diff = sorted[i] - mean;
      sqDiffSum += diff * diff;
    }
    var stdev = Math.sqrt(sqDiffSum / sorted.length);
    return {
      count: sorted.length,
      sum: sum,
      mean: mean,
      stdev: stdev,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      median: quantile(sorted, 0.5),
      p25: quantile(sorted, 0.25),
      p75: quantile(sorted, 0.75),
      p90: quantile(sorted, 0.90)
    };
  }

  function updateInteractiveView() {
    if (!state.rows) { return; }
    var totalRows = state.rows.length;

    // Filter rows
    state.filteredRows = state.rows.filter(function (row) {
      if (state.phase && state.phase !== 'aggregate' && state.phase !== 'all') {
        var p = (row.phase || '').toLowerCase();
        if (state.phase === 'verifier') {
          if (p !== 'verifier' && p !== 'verify') { return false; }
        } else if (p !== state.phase.toLowerCase()) {
          return false;
        }
      }
      for (var dim in state.dimensions) {
        if (Object.prototype.hasOwnProperty.call(state.dimensions, dim)) {
          var expected = state.dimensions[dim];
          if (String(row[dim] || '') !== expected) {
            return false;
          }
        }
      }
      return true;
    });

    var filteredCount = state.filteredRows.length;
    var pct = totalRows > 0 ? (filteredCount / totalRows * 100).toFixed(1) : '0.0';

    // Extract metric values
    var metricConf = METRICS[state.metric] || METRICS['cost'];
    var targetCol = metricConf.col;
    var numbers = [];
    for (var i = 0; i < state.filteredRows.length; i++) {
      var val = state.filteredRows[i][targetCol];
      if (val !== null && val !== undefined && typeof val === 'number' && !isNaN(val) && isFinite(val)) {
        numbers.push(val);
      }
    }

    var stats = calcStats(numbers);
    var binned = binSeries(numbers, 40);
    var path = seriesPathData(binned.counts, 640, 200);

    // Update filter summary banner
    var summaryEl = document.getElementById('filter-summary');
    if (summaryEl) {
      var dimParts = [];
      for (var d in state.dimensions) {
        if (Object.prototype.hasOwnProperty.call(state.dimensions, d)) {
          dimParts.push(d + ': ' + state.dimensions[d]);
        }
      }
      var dimStr = dimParts.length ? dimParts.join(', ') : 'None';
      var phaseLabel = state.phase === 'aggregate' || state.phase === 'all' ? 'All' : state.phase;
      summaryEl.innerHTML = 'Showing <strong>' + filteredCount + '</strong> of <strong>' + totalRows +
        '</strong> runs (' + pct + '%) &mdash; ' +
        'Metric: <strong>' + metricConf.label + '</strong> &middot; ' +
        'Phase: <strong>' + phaseLabel + '</strong> &middot; ' +
        'Filters: <strong>' + dimStr + '</strong>';
    }

    // Update chart
    var capEl = document.getElementById('chart-interactive-cap');
    if (capEl) {
      capEl.textContent = metricConf.label + ' distribution (' + filteredCount + ' runs)';
    }
    var descEl = document.getElementById('chart-interactive-desc');
    if (descEl) {
      descEl.textContent = metricConf.label + ' distribution for ' + filteredCount + ' runs';
    }
    var pathEl = document.getElementById('chart-interactive-path');
    if (pathEl) {
      pathEl.setAttribute('d', path);
    }
    var minAxisEl = document.getElementById('chart-axis-min');
    if (minAxisEl) {
      minAxisEl.textContent = 'Min: ' + (stats ? formatValue(stats.min, state.metric) : '—');
    }
    var maxAxisEl = document.getElementById('chart-axis-max');
    if (maxAxisEl) {
      maxAxisEl.textContent = 'Max: ' + (stats ? formatValue(stats.max, state.metric) : '—');
    }
    var midAxisEl = document.getElementById('chart-axis-mid');
    if (midAxisEl) {
      midAxisEl.textContent = 'Median: ' + (stats ? formatValue(stats.median, state.metric) : '—');
    }

    var chartSummaryEl = document.getElementById('chart-interactive-summary');
    if (chartSummaryEl) {
      if (stats) {
        chartSummaryEl.textContent = metricConf.label + ': ' + numbers.length +
          ' observations summarized into ' + binned.bin_count + ' bins. ' +
          'Total: ' + formatValue(stats.sum, state.metric) +
          ', Median: ' + formatValue(stats.median, state.metric) +
          ', Mean: ' + formatValue(stats.mean, state.metric) + '.';
      } else {
        chartSummaryEl.textContent = 'No observations match the selected filters.';
      }
    }

    // Update exact statistics table
    function setCell(id, text) {
      var el = document.getElementById(id);
      if (el) { el.textContent = text; }
    }
    setCell('stat-sample-size', stats ? String(stats.count) : '0');
    setCell('stat-total', stats ? formatValue(stats.sum, state.metric) : '—');
    setCell('stat-mean', stats ? formatValue(stats.mean, state.metric) : '—');
    setCell('stat-median', stats ? formatValue(stats.median, state.metric) : '—');
    setCell('stat-p25', stats ? formatValue(stats.p25, state.metric) : '—');
    setCell('stat-p75', stats ? formatValue(stats.p75, state.metric) : '—');
    setCell('stat-p90', stats ? formatValue(stats.p90, state.metric) : '—');
    setCell('stat-min', stats ? formatValue(stats.min, state.metric) : '—');
    setCell('stat-max', stats ? formatValue(stats.max, state.metric) : '—');

    // Reset pagination and update raw table
    state.page = 0;
    renderPage();
  }

  function renderPage() {
    var body = document.getElementById('raw-body');
    var status = document.getElementById('raw-status');
    if (!body || !state.data) { return; }
    var cols = state.data.columns || [];
    var rowsToRender = state.filteredRows || state.rows || [];
    var totalFiltered = rowsToRender.length;
    var totalAll = (state.rows || []).length;
    var start = state.page * PAGE;
    var end = Math.min(start + PAGE, totalFiltered);
    body.textContent = '';
    for (var r = start; r < end; r++) {
      var tr = document.createElement('tr');
      var row = rowsToRender[r];
      for (var c = 0; c < cols.length; c++) {
        var td = document.createElement('td');
        var cell = row ? row[cols[c]] : null;
        td.textContent = cell === null || cell === undefined ? '' : String(cell);
        tr.appendChild(td);
      }
      body.appendChild(tr);
    }
    if (status) {
      status.textContent = 'Showing rows ' + (totalFiltered ? start + 1 : 0) + ' to ' + end +
        ' of ' + totalFiltered + ' filtered runs (' + totalAll + ' total). Rows are paginated.';
    }
  }

  document.addEventListener('click', function (event) {
    var target = event.target;
    if (!target || !target.getAttribute) { return; }
    if (target.getAttribute('aria-disabled') === 'true' || target.hasAttribute('disabled')) { return; }

    var group = target.getAttribute('data-group');
    var val = target.getAttribute('data-value');

    if (group === 'metric') {
      if (val && METRICS[val]) {
        state.metric = val;
        setPressed('metric', val);
        updateInteractiveView();
      }
      return;
    }

    if (group === 'phase') {
      if (val) {
        state.phase = val;
        setPressed('phase', val);
        updateInteractiveView();
      }
      return;
    }

    if (group) {
      // Dimension toggle (model, host, status, etc.)
      if (state.dimensions[group] === val) {
        delete state.dimensions[group];
        target.setAttribute('aria-pressed', 'false');
      } else {
        state.dimensions[group] = val;
        setPressed(group, val);
      }
      updateInteractiveView();
      return;
    }

    var step = target.getAttribute('data-page-step');
    if (step && state.filteredRows) {
      var pages = Math.max(1, Math.ceil(state.filteredRows.length / PAGE));
      state.page = Math.min(Math.max(0, state.page + parseInt(step, 10)), pages - 1);
      renderPage();
    }
  });

  var loader = document.getElementById('load-raw');
  if (loader) {
    loader.addEventListener('click', function () {
      if (state.data && state.rows.length) {
        renderPage();
        return;
      }
      var result = inflate(RAW);
      var status = document.getElementById('raw-status');
      if (!result) {
        if (status) { status.textContent = 'This browser cannot inflate the embedded payload; the companion JSON file beside this document carries the same rows.'; }
        return;
      }
      result.then(function (data) {
        state.data = data;
        state.rows = rowsFromColumnar(data);
        updateInteractiveView();
      });
    });
  }

  // Initial load
  if (MODEL.payload && MODEL.payload.data) {
    state.data = MODEL.payload;
    state.rows = rowsFromColumnar(MODEL.payload);
    updateInteractiveView();
  } else if (RAW) {
    var res = inflate(RAW);
    if (res) {
      res.then(function (data) {
        state.data = data;
        state.rows = rowsFromColumnar(data);
        updateInteractiveView();
      });
    }
  }
})();
