import leafmap.foliumap as leafmap
import pandas as pd
import streamlit as st
from apps.preprocessor import Preprocessor

import os

def app():

    prepro=Preprocessor()
    st.title("Add Points from XY")
    option = st.selectbox(
        "How would you like to upload the data",
        ("Link","Uploaed File")
    )
    m = leafmap.Map(locate_control=True, plugin_LatLngPopup=False)
    # Add custom basemap
    m.add_basemap("HYBRID")
    m.add_basemap("Esri.NatGeoWorldMap")

    if option == "Link":
        url = st.text_input("Enter URL:")
        if url != None:
            try:
                df = prepro.preprocessing(url)
            except Exception as e:
                st.write("*Please input the URL")
    elif option == "Uploaed File":
        data = st.file_uploader(
        "Upload a dataset", type=["csv"]
        )
        if data != None:
            try:
                df = prepro.preprocessing(data)
            except Exception as e:
                st.write("*Please Uploaded data")
    submit = st.button("Submit")

    try:
        if submit:
            columns = df.columns.values.tolist()
            row1_col1, row1_col2, row1_col3, row1_col4, row1_col5 = st.columns(
                [1, 1, 3, 2, 2]
            )

            lon_index = 0
            lat_index = 0

            for col in columns:
                if col.lower() in ["lon", "longitude", "long", "lng"]:
                    lon_index = columns.index(col)
                elif col.lower() in ["lat", "latitude"]:
                    lat_index = columns.index(col)

            with row1_col1:
                x = st.selectbox("Select longitude column", columns, lon_index)

            with row1_col2:
                y = st.selectbox("Select latitude column", columns, lat_index)

            with row1_col3:
                popups = st.multiselect("Select popup columns", columns, columns)

            with row1_col4:
                heatmap = st.checkbox("Add heatmap")
                filter = st.checkbox("Filter")

            if heatmap:
                with row1_col5:
                    if "pop_max" in columns:
                        index = columns.index("pop_max")
                    else:
                        index = 0
                    heatmap_col = st.selectbox("Select heatmap column", columns, index)
                    try:
                        m.add_heatmap(df, y, x, heatmap_col)
                    except:
                        st.error("Please select a numeric column")
    

            try:
                print(type(popups))
                m.add_points_from_xy(df, x, y, popups)
            except:
                st.error("Please select a numeric column")


            m.to_streamlit()
    except:
        st.error("Please uploaded the data or insert the link first ")




