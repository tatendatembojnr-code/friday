"""Soft UI Dashboard HTML template for FRIDAY Command Center."""

SOFT_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
  <title>FRIDAY — Institutional Trading Command Center</title>
  <link href="https://fonts.googleapis.com/css?family=Open+Sans:300,400,600,700" rel="stylesheet" />
  <link href="/assets/css/nucleo-icons.css" rel="stylesheet" />
  <link href="/assets/css/nucleo-svg.css" rel="stylesheet" />
  <link id="pagestyle" href="/assets/css/soft-ui-dashboard.min.css" rel="stylesheet" />
  <style>
    .nav-link.active-tab { background-color: #fff; box-shadow: 0 20px 27px 0 rgba(0,0,0,0.05); border-radius: 0.5rem; font-weight: 700; color: #344767 !important; }
    .tab-pane-custom { display: none; }
    .tab-pane-custom.active { display: block; }
    .log-box { background: #111827; color: #e5e7eb; font-family: monospace; font-size: 12px; padding: 14px; border-radius: 10px; max-height: 460px; overflow-y: auto; white-space: pre-wrap; }
  </style>
</head>
<body class="g-sidenav-show bg-gray-100">
  <aside class="sidenav navbar navbar-vertical navbar-expand-xs border-0 border-radius-xl my-3 fixed-start ms-3 bg-white" id="sidenav-main">
    <div class="sidenav-header">
      <a class="navbar-brand m-0" href="#" onclick="switchTab('dashboard', this)">
        <span class="ms-1 font-weight-bold text-dark" style="font-size:1.1rem;">FRIDAY AI BOT</span>
      </a>
    </div>
    <hr class="horizontal dark mt-0" />
    <div class="collapse navbar-collapse w-auto" id="sidenav-collapse-main">
      <ul class="navbar-nav">
        <li class="nav-item"><a class="nav-link active-tab" href="#" onclick="switchTab('dashboard', this)"><span class="nav-link-text ms-1">Dashboard</span></a></li>
        <li class="nav-item"><a class="nav-link" href="#" onclick="switchTab('markets', this)"><span class="nav-link-text ms-1">Live Markets</span></a></li>
        <li class="nav-item"><a class="nav-link" href="#" onclick="switchTab('journal', this)"><span class="nav-link-text ms-1">AI &amp; Trade Journal</span></a></li>
        <li class="nav-item"><a class="nav-link" href="#" onclick="switchTab('config', this)"><span class="nav-link-text ms-1">Accounts &amp; Config</span></a></li>
        <li class="nav-item"><a class="nav-link" href="#" onclick="switchTab('logs', this)"><span class="nav-link-text ms-1">Live Logs</span></a></li>
      </ul>
    </div>
  </aside>

  <main class="main-content position-relative max-height-vh-100 h-100 border-radius-lg">
    <nav class="navbar navbar-main navbar-expand-lg px-0 mx-4 shadow-none border-radius-xl" id="navbarBlur">
      <div class="container-fluid py-2 px-3 d-flex justify-content-between align-items-center">
        <div>
          <h6 class="font-weight-bolder mb-0">FRIDAY Command Center</h6>
          <span class="text-xs text-secondary" id="sessionInfo">Connecting...</span>
        </div>
        <div class="d-flex gap-2 align-items-center">
          <span id="statusBadge" class="badge bg-gradient-info">--</span>
          <button id="toggleBotBtn" class="btn btn-sm bg-gradient-dark mb-0" onclick="toggleBot()">Pause Bot</button>
          <button class="btn btn-sm bg-gradient-danger mb-0" onclick="closeAllPositions()">Close All</button>
        </div>
      </div>
    </nav>

    <div class="container-fluid py-3">
      <!-- TAB 1: DASHBOARD -->
      <div id="tab-dashboard" class="tab-pane-custom active">
        <div class="row">
          <div class="col-xl col-sm-6 mb-4">
            <div class="card"><div class="card-body p-3">
              <p class="text-sm mb-0 text-capitalize font-weight-bold">Total Balance</p>
              <h5 class="font-weight-bolder mb-0" id="cardBalance">--</h5>
              <span class="text-xs text-secondary" id="cardEquity">Equity: --</span>
            </div></div>
          </div>
          <div class="col-xl col-sm-6 mb-4">
            <div class="card"><div class="card-body p-3">
              <p class="text-sm mb-0 text-capitalize font-weight-bold">Free Margin</p>
              <h5 class="font-weight-bolder mb-0" id="cardMargin">--</h5>
              <span class="text-xs text-secondary" id="cardFloating">Floating: --</span>
            </div></div>
          </div>
          <div class="col-xl col-sm-6 mb-4">
            <div class="card"><div class="card-body p-3">
              <p class="text-sm mb-0 text-capitalize font-weight-bold">Total Profits</p>
              <h5 class="font-weight-bolder text-success mb-0" id="cardProfits">--</h5>
              <span class="text-xs text-secondary" id="cardWinRate">Win Rate: --</span>
            </div></div>
          </div>
          <div class="col-xl col-sm-6 mb-4">
            <div class="card"><div class="card-body p-3">
              <p class="text-sm mb-0 text-capitalize font-weight-bold">Total Losses</p>
              <h5 class="font-weight-bolder text-danger mb-0" id="cardLosses">--</h5>
              <span class="text-xs text-secondary" id="cardLossCount">Closed Losses: --</span>
            </div></div>
          </div>
          <div class="col-xl col-sm-6 mb-4">
            <div class="card"><div class="card-body p-3">
              <p class="text-sm mb-0 text-capitalize font-weight-bold">Open Trades</p>
              <h5 class="font-weight-bolder mb-0" id="cardOpenTrades">--</h5>
              <span class="text-xs text-secondary">Active MT5 Positions</span>
            </div></div>
          </div>
        </div>

        <div class="row">
          <div class="col-lg-6 mb-4">
            <div class="card z-index-2"><div class="card-header pb-0">
              <h6>Equity &amp; Realized P&amp;L Curve</h6>
            </div><div class="card-body p-3">
              <canvas id="equityChart" height="190"></canvas>
            </div></div>
          </div>
          <div class="col-lg-6 mb-4">
            <div class="card z-index-2"><div class="card-header pb-0 d-flex justify-content-between align-items-center">
              <h6 class="mb-0">Live Market Chart (M15)</h6>
              <select id="marketSymbolSelect" class="form-select form-select-sm w-auto" onchange="refreshMarketChart()">
                <option value="EURUSD">EURUSD</option>
                <option value="GBPUSD">GBPUSD</option>
                <option value="USDJPY">USDJPY</option>
                <option value="XAUUSD" selected>XAUUSD</option>
              </select>
            </div><div class="card-body p-3">
              <canvas id="marketChart" height="190"></canvas>
            </div></div>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header pb-0"><h6>Current Open Trades</h6></div>
          <div class="card-body px-0 pt-0 pb-2"><div class="table-responsive p-0">
            <table class="table align-items-center mb-0">
              <thead><tr>
                <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Ticket</th>
                <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Symbol</th>
                <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Side</th>
                <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Lots</th>
                <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Open</th>
                <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Current</th>
                <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">SL / TP</th>
                <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">P&amp;L</th>
                <th class="text-uppercase text-secondary text-xxs font-weight-bolder opacity-7">Action</th>
              </tr></thead>
              <tbody id="openTradesBody"></tbody>
            </table>
          </div></div>
        </div>
      </div>

      <!-- TAB 2: LIVE MARKETS -->
      <div id="tab-markets" class="tab-pane-custom">
        <div class="card mb-4">
          <div class="card-header pb-0"><h6>Live Market Watch &amp; Multi-Timeframe Scanner</h6></div>
          <div class="card-body"><div class="table-responsive">
            <table class="table align-items-center mb-0">
              <thead><tr><th>Symbol</th><th>Bid</th><th>Ask</th><th>Spread (pts)</th><th>M15 Close</th></tr></thead>
              <tbody id="marketWatchBody"></tbody>
            </table>
          </div></div>
        </div>
      </div>

      <!-- TAB 3: AI & TRADE JOURNAL -->
      <div id="tab-journal" class="tab-pane-custom">
        <div class="card mb-4">
          <div class="card-header pb-0"><h6>AI Council Decisions</h6></div>
          <div class="card-body"><div class="table-responsive">
            <table class="table align-items-center mb-0">
              <thead><tr><th>Time</th><th>Symbol</th><th>Dir</th><th>SMC</th><th>AI</th><th>Regime</th><th>Reasoning</th></tr></thead>
              <tbody id="aiJournalBody"></tbody>
            </table>
          </div></div>
        </div>
        <div class="card">
          <div class="card-header pb-0"><h6>Closed Trades History</h6></div>
          <div class="card-body"><div class="table-responsive">
            <table class="table align-items-center mb-0">
              <thead><tr><th>Ticket</th><th>Time</th><th>Symbol</th><th>Dir</th><th>Outcome</th><th>P&amp;L</th></tr></thead>
              <tbody id="closedDealsBody"></tbody>
            </table>
          </div></div>
        </div>
      </div>

      <!-- TAB 4: ACCOUNTS & BOT CONFIG -->
      <div id="tab-config" class="tab-pane-custom">
        <div class="row">
          <div class="col-lg-6 mb-4">
            <div class="card"><div class="card-header pb-0"><h6>MT5 Account &amp; AI Credentials</h6></div>
            <div class="card-body">
              <div class="mb-2"><label class="form-label">MT5 Login</label><input id="cfgLogin" class="form-control form-control-sm" /></div>
              <div class="mb-2"><label class="form-label">MT5 Password</label><input id="cfgPassword" type="password" class="form-control form-control-sm" /></div>
              <div class="mb-2"><label class="form-label">MT5 Server</label><input id="cfgServer" class="form-control form-control-sm" /></div>
              <div class="mb-2"><label class="form-label">Gemini / Groq / OpenAI Key (Optional)</label><input id="cfgGemini" placeholder="GEMINI_API_KEY" class="form-control form-control-sm mb-1" /><input id="cfgGroq" placeholder="GROQ_API_KEY" class="form-control form-control-sm" /></div>
              <button class="btn btn-sm bg-gradient-primary mt-2" onclick="saveConfig()">Save Credentials &amp; Config</button>
              <span id="cfgSaveMsg" class="text-xs ms-2"></span>
            </div></div>
          </div>
          <div class="col-lg-6 mb-4">
            <div class="card"><div class="card-header pb-0"><h6>Risk &amp; Strategy Parameters</h6></div>
            <div class="card-body">
              <div class="mb-2"><label class="form-label">Risk Per Trade (%)</label><input id="cfgRiskPct" type="number" step="0.05" class="form-control form-control-sm" /></div>
              <div class="mb-2"><label class="form-label">Max Open Trades</label><input id="cfgMaxOpen" type="number" class="form-control form-control-sm" /></div>
              <div class="mb-2"><label class="form-label">Min SMC Score (0-100)</label><input id="cfgMinSmc" type="number" class="form-control form-control-sm" /></div>
              <div class="mb-2"><label class="form-label">Default R:R Target</label><input id="cfgRR" type="number" step="0.1" class="form-control form-control-sm" /></div>
              <div class="form-check form-switch mt-2">
                <input class="form-check-input" type="checkbox" id="cfgDryRun" />
                <label class="form-check-label" for="cfgDryRun">Dry-Run Mode (Simulate Orders)</label>
              </div>
            </div></div>
          </div>
        </div>
      </div>

      <!-- TAB 5: LIVE LOGS -->
      <div id="tab-logs" class="tab-pane-custom">
        <div class="card"><div class="card-header pb-0"><h6>FRIDAY Live Logs</h6></div>
        <div class="card-body"><div id="logViewer" class="log-box">Loading...</div></div></div>
      </div>
    </div>
  </main>

  <script src="/assets/js/core/bootstrap.min.js"></script>
  <script src="/assets/js/plugins/chartjs.min.js"></script>
  <script>
    let equityChart = null, marketChart = null, configLoaded = false;

    function switchTab(name, el) {
      document.querySelectorAll('.tab-pane-custom').forEach(t => t.classList.remove('active'));
      document.getElementById('tab-' + name).classList.add('active');
      document.querySelectorAll('.sidenav .nav-link').forEach(a => a.classList.remove('active-tab'));
      if (el) el.classList.add('active-tab');
    }

    async function refreshStatus() {
      try {
        const r = await fetch('/api/status');
        const d = await r.json();
        document.getElementById('sessionInfo').textContent = `${d.session} | Last Update: ${new Date().toLocaleTimeString()}`;
        const badge = document.getElementById('statusBadge');
        badge.textContent = d.paused ? `${d.mode} (PAUSED)` : d.mode;
        badge.className = 'badge ' + (d.paused ? 'bg-gradient-warning' : 'bg-gradient-success');
        document.getElementById('toggleBotBtn').textContent = d.paused ? 'Resume Bot' : 'Pause Bot';

        document.getElementById('cardBalance').textContent = `$${d.balance.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        document.getElementById('cardEquity').textContent = `Equity: $${d.equity.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        document.getElementById('cardMargin').textContent = `$${d.margin_free.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        document.getElementById('cardFloating').textContent = `Floating: ${d.floating_pnl >= 0 ? '+' : ''}$${d.floating_pnl.toFixed(2)}`;
        document.getElementById('cardProfits').textContent = `+$${d.total_profits.toFixed(2)}`;
        document.getElementById('cardWinRate').textContent = `Win Rate: ${d.win_rate_pct}% (${d.win_count}W)`;
        document.getElementById('cardLosses').textContent = `-$${Math.abs(d.total_losses).toFixed(2)}`;
        document.getElementById('cardLossCount').textContent = `Closed Losses: ${d.loss_count}`;
        document.getElementById('cardOpenTrades').textContent = `${d.positions.length} / ${d.max_open_trades}`;

        document.getElementById('openTradesBody').innerHTML = d.positions.length ? d.positions.map(p => `
          <tr>
            <td class="ps-3 text-xs">${p.ticket}</td>
            <td class="text-xs font-weight-bold">${p.symbol}</td>
            <td class="text-xs">${p.type}</td>
            <td class="text-xs">${p.volume}</td>
            <td class="text-xs">${p.price_open}</td>
            <td class="text-xs">${p.price_current}</td>
            <td class="text-xs">${p.sl} / ${p.tp}</td>
            <td class="text-xs font-weight-bold ${p.profit >= 0 ? 'text-success' : 'text-danger'}">${p.profit >= 0 ? '+' : ''}$${p.profit.toFixed(2)}</td>
            <td><button class="btn btn-link text-danger text-xs p-0 mb-0" onclick="closeOne(${p.ticket})">Close</button></td>
          </tr>`).join('') : '<tr><td colspan="9" class="text-center text-xs text-secondary py-3">No open positions</td></tr>';

        document.getElementById('aiJournalBody').innerHTML = d.recent_decisions.map(x => `
          <tr>
            <td class="text-xs">${(x.timestamp||'').slice(11,19)}</td><td class="text-xs font-weight-bold">${x.symbol}</td>
            <td class="text-xs">${x.direction}</td><td class="text-xs">${x.smc_score}</td>
            <td class="text-xs">${x.ai_decision} (${x.ai_confidence}%)</td><td class="text-xs">${x.ai_regime}</td>
            <td class="text-xs text-secondary">${x.ai_reasoning}</td>
          </tr>`).join('');

        document.getElementById('closedDealsBody').innerHTML = d.closed_deals.map(c => `
          <tr>
            <td class="text-xs">${c.ticket}</td><td class="text-xs">${(c.timestamp||'').slice(0,19)}</td>
            <td class="text-xs font-weight-bold">${c.symbol}</td><td class="text-xs">${c.direction}</td>
            <td class="text-xs font-weight-bold ${c.outcome==='WIN'?'text-success':'text-danger'}">${c.outcome}</td>
            <td class="text-xs ${c.pnl>=0?'text-success':'text-danger'}">${c.pnl>=0?'+':''}$${c.pnl.toFixed(2)}</td>
          </tr>`).join('');

        document.getElementById('marketWatchBody').innerHTML = d.market_watch.map(m => `
          <tr><td class="text-xs font-weight-bold">${m.symbol}</td><td class="text-xs">${m.bid}</td><td class="text-xs">${m.ask}</td><td class="text-xs">${m.spread}</td><td class="text-xs">${m.last_close}</td></tr>`).join('');

        document.getElementById('logViewer').textContent = d.logs.join('\\n');
        updateEquityChart(d.equity_curve);

        if (!configLoaded && d.config) {
          document.getElementById('cfgLogin').value = d.config.mt5_login || '';
          document.getElementById('cfgServer').value = d.config.mt5_server || '';
          document.getElementById('cfgRiskPct').value = d.config.risk_per_trade_pct;
          document.getElementById('cfgMaxOpen').value = d.config.max_open_trades;
          document.getElementById('cfgMinSmc').value = d.config.min_smc_score;
          document.getElementById('cfgRR').value = d.config.default_rr_target;
          document.getElementById('cfgDryRun').checked = !!d.config.dry_run;
          configLoaded = true;
        }
      } catch(e) {}
    }

    function updateEquityChart(curve) {
      const ctx = document.getElementById('equityChart').getContext('2d');
      const labels = curve.map(p => p.label);
      const data = curve.map(p => p.value);
      if (!equityChart) {
        equityChart = new Chart(ctx, {
          type: 'line',
          data: { labels, datasets: [{ label: 'Equity ($)', data, borderColor: '#cb0c9f', backgroundColor: 'rgba(203,12,159,0.1)', fill: true, tension: 0.35 }] },
          options: { responsive: true, plugins: { legend: { display: false } } }
        });
      } else {
        equityChart.data.labels = labels;
        equityChart.data.datasets[0].data = data;
        equityChart.update('none');
      }
    }

    async function refreshMarketChart() {
      const sym = document.getElementById('marketSymbolSelect').value;
      try {
        const r = await fetch(`/api/market_chart?symbol=${sym}`);
        const d = await r.json();
        const ctx = document.getElementById('marketChart').getContext('2d');
        if (!marketChart) {
          marketChart = new Chart(ctx, {
            type: 'line',
            data: { labels: d.labels, datasets: [{ label: sym, data: d.closes, borderColor: '#17ad37', backgroundColor: 'rgba(23,173,55,0.1)', fill: true, tension: 0.2 }] },
            options: { responsive: true, plugins: { legend: { display: true } } }
          });
        } else {
          marketChart.data.labels = d.labels;
          marketChart.data.datasets[0].label = sym;
          marketChart.data.datasets[0].data = d.closes;
          marketChart.update('none');
        }
      } catch(e) {}
    }

    async function toggleBot() { await fetch('/api/bot/toggle', {method:'POST'}); refreshStatus(); }
    async function closeOne(ticket) { await fetch('/api/close_position', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ticket})}); refreshStatus(); }
    async function closeAllPositions() { if(confirm('Close all open MT5 positions?')) { await fetch('/api/close_all', {method:'POST'}); refreshStatus(); } }
    async function saveConfig() {
      const payload = {
        mt5_login: document.getElementById('cfgLogin').value,
        mt5_password: document.getElementById('cfgPassword').value,
        mt5_server: document.getElementById('cfgServer').value,
        gemini_api_key: document.getElementById('cfgGemini').value,
        groq_api_key: document.getElementById('cfgGroq').value,
        risk_per_trade_pct: parseFloat(document.getElementById('cfgRiskPct').value),
        max_open_trades: parseInt(document.getElementById('cfgMaxOpen').value),
        min_smc_score: parseInt(document.getElementById('cfgMinSmc').value),
        default_rr_target: parseFloat(document.getElementById('cfgRR').value),
        dry_run: document.getElementById('cfgDryRun').checked
      };
      const r = await fetch('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const res = await r.json();
      document.getElementById('cfgSaveMsg').textContent = res.message || 'Saved!';
    }

    refreshStatus();
    refreshMarketChart();
    setInterval(refreshStatus, 3000);
    setInterval(refreshMarketChart, 10000);
  </script>
</body>
</html>
"""
