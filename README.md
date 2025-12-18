# NSW Firearms Licensing and Ownership Analysis

An analysis and visualization of firearms ownership data across New South Wales (NSW), Australia, combining 2021 Census population data with firearms licensing information.

> **Note**: This project is 100% vibe coded.

## Live Demo

🗺️ **[View the project page](https://malone-c.github.io/nsw-firearms/)**

The landing page includes project statistics and links to the repository. The full interactive choropleth map can be generated locally using the provided scripts.

## Overview

This project creates interactive visualizations showing the distribution of firearms ownership across NSW postcodes, normalized by population. The data includes:
- Firearms counts by postcode
- Population data from the 2021 Australian Census
- Geographic boundary data for postal areas

## Project Structure

```
nsw-firearms/
├── data/
│   ├── raw/                                      # Original data files
│   │   ├── postcode_firearms.csv                 # Firearms count by postcode
│   │   ├── 2021_GCP_POA_for_NSW_short-header/   # 2021 Census data
│   │   └── poa_2021/                             # ABS Postal Area boundaries (shapefile)
│   └── processed/                                # Processed/combined datasets
│       ├── postcode_population.csv               # Extracted population by postcode
│       └── postcode_population_firearms.csv      # Combined population & firearms data
├── scripts/                                      # Python scripts
│   ├── extract_population.py                     # Extract population from census data
│   ├── combine_data.py                           # Combine population & firearms data
│   ├── create_heatmap.py                         # Create point-based heatmap
│   └── create_choropleth_map.py                  # Create choropleth map with boundaries
├── output/                                       # Generated visualizations
│   ├── nsw_firearms_heatmap.html                 # Interactive point-based map
│   └── nsw_firearms_choropleth.html              # Interactive choropleth map
├── docs/                                         # Documentation
│   └── NSW_Firearms_Licensing_and_Ownership_Information_Jun25.pdf
└── README.md
```

## Data Sources

1. **Firearms Data**: NSW firearms licensing counts by postcode (June 2025)
2. **Census Data**: 2021 Australian Census - General Community Profile (GCP) for NSW Postal Areas
3. **Spatial Data**: Australian Bureau of Statistics (ABS) 2021 Postal Area Boundaries (GDA2020)

## Key Statistics

- **Postcodes analyzed**: 611 NSW postcodes
- **Firearms per 1000 people**:
  - Minimum: 3.27 per 1000 (urban areas)
  - Maximum: 2090.91 per 1000 (very small population postcodes)
  - Mean: 343.35 per 1000
  - Median: 138.56 per 1000

## Usage

### Setup

```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install folium pgeocode pandas geopandas
```

### Running the Scripts

```bash
# 1. Extract population data from census
uv run scripts/extract_population.py

# 2. Combine population with firearms data
uv run scripts/combine_data.py

# 3. Create visualizations
uv run scripts/create_heatmap.py           # Point-based heatmap
uv run scripts/create_choropleth_map.py    # Choropleth with postcode boundaries
```

### Viewing the Maps

Open the HTML files in `output/` with any web browser:
- `nsw_firearms_choropleth.html` - Recommended: Shows actual postcode boundaries
- `nsw_firearms_heatmap.html` - Alternative: Point-based visualization

Both maps feature:
- Interactive zoom and pan
- Hover tooltips with detailed statistics
- Color-coded visualization of firearms ownership rates
- Multiple base map options

## Data Fields

### postcode_population_firearms.csv

| Field | Description |
|-------|-------------|
| POSTCODE | Australian postcode |
| POPULATION | Total population (2021 Census) |
| FIREARMS | Number of registered firearms |
| FIREARMS_PER_1000 | Firearms per 1000 residents |

## Requirements

- Python 3.9+
- folium
- pgeocode
- pandas
- geopandas

## GitHub Pages Setup

The interactive choropleth map is available via GitHub Pages. To enable it:

1. Go to your repository settings on GitHub
2. Navigate to **Pages** in the left sidebar
3. Under **Source**, select **Deploy from a branch**
4. Select the **main** branch and **/ (root)** folder
5. Click **Save**

GitHub will automatically deploy `index.html` from the repository root. The map will be available at:
```
https://yourusername.github.io/repository-name/
```

After enabling GitHub Pages, update the Live Demo link in this README with your actual GitHub Pages URL.

## TODO

- Rate of people with more than 0 guns
- Rate of people with more than 10 guns

## License

Data sources are subject to their respective licenses:
- ABS Census data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- ABS Spatial data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
