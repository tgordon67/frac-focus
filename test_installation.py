"""
Test script to verify FracFocus Analysis Tool installation and functionality.

This script creates a small synthetic dataset and runs the analysis pipeline
to verify that all components are working correctly.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Import the analyzer
try:
    from fracfocus_analysis import FracFocusAnalyzer
    logger.info("✓ Successfully imported FracFocusAnalyzer")
except ImportError as e:
    logger.error(f"✗ Failed to import FracFocusAnalyzer: {e}")
    sys.exit(1)


def create_sample_data(n_disclosures=100):
    """Create synthetic FracFocus data for testing"""
    logger.info(f"Creating sample dataset with {n_disclosures} disclosures...")

    np.random.seed(42)

    # Generate disclosure IDs
    disclosure_ids = [f"TEST_{i:06d}" for i in range(n_disclosures)]

    # Sample data will have 3 rows per disclosure (2 chemicals + 1 proppant)
    data = []

    for disc_id in disclosure_ids:
        # Random location (Texas counties in Permian)
        counties = ['Martin', 'Midland', 'Ector', 'Upton', 'Andrews']
        county = np.random.choice(counties)

        # Random date in 2023
        start_date = pd.Timestamp('2023-01-01') + pd.Timedelta(days=np.random.randint(0, 365))
        end_date = start_date + pd.Timedelta(days=np.random.randint(3, 10))

        # Random water volume (3-8 million gallons)
        water_volume = np.random.uniform(3_000_000, 8_000_000)

        # Create rows for this disclosure
        # Row 1: Proppant
        data.append({
            'DisclosureId': disc_id,
            'APINumber': f'42-{np.random.randint(100, 999)}-{np.random.randint(10000, 99999)}',
            'StateName': 'Texas',
            'CountyName': county,
            'JobStartDate': start_date,
            'JobEndDate': end_date,
            'TotalBaseWaterVolume': water_volume,
            'Purpose': 'Proppant',
            'IngredientName': 'Silica Sand',
            'PercentHFJob': np.random.uniform(8, 12),  # 8-12% proppant
            'MassIngredient': None,  # Will be missing for most
            'OperatorName': 'Test Operator',
            'TVD': np.random.uniform(8000, 12000)
        })

        # Row 2: Surfactant
        data.append({
            'DisclosureId': disc_id,
            'APINumber': f'42-{np.random.randint(100, 999)}-{np.random.randint(10000, 99999)}',
            'StateName': 'Texas',
            'CountyName': county,
            'JobStartDate': start_date,
            'JobEndDate': end_date,
            'TotalBaseWaterVolume': water_volume,
            'Purpose': 'Surfactant',
            'IngredientName': 'Test Surfactant',
            'PercentHFJob': np.random.uniform(0.1, 0.5),
            'MassIngredient': None,
            'OperatorName': 'Test Operator',
            'TVD': np.random.uniform(8000, 12000)
        })

        # Row 3: Acid
        data.append({
            'DisclosureId': disc_id,
            'APINumber': f'42-{np.random.randint(100, 999)}-{np.random.randint(10000, 99999)}',
            'StateName': 'Texas',
            'CountyName': county,
            'JobStartDate': start_date,
            'JobEndDate': end_date,
            'TotalBaseWaterVolume': water_volume,
            'Purpose': 'Acid',
            'IngredientName': 'Hydrochloric Acid',
            'PercentHFJob': np.random.uniform(0.5, 2.0),
            'MassIngredient': None,
            'OperatorName': 'Test Operator',
            'TVD': np.random.uniform(8000, 12000)
        })

    df = pd.DataFrame(data)
    logger.info(f"✓ Created sample dataset: {len(df)} rows, {df['DisclosureId'].nunique()} disclosures")

    return df


def run_tests():
    """Run test suite"""
    logger.info("\n" + "="*60)
    logger.info("FRACFOCUS ANALYSIS TOOL - INSTALLATION TEST")
    logger.info("="*60 + "\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Check dependencies
    logger.info("Test 1: Checking dependencies...")
    try:
        import pandas
        import numpy
        import plotly
        import dash
        logger.info("✓ All required packages installed")
        tests_passed += 1
    except ImportError as e:
        logger.error(f"✗ Missing dependency: {e}")
        tests_failed += 1
        return

    # Test 2: Create sample data
    logger.info("\nTest 2: Creating sample data...")
    try:
        df = create_sample_data(n_disclosures=50)
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Failed to create sample data: {e}")
        tests_failed += 1
        return

    # Test 3: Initialize analyzer
    logger.info("\nTest 3: Initializing analyzer...")
    try:
        analyzer = FracFocusAnalyzer()
        logger.info("✓ Analyzer initialized successfully")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Failed to initialize analyzer: {e}")
        tests_failed += 1
        return

    # Test 4: Clean data
    logger.info("\nTest 4: Testing data cleaning...")
    try:
        df_clean = analyzer.clean_data(df)
        logger.info(f"✓ Data cleaned: {len(df_clean)} rows retained")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Data cleaning failed: {e}")
        tests_failed += 1
        return

    # Test 5: Calculate proppant
    logger.info("\nTest 5: Testing proppant calculations...")
    try:
        df_proppant = analyzer.add_proppant_calculations(df_clean)
        total_proppant = df_proppant['Proppant_lbs'].sum()
        logger.info(f"✓ Proppant calculated: {total_proppant:,.0f} lbs total")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Proppant calculation failed: {e}")
        tests_failed += 1
        return

    # Test 6: Quarterly attribution
    logger.info("\nTest 6: Testing quarterly attribution...")
    try:
        df_quarterly = analyzer.attribute_to_quarters(df_proppant)
        quarters = df_quarterly['Quarter'].nunique()
        logger.info(f"✓ Quarterly attribution complete: {quarters} quarters")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Quarterly attribution failed: {e}")
        tests_failed += 1
        return

    # Test 7: Regional classification
    logger.info("\nTest 7: Testing regional classification...")
    try:
        df_quarterly = analyzer.add_regional_classifications(df_quarterly)
        basins = df_quarterly['Basin'].value_counts()
        logger.info(f"✓ Regional classification complete")
        logger.info(f"  Permian Basin: {basins.get('Permian Basin', 0)} records")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Regional classification failed: {e}")
        tests_failed += 1
        return

    # Test 8: Aggregation
    logger.info("\nTest 8: Testing aggregation...")
    try:
        summary = analyzer.aggregate_by_region(df_quarterly, group_by=['Quarter', 'Basin'])
        logger.info(f"✓ Aggregation complete: {len(summary)} summary rows")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Aggregation failed: {e}")
        tests_failed += 1
        return

    # Test 9: Validation
    logger.info("\nTest 9: Testing validation...")
    try:
        issues = analyzer.validate_data(df_proppant)
        total_issues = sum(len(v) for v in issues.values())
        logger.info(f"✓ Validation complete: {total_issues} issues found (expected for sample data)")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Validation failed: {e}")
        tests_failed += 1
        return

    # Test 10: Check dashboard imports
    logger.info("\nTest 10: Checking dashboard components...")
    try:
        import dashboard
        logger.info("✓ Dashboard module imported successfully")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Dashboard import failed: {e}")
        tests_failed += 1

    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Tests passed: {tests_passed}")
    logger.info(f"Tests failed: {tests_failed}")

    if tests_failed == 0:
        logger.info("\n✓ ALL TESTS PASSED - Installation verified!")
        logger.info("\nYou can now:")
        logger.info("1. Download FracFocus data to data/fracfocus_data.zip")
        logger.info("2. Run: python fracfocus_analysis.py")
        logger.info("3. Run: python dashboard.py")
        return 0
    else:
        logger.error("\n✗ SOME TESTS FAILED - Please check error messages above")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
