# FracFocus Proppant & Water Demand Analysis Tool

An interactive data analysis tool for processing FracFocus Chemical Disclosure Registry data to track proppant and water consumption by quarter and region, with focus on the Permian Basin for AESI supply chain analysis.

## Project Status

🚧 **In Development** 🚧

### Completed Phases
- ✅ Phase 1: Data Acquisition (In Progress)
- ⏳ Phase 2: Data Cleaning
- ⏳ Phase 3: Proppant Calculations
- ⏳ Phase 4: Quarterly Attribution
- ⏳ Phase 5: Regional Aggregation
- ⏳ Phase 6: Interactive Visualization
- ⏳ Phase 7: Validation & Edge Cases

## Installation

```bash
pip install -r requirements.txt
```

## Data Acquisition

### Manual Download Required

1. Visit [FracFocus Data Download](https://fracfocus.org/data-download)
2. Click "Download CSV" under "Oil and Gas Data"
3. Save the ZIP file to `data/fracfocus_data.zip`

### Alternative: Use Existing Data

If you already have consolidated data:
```bash
# Place your consolidated CSV in:
data/consolidated_data.csv
```

## Usage

```bash
python fracfocus_analysis.py
```

## Project Structure

```
frac-focus/
├── fracfocus_analysis.py    # Main analysis script
├── requirements.txt          # Python dependencies
├── data/                     # Data directory (gitignored)
│   ├── fracfocus_data.zip   # Downloaded ZIP file
│   └── consolidated_data.csv # Consolidated data
├── output/                   # Analysis outputs
│   ├── quarterly_summary.csv
│   └── validation_report.txt
└── README.md                 # This file
```

## Key Features (Planned)

### Data Processing
- Automated data consolidation from multiple CSV files
- Outlier detection and removal
- Missing data handling
- Proppant mass calculation from percentages

### Quarterly Attribution
- Smart quarterly attribution for multi-quarter jobs
- Just-in-time delivery assumption (proppant attributed to job start)
- Proportional distribution for long-duration jobs

### Regional Analysis
- Pre-configured basin definitions (Permian, Eagle Ford, Haynesville, etc.)
- County-level aggregation
- State-level rollups

### Interactive Dashboard
- Time series visualization
- Regional comparison
- Metric selection (proppant/water/well count)
- Export capabilities

## Data Quality Considerations

The FracFocus dataset has known quality issues:
- 2,000+ disclosures report sand > water (data entry errors)
- 30,000+ disclosures missing TotalBaseWaterVolume
- Outlier values (e.g., 1 trillion lbs proppant)
- Inconsistent MassIngredient reporting

This tool implements robust cleaning and validation to handle these issues.

## Business Context

### AESI Supply Chain Analysis

This tool is designed for financial modeling of proppant suppliers like AESI:

**Key Business Logic:**
- Proppant is delivered just-in-time (not stockpiled months in advance)
- Revenue is recognized when proppant is delivered/consumed
- Short jobs (≤45 days): 100% attributed to start quarter
- Long jobs (>45 days): Distributed proportionally across quarters

## Technical Details

### Proppant Calculation Method

**Primary Method:** Direct calculation from PercentHFJob

```python
Proppant_lbs = (PercentHFJob / 100) × TotalBaseWaterVolume × 8.34 lbs/gal
```

Where:
- `PercentHFJob` = % by mass of total fluid
- `TotalBaseWaterVolume` = Water volume in gallons
- `8.34 lbs/gal` = Water density

**Validation:** Compare against MassIngredient when available

### Quarterly Attribution Rules

| Job Duration | Attribution Method | Rationale |
|--------------|-------------------|-----------|
| ≤45 days     | 100% to start quarter | Typical frac job (3-5 days) |
| 46-365 days  | Proportional distribution | Multi-quarter jobs |
| >365 days    | Flag for manual review | Likely data errors |

## License

This tool is for internal analysis purposes.

## Data Source

FracFocus Chemical Disclosure Registry: https://fracfocus.org

**Citation:** FracFocus Chemical Disclosure Registry. Accessed [Date]. https://fracfocus.org/data-download
