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
from itertools import chain
from collections import Counter


pd.set_option('display.max_colwidth', 0)
st.set_page_config(layout="wide")

def get_output_data(df):
    columns = [["org", "orgs"], ["place", "places"], ["homeland", "homelands"], ["province", "provinces"], ["hrv", "hrvs"]]
    final_dict = {}
    for column, ss_key in columns:
        temp_df = df[df[column].notna()]
        hits = temp_df[column].tolist()
        uniques = []
        for hit in hits:
            for item in hit:
                if item not in uniques and item != None:
                    uniques.append(item)
        uniques.sort()
        final_dict[column] = uniques
    formatted_text = ""
    for item in final_dict:
        formatted_text = formatted_text+f"**{item.upper()}**(S): {', '.join(final_dict[item])}<br><br>"
    return formatted_text

def filter_df(df, column, selected_list):
    final = []
    for idx, row in df.iterrows():
        # st.write(type(row[column]))
        if str(type(row[column])) == "<class 'numpy.ndarray'>":
            if any(item in selected_list for item in row[column]):
                final.append(row)
    res = pd.DataFrame(final)
    return res

def grab_uniques(df, column):
    items = []
    df = df[df[column].notna()]
    for idx, row in df.iterrows():
        for item in row[column]:
            if item not in items and item != None:
                items.append(item)
    items.sort()
    return items
@st.cache(allow_output_mutation=True)
def load_data():
    data = pd.read_feather("data/full_data")
    dates_only = pd.read_feather("data/dates_only")
    orgs = grab_uniques(data, "org")
    places = grab_uniques(data, "place")
    homelands = grab_uniques(data, "homeland")
    provinces = grab_uniques(data, "province")
    hrvs = grab_uniques(data, "hrv")

    return orgs, places, homelands, provinces, hrvs, data, dates_only

def get_new_lists(df, ignore_column):
    columns = [["org", "orgs"], ["place", "places"], ["homeland", "homelands"], ["province", "provinces"], ["hrv", "hrvs"]]
    for column, ss_key in columns:
        if column != ignore_column:
            temp_df = df[df[column].notna()]
            hits = temp_df[column].tolist()
            uniques = []
            for hit in hits:
                for item in hit.split("|"):
                    if item not in uniques and item != None:
                        uniques.append(item)
            uniques.sort()
            st.session_state[ss_key] = uniques
orgs, places, homelands, provinces, hrvs, full_data, dates_only = load_data()

# param_columns = st.columns(2)
# layers_option = param_columns[0].checkbox("Multiple Layers?", )
# dates_checkbox = param_columns[1].checkbox("Use Dates?")
# if layers_option:
#     num_layers = st.number_input("How many Layers?", 1, 3)
#     layers_select = st.selectbox("Which Layers", [f"Layer {i+1}" for i in range(num_layers)])

def change_sessions(name, data_list, refresh=False):
    if refresh==True:
        st.session_state[name] = data_list
    if name not in st.session_state:
        st.session_state[name] = data_list



layer_nums = st.sidebar.number_input("Select Number of Layers", 1, 3, 1)
selections = []
for layer in range(layer_nums):
    layer = layer+1
    expander_layer = st.sidebar.expander(f"Layer {layer}")
    data_lists = [[f"orgs_{layer}", orgs],
                [f"places_{layer}", places],
                [f"homelands_{layer}", homelands],
                [f"provinces_{layer}", provinces],
                [f"hrvs_{layer}", hrvs]]

    for name, data_list in data_lists:
        change_sessions(name, data_list)

    selected_orgs = expander_layer.multiselect(f"Select Organization(s) for Layer {layer}", st.session_state[f"orgs_{layer}"])
    selected_places = expander_layer.multiselect(f"Select Place(s) for Layer {layer}", st.session_state[f"places_{layer}"])
    selected_homelands = expander_layer.multiselect(f"Select Homeland(s) for Layer {layer}", st.session_state[f"homelands_{layer}"])
    selected_provinces = expander_layer.multiselect(f"Select Province(s) for Layer {layer}", st.session_state[f"provinces_{layer}"])
    selected_hrvs = expander_layer.multiselect(f"Select HRV(s) for Layer {layer}", st.session_state[f"hrvs_{layer}"])
    selections.append({"selected_orgs": selected_orgs,
                        "selected_places": selected_places,
                        "selected_homelands": selected_homelands,
                        "selected_provinces": selected_provinces,
                        "selected_hrvs": selected_hrvs})

dates_checkbox = st.sidebar.checkbox("Use Dates?")
cols = st.sidebar.columns(2)
hits_container = st.container()
dataframe_expander = st.expander("Open to Examine the Data")
    # metadata_expander = st.expander("Open to Examine Connected Data")
# if dates_checkbox:
#     start_date = cols[0].date_input("Start Date", datetime.date(1980, 7, 6),
#                                             min_value=datetime.date(1950, 7, 6),
#                                             max_value=datetime.date(2000, 7, 6))
#     end_date = cols[1].date_input("End Date", datetime.date(1981, 7, 6),
#                                         min_value=datetime.date(1950, 7, 6),
#                                         max_value=datetime.date(2000, 7, 6))
# else:
#     start_date = 0
#     end_date = 0
layer_res = []
if st.sidebar.button("Create Map and Data"):
    layer_data = []
    for layer in range(layer_nums):
        # st.write(layer)
        res = full_data
        if selected_orgs:
            res = filter_df(full_data, "org", selections[layer]["selected_orgs"])
            # st.write(res)
        if selected_places:
            res = filter_df(res, "place", selections[layer]["selected_places"])
            # res = res.loc[res.place.isin(selected_places)]
        if selected_homelands:
            res = filter_df(res, "homeland", selections[layer]["selected_homelands"])
            # res = res.loc[res.homeland.isin(selected_homelands)]
        if selected_provinces:
            res = filter_df(res, "province", selections[layer]["selected_provinces"])
            # res = res.loc[res.province.isin(selected_provinces)]
        if selected_hrvs:
            res = filter_df(res, "hrv", selections[layer]["selected_hrvs"])
        layer_res.append(res)
            # res = res.loc[res.hrv.isin(selected_hrvs)]

        # metadata_connections = get_output_data(res)
        # metadata_expander.markdown(metadata_connections, unsafe_allow_html=True)
        if len(res) > 0:
            hit_ids = res.object_id.tolist()
            if dates_checkbox:
                full_data = full_data[full_data['date_time'].notna()]
                data = full_data.loc[dates_only["object_id"].isin(hit_ids)]
                data = data.loc[data["date_time"] > start_date and data["date_time"] < end_date]
            else:
                data = full_data.loc[full_data["object_id"].isin(hit_ids)]
            hits_container.write(f"Total Hits for Layer {layer+1}: {len(data)}")
            cols2 = st.columns(2)
            if len(data) > 0:
                final_data = json.loads(data[["place", "coordinates"]].to_json())
                final_df = pd.DataFrame(final_data)


                places = final_df.place.tolist()
                frequencies = Counter(chain.from_iterable(places))
                final_df["frequency"] = 1
                for idx, row in final_df.iterrows():
                    final_df.at[idx, "frequency"] = frequencies[row.place[0]]
                    # st.write(row.frequency)

                # st.write(final_df)
                # final_df['frequency'] = final_df['place'].map(final_df['place'].value_counts())
                final_df["radius"] = final_df["frequency"].apply(lambda quantity: quantity*10)
                if layer == 0:
                    line_color=[255, 140, 0]
                elif layer == 1:
                    line_color = [0, 2442, 255]
                elif layer == 2:
                    line_color = [140, 0, 255]

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
                    get_line_color=line_color,
                )
                layer_data.append(layer)

        # Set the viewport location
    view_state = pdk.ViewState(longitude=25.975520, latitude=-30.50329, zoom=5, bearing=0, pitch=0, height=1000)

    # Render
    r = pdk.Deck(layers=layer_data, initial_view_state=view_state, tooltip={"text": "{place} ({frequency})"})

    st.pydeck_chart(r)
    for i, res in enumerate(layer_res):
        dataframe_expander.header(f"Data for Layer {i+1}")
        dataframe_expander.dataframe(res)
else:
    st.markdown("**There are no matches**")
