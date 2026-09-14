(function () {
  "use strict";
  var RAW = document.getElementById('embedded-data').textContent.trim();
  var MODEL = JSON.parse(document.getElementById('view-model').textContent);
  var PAGE = MODEL.raw_view_page_size || 100;
  function inflate(b64) {
    // Decoded lazily and only on demand: the raw view is the sole consumer, and a
    // corpus-scale payload should not be parsed to draw the overview.
    var bin = atob(b64), bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) { bytes[i] = bin.charCodeAt(i); }
    if (typeof DecompressionStream === 'undefined') { return null; }
    return new Response(
      new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))
    ).text().then(JSON.parse);
  }
  var state = { page: 0, data: null };
  function setPressed(group, value) {
    var buttons = document.querySelectorAll('[data-group="' + group + '"]');
    for (var i = 0; i < buttons.length; i++) {
      var pressed = buttons[i].getAttribute('data-value') === value;
      buttons[i].setAttribute('aria-pressed', pressed ? 'true' : 'false');
    }
  }
  function renderPage() {
    var body = document.getElementById('raw-body');
    var status = document.getElementById('raw-status');
    if (!body || !state.data) { return; }
    var cols = state.data.columns, total = state.data.row_count;
    var start = state.page * PAGE, end = Math.min(start + PAGE, total);
    body.textContent = '';
    for (var r = start; r < end; r++) {
      var tr = document.createElement('tr');
      for (var c = 0; c < cols.length; c++) {
        var td = document.createElement('td');
        var col = state.data.data[cols[c]] || [];
        var cell = col[r];
        // Assigned via textContent only: the DOM text API escapes by construction, so a
        // hostile cell cannot become markup on the client either.
        td.textContent = cell === null || cell === undefined ? '' : String(cell);
        tr.appendChild(td);
      }
      body.appendChild(tr);
    }
    if (status) {
      status.textContent = 'Showing rows ' + (total ? start + 1 : 0) + ' to ' + end +
        ' of ' + total + '. Rows are paginated; the full set is never materialized.';
    }
  }
  document.addEventListener('click', function (event) {
    var target = event.target;
    if (!target || !target.getAttribute) { return; }
    if (target.getAttribute('aria-disabled') === 'true') { return; }
    var group = target.getAttribute('data-group');
    if (group) { setPressed(group, target.getAttribute('data-value')); return; }
    var step = target.getAttribute('data-page-step');
    if (step && state.data) {
      var pages = Math.ceil(state.data.row_count / PAGE);
      state.page = Math.min(Math.max(0, state.page + parseInt(step, 10)), pages - 1);
      renderPage();
    }
  });
  var loader = document.getElementById('load-raw');
  if (loader) {
    loader.addEventListener('click', function () {
      var result = inflate(RAW);
      var status = document.getElementById('raw-status');
      if (!result) {
        if (status) { status.textContent = 'This browser cannot inflate the embedded payload; the companion JSON file beside this document carries the same rows.'; }
        return;
      }
      result.then(function (data) { state.data = data; state.page = 0; renderPage(); });
    });
  }
})();
