@echo off
echo Starting Boss Fight RL...
echo.

echo [1/2] Starting backend on port 3000...
start "Backend - Boss Fight RL" cmd /k "cd /d %~dp0backend && npm install && npm start"

echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak >nul

echo [2/2] Starting frontend on port 4200...
start "Frontend - Boss Fight RL" cmd /k "cd /d %~dp0frontend && npm install && npm start"

echo.
echo Both servers starting...
echo Backend:  http://localhost:3000
echo Frontend: http://localhost:4200
echo.
echo Close the terminal windows to stop the servers.
pause
