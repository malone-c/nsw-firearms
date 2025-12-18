#!/usr/bin/env python3
import csv
from pathlib import Path

# Get the project root directory (parent of scripts/)
project_root = Path(__file__).parent.parent

# Path to the census file
census_file = project_root / 'data/raw/2021_GCP_POA_for_NSW_short-header/2021 Census GCP Postal Areas for NSW/2021Census_G01_NSW_POA.csv'
output_file = project_root / 'data/processed/postcode_population.csv'

# Extract postcode and population data
populations = []

with open(census_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        postcode = row['POA_CODE_2021']
        # Remove 'POA' prefix if present (e.g., 'POA2000' -> '2000')
        if postcode.startswith('POA'):
            postcode = postcode[3:]

        population = row['Tot_P_P']
        populations.append({'POSTCODE': postcode, 'POPULATION': population})

# Write to CSV
with open(output_file, 'w', newline='') as f:
    fieldnames = ['POSTCODE', 'POPULATION']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(populations)

print(f"Extracted {len(populations)} postcodes with population data to {output_file}")
