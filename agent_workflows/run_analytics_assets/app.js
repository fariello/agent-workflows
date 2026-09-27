(function () {
  "use strict";

  var RAW = (document.getElementById('embedded-data') || {}).textContent || '';
  RAW = RAW.trim();
  var MODEL_EL = document.getElementById('view-model');
  var MODEL = MODEL_EL ? JSON.parse(MODEL_EL.textContent) : {};
  var PAGE = MODEL.raw_view_page_size || 100;

  var METRICS = {
    'cost': { col: 'cost_usd', label: 'Cost (USD)', unit: '$' },
    'time': { col: 'wall_seconds', label: 'Wall time', unit: 's' },
    'input tokens': { col: 'input_tokens', label: 'Input tokens', unit: 'tokens' },
    'output tokens': { col: 'output_tokens', label: 'Output tokens', unit: 'tokens' },
    'cache tokens': { col: 'cache_tokens', label: 'Cache tokens', unit: 'tokens' },
    'total tokens': { col: 'total_tokens', label: 'Total tokens', unit: 'tokens' }
  };

  var PHASE_ORDER = [
    { id: 'aggregate', label: 'Aggregate' },
    { id: 'review', label: 'Review' },
    { id: 'execute', label: 'Execute' },
    { id: 'verifier', label: 'Verifier' },
    { id: 'recovery', label: 'Recovery' }
  ];

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
    statMode: 'mean',
    selectedPhase: null,
    dimensions: {},
    phaseStats: {}
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
    if (!numbers || !numbers.length) {
      return { n: 0, sum: 0, mean: 0, stdev: 0, min: 0, max: 0, median: 0, p25: 0, p75: 0 };
    }
    var sorted = numbers.slice().sort(function (a, b) { return a - b; });
    var sum = 0;
    for (var i = 0; i < sorted.length; i++) { sum += sorted[i]; }
    var n = sorted.length;
    var mean = sum / n;
    var sqDiffSum = 0;
    for (var i = 0; i < n; i++) {
      var diff = sorted[i] - mean;
      sqDiffSum += diff * diff;
    }
    var stdev = Math.sqrt(sqDiffSum / n);
    return {
      n: n,
      sum: sum,
      mean: mean,
      stdev: stdev,
      min: sorted[0],
      max: sorted[n - 1],
      median: quantile(sorted, 0.5),
      p25: quantile(sorted, 0.25),
      p75: quantile(sorted, 0.75)
    };
  }

  function updateInteractiveView() {
    if (!state.rows) { return; }

    // 1. Filter rows by dimensions
    var matchingRows = state.rows.filter(function (row) {
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

    var metricConf = METRICS[state.metric] || METRICS['cost'];
    var targetCol = metricConf.col;

    // 2. Compute stats per phase
    var phaseStats = {};
    var yMaxCandidates = [1.0];

    for (var p = 0; p < PHASE_ORDER.length; p++) {
      var pId = PHASE_ORDER[p].id;
      var vals = [];
      for (var r = 0; r < matchingRows.length; r++) {
        var row = matchingRows[r];
        var rowPhase = (row.phase || '').toLowerCase();
        var matchPhase = false;
        if (pId === 'aggregate') {
          matchPhase = (rowPhase === 'aggregate' || rowPhase === 'unknown');
        } else if (pId === 'verifier') {
          matchPhase = (rowPhase === 'verifier' || rowPhase === 'verify');
        } else {
          matchPhase = (rowPhase === pId);
        }
        if (matchPhase) {
          var val = row[targetCol];
          if (val !== null && val !== undefined && typeof val === 'number' && !isNaN(val) && isFinite(val) && val >= 0) {
            vals.push(val);
          }
        }
      }
      var st = calcStats(vals);
      phaseStats[pId] = st;
      if (st.n > 0) {
        if (state.statMode === 'mean') {
          yMaxCandidates.push(st.mean + st.stdev);
        } else {
          yMaxCandidates.push(st.p75);
          yMaxCandidates.push(st.max);
        }
      }
    }
    state.phaseStats = phaseStats;

    // 3. Compute Y-axis scale
    var rawMax = Math.max.apply(null, yMaxCandidates);
    if (!rawMax || rawMax <= 0) { rawMax = 1.0; }
    var orderMag = Math.pow(10, Math.floor(Math.log10(rawMax) || 0));
    var frac = rawMax / (orderMag || 1.0);
    var yMax = 1.0;
    if (frac <= 1.2) { yMax = 1.2 * orderMag; }
    else if (frac <= 2.0) { yMax = 2.0 * orderMag; }
    else if (frac <= 5.0) { yMax = 5.0 * orderMag; }
    else { yMax = 10.0 * orderMag; }

    var yOrigin = 285.0;
    var plotH = 250.0;
    function toY(v) {
      return (yOrigin - (v / yMax) * plotH).toFixed(2);
    }

    // 4. Update SVG
    var svgEl = document.getElementById('phase-chart-svg');
    if (svgEl) {
      var svgParts = [];
      svgParts.push('<title id="phase-chart-desc">Phase comparison for ' + metricConf.label + '</title>');

      // Y-axis grid and tick labels (5 ticks: 0, 25%, 50%, 75%, 100%)
      for (var i = 0; i < 5; i++) {
        var tickVal = (yMax / 4.0) * i;
        var yPos = toY(tickVal);
        svgParts.push('<line class="chart-grid-line" x1="90" y1="' + yPos + '" x2="690" y2="' + yPos + '" stroke="var(--line)" stroke-width="0.5" stroke-dasharray="3 3"/>');
        svgParts.push('<text class="chart-axis-label" x="82" y="' + (parseFloat(yPos) + 4).toFixed(2) + '" text-anchor="end" font-size="11" fill="var(--muted)">' + formatValue(tickVal, state.metric) + '</text>');
      }

      // Axis lines & labels
      svgParts.push('<line class="chart-axis-line" x1="90" y1="35" x2="90" y2="285" stroke="var(--line)" stroke-width="1"/>');
      svgParts.push('<text class="chart-axis-title" x="90" y="22" font-size="12" font-weight="600" fill="var(--ink)">' + metricConf.label + '</text>');
      svgParts.push('<line class="chart-axis-line" x1="90" y1="285" x2="690" y2="285" stroke="var(--line)" stroke-width="1"/>');

      var xPositions = [150, 270, 390, 510, 630];
      for (var idx = 0; idx < PHASE_ORDER.length; idx++) {
        var pInfo = PHASE_ORDER[idx];
        var x = xPositions[idx];
        var st = phaseStats[pInfo.id];
        var isSelected = state.selectedPhase === pInfo.id;

        if (isSelected) {
          svgParts.push('<rect class="phase-col-selected" x="' + (x - 48) + '" y="35" width="96" height="250" rx="4" fill="rgba(11, 79, 158, 0.12)"/>');
        }

        svgParts.push('<text class="phase-col-label' + (isSelected ? ' selected' : '') + '" x="' + x + '" y="303" text-anchor="middle" font-size="13" font-weight="600" fill="var(--ink)">' + pInfo.label + '</text>');
        svgParts.push('<text class="phase-count-label" x="' + x + '" y="321" text-anchor="middle" font-size="11" fill="var(--muted)">n=' + st.n + '</text>');

        if (st.n > 0) {
          if (state.statMode === 'mean') {
            var yMean = toY(st.mean);
            var yTop = toY(Math.min(yMax, st.mean + st.stdev));
            var yBot = toY(Math.max(0, st.mean - st.stdev));
            svgParts.push('<line class="error-bar-line" x1="' + x + '" y1="' + yTop + '" x2="' + x + '" y2="' + yBot + '" stroke="#0b4f9e" stroke-width="2.5" stroke-linecap="round"/>');
            svgParts.push('<line class="error-bar-cap" x1="' + (x - 14) + '" y1="' + yTop + '" x2="' + (x + 14) + '" y2="' + yTop + '" stroke="#0b4f9e" stroke-width="2.5"/>');
            svgParts.push('<line class="error-bar-cap" x1="' + (x - 14) + '" y1="' + yBot + '" x2="' + (x + 14) + '" y2="' + yBot + '" stroke="#0b4f9e" stroke-width="2.5"/>');
            svgParts.push('<circle class="stat-marker" cx="' + x + '" cy="' + yMean + '" r="6" fill="#0b4f9e" stroke="#ffffff" stroke-width="2"/>');
            var yLabel = Math.max(22, parseFloat(yTop) - 6).toFixed(2);
            svgParts.push('<text class="stat-value-label" x="' + x + '" y="' + yLabel + '" text-anchor="middle" font-size="11" font-weight="600" fill="var(--ink)">' + formatValue(st.mean, state.metric) + '</text>');
          } else {
            var yMed = toY(st.median);
            var yP25 = toY(st.p25);
            var yP75 = toY(st.p75);
            var yMin = toY(st.min);
            var yMaxPoint = toY(Math.min(yMax, st.max));
            var boxHeight = Math.max(2, parseFloat(yP25) - parseFloat(yP75));

            svgParts.push('<line class="error-bar-line" x1="' + x + '" y1="' + yMaxPoint + '" x2="' + x + '" y2="' + yMin + '" stroke="#0b4f9e" stroke-width="1.5" stroke-dasharray="2 2"/>');
            svgParts.push('<line class="error-bar-cap" x1="' + (x - 8) + '" y1="' + yMaxPoint + '" x2="' + (x + 8) + '" y2="' + yMaxPoint + '" stroke="#0b4f9e" stroke-width="2"/>');
            svgParts.push('<line class="error-bar-cap" x1="' + (x - 8) + '" y1="' + yMin + '" x2="' + (x + 8) + '" y2="' + yMin + '" stroke="#0b4f9e" stroke-width="2"/>');
            svgParts.push('<rect class="iqr-box" x="' + (x - 18) + '" y="' + yP75 + '" width="36" height="' + boxHeight.toFixed(2) + '" rx="2" fill="rgba(11, 79, 158, 0.2)" stroke="#0b4f9e" stroke-width="2"/>');
            svgParts.push('<line class="median-line" x1="' + (x - 18) + '" y1="' + yMed + '" x2="' + (x + 18) + '" y2="' + yMed + '" stroke="#0b4f9e" stroke-width="3.5" stroke-linecap="round"/>');

            var yLabelMed = Math.max(22, parseFloat(yMaxPoint) - 6).toFixed(2);
            svgParts.push('<text class="stat-value-label" x="' + x + '" y="' + yLabelMed + '" text-anchor="middle" font-size="11" font-weight="600" fill="var(--ink)">' + formatValue(st.median, state.metric) + '</text>');
          }
        } else {
          svgParts.push('<text x="' + x + '" y="160" text-anchor="middle" font-size="12" fill="var(--muted)">no data</text>');
        }

        svgParts.push('<rect class="phase-hitbox" data-phase-id="' + pInfo.id + '" data-phase-name="' + pInfo.id + '" data-phase-idx="' + idx + '" x="' + (x - 55) + '" y="35" width="110" height="250" fill="transparent" cursor="pointer"/>');
      }

      svgEl.innerHTML = svgParts.join('');
    }

    // 5. Update caption
    var capEl = document.getElementById('phase-chart-cap');
    if (capEl) {
      capEl.textContent = metricConf.label + ' across run phases (' + (state.statMode === 'mean' ? 'Mean ± Std Dev' : 'Median / IQR P25–P75') + ')';
    }

    // 6. Update comparison table
    var tbodyEl = document.getElementById('phase-comparison-body');
    if (tbodyEl) {
      var rowsHtml = [];
      for (var p = 0; p < PHASE_ORDER.length; p++) {
        var pInfo = PHASE_ORDER[p];
        var st = phaseStats[pInfo.id];
        if (st.n > 0) {
          rowsHtml.push('<tr>' +
            '<th scope="row">' + pInfo.label + '</th>' +
            '<td>' + st.n + '</td>' +
            '<td>' + formatValue(st.mean, state.metric) + '</td>' +
            '<td>&plusmn;' + formatValue(st.stdev, state.metric) + '</td>' +
            '<td>' + formatValue(st.median, state.metric) + '</td>' +
            '<td>' + formatValue(st.p25, state.metric) + '</td>' +
            '<td>' + formatValue(st.p75, state.metric) + '</td>' +
            '<td>' + formatValue(st.min, state.metric) + '</td>' +
            '<td>' + formatValue(st.max, state.metric) + '</td>' +
            '<td>' + formatValue(st.sum, state.metric) + '</td>' +
            '</tr>');
        } else {
          rowsHtml.push('<tr><th scope="row">' + pInfo.label + '</th><td>0</td><td>&mdash;</td><td>&mdash;</td><td>&mdash;</td><td>&mdash;</td><td>&mdash;</td><td>&mdash;</td><td>&mdash;</td><td>&mdash;</td></tr>');
        }
      }
      tbodyEl.innerHTML = rowsHtml.join('');
    }

    // 7. Update filter summary banner
    var summaryEl = document.getElementById('filter-summary');
    if (summaryEl) {
      var dimParts = [];
      for (var d in state.dimensions) {
        if (Object.prototype.hasOwnProperty.call(state.dimensions, d)) {
          dimParts.push(d + ': ' + state.dimensions[d]);
        }
      }
      var dimStr = dimParts.length ? dimParts.join(', ') : 'None';
      var phaseLabel = state.selectedPhase ? (state.selectedPhase.charAt(0).toUpperCase() + state.selectedPhase.slice(1)) : 'All';
      summaryEl.innerHTML = 'Metric: <strong id="filter-summary-metric">' + metricConf.label + '</strong> &middot; ' +
        'Filters: <strong id="filter-summary-dimensions">' + dimStr + '</strong> &middot; ' +
        'Selected Phase: <strong>' + phaseLabel + '</strong>';
    }

    // 8. Filter raw view table
    if (state.selectedPhase) {
      state.filteredRows = matchingRows.filter(function (row) {
        var rp = (row.phase || '').toLowerCase();
        if (state.selectedPhase === 'aggregate') {
          return rp === 'aggregate' || rp === 'unknown';
        }
        if (state.selectedPhase === 'verifier') {
          return rp === 'verifier' || rp === 'verify';
        }
        return rp === state.selectedPhase;
      });
    } else {
      state.filteredRows = matchingRows;
    }
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

  // Hover tooltip listener
  var chartContainer = document.querySelector('.chart-container');
  var tooltipEl = document.getElementById('chart-tooltip');
  if (chartContainer && tooltipEl) {
    chartContainer.addEventListener('mousemove', function (e) {
      var target = e.target;
      if (target && target.classList && target.classList.contains('phase-hitbox')) {
        var phaseId = target.getAttribute('data-phase-id');
        var st = state.phaseStats ? state.phaseStats[phaseId] : null;
        var pLabel = '';
        for (var i = 0; i < PHASE_ORDER.length; i++) {
          if (PHASE_ORDER[i].id === phaseId) { pLabel = PHASE_ORDER[i].label; break; }
        }
        if (st && st.n > 0) {
          tooltipEl.innerHTML =
            '<div class="tooltip-title">' + pLabel + ' (n=' + st.n + ')</div>' +
            '<div class="tooltip-row"><span>Mean:</span> <strong>' + formatValue(st.mean, state.metric) + ' &plusmn; ' + formatValue(st.stdev, state.metric) + '</strong></div>' +
            '<div class="tooltip-row"><span>Median:</span> <strong>' + formatValue(st.median, state.metric) + '</strong></div>' +
            '<div class="tooltip-row"><span>IQR (P25–P75):</span> <strong>' + formatValue(st.p25, state.metric) + ' &ndash; ' + formatValue(st.p75, state.metric) + '</strong></div>' +
            '<div class="tooltip-row"><span>Min &ndash; Max:</span> <strong>' + formatValue(st.min, state.metric) + ' &ndash; ' + formatValue(st.max, state.metric) + '</strong></div>' +
            '<div class="tooltip-row"><span>Total:</span> <strong>' + formatValue(st.sum, state.metric) + '</strong></div>';
          tooltipEl.style.display = 'block';
          tooltipEl.setAttribute('aria-hidden', 'false');

          var rect = chartContainer.getBoundingClientRect();
          var mouseX = e.clientX - rect.left;
          var mouseY = e.clientY - rect.top;
          var left = Math.min(rect.width - 240, Math.max(10, mouseX + 15));
          var top = Math.max(10, mouseY - 40);
          tooltipEl.style.left = left + 'px';
          tooltipEl.style.top = top + 'px';
          return;
        }
      }
      tooltipEl.style.display = 'none';
      tooltipEl.setAttribute('aria-hidden', 'true');
    });

    chartContainer.addEventListener('mouseleave', function () {
      tooltipEl.style.display = 'none';
      tooltipEl.setAttribute('aria-hidden', 'true');
    });
  }

  // Click listener
  document.addEventListener('click', function (event) {
    var target = event.target;
    if (!target || !target.getAttribute) { return; }
    if (target.getAttribute('aria-disabled') === 'true' || target.hasAttribute('disabled')) { return; }

    var statMode = target.getAttribute('data-stat-mode');
    if (statMode) {
      state.statMode = statMode;
      var statButtons = document.querySelectorAll('[data-stat-mode]');
      for (var i = 0; i < statButtons.length; i++) {
        var pressed = statButtons[i].getAttribute('data-stat-mode') === statMode;
        statButtons[i].setAttribute('aria-pressed', pressed ? 'true' : 'false');
      }
      updateInteractiveView();
      return;
    }

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
        if (state.selectedPhase === val) {
          state.selectedPhase = null;
          setPressed('phase', '');
        } else {
          state.selectedPhase = val;
          setPressed('phase', val);
        }
        updateInteractiveView();
      }
      return;
    }

    if (target.classList && target.classList.contains('phase-hitbox')) {
      var pId = target.getAttribute('data-phase-id');
      if (pId) {
        if (state.selectedPhase === pId) {
          state.selectedPhase = null;
          setPressed('phase', '');
        } else {
          state.selectedPhase = pId;
          setPressed('phase', pId);
        }
        updateInteractiveView();
      }
      return;
    }

    if (group) {
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
