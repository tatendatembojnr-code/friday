@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Allow "run friday [args]" or "run [args]"
if /i "%~1"=="friday" (
    shift
)

:: Collect remaining arguments
set "ARGS="
:loop
if "%~1"=="" goto done_args
set "ARGS=!ARGS! %~1"
shift
goto loop
:done_args

echo ============================================
echo   FRIDAY - SMC + AI Council Trading Bot
echo ============================================

:: 1. Ensure virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [FRIDAY] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Python 3.10+ is required and must be on PATH.
        exit /b 1
    )
)

:: 2. Run preflight credential check (zero-dependency)
".venv\Scripts\python.exe" preflight.py %ARGS%
if errorlevel 1 (
    exit /b 1
)

:: 3. Verify required packages are installed
".venv\Scripts\python.exe" -c "import MetaTrader5, pandas, numpy, openai, dotenv, colorlog" 2>nul
if errorlevel 1 (
    echo [FRIDAY] Installing missing dependencies...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies. Check your internet connection and retry.
        exit /b 1
    )
)

:: 4. Launch FRIDAY (or CLI Backtester)
if /i "%~1"=="--backtest" (
    echo [FRIDAY] Running multi-symbol CLI backtest...
    ".venv\Scripts\python.exe" backtest_cli.py
    exit /b %errorlevel%
)
echo [FRIDAY] Starting bot...
".venv\Scripts\python.exe" main.py %ARGS%
