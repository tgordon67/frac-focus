"""
Atlas Energy Solutions - Revenue Prediction Model

This tool analyzes FracFocus data to track Atlas's specific volumes, market share,
and predict quarterly revenue for investment decision-making.

Key Features:
- Atlas volume tracking from FracFocus supplier data
- Market share calculation (Atlas vs total market)
- Geographic breakdown (basin/state/county)
- Revenue estimation framework
- Data completeness validation
- Backtesting capability
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import json

# Import the base analyzer
from fracfocus_analysis import FracFocusAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path('data')
OUTPUT_DIR = Path('output')
ATLAS_OUTPUT_DIR = OUTPUT_DIR / 'atlas'

# Ensure directories exist
ATLAS_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class AtlasAnalyzer(FracFocusAnalyzer):
    """
    Extended analyzer specifically for Atlas Energy Solutions tracking.
    Inherits from FracFocusAnalyzer and adds supplier-specific analysis.
    """

    def __init__(self):
        super().__init__()
        self.atlas_data = None
        self.atlas_quarterly = None

        # Atlas supplier name variations (case-insensitive matching)
        self.atlas_patterns = [
            'ATLAS SAND COMPANY',
            'ATLAS SAND CO',
            'ATLAS SAND',
            'ATLAS ENERGY',
            'ATLAS',
        ]

    # ==================== SUPPLIER NORMALIZATION ====================

    def normalize_suppliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize supplier names and flag Atlas records.

        Args:
            df: DataFrame with Supplier column

        Returns:
            DataFrame with Supplier_Clean and Is_Atlas columns added
        """
        logger.info("Normalizing supplier names...")

        # Clean supplier names
        df['Supplier_Clean'] = df['Supplier'].str.upper().str.strip()

        # Flag Atlas records
        atlas_pattern = '|'.join(self.atlas_patterns)
        df['Is_Atlas'] = df['Supplier_Clean'].str.contains(
            atlas_pattern,
            case=False,
            na=False,
            regex=True
        )

        # Log statistics
        total_records = len(df)
        supplier_available = df['Supplier'].notna().sum()
        atlas_records = df['Is_Atlas'].sum()

        logger.info(f"Total records: {total_records:,}")
        logger.info(f"Records with supplier data: {supplier_available:,} ({supplier_available/total_records*100:.1f}%)")
        logger.info(f"Atlas records identified: {atlas_records:,} ({atlas_records/total_records*100:.1f}%)")

        return df

    def validate_supplier_data_completeness(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Check what percentage of records have supplier information.

        Args:
            df: DataFrame to validate

        Returns:
            Dictionary with completeness metrics
        """
        logger.info("\n=== SUPPLIER DATA COMPLETENESS VALIDATION ===")

        metrics = {}

        # Overall completeness
        total = len(df)
        with_supplier = df['Supplier'].notna().sum()
        metrics['overall_completeness'] = with_supplier / total * 100

        # Proppant-specific completeness
        proppant_df = df[df['Purpose'].str.contains('Proppant', case=False, na=False)]
        proppant_total = len(proppant_df)
        proppant_with_supplier = proppant_df['Supplier'].notna().sum()
        metrics['proppant_completeness'] = proppant_with_supplier / proppant_total * 100 if proppant_total > 0 else 0

        # Completeness by year
        df['Year'] = pd.to_datetime(df['JobStartDate']).dt.year
        yearly_completeness = df.groupby('Year').apply(
            lambda x: x['Supplier'].notna().sum() / len(x) * 100
        )
        metrics['yearly_completeness'] = yearly_completeness.to_dict()

        # Log results
        logger.info(f"Overall completeness: {metrics['overall_completeness']:.1f}%")
        logger.info(f"Proppant records completeness: {metrics['proppant_completeness']:.1f}%")
        logger.info("\nCompleteness by year:")
        for year, pct in sorted(metrics['yearly_completeness'].items()):
            logger.info(f"  {year}: {pct:.1f}%")

        # Warning if low completeness
        if metrics['proppant_completeness'] < 80:
            logger.warning(f"⚠️  Supplier data completeness is only {metrics['proppant_completeness']:.1f}%")
            logger.warning("    Revenue predictions may be understated!")

        return metrics

    # ==================== ATLAS VOLUME TRACKING ====================

    def calculate_atlas_volumes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Atlas-specific volumes by quarter and compare to total market.

        Args:
            df: Quarterly DataFrame with Is_Atlas flag

        Returns:
            DataFrame with quarterly Atlas volumes and market share
        """
        logger.info("\n=== CALCULATING ATLAS VOLUMES ===")

        # Filter to proppant records only
        proppant_df = df[df['Purpose'].str.contains('Proppant', case=False, na=False)]

        # Atlas volumes by quarter
        atlas_quarterly = proppant_df[proppant_df['Is_Atlas']].groupby('Quarter').agg({
            'Proppant_lbs': 'sum',
            'DisclosureId': 'nunique',
            'Water_gal': 'sum'
        }).rename(columns={
            'Proppant_lbs': 'Atlas_Proppant_lbs',
            'DisclosureId': 'Atlas_Well_Count',
            'Water_gal': 'Atlas_Water_gal'
        })

        # Total market by quarter
        total_quarterly = proppant_df.groupby('Quarter').agg({
            'Proppant_lbs': 'sum',
            'DisclosureId': 'nunique',
            'Water_gal': 'sum'
        }).rename(columns={
            'Proppant_lbs': 'Total_Proppant_lbs',
            'DisclosureId': 'Total_Well_Count',
            'Water_gal': 'Total_Water_gal'
        })

        # Merge
        result = atlas_quarterly.join(total_quarterly, how='outer')
        result = result.fillna(0)

        # Calculate market share
        result['Atlas_Market_Share_Pct'] = (
            result['Atlas_Proppant_lbs'] / result['Total_Proppant_lbs'] * 100
        ).round(2)

        # Convert to millions for readability
        result['Atlas_Proppant_MM_lbs'] = result['Atlas_Proppant_lbs'] / 1_000_000
        result['Total_Proppant_MM_lbs'] = result['Total_Proppant_lbs'] / 1_000_000
        result['Atlas_Water_MM_gal'] = result['Atlas_Water_gal'] / 1_000_000

        # Calculate average per well
        result['Atlas_Avg_Proppant_per_Well_lbs'] = (
            result['Atlas_Proppant_lbs'] / result['Atlas_Well_Count']
        ).replace([np.inf, -np.inf], 0)

        # Sort by quarter
        result = result.sort_index()

        # Log summary
        logger.info(f"Quarters analyzed: {len(result)}")
        logger.info(f"Average Atlas market share: {result['Atlas_Market_Share_Pct'].mean():.2f}%")
        logger.info(f"Total Atlas volume (all time): {result['Atlas_Proppant_MM_lbs'].sum():,.0f} MM lbs")
        logger.info(f"Total market volume (all time): {result['Total_Proppant_MM_lbs'].sum():,.0f} MM lbs")

        self.atlas_quarterly = result
        return result.reset_index()

    def calculate_atlas_by_basin(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Atlas volumes broken down by basin.

        Args:
            df: Quarterly DataFrame with Is_Atlas flag and Basin column

        Returns:
            DataFrame with quarterly Atlas volumes by basin
        """
        logger.info("\n=== CALCULATING ATLAS VOLUMES BY BASIN ===")

        # Filter to Atlas proppant records
        atlas_proppant = df[
            (df['Is_Atlas']) &
            (df['Purpose'].str.contains('Proppant', case=False, na=False))
        ]

        # Group by quarter and basin
        atlas_basin = atlas_proppant.groupby(['Quarter', 'Basin']).agg({
            'Proppant_lbs': 'sum',
            'DisclosureId': 'nunique',
            'Water_gal': 'sum'
        }).rename(columns={
            'Proppant_lbs': 'Atlas_Proppant_lbs',
            'DisclosureId': 'Atlas_Well_Count',
            'Water_gal': 'Atlas_Water_gal'
        })

        # Total market by quarter and basin
        total_basin = df[
            df['Purpose'].str.contains('Proppant', case=False, na=False)
        ].groupby(['Quarter', 'Basin']).agg({
            'Proppant_lbs': 'sum',
            'DisclosureId': 'nunique'
        }).rename(columns={
            'Proppant_lbs': 'Total_Proppant_lbs',
            'DisclosureId': 'Total_Well_Count'
        })

        # Merge
        result = atlas_basin.join(total_basin)

        # Calculate market share by basin
        result['Atlas_Market_Share_Pct'] = (
            result['Atlas_Proppant_lbs'] / result['Total_Proppant_lbs'] * 100
        ).round(2)

        # Convert to millions
        result['Atlas_Proppant_MM_lbs'] = result['Atlas_Proppant_lbs'] / 1_000_000
        result['Total_Proppant_MM_lbs'] = result['Total_Proppant_lbs'] / 1_000_000

        # Sort and clean
        result = result.sort_index()

        # Log basin breakdown
        logger.info("\nAtlas volume by basin (all time):")
        basin_totals = result.groupby(level='Basin')['Atlas_Proppant_MM_lbs'].sum().sort_values(ascending=False)
        for basin, volume in basin_totals.items():
            pct = volume / basin_totals.sum() * 100
            logger.info(f"  {basin}: {volume:,.0f} MM lbs ({pct:.1f}%)")

        return result.reset_index()

    def calculate_atlas_by_county(self, df: pd.DataFrame, basin_filter: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate Atlas volumes by county (optionally filtered to specific basin).

        Args:
            df: Quarterly DataFrame with Is_Atlas flag
            basin_filter: Optional basin name to filter (e.g., 'Permian Basin')

        Returns:
            DataFrame with quarterly Atlas volumes by county
        """
        logger.info(f"\n=== CALCULATING ATLAS VOLUMES BY COUNTY{' ('+basin_filter+')' if basin_filter else ''} ===")

        # Apply basin filter if specified
        if basin_filter:
            df = df[df['Basin'] == basin_filter]

        # Filter to Atlas proppant records
        atlas_proppant = df[
            (df['Is_Atlas']) &
            (df['Purpose'].str.contains('Proppant', case=False, na=False))
        ]

        # Group by quarter, state, and county
        atlas_county = atlas_proppant.groupby(['Quarter', 'StateName', 'CountyName']).agg({
            'Proppant_lbs': 'sum',
            'DisclosureId': 'nunique'
        }).rename(columns={
            'Proppant_lbs': 'Atlas_Proppant_lbs',
            'DisclosureId': 'Atlas_Well_Count'
        })

        # Total market by county
        total_county = df[
            df['Purpose'].str.contains('Proppant', case=False, na=False)
        ].groupby(['Quarter', 'StateName', 'CountyName']).agg({
            'Proppant_lbs': 'sum',
            'DisclosureId': 'nunique'
        }).rename(columns={
            'Proppant_lbs': 'Total_Proppant_lbs',
            'DisclosureId': 'Total_Well_Count'
        })

        # Merge
        result = atlas_county.join(total_county)

        # Calculate market share
        result['Atlas_Market_Share_Pct'] = (
            result['Atlas_Proppant_lbs'] / result['Total_Proppant_lbs'] * 100
        ).round(2)

        # Convert to millions
        result['Atlas_Proppant_MM_lbs'] = result['Atlas_Proppant_lbs'] / 1_000_000

        result = result.sort_index()

        # Log top counties
        logger.info("\nTop 10 counties by Atlas volume (all time):")
        county_totals = result.groupby(level=['StateName', 'CountyName'])['Atlas_Proppant_MM_lbs'].sum()
        county_totals = county_totals.sort_values(ascending=False).head(10)
        for (state, county), volume in county_totals.items():
            logger.info(f"  {county}, {state}: {volume:,.0f} MM lbs")

        return result.reset_index()

    # ==================== REVENUE ESTIMATION ====================

    def estimate_revenue(self, df_volumes: pd.DataFrame,
                         price_per_ton: float = 60.0,
                         contract_pct: float = 0.80,
                         spot_price_adjustment: float = 1.0) -> pd.DataFrame:
        """
        Estimate Atlas's quarterly revenue based on volumes and pricing assumptions.

        Args:
            df_volumes: DataFrame with Atlas_Proppant_lbs column
            price_per_ton: Base price per ton (default $60)
            contract_pct: Percentage of volume under contract (default 80%)
            spot_price_adjustment: Multiplier for spot pricing vs contract (default 1.0 = same)

        Returns:
            DataFrame with revenue estimates added
        """
        logger.info("\n=== ESTIMATING ATLAS REVENUE ===")
        logger.info(f"Pricing assumptions:")
        logger.info(f"  Contract price: ${price_per_ton:.2f}/ton ({contract_pct*100:.0f}% of volume)")
        logger.info(f"  Spot price: ${price_per_ton * spot_price_adjustment:.2f}/ton ({(1-contract_pct)*100:.0f}% of volume)")

        df = df_volumes.copy()

        # Convert lbs to tons (2000 lbs per ton)
        df['Atlas_Proppant_tons'] = df['Atlas_Proppant_lbs'] / 2000

        # Split into contract and spot volume
        df['Atlas_Contract_tons'] = df['Atlas_Proppant_tons'] * contract_pct
        df['Atlas_Spot_tons'] = df['Atlas_Proppant_tons'] * (1 - contract_pct)

        # Calculate revenue components
        df['Contract_Revenue_MM'] = (df['Atlas_Contract_tons'] * price_per_ton) / 1_000_000
        df['Spot_Revenue_MM'] = (df['Atlas_Spot_tons'] * price_per_ton * spot_price_adjustment) / 1_000_000
        df['Total_Revenue_Estimate_MM'] = df['Contract_Revenue_MM'] + df['Spot_Revenue_MM']

        # Calculate average price per ton (blended)
        df['Blended_Price_per_ton'] = (
            (contract_pct * price_per_ton) +
            ((1 - contract_pct) * price_per_ton * spot_price_adjustment)
        )

        # Log summary
        logger.info(f"\nRevenue estimates (all time):")
        logger.info(f"  Total estimated revenue: ${df['Total_Revenue_Estimate_MM'].sum():,.1f}M")
        logger.info(f"  Average quarterly revenue: ${df['Total_Revenue_Estimate_MM'].mean():,.1f}M")
        logger.info(f"  Contract revenue: ${df['Contract_Revenue_MM'].sum():,.1f}M")
        logger.info(f"  Spot revenue: ${df['Spot_Revenue_MM'].sum():,.1f}M")

        return df

    def backsolve_pricing(self, df_volumes: pd.DataFrame,
                          reported_revenues: Dict[str, float]) -> pd.DataFrame:
        """
        Back-calculate implied pricing from reported revenues.

        Args:
            df_volumes: DataFrame with Atlas_Proppant_lbs column
            reported_revenues: Dictionary of {Quarter: Revenue_in_millions}
                              Example: {'2023Q1': 425.5, '2023Q2': 450.2}

        Returns:
            DataFrame with implied pricing added
        """
        logger.info("\n=== BACKSOLVING PRICING FROM REPORTED REVENUES ===")

        df = df_volumes.copy()

        # Convert to tons
        df['Atlas_Proppant_tons'] = df['Atlas_Proppant_lbs'] / 2000

        # Add reported revenues
        df['Reported_Revenue_MM'] = df['Quarter'].map(reported_revenues)

        # Calculate implied price per ton
        df['Implied_Price_per_ton'] = (
            (df['Reported_Revenue_MM'] * 1_000_000) / df['Atlas_Proppant_tons']
        ).round(2)

        # Filter to quarters with reported data
        with_pricing = df[df['Reported_Revenue_MM'].notna()]

        if len(with_pricing) > 0:
            avg_price = with_pricing['Implied_Price_per_ton'].mean()
            std_price = with_pricing['Implied_Price_per_ton'].std()

            logger.info(f"Implied pricing statistics ({len(with_pricing)} quarters):")
            logger.info(f"  Average price: ${avg_price:.2f}/ton")
            logger.info(f"  Std deviation: ${std_price:.2f}/ton")
            logger.info(f"  Price range: ${with_pricing['Implied_Price_per_ton'].min():.2f} - ${with_pricing['Implied_Price_per_ton'].max():.2f}/ton")

            # Price volatility
            volatility = (std_price / avg_price * 100) if avg_price > 0 else 0
            logger.info(f"  Price volatility: {volatility:.1f}%")

            if volatility < 15:
                logger.info("  ✅ Pricing is relatively stable")
            else:
                logger.warning("  ⚠️  High price volatility detected")
        else:
            logger.warning("  ⚠️  No reported revenue data provided for pricing calculation")

        return df

    # ==================== VALIDATION & TESTING ====================

    def validate_volume_accuracy(self, df_volumes: pd.DataFrame,
                                  reported_volumes: Dict[str, float]) -> pd.DataFrame:
        """
        Compare our calculated volumes to Atlas's reported volumes.

        Args:
            df_volumes: DataFrame with Atlas_Proppant_lbs column
            reported_volumes: Dictionary of {Quarter: Volume_in_lbs}
                             Example: {'2023Q1': 6_400_000_000}

        Returns:
            DataFrame with validation metrics
        """
        logger.info("\n=== VALIDATING VOLUME ACCURACY ===")

        df = df_volumes.copy()

        # Add reported volumes
        df['Reported_Volume_lbs'] = df['Quarter'].map(reported_volumes)

        # Calculate error
        df['Volume_Error_lbs'] = df['Atlas_Proppant_lbs'] - df['Reported_Volume_lbs']
        df['Volume_Error_Pct'] = (
            df['Volume_Error_lbs'] / df['Reported_Volume_lbs'] * 100
        ).round(2)

        # Filter to quarters with reported data
        with_validation = df[df['Reported_Volume_lbs'].notna()]

        if len(with_validation) > 0:
            avg_error = with_validation['Volume_Error_Pct'].abs().mean()

            logger.info(f"Volume validation results ({len(with_validation)} quarters):")
            logger.info(f"  Average absolute error: {avg_error:.1f}%")

            # Show quarter-by-quarter
            logger.info("\n  Quarter-by-quarter comparison:")
            for _, row in with_validation.iterrows():
                logger.info(f"    {row['Quarter']}: "
                          f"Calculated: {row['Atlas_Proppant_lbs']:,.0f} lbs | "
                          f"Reported: {row['Reported_Volume_lbs']:,.0f} lbs | "
                          f"Error: {row['Volume_Error_Pct']:+.1f}%")

            if avg_error < 10:
                logger.info("  ✅ Volume tracking is highly accurate (<10% error)")
            elif avg_error < 20:
                logger.warning("  🟡 Volume tracking has moderate accuracy (10-20% error)")
            else:
                logger.warning("  ⚠️  Volume tracking has high error (>20% error)")
                logger.warning("     This may indicate data completeness issues")
        else:
            logger.warning("  ⚠️  No reported volume data provided for validation")

        return df

    def test_early_quarter_prediction(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Test if first 2 months of data can predict full quarter volumes.

        Args:
            df: Full DataFrame with JobStartDate

        Returns:
            DataFrame with prediction test results
        """
        logger.info("\n=== TESTING EARLY-QUARTER PREDICTION POWER ===")

        # Filter to Atlas proppant
        atlas_df = df[
            (df['Is_Atlas']) &
            (df['Purpose'].str.contains('Proppant', case=False, na=False))
        ]

        # Get unique quarters
        quarters = atlas_df['Quarter'].unique()

        results = []

        for quarter in quarters:
            quarter_data = atlas_df[atlas_df['Quarter'] == quarter]

            # Parse quarter to get first 2 months
            # Q1 = Jan, Feb; Q2 = Apr, May; Q3 = Jul, Aug; Q4 = Oct, Nov
            quarter_num = int(quarter[-1])
            year = int(quarter[:4])

            if quarter_num == 1:
                early_months = [1, 2]
            elif quarter_num == 2:
                early_months = [4, 5]
            elif quarter_num == 3:
                early_months = [7, 8]
            else:  # Q4
                early_months = [10, 11]

            # Filter to early months
            early_data = quarter_data[
                pd.to_datetime(quarter_data['JobStartDate']).dt.month.isin(early_months)
            ]

            early_volume = early_data['Proppant_lbs'].sum()
            full_volume = quarter_data['Proppant_lbs'].sum()

            # Simple prediction: Full quarter = Early volume × 1.5
            predicted_volume = early_volume * 1.5
            error = abs(predicted_volume - full_volume) / full_volume * 100 if full_volume > 0 else 0

            results.append({
                'Quarter': quarter,
                'Early_Volume_MM_lbs': early_volume / 1_000_000,
                'Full_Volume_MM_lbs': full_volume / 1_000_000,
                'Predicted_Volume_MM_lbs': predicted_volume / 1_000_000,
                'Prediction_Error_Pct': error
            })

        results_df = pd.DataFrame(results).sort_values('Quarter')

        # Calculate average error
        avg_error = results_df['Prediction_Error_Pct'].mean()

        logger.info(f"Early-quarter prediction test ({len(results_df)} quarters):")
        logger.info(f"  Average prediction error: {avg_error:.1f}%")

        if avg_error < 15:
            logger.info("  ✅ Early data is highly predictive (<15% error)")
            logger.info("     You can make predictions with just 2 months of data!")
        elif avg_error < 25:
            logger.warning("  🟡 Early data has moderate predictive power (15-25% error)")
        else:
            logger.warning("  ⚠️  Early data has low predictive power (>25% error)")
            logger.warning("     Need full quarter data for accurate predictions")

        # Show recent quarters
        logger.info("\n  Recent quarters:")
        for _, row in results_df.tail(4).iterrows():
            logger.info(f"    {row['Quarter']}: "
                      f"Early: {row['Early_Volume_MM_lbs']:.0f} MM lbs | "
                      f"Predicted: {row['Predicted_Volume_MM_lbs']:.0f} MM lbs | "
                      f"Actual: {row['Full_Volume_MM_lbs']:.0f} MM lbs | "
                      f"Error: {row['Prediction_Error_Pct']:.1f}%")

        return results_df

    # ==================== REPORTING ====================

    def generate_atlas_summary_report(self, output_path: Path) -> None:
        """
        Generate a comprehensive text report summarizing Atlas analysis.

        Args:
            output_path: Path to save the report
        """
        logger.info(f"\n=== GENERATING ATLAS SUMMARY REPORT ===")

        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("ATLAS ENERGY SOLUTIONS - MARKET ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            if self.atlas_quarterly is not None:
                f.write("QUARTERLY VOLUMES & MARKET SHARE\n")
                f.write("-" * 80 + "\n")

                # Recent quarters
                recent = self.atlas_quarterly.tail(8)
                f.write("\nRecent 8 Quarters:\n")
                f.write(f"{'Quarter':<12} {'Atlas Vol (MM lbs)':<20} {'Market Share':<15} {'Wells':<10}\n")
                f.write("-" * 80 + "\n")

                for quarter, row in recent.iterrows():
                    f.write(f"{str(quarter):<12} "
                          f"{row['Atlas_Proppant_MM_lbs']:>15,.0f}     "
                          f"{row['Atlas_Market_Share_Pct']:>10,.1f}%    "
                          f"{row['Atlas_Well_Count']:>7,.0f}\n")

                # Summary statistics
                f.write("\n\nSUMMARY STATISTICS\n")
                f.write("-" * 80 + "\n")
                f.write(f"Total quarters analyzed: {len(self.atlas_quarterly)}\n")
                f.write(f"Average market share: {self.atlas_quarterly['Atlas_Market_Share_Pct'].mean():.2f}%\n")
                f.write(f"Market share trend: {self.atlas_quarterly['Atlas_Market_Share_Pct'].iloc[-4:].mean():.2f}% (last 4 quarters)\n")
                f.write(f"Total Atlas volume (all time): {self.atlas_quarterly['Atlas_Proppant_MM_lbs'].sum():,.0f} MM lbs\n")
                f.write(f"Average quarterly volume: {self.atlas_quarterly['Atlas_Proppant_MM_lbs'].mean():,.0f} MM lbs\n")

                # Growth metrics
                if len(self.atlas_quarterly) >= 4:
                    recent_avg = self.atlas_quarterly['Atlas_Proppant_MM_lbs'].iloc[-4:].mean()
                    prior_avg = self.atlas_quarterly['Atlas_Proppant_MM_lbs'].iloc[-8:-4].mean() if len(self.atlas_quarterly) >= 8 else 0
                    growth = ((recent_avg - prior_avg) / prior_avg * 100) if prior_avg > 0 else 0
                    f.write(f"Volume growth (recent 4Q vs prior 4Q): {growth:+.1f}%\n")

            f.write("\n\n" + "=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")

        logger.info(f"Report saved to: {output_path}")


def main():
    """Main execution function for Atlas analysis"""
    logger.info("=" * 80)
    logger.info("ATLAS ENERGY SOLUTIONS - REVENUE PREDICTION MODEL")
    logger.info("=" * 80)

    # Initialize analyzer
    analyzer = AtlasAnalyzer()

    # Phase 1: Load base FracFocus data
    logger.info("\n=== PHASE 1: LOADING FRACFOCUS DATA ===")
    try:
        df = analyzer.load_consolidated_data()
    except FileNotFoundError:
        logger.error("Consolidated data not found. Please run fracfocus_analysis.py first.")
        return

    # Phase 2: Clean data
    logger.info("\n=== PHASE 2: CLEANING DATA ===")
    df_clean = analyzer.clean_data(df)

    # Phase 3: Calculate proppant
    logger.info("\n=== PHASE 3: CALCULATING PROPPANT ===")
    df_with_proppant = analyzer.add_proppant_calculations(df_clean)

    # Phase 4: Normalize suppliers (NEW!)
    logger.info("\n=== PHASE 4: NORMALIZING SUPPLIERS ===")
    df_with_proppant = analyzer.normalize_suppliers(df_with_proppant)

    # Validate supplier data completeness
    completeness_metrics = analyzer.validate_supplier_data_completeness(df_with_proppant)

    # Phase 5: Quarterly attribution
    logger.info("\n=== PHASE 5: QUARTERLY ATTRIBUTION ===")
    df_quarterly = analyzer.attribute_to_quarters(df_with_proppant)

    # Phase 6: Regional classification
    logger.info("\n=== PHASE 6: REGIONAL CLASSIFICATION ===")
    df_quarterly = analyzer.add_regional_classifications(df_quarterly)

    # ATLAS-SPECIFIC ANALYSIS STARTS HERE

    # Phase 7: Calculate Atlas volumes
    logger.info("\n=== PHASE 7: ATLAS VOLUME ANALYSIS ===")
    atlas_quarterly = analyzer.calculate_atlas_volumes(df_quarterly)

    # Phase 8: Atlas by basin
    logger.info("\n=== PHASE 8: ATLAS BASIN BREAKDOWN ===")
    atlas_by_basin = analyzer.calculate_atlas_by_basin(df_quarterly)

    # Phase 9: Atlas by county (Permian focus)
    logger.info("\n=== PHASE 9: ATLAS COUNTY BREAKDOWN ===")
    atlas_permian_counties = analyzer.calculate_atlas_by_county(df_quarterly, basin_filter='Permian Basin')
    atlas_all_counties = analyzer.calculate_atlas_by_county(df_quarterly)

    # Phase 10: Revenue estimation
    logger.info("\n=== PHASE 10: REVENUE ESTIMATION ===")

    # Default pricing assumptions (user can modify these)
    DEFAULT_PRICE_PER_TON = 60.0
    DEFAULT_CONTRACT_PCT = 0.80
    DEFAULT_SPOT_ADJUSTMENT = 1.0

    atlas_with_revenue = analyzer.estimate_revenue(
        atlas_quarterly,
        price_per_ton=DEFAULT_PRICE_PER_TON,
        contract_pct=DEFAULT_CONTRACT_PCT,
        spot_price_adjustment=DEFAULT_SPOT_ADJUSTMENT
    )

    # Phase 11: Backtesting (if you have reported data)
    logger.info("\n=== PHASE 11: VALIDATION & BACKTESTING ===")

    # Example: Add your Atlas reported revenues here
    # Format: {'Quarter': Revenue_in_millions}
    reported_revenues = {
        # '2023Q1': 425.5,
        # '2023Q2': 450.2,
        # '2023Q3': 475.8,
        # '2023Q4': 490.3,
    }

    if reported_revenues:
        atlas_with_pricing = analyzer.backsolve_pricing(atlas_quarterly, reported_revenues)

        # Validate volume accuracy (if you have reported volumes)
        reported_volumes = {
            # '2023Q1': 6_400_000_000,  # lbs
        }

        if reported_volumes:
            validation_df = analyzer.validate_volume_accuracy(atlas_quarterly, reported_volumes)

    # Test early-quarter prediction
    prediction_test = analyzer.test_early_quarter_prediction(df_quarterly)

    # Save all outputs
    logger.info("\n=== SAVING OUTPUTS ===")

    output_files = {
        'atlas_quarterly_volumes.csv': atlas_with_revenue,
        'atlas_by_basin.csv': atlas_by_basin,
        'atlas_permian_counties.csv': atlas_permian_counties,
        'atlas_all_counties.csv': atlas_all_counties,
        'atlas_prediction_test.csv': prediction_test,
        'supplier_completeness_metrics.json': json.dumps(completeness_metrics, indent=2)
    }

    for filename, data in output_files.items():
        output_path = ATLAS_OUTPUT_DIR / filename
        if filename.endswith('.json'):
            with open(output_path, 'w') as f:
                f.write(data)
            logger.info(f"Saved {filename}")
        else:
            logger.info(f"Saving {filename} ({len(data):,} rows)")
            data.to_csv(output_path, index=False)

    # Generate summary report
    report_path = ATLAS_OUTPUT_DIR / 'atlas_summary_report.txt'
    analyzer.generate_atlas_summary_report(report_path)

    # Display key insights
    logger.info("\n" + "=" * 80)
    logger.info("KEY INSIGHTS")
    logger.info("=" * 80)

    if len(atlas_with_revenue) > 0:
        latest_quarter = atlas_with_revenue.iloc[-1]
        logger.info(f"\nLatest Quarter: {latest_quarter['Quarter']}")
        logger.info(f"  Atlas Volume: {latest_quarter['Atlas_Proppant_MM_lbs']:,.0f} MM lbs")
        logger.info(f"  Market Share: {latest_quarter['Atlas_Market_Share_Pct']:.2f}%")
        logger.info(f"  Est. Revenue: ${latest_quarter['Total_Revenue_Estimate_MM']:.1f}M")
        logger.info(f"  Well Count: {latest_quarter['Atlas_Well_Count']:,.0f}")

        # Growth trends
        if len(atlas_with_revenue) >= 4:
            recent_4q_avg = atlas_with_revenue['Atlas_Proppant_MM_lbs'].iloc[-4:].mean()
            prior_4q_avg = atlas_with_revenue['Atlas_Proppant_MM_lbs'].iloc[-8:-4].mean() if len(atlas_with_revenue) >= 8 else 0

            if prior_4q_avg > 0:
                growth = (recent_4q_avg - prior_4q_avg) / prior_4q_avg * 100
                logger.info(f"\n4-Quarter Growth Trend: {growth:+.1f}%")

    logger.info("\n" + "=" * 80)
    logger.info("ANALYSIS COMPLETE")
    logger.info("=" * 80)
    logger.info(f"All Atlas outputs saved to: {ATLAS_OUTPUT_DIR.absolute()}")
    logger.info("\nNext steps:")
    logger.info("1. Review atlas_quarterly_volumes.csv for quarterly trends")
    logger.info("2. Add reported revenues/volumes to validate model accuracy")
    logger.info("3. Adjust pricing assumptions in estimate_revenue() if needed")
    logger.info("4. Use atlas_prediction_test.csv to assess early-quarter predictive power")


if __name__ == '__main__':
    main()
