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
import copy


pd.set_option('display.max_colwidth', 0)
st.set_page_config(layout="wide")

# st.title("BAP SAHA-Infocom Map")
def grab_uniques(df, column):
    items = []
    for idx, row in df.iterrows():
        if pd.isnull(row[column]):
            pass
        else:
            for item in row[column].split("|"):
                if item not in items:
                    items.append(item)
    items.sort()
    return items
@st.cache(allow_output_mutation=True)
def load_data():
    df = pd.read_csv("data/data_cleaned.csv")
    # df = df[:1000]
    df = df[df['place'].notna()]
    df = df[df['long'].notna()]
    df = df[df['lat'].notna()]
    df.index = df.object_id
    orgs = grab_uniques(df, "org")
    places = grab_uniques(df, "place")
    homelands = grab_uniques(df, "homeland")
    provinces = grab_uniques(df, "province")
    hrvs = grab_uniques(df, "hrv")

    data = []
    dates_only = []
    for idx, row in df.iterrows():
        if "-" not in str(row.long):
            # try:
            # st.write(row.dates)
            # if dates_checkbox:
            if pd.isnull(row.date):
                # if dates_checkbox == False:
                name = f"{row.full_name}"
                coords = [float(row.long), float(row.lat)]
                place = row.place
                description = row.description
                data.append({"name": str(name),
                "place": str(place),
                "description": str(description),
                "coordinates": coords,
                "date": "Date: " + "Unknown",
                "id": row.object_id})
                # pass
            else:

                dates = row.date.split("|")
                # st.write(dates)
                for date in dates:
                    date = dateparser.parse(date)
                    if date != None:
                        date = date.date()
                        # if (dates_checkbox==False) or (date > start_date and date < end_date):
                        if pd.isnull(row.long) or pd.isnull(row.lat):
                            pass
                        else:
                            name = f"{row.full_name}"
                            coords = [float(row.long), float(row.lat)]
                            place = row.place
                            description = row.description
                            temp = {"name": str(name),
                            "place": str(place),
                            "description": str(description),
                            "coordinates": coords,
                            "date": "Date: " + str(date),
                            "date_time": date,
                            "id": row.object_id}
                            data.append(temp)
                            dates_only.append(temp)
    return df, orgs, places, homelands, provinces, hrvs, data, dates_only

df, orgs, places, homelands, provinces, hrvs, full_data, dates_only = load_data()

# param_columns = st.columns(2)
# layers_option = param_columns[0].checkbox("Multiple Layers?", )
# dates_checkbox = param_columns[1].checkbox("Use Dates?")
# if layers_option:
#     num_layers = st.number_input("How many Layers?", 1, 3)
#     layers_select = st.selectbox("Which Layers", [f"Layer {i+1}" for i in range(num_layers)])


selected_orgs = st.sidebar.multiselect("Select Organization(s)", orgs)
selected_places = st.sidebar.multiselect("Select Place(s)", places)
selected_homelands = st.sidebar.multiselect("Select Homeland(s)", homelands)
selected_provinces = st.sidebar.multiselect("Select Province(s)", provinces)
selected_hrvs = st.sidebar.multiselect("Select HRV(s)", hrvs)

dates_checkbox = st.sidebar.checkbox("Use Dates?")
cols = st.sidebar.columns(2)
hits_container = st.container()
dataframe_expander = st.expander("Open to Examine the Data")

if dates_checkbox:
    start_date = cols[0].date_input("Start Date", datetime.date(1980, 7, 6),
                                            min_value=datetime.date(1950, 7, 6),
                                            max_value=datetime.date(2000, 7, 6))
    end_date = cols[1].date_input("End Date", datetime.date(1981, 7, 6),
                                        min_value=datetime.date(1950, 7, 6),
                                        max_value=datetime.date(2000, 7, 6))
else:
    start_date = 0
    end_date = 0
res = df
if selected_orgs:
    res = df.loc[df.org.isin(selected_orgs)]
if selected_places:
    res = res.loc[res.place.isin(selected_places)]
if selected_homelands:
    res = res.loc[res.homeland.isin(selected_homelands)]
if selected_provinces:
    res = res.loc[res.province.isin(selected_provinces)]
if selected_hrvs:
    res = res.loc[res.hrv.isin(selected_hrvs)]

hit_ids = res.object_id.tolist()
# st.write(hit_ids)
# st.write(dates_only[0])
if dates_checkbox:
    data = []
    for item in dates_only:
        if "date_time" in item and item["id"] in hit_ids:
            if item["date_time"] > start_date and item["date_time"] < end_date:
                data.append(copy.copy(item))
    for item in data:
        item.pop("date_time")
else:
    data = [copy.copy(item) for item in full_data if item["id"] in hit_ids]
    for item in data:
        if "date_time" in item:
            item.pop("date_time")
    # st.write(data[0])
hits_container.write(f"Total Hits: {len(data)}")
cols2 = st.columns(2)
if len(data) > 0:
    final_df = pd.DataFrame(data)
    final_df = final_df[["place", "coordinates"]]
    final_df['frequency'] = final_df['place'].map(final_df['place'].value_counts())
    final_df["radius"] = final_df["frequency"].apply(lambda quantity: quantity*10)

    layer = pdk.Layer(
        "ScatterplotLayer",
        final_df,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=False,
        radius_scale=6,
        radius_min_pixels=1,
        radius_max_pixels=1000,
        line_width_min_pixels=5,
        get_position="coordinates",
        get_radius="radius",
        get_fill_color=[255, 140, 0],
        get_line_color=[255, 140, 0],
    )

    # Set the viewport location
    view_state = pdk.ViewState(longitude=25.975520, latitude=-30.50329, zoom=5, bearing=0, pitch=0, height=1000)

    # Render
    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{place} ({frequency})"})
    # r.to_html("scatterplot_layer.html")
    st.pydeck_chart(r)
    # display_res = res["Last", "First", "Description"]
    dataframe_expander.dataframe(res)
