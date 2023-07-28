#import leafmap.foliumap as leafmap
import pandas as pd
#from apps.preprocessor import Preprocessor


class Map_plotter:
    def __init__(self, dataclean):
        """
        dataclean is from the data that has been proccesed from the preprocesscor
        """
        self.map = None
        self.df= dataclean

    def load_map(self):
        """
        Create the map and add point on the map

        """
        m = leafmap.Map(locate_control= True, plugin_LatLngPopup=False)
        y = "Latitude"
        x = "Longitude"
        # Add custom basemap
        m.add_basemap("HYBRID")
        m.add_basemap("Esri.NatGeoWorldMap")
        m.add_points_from_xy(self.df,x=x, y=y)
        return m


        
        


        
