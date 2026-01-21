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

    # ==================== PHASE 4: QUARTERLY ATTRIBUTION ====================

    def distribute_across_quarters(self, row: pd.Series) -> Dict[str, float]:
        """
        For jobs spanning multiple quarters, distribute proppant proportionally
        based on days in each quarter.

        Example: Job from Dec 15, 2023 to Jan 15, 2024 (31 days)
        - Q4 2023: 16 days → 52% of proppant
        - Q1 2024: 15 days → 48% of proppant

        Args:
            row: DataFrame row with JobStartDate, JobEndDate, JobDurationDays

        Returns:
            Dictionary of {quarter: proportion}
        """
        start = row['JobStartDate']
        end = row['JobEndDate']
        total_days = row['JobDurationDays']

        if total_days == 0:
            # Single day job
            return {start.to_period('Q'): 1.0}

        # Generate date range for each day of the job
        date_range = pd.date_range(start, end, freq='D')

        # Count days in each quarter
        quarter_days = date_range.to_period('Q').value_counts()

        # Calculate proportion for each quarter
        proportions = {}
        for quarter, days in quarter_days.items():
            proportions[str(quarter)] = days / total_days

        return proportions

    def attribute_to_quarters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create a quarterly aggregation with proppant attributed correctly.

        Business Rules:
        - Short jobs (≤45 days): 100% attributed to start quarter
        - Long jobs (>45 days): Distributed proportionally across quarters
        - Extreme outliers (>365 days): Flagged for manual review

        Args:
            df: DataFrame with Proppant_lbs calculated

        Returns:
            DataFrame with one row per disclosure-quarter combination
        """
        logger.info("Attributing proppant and water to quarters...")

        # Get unique disclosures (one row per disclosure)
        disclosure_df = df.drop_duplicates(subset=['DisclosureId'])

        results = []
        long_jobs = 0
        extreme_outliers = 0

        for idx, row in disclosure_df.iterrows():
            job_duration = row['JobDurationDays']
            proppant_lbs = row['Proppant_lbs']
            water_gal = row['TotalBaseWaterVolume']

            # Flag extreme outliers
            if job_duration > 365:
                extreme_outliers += 1

            if job_duration <= 45:
                # Simple case: all to start quarter
                results.append({
                    'Quarter': str(row['JobStartDate'].to_period('Q')),
                    'Proppant_lbs': proppant_lbs,
                    'Water_gal': water_gal,
                    'StateName': row['StateName'],
                    'CountyName': row['CountyName'],
                    'DisclosureId': row['DisclosureId'],
                    'JobDurationDays': job_duration,
                    'APINumber': row.get('APINumber', None),
                    'Outlier_LongJob': job_duration > 365
                })
            else:
                # Complex case: distribute across quarters
                long_jobs += 1
                proportions = self.distribute_across_quarters(row)

                for quarter, pct in proportions.items():
                    results.append({
                        'Quarter': quarter,
                        'Proppant_lbs': proppant_lbs * pct,
                        'Water_gal': water_gal * pct,
                        'StateName': row['StateName'],
                        'CountyName': row['CountyName'],
                        'DisclosureId': row['DisclosureId'],
                        'JobDurationDays': job_duration,
                        'APINumber': row.get('APINumber', None),
                        'Outlier_LongJob': job_duration > 365
                    })

        logger.info(f"Processed {len(disclosure_df):,} disclosures")
        logger.info(f"  Short jobs (≤45 days): {len(disclosure_df) - long_jobs:,}")
        logger.info(f"  Long jobs (>45 days): {long_jobs:,}")
        logger.info(f"  Extreme outliers (>365 days): {extreme_outliers:,}")

        quarterly_df = pd.DataFrame(results)
        self.quarterly_data = quarterly_df

        return quarterly_df

    # ==================== PHASE 5: REGIONAL AGGREGATION ====================

    # Basin definitions
    BASIN_DEFINITIONS = {
        'Permian Basin': {
            'Texas': [
                'Andrews', 'Borden', 'Crane', 'Crockett', 'Dawson', 'Ector',
                'Gaines', 'Glasscock', 'Howard', 'Loving', 'Martin', 'Midland',
                'Pecos', 'Reeves', 'Terrell', 'Upton', 'Ward', 'Winkler',
                'Coke', 'Sterling', 'Garza', 'Lynn', 'Mitchell', 'Reagan', 'Tom Green'
            ],
            'New Mexico': ['Lea', 'Eddy', 'Chaves']
        },
        'Eagle Ford': {
            'Texas': [
                'Atascosa', 'Bee', 'DeWitt', 'Dimmit', 'Frio', 'Gonzales',
                'Karnes', 'La Salle', 'Lavaca', 'Live Oak', 'McMullen',
                'Webb', 'Wilson', 'Zavala'
            ]
        },
        'Haynesville': {
            'Texas': ['Harrison', 'Panola', 'Shelby'],
            'Louisiana': ['Bossier', 'Caddo', 'De Soto', 'Red River']
        },
        'Bakken': {
            'North Dakota': ['Dunn', 'McKenzie', 'Mountrail', 'Williams'],
            'Montana': ['Richland', 'Roosevelt']
        },
        'Marcellus': {
            'Pennsylvania': ['Allegheny', 'Armstrong', 'Beaver', 'Butler', 'Fayette',
                           'Greene', 'Washington', 'Westmoreland'],
            'West Virginia': ['Marshall', 'Wetzel', 'Tyler', 'Doddridge', 'Harrison']
        }
    }

    def assign_basin(self, row: pd.Series) -> str:
        """
        Assign basin based on state + county.

        Args:
            row: DataFrame row with StateName and CountyName

        Returns:
            Basin name or 'Other'
        """
        state = row['StateName']
        county = row['CountyName']

        # Handle missing values
        if pd.isna(state) or pd.isna(county):
            return 'Other'

        for basin_name, basin_def in self.BASIN_DEFINITIONS.items():
            if state in basin_def and county in basin_def[state]:
                return basin_name

        return 'Other'

    def add_regional_classifications(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add basin classification to each row.

        Args:
            df: DataFrame with StateName and CountyName

        Returns:
            DataFrame with Basin column added
        """
        logger.info("Adding regional classifications...")

        df['Basin'] = df.apply(self.assign_basin, axis=1)

        # Log basin distribution
        basin_counts = df['Basin'].value_counts()
        logger.info("\nBasin distribution:")
        for basin, count in basin_counts.items():
            logger.info(f"  {basin}: {count:,} records")

        return df

    def aggregate_by_region(self, df: pd.DataFrame,
                           group_by: List[str] = ['Quarter', 'Basin']) -> pd.DataFrame:
        """
        Aggregate data by specified grouping (Quarter, Basin, State, County, etc.)

        Args:
            df: Quarterly attributed DataFrame
            group_by: List of columns to group by

        Returns:
            Aggregated DataFrame
        """
        logger.info(f"Aggregating by: {', '.join(group_by)}")

        aggregated = df.groupby(group_by).agg({
            'Proppant_lbs': 'sum',
            'Water_gal': 'sum',
            'DisclosureId': 'count'  # Well count
        }).reset_index()

        # Rename for clarity
        aggregated = aggregated.rename(columns={
            'DisclosureId': 'Well_count'
        })

        # Add calculated metrics
        aggregated['Proppant_MM_lbs'] = aggregated['Proppant_lbs'] / 1_000_000
        aggregated['Water_MM_gal'] = aggregated['Water_gal'] / 1_000_000
        aggregated['Avg_Proppant_per_Well_lbs'] = (
            aggregated['Proppant_lbs'] / aggregated['Well_count']
        )
        aggregated['Avg_Water_per_Well_gal'] = (
            aggregated['Water_gal'] / aggregated['Well_count']
        )

        return aggregated


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

    # Phase 4: Quarterly attribution
    logger.info("\n=== PHASE 4: QUARTERLY ATTRIBUTION ===")
    df_quarterly = analyzer.attribute_to_quarters(df_with_proppant)

    # Phase 5: Regional aggregation
    logger.info("\n=== PHASE 5: REGIONAL AGGREGATION ===")
    df_quarterly = analyzer.add_regional_classifications(df_quarterly)

    # Generate aggregated summaries
    logger.info("\n=== GENERATING SUMMARIES ===")

    # By Quarter and Basin
    summary_basin = analyzer.aggregate_by_region(
        df_quarterly,
        group_by=['Quarter', 'Basin']
    )

    # By Quarter and State
    summary_state = analyzer.aggregate_by_region(
        df_quarterly,
        group_by=['Quarter', 'StateName']
    )

    # By Quarter, State, and County
    summary_county = analyzer.aggregate_by_region(
        df_quarterly,
        group_by=['Quarter', 'StateName', 'CountyName']
    )

    # Permian Basin specific
    df_permian = df_quarterly[df_quarterly['Basin'] == 'Permian Basin']
    if len(df_permian) > 0:
        summary_permian_county = analyzer.aggregate_by_region(
            df_permian,
            group_by=['Quarter', 'CountyName']
        )
    else:
        summary_permian_county = None
        logger.warning("No Permian Basin data found")

    # Save all outputs
    logger.info("\n=== SAVING OUTPUTS ===")

    output_files = {
        'quarterly_by_basin.csv': summary_basin,
        'quarterly_by_state.csv': summary_state,
        'quarterly_by_county.csv': summary_county,
        'quarterly_detail.csv': df_quarterly
    }

    if summary_permian_county is not None:
        output_files['permian_by_county.csv'] = summary_permian_county

    for filename, data in output_files.items():
        output_path = OUTPUT_DIR / filename
        logger.info(f"Saving {filename} ({len(data):,} rows)")
        data.to_csv(output_path, index=False)

    # Display summary statistics
    logger.info("\n=== SUMMARY STATISTICS ===")
    logger.info(f"Total quarters analyzed: {df_quarterly['Quarter'].nunique()}")
    logger.info(f"Date range: {df_quarterly['Quarter'].min()} to {df_quarterly['Quarter'].max()}")
    logger.info(f"Total proppant: {summary_basin['Proppant_lbs'].sum() / 1e9:.2f} billion lbs")
    logger.info(f"Total water: {summary_basin['Water_gal'].sum() / 1e9:.2f} billion gallons")
    logger.info(f"Total wells: {df_quarterly['DisclosureId'].nunique():,}")

    logger.info("\n=== ANALYSIS COMPLETE ===")
    logger.info(f"Output files saved to: {OUTPUT_DIR.absolute()}")
    logger.info("Next steps: Run interactive dashboard for visualization")


if __name__ == '__main__':
    main()
