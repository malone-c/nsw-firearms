#!/usr/bin/env python3
import csv
import geopandas as gpd
import folium
import json
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent

print("Loading postcode boundary data...")
gdf = gpd.read_file(project_root / 'data/raw/poa_2021/POA_2021_AUST_GDA2020.shp')
gdf = gdf.to_crs(epsg=4326)

print("Loading firearms/population data...")
firearms_data = {}
with open(project_root / 'data/processed/postcode_population_firearms.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['FIREARMS_PER_1000'] and row['FIREARMS_PER_1000'] != 'N/A':
            firearms_data[row['POSTCODE']] = {
                'population': row['POPULATION'],
                'firearms': row['FIREARMS'],
                'rate': float(row['FIREARMS_PER_1000'])
            }

# Add data to GeoDataFrame
gdf['POA_CODE21'] = gdf['POA_CODE21'].astype(str)
gdf['firearms_rate'] = gdf['POA_CODE21'].map(lambda x: firearms_data.get(x, {}).get('rate', None))
gdf['population'] = gdf['POA_CODE21'].map(lambda x: firearms_data.get(x, {}).get('population', 'N/A'))
gdf['firearms'] = gdf['POA_CODE21'].map(lambda x: firearms_data.get(x, {}).get('firearms', 'N/A'))

# Filter NSW postcodes with data
nsw_gdf = gdf[(gdf['POA_CODE21'].str.startswith('2')) & (gdf['firearms_rate'].notna())].copy()

print(f"Simplifying geometries for {len(nsw_gdf)} postcodes...")
# Simplify geometries to reduce file size (tolerance in degrees, ~1km)
nsw_gdf['geometry'] = nsw_gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# Get statistics
min_rate = nsw_gdf['firearms_rate'].min()
max_rate = nsw_gdf['firearms_rate'].max()

print(f"\nStatistics:")
print(f"  Min rate: {min_rate:.2f} per 1000")
print(f"  Max rate: {max_rate:.2f} per 1000")

# Create the map
map_center = [-32.5, 147.0]
m = folium.Map(
    location=map_center,
    zoom_start=7,
    tiles='CartoDB positron'
)

# Convert to GeoJSON with simplified properties
nsw_geojson = json.loads(nsw_gdf[['POA_CODE21', 'firearms_rate', 'population', 'firearms', 'geometry']].to_json())

# Create choropleth
folium.Choropleth(
    geo_data=nsw_geojson,
    name='Firearms per 1000 people',
    data=nsw_gdf,
    columns=['POA_CODE21', 'firearms_rate'],
    key_on='feature.properties.POA_CODE21',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    line_weight=1,
    legend_name='Firearms per 1000 People',
    nan_fill_color='lightgray'
).add_to(m)

# Add tooltips
tooltip = folium.features.GeoJsonTooltip(
    fields=['POA_CODE21', 'population', 'firearms', 'firearms_rate'],
    aliases=['Postcode:', 'Population:', 'Firearms:', 'Per 1000:'],
    style="background-color: white; color: #333; font-family: arial; font-size: 12px; padding: 10px;"
)

folium.GeoJson(
    nsw_geojson,
    style_function=lambda x: {'fillColor': '#ffffff', 'color': '#000000', 'fillOpacity': 0.1, 'weight': 0.1},
    highlight_function=lambda x: {'fillColor': '#000000', 'color': '#000000', 'fillOpacity': 0.3, 'weight': 2},
    tooltip=tooltip
).add_to(m)

# Add title
title_html = '''
<div style="position: fixed; top: 10px; left: 50px; width: 500px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:14px; padding: 10px; border-radius: 5px;">
    <h3 style="margin:0">NSW Firearms Ownership by Postcode (2021)</h3>
    <p style="margin:5px 0 0 0; font-size:11px;">Hover over postcodes for details</p>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Save the map
output_file = project_root / 'map.html'
m.save(output_file)

# Check file size
import os
file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
print(f"\nOptimized map saved to {output_file}")
print(f"File size: {file_size_mb:.2f} MB")

if file_size_mb > 90:
    print("⚠️  Warning: File is still quite large. May need further optimization.")
else:
    print("✓ File size is acceptable for GitHub Pages")
