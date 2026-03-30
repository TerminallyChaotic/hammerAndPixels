@echo off
REM One-click launcher for CT LLC Scraper (Windows)
REM Usage: double-click start.bat or run from command prompt

echo ======================================
echo   CT LLC Scraper - Hammer ^& Pixels
echo ======================================
echo.

REM Check for Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Docker is not installed.
    echo Install Docker Desktop from https://docker.com/get-started
    pause
    exit /b 1
)

echo Building and starting container...
echo.
docker compose up --build -d

echo.
echo ======================================
echo   LLC Scraper is running!
echo.
echo   Dashboard: http://localhost:5001
echo.
echo   Commands:
echo     Stop:    docker compose down
echo     Logs:    docker compose logs -f
echo     Rebuild: docker compose up --build -d
echo ======================================
echo.

REM Open browser
start http://localhost:5001

pause
