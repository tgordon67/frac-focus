#!/bin/bash
# Quick start script for FracFocus Analysis Tool
# Usage: ./run_analysis.sh [--dashboard-only]

set -e  # Exit on error

echo "=========================================="
echo "FracFocus Proppant Analysis Tool"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import pandas" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# If --dashboard-only flag is set, skip analysis
if [ "$1" == "--dashboard-only" ]; then
    echo ""
    echo "Launching dashboard (skipping analysis)..."
    echo "Dashboard will be available at: http://127.0.0.1:8050"
    echo ""
    python3 dashboard.py
    exit 0
fi

# Check if data exists
if [ ! -f "data/fracfocus_data.zip" ] && [ ! -f "data/consolidated_data.csv" ]; then
    echo ""
    echo "=========================================="
    echo "DATA DOWNLOAD REQUIRED"
    echo "=========================================="
    echo ""
    echo "Please download FracFocus data:"
    echo "1. Visit: https://fracfocus.org/data-download"
    echo "2. Click 'Download CSV' under 'Oil and Gas Data'"
    echo "3. Save the ZIP file to: data/fracfocus_data.zip"
    echo ""
    echo "Then run this script again."
    echo ""
    exit 1
fi

# Run analysis
echo ""
echo "=========================================="
echo "STEP 1: Running Analysis"
echo "=========================================="
echo "This may take 10-60 minutes depending on data size..."
echo ""

python3 fracfocus_analysis.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Analysis failed. Check the error messages above."
    exit 1
fi

echo ""
echo "=========================================="
echo "STEP 2: Launching Dashboard"
echo "=========================================="
echo "Dashboard will be available at: http://127.0.0.1:8050"
echo "Press Ctrl+C to stop the dashboard"
echo ""

python3 dashboard.py
