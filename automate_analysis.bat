@echo off
REM Automated FracFocus Analysis Pipeline for Windows
REM This script downloads data, runs analysis
REM Can be scheduled via Windows Task Scheduler

setlocal enabledelayedexpansion

REM Change to script directory
cd /d "%~dp0"

REM Create logs directory
if not exist logs mkdir logs

REM Log file for this run
set LOG_FILE=logs\automation_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOG_FILE=%LOG_FILE: =0%

echo ========================================== >> %LOG_FILE%
echo FracFocus Automated Analysis Pipeline >> %LOG_FILE%
echo ========================================== >> %LOG_FILE%
echo [%date% %time%] Starting pipeline >> %LOG_FILE%

REM Step 1: Download latest data
echo Step 1: Downloading latest FracFocus data...
echo [%date% %time%] Downloading data >> %LOG_FILE%
python download_data.py >> %LOG_FILE% 2>&1

if not exist data\fracfocus_data.zip (
    if not exist data\consolidated_data.csv (
        echo ERROR: No data available >> %LOG_FILE%
        echo Please download manually from:
        echo   https://www.fracfocusdata.org/digitaldownload/FracFocusCSV.zip
        echo   Save to: data\fracfocus_data.zip
        exit /b 1
    )
)

REM Step 2: Run analysis
echo.
echo Step 2: Running FracFocus analysis...
echo [%date% %time%] Running analysis >> %LOG_FILE%
python fracfocus_analysis.py >> %LOG_FILE% 2>&1

if errorlevel 1 (
    echo Analysis failed - see log: %LOG_FILE%
    exit /b 1
)

REM Step 3: Summary
echo.
echo ========================================== >> %LOG_FILE%
echo Pipeline complete! >> %LOG_FILE%
echo ========================================== >> %LOG_FILE%
echo Output files available in: %cd%\output\ >> %LOG_FILE%
echo Validation report: %cd%\output\validation_report.txt >> %LOG_FILE%
echo.
echo To view results: >> %LOG_FILE%
echo   Run: python dashboard.py >> %LOG_FILE%

echo.
echo Pipeline complete!
echo Full log: %LOG_FILE%

exit /b 0
