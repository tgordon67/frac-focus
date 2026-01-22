# FracFocus Automation Guide

## Overview

This system provides **fully automated** FracFocus data analysis with recurring updates. Once configured, it will:

1. **Download** latest data from FracFocus (updated 5 days/week)
2. **Analyze** the data and calculate proppant/water metrics
3. **Generate** output reports and dashboard data
4. **Repeat** automatically on your chosen schedule

**Zero manual intervention required after setup!**

---

## Quick Start (3 Steps)

### Step 1: Initial Setup & Test

```bash
# Run the interactive setup
./setup_automation.sh

# This will:
# - Make all scripts executable
# - Offer to configure automatic scheduling
# - Run a test to verify everything works
```

### Step 2: Configure Schedule (Recommended)

The setup script offers to add a cron job for you. Recommended schedule:

```bash
# Monday-Friday at 8 AM (after FracFocus updates)
0 8 * * 1-5 cd /home/user/frac-focus && ./automate_analysis.sh
```

This runs automatically every weekday morning, downloading new data and updating your dashboard.

### Step 3: Launch Dashboard Anytime

```bash
./launch_dashboard.sh

# Opens at: http://127.0.0.1:8050
```

**That's it!** Your analysis stays up-to-date automatically.

---

## FracFocus Update Schedule

**Official FracFocus Update Frequency:**
- **5 days per week** (Monday-Friday)
- Data includes latest disclosures submitted

**Your Automation Options:**
1. **Daily (Recommended):** Runs every day, skips download if data <1 day old
2. **Weekdays Only:** Runs Monday-Friday (matches FracFocus schedule)
3. **Weekly:** Runs once per week (e.g., every Monday)
4. **On-Demand:** Run manually anytime with `./automate_analysis.sh`

---

## How It Works

### Automated Pipeline Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. DOWNLOAD (download_data.py)                         │
│     - Checks if data >1 day old                         │
│     - Downloads from FracFocus if needed                │
│     - Creates backup of previous version                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. ANALYZE (fracfocus_analysis.py)                     │
│     - Extract & consolidate CSVs                        │
│     - Clean data & calculate proppant                   │
│     - Quarterly attribution                             │
│     - Regional aggregation                              │
│     - Validation checks                                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. OUTPUTS READY                                       │
│     - 6 CSV files in output/                            │
│     - validation_report.txt                             │
│     - Dashboard ready to launch                         │
└─────────────────────────────────────────────────────────┘
```

### Smart Features

1. **Incremental Downloads**
   - Only downloads if data >1 day old
   - Saves bandwidth and time
   - Force mode available: `python download_data.py --force`

2. **Automatic Backups**
   - Keeps last 5 versions in `data/backups/`
   - Named with timestamps
   - Auto-cleanup of old backups

3. **Comprehensive Logging**
   - All runs logged to `logs/`
   - Timestamped log files
   - Keeps last 10 logs automatically

4. **Error Handling**
   - Continues if download fails (uses existing data)
   - Clear error messages
   - Logs all failures

---

## Files & Scripts

### Main Automation Scripts

| File | Purpose | Platform | Usage |
|------|---------|----------|-------|
| `automate_analysis.sh` | Full pipeline | Linux/Mac | `./automate_analysis.sh` |
| `automate_analysis.bat` | Full pipeline | Windows | `automate_analysis.bat` |
| `download_data.py` | Download only | All | `python download_data.py` |
| `launch_dashboard.sh` | Dashboard launcher | Linux/Mac | `./launch_dashboard.sh` |
| `launch_dashboard.bat` | Dashboard launcher | Windows | `launch_dashboard.bat` |
| `setup_automation.sh` | Interactive setup | Linux/Mac | `./setup_automation.sh` |

### Manual Operations

```bash
# Download new data (force)
python download_data.py --force

# Run analysis only (skip download)
python fracfocus_analysis.py

# Launch dashboard
python dashboard.py

# Or use convenience script
./launch_dashboard.sh
```

---

## Scheduling Options

### Linux/macOS (Cron)

Edit crontab:
```bash
crontab -e
```

Add one of these schedules:

```bash
# Every weekday at 8 AM
0 8 * * 1-5 cd /home/user/frac-focus && ./automate_analysis.sh

# Every day at 6 AM
0 6 * * * cd /home/user/frac-focus && ./automate_analysis.sh

# Twice daily (6 AM and 6 PM)
0 6,18 * * * cd /home/user/frac-focus && ./automate_analysis.sh

# Every Monday at 7 AM
0 7 * * 1 cd /home/user/frac-focus && ./automate_analysis.sh

# Every 4 hours (for frequent updates)
0 */4 * * * cd /home/user/frac-focus && ./automate_analysis.sh
```

**View your scheduled jobs:**
```bash
crontab -l
```

**Remove automation:**
```bash
crontab -e  # Then delete the FracFocus line
```

### Windows (Task Scheduler)

1. Open Task Scheduler (`taskschd.msc`)
2. **Create Basic Task**
3. Name: `FracFocus Analysis`
4. Trigger: Choose frequency
   - **Daily** → Set time (e.g., 8:00 AM)
   - **Weekly** → Select days (Mon-Fri) and time
5. Action: **Start a program**
6. Program: `C:\path\to\frac-focus\automate_analysis.bat`
7. Finish

**Test your task:**
- Right-click → Run
- Check `logs/automation_*.log` for output

---

## Monitoring & Logs

### Log Files

All automation runs create logs in `logs/` directory:

```
logs/
├── download_20260121.log           # Download logs (by date)
├── automation_20260121_080000.log  # Full pipeline logs (by timestamp)
└── analysis_run.log                # Manual analysis runs
```

### Check Last Run

```bash
# View latest automation log
ls -t logs/automation_*.log | head -1 | xargs cat

# Check download status
cat logs/download_$(date +%Y%m%d).log

# View last 20 lines of latest log
ls -t logs/automation_*.log | head -1 | xargs tail -20
```

### Verify Outputs

```bash
# Check output files
ls -lh output/

# View validation report
cat output/validation_report.txt

# Check latest quarter
tail -1 output/quarterly_by_basin.csv
```

---

## Troubleshooting

### Problem: Automation not running

**Check cron:**
```bash
crontab -l  # Verify job is listed
grep CRON /var/log/syslog  # Check if cron is executing (Linux)
```

**Check permissions:**
```bash
chmod +x automate_analysis.sh
chmod +x launch_dashboard.sh
```

**Test manually:**
```bash
./automate_analysis.sh
# Check output and logs/automation_*.log
```

### Problem: Download fails

**Check internet connection:**
```bash
ping fracfocus.org
```

**Manual download:**
1. Go to: https://www.fracfocusdata.org/digitaldownload/FracFocusCSV.zip
2. Download ZIP file
3. Save to: `data/fracfocus_data.zip`

**Force re-download:**
```bash
python download_data.py --force
```

### Problem: Analysis fails

**Check data file:**
```bash
ls -lh data/fracfocus_data.zip
# Should be ~410 MB
```

**Check disk space:**
```bash
df -h .
# Need ~10 GB free for processing
```

**View error logs:**
```bash
cat logs/automation_*.log | grep ERROR
```

### Problem: Dashboard won't start

**Verify outputs exist:**
```bash
ls output/*.csv
# Should show 4-5 CSV files
```

**Check port availability:**
```bash
lsof -i :8050
# If in use, kill process or use different port
```

**Run analysis first:**
```bash
./automate_analysis.sh
```

---

## Advanced Configuration

### Change Update Frequency

Edit the smart download check in `download_data.py`:

```python
# Line ~130: Change age threshold
if file_age_days > 1:  # Change 1 to desired days
```

### Customize Backup Retention

Edit backup cleanup in `download_data.py`:

```python
# Line ~86: Change number of backups to keep
if len(backups) > 5:  # Change 5 to desired count
```

### Add Email Notifications

Add to end of `automate_analysis.sh`:

```bash
# Send email on completion
echo "FracFocus analysis complete" | mail -s "Analysis Update" your@email.com
```

### Run Analysis on Subset

Edit `fracfocus_analysis.py` to filter data:

```python
# After loading data, add filter
df = df[df['StateName'].isin(['Texas', 'New Mexico'])]  # Permian focus
```

---

## Performance Notes

### Typical Run Times

| Step | Time | Notes |
|------|------|-------|
| Download | 2-5 min | 410 MB file |
| Analysis | 15-60 min | Depends on data size |
| Dashboard startup | <10 sec | Instant once data ready |

**Total automated run:** ~20-65 minutes

### Resource Usage

- **Disk:** ~10 GB during processing, ~2 GB for outputs
- **RAM:** 2-8 GB during analysis
- **Network:** 410 MB download per update

### Optimization Tips

1. **Schedule during off-hours** (e.g., 2 AM) to avoid impacting work
2. **Use SSD** for faster processing
3. **Increase RAM** if processing >10M rows
4. **Keep backups on separate drive** if disk space limited

---

## Maintenance

### Weekly Tasks

✅ Check that automation ran successfully:
```bash
ls -lt logs/automation_*.log | head -5
```

✅ Verify latest data in dashboard

### Monthly Tasks

✅ Review disk space usage:
```bash
du -sh data/ output/ logs/
```

✅ Clean up old backups if needed:
```bash
ls -lh data/backups/
```

### As Needed

✅ Update basin definitions in `basin_definitions.json`

✅ Review validation report for new issues:
```bash
cat output/validation_report.txt
```

---

## Complete Example Workflow

### Initial Setup (One Time)

```bash
# 1. Clone/navigate to project
cd /home/user/frac-focus

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run setup
./setup_automation.sh
# → Choose 'y' to add cron job
# → Choose 'y' to run test

# 4. Wait for initial analysis (~30 min)

# 5. Launch dashboard
./launch_dashboard.sh
```

### Daily Use (Automated)

```
Morning (8 AM):
  → Cron runs automate_analysis.sh
  → Downloads new data (if available)
  → Runs analysis
  → Updates output files

Anytime you want:
  → Run: ./launch_dashboard.sh
  → View updated charts and data
  → Export CSV as needed
```

### Manual Updates

```bash
# Force update right now
python download_data.py --force
python fracfocus_analysis.py
./launch_dashboard.sh
```

---

## Summary

✅ **Fully Automated:** Set and forget
✅ **Smart Updates:** Only downloads when needed
✅ **Reliable:** Backups, logging, error handling
✅ **Flexible:** On-demand or scheduled
✅ **Cross-platform:** Linux, Mac, Windows

**You're all set for automated FracFocus analysis!**

For questions, see:
- `README.md` - Full project documentation
- `QUICK_START.md` - Quick reference
- `DATA_DICTIONARY.md` - Field definitions
- `logs/` - Detailed execution logs
