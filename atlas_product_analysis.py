"""
Atlas Energy Solutions - Product-Level Volume Analysis

Processes FracFocus data to track Atlas's specific product volumes over time.

Based on:
- Atlas 10-K Exhibit 21.1 (subsidiary list)
- Validated product list (what Atlas actually produces)

Output: Time series of Atlas volumes by product type
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Set
import logging
from datetime import datetime
import glob

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path('data')
OUTPUT_DIR = Path('output') / 'atlas'

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class AtlasProductAnalyzer:
    """
    Analyzer for Atlas-specific product volumes.
    """

    def __init__(self):
        # Atlas supplier name variations (from 10-K Exhibit 21.1)
        self.atlas_supplier_patterns = [
            'ATLAS ENERGY SOLUTIONS',
            'ATLAS SAND COMPANY',
            'ATLAS SAND CO',
            'ATLAS SAND OPERATING',
            'ATLAS SAND',
            'AESI HOLDINGS',
            'OLC KERMIT',
            'OLC MONAHANS',
            'FOUNTAINHEAD LOGISTICS',
            # Legacy/brand names
            'CAPITAL SAND',  # Legacy brand
        ]

        # Products Atlas DEFINITELY produces (from your list)
        self.atlas_products_definite = {
            # Primary mesh sizes
            '40/70', '100', '100M', '100 MESH',
            '40/140 BROWN DRY', '40/140 BROWN DAMP',
            '100 MESH PROPPANT', 'SAND (100 MESH PROPPANT)', 'SAND (40/70 PROPPANT)',
            '40/70 MESH',
            # Permian-specific
            'SAND, PERMIAN 40/140', '100 MESH PERMIAN',
            'SAND-LOCAL, 100M', 'SAND-LOCAL, 40/70',
            'WEST TX 100 MESH', 'WEST TX 40/70',
            'CAPITAL SAND 40/140',
            # Regional identifiers
            'SAND - REGIONAL', '40/70 REGIONAL', '100 MESH REGIONAL SAND',
            'SAND, COMMON BROWN 100 MESH',
            'SAND, SAN ANTONIO, 40/70', 'SAND, SAN ANTONIO - 100M',
            # Generic (but Atlas does produce these)
            'SAND', 'SILICA SAND', 'SAND (PROPPANT)',
            'CRYSTALLINE SILICA QUARTZ',
            # Ambiguous but likely Atlas
            'SAND,NATIVE,100 MESH', 'SAND (40/140 PROPPANT)',
        }

        # Products Atlas DOES NOT produce (exclusion list)
        self.atlas_products_exclude = {
            # Northern White Sand
            'SAND-COMMON WHITE-100 MESH', 'SAND-PREMIUM WHITE-40/70', 'SAND-PREMIUM WHITE-30/50',
            'SAND-COMMON WHITE, 100M', 'SAND-COMMON WHITE 40/70',
            '100 MESH WESTERN', '100 MESH POWDER RIVER',
            # Resin-coated
            'GARNET', 'PEARL', 'CHROME', 'RESIN COATED PROPPANT',
            'SAND-CRC-40/70', 'CRC',
            # Ceramic
            'CARBOLITE', 'CERAMIC PROPPANT', 'DEEPROP',
            # Specialty
            'NANOMITE', 'MP-D1', 'S901',
            # Non-proppant
            'PETCOKE', 'PETROLEUM COKE', 'SURFACTANT',
        }

    def normalize_supplier_name(self, supplier: str) -> str:
        """
        Normalize supplier name for matching.

        Args:
            supplier: Raw supplier string

        Returns:
            Normalized supplier string
        """
        if pd.isna(supplier):
            return ''

        # Convert to uppercase and strip
        normalized = str(supplier).upper().strip()

        # Remove common suffixes
        normalized = normalized.replace(' LLC', '').replace(' INC', '').replace(' L.L.C.', '')
        normalized = normalized.replace(',', '').replace('.', '')

        return normalized

    def is_atlas_supplier(self, supplier: str) -> bool:
        """
        Check if supplier is an Atlas entity.
        Permissive matching: accepts anything with "ATLAS" in the name.

        Args:
            supplier: Supplier name

        Returns:
            True if Atlas entity
        """
        normalized = self.normalize_supplier_name(supplier)

        if not normalized:
            return False

        # Accept anything with "ATLAS" substring
        return 'ATLAS' in normalized

    def normalize_product_name(self, tradename: str) -> str:
        """
        Normalize product/tradename for matching.

        Args:
            tradename: Raw TradeName string

        Returns:
            Normalized product string
        """
        if pd.isna(tradename):
            return ''

        # Convert to uppercase and strip
        normalized = str(tradename).upper().strip()

        # Remove common prefixes that don't add meaning
        normalized = normalized.replace('SAND (', '').replace(')', '')
        normalized = normalized.replace('SAND - ', '')

        return normalized

    def is_atlas_product(self, tradename: str) -> bool:
        """
        Check if product is something Atlas produces.

        Args:
            tradename: Product/TradeName

        Returns:
            True if Atlas product, False if excluded or unknown
        """
        normalized = self.normalize_product_name(tradename)

        if not normalized:
            return False

        # Check exclusions first (more specific)
        for exclude_pattern in self.atlas_products_exclude:
            if exclude_pattern.upper() in normalized:
                return False

        # Check if it's a known Atlas product
        for product_pattern in self.atlas_products_definite:
            if product_pattern.upper() in normalized:
                return True

        # If contains "WHITE" (and not in definite list), exclude
        if 'WHITE' in normalized and 'COMMON WHITE' not in self.atlas_products_definite:
            return False

        # If contains "RESIN" or "CERAMIC", exclude
        if any(x in normalized for x in ['RESIN', 'CERAMIC', 'CARBO']):
            return False

        return False

    def standardize_product_category(self, tradename: str) -> str:
        """
        Standardize product names into categories.

        Args:
            tradename: Raw TradeName

        Returns:
            Standardized product category
        """
        normalized = self.normalize_product_name(tradename)

        # Map to standard categories
        if '40/70' in normalized:
            return '40/70 Mesh'
        elif '100' in normalized or '100M' in normalized:
            return '100 Mesh'
        elif '40/140' in normalized:
            return '40/140 Mesh'
        elif 'SAND' in normalized and 'MESH' not in normalized:
            return 'Sand (Unspecified)'
        else:
            return 'Other Regional Sand'

    def process_registry_file(self, file_path: Path) -> pd.DataFrame:
        """
        Process a single FracFocus Registry CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            Filtered DataFrame with Atlas records only
        """
        logger.info(f"Processing {file_path.name}...")

        try:
            # Read CSV
            df = pd.read_csv(file_path, low_memory=False)

            initial_count = len(df)
            logger.info(f"  Loaded {initial_count:,} rows")

            # Filter to proppant records
            if 'Purpose' in df.columns:
                df = df[df['Purpose'].str.contains('Proppant', case=False, na=False)]
                logger.info(f"  Proppant records: {len(df):,}")

            # Filter to Atlas suppliers
            if 'Supplier' in df.columns:
                df['Is_Atlas'] = df['Supplier'].apply(self.is_atlas_supplier)
                df = df[df['Is_Atlas']]
                logger.info(f"  Atlas supplier records: {len(df):,}")
            else:
                logger.warning(f"  No Supplier column in {file_path.name}")
                return pd.DataFrame()

            # Filter to Atlas products
            if 'TradeName' in df.columns:
                df['Is_Atlas_Product'] = df['TradeName'].apply(self.is_atlas_product)
                df = df[df['Is_Atlas_Product']]
                logger.info(f"  Atlas product records: {len(df):,}")
            else:
                logger.warning(f"  No TradeName column in {file_path.name}")

            # Keep only relevant columns
            columns_to_keep = [
                'DisclosureId', 'JobStartDate', 'JobEndDate',
                'Supplier', 'TradeName', 'Purpose',
                'PercentHFJob', 'MassIngredient',
                'TotalBaseWaterVolume',
                'StateName', 'CountyName', 'OperatorName'
            ]

            # Only keep columns that exist
            columns_to_keep = [col for col in columns_to_keep if col in df.columns]
            df = df[columns_to_keep]

            logger.info(f"  Final Atlas records: {len(df):,}")

            return df

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            return pd.DataFrame()

    def process_all_registry_files(self, data_dir: Path) -> pd.DataFrame:
        """
        Process all FracFocus Registry CSV files.

        Args:
            data_dir: Directory containing CSV files

        Returns:
            Combined DataFrame with all Atlas records
        """
        logger.info("\n=== PROCESSING ALL FRACFOCUS REGISTRY FILES ===")

        # Find all registry CSV files
        pattern = str(data_dir / 'FracFocusRegistry_*.csv')
        csv_files = sorted(glob.glob(pattern))

        if not csv_files:
            logger.error(f"No FracFocusRegistry_*.csv files found in {data_dir}")
            # Check if there's extracted data
            extracted_dir = data_dir / 'extracted'
            if extracted_dir.exists():
                pattern = str(extracted_dir / '**' / 'FracFocusRegistry*.csv')
                csv_files = sorted(glob.glob(pattern, recursive=True))

        if not csv_files:
            raise FileNotFoundError(f"No FracFocus CSV files found in {data_dir}")

        logger.info(f"Found {len(csv_files)} CSV files to process")

        # Process each file
        dataframes = []
        for csv_file in csv_files:
            df = self.process_registry_file(Path(csv_file))
            if len(df) > 0:
                dataframes.append(df)

        if not dataframes:
            raise ValueError("No Atlas records found in any files")

        # Concatenate all dataframes
        logger.info("\n=== CONSOLIDATING ALL ATLAS RECORDS ===")
        combined_df = pd.concat(dataframes, ignore_index=True)

        logger.info(f"Total Atlas records: {len(combined_df):,}")
        logger.info(f"Unique disclosures: {combined_df['DisclosureId'].nunique():,}")

        return combined_df

    def calculate_volume_from_mass(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate volume in tonnes from MassIngredient or proxy method.

        Args:
            df: DataFrame with Atlas records

        Returns:
            DataFrame with Volume_tonnes column
        """
        logger.info("\n=== CALCULATING VOLUMES ===")

        # Method 1: Direct from MassIngredient
        if 'MassIngredient' in df.columns:
            has_mass = df['MassIngredient'].notna()
            mass_count = has_mass.sum()
            logger.info(f"Records with MassIngredient: {mass_count:,} ({mass_count/len(df)*100:.1f}%)")

            # Convert lbs to tonnes (1 tonne = 2204.62 lbs)
            df.loc[has_mass, 'Volume_tonnes'] = df.loc[has_mass, 'MassIngredient'] / 2204.62

        # Method 2: Proxy from PercentHFJob × water mass
        needs_proxy = df['Volume_tonnes'].isna() if 'Volume_tonnes' in df.columns else pd.Series([True] * len(df))

        if needs_proxy.sum() > 0:
            logger.info(f"Using proxy method for {needs_proxy.sum():,} records")

            if 'PercentHFJob' in df.columns and 'TotalBaseWaterVolume' in df.columns:
                # Calculate fluid mass
                df.loc[needs_proxy, 'Fluid_mass_lbs'] = df.loc[needs_proxy, 'TotalBaseWaterVolume'] * 8.34

                # Calculate proppant mass
                df.loc[needs_proxy, 'Proppant_mass_lbs'] = (
                    (df.loc[needs_proxy, 'PercentHFJob'] / 100.0) *
                    df.loc[needs_proxy, 'Fluid_mass_lbs']
                )

                # Convert to tonnes
                df.loc[needs_proxy, 'Volume_tonnes'] = df.loc[needs_proxy, 'Proppant_mass_lbs'] / 2204.62

        # Fill any remaining NaN with 0
        if 'Volume_tonnes' not in df.columns:
            df['Volume_tonnes'] = 0
        else:
            df['Volume_tonnes'] = df['Volume_tonnes'].fillna(0)

        logger.info(f"Total volume calculated: {df['Volume_tonnes'].sum():,.0f} tonnes")

        return df

    def add_time_dimensions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Year, Quarter, Month columns from JobStartDate.

        Args:
            df: DataFrame with JobStartDate

        Returns:
            DataFrame with time dimensions added
        """
        logger.info("\n=== ADDING TIME DIMENSIONS ===")

        # Parse dates
        df['JobStartDate'] = pd.to_datetime(df['JobStartDate'], errors='coerce')

        # Extract time components
        df['Year'] = df['JobStartDate'].dt.year
        df['Quarter'] = df['JobStartDate'].dt.quarter
        df['Month'] = df['JobStartDate'].dt.month
        df['Month_Name'] = df['JobStartDate'].dt.strftime('%B')
        df['Year_Quarter'] = df['JobStartDate'].dt.to_period('Q').astype(str)

        # Remove rows with invalid dates
        initial_count = len(df)
        df = df[df['Year'].notna()]
        removed = initial_count - len(df)

        if removed > 0:
            logger.warning(f"Removed {removed:,} rows with invalid dates")

        logger.info(f"Date range: {df['Year'].min():.0f} to {df['Year'].max():.0f}")

        return df

    def aggregate_by_time_and_product(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate volumes by time period and product.

        Args:
            df: DataFrame with volumes and time dimensions

        Returns:
            Aggregated DataFrame
        """
        logger.info("\n=== AGGREGATING BY TIME AND PRODUCT ===")

        # Standardize product categories
        df['Product_Category'] = df['TradeName'].apply(self.standardize_product_category)

        # Aggregate by Year, Quarter, Month, and Product
        agg_df = df.groupby(['Year', 'Quarter', 'Month', 'Product_Category']).agg({
            'Volume_tonnes': 'sum',
            'DisclosureId': 'nunique',  # Count of unique jobs
            'TradeName': 'first'  # Sample product name
        }).reset_index()

        # Rename columns
        agg_df = agg_df.rename(columns={
            'DisclosureId': 'Job_Count',
            'TradeName': 'Sample_Product_Name'
        })

        # Sort by time
        agg_df = agg_df.sort_values(['Year', 'Quarter', 'Month', 'Product_Category'])

        logger.info(f"Aggregated to {len(agg_df):,} rows")
        logger.info(f"Product categories: {agg_df['Product_Category'].nunique()}")

        return agg_df

    def generate_summary_report(self, df: pd.DataFrame, output_path: Path) -> None:
        """
        Generate summary report of Atlas product volumes.

        Args:
            df: Aggregated DataFrame
            output_path: Path to save report
        """
        logger.info("\n=== GENERATING SUMMARY REPORT ===")

        with open(output_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("ATLAS ENERGY SOLUTIONS - PRODUCT VOLUME ANALYSIS\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            # Overall statistics
            f.write("OVERALL STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total volume (all time): {df['Volume_tonnes'].sum():,.0f} tonnes\n")
            f.write(f"Date range: {df['Year'].min():.0f} to {df['Year'].max():.0f}\n")
            f.write(f"Total jobs: {df['Job_Count'].sum():,.0f}\n")
            f.write(f"Product categories: {df['Product_Category'].nunique()}\n\n")

            # Volume by product category
            f.write("VOLUME BY PRODUCT CATEGORY (All Time)\n")
            f.write("-" * 80 + "\n")
            product_totals = df.groupby('Product_Category')['Volume_tonnes'].sum().sort_values(ascending=False)

            for product, volume in product_totals.items():
                pct = volume / product_totals.sum() * 100
                f.write(f"{product:<30} {volume:>15,.0f} tonnes ({pct:>5.1f}%)\n")

            # Recent quarterly trends
            f.write("\n\nRECENT QUARTERLY TRENDS\n")
            f.write("-" * 80 + "\n")

            quarterly = df.groupby(['Year', 'Quarter'])['Volume_tonnes'].sum().tail(8)

            f.write(f"{'Quarter':<15} {'Volume (tonnes)':<20} {'Jobs':<10}\n")
            f.write("-" * 80 + "\n")

            for (year, quarter), volume in quarterly.items():
                jobs = df[(df['Year'] == year) & (df['Quarter'] == quarter)]['Job_Count'].sum()
                quarter_str = f"{int(year)}Q{int(quarter)}"
                f.write(f"{quarter_str:<15} {volume:>15,.0f}     {jobs:>7,.0f}\n")

            f.write("\n" + "=" * 80 + "\n")

        logger.info(f"Summary report saved to {output_path}")


def main():
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("ATLAS ENERGY SOLUTIONS - PRODUCT VOLUME ANALYSIS")
    logger.info("=" * 80)

    analyzer = AtlasProductAnalyzer()

    # Process all registry files
    try:
        atlas_df = analyzer.process_all_registry_files(DATA_DIR)
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.info("\nPlease ensure FracFocus CSV files are in the data/ directory")
        logger.info("Files should be named: FracFocusRegistry_1.csv, FracFocusRegistry_2.csv, etc.")
        return

    # Calculate volumes
    atlas_df = analyzer.calculate_volume_from_mass(atlas_df)

    # Add time dimensions
    atlas_df = analyzer.add_time_dimensions(atlas_df)

    # Save verification file FIRST (before aggregation)
    logger.info("\n=== SAVING VERIFICATION FILE ===")
    verification_columns = ['DisclosureId', 'Year', 'Quarter', 'Year_Quarter', 'Volume_tonnes']
    verification_df = atlas_df[verification_columns].copy()
    verification_df = verification_df.sort_values(['Year', 'Quarter', 'DisclosureId'])

    verification_path = OUTPUT_DIR / 'atlas_verification_disclosures.csv'
    logger.info(f"Saving verification file: {verification_path}")
    verification_df.to_csv(verification_path, index=False)
    logger.info(f"Verification file has {len(verification_df):,} disclosure records")

    # Aggregate by time and product
    aggregated_df = analyzer.aggregate_by_time_and_product(atlas_df)

    # Save outputs
    logger.info("\n=== SAVING OUTPUTS ===")

    # Save detailed records
    detail_path = OUTPUT_DIR / 'atlas_product_details.csv'
    logger.info(f"Saving detailed records: {detail_path}")
    atlas_df.to_csv(detail_path, index=False)

    # Save aggregated time series
    timeseries_path = OUTPUT_DIR / 'atlas_product_timeseries.csv'
    logger.info(f"Saving time series: {timeseries_path}")
    aggregated_df.to_csv(timeseries_path, index=False)

    # Generate summary report
    report_path = OUTPUT_DIR / 'atlas_product_summary.txt'
    analyzer.generate_summary_report(aggregated_df, report_path)

    # Display sample
    logger.info("\n=== SAMPLE OUTPUT (Recent Quarters) ===")
    print(aggregated_df.tail(20).to_string())

    logger.info("\n" + "=" * 80)
    logger.info("ANALYSIS COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Outputs saved to: {OUTPUT_DIR.absolute()}")


if __name__ == '__main__':
    main()
