import streamlit as st
from multiapp import MultiApp
from apps import (
    device_loc,
    heatmap,
    home,
    plotly_maps,
    raster,
    xy,
)

st.set_page_config(layout="wide")


apps = MultiApp()

# Add all your application here

apps.add_app("Home", home.app)
apps.add_app("Visualize Raster Data", raster.app)
apps.add_app("Heatmaps", heatmap.app)
apps.add_app("Add Points from XY", xy.app)
apps.add_app("Geolocation", device_loc.app)
apps.add_app("Plotly", plotly_maps.app)

# The main app
apps.run()
