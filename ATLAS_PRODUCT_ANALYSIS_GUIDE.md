# Atlas Product-Level Analysis Guide

## What This Script Does

`atlas_product_analysis.py` processes FracFocus data to extract **Atlas Energy Solutions' specific volumes by product type over time**.

### Key Features:
1. **Identifies Atlas entities** using 10-K Exhibit 21.1 subsidiary list
2. **Filters to products Atlas actually makes** (excludes Northern White, ceramic, resin-coated)
3. **Processes all Registry CSV files** efficiently
4. **Outputs time series**: Year | Quarter | Month | Product | Tonnes

---

## Atlas Entity Identification

Based on **Atlas 10-K Exhibit 21.1**, the script recognizes these as Atlas:

```
ATLAS ENERGY SOLUTIONS
ATLAS SAND COMPANY (LLC)
ATLAS SAND CO
ATLAS SAND OPERATING
AESI HOLDINGS
OLC KERMIT
OLC MONAHANS
FOUNTAINHEAD LOGISTICS
CAPITAL SAND (legacy brand)
```

**Why this matters**: FracFocus records show legal entity names, not the public parent brand. All these are the same economic entity (consolidated under NYSE: AESI).

---

## Product Filtering

### ✅ Products Atlas DOES Produce:

**Primary Mesh Sizes:**
- 40/70 Mesh (most common)
- 100 Mesh
- 40/140 Brown Sand

**Regional/Permian Sand:**
- West TX 40/70 / 100 Mesh
- Permian regional sand
- San Antonio sand
- Common Brown sand

**Total: ~30 product variations** (all Permian basin regional sand)

### ❌ Products Atlas DOES NOT Produce:

**Northern White Sand:**
- Common/Premium White 40/70, 100 Mesh
- Powder River / Western Mesh

**Specialty Proppants:**
- Resin-coated (RCS, CRC)
- Ceramic (CarboLite, Deeprop)
- Engineered proppants

**Why excluded**: Atlas mines ONLY in-basin Permian brown sand. No Northern White capability, no coating facilities, no ceramic manufacturing.

---

## Input Data

The script expects **FracFocus Registry CSV files** in the `data/` directory:

```
data/
├── FracFocusRegistry_1.csv
├── FracFocusRegistry_2.csv
├── FracFocusRegistry_3.csv
├── ...
└── FracFocusRegistry_15.csv
```

**Where to get these:**
- Download from FracFocus.org
- Or run `python download_data.py` first to get consolidated data
- Or extract from `fracfocus_data.zip`

---

## How to Run

```bash
# Make sure you have FracFocus data in data/ directory
python atlas_product_analysis.py
```

**Processing flow:**
1. Loads each Registry CSV file
2. Filters to proppant records
3. Identifies Atlas suppliers
4. Validates products Atlas makes
5. Calculates volumes (MassIngredient or proxy)
6. Adds time dimensions (Year, Quarter, Month)
7. Aggregates by product and time
8. Saves outputs

**Expected runtime:** 5-15 minutes (depending on data size)

---

## Output Files

All saved to `output/atlas/`:

### 1. `atlas_product_details.csv`
**Row-level data** with all Atlas proppant records:

| Column | Description |
|--------|-------------|
| DisclosureId | Unique frac job ID |
| JobStartDate | Job start date |
| Supplier | Atlas entity name |
| TradeName | Product name |
| Volume_tonnes | Calculated volume |
| Year, Quarter, Month | Time dimensions |
| Product_Category | Standardized category |

**Use for**: Detailed analysis, auditing, validation

### 2. `atlas_product_timeseries.csv`
**Aggregated time series** (the main output):

| Year | Quarter | Month | Product_Category | Volume_tonnes | Job_Count |
|------|---------|-------|------------------|---------------|-----------|
| 2023 | 1 | 1 | 40/70 Mesh | 45,230 | 120 |
| 2023 | 1 | 1 | 100 Mesh | 18,540 | 45 |
| ... | ... | ... | ... | ... | ... |

**Use for**: Time series analysis, forecasting, visualization

### 3. `atlas_product_summary.txt`
**Human-readable report** with:
- Total volumes by product
- Quarterly trends
- Job counts
- Date ranges

**Use for**: Quick overview, presentations

---

## Understanding the Output

### Product Categories (Standardized)

The script maps specific product names to categories:

| Category | Examples | Atlas % |
|----------|----------|---------|
| **40/70 Mesh** | "40/70", "40/70 Regional", "West TX 40/70" | ~60-70% |
| **100 Mesh** | "100", "100M", "100 Mesh Permian" | ~25-35% |
| **40/140 Mesh** | "40/140 Brown Damp", "Permian 40/140" | ~5-10% |
| **Sand (Unspecified)** | "Sand", "Silica Sand" (generic) | ~1-5% |
| **Other Regional** | Catch-all for other Permian products | ~1-5% |

**Why standardize?** FracFocus has 50+ product name variations for essentially the same products. Standardization enables time series analysis.

### Volume Calculation Methods

**Priority 1: MassIngredient** (when available)
```
Volume (tonnes) = sum(MassIngredient) / 2204.62 lbs/tonne
```
- Most accurate (directly reported)
- Available in ~50-70% of records

**Priority 2: Proxy Method** (fallback)
```
Volume (tonnes) = (PercentHFJob / 100) × TotalBaseWaterVolume × 8.34 / 2204.62
```
- Based on water volume and percentage
- Used when MassIngredient is missing

The script logs which method is used for what % of records.

---

## Validation Checks

### 1. Data Completeness Test
```python
# Check how many records have Supplier data
supplier_completeness = records_with_supplier / total_records
```

**Good**: >85%
**Warning**: 70-85%
**Problem**: <70% (too much missing data)

### 2. Volume Reasonableness Test
```python
# Typical Atlas volumes
avg_volume_per_job = 4-8 million lbs = 1,800-3,600 tonnes
total_quarterly_volume = 150-400 million lbs = 68,000-180,000 tonnes
```

If your output shows wildly different numbers, investigate:
- Are we capturing all Atlas entities?
- Are we excluding products we shouldn't?
- Is MassIngredient data quality poor?

### 3. Product Mix Validation

**Expected Atlas product mix** (rough estimate):
- 40/70 mesh: 60-70%
- 100 mesh: 25-35%
- 40/140 mesh: 5-10%
- Other: <5%

If you see:
- 100% in one category → product filter is too narrow
- Even distribution → product filter is too broad

---

## Integration with Revenue Model

This product-level analysis feeds into your revenue prediction model:

```
Revenue = Σ (Volume_by_product × Price_by_product)

Where:
- Volume_by_product: From this script's output
- Price_by_product:
  - 40/70: $55-65/ton (commodity pricing)
  - 100 mesh: $50-60/ton (slightly cheaper, finer)
  - 40/140: $50-58/ton (brown sand, local)
```

**Why product-level matters:**
- Different products have different pricing
- 40/70 typically trades at premium to 100 mesh
- Blended average price = Σ (volume_pct × price)

**Example calculation:**
```
Q1 2024 Atlas volumes:
- 40/70: 120,000 tonnes @ $60/ton = $7.2M
- 100 mesh: 60,000 tonnes @ $55/ton = $3.3M
- 40/140: 20,000 tonnes @ $52/ton = $1.04M
Total: 200,000 tonnes → $11.54M revenue

Blended price: $11.54M / 200k tonnes = $57.70/ton
```

This is more accurate than assuming flat $60/ton for all products.

---

## Next Steps

### For Investment Analysis:

1. **Run this script** to get product-level volumes
2. **Compare to Atlas's 10-K reported volumes**
   - Get tons sold from quarterly filings
   - Test correlation with your FracFocus data
3. **Backsolve pricing by product**
   - Use reported revenue / reported volume
   - Break down by mesh size if disclosed
4. **Build revenue prediction model**
   - Forecast volumes by product
   - Apply product-specific pricing
   - Sum to total revenue

### For Due Diligence:

1. **Validate market share trends**
   ```python
   atlas_share = atlas_volume / total_permian_volume
   ```
   - Is Atlas gaining or losing share?
   - Which products are growing fastest?

2. **Analyze geographic mix**
   - Where is Atlas' volume concentrated?
   - Permian Sub-basins (Delaware vs Midland)?
   - County-level breakdown

3. **Track product mix evolution**
   - Is 40/70 growing vs 100 mesh?
   - Market preference shifts?
   - Pricing implications

---

## Troubleshooting

### Error: "No FracFocusRegistry_*.csv files found"

**Solution:**
```bash
# Option 1: Extract from ZIP
cd data/
unzip fracfocus_data.zip

# Option 2: Run consolidation first
python fracfocus_analysis.py

# Option 3: Download fresh data
python download_data.py
```

### Warning: "Supplier data completeness only 45%"

**Problem**: Too many records missing Supplier field

**Impact**: You're only capturing ~half of Atlas's volume

**Solutions:**
1. Check if Supplier field exists in your data
2. Try using OperatorName as fallback
3. Accept that pre-2015 data has poor supplier attribution

### Issue: Product volumes seem too low

**Checklist:**
1. ✅ Are all Atlas entity names in the pattern list?
2. ✅ Are product filters too restrictive?
3. ✅ Is data from all registries being processed?
4. ✅ Check the ingredient-level bug is fixed (should be after recent commits)

---

## Example Output

### Sample Time Series (Recent Quarters):

```
Year | Quarter | Month | Product_Category | Volume_tonnes | Job_Count
-----|---------|-------|------------------|---------------|----------
2023 | 1       | 1     | 40/70 Mesh      | 45,230        | 120
2023 | 1       | 1     | 100 Mesh        | 18,540        | 45
2023 | 1       | 2     | 40/70 Mesh      | 52,180        | 138
2023 | 1       | 2     | 100 Mesh        | 21,340        | 52
2023 | 1       | 3     | 40/70 Mesh      | 48,920        | 128
2023 | 1       | 3     | 100 Mesh        | 19,870        | 48
2023 | 2       | 4     | 40/70 Mesh      | 55,340        | 145
...
```

**What this tells you:**
- Atlas's 40/70 mesh volume in Jan 2023: 45,230 tonnes from 120 jobs
- Average per job: 377 tonnes = 831,000 lbs (reasonable for Permian jobs)
- 40/70 is ~70% of volume, 100 mesh is ~30% (typical mix)

---

## Files Reference

| File | Purpose |
|------|---------|
| `atlas_product_analysis.py` | Main script (this analysis) |
| `atlas_analysis.py` | Supplier-level analysis (all products combined) |
| `fracfocus_analysis.py` | Base market analysis (all suppliers) |
| `MODEL_VALIDATION.md` | Validation framework for revenue model |
| `BUG_FIX_SUMMARY.md` | Critical bug fixes applied |

**Workflow:**
```
1. fracfocus_analysis.py → Market-level demand
2. atlas_analysis.py → Atlas volumes (supplier focus)
3. atlas_product_analysis.py → Atlas by product (THIS SCRIPT)
4. Use outputs → Build revenue model
```

---

## Questions?

This script is built for:
- **Investor due diligence** on Atlas Energy Solutions
- **Revenue prediction** modeling
- **Market share** analysis
- **Product mix** tracking

If you need to modify:
- **Add more product categories**: Edit `standardize_product_category()`
- **Change Atlas entities**: Edit `atlas_supplier_patterns` list
- **Adjust product filters**: Edit `atlas_products_definite` / `atlas_products_exclude`
- **Change time granularity**: Modify `aggregate_by_time_and_product()`
