// ── RetailMIS Dashboard Charts ──────────────────────
// All chart functions are global so dashboard.html can call them.

const COLORS = {
  mint:   '#a8f0de',
  lav:    '#c9b8ff',
  peach:  '#ffc9a8',
  sky:    '#a8d8f0',
  rose:   '#ffb8c8',
  sage:   '#b8f0c0',
  lemon:  '#f0eda8',
  warn:   '#ffd49a',
  muted:  '#5a6380',
  grid:   'rgba(120,160,255,0.08)',
  text:   '#9aa3b8',
  card:   '#0f1c35',
};

// Apply global Chart.js defaults
Chart.defaults.color          = COLORS.text;
Chart.defaults.font.family    = "'Plus Jakarta Sans', sans-serif";
Chart.defaults.font.size      = 12;
Chart.defaults.animation.duration = 800;

const TIP = {
  backgroundColor: '#132240',
  borderColor:     'rgba(120,160,255,0.2)',
  borderWidth:     1,
  titleColor:      '#edf0f7',
  bodyColor:       '#9aa3b8',
  padding:         12,
  cornerRadius:    8,
};

// ── helper: safe canvas context ──────────────────────
function ctx(id) {
  var el = document.getElementById(id);
  if (!el) { console.warn('Canvas not found: ' + id); return null; }
  return el;
}

// ════════════════════════════════════════════════════
// 1. REVENUE TREND + FORECAST
// ════════════════════════════════════════════════════
function drawRevenueTrend(labels, revenues, forecastVals, upperVals, lowerVals) {
  var el = ctx('revChart');
  if (!el) return;

  // Replace null with NaN so Chart.js handles gaps
  function clean(arr) {
    if (!arr || !Array.isArray(arr)) return [];
    return arr.map(function(v) { return (v === null || v === undefined) ? NaN : Number(v); });
  }

  var actuals  = clean(revenues);
  var forecast = clean(forecastVals);
  var upper    = clean(upperVals);
  var lower    = clean(lowerVals);

  var gradient = el.getContext('2d').createLinearGradient(0, 0, 0, 280);
  gradient.addColorStop(0,   'rgba(168,240,222,0.25)');
  gradient.addColorStop(1,   'rgba(168,240,222,0.00)');

  new Chart(el, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label:           'Actual Revenue',
          data:            actuals,
          borderColor:     COLORS.mint,
          backgroundColor: gradient,
          borderWidth:     2.5,
          pointRadius:     3,
          pointHoverRadius:6,
          pointBackgroundColor: COLORS.mint,
          tension:         0.35,
          fill:            true,
          spanGaps:        false,
        },
        {
          label:           'Forecast',
          data:            forecast,
          borderColor:     COLORS.lav,
          backgroundColor: 'transparent',
          borderWidth:     2,
          borderDash:      [7, 4],
          pointRadius:     4,
          pointBackgroundColor: COLORS.lav,
          tension:         0.35,
          fill:            false,
          spanGaps:        false,
        },
        {
          label:           'Upper Bound',
          data:            upper,
          borderColor:     'rgba(201,184,255,0.25)',
          backgroundColor: 'rgba(201,184,255,0.07)',
          borderWidth:     1,
          borderDash:      [3, 3],
          pointRadius:     0,
          fill:            '+1',
          spanGaps:        false,
        },
        {
          label:           'Lower Bound',
          data:            lower,
          borderColor:     'rgba(201,184,255,0.25)',
          backgroundColor: 'transparent',
          borderWidth:     1,
          borderDash:      [3, 3],
          pointRadius:     0,
          fill:            false,
          spanGaps:        false,
        },
      ],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: {
          grid:  { color: COLORS.grid },
          ticks: { color: COLORS.muted, maxRotation: 45, maxTicksLimit: 10 },
        },
        y: {
          grid:  { color: COLORS.grid },
          ticks: {
            color: COLORS.muted,
            callback: function(v) { return '£' + Number(v).toLocaleString(); },
          },
        },
      },
      plugins: {
        legend: {
          display:  true,
          position: 'top',
          labels:   { boxWidth: 10, padding: 14, color: COLORS.text, font: { size: 11 } },
        },
        tooltip: Object.assign({}, TIP, {
          callbacks: {
            label: function(c) {
              if (isNaN(c.parsed.y)) return null;
              return ' ' + c.dataset.label + ': £' + c.parsed.y.toLocaleString();
            },
          },
        }),
      },
    },
  });
}

// ════════════════════════════════════════════════════
// 2. TOP PRODUCTS (horizontal bar)
// ════════════════════════════════════════════════════
function drawProducts(labels, revenues) {
  var el = ctx('prodChart');
  if (!el) return;

  var n = (revenues || []).length;
  var colors = (revenues || []).map(function(_, i) {
    return i === n - 1 ? COLORS.mint : 'rgba(168,240,222,' + (0.75 - i * 0.07) + ')';
  });

  new Chart(el, {
    type: 'bar',
    data: {
      labels: (labels || []).map(function(l) {
        return l.length > 28 ? l.substring(0, 26) + '…' : l;
      }),
      datasets: [{
        data:            revenues || [],
        backgroundColor: colors,
        borderRadius:    6,
        borderSkipped:   false,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      scales: {
        x: {
          grid:  { color: COLORS.grid },
          ticks: { color: COLORS.muted, callback: function(v) { return '£' + Number(v).toLocaleString(); } },
        },
        y: {
          grid:  { display: false },
          ticks: { color: COLORS.text, font: { size: 11 } },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: Object.assign({}, TIP, {
          callbacks: { label: function(c) { return ' £' + c.parsed.x.toLocaleString(); } },
        }),
      },
    },
  });
}

// ════════════════════════════════════════════════════
// 3. COUNTRY DOUGHNUT
// ════════════════════════════════════════════════════
function drawCountries(labels, revenues) {
  var el = ctx('countryChart');
  if (!el) return;

  var palette = [COLORS.mint, COLORS.lav, COLORS.peach, COLORS.sky,
                 COLORS.rose, COLORS.sage, COLORS.lemon, COLORS.warn];

  new Chart(el, {
    type: 'doughnut',
    data: {
      labels: labels || [],
      datasets: [{
        data:            revenues || [],
        backgroundColor: palette,
        borderWidth:     2,
        borderColor:     COLORS.card,
        hoverOffset:     6,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: {
          display:  true,
          position: 'right',
          labels:   { boxWidth: 10, padding: 12, color: COLORS.text, font: { size: 11 } },
        },
        tooltip: Object.assign({}, TIP, {
          callbacks: { label: function(c) { return ' ' + c.label + ': £' + c.parsed.toLocaleString(); } },
        }),
      },
    },
  });
}

// ════════════════════════════════════════════════════
// 4. RFM PIE
// ════════════════════════════════════════════════════
function drawRFM(labels, counts) {
  var el = ctx('rfmChart');
  if (!el) return;

  var segColors = {
    'Champions':           COLORS.lemon,
    'Loyal Customers':     COLORS.mint,
    'Potential Loyalists': COLORS.sky,
    'At Risk':             COLORS.peach,
    'Lost':                COLORS.rose,
  };
  var colors = (labels || []).map(function(l) { return segColors[l] || COLORS.lav; });

  new Chart(el, {
    type: 'pie',
    data: {
      labels: labels || [],
      datasets: [{
        data:            counts || [],
        backgroundColor: colors,
        borderWidth:     2,
        borderColor:     COLORS.card,
        hoverOffset:     5,
      }],
    },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display:  true,
          position: 'bottom',
          labels:   { boxWidth: 10, padding: 10, color: COLORS.text, font: { size: 10 } },
        },
        tooltip: Object.assign({}, TIP, {
          callbacks: { label: function(c) { return ' ' + c.label + ': ' + c.parsed + ' customers'; } },
        }),
      },
    },
  });
}

// ════════════════════════════════════════════════════
// 5. SEASONAL HEATMAPS (day-of-week + month)
// ════════════════════════════════════════════════════
function drawHeatmap(dowData, monthData) {

  // Day of week
  var dowEl = ctx('dowChart');
  if (dowEl && dowData && Object.keys(dowData).length > 0) {
    var days = Object.keys(dowData);
    var dVals = days.map(function(d) { return dowData[d]; });
    var maxD  = Math.max.apply(null, dVals) || 1;

    new Chart(dowEl, {
      type: 'bar',
      data: {
        labels: days,
        datasets: [{
          data: dVals,
          backgroundColor: dVals.map(function(v) {
            return 'rgba(168,240,222,' + (0.2 + (v / maxD) * 0.75) + ')';
          }),
          borderRadius:  5,
          borderSkipped: false,
        }],
      },
      options: {
        responsive:          true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: Object.assign({}, TIP, {
            callbacks: { label: function(c) { return ' £' + c.parsed.y.toLocaleString(); } },
          }),
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: COLORS.muted } },
          y: { grid: { color: COLORS.grid }, ticks: { color: COLORS.muted, callback: function(v) { return '£' + Number(v).toLocaleString(); } } },
        },
      },
    });
  }

  // Month
  var monthEl = ctx('monthChart');
  if (monthEl && monthData && Object.keys(monthData).length > 0) {
    var months = Object.keys(monthData);
    var mVals  = months.map(function(m) { return monthData[m]; });
    var maxM   = Math.max.apply(null, mVals) || 1;

    new Chart(monthEl, {
      type: 'bar',
      data: {
        labels: months.map(function(m) { return m.substring(0, 3); }),
        datasets: [{
          data: mVals,
          backgroundColor: mVals.map(function(v) {
            return 'rgba(201,184,255,' + (0.2 + (v / maxM) * 0.75) + ')';
          }),
          borderRadius:  5,
          borderSkipped: false,
        }],
      },
      options: {
        responsive:          true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: Object.assign({}, TIP, {
            callbacks: { label: function(c) { return ' £' + c.parsed.y.toLocaleString(); } },
          }),
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: COLORS.muted } },
          y: { grid: { color: COLORS.grid }, ticks: { color: COLORS.muted, callback: function(v) { return '£' + Number(v).toLocaleString(); } } },
        },
      },
    });
  }
}

// ════════════════════════════════════════════════════
// 6. KPI COUNTER ANIMATION
// ════════════════════════════════════════════════════
function animateCounters() {
  document.querySelectorAll('[data-count]').forEach(function(el) {
    var raw    = el.getAttribute('data-count');
    var target = parseFloat(raw.replace(/,/g, ''));
    var prefix = el.getAttribute('data-prefix') || '';
    var isFloat= el.getAttribute('data-float') === 'true';
    if (isNaN(target)) return;
    var steps   = 60;
    var inc     = target / steps;
    var current = 0;
    var timer   = setInterval(function() {
      current = Math.min(current + inc, target);
      el.textContent = prefix + (isFloat ? current.toFixed(2) : Math.round(current).toLocaleString());
      if (current >= target) clearInterval(timer);
    }, 1200 / steps);
  });
}

// ════════════════════════════════════════════════════
// 7. REVENUE PROGRESS BARS
// ════════════════════════════════════════════════════
function setRevenueBars() {
  setTimeout(function() {
    document.querySelectorAll('.revenue-bar[data-pct]').forEach(function(b) {
      b.style.width = b.getAttribute('data-pct') + '%';
    });
  }, 400);
}

// ════════════════════════════════════════════════════
// INIT on DOM ready
// ════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', function() {
  animateCounters();
  setRevenueBars();
});