import streamlit as st
import leafmap.colormaps as cm
from leafmap.common import hex_to_rgb
import pandas as pd
import pydeck as pdk
import geopandas as gpd
import math
import json
import datetime
import dateparser

st.set_page_config(layout="wide")

df = pd.read_csv("data/data_dates.csv")
df = df[:1000]
orgs = []
for idx, row in df.iterrows():
    if pd.isnull(row.ORG):
        pass
    else:
        for org in row.ORG.split("|"):
            if org not in orgs:
                orgs.append(org)
orgs.sort()

selected_orgs = st.multiselect("Select Organization(s)", orgs)
dates_checkbox = st.checkbox("Use Dates?")
if dates_checkbox:
    cols = st.columns(2)
    start_date = cols[0].date_input("Start Date", datetime.date(1980, 7, 6),
                                            min_value=datetime.date(1950, 7, 6),
                                            max_value=datetime.date(2000, 7, 6))
    end_date = cols[1].date_input("End Date", datetime.date(1981, 7, 6),
                                        min_value=datetime.date(1950, 7, 6),
                                        max_value=datetime.date(2000, 7, 6))
else:
    start_date = 0
    end_date = 0

res = df.loc[df.ORG.str.contains("|".join(selected_orgs), na=False)]
data = []
for idx, row in res.iterrows():
    # try:
    # st.write(row.dates)
    # if dates_checkbox:
    if pd.isnull(row.dates):
        pass
    else:
        dates = row.dates.split("|")
        # st.write(dates)
        for date in dates:
            date = dateparser.parse(date).date()
            if (dates_checkbox==False) or (date > start_date and date < end_date):
                name = f"{row.First} {row.Last}"
                coords = [float(row.Long), float(row.Lat)]
                address = row.Place
                description = row.Description
                if pd.isnull(row.Long):
                    pass
                else:

                    data.append({"name": name,
                    "address": address,
                    "description": description,
                    "coordinates": coords,
                    "date": "Date: " + str(date)})


    # except:
    #     Exception
st.write(f"Total Hits: {len(data)}")
if len(data) > 0:
    with open("temp.json", "w") as f:
        json.dump(data, f, indent=4)

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
        radius_max_pixels=1000,
        line_width_min_pixels=1,
        get_position="coordinates",
        get_radius="radius",
        get_fill_color=[255, 140, 0],
        get_line_color=[0, 0, 0],
    )

    # Set the viewport location
    view_state = pdk.ViewState(longitude=25.975520, latitude=-30.50329, zoom=5, bearing=0, pitch=0)

    # Render
    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{date}\n{name}\n{address}\n{description}"})
    # r.to_html("scatterplot_layer.html")
    st.pydeck_chart(r)
    st.write(final_df)
