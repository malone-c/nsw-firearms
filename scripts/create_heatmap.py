#!/usr/bin/env python3
import csv
import folium
from folium.plugins import HeatMap
import pgeocode
from pathlib import Path

# Get the project root directory (parent of scripts/)
project_root = Path(__file__).parent.parent

# Read the combined data
data = []
with open(project_root / 'data/processed/postcode_population_firearms.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['FIREARMS_PER_1000'] and row['FIREARMS_PER_1000'] != 'N/A':
            data.append(row)

# Initialize pgeocode for Australia
nomi = pgeocode.Nominatim('AU')

# Get coordinates and prepare data for the map
locations = []
max_rate = 0
min_rate = float('inf')

print("Geocoding postcodes...")
for i, row in enumerate(data):
    postcode = row['POSTCODE']
    location = nomi.query_postal_code(postcode)

    if location.latitude and location.longitude:
        try:
            rate = float(row['FIREARMS_PER_1000'])
            max_rate = max(max_rate, rate)
            min_rate = min(min_rate, rate)

            locations.append({
                'lat': location.latitude,
                'lon': location.longitude,
                'postcode': postcode,
                'population': row['POPULATION'],
                'firearms': row['FIREARMS'],
                'rate': rate
            })
        except ValueError:
            pass

    if (i + 1) % 50 == 0:
        print(f"Processed {i + 1}/{len(data)} postcodes...")

print(f"Successfully geocoded {len(locations)} postcodes")
print(f"Rate range: {min_rate:.2f} to {max_rate:.2f} per 1000 people")

# Create the map centered on NSW
map_center = [-32.5, 147.0]  # Approximate center of NSW
m = folium.Map(
    location=map_center,
    zoom_start=7,
    tiles='OpenStreetMap'
)

# Add alternative tile layers
folium.TileLayer('CartoDB positron').add_to(m)
folium.TileLayer('CartoDB dark_matter').add_to(m)

# Function to get color based on rate
def get_color(rate):
    """Returns color based on firearms per 1000 people"""
    # Create a gradient from green (low) to red (high)
    normalized = (rate - min_rate) / (max_rate - min_rate) if max_rate != min_rate else 0

    if normalized < 0.2:
        return '#00ff00'  # Green
    elif normalized < 0.4:
        return '#7fff00'  # Yellow-green
    elif normalized < 0.6:
        return '#ffff00'  # Yellow
    elif normalized < 0.8:
        return '#ff7f00'  # Orange
    else:
        return '#ff0000'  # Red

# Add circles for each postcode
for loc in locations:
    color = get_color(loc['rate'])

    # Create popup text
    popup_text = f"""
    <div style="font-family: Arial; min-width: 200px;">
        <h4>Postcode {loc['postcode']}</h4>
        <table style="width:100%">
            <tr><td><b>Population:</b></td><td>{loc['population']}</td></tr>
            <tr><td><b>Firearms:</b></td><td>{loc['firearms']}</td></tr>
            <tr><td><b>Per 1000:</b></td><td>{loc['rate']:.2f}</td></tr>
        </table>
    </div>
    """

    folium.CircleMarker(
        location=[loc['lat'], loc['lon']],
        radius=8,
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=f"Postcode {loc['postcode']}: {loc['rate']:.2f} per 1000",
        color=color,
        fillColor=color,
        fillOpacity=0.7,
        weight=2
    ).add_to(m)

# Add a custom legend
legend_html = f'''
<div style="position: fixed;
            bottom: 50px; right: 50px; width: 220px; height: 200px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:14px; padding: 10px; border-radius: 5px;">
    <h4 style="margin-top:0">Firearms per 1000 people</h4>
    <div style="display: flex; align-items: center; margin: 5px 0;">
        <div style="width: 20px; height: 20px; background-color: #00ff00; margin-right: 10px;"></div>
        <span>Low ({min_rate:.1f} - {min_rate + (max_rate-min_rate)*0.2:.1f})</span>
    </div>
    <div style="display: flex; align-items: center; margin: 5px 0;">
        <div style="width: 20px; height: 20px; background-color: #7fff00; margin-right: 10px;"></div>
        <span>{min_rate + (max_rate-min_rate)*0.2:.1f} - {min_rate + (max_rate-min_rate)*0.4:.1f}</span>
    </div>
    <div style="display: flex; align-items: center; margin: 5px 0;">
        <div style="width: 20px; height: 20px; background-color: #ffff00; margin-right: 10px;"></div>
        <span>{min_rate + (max_rate-min_rate)*0.4:.1f} - {min_rate + (max_rate-min_rate)*0.6:.1f}</span>
    </div>
    <div style="display: flex; align-items: center; margin: 5px 0;">
        <div style="width: 20px; height: 20px; background-color: #ff7f00; margin-right: 10px;"></div>
        <span>{min_rate + (max_rate-min_rate)*0.6:.1f} - {min_rate + (max_rate-min_rate)*0.8:.1f}</span>
    </div>
    <div style="display: flex; align-items: center; margin: 5px 0;">
        <div style="width: 20px; height: 20px; background-color: #ff0000; margin-right: 10px;"></div>
        <span>High ({min_rate + (max_rate-min_rate)*0.8:.1f} - {max_rate:.1f})</span>
    </div>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Add layer control
folium.LayerControl().add_to(m)

# Save the map
output_file = project_root / 'output/nsw_firearms_heatmap.html'
m.save(output_file)
print(f"\nMap saved to {output_file}")
print("Open this file in a web browser to view the interactive map!")
