#!/usr/bin/env python3
import csv
from pathlib import Path

# Get the project root directory (parent of scripts/)
project_root = Path(__file__).parent.parent

# Read population data into a dictionary
populations = {}
with open(project_root / 'data/processed/postcode_population.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        populations[row['POSTCODE']] = row['POPULATION']

# Read firearms data and combine with population
combined_data = []
with open(project_root / 'data/raw/postcode_firearms.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        postcode = row['POSTCODE']
        firearms = row['FIREARMS']
        population = populations.get(postcode, 'N/A')

        # Calculate firearms per 1000 people if we have population data
        firearms_per_1000 = ''
        if population != 'N/A' and population != '0':
            try:
                firearms_per_1000 = f"{(int(firearms) / int(population) * 1000):.2f}"
            except (ValueError, ZeroDivisionError):
                firearms_per_1000 = 'N/A'

        combined_data.append({
            'POSTCODE': postcode,
            'POPULATION': population,
            'FIREARMS': firearms,
            'FIREARMS_PER_1000': firearms_per_1000
        })

# Write combined data to CSV
output_file = project_root / 'data/processed/postcode_population_firearms.csv'
with open(output_file, 'w', newline='') as f:
    fieldnames = ['POSTCODE', 'POPULATION', 'FIREARMS', 'FIREARMS_PER_1000']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(combined_data)

print(f"Combined data written to {output_file}")
print(f"Total postcodes: {len(combined_data)}")

# Count how many postcodes have population data
with_pop = sum(1 for row in combined_data if row['POPULATION'] != 'N/A')
print(f"Postcodes with population data: {with_pop}")
print(f"Postcodes without population data: {len(combined_data) - with_pop}")
