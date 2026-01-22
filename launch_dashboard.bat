@echo off
REM Launch FracFocus Dashboard for Windows

cd /d "%~dp0"

echo ==========================================
echo FracFocus Analysis Dashboard
echo ==========================================
echo.

REM Check if output files exist
if not exist output\quarterly_by_basin.csv (
    echo WARNING: No analysis output files found!
    echo.
    echo Please run the analysis first:
    echo   automate_analysis.bat
    echo.
    echo Or manually:
    echo   python download_data.py
    echo   python fracfocus_analysis.py
    echo.
    pause
    exit /b 1
)

echo ✓ Output files found
echo.
echo Starting dashboard...
echo The dashboard will be available at: http://127.0.0.1:8050
echo.
echo Press Ctrl+C to stop the dashboard
echo.

REM Launch dashboard
python dashboard.py
