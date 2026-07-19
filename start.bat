@echo off
REM ============================================================
REM  S.A.R.A.L. - one-command launcher (Windows)
REM  Starts the FastAPI backend (:8000) and the Next.js
REM  frontend (:3000) in two separate windows. Both talk HTTP.
REM
REM  Usage:  double-click this file, or run  start.bat  from
REM  the project root in a terminal.
REM ============================================================

setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo(
echo  Starting S.A.R.A.L.
echo    Backend  -^> http://localhost:8000
echo    Frontend -^> http://localhost:3000
echo(

REM --- First-run: install web deps if missing ---------------
if not exist "%ROOT%web\node_modules" (
    echo  [setup] Installing frontend dependencies ^(first run^)...
    pushd "%ROOT%web"
    call npm install
    popd
)

REM --- Backend: FastAPI via uvicorn (auto-reload on code changes) -
start "SARAL Backend (FastAPI :8000)" cmd /k "cd /d "%ROOT%" && set SARAL_RELOAD=1 && python -m backend.app.main"

REM --- Frontend: Next.js dev server -------------------------
start "SARAL Frontend (Next.js :3000)" cmd /k "cd /d "%ROOT%web" && npm run dev"

echo  Launched. Two windows opened (backend + frontend).
echo  Close those windows to stop the servers.
endlocal
