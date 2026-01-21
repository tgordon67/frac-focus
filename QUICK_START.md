# FracFocus Analysis Tool - Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- 8GB+ RAM (16GB recommended for full dataset)
- ~10GB free disk space

## Installation

```bash
# Clone repository
git clone <repository-url>
cd frac-focus

# Install dependencies
pip install -r requirements.txt

# Test installation (optional but recommended)
python test_installation.py
```

## Quick Start (3 Steps)

### Step 1: Get Data

**Option A - Download from FracFocus:**
1. Go to https://fracfocus.org/data-download
2. Click "Download CSV" under "Oil and Gas Data"
3. Save ZIP to: `data/fracfocus_data.zip`

**Option B - Use existing consolidated data:**
- Place your CSV file at: `data/consolidated_data.csv`

### Step 2: Run Analysis

```bash
# Option A: Use helper script (Linux/Mac)
./run_analysis.sh

# Option B: Run manually
python fracfocus_analysis.py
```

**Wait:** 10-60 minutes depending on data size

**Output:** 6 CSV files + validation report in `output/` directory

### Step 3: View Results

```bash
# Option A: Interactive dashboard
python dashboard.py
# Then open browser to: http://127.0.0.1:8050

# Option B: Analyze CSV files directly
# Open files in output/ folder with Excel or Python
```

## Output Files Reference

| File | Description | Use Case |
|------|-------------|----------|
| `quarterly_by_basin.csv` | Quarterly totals by basin | Basin trend analysis |
| `quarterly_by_state.csv` | Quarterly totals by state | State-level analysis |
| `quarterly_by_county.csv` | Quarterly totals by county | County-level detail |
| `permian_by_county.csv` | Permian Basin counties only | AESI supply chain focus |
| `quarterly_detail.csv` | Disclosure-level detail | Custom analysis |
| `validation_report.txt` | Data quality report | Understanding limitations |

## Key Metrics Explained

| Metric | Unit | Description |
|--------|------|-------------|
| `Proppant_lbs` | pounds | Total proppant used |
| `Proppant_MM_lbs` | million lbs | Proppant (easier to read) |
| `Water_gal` | gallons | Total water used |
| `Water_MM_gal` | million gallons | Water (easier to read) |
| `Well_count` | count | Number of frac jobs |
| `Avg_Proppant_per_Well_lbs` | lbs/well | Proppant intensity |
| `Avg_Water_per_Well_gal` | gal/well | Water intensity |

## Common Tasks

### Analyze Specific Basin

**Dashboard:** Select basin from dropdown

**Python:**
```python
import pandas as pd
df = pd.read_csv('output/quarterly_by_basin.csv')
permian = df[df['Basin'] == 'Permian Basin']
```

### Filter Date Range

**Dashboard:** View automatically shows full range

**Python:**
```python
df_2023 = df[df['Quarter'] >= '2023Q1']
```

### Export Data from Dashboard

1. Select your view and filters
2. Click "Download Data" button
3. CSV file downloads automatically

### Add Custom Basin

1. Edit `basin_definitions.json`
2. Add your basin with counties
3. Re-run analysis

Example:
```json
{
  "basins": {
    "My Custom Basin": {
      "states": {
        "Texas": ["County1", "County2"]
      }
    }
  }
}
```

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| "File not found" error | Download data to `data/fracfocus_data.zip` |
| Dashboard shows no data | Run `python fracfocus_analysis.py` first |
| Memory error | Close other apps, or filter by state/date |
| Port 8050 in use | Kill other process or change port in dashboard.py |
| Slow performance | Use SSD, increase RAM, or process smaller subset |

## Performance Tips

- **First run:** Use consolidated CSV to skip extraction (~30 min saved)
- **Large dataset:** Filter by state before processing
- **Repeated analysis:** Keep `consolidated_data.csv` to skip extraction
- **Dashboard:** Pre-filter data to specific regions for faster loading

## File Locations

```
frac-focus/
├── data/                  # Put data here
│   └── fracfocus_data.zip # Downloaded ZIP file
├── output/                # Results appear here
│   ├── quarterly_by_basin.csv
│   └── ...
├── fracfocus_analysis.py  # Run this first
└── dashboard.py           # Run this second
```

## Getting Help

1. **Data fields:** See `DATA_DICTIONARY.md`
2. **Basin definitions:** See `basin_definitions.json`
3. **Data quality:** Check `output/validation_report.txt`
4. **Full guide:** See `README.md`

## Next Steps

After completing Quick Start:

1. **Review validation report** to understand data limitations
2. **Explore dashboard** to visualize trends
3. **Customize basins** if needed (edit `basin_definitions.json`)
4. **Export filtered data** for deeper analysis in Excel/Python
5. **Read DATA_DICTIONARY.md** to understand all fields

## Key Concepts

### Quarterly Attribution
- **Short jobs (≤45 days):** 100% attributed to start quarter
- **Long jobs (>45 days):** Split proportionally across quarters
- **Why?** Reflects just-in-time proppant delivery

### Basin Classification
- Based on county location
- Pre-configured for 9 major basins
- "Other" category for unclassified regions

### Proppant Calculation
```
Proppant (lbs) = (Percent / 100) × Water (gal) × 8.34 lbs/gal
```

## Sample Workflow

```bash
# 1. Test installation
python test_installation.py

# 2. Download data (manual step on website)

# 3. Run full analysis
python fracfocus_analysis.py

# 4. Review validation
cat output/validation_report.txt

# 5. Launch dashboard
python dashboard.py

# 6. Analyze in browser
# Open http://127.0.0.1:8050
# Select: View=Basin, Metric=Proppant, Basin=Permian Basin

# 7. Export results
# Click "Download Data" in dashboard
```

## Typical Analysis Time

| Dataset | Extraction | Analysis | Total |
|---------|-----------|----------|-------|
| Small (100K rows) | 2 min | 5 min | 7 min |
| Medium (1M rows) | 5 min | 15 min | 20 min |
| Large (10M+ rows) | 15 min | 45 min | 60 min |

## Support

Questions? Check these resources:
- `README.md` - Full documentation
- `DATA_DICTIONARY.md` - Field definitions
- `validation_report.txt` - Data quality report
- `basin_definitions.json` - Region mappings

---

**Ready to start? Run:** `python test_installation.py`
