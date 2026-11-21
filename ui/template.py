"""FRIDAY Soft UI Dashboard — White & Lime Green Theme with Tabler Icons."""

SOFT_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
  <link rel="icon" type="image/png" href="/assets/img/friday-icon.png" />
  <link rel="apple-touch-icon" sizes="76x76" href="/assets/img/friday-icon.png" />
  <title>FRIDAY — Institutional Trading Command Center</title>
  <link href="https://fonts.googleapis.com/css?family=Inter:400,500,600,700,800" rel="stylesheet" />
  <link href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css" rel="stylesheet" />
  <link id="pagestyle" href="/assets/css/soft-ui-dashboard.css?v=1.1.0" rel="stylesheet" />
  <style>
    :root {
      --lime-dark: #4d7c0f;
      --lime-main: #65a30d;
      --lime-bright: #84cc16;
      --lime-soft: rgba(132, 204, 22, 0.14);
    }
    body { background-color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    .bg-lime-grad { background: linear-gradient(310deg, #4d7c0f 0%, #84cc16 100%) !important; color: #fff !important; }
    .text-lime { color: #65a30d !important; }
    .btn-lime { background: linear-gradient(310deg, #4d7c0f 0%, #84cc16 100%) !important; color: #fff !important; border: none !important; }
    .btn-outline-lime { border: 1px solid #65a30d !important; color: #4d7c0f !important; background: #fff !important; }
    .sidenav .nav-link.active {
      background: #fff !important;
      box-shadow: 0 8px 20px rgba(101, 163, 13, 0.12) !important;
      border-radius: 0.65rem;
      color: #1e293b !important;
      font-weight: 700;
    }
    .sidenav .nav-link.active .icon-box {
      background: linear-gradient(310deg, #4d7c0f 0%, #84cc16 100%) !important;
      color: #fff !important;
    }
    .icon-box {
      width: 32px; height: 32px; border-radius: 0.5rem;
      background: #f1f5f9; color: #475569;
      display: inline-flex; align-items: center; justify-content: center;
      font-size: 16px; flex-shrink: 0;
    }
    .stat-icon {
      width: 46px; height: 46px; border-radius: 0.75rem;
      display: inline-flex; align-items: center; justify-content: center;
      font-size: 22px; flex-shrink: 0;
      box-shadow: 0 6px 14px rgba(101, 163, 13, 0.22);
    }
    .stat-value { font-size: clamp(1.05rem, 1.35vw, 1.35rem); font-weight: 700; white-space: nowrap; }
    .card { border: 1px solid #eef2f6 !important; box-shadow: 0 4px 18px rgba(15, 23, 42, 0.04) !important; border-radius: 1rem !important; }
    .tab-pane-custom { display: none; }
    .tab-pane-custom.active { display: block; }
    .log-box {
      background: #f8fafc; color: #1e293b; border: 1px solid #e2e8f0;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11.5px;
      padding: 12px; border-radius: 10px; height: 240px; overflow-y: auto; white-space: pre-wrap;
    }
    .log-box-tall { height: 480px; }
  </style>
</head>
<body class="g-sidenav-show">
  <aside class="sidenav navbar navbar-vertical navbar-expand-xs border-0 border-radius-xl my-3 fixed-start ms-3 bg-white" id="sidenav-main">
    <div class="sidenav-header">
      <a class="navbar-brand m-0 d-flex align-items-center" href="#" onclick="switchTab('dashboard', this, 'Dashboard')">
        <img src="/assets/img/friday-icon.png" alt="FRIDAY" style="width:34px;height:34px;border-radius:8px;object-fit:contain;" class="me-2" />
        <span class="font-weight-bold text-dark" style="font-size:1.05rem;">FRIDAY AI</span>
      </a>
    </div>
    <hr class="horizontal dark mt-0" />
    <div class="collapse navbar-collapse w-auto" id="sidenav-collapse-main">
      <ul class="navbar-nav px-2">
        <li class="nav-item mb-1">
          <a class="nav-link active" href="#" onclick="switchTab('dashboard', this, 'Dashboard')">
            <span class="icon-box me-2"><i class="ti ti-layout-dashboard"></i></span>
            <span class="nav-link-text">Dashboard</span>
          </a>
        </li>
        <li class="nav-item mb-1">
          <a class="nav-link" href="#" onclick="switchTab('markets', this, 'Live Markets')">
            <span class="icon-box me-2"><i class="ti ti-chart-candle"></i></span>
            <span class="nav-link-text">Live Markets</span>
          </a>
        </li>
        <li class="nav-item mb-1">
          <a class="nav-link" href="#" onclick="switchTab('journal', this, 'AI & Trade Journal')">
            <span class="icon-box me-2"><i class="ti ti-brain"></i></span>
            <span class="nav-link-text">AI &amp; Journal</span>
          </a>
        </li>
        <li class="nav-item mb-1">
          <a class="nav-link" href="#" onclick="switchTab('backtest', this, 'Strategy Backtester')">
            <span class="icon-box me-2"><i class="ti ti-player-play"></i></span>
            <span class="nav-link-text">Backtester</span>
          </a>
        </li>
        <li class="nav-item mt-3 mb-1">
          <h6 class="ps-3 text-uppercase text-xs font-weight-bolder opacity-6">System</h6>
        </li>
        <li class="nav-item mb-1">
          <a class="nav-link" href="#" onclick="switchTab('config', this, 'Accounts & Config')">
            <span class="icon-box me-2"><i class="ti ti-adjustments-horizontal"></i></span>
            <span class="nav-link-text">Accounts &amp; Config</span>
          </a>
        </li>
        <li class="nav-item mb-1">
          <a class="nav-link" href="#" onclick="switchTab('logs', this, 'Live Logs')">
            <span class="icon-box me-2"><i class="ti ti-terminal-2"></i></span>
            <span class="nav-link-text">Live Logs</span>
          </a>
        </li>
      </ul>
    </div>
    <div class="sidenav-footer mx-3 mt-4">
      <div class="card bg-lime-grad border-0">
        <div class="card-body p-3 text-white">
          <div class="d-flex align-items-center mb-2">
            <i class="ti ti-shield-check fs-4 me-2"></i>
            <h6 class="text-white mb-0">Engine Status</h6>
          </div>
          <p class="text-xs mb-2 opacity-9" id="sidebarSession">Connecting...</p>
          <button class="btn btn-white btn-sm w-100 mb-0 text-dark font-weight-bold" onclick="toggleBot()" id="sidebarToggleBtn">Pause Bot</button>
        </div>
      </div>
    </div>
  </aside>

  <main class="main-content position-relative max-height-vh-100 h-100 border-radius-lg">
    <nav class="navbar navbar-main navbar-expand-lg px-0 mx-4 shadow-none border-radius-xl" id="navbarBlur">
      <div class="container-fluid py-2 px-3 d-flex justify-content-between align-items-center">
        <div>
          <ol class="breadcrumb bg-transparent mb-0 pb-0 pt-1 px-0">
            <li class="breadcrumb-item text-sm text-secondary">FRIDAY</li>
            <li class="breadcrumb-item text-sm text-dark font-weight-bold active" id="breadcrumbTitle">Dashboard</li>
          </ol>
          <h5 class="font-weight-bolder mb-0" id="pageTitle">Dashboard</h5>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span class="text-xs text-secondary me-2" id="livePulse"><i class="ti ti-activity text-lime"></i> Live 2s</span>
          <span id="dbBadge" class="badge bg-light text-dark border">DB: SQLITE</span>
          <span id="statusBadge" class="badge bg-lime-grad">--</span>
          <button id="toggleBotBtn" class="btn btn-outline-lime btn-sm mb-0" onclick="toggleBot()">Pause Bot</button>
          <button class="btn btn-danger btn-sm mb-0" onclick="closeAllPositions()"><i class="ti ti-x me-1"></i>Close All</button>
          <button class="btn btn-light btn-sm mb-0 border" onclick="logout()" title="Sign Out"><i class="ti ti-logout"></i></button>
        </div>
      </div>
    </nav>

    <div class="container-fluid py-3">
      <!-- LOCK-SCREEN GREETING & WEEKEND MARKET COUNTDOWN BANNER -->
      <div class="card mb-3 border-0" id="greetingBanner" style="background: linear-gradient(90deg, #ffffff 0%, #f7fee7 100%);">
        <div class="card-body py-3 px-4 d-flex flex-wrap justify-content-between align-items-center gap-2">
          <div>
            <h5 class="mb-0 font-weight-bolder text-dark" id="lockGreeting">Welcome back, Tatenda</h5>
            <span class="text-xs text-secondary" id="marketStatusMsg">Checking market hours...</span>
          </div>
          <div id="countdownBox" class="d-none align-items-center gap-2 bg-white px-3 py-2 border-radius-lg shadow-xs" style="border:1px solid #d9f99d;">
            <i class="ti ti-clock-hour-4 text-lime fs-5"></i>
            <div>
              <div class="text-xxs text-uppercase text-secondary font-weight-bold">Markets Open In</div>
              <div class="text-sm font-weight-bolder text-lime" id="marketCountdown">--:--:--</div>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 1: DASHBOARD -->
      <div id="tab-dashboard" class="tab-pane-custom active">
        <div class="row g-3 mb-4">
          <div class="col-xl col-md-4 col-sm-6">
            <div class="card h-100"><div class="card-body p-3 d-flex justify-content-between align-items-center">
              <div>
                <p class="text-xs mb-1 text-uppercase text-secondary font-weight-bold">Total Balance</p>
                <div class="stat-value text-dark" id="cardBalance">--</div>
                <span class="text-xs text-secondary" id="cardEquity">Equity: --</span>
              </div>
              <span class="stat-icon bg-lime-grad"><i class="ti ti-wallet"></i></span>
            </div></div>
          </div>
          <div class="col-xl col-md-4 col-sm-6">
            <div class="card h-100"><div class="card-body p-3 d-flex justify-content-between align-items-center">
              <div>
                <p class="text-xs mb-1 text-uppercase text-secondary font-weight-bold">Free Margin</p>
                <div class="stat-value text-dark" id="cardMargin">--</div>
                <span class="text-xs text-secondary" id="cardFloating">Floating: --</span>
              </div>
              <span class="stat-icon bg-lime-grad"><i class="ti ti-scale"></i></span>
            </div></div>
          </div>
          <div class="col-xl col-md-4 col-sm-6">
            <div class="card h-100"><div class="card-body p-3 d-flex justify-content-between align-items-center">
              <div>
                <p class="text-xs mb-1 text-uppercase text-secondary font-weight-bold">Total Profits</p>
                <div class="stat-value text-lime" id="cardProfits">--</div>
                <span class="text-xs text-secondary" id="cardWinRate">Win Rate: --</span>
              </div>
              <span class="stat-icon bg-lime-grad"><i class="ti ti-trending-up"></i></span>
            </div></div>
          </div>
          <div class="col-xl col-md-6 col-sm-6">
            <div class="card h-100"><div class="card-body p-3 d-flex justify-content-between align-items-center">
              <div>
                <p class="text-xs mb-1 text-uppercase text-secondary font-weight-bold">Total Losses</p>
                <div class="stat-value text-danger" id="cardLosses">--</div>
                <span class="text-xs text-secondary" id="cardLossCount">Closed: --</span>
              </div>
              <span class="stat-icon bg-gradient-danger text-white"><i class="ti ti-trending-down"></i></span>
            </div></div>
          </div>
          <div class="col-xl col-md-6 col-sm-6">
            <div class="card h-100"><div class="card-body p-3 d-flex justify-content-between align-items-center">
              <div>
                <p class="text-xs mb-1 text-uppercase text-secondary font-weight-bold">Open Trades</p>
                <div class="stat-value text-dark" id="cardOpenTrades">--</div>
                <span class="text-xs text-secondary" id="cardSessionShort">Session: --</span>
              </div>
              <span class="stat-icon bg-lime-grad"><i class="ti ti-arrows-exchange"></i></span>
            </div></div>
          </div>
        </div>

        <!-- EQUAL WHITE & LIME GREEN CHARTS -->
        <div class="row g-3 mb-4">
          <div class="col-lg-6">
            <div class="card h-100">
              <div class="card-header bg-white pb-0 d-flex justify-content-between align-items-center">
                <div>
                  <h6 class="mb-0">Equity &amp; Realized P&amp;L Curve</h6>
                  <p class="text-xs text-secondary mb-0" id="sessionInfo">Live MT5 Account Growth</p>
                </div>
                <span class="badge bg-lime-grad">LIVE</span>
              </div>
              <div class="card-body p-3"><canvas id="equityChart" height="175"></canvas></div>
            </div>
          </div>
          <div class="col-lg-6">
            <div class="card h-100">
              <div class="card-header bg-white pb-0 d-flex justify-content-between align-items-center">
                <div>
                  <h6 class="mb-0">Live Market Chart (M15)</h6>
                  <p class="text-xs text-secondary mb-0"><i class="ti ti-chart-line text-lime"></i> Real-Time MT5 Feed</p>
                </div>
                <select id="marketSymbolSelect" class="form-select form-select-sm w-auto" onchange="refreshMarketChart()">
                  <option value="EURUSD">EURUSD</option>
                  <option value="GBPUSD">GBPUSD</option>
                  <option value="USDJPY">USDJPY</option>
                  <option value="XAUUSD" selected>XAUUSD</option>
                </select>
              </div>
              <div class="card-body p-3"><canvas id="marketChart" height="175"></canvas></div>
            </div>
          </div>
        </div>

        <!-- OPEN TRADES + LIVE LOGS SIDE BY SIDE -->
        <div class="row g-3">
          <div class="col-lg-7">
            <div class="card h-100">
              <div class="card-header bg-white pb-0 d-flex justify-content-between align-items-center">
                <h6 class="mb-0"><i class="ti ti-list-details text-lime me-1"></i>Current Open Trades</h6>
              </div>
              <div class="card-body px-0 pb-2"><div class="table-responsive">
                <table class="table align-items-center mb-0">
                  <thead><tr>
                    <th class="text-uppercase text-secondary text-xxs font-weight-bolder">Ticket</th>
                    <th class="text-uppercase text-secondary text-xxs font-weight-bolder">Symbol</th>
                    <th class="text-uppercase text-secondary text-xxs font-weight-bolder">Side</th>
                    <th class="text-uppercase text-secondary text-xxs font-weight-bolder">Lots</th>
                    <th class="text-uppercase text-secondary text-xxs font-weight-bolder">Open / Curr</th>
                    <th class="text-uppercase text-secondary text-xxs font-weight-bolder">SL / TP</th>
                    <th class="text-uppercase text-secondary text-xxs font-weight-bolder">P&amp;L</th>
                    <th class="text-uppercase text-secondary text-xxs font-weight-bolder">Action</th>
                  </tr></thead>
                  <tbody id="openTradesBody"></tbody>
                </table>
              </div></div>
            </div>
          </div>
          <div class="col-lg-5">
            <div class="card h-100">
              <div class="card-header bg-white pb-0 d-flex justify-content-between align-items-center">
                <h6 class="mb-0"><i class="ti ti-terminal-2 text-lime me-1"></i>Live Execution Logs</h6>
              </div>
              <div class="card-body p-3"><div id="dashLogViewer" class="log-box">Loading...</div></div>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 2: LIVE MARKETS -->
      <div id="tab-markets" class="tab-pane-custom">
        <div class="row g-3 mb-4">
          <div class="col-lg-8">
            <div class="card h-100">
              <div class="card-header bg-white pb-0 d-flex justify-content-between align-items-center">
                <div>
                  <h6 class="mb-0"><i class="ti ti-chart-candle text-lime me-1"></i>Interactive Candlestick Chart (M15)</h6>
                  <span class="text-xs text-secondary">Live MT5 OHLC Price Action</span>
                </div>
                <select id="candleSymbolSelect" class="form-select form-select-sm w-auto" onchange="refreshCandles()">
                  <option value="EURUSD">EURUSD</option>
                  <option value="GBPUSD">GBPUSD</option>
                  <option value="USDJPY">USDJPY</option>
                  <option value="XAUUSD" selected>XAUUSD</option>
                </select>
              </div>
              <div class="card-body p-3">
                <div id="candleChartContainer" style="width:100%; height:340px;"></div>
              </div>
            </div>
          </div>
          <div class="col-lg-4">
            <div class="card h-100">
              <div class="card-header bg-white pb-0 d-flex justify-content-between align-items-center">
                <h6 class="mb-0"><i class="ti ti-news text-lime me-1"></i>Live Market News</h6>
                <button class="btn btn-link text-lime text-xs p-0 mb-0" onclick="refreshNews()">Refresh</button>
              </div>
              <div class="card-body p-3" id="newsFeedBox" style="max-height:360px; overflow-y:auto;">
                <span class="text-xs text-secondary">Loading headlines...</span>
              </div>
            </div>
          </div>
        </div>
        <div class="card mb-4">
          <div class="card-header bg-white pb-0"><h6><i class="ti ti-world text-lime me-1"></i>Live Market Watch &amp; Spreads</h6></div>
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
          <div class="card-header bg-white pb-0"><h6><i class="ti ti-brain text-lime me-1"></i>AI Council Decisions</h6></div>
          <div class="card-body"><div class="table-responsive">
            <table class="table align-items-center mb-0">
              <thead><tr><th>Time</th><th>Symbol</th><th>Dir</th><th>SMC</th><th>AI</th><th>Regime</th><th>Reasoning</th></tr></thead>
              <tbody id="aiJournalBody"></tbody>
            </table>
          </div></div>
        </div>
        <div class="card">
          <div class="card-header bg-white pb-0"><h6><i class="ti ti-history text-lime me-1"></i>Closed Trades History</h6></div>
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
        <div class="row g-3">
          <div class="col-lg-6">
            <div class="card h-100"><div class="card-header bg-white pb-0"><h6><i class="ti ti-key text-lime me-1"></i>MT5 Account, AI &amp; Telegram Credentials</h6></div>
            <div class="card-body">
              <div class="mb-2"><label class="form-label text-xs">MT5 Login</label><input id="cfgLogin" class="form-control form-control-sm" /></div>
              <div class="mb-2"><label class="form-label text-xs">MT5 Password</label><input id="cfgPassword" type="password" placeholder="Leave blank to keep current" class="form-control form-control-sm" /></div>
              <div class="mb-2"><label class="form-label text-xs">MT5 Server</label><input id="cfgServer" class="form-control form-control-sm" /></div>
              <div class="mb-2"><label class="form-label text-xs">AI API Keys (OpenAI / Gemini / Groq / Ollama)</label>
                <input id="cfgOpenAI" placeholder="OPENAI_API_KEY (sk-...)" class="form-control form-control-sm mb-1" />
                <input id="cfgGemini" placeholder="GEMINI_API_KEY" class="form-control form-control-sm mb-1" />
                <input id="cfgGroq" placeholder="GROQ_API_KEY" class="form-control form-control-sm mb-1" />
                <div class="row g-1">
                  <div class="col-7"><input id="cfgOllamaKey" placeholder="OLLAMA_API_KEY" class="form-control form-control-sm" /></div>
                  <div class="col-5"><input id="cfgOllamaModel" placeholder="deepseek-v4.1-flash" class="form-control form-control-sm" /></div>
                </div>
              </div>
              <div class="mb-2"><label class="form-label text-xs">Trading Symbols (comma-separated)</label><input id="cfgSymbols" class="form-control form-control-sm" /></div>
              <div class="mb-2"><label class="form-label text-xs">Telegram Alerts (Optional)</label>
                <input id="cfgTgToken" placeholder="TELEGRAM_BOT_TOKEN" class="form-control form-control-sm mb-1" />
                <input id="cfgTgChat" placeholder="TELEGRAM_CHAT_ID" class="form-control form-control-sm" />
              </div>
            </div></div>
          </div>
          <div class="col-lg-6">
            <div class="card h-100"><div class="card-header bg-white pb-0"><h6><i class="ti ti-shield-lock text-lime me-1"></i>Risk, Strategy &amp; Speed Parameters</h6></div>
            <div class="card-body">
              <div class="row g-2">
                <div class="col-6"><label class="form-label text-xs">Risk Per Trade (%)</label><input id="cfgRiskPct" type="number" step="0.05" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Max Daily Loss (%)</label><input id="cfgDailyLoss" type="number" step="0.1" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Max Drawdown (%)</label><input id="cfgMaxDD" type="number" step="0.5" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Max Open Trades</label><input id="cfgMaxOpen" type="number" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Max Per Symbol</label><input id="cfgMaxPerSym" type="number" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Max USD Exposure</label><input id="cfgMaxUsd" type="number" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Max Daily Trades</label><input id="cfgMaxDaily" type="number" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Min SMC Score</label><input id="cfgMinSmc" type="number" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">AI Min Confidence (%)</label><input id="cfgAiConf" type="number" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Default R:R Target</label><input id="cfgRR" type="number" step="0.1" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Breakeven / Partial (R)</label><input id="cfgBeRR" type="number" step="0.1" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Trailing Start (R)</label><input id="cfgTrailRR" type="number" step="0.1" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Max Trade Duration (min, 0=off)</label><input id="cfgMaxDur" type="number" class="form-control form-control-sm" /></div>
                <div class="col-6"><label class="form-label text-xs">Scan Interval (sec)</label><input id="cfgPollSec" type="number" class="form-control form-control-sm" /></div>
              </div>
              <div class="form-check form-switch mt-3">
                <input class="form-check-input" type="checkbox" id="cfgDryRun" />
                <label class="form-check-label text-sm" for="cfgDryRun">Dry-Run Mode (Simulate Orders)</label>
              </div>
              <button class="btn btn-sm btn-lime mt-3" onclick="saveConfig()"><i class="ti ti-device-floppy me-1"></i>Save &amp; Apply Settings</button>
              <span id="cfgSaveMsg" class="text-xs text-lime ms-2"></span>
            </div></div>
          </div>
        </div>
      </div>

      <!-- TAB 5: LIVE LOGS -->
      <div id="tab-logs" class="tab-pane-custom">
        <div class="card"><div class="card-header bg-white pb-0"><h6><i class="ti ti-terminal-2 text-lime me-1"></i>Full Execution Logs</h6></div>
        <div class="card-body"><div id="logViewer" class="log-box log-box-tall">Loading...</div></div></div>
      </div>

      <!-- TAB 6: STRATEGY BACKTESTER -->
      <div id="tab-backtest" class="tab-pane-custom">
        <div class="card mb-4">
          <div class="card-header bg-white pb-0 d-flex flex-wrap justify-content-between align-items-center gap-2">
            <div>
              <h6 class="mb-0"><i class="ti ti-player-play text-lime me-1"></i>One-Click Strategy Backtester</h6>
              <span class="text-xs text-secondary">Replay FRIDAY's SMC + 0.5R Breakeven + 1.8R TP on historical M15 bars</span>
            </div>
            <div class="d-flex gap-2 align-items-center">
              <select id="btSymbol" class="form-select form-select-sm w-auto">
                <option value="EURUSD">EURUSD</option>
                <option value="GBPUSD">GBPUSD</option>
                <option value="USDJPY">USDJPY</option>
                <option value="XAUUSD" selected>XAUUSD</option>
              </select>
              <select id="btBars" class="form-select form-select-sm w-auto">
                <option value="200">200 Bars</option>
                <option value="300" selected>300 Bars</option>
                <option value="500">500 Bars</option>
              </select>
              <button class="btn btn-sm btn-lime mb-0" onclick="runBacktestUI()">Run Backtest</button>
            </div>
          </div>
          <div class="card-body">
            <div class="row g-3 mb-3 text-center">
              <div class="col-md-3 col-6"><div class="p-2 border rounded"><div class="text-xs text-secondary">Trades</div><div class="fw-bold" id="btTrades">--</div></div></div>
              <div class="col-md-3 col-6"><div class="p-2 border rounded"><div class="text-xs text-secondary">Win Rate</div><div class="fw-bold text-lime" id="btWinRate">--</div></div></div>
              <div class="col-md-3 col-6"><div class="p-2 border rounded"><div class="text-xs text-secondary">Profit Factor</div><div class="fw-bold" id="btPF">--</div></div></div>
              <div class="col-md-3 col-6"><div class="p-2 border rounded"><div class="text-xs text-secondary">Net Return / Max DD</div><div class="fw-bold" id="btRet">--</div></div></div>
            </div>
            <canvas id="btChart" height="120"></canvas>
          </div>
        </div>
      </div>
    </div>
  </main>

  <script src="/assets/js/core/popper.min.js"></script>
  <script src="/assets/js/core/bootstrap.min.js"></script>
  <script src="/assets/js/plugins/chartjs.min.js"></script>
  <script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
  <script>
    let equityChart = null, marketChart = null, candleChart = null, candleSeries = null, btChart = null, configLoaded = false, countdownSec = 0;

    function formatCountdown(sec) {
      if (sec <= 0) return '00h 00m 00s';
      const d = Math.floor(sec / 86400);
      const h = Math.floor((sec % 86400) / 3600);
      const m = Math.floor((sec % 3600) / 60);
      const s = sec % 60;
      return `${d > 0 ? d + 'd ' : ''}${String(h).padStart(2,'0')}h ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s`;
    }
    setInterval(() => {
      if (countdownSec > 0) {
        countdownSec--;
        document.getElementById('marketCountdown').textContent = formatCountdown(countdownSec);
      }
    }, 1000);

    function switchTab(name, el, title) {
      document.querySelectorAll('.tab-pane-custom').forEach(t => t.classList.remove('active'));
      document.getElementById('tab-' + name).classList.add('active');
      document.querySelectorAll('.sidenav .nav-link').forEach(a => a.classList.remove('active'));
      if (el) el.classList.add('active');
      if (title) {
        document.getElementById('pageTitle').textContent = title;
        document.getElementById('breadcrumbTitle').textContent = title;
      }
      if (name === 'markets') { refreshCandles(); refreshNews(); }
    }

    async function refreshStatus() {
      try {
        const r = await fetch('/api/status');
        const d = await r.json();
        document.getElementById('sessionInfo').textContent = `${d.session} | Updated ${new Date().toLocaleTimeString()}`;
        document.getElementById('sidebarSession').textContent = `${d.session} (${d.mode})`;
        document.getElementById('cardSessionShort').textContent = d.session;
        if (d.db_backend) document.getElementById('dbBadge').textContent = `DB: ${d.db_backend.toUpperCase()}`;
        if (d.schedule) {
          document.getElementById('lockGreeting').textContent = d.schedule.greeting;
          document.getElementById('marketStatusMsg').textContent = d.schedule.status_message;
          const cBox = document.getElementById('countdownBox');
          if (d.schedule.is_weekend_closed) {
            cBox.classList.remove('d-none');
            cBox.classList.add('d-flex');
            countdownSec = d.schedule.seconds_to_open;
            document.getElementById('marketCountdown').textContent = formatCountdown(countdownSec);
          } else {
            cBox.classList.add('d-none');
            cBox.classList.remove('d-flex');
          }
        }
        const badge = document.getElementById('statusBadge');
        badge.textContent = d.paused ? `${d.mode} (PAUSED)` : d.mode;
        badge.className = 'badge ' + (d.paused ? 'bg-gradient-warning' : 'bg-lime-grad');
        const btnLabel = d.paused ? 'Resume Bot' : 'Pause Bot';
        document.getElementById('toggleBotBtn').textContent = btnLabel;
        document.getElementById('sidebarToggleBtn').textContent = btnLabel;

        document.getElementById('cardBalance').textContent = `$${d.balance.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        document.getElementById('cardEquity').textContent = `Equity: $${d.equity.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        document.getElementById('cardMargin').textContent = `$${d.margin_free.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        document.getElementById('cardFloating').textContent = `Floating: ${d.floating_pnl >= 0 ? '+' : ''}$${d.floating_pnl.toFixed(2)}`;
        document.getElementById('cardProfits').textContent = `+$${d.total_profits.toLocaleString('en-US', {minimumFractionDigits:2})}`;
        document.getElementById('cardWinRate').textContent = `Win Rate: ${d.win_rate_pct}% (${d.win_count}W)`;
        document.getElementById('cardLosses').textContent = `-$${Math.abs(d.total_losses).toLocaleString('en-US', {minimumFractionDigits:2})}`;
        document.getElementById('cardLossCount').textContent = `Closed: ${d.loss_count}L`;
        document.getElementById('cardOpenTrades').textContent = `${d.positions.length} / ${d.max_open_trades}`;

        document.getElementById('openTradesBody').innerHTML = d.positions.length ? d.positions.map(p => `
          <tr>
            <td class="ps-3 text-xs">${p.ticket}</td>
            <td class="text-xs font-weight-bold">${p.symbol}</td>
            <td class="text-xs"><span class="badge ${p.type==='BUY'?'bg-lime-grad':'bg-gradient-danger'}">${p.type}</span></td>
            <td class="text-xs">${p.volume}</td>
            <td class="text-xs">${p.price_open} / ${p.price_current}</td>
            <td class="text-xs">${p.sl} / ${p.tp}</td>
            <td class="text-xs font-weight-bold ${p.profit >= 0 ? 'text-lime' : 'text-danger'}">${p.profit >= 0 ? '+' : ''}$${p.profit.toFixed(2)}</td>
            <td><button class="btn btn-link text-danger text-xs p-0 mb-0" onclick="closeOne(${p.ticket})">Close</button></td>
          </tr>`).join('') : '<tr><td colspan="8" class="text-center text-xs text-secondary py-3">No open positions</td></tr>';

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
            <td class="text-xs font-weight-bold ${c.outcome==='WIN'?'text-lime':'text-danger'}">${c.outcome}</td>
            <td class="text-xs ${c.pnl>=0?'text-lime':'text-danger'}">${c.pnl>=0?'+':''}$${c.pnl.toFixed(2)}</td>
          </tr>`).join('');

        document.getElementById('marketWatchBody').innerHTML = d.market_watch.map(m => `
          <tr><td class="text-xs font-weight-bold">${m.symbol}</td><td class="text-xs">${m.bid}</td><td class="text-xs">${m.ask}</td><td class="text-xs">${m.spread}</td><td class="text-xs">${m.last_close}</td></tr>`).join('');

        const logText = d.logs.join('\\n');
        document.getElementById('logViewer').textContent = logText;
        document.getElementById('dashLogViewer').textContent = d.logs.slice(-14).join('\\n');
        updateEquityChart(d.equity_curve);

        if (!configLoaded && d.config) {
          document.getElementById('cfgLogin').value = d.config.mt5_login || '';
          document.getElementById('cfgServer').value = d.config.mt5_server || '';
          document.getElementById('cfgSymbols').value = d.config.symbols || '';
          document.getElementById('cfgRiskPct').value = d.config.risk_per_trade_pct;
          document.getElementById('cfgDailyLoss').value = d.config.max_daily_loss_pct;
          document.getElementById('cfgMaxDD').value = d.config.max_drawdown_pct;
          document.getElementById('cfgMaxOpen').value = d.config.max_open_trades;
          document.getElementById('cfgMaxPerSym').value = d.config.max_trades_per_symbol;
          document.getElementById('cfgMaxUsd').value = d.config.max_usd_exposure;
          document.getElementById('cfgMaxDaily').value = d.config.max_daily_trades;
          document.getElementById('cfgMinSmc').value = d.config.min_smc_score;
          document.getElementById('cfgAiConf').value = d.config.ai_min_confidence;
          document.getElementById('cfgRR').value = d.config.default_rr_target;
          document.getElementById('cfgBeRR').value = d.config.breakeven_at_rr;
          document.getElementById('cfgTrailRR').value = d.config.trailing_start_rr;
          document.getElementById('cfgMaxDur').value = d.config.max_trade_duration_minutes;
          document.getElementById('cfgPollSec').value = d.config.poll_interval_seconds;
          document.getElementById('cfgDryRun').checked = !!d.config.dry_run;
          configLoaded = true;
        }
      } catch(e) {}
    }

    function updateEquityChart(curve) {
      const ctx = document.getElementById('equityChart').getContext('2d');
      const labels = curve.map(p => p.label);
      const data = curve.map(p => p.value);
      const grad = ctx.createLinearGradient(0, 200, 0, 20);
      grad.addColorStop(1, 'rgba(132, 204, 22, 0.25)');
      grad.addColorStop(0, 'rgba(132, 204, 22, 0.0)');
      if (!equityChart) {
        equityChart = new Chart(ctx, {
          type: 'line',
          data: { labels, datasets: [{ label: 'Equity ($)', data, borderColor: '#65a30d', backgroundColor: grad, fill: true, tension: 0.35, borderWidth: 2.5, pointRadius: 2 }] },
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
        const grad = ctx.createLinearGradient(0, 200, 0, 20);
        grad.addColorStop(1, 'rgba(101, 163, 13, 0.25)');
        grad.addColorStop(0, 'rgba(101, 163, 13, 0.0)');
        if (!marketChart) {
          marketChart = new Chart(ctx, {
            type: 'line',
            data: { labels: d.labels, datasets: [{ label: sym, data: d.closes, borderColor: '#4d7c0f', backgroundColor: grad, fill: true, tension: 0.35, borderWidth: 2.5, pointRadius: 0 }] },
            options: { responsive: true, plugins: { legend: { display: false } } }
          });
        } else {
          marketChart.data.labels = d.labels;
          marketChart.data.datasets[0].label = sym;
          marketChart.data.datasets[0].data = d.closes;
          marketChart.update('none');
        }
      } catch(e) {}
    }

    async function refreshCandles() {
      const sym = document.getElementById('candleSymbolSelect').value;
      const container = document.getElementById('candleChartContainer');
      if (!window.LightweightCharts || !container) return;
      try {
        const r = await fetch(`/api/market_chart?symbol=${sym}`);
        const d = await r.json();
        if (!candleChart) {
          candleChart = LightweightCharts.createChart(container, {
            width: container.clientWidth,
            height: 340,
            layout: { background: { color: '#ffffff' }, textColor: '#334155' },
            grid: { vertLines: { color: '#f1f5f9' }, horzLines: { color: '#f1f5f9' } },
            timeScale: { timeVisible: true, secondsVisible: false }
          });
          candleSeries = candleChart.addCandlestickSeries({
            upColor: '#65a30d', downColor: '#ef4444', borderVisible: false,
            wickUpColor: '#65a30d', wickDownColor: '#ef4444'
          });
        }
        if (d.candles && d.candles.length) {
          candleSeries.setData(d.candles);
          candleChart.timeScale().fitContent();
        }
      } catch(e) {}
    }

    async function refreshNews() {
      try {
        const r = await fetch('/api/news');
        const d = await r.json();
        document.getElementById('newsFeedBox').innerHTML = (d.items || []).map(n => `
          <div class="mb-3 pb-2 border-bottom">
            <a href="${n.link}" target="_blank" class="text-xs font-weight-bold text-dark d-block">${n.title}</a>
            <span class="text-xxs text-secondary">${n.pubDate || ''}</span>
          </div>`).join('') || '<span class="text-xs text-secondary">No headlines available.</span>';
      } catch(e) {}
    }

    async function toggleBot() { await fetch('/api/bot/toggle', {method:'POST'}); refreshStatus(); }
    async function runBacktestUI() {
      const sym = document.getElementById('btSymbol').value;
      const bars = document.getElementById('btBars').value;
      const r = await fetch(`/api/backtest?symbol=${sym}&bars=${bars}`);
      const d = await r.json();
      if (d.error) { alert(d.error); return; }
      document.getElementById('btTrades').textContent = `${d.total_trades} (${d.wins}W / ${d.losses}L)`;
      document.getElementById('btWinRate').textContent = `${d.win_rate_pct}%`;
      document.getElementById('btPF').textContent = d.profit_factor;
      document.getElementById('btRet').textContent = `${d.net_return_pct >= 0 ? '+' : ''}${d.net_return_pct}% / -${d.max_drawdown_pct}%`;
      const ctx = document.getElementById('btChart').getContext('2d');
      const labels = (d.equity_curve || []).map(p => `Bar ${p.bar}`);
      const vals = (d.equity_curve || []).map(p => p.equity);
      if (btChart) btChart.destroy();
      btChart = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets: [{ label: `${sym} Backtest ($)`, data: vals, borderColor: '#65a30d', backgroundColor: 'rgba(132,204,22,0.18)', fill: true, tension: 0.3 }] },
        options: { responsive: true }
      });
    }
    async function logout() { await fetch('/api/logout', {method:'POST'}); window.location.href = '/login'; }
    async function closeOne(ticket) { await fetch('/api/close_position', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ticket})}); refreshStatus(); }
    async function closeAllPositions() { if(confirm('Close all open MT5 positions?')) { await fetch('/api/close_all', {method:'POST'}); refreshStatus(); } }
    async function saveConfig() {
      const payload = {
        mt5_login: document.getElementById('cfgLogin').value,
        mt5_password: document.getElementById('cfgPassword').value,
        mt5_server: document.getElementById('cfgServer').value,
        symbols: document.getElementById('cfgSymbols').value,
        openai_api_key: document.getElementById('cfgOpenAI').value,
        gemini_api_key: document.getElementById('cfgGemini').value,
        groq_api_key: document.getElementById('cfgGroq').value,
        ollama_api_key: document.getElementById('cfgOllamaKey').value,
        ollama_model: document.getElementById('cfgOllamaModel').value,
        telegram_bot_token: document.getElementById('cfgTgToken').value,
        telegram_chat_id: document.getElementById('cfgTgChat').value,
        risk_per_trade_pct: parseFloat(document.getElementById('cfgRiskPct').value),
        max_daily_loss_pct: parseFloat(document.getElementById('cfgDailyLoss').value),
        max_drawdown_pct: parseFloat(document.getElementById('cfgMaxDD').value),
        max_open_trades: parseInt(document.getElementById('cfgMaxOpen').value),
        max_trades_per_symbol: parseInt(document.getElementById('cfgMaxPerSym').value),
        max_usd_exposure: parseInt(document.getElementById('cfgMaxUsd').value),
        max_daily_trades: parseInt(document.getElementById('cfgMaxDaily').value),
        min_smc_score: parseInt(document.getElementById('cfgMinSmc').value),
        ai_min_confidence: parseInt(document.getElementById('cfgAiConf').value),
        default_rr_target: parseFloat(document.getElementById('cfgRR').value),
        breakeven_at_rr: parseFloat(document.getElementById('cfgBeRR').value),
        trailing_start_rr: parseFloat(document.getElementById('cfgTrailRR').value),
        max_trade_duration_minutes: parseInt(document.getElementById('cfgMaxDur').value),
        poll_interval_seconds: parseInt(document.getElementById('cfgPollSec').value),
        dry_run: document.getElementById('cfgDryRun').checked
      };
      const r = await fetch('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const res = await r.json();
      document.getElementById('cfgSaveMsg').textContent = res.message || 'Saved!';
    }

    refreshStatus();
    refreshMarketChart();
    setInterval(refreshStatus, 2000);
    setInterval(refreshMarketChart, 5000);
  </script>
</body>
</html>
"""

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
  <link rel="icon" type="image/png" href="/assets/img/friday-icon.png" />
  <title>Sign In — FRIDAY AI Trading</title>
  <link href="https://fonts.googleapis.com/css?family=Inter:400,500,600,700,800" rel="stylesheet" />
  <link href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css" rel="stylesheet" />
  <link href="/assets/css/soft-ui-dashboard.css?v=1.1.0" rel="stylesheet" />
  <style>
    body { background: linear-gradient(135deg, #f8fafc 0%, #ecfccb 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Inter', sans-serif; }
    .login-card { max-width: 430px; width: 100%; border-radius: 1.25rem; border: 1px solid #e2e8f0; box-shadow: 0 20px 50px rgba(15,23,42,0.08); background: #fff; }
    .btn-lime { background: linear-gradient(310deg, #4d7c0f 0%, #84cc16 100%) !important; color: #fff !important; border: none !important; }
  </style>
</head>
<body>
  <div class="login-card p-4 p-md-5 m-3">
    <div class="text-center mb-4">
      <img src="/assets/img/friday-logo-main.png" alt="FRIDAY" style="max-width:210px;height:auto;border-radius:12px;" class="mb-2" />
      <h5 class="font-weight-bolder text-dark mb-1">Command Center Sign In</h5>
      <p class="text-xs text-secondary mb-0">Think Smart. Trade Sharp. AI-Powered Trading Intelligence</p>
    </div>
    <div id="errBox" class="alert alert-danger text-white text-xs py-2 d-none"></div>
    <form onsubmit="doLogin(event)">
      <div class="mb-3">
        <label class="form-label text-xs font-weight-bold">Username</label>
        <input id="username" class="form-control" placeholder="tatenda" required autofocus />
      </div>
      <div class="mb-4">
        <label class="form-label text-xs font-weight-bold">Password</label>
        <input id="password" type="password" class="form-control" placeholder="••••••••" required />
      </div>
      <button type="submit" class="btn btn-lime w-100 py-2 font-weight-bold">
        <i class="ti ti-lock-open me-1"></i> Sign In to FRIDAY
      </button>
    </form>
  </div>
  <script>
    async function doLogin(e) {
      e.preventDefault();
      const err = document.getElementById('errBox');
      err.classList.add('d-none');
      const r = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          username: document.getElementById('username').value,
          password: document.getElementById('password').value
        })
      });
      const d = await r.json();
      if (r.ok && d.ok) {
        window.location.href = '/';
      } else {
        err.textContent = d.error || 'Invalid credentials';
        err.classList.remove('d-none');
      }
    }
  </script>
</body>
</html>
"""

