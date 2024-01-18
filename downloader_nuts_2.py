import requests
import shapely.geometry
import mercantile
import pandas as pd
import tempfile
from tqdm import tqdm
import geopandas as gpd
import json

# Fetch and parse NUTS 2 level GeoJson file from GISCO
nuts_2_url = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2021_4326_LEVL_2.geojson"
response = requests.get(nuts_2_url)
nuts_2 = response.json()

# Define the target region
target_name = "Piemonte" # Specify the name of the target region (e.g., "Piemonte")
target_feature = next((feature for feature in nuts_2["features"] if feature["properties"]["NUTS_NAME"] == target_name), None)
if target_feature:
    target_shape = shapely.geometry.shape(target_feature["geometry"])
    minx, miny, maxx, maxy = target_shape.bounds

# Calculate quad keys for tiles covering the bounding box of the target region
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

# Create a mask GeoDataFrame for the target region
mask = gpd.GeoDataFrame([{"geometry": target_shape}], crs=4326)

# Overlay the concatenated GeoDataFrame with the target region mask
overlayed_gdf = gpd.overlay(concatenated_gdf, mask, how="intersection")

# Convert the GeoDataFrame to GeoJson
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
