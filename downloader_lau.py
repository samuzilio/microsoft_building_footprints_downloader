import requests
import shapely.geometry
import mercantile
import pandas as pd
import tempfile
from tqdm import tqdm
import geopandas as gpd
import json

# Fetch and parse Local Administrative Units GeoJSON file from GISCO
lau_url = "https://gisco-services.ec.europa.eu/distribution/v2/lau/geojson/LAU_RG_01M_2021_4326.geojson"
response = requests.get(lau_url)
lau = response.json()

# Define the target municipality
target_name = "Torino" # Specify the name of the target municipality (e.g., "Torino")
target_feature = next((feature for feature in lau["features"] if feature["properties"]["LAU_NAME"] == target_name), None)
if target_feature:
    target_shape = shapely.geometry.shape(target_feature["geometry"])
    minx, miny, maxx, maxy = target_shape.bounds

# Calculate quad keys for tiles covering the bounding box of the target municipality
quad_keys = set()
for tile in list(mercantile.tiles(minx, miny, maxx, maxy, zooms=9)):
    quad_keys.add(int(mercantile.quadkey(tile)))
quad_keys = list(quad_keys)
print(f"The input area spans {len(quad_keys)} tiles: {quad_keys}")

# Read building data from the CSV file
df = pd.read_csv("https://minedbuildings.blob.core.windows.net/global-buildings/dataset-links.csv")

# Process building data for each quad key
combined_rows = []
with tempfile.TemporaryDirectory() as tmpdir:
    for quad_key in tqdm(quad_keys):
        rows = df[df["QuadKey"] == quad_key] 
        if rows.shape[0] == 1:
            url = rows.iloc[0]["Url"]
            df2 = pd.read_json(url, lines=True)
            df2["geometry"] = df2["geometry"].apply(shapely.geometry.shape)
            gdf = gpd.GeoDataFrame(df2, crs=4326)
            combined_rows.append(gdf)
        elif rows.shape[0] > 1:
            print(f"Multiple rows found for QuadKey: {quad_key}")
            print(rows)
            chosen_row = rows[rows["Location"] == "Italy"] # Choose a specific row based on the "Location" column (e.g., "Italy")
            if not chosen_row.empty:
                chosen_row = chosen_row.iloc[0]
                url = chosen_row["Url"]
                df2 = pd.read_json(url, lines=True)
                df2["geometry"] = df2["geometry"].apply(shapely.geometry.shape)
                gdf = gpd.GeoDataFrame(df2, crs=4326)
                combined_rows.append(gdf)
            else:
                print(f"No rows found for QuadKey: {quad_key} and Location: Italy")
        else:
            print(f"Warning: QuadKey {quad_key} not found in dataset")

# Concatenate GeoDataFrames obtained for each quad key
concatenated_gdf = gpd.GeoDataFrame(pd.concat(combined_rows, ignore_index=True), crs=4326)

# Create a mask GeoDataFrame for the target municipality
mask = gpd.GeoDataFrame([{"geometry": target_shape}], crs=4326)

# Overlay the concatenated GeoDataFrame with the target municipality mask
overlayed_gdf = gpd.overlay(concatenated_gdf, mask, how="intersection")

# Convert the GeoDataFrame to GeoJSON
geojson_data = overlayed_gdf.to_json()

# Un-nest "properties" key
geojson_data = json.loads(geojson_data)
for feature in geojson_data['features']:
    feature['properties'] = feature['properties']['properties']
    feature['properties'].pop('type', None)

# Save the result
output_geojson_path = f".\{target_name}.geojson"
with open(output_geojson_path, 'w', encoding='utf-8') as output_file:
    json.dump(geojson_data, output_file, ensure_ascii=False, indent=2)
