@echo off
REM ============================================================
REM  S.A.R.A.L. - one-command launcher (Windows)
REM  Starts the FastAPI backend (:8000) and the Next.js
REM  frontend (:3000) in two separate windows.
REM
REM  Usage:  double-click this file, or run  start.bat  from
REM  the project root in a terminal.
REM ============================================================

setlocal EnableExtensions

REM %~dp0 always has a trailing "\". That breaks `start /D "path\"`
REM (backslash escapes the closing quote). Strip it.
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

echo(
echo  Starting S.A.R.A.L.
echo    Backend  -^> http://localhost:8000
echo    Frontend -^> http://localhost:3000
echo(

REM --- Prefer project venv (relative path; works with spaces in ROOT) ---
set "PY_CMD=python"
if exist "%ROOT%\.venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
    echo  [setup] Using venv: .venv\Scripts\python.exe
) else (
    echo  [setup] No .venv found — using system python
)

REM --- First-run: install web deps if missing ---------------
if not exist "%ROOT%\web\node_modules\" (
    echo  [setup] Installing frontend dependencies ^(first run^)...
    pushd "%ROOT%\web"
    call npm install
    if errorlevel 1 (
        echo  [error] npm install failed.
        popd
        pause
        exit /b 1
    )
    popd
)

REM --- Free stale listeners (crashes / duplicate start.bat runs) ---
call :free_port 8000
call :free_port 3000
call :free_port 3001
REM Give Windows a moment to fully release the sockets
ping -n 3 127.0.0.1 >nul

REM --- Backend ------------------------------------------------
REM /D sets the working directory without nesting `cd /d "..."` quotes.
echo  [launch] Backend window...
start "SARAL Backend (FastAPI :8000)" /D "%ROOT%" cmd /k "set SARAL_RELOAD=1&& %PY_CMD% -m backend.app.main"

REM Brief pause so backend can bind before Next starts
ping -n 3 127.0.0.1 >nul

REM --- Frontend (force port 3000 so we never silently move to 3001) ---
echo  [launch] Frontend window...
start "SARAL Frontend (Next.js :3000)" /D "%ROOT%\web" cmd /k "npm run dev -- -p 3000"

echo(
echo  Launched. Two windows opened ^(backend + frontend^).
echo  Close those windows to stop the servers.
echo  Open http://localhost:3000  ^(not 3001^).
echo(
endlocal
exit /b 0

:free_port
set "PORT=%~1"
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do (
    echo  [setup] Port %PORT% busy ^(PID %%P^) — stopping it...
    taskkill /F /PID %%P >nul 2>&1
)
exit /b 0
