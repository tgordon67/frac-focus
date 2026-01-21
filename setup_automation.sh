#!/bin/bash
# Setup Automation for FracFocus Analysis
# This script configures cron to run the analysis automatically

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "FracFocus Automation Setup"
echo "=========================================="
echo ""

# Make scripts executable
chmod +x "$SCRIPT_DIR/automate_analysis.sh"
chmod +x "$SCRIPT_DIR/run_analysis.sh"

echo "✓ Made scripts executable"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    # Linux or macOS
    echo "Detected: Linux/macOS"
    echo ""
    echo "To schedule automatic updates, add this to your crontab:"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "# Run FracFocus analysis Monday-Friday at 8 AM"
    echo "0 8 * * 1-5 cd $SCRIPT_DIR && ./automate_analysis.sh"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "To edit your crontab, run: crontab -e"
    echo ""
    echo "Alternative schedules:"
    echo "  Daily at 6 AM:        0 6 * * * cd $SCRIPT_DIR && ./automate_analysis.sh"
    echo "  Twice daily (6 AM, 6 PM): 0 6,18 * * * cd $SCRIPT_DIR && ./automate_analysis.sh"
    echo "  Every Monday at 7 AM: 0 7 * * 1 cd $SCRIPT_DIR && ./automate_analysis.sh"
    echo ""

    # Offer to add cron job automatically
    read -p "Would you like to add the Monday-Friday 8 AM schedule now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Add to crontab
        (crontab -l 2>/dev/null; echo "# FracFocus Analysis - Monday-Friday at 8 AM"; echo "0 8 * * 1-5 cd $SCRIPT_DIR && ./automate_analysis.sh") | crontab -
        echo "✓ Cron job added successfully!"
        echo ""
        echo "View your crontab with: crontab -l"
        echo "Remove it later with: crontab -e (then delete the FracFocus lines)"
    else
        echo "Skipped automatic setup. Add manually using instructions above."
    fi

elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "Detected: Windows"
    echo ""
    echo "For Windows Task Scheduler automation:"
    echo "1. Open Task Scheduler (taskschd.msc)"
    echo "2. Create Basic Task → Name: 'FracFocus Analysis'"
    echo "3. Trigger: Daily or Weekly (Monday-Friday)"
    echo "4. Action: Start a program"
    echo "5. Program: $SCRIPT_DIR/automate_analysis.bat"
    echo ""
    echo "Or run manually: python download_data.py && python fracfocus_analysis.py"
fi

echo ""
echo "=========================================="
echo "Quick Test"
echo "=========================================="
echo ""
read -p "Would you like to run a test now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Running test (downloading data and analyzing)..."
    ./automate_analysis.sh
fi

echo ""
echo "Setup complete!"
