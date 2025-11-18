@echo off
REM ============================================================
REM Script to run the P2P Chat System on MACHINE 1 (SERVER)
REM This machine will host: Tracker, App UIs, and Proxy
REM ============================================================

echo ============================================================
echo  STARTING P2P CHAT SYSTE
echo ============================================================

REM Update proxy.conf with LAN IP
echo Updating configuration files...
python update_config.py

REM Get the LAN IP address
for /f "tokens=*" %%i in ('python get_lan_ip.py') do set OUTPUT=%%i
for /f "tokens=2 delims=: " %%a in ("%OUTPUT%") do set SERVER_IP=%%a

echo.
echo Detected LAN IP: %SERVER_IP%
echo.
echo This machine will run:
echo   - Tracker (port 9000)
echo   - App UI 1 (port 9001)
echo   - App UI 2 (port 9002)
echo   - Proxy (port 8080)
echo.
echo Other machines should access via: http://%SERVER_IP%:8080
echo.
echo ============================================================
echo.

REM Start all services
start "Tracker" cmd /k python start_backend.py --server-ip 0.0.0.0 --server-port 9000
timeout /t 2 /nobreak >nul

start "Backend UI 1" cmd /k python start_sampleapp.py --server-ip 0.0.0.0 --server-port 9001
timeout /t 1 /nobreak >nul

start "Backend UI 2" cmd /k python start_sampleapp.py --server-ip 0.0.0.0 --server-port 9002
timeout /t 1 /nobreak >nul

start "Proxy" cmd /k python start_proxy.py --server-ip 0.0.0.0 --server-port 8080

echo.
echo ============================================================
echo All services started!
echo.
echo Open browser and go to: http://%SERVER_IP%:8080
echo or use: http://localhost:8080 on this machine
echo.
echo IMPORTANT: Update Windows hosts file with:
echo %SERVER_IP% tracker.local
echo %SERVER_IP% app.local
echo.
echo Press any key to exit this window...
echo ============================================================
pause >nul
