#!/usr/bin/env python3
import csv
import geopandas as gpd
import json
from pathlib import Path
import topojson as tp

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

print(f"Converting {len(nsw_gdf)} postcodes to TopoJSON...")
# Convert to TopoJSON for better compression
topo = tp.Topology(nsw_gdf, prequantize=1e4)
topojson_data = topo.to_dict()

# Save TopoJSON
topojson_file = project_root / 'data.topojson'
with open(topojson_file, 'w') as f:
    json.dump(topojson_data, f)

import os
file_size_mb = os.path.getsize(topojson_file) / (1024 * 1024)
print(f"TopoJSON saved: {file_size_mb:.2f} MB")

# Get statistics
min_rate = nsw_gdf['firearms_rate'].min()
max_rate = nsw_gdf['firearms_rate'].max()
mean_rate = nsw_gdf['firearms_rate'].mean()

# Create HTML with external TopoJSON
html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NSW Firearms Ownership Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/topojson@3.0.2/dist/topojson.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .info {{
            padding: 10px;
            background: white;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
        }}
        .info h4 {{ margin: 0 0 5px; color: #777; }}
        .legend {{
            line-height: 18px;
            color: #555;
        }}
        .legend i {{
            width: 18px;
            height: 18px;
            float: left;
            margin-right: 8px;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        const map = L.map('map').setView([-32.5, 147.0], 7);

        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap &copy; CartoDB',
            maxZoom: 20
        }}).addTo(map);

        // Color scale function
        function getColor(rate) {{
            const min = {min_rate};
            const max = {max_rate};
            const normalized = (rate - min) / (max - min);

            return normalized > 0.8 ? '#800026' :
                   normalized > 0.6 ? '#BD0026' :
                   normalized > 0.4 ? '#E31A1C' :
                   normalized > 0.2 ? '#FC4E2A' :
                   normalized > 0.1 ? '#FD8D3C' :
                   normalized > 0.05 ? '#FEB24C' :
                   normalized > 0.02 ? '#FED976' :
                                      '#FFEDA0';
        }}

        function style(feature) {{
            return {{
                fillColor: getColor(feature.properties.firearms_rate),
                weight: 1,
                opacity: 0.5,
                color: 'white',
                fillOpacity: 0.7
            }};
        }}

        function highlightFeature(e) {{
            const layer = e.target;
            layer.setStyle({{
                weight: 3,
                color: '#666',
                fillOpacity: 0.9
            }});
            layer.bringToFront();
            info.update(layer.feature.properties);
        }}

        function resetHighlight(e) {{
            geojsonLayer.resetStyle(e.target);
            info.update();
        }}

        let geojsonLayer;

        // Load TopoJSON
        fetch('data.topojson')
            .then(response => response.json())
            .then(data => {{
                const geojson = topojson.feature(data, data.objects.data);

                geojsonLayer = L.geoJson(geojson, {{
                    style: style,
                    onEachFeature: function(feature, layer) {{
                        layer.on({{
                            mouseover: highlightFeature,
                            mouseout: resetHighlight
                        }});

                        layer.bindPopup(`
                            <b>Postcode: ${{feature.properties.POA_CODE21}}</b><br>
                            Population: ${{feature.properties.population}}<br>
                            Firearms: ${{feature.properties.firearms}}<br>
                            Per 1000: ${{feature.properties.firearms_rate.toFixed(2)}}
                        `);
                    }}
                }}).addTo(map);
            }});

        // Info control
        const info = L.control();
        info.onAdd = function() {{
            this._div = L.DomUtil.create('div', 'info');
            this.update();
            return this._div;
        }};
        info.update = function(props) {{
            this._div.innerHTML = '<h4>NSW Firearms Ownership</h4>' + (props ?
                '<b>Postcode ' + props.POA_CODE21 + '</b><br>' +
                'Population: ' + props.population + '<br>' +
                'Firearms: ' + props.firearms + '<br>' +
                'Per 1000: ' + props.firearms_rate.toFixed(2)
                : 'Hover over a postcode');
        }};
        info.addTo(map);

        // Legend
        const legend = L.control({{position: 'bottomright'}});
        legend.onAdd = function() {{
            const div = L.DomUtil.create('div', 'info legend');
            const grades = [0, 0.02, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8].map(g =>
                {min_rate} + g * ({max_rate} - {min_rate})
            );

            div.innerHTML = '<h4>Firearms per 1000</h4>';
            for (let i = 0; i < grades.length; i++) {{
                div.innerHTML +=
                    '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
                    grades[i].toFixed(0) + (grades[i + 1] ? '&ndash;' + grades[i + 1].toFixed(0) + '<br>' : '+');
            }}
            return div;
        }};
        legend.addTo(map);
    </script>
</body>
</html>'''

# Save HTML
html_file = project_root / 'map.html'
with open(html_file, 'w') as f:
    f.write(html_content)

html_size_mb = os.path.getsize(html_file) / (1024 * 1024)
print(f"HTML saved: {html_size_mb:.2f} MB")
print(f"Total size: {file_size_mb + html_size_mb:.2f} MB")
print(f"\n✓ High-quality map created successfully!")
