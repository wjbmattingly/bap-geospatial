import streamlit as st
import leafmap.colormaps as cm
from leafmap.common import hex_to_rgb
import pandas as pd
import pydeck as pdk
import geopandas as gpd
import math
import json

SCATTERPLOT_LAYER_DATA = "https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/bart-stations.json"
df = pd.read_csv("data/data.csv")
data = []
for idx, row in df.iterrows():
    try:
        name = f"{row.First} {row.Last}"
        coords = [float(row.Long), float(row.Lat)]
        address = row.Place
        description = row.Description
        if pd.isnull(row.Long):
            pass
        else:
            data.append({"name": name, "address": address, "description": description, "coordinates": coords})
    except:
        Exception
st.write(len(data))

with open("temp.json", "w") as f:
    json.dump(data, f, indent=4)
# Use pandas to calculate additional data
# df["exits_radius"] = df["exits"].apply(lambda exits_count: math.sqrt(exits_count))
final_df = pd.read_json("temp.json")

final_df['frequency'] = final_df['address'].map(final_df['address'].value_counts())
final_df["radius"] = final_df["frequency"].apply(lambda quantity: quantity*10)
# Define a layer to display on a map
layer = pdk.Layer(
    "ScatterplotLayer",
    final_df,
    pickable=True,
    opacity=0.8,
    stroked=True,
    filled=True,
    radius_scale=6,
    radius_min_pixels=1,
    radius_max_pixels=100,
    line_width_min_pixels=1,
    get_position="coordinates",
    get_radius="radius",
    get_fill_color=[255, 140, 0],
    get_line_color=[0, 0, 0],
)

# Set the viewport location
view_state = pdk.ViewState(longitude=25.975520, latitude=-30.50329, zoom=6, bearing=0, pitch=0)

# Render
r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{name}\n{address}\n{description}"})
# r.to_html("scatterplot_layer.html")
st.pydeck_chart(r)
