#!/usr/bin/env python3
import csv
import geopandas as gpd
import folium
import json
from pathlib import Path

# Get the project root directory (parent of scripts/)
project_root = Path(__file__).parent.parent

print("Loading postcode boundary data...")
# Read the shapefile
gdf = gpd.read_file(project_root / 'data/raw/poa_2021/POA_2021_AUST_GDA2020.shp')

# Convert to WGS84 (standard lat/lon coordinates for web maps)
gdf = gdf.to_crs(epsg=4326)

print(f"Loaded {len(gdf)} postcode boundaries")

# Read our firearms/population data
print("Loading firearms and population data...")
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

print(f"Loaded data for {len(firearms_data)} postcodes")

# Merge the data with geometries
# The shapefile uses POA_CODE21 for postcode
gdf['POA_CODE21'] = gdf['POA_CODE21'].astype(str)

# Add firearms data to the GeoDataFrame
gdf['firearms_rate'] = gdf['POA_CODE21'].map(
    lambda x: firearms_data.get(x, {}).get('rate', None)
)
gdf['population'] = gdf['POA_CODE21'].map(
    lambda x: firearms_data.get(x, {}).get('population', 'N/A')
)
gdf['firearms'] = gdf['POA_CODE21'].map(
    lambda x: firearms_data.get(x, {}).get('firearms', 'N/A')
)

# Filter to only NSW postcodes (postcodes starting with 2)
# and those that have firearms data
nsw_gdf = gdf[
    (gdf['POA_CODE21'].str.startswith('2')) &
    (gdf['firearms_rate'].notna())
].copy()

print(f"Filtered to {len(nsw_gdf)} NSW postcodes with data")

# Get statistics for the color scale
min_rate = nsw_gdf['firearms_rate'].min()
max_rate = nsw_gdf['firearms_rate'].max()
mean_rate = nsw_gdf['firearms_rate'].mean()
median_rate = nsw_gdf['firearms_rate'].median()

print(f"\nStatistics:")
print(f"  Min rate: {min_rate:.2f} per 1000")
print(f"  Max rate: {max_rate:.2f} per 1000")
print(f"  Mean rate: {mean_rate:.2f} per 1000")
print(f"  Median rate: {median_rate:.2f} per 1000")

# Create the map centered on NSW
map_center = [-32.5, 147.0]
m = folium.Map(
    location=map_center,
    zoom_start=7,
    tiles='CartoDB positron'
)

# Convert to GeoJSON for Folium
nsw_geojson = json.loads(nsw_gdf.to_json())

# Create choropleth layer
choropleth = folium.Choropleth(
    geo_data=nsw_geojson,
    name='Firearms per 1000 people',
    data=nsw_gdf,
    columns=['POA_CODE21', 'firearms_rate'],
    key_on='feature.properties.POA_CODE21',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name='Firearms per 1000 People',
    highlight=True,
    nan_fill_color='lightgray',
    nan_fill_opacity=0.2
).add_to(m)

# Add tooltips with detailed information
style_function = lambda x: {
    'fillColor': '#ffffff',
    'color': '#000000',
    'fillOpacity': 0.1,
    'weight': 0.1
}

highlight_function = lambda x: {
    'fillColor': '#000000',
    'color': '#000000',
    'fillOpacity': 0.3,
    'weight': 2
}

# Create a custom tooltip/popup for each postcode
tooltip = folium.features.GeoJsonTooltip(
    fields=['POA_CODE21', 'population', 'firearms', 'firearms_rate'],
    aliases=['Postcode:', 'Population:', 'Firearms:', 'Per 1000:'],
    style=("background-color: white; color: #333333; font-family: arial; "
           "font-size: 12px; padding: 10px;"),
    localize=True
)

# Add the GeoJson with tooltips
folium.GeoJson(
    nsw_geojson,
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=tooltip,
    name='Postcode Details'
).add_to(m)

# Add alternative tile layers
folium.TileLayer('OpenStreetMap').add_to(m)
folium.TileLayer('CartoDB dark_matter').add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Add title
title_html = '''
<div style="position: fixed;
            top: 10px; left: 50px; width: 500px; height: 60px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:16px; padding: 10px; border-radius: 5px;">
    <h3 style="margin-top:0">NSW Firearms Ownership by Postcode (2021)</h3>
    <p style="margin:0; font-size:12px;">Hover over postcodes for details. Use layer control (top right) to toggle layers.</p>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Save the map
output_file = project_root / 'output/nsw_firearms_choropleth.html'
m.save(output_file)

print(f"\nChoropleth map saved to {output_file}")
print("Open this file in a web browser to view the interactive map!")
