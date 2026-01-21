#!/bin/bash
# Launch FracFocus Dashboard
# Simple launcher for the interactive dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "FracFocus Analysis Dashboard"
echo "=========================================="
echo ""

# Check if output files exist
if [ ! -f "output/quarterly_by_basin.csv" ]; then
    echo "WARNING: No analysis output files found!"
    echo ""
    echo "Please run the analysis first:"
    echo "  ./automate_analysis.sh"
    echo ""
    echo "Or manually:"
    echo "  python3 download_data.py"
    echo "  python3 fracfocus_analysis.py"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✓ Output files found"
echo ""
echo "Starting dashboard..."
echo "The dashboard will be available at: http://127.0.0.1:8050"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

# Launch dashboard
python3 dashboard.py
