"""
Validate FracFocus Data as Proxy for Atlas Revenue Growth

Tests if % change in FracFocus tonnage (2022→2023) can predict
% change in actual revenue (2022→2023).

Atlas Actual (from 10-K):
- 2022 Product sales: $408,446,000
- 2023 Product sales: $468,119,000
- Revenue growth: +14.6%
"""

import pandas as pd
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path('data')
CSV_FILE = DATA_DIR / 'FracFocusRegistry_13.csv'

# Constants
PRICE_PER_TON = 28.0  # $/ton (from user)
ACTUAL_PRODUCT_SALES_2022 = 408_446_000  # $ (from 10-K)
ACTUAL_PRODUCT_SALES_2023 = 468_119_000  # $ (from 10-K)
ACTUAL_REVENUE_GROWTH_PCT = ((ACTUAL_PRODUCT_SALES_2023 - ACTUAL_PRODUCT_SALES_2022) / ACTUAL_PRODUCT_SALES_2022) * 100
LBS_PER_TON = 2000.0


def normalize_supplier_name(supplier: str) -> str:
    """Normalize supplier name for matching."""
    if pd.isna(supplier):
        return ''

    normalized = str(supplier).upper().strip()
    normalized = normalized.replace(' LLC', '').replace(' INC', '').replace(' L.L.C.', '')
    normalized = normalized.replace(',', '').replace('.', '')

    return normalized


def is_atlas_supplier(supplier: str) -> bool:
    """
    Check if supplier is Atlas (permissive matching).
    Accepts anything with "ATLAS" in the name.
    """
    normalized = normalize_supplier_name(supplier)
    if not normalized:
        return False

    return 'ATLAS' in normalized


def calculate_proppant_mass(row: pd.Series) -> float:
    """
    Calculate proppant mass for a single disclosure.
    Uses percentage-based proxy method.

    Args:
        row: DataFrame row with disclosure data

    Returns:
        Proppant mass in pounds
    """
    try:
        # Get water volume (gallons)
        water_volume = row.get('TotalBaseWaterVolume', 0)
        if pd.isna(water_volume) or water_volume <= 0:
            return 0.0

        # Get proppant percentage
        proppant_pct = row.get('PercentHFJob', 0)
        if pd.isna(proppant_pct) or proppant_pct <= 0:
            return 0.0

        # Calculate total fluid mass (water is 8.34 lbs/gal)
        total_fluid_mass_lbs = water_volume * 8.34

        # Calculate proppant mass
        proppant_mass_lbs = (proppant_pct / 100.0) * total_fluid_mass_lbs

        return proppant_mass_lbs

    except Exception as e:
        logger.warning(f"Error calculating mass: {e}")
        return 0.0


def calculate_annual_tonnage(atlas_df: pd.DataFrame, year: int) -> tuple:
    """
    Calculate total tonnage for a specific year.

    Returns:
        (total_tonnes, unique_wells, avg_tonnes_per_well)
    """
    # Filter to specific year
    atlas_year = atlas_df[atlas_df['Year'] == year].copy()
    logger.info(f"\n{year} Atlas records: {len(atlas_year):,}")

    if len(atlas_year) == 0:
        logger.warning(f"No {year} Atlas records found!")
        return 0.0, 0, 0.0

    # Calculate proppant mass for EACH ingredient row (do NOT deduplicate!)
    logger.info(f"Calculating proppant mass for each ingredient row...")
    logger.info(f"Total ingredient rows: {len(atlas_year):,}")

    atlas_year['Proppant_Mass_Lbs'] = atlas_year.apply(calculate_proppant_mass, axis=1)

    # Remove records with zero mass
    atlas_year = atlas_year[atlas_year['Proppant_Mass_Lbs'] > 0]
    logger.info(f"Valid ingredient rows with mass: {len(atlas_year):,}")

    # Convert to tonnes
    atlas_year['Proppant_Tonnes'] = atlas_year['Proppant_Mass_Lbs'] / LBS_PER_TON

    # Group by DisclosureId and sum all proppant ingredients per well
    logger.info(f"Aggregating proppant by well (summing all ingredient rows)...")
    well_totals = atlas_year.groupby('DisclosureId').agg({
        'Proppant_Tonnes': 'sum',
        'JobStartDate': 'first',
        'Supplier': 'first'
    }).reset_index()

    unique_wells = len(well_totals)
    avg_per_well = well_totals['Proppant_Tonnes'].mean()
    total_tonnes = well_totals['Proppant_Tonnes'].sum()

    logger.info(f"Unique wells: {unique_wells:,}")
    logger.info(f"Average proppant per well: {avg_per_well:,.0f} tonnes")
    logger.info(f"Total tonnage: {total_tonnes:,.0f} tonnes")

    return total_tonnes, unique_wells, avg_per_well


def main():
    """Main validation logic"""
    logger.info("=" * 80)
    logger.info("FRACFOCUS DATA VALIDATION - GROWTH RATE PREDICTION")
    logger.info("=" * 80)

    # Check file exists
    if not CSV_FILE.exists():
        logger.error(f"File not found: {CSV_FILE}")
        logger.info("Please ensure FracFocusRegistry_13.csv is in the data/ directory")
        return

    # Load data
    logger.info(f"\nLoading: {CSV_FILE}")
    df = pd.read_csv(CSV_FILE, low_memory=False)
    logger.info(f"Total rows loaded: {len(df):,}")

    # Filter to proppant records
    if 'Purpose' in df.columns:
        df = df[df['Purpose'].str.contains('Proppant', case=False, na=False)]
        logger.info(f"Proppant records: {len(df):,}")
    else:
        logger.warning("No 'Purpose' column found - assuming all rows are proppant")

    # Filter to Atlas suppliers
    if 'Supplier' not in df.columns:
        logger.error("No 'Supplier' column found in data!")
        return

    df['Is_Atlas'] = df['Supplier'].apply(is_atlas_supplier)
    atlas_df = df[df['Is_Atlas']].copy()
    logger.info(f"Atlas records: {len(atlas_df):,}")

    if len(atlas_df) == 0:
        logger.error("No Atlas records found! Check supplier matching logic.")
        return

    # Show sample of Atlas suppliers found
    atlas_suppliers = atlas_df['Supplier'].value_counts().head(10)
    logger.info("\nTop Atlas suppliers found:")
    for supplier, count in atlas_suppliers.items():
        logger.info(f"  {supplier}: {count:,} records")

    # Parse dates
    atlas_df['JobStartDate'] = pd.to_datetime(atlas_df['JobStartDate'], errors='coerce')
    atlas_df['Year'] = atlas_df['JobStartDate'].dt.year

    # Calculate tonnage for 2022 and 2023
    logger.info("\n" + "=" * 80)
    logger.info("CALCULATING 2022 TONNAGE")
    logger.info("=" * 80)
    tonnes_2022, wells_2022, avg_2022 = calculate_annual_tonnage(atlas_df, 2022)

    logger.info("\n" + "=" * 80)
    logger.info("CALCULATING 2023 TONNAGE")
    logger.info("=" * 80)
    tonnes_2023, wells_2023, avg_2023 = calculate_annual_tonnage(atlas_df, 2023)

    # Calculate growth rates
    if tonnes_2022 == 0:
        logger.error("No 2022 data found - cannot calculate growth rate!")
        return

    tonnage_growth_pct = ((tonnes_2023 - tonnes_2022) / tonnes_2022) * 100

    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("RESULTS: GROWTH RATE COMPARISON")
    logger.info("=" * 80)

    logger.info(f"\n📊 FracFocus Data (2022 → 2023):")
    logger.info(f"  2022 tonnage: {tonnes_2022:,.0f} tonnes ({wells_2022:,} wells)")
    logger.info(f"  2023 tonnage: {tonnes_2023:,.0f} tonnes ({wells_2023:,} wells)")
    logger.info(f"  Growth: {tonnage_growth_pct:+.1f}%")

    logger.info(f"\n💰 Atlas Actual Revenue (2022 → 2023):")
    logger.info(f"  2022 product sales: ${ACTUAL_PRODUCT_SALES_2022:,.0f}")
    logger.info(f"  2023 product sales: ${ACTUAL_PRODUCT_SALES_2023:,.0f}")
    logger.info(f"  Growth: {ACTUAL_REVENUE_GROWTH_PCT:+.1f}%")

    # Compare growth rates
    growth_error = tonnage_growth_pct - ACTUAL_REVENUE_GROWTH_PCT

    logger.info(f"\n🎯 Growth Rate Prediction Accuracy:")
    logger.info(f"  FracFocus predicted: {tonnage_growth_pct:+.1f}% growth")
    logger.info(f"  Actual revenue grew: {ACTUAL_REVENUE_GROWTH_PCT:+.1f}%")
    logger.info(f"  Prediction error: {growth_error:+.1f} percentage points")

    # Interpretation
    logger.info("\n" + "=" * 80)
    logger.info("INTERPRETATION")
    logger.info("=" * 80)

    if abs(growth_error) < 3:
        logger.info("✅ EXCELLENT: FracFocus growth rate matches actual within 3pp!")
        logger.info("   This model CAN predict quarterly revenue changes!")
        logger.info("   Even if absolute tonnage is incomplete, the TREND is accurate.")
    elif abs(growth_error) < 5:
        logger.info("✅ GOOD: FracFocus growth rate matches actual within 5pp.")
        logger.info("   This model can reasonably predict revenue direction.")
    elif abs(growth_error) < 10:
        logger.info("⚠️  MODERATE: FracFocus growth rate is within 10pp of actual.")
        logger.info("   Directionally useful but significant noise.")
    else:
        logger.info("❌ POOR: FracFocus growth rate differs by >10pp from actual.")
        logger.info("   This model cannot reliably predict revenue changes.")

    # Possible explanations
    logger.info("\nPossible explanations for growth rate discrepancy:")
    if growth_error < -5:
        logger.info("  - FracFocus coverage declined 2022→2023")
        logger.info("  - More wells missing from 2023 data than 2022")
        logger.info("  - Atlas ASP increased (price growth not captured)")
    elif growth_error > 5:
        logger.info("  - FracFocus coverage improved 2022→2023")
        logger.info("  - More complete disclosure in 2023")
        logger.info("  - Atlas ASP decreased (tonnage grew faster than revenue)")
    else:
        logger.info("  - Coverage relatively consistent year-over-year")
        logger.info("  - FracFocus can serve as early indicator of demand trends")

    # Save detailed output
    output_path = Path('output') / 'validation_growth_rates.txt'
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        f.write("FRACFOCUS GROWTH RATE VALIDATION\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"2022 tonnage: {tonnes_2022:,.0f} tonnes ({wells_2022:,} wells)\n")
        f.write(f"2023 tonnage: {tonnes_2023:,.0f} tonnes ({wells_2023:,} wells)\n")
        f.write(f"FracFocus growth: {tonnage_growth_pct:+.1f}%\n\n")
        f.write(f"2022 revenue: ${ACTUAL_PRODUCT_SALES_2022:,.0f}\n")
        f.write(f"2023 revenue: ${ACTUAL_PRODUCT_SALES_2023:,.0f}\n")
        f.write(f"Actual growth: {ACTUAL_REVENUE_GROWTH_PCT:+.1f}%\n\n")
        f.write(f"Prediction error: {growth_error:+.1f} pp\n")

    logger.info(f"\nResults saved to: {output_path}")

    logger.info("\n" + "=" * 80)


if __name__ == '__main__':
    main()
