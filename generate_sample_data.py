"""
Generate sample data for dashboard demonstration
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# Define basins and their counties
basins = {
    'Permian Basin': ['Midland', 'Martin', 'Ector', 'Andrews', 'Reeves', 'Ward', 'Loving'],
    'Eagle Ford': ['Karnes', 'DeWitt', 'Gonzales', 'La Salle', 'Webb'],
    'Haynesville': ['Harrison', 'Panola', 'Shelby', 'Caddo', 'De Soto'],
    'Bakken': ['McKenzie', 'Mountrail', 'Williams', 'Dunn'],
    'Marcellus': ['Washington', 'Greene', 'Susquehanna', 'Bradford']
}

states = {
    'Permian Basin': ['Texas', 'New Mexico'],
    'Eagle Ford': ['Texas'],
    'Haynesville': ['Texas', 'Louisiana'],
    'Bakken': ['North Dakota'],
    'Marcellus': ['Pennsylvania']
}

# Generate quarterly data
quarters = pd.date_range('2020-01-01', '2023-12-31', freq='QS')
data = []

for basin in basins.keys():
    for quarter in quarters:
        # Generate realistic values with some variation
        base_proppant = random.uniform(50_000_000, 500_000_000)
        base_water = random.uniform(100_000_000, 1_000_000_000)
        well_count = random.randint(50, 500)

        # Add trend over time
        time_factor = 1 + (quarter - quarters[0]).days / 365 * 0.05

        state = random.choice(states[basin])
        county = random.choice(basins[basin])

        data.append({
            'Quarter': quarter.strftime('%Y-Q%q'),
            'Basin': basin,
            'StateName': state,
            'CountyName': county,
            'Proppant_lbs': base_proppant * time_factor,
            'Water_gal': base_water * time_factor,
            'Well_count': well_count,
            'Proppant_MM_lbs': base_proppant * time_factor / 1_000_000,
            'Water_MM_gal': base_water * time_factor / 1_000_000,
            'Avg_Proppant_per_Well_lbs': base_proppant * time_factor / well_count,
            'Avg_Water_per_Well_gal': base_water * time_factor / well_count
        })

# Create DataFrames
df = pd.DataFrame(data)

# Create output directory
import os
os.makedirs('output', exist_ok=True)

# Save by basin
df_basin = df.groupby(['Quarter', 'Basin']).agg({
    'Proppant_lbs': 'sum',
    'Water_gal': 'sum',
    'Well_count': 'sum'
}).reset_index()

df_basin['Proppant_MM_lbs'] = df_basin['Proppant_lbs'] / 1_000_000
df_basin['Water_MM_gal'] = df_basin['Water_gal'] / 1_000_000
df_basin['Avg_Proppant_per_Well_lbs'] = df_basin['Proppant_lbs'] / df_basin['Well_count']
df_basin['Avg_Water_per_Well_gal'] = df_basin['Water_gal'] / df_basin['Well_count']

df_basin.to_csv('output/quarterly_by_basin.csv', index=False)
print(f"✓ Created quarterly_by_basin.csv with {len(df_basin)} rows")

# Save by state
df_state = df.groupby(['Quarter', 'StateName']).agg({
    'Proppant_lbs': 'sum',
    'Water_gal': 'sum',
    'Well_count': 'sum'
}).reset_index()

df_state['Proppant_MM_lbs'] = df_state['Proppant_lbs'] / 1_000_000
df_state['Water_MM_gal'] = df_state['Water_gal'] / 1_000_000
df_state['Avg_Proppant_per_Well_lbs'] = df_state['Proppant_lbs'] / df_state['Well_count']
df_state['Avg_Water_per_Well_gal'] = df_state['Water_gal'] / df_state['Well_count']

df_state.to_csv('output/quarterly_by_state.csv', index=False)
print(f"✓ Created quarterly_by_state.csv with {len(df_state)} rows")

# Save by county
df_county = df.copy()
df_county.to_csv('output/quarterly_by_county.csv', index=False)
print(f"✓ Created quarterly_by_county.csv with {len(df_county)} rows")

# Save Permian subset
df_permian = df[df['Basin'] == 'Permian Basin'].copy()
df_permian.to_csv('output/permian_by_county.csv', index=False)
print(f"✓ Created permian_by_county.csv with {len(df_permian)} rows")

# Create validation report
with open('output/validation_report.txt', 'w') as f:
    f.write("=== SAMPLE DATA VALIDATION REPORT ===\n\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("NOTE: This is sample/demo data for UI testing.\n")
    f.write("To use real FracFocus data, download from:\n")
    f.write("https://fracfocus.org/data-download\n\n")
    f.write(f"Total records: {len(df)}\n")
    f.write(f"Basins: {', '.join(basins.keys())}\n")
    f.write(f"Date range: {df['Quarter'].min()} to {df['Quarter'].max()}\n")
    f.write("\n✓ Sample data generated successfully\n")

print("✓ Created validation_report.txt")
print("\n" + "="*60)
print("Sample data generation complete!")
print("You can now run: python dashboard.py")
print("="*60)
