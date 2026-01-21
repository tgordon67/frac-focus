#!/bin/bash
# Automated FracFocus Analysis Pipeline
# This script downloads data, runs analysis, and optionally launches dashboard
# Can be run via cron for automatic updates

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory
mkdir -p logs

# Log file for this run
LOG_FILE="logs/automation_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "FracFocus Automated Analysis Pipeline"
log "=========================================="

# Step 1: Download latest data
log "Step 1: Downloading latest FracFocus data..."
if python3 download_data.py >> "$LOG_FILE" 2>&1; then
    log "✓ Data download complete"
else
    log "✗ Data download failed or skipped (see log)"
    # Continue anyway - maybe we have existing data
fi

# Check if data exists
if [ ! -f "data/fracfocus_data.zip" ] && [ ! -f "data/consolidated_data.csv" ]; then
    log "ERROR: No data available. Please download manually from:"
    log "  https://www.fracfocusdata.org/digitaldownload/FracFocusCSV.zip"
    log "  Save to: data/fracfocus_data.zip"
    exit 1
fi

# Step 2: Run analysis
log ""
log "Step 2: Running FracFocus analysis..."
if python3 fracfocus_analysis.py >> "$LOG_FILE" 2>&1; then
    log "✓ Analysis complete"
else
    log "✗ Analysis failed (see log: $LOG_FILE)"
    exit 1
fi

# Step 3: Generate summary report
log ""
log "Step 3: Generating summary report..."

# Count output files
OUTPUT_COUNT=$(ls -1 output/*.csv 2>/dev/null | wc -l)
log "Generated $OUTPUT_COUNT output files"

# Display summary from latest quarterly_by_basin.csv
if [ -f "output/quarterly_by_basin.csv" ]; then
    # Get latest quarter
    LATEST_QUARTER=$(tail -n +2 output/quarterly_by_basin.csv | cut -d',' -f1 | sort | tail -1)
    log "Latest quarter in data: $LATEST_QUARTER"
fi

log ""
log "=========================================="
log "Pipeline complete!"
log "=========================================="
log "Output files available in: $SCRIPT_DIR/output/"
log "Validation report: $SCRIPT_DIR/output/validation_report.txt"
log ""
log "To view results:"
log "  Option 1: Run dashboard - python3 dashboard.py"
log "  Option 2: Open CSV files in output/ directory"
log ""
log "Full log: $LOG_FILE"

# Clean up old logs (keep last 10)
log "Cleaning up old logs..."
ls -t logs/automation_*.log | tail -n +11 | xargs -r rm
log "Done!"

exit 0
