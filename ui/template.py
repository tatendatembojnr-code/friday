"""Exact Soft UI Dashboard 3 (v1.1.0) HTML template for FRIDAY Command Center."""

SOFT_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
  <link rel="icon" type="image/png" href="/assets/img/favicon.png" />
  <title>FRIDAY — Soft UI Trading Dashboard</title>
  <link href="https://fonts.googleapis.com/css?family=Inter:300,400,500,600,700,800" rel="stylesheet" />
  <link href="/assets/css/nucleo-icons.css" rel="stylesheet" />
  <link href="/assets/css/nucleo-svg.css" rel="stylesheet" />
  <link id="pagestyle" href="/assets/css/soft-ui-dashboard.css?v=1.1.0" rel="stylesheet" />
  <style>
    .tab-pane-custom { display: none; }
    .tab-pane-custom.active { display: block; }
    .log-box { background: #111827; color: #e5e7eb; font-family: monospace; font-size: 12px; padding: 14px; border-radius: 10px; max-height: 460px; overflow-y: auto; white-space: pre-wrap; }
  </style>
</head>
<body class="g-sidenav-show bg-gray-100">
  <aside class="sidenav navbar navbar-vertical navbar-expand-xs border-0 border-radius-xl my-3 fixed-start ms-3" id="sidenav-main">
    <div class="sidenav-header">
      <a class="navbar-brand m-0" href="#" onclick="switchTab('dashboard', this, 'Dashboard')">
        <img src="/assets/img/logo-ct-dark.png" class="navbar-brand-img h-100" alt="main_logo" />
        <span class="ms-1 font-weight-bold">FRIDAY AI Bot</span>
      </a>
    </div>
    <hr class="horizontal dark mt-0" />
    <div class="collapse navbar-collapse w-auto" id="sidenav-collapse-main">
      <ul class="navbar-nav">
        <li class="nav-item">
          <a class="nav-link active" href="#" onclick="switchTab('dashboard', this, 'Dashboard')">
            <div class="icon icon-shape icon-sm shadow border-radius-md bg-white text-center me-2 d-flex align-items-center justify-content-center">
              <i class="ni ni-shop text-dark text-sm opacity-10"></i>
            </div>
            <span class="nav-link-text ms-1">Dashboard</span>
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#" onclick="switchTab('markets', this, 'Live Markets')">
            <div class="icon icon-shape icon-sm shadow border-radius-md bg-white text-center me-2 d-flex align-items-center justify-content-center">
              <i class="ni ni-chart-bar-32 text-dark text-sm opacity-10"></i>
            </div>
            <span class="nav-link-text ms-1">Live Markets</span>
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#" onclick="switchTab('journal', this, 'AI & Trade Journal')">
            <div class="icon icon-shape icon-sm shadow border-radius-md bg-white text-center me-2 d-flex align-items-center justify-content-center">
              <i class="ni ni-bullet-list-67 text-dark text-sm opacity-10"></i>
            </div>
            <span class="nav-link-text ms-1">AI &amp; Trade Journal</span>
          </a>
        </li>
        <li class="nav-item mt-3">
          <h6 class="ps-4 ms-2 text-uppercase text-xs font-weight-bolder opacity-6">Configuration</h6>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#" onclick="switchTab('config', this, 'Accounts & Config')">
            <div class="icon icon-shape icon-sm shadow border-radius-md bg-white text-center me-2 d-flex align-items-center justify-content-center">
              <i class="ni ni-settings-gear-65 text-dark text-sm opacity-10"></i>
            </div>
            <span class="nav-link-text ms-1">Accounts &amp; Config</span>
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#" onclick="switchTab('logs', this, 'Live Logs')">
            <div class="icon icon-shape icon-sm shadow border-radius-md bg-white text-center me-2 d-flex align-items-center justify-content-center">
              <i class="ni ni-single-copy-04 text-dark text-sm opacity-10"></i>
            </div>
            <span class="nav-link-text ms-1">Live Logs</span>
          </a>
        </li>
      </ul>
    </div>
    <div class="sidenav-footer mx-3 mt-3">
      <div class="card card-background shadow-none card-background-mask-secondary" id="sidenavCard">
        <div class="full-background" style="background-image: url('/assets/img/curved-images/white-curved.jpg')"></div>
        <div class="card-body text-start p-3 w-100">
          <div class="icon icon-shape icon-sm bg-white shadow text-center mb-3 d-flex align-items-center justify-content-center border-radius-md">
            <i class="ni ni-diamond text-dark text-gradient text-lg top-0" aria-hidden="true"></i>
          </div>
          <div class="docs-info">
            <h6 class="text-white up mb-0">FRIDAY Engine</h6>
            <p class="text-xs font-weight-bold mb-2" id="sidebarSession">SMC + AI Council</p>
            <button class="btn btn-white btn-sm w-100 mb-0" onclick="toggleBot()" id="sidebarToggleBtn">Pause Bot</button>
          </div>
        </div>
      </div>
    </div>
  </aside>

  <main class="main-content position-relative max-height-vh-100 h-100 border-radius-lg">
    <nav class="navbar navbar-main navbar-expand-lg px-0 mx-4 shadow-none border-radius-xl" id="navbarBlur" navbar-scroll="true">
      <div class="container-fluid py-1 px-3">
        <nav aria-label="breadcrumb">
          <ol class="breadcrumb bg-transparent mb-0 pb-0 pt-1 px-0 me-sm-6 me-5">
            <li class="breadcrumb-item text-sm"><a class="opacity-5 text-dark" href="javascript:;">FRIDAY</a></li>
            <li class="breadcrumb-item text-sm text-dark active" id="breadcrumbTitle" aria-current="page">Dashboard</li>
          </ol>
          <h6 class="font-weight-bolder mb-0" id="pageTitle">Dashboard</h6>
        </nav>
        <div class="collapse navbar-collapse mt-sm-0 mt-2 me-md-0 me-sm-4 justify-content-end" id="navbar">
          <ul class="navbar-nav justify-content-end align-items-center gap-2">
            <li class="nav-item"><span id="statusBadge" class="badge badge-sm bg-gradient-success">--</span></li>
            <li class="nav-item"><button id="toggleBotBtn" class="btn btn-outline-primary btn-sm mb-0" onclick="toggleBot()">Pause Bot</button></li>
            <li class="nav-item"><button class="btn bg-gradient-danger btn-sm mb-0" onclick="closeAllPositions()">Close All</button></li>
          </ul>
        </div>
      </div>
    </nav>

    <div class="container-fluid py-4">
      <!-- TAB 1: DASHBOARD -->
      <div id="tab-dashboard" class="tab-pane-custom active">
        <div class="row">
          <div class="col-xl col-sm-6 mb-xl-0 mb-4">
            <div class="card"><div class="card-body p-3"><div class="row">
              <div class="col-8"><div class="numbers">
                <p class="text-sm mb-0 text-capitalize font-weight-bold">Total Balance</p>
                <h5 class="font-weight-bolder mb-0" id="cardBalance">--</h5>
                <span class="text-xs text-secondary" id="cardEquity">Equity: --</span>
              </div></div>
              <div class="col-4 text-end"><div class="icon icon-shape bg-gradient-primary shadow text-center border-radius-md">
                <i class="ni ni-money-coins text-lg opacity-10" aria-hidden="true"></i>
              </div></div>
            </div></div></div>
          </div>
          <div class="col-xl col-sm-6 mb-xl-0 mb-4">
            <div class="card"><div class="card-body p-3"><div class="row">
              <div class="col-8"><div class="numbers">
                <p class="text-sm mb-0 text-capitalize font-weight-bold">Free Margin</p>
                <h5 class="font-weight-bolder mb-0" id="cardMargin">--</h5>
                <span class="text-xs text-secondary" id="cardFloating">Floating: --</span>
              </div></div>
              <div class="col-4 text-end"><div class="icon icon-shape bg-gradient-info shadow text-center border-radius-md">
                <i class="ni ni-world text-lg opacity-10" aria-hidden="true"></i>
              </div></div>
            </div></div></div>
          </div>
          <div class="col-xl col-sm-6 mb-xl-0 mb-4">
            <div class="card"><div class="card-body p-3"><div class="row">
              <div class="col-8"><div class="numbers">
                <p class="text-sm mb-0 text-capitalize font-weight-bold">Total Profits</p>
                <h5 class="font-weight-bolder text-success mb-0" id="cardProfits">--</h5>
                <span class="text-xs text-secondary" id="cardWinRate">Win Rate: --</span>
              </div></div>
              <div class="col-4 text-end"><div class="icon icon-shape bg-gradient-success shadow text-center border-radius-md">
                <i class="ni ni-trophy text-lg opacity-10" aria-hidden="true"></i>
              </div></div>
            </div></div></div>
          </div>
          <div class="col-xl col-sm-6 mb-xl-0 mb-4">
            <div class="card"><div class="card-body p-3"><div class="row">
              <div class="col-8"><div class="numbers">
                <p class="text-sm mb-0 text-capitalize font-weight-bold">Total Losses</p>
                <h5 class="font-weight-bolder text-danger mb-0" id="cardLosses">--</h5>
                <span class="text-xs text-secondary" id="cardLossCount">Closed: --</span>
              </div></div>
              <div class="col-4 text-end"><div class="icon icon-shape bg-gradient-danger shadow text-center border-radius-md">
                <i class="ni ni-fat-remove text-lg opacity-10" aria-hidden="true"></i>
              </div></div>
            </div></div></div>
          </div>
          <div class="col-xl col-sm-6">
            <div class="card"><div class="card-body p-3"><div class="row">
              <div class="col-8"><div class="numbers">
                <p class="text-sm mb-0 text-capitalize font-weight-bold">Open Trades</p>
                <h5 class="font-weight-bolder mb-0" id="cardOpenTrades">--</h5>
                <span class="text-xs text-secondary">Active MT5</span>
              </div></div>
              <div class="col-4 text-end"><div class="icon icon-shape bg-gradient-warning shadow text-center border-radius-md">
                <i class="ni ni-cart text-lg opacity-10" aria-hidden="true"></i>
              </div></div>
            </div></div></div>
          </div>
        </div>

        <div class="row mt-4">
          <div class="col-lg-5 mb-lg-0 mb-4">
            <div class="card z-index-2">
              <div class="card-body p-3">
                <div class="bg-gradient-dark border-radius-lg py-3 pe-1 mb-3">
                  <div class="chart"><canvas id="equityChart" class="chart-canvas" height="170"></canvas></div>
                </div>
                <h6 class="ms-2 mt-4 mb-0">Equity &amp; Realized P&amp;L Curve</h6>
                <p class="text-sm ms-2" id="sessionInfo">Live MT5 Account Performance</p>
              </div>
            </div>
          </div>
          <div class="col-lg-7">
            <div class="card z-index-2">
              <div class="card-header pb-0 d-flex justify-content-between align-items-center">
                <div>
                  <h6 class="mb-0">Live Market Chart (M15)</h6>
                  <p class="text-sm mb-0"><i class="ni ni-bold-up text-success"></i> Real-Time MT5 Feed</p>
                </div>
                <select id="marketSymbolSelect" class="form-select form-select-sm w-auto" onchange="refreshMarketChart()">
                  <option value="EURUSD">EURUSD</option>
                  <option value="GBPUSD">GBPUSD</option>
                  <option value="USDJPY">USDJPY</option>
                  <option value="XAUUSD" selected>XAUUSD</option>
                </select>
              </div>
              <div class="card-body p-3">
                <div class="chart"><canvas id="marketChart" class="chart-canvas" height="225"></canvas></div>
              </div>
            </div>
          </div>
        </div>

        <div class="row my-4">
          <div class="col-12">
            <div class="card">
              <div class="card-header pb-0"><h6>Current Open Trades</h6></div>
              <div class="card-body px-0 pb-2"><div class="table-responsive">
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
        </div>
      </div>

      <!-- TAB 2: LIVE MARKETS -->
      <div id="tab-markets" class="tab-pane-custom">
        <div class="card mb-4">
          <div class="card-header pb-0"><h6>Live Market Watch</h6></div>
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
              <div class="mb-2"><label class="form-label">Free AI Keys (Gemini / Groq)</label><input id="cfgGemini" placeholder="GEMINI_API_KEY" class="form-control form-control-sm mb-1" /><input id="cfgGroq" placeholder="GROQ_API_KEY" class="form-control form-control-sm" /></div>
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

  <script src="/assets/js/core/popper.min.js"></script>
  <script src="/assets/js/core/bootstrap.min.js"></script>
  <script src="/assets/js/plugins/perfect-scrollbar.min.js"></script>
  <script src="/assets/js/plugins/smooth-scrollbar.min.js"></script>
  <script src="/assets/js/plugins/chartjs.min.js"></script>
  <script src="/assets/js/soft-ui-dashboard.min.js?v=1.1.0"></script>
  <script>
    let equityChart = null, marketChart = null, configLoaded = false;

    function switchTab(name, el, title) {
      document.querySelectorAll('.tab-pane-custom').forEach(t => t.classList.remove('active'));
      document.getElementById('tab-' + name).classList.add('active');
      document.querySelectorAll('.sidenav .nav-link').forEach(a => a.classList.remove('active'));
      if (el) el.classList.add('active');
      if (title) {
        document.getElementById('pageTitle').textContent = title;
        document.getElementById('breadcrumbTitle').textContent = title;
      }
    }

    async function refreshStatus() {
      try {
        const r = await fetch('/api/status');
        const d = await r.json();
        document.getElementById('sessionInfo').textContent = `${d.session} | Updated ${new Date().toLocaleTimeString()}`;
        document.getElementById('sidebarSession').textContent = `${d.session} (${d.mode})`;
        const badge = document.getElementById('statusBadge');
        badge.textContent = d.paused ? `${d.mode} (PAUSED)` : d.mode;
        badge.className = 'badge badge-sm ' + (d.paused ? 'bg-gradient-warning' : 'bg-gradient-success');
        const btnLabel = d.paused ? 'Resume Bot' : 'Pause Bot';
        document.getElementById('toggleBotBtn').textContent = btnLabel;
        document.getElementById('sidebarToggleBtn').textContent = btnLabel;

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
          data: { labels, datasets: [{ label: 'Equity ($)', data, borderColor: '#fff', backgroundColor: 'rgba(255,255,255,0.12)', fill: true, tension: 0.35, pointRadius: 2 }] },
          options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#fff' }, grid: { display: false } }, y: { ticks: { color: '#fff' }, grid: { color: 'rgba(255,255,255,0.15)' } } } }
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
        const gradient = ctx.createLinearGradient(0, 230, 0, 50);
        gradient.addColorStop(1, 'rgba(203,12,159,0.2)');
        gradient.addColorStop(0.2, 'rgba(72,72,176,0.0)');
        gradient.addColorStop(0, 'rgba(203,12,159,0)');
        if (!marketChart) {
          marketChart = new Chart(ctx, {
            type: 'line',
            data: { labels: d.labels, datasets: [{ label: sym, data: d.closes, borderColor: '#cb0c9f', backgroundColor: gradient, fill: true, tension: 0.4, borderWidth: 3, pointRadius: 0 }] },
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
