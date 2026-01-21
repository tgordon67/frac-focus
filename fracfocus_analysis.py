"""
FracFocus Proppant & Water Demand Analysis Tool

This tool processes FracFocus Chemical Disclosure Registry data to track
proppant and water consumption by quarter and region, with focus on the
Permian Basin for AESI supply chain analysis.
"""

import os
import requests
import zipfile
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path('data')
OUTPUT_DIR = Path('output')
FRACFOCUS_URL = 'https://fracfocus.org/data-download'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


class FracFocusAnalyzer:
    """Main analyzer class for FracFocus data processing"""

    def __init__(self):
        self.raw_data = None
        self.cleaned_data = None
        self.quarterly_data = None

    # ==================== PHASE 1: DATA ACQUISITION ====================

    def download_fracfocus_data(self, save_path: Optional[Path] = None) -> Path:
        """
        Download FracFocus CSV data from the official website.

        Note: The actual download requires clicking through the website.
        This method provides instructions and validates the downloaded file.

        Args:
            save_path: Path where the ZIP file is saved

        Returns:
            Path to the downloaded ZIP file
        """
        if save_path is None:
            save_path = DATA_DIR / 'fracfocus_data.zip'

        if save_path.exists():
            logger.info(f"Data file already exists at {save_path}")
            return save_path

        logger.warning(f"""
        MANUAL DOWNLOAD REQUIRED:

        1. Go to: {FRACFOCUS_URL}
        2. Click 'Download CSV' under 'Oil and Gas Data'
        3. Save the ZIP file to: {save_path}

        Once downloaded, run this script again.
        """)

        raise FileNotFoundError(f"Please download data to {save_path}")

    def extract_and_consolidate_data(self, zip_path: Path) -> pd.DataFrame:
        """
        Extract all CSVs from ZIP and consolidate into a single DataFrame.

        Args:
            zip_path: Path to the FracFocus ZIP file

        Returns:
            Consolidated DataFrame with all records
        """
        logger.info(f"Extracting data from {zip_path}")

        extract_dir = DATA_DIR / 'extracted'
        extract_dir.mkdir(exist_ok=True)

        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find all CSV files
        csv_files = list(extract_dir.glob('**/*.csv'))
        logger.info(f"Found {len(csv_files)} CSV files")

        if not csv_files:
            raise ValueError("No CSV files found in ZIP archive")

        # Read and consolidate CSVs
        dataframes = []
        for csv_file in csv_files:
            logger.info(f"Reading {csv_file.name}...")
            try:
                df = pd.read_csv(csv_file, low_memory=False)
                dataframes.append(df)
                logger.info(f"  Loaded {len(df):,} rows")
            except Exception as e:
                logger.error(f"  Error reading {csv_file}: {e}")

        # Concatenate all dataframes
        logger.info("Consolidating all data...")
        consolidated_df = pd.concat(dataframes, ignore_index=True)

        logger.info(f"Total records: {len(consolidated_df):,}")
        logger.info(f"Columns: {list(consolidated_df.columns)}")

        # Save consolidated data
        consolidated_path = DATA_DIR / 'consolidated_data.csv'
        logger.info(f"Saving consolidated data to {consolidated_path}")
        consolidated_df.to_csv(consolidated_path, index=False)

        self.raw_data = consolidated_df
        return consolidated_df

    def load_consolidated_data(self, path: Optional[Path] = None) -> pd.DataFrame:
        """
        Load previously consolidated data for faster subsequent runs.

        Args:
            path: Path to consolidated CSV file

        Returns:
            DataFrame with all records
        """
        if path is None:
            path = DATA_DIR / 'consolidated_data.csv'

        if not path.exists():
            raise FileNotFoundError(f"Consolidated data not found at {path}")

        logger.info(f"Loading consolidated data from {path}")
        df = pd.read_csv(path, low_memory=False)
        logger.info(f"Loaded {len(df):,} rows with {len(df.columns)} columns")

        self.raw_data = df
        return df

    # ==================== PHASE 2: DATA CLEANING ====================

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare data for analysis.

        Handles:
        - Outlier removal
        - Date parsing
        - Missing value handling
        - Duration calculation

        Args:
            df: Raw DataFrame

        Returns:
            Cleaned DataFrame
        """
        logger.info("Starting data cleaning...")
        initial_count = len(df)

        # Make a copy to avoid modifying original
        df = df.copy()

        # 1. Remove obvious outliers
        logger.info("Removing outliers...")
        df = df[df['TotalBaseWaterVolume'] < 50_000_000]  # Max 50M gallons

        # Only filter TVD if column exists
        if 'TVD' in df.columns:
            df = df[df['TVD'] < 50_000]  # Max 50k feet depth

        # 2. Handle missing dates
        logger.info("Handling dates...")
        df = df.dropna(subset=['JobStartDate', 'JobEndDate'])

        # 3. Parse dates
        df['JobStartDate'] = pd.to_datetime(df['JobStartDate'], errors='coerce')
        df['JobEndDate'] = pd.to_datetime(df['JobEndDate'], errors='coerce')

        # Remove rows where date parsing failed
        df = df.dropna(subset=['JobStartDate', 'JobEndDate'])

        # 4. Filter out disclosures with no water volume
        df = df[df['TotalBaseWaterVolume'].notna()]
        df = df[df['TotalBaseWaterVolume'] > 0]

        # 5. Create duration column
        df['JobDurationDays'] = (df['JobEndDate'] - df['JobStartDate']).dt.days

        # Remove negative durations (data errors)
        df = df[df['JobDurationDays'] >= 0]

        # 6. Handle duplicate disclosures (keep first occurrence)
        df = df.drop_duplicates(subset=['DisclosureId'], keep='first')

        final_count = len(df)
        removed = initial_count - final_count
        logger.info(f"Cleaning complete: Removed {removed:,} rows ({removed/initial_count*100:.1f}%)")
        logger.info(f"Remaining records: {final_count:,}")

        self.cleaned_data = df
        return df

    # ==================== PHASE 3: PROPPANT CALCULATION ====================

    def calculate_proppant_mass(self, disclosure_group: pd.DataFrame) -> float:
        """
        Calculate proppant mass for a single disclosure.

        Logic:
        - PercentHFJob is % by MASS of total fluid
        - Total fluid mass ≈ TotalBaseWaterVolume × water_density (8.34 lbs/gal)
        - Proppant mass = (PercentHFJob / 100) × Total fluid mass

        Args:
            disclosure_group: All rows for a single DisclosureId

        Returns:
            Proppant mass in pounds
        """
        # Get total water volume (same for all rows in this disclosure)
        water_volume_gal = disclosure_group['TotalBaseWaterVolume'].iloc[0]

        # Approximate total fluid mass (water density ≈ 8.34 lbs/gal)
        total_fluid_mass_lbs = water_volume_gal * 8.34

        # Get proppant rows
        proppant_rows = disclosure_group[
            disclosure_group['Purpose'].str.contains('Proppant', case=False, na=False)
        ]

        if len(proppant_rows) == 0:
            return 0.0

        # Sum all proppant percentages
        total_proppant_pct = proppant_rows['PercentHFJob'].sum()

        # Handle missing/invalid percentages
        if pd.isna(total_proppant_pct) or total_proppant_pct < 0:
            return 0.0

        # Calculate proppant mass
        proppant_mass_lbs = (total_proppant_pct / 100.0) * total_fluid_mass_lbs

        return proppant_mass_lbs

    def add_proppant_calculations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add proppant mass calculations to each disclosure.

        Args:
            df: Cleaned DataFrame

        Returns:
            DataFrame with Proppant_lbs column added
        """
        logger.info("Calculating proppant mass for each disclosure...")

        # Calculate proppant for each disclosure
        proppant_by_disclosure = df.groupby('DisclosureId').apply(
            self.calculate_proppant_mass
        )

        # Add back to dataframe
        df['Proppant_lbs'] = df['DisclosureId'].map(proppant_by_disclosure)

        # Fill any NaN values with 0
        df['Proppant_lbs'] = df['Proppant_lbs'].fillna(0)

        logger.info(f"Average proppant per job: {df['Proppant_lbs'].mean():,.0f} lbs")
        logger.info(f"Total proppant: {df['Proppant_lbs'].sum():,.0f} lbs")

        return df


def main():
    """Main execution function"""
    logger.info("Starting FracFocus Analysis Tool")

    analyzer = FracFocusAnalyzer()

    # Phase 1: Load or download data
    try:
        # Try to load existing consolidated data
        df = analyzer.load_consolidated_data()
    except FileNotFoundError:
        # If not found, guide user to download
        try:
            zip_path = analyzer.download_fracfocus_data()
            df = analyzer.extract_and_consolidate_data(zip_path)
        except FileNotFoundError as e:
            logger.error(str(e))
            return

    # Display initial data info
    logger.info("\n=== DATA OVERVIEW ===")
    logger.info(f"Total rows: {len(df):,}")
    logger.info(f"Columns: {len(df.columns)}")
    logger.info(f"Memory usage: {df.memory_usage(deep=True).sum() / 1e9:.2f} GB")

    # Phase 2: Clean data
    df_clean = analyzer.clean_data(df)

    # Phase 3: Calculate proppant
    df_with_proppant = analyzer.add_proppant_calculations(df_clean)

    # Save intermediate results
    output_path = OUTPUT_DIR / 'processed_data.csv'
    logger.info(f"\nSaving processed data to {output_path}")
    df_with_proppant.to_csv(output_path, index=False)

    logger.info("\n=== ANALYSIS COMPLETE ===")
    logger.info("Next steps: Run quarterly attribution and regional analysis")


if __name__ == '__main__':
    main()
