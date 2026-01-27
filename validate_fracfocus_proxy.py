"""
Validate FracFocus Data as Proxy for Atlas Revenue

Compares FracFocus-derived tonnage to Atlas's actual 2023 product sales
to determine if this approach is viable.

Atlas 2023 Actual (from 10-K):
- Product sales: $468,119,000
- Expected price: ~$28/ton
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
ACTUAL_PRODUCT_SALES_2023 = 468_119_000  # $ (from 10-K)
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


def main():
    """Main validation logic"""
    logger.info("=" * 80)
    logger.info("FRACFOCUS DATA VALIDATION - ATLAS 2023 REVENUE PROXY")
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

    # Filter to 2023
    atlas_2023 = atlas_df[atlas_df['Year'] == 2023].copy()
    logger.info(f"\nAtlas 2023 records: {len(atlas_2023):,}")

    if len(atlas_2023) == 0:
        logger.error("No 2023 Atlas records found!")
        return

    # Deduplicate by DisclosureId (keep first occurrence)
    initial_count = len(atlas_2023)
    atlas_2023 = atlas_2023.drop_duplicates(subset=['DisclosureId'], keep='first')
    logger.info(f"After deduplication: {len(atlas_2023):,} unique disclosures")
    logger.info(f"Removed {initial_count - len(atlas_2023):,} duplicate records")

    # Calculate proppant mass for each disclosure
    logger.info("\nCalculating proppant mass...")
    atlas_2023['Proppant_Mass_Lbs'] = atlas_2023.apply(calculate_proppant_mass, axis=1)

    # Remove records with zero mass
    valid_records = atlas_2023[atlas_2023['Proppant_Mass_Lbs'] > 0]
    logger.info(f"Valid mass calculations: {len(valid_records):,}")
    logger.info(f"Records with zero mass: {len(atlas_2023) - len(valid_records):,}")

    # Convert to tonnes
    valid_records['Proppant_Tonnes'] = valid_records['Proppant_Mass_Lbs'] / LBS_PER_TON

    # Calculate totals
    total_tonnes = valid_records['Proppant_Tonnes'].sum()
    implied_revenue = total_tonnes * PRICE_PER_TON

    # Calculate accuracy
    revenue_delta = implied_revenue - ACTUAL_PRODUCT_SALES_2023
    revenue_pct_error = (revenue_delta / ACTUAL_PRODUCT_SALES_2023) * 100

    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    logger.info(f"\nFracFocus 2023 Data:")
    logger.info(f"  Total tonnage: {total_tonnes:,.0f} tonnes")
    logger.info(f"  Implied revenue (@${PRICE_PER_TON}/ton): ${implied_revenue:,.0f}")

    logger.info(f"\nAtlas 2023 Actual (10-K):")
    logger.info(f"  Product sales: ${ACTUAL_PRODUCT_SALES_2023:,.0f}")

    logger.info(f"\nComparison:")
    logger.info(f"  Delta: ${revenue_delta:+,.0f}")
    logger.info(f"  Error: {revenue_pct_error:+.1f}%")

    # Interpretation
    logger.info("\n" + "=" * 80)
    logger.info("INTERPRETATION")
    logger.info("=" * 80)

    if abs(revenue_pct_error) < 10:
        logger.info("✅ EXCELLENT: FracFocus data is within 10% of actual revenue!")
        logger.info("   This approach is highly viable as a revenue proxy.")
    elif abs(revenue_pct_error) < 25:
        logger.info("⚠️  MODERATE: FracFocus data is within 25% of actual revenue.")
        logger.info("   This approach may be useful but needs refinement.")
    elif abs(revenue_pct_error) < 50:
        logger.info("⚠️  POOR: FracFocus data is 25-50% off from actual revenue.")
        logger.info("   Significant issues with data completeness or methodology.")
    else:
        logger.info("❌ FAILED: FracFocus data is >50% off from actual revenue.")
        logger.info("   This approach is not viable without major corrections.")

    # Possible explanations for error
    logger.info("\nPossible explanations for discrepancy:")
    if revenue_pct_error < -25:
        logger.info("  - FracFocus data is incomplete (not all jobs reported)")
        logger.info("  - Timing lag (2023 shipments reported in 2024)")
        logger.info("  - Price assumption too low (actual ASP > $28/ton)")
    elif revenue_pct_error > 25:
        logger.info("  - Duplicate records not fully removed")
        logger.info("  - Non-Atlas suppliers incorrectly matched")
        logger.info("  - Price assumption too high (actual ASP < $28/ton)")
    else:
        logger.info("  - Data quality is reasonable")
        logger.info("  - Minor timing lags or pricing variations")

    # Save detailed output
    output_path = Path('output') / 'validation_results_2023.csv'
    output_path.parent.mkdir(exist_ok=True)

    valid_records[['DisclosureId', 'JobStartDate', 'Supplier',
                   'Proppant_Mass_Lbs', 'Proppant_Tonnes']].to_csv(output_path, index=False)
    logger.info(f"\nDetailed results saved to: {output_path}")

    logger.info("\n" + "=" * 80)


if __name__ == '__main__':
    main()
