from re import L
from PIL import Image
import numpy as np
from scipy import spatial
from . import dataextract

class Similarity:
    def __init__(self,dataextract):
        self.ref = dataextract.ref
        self.com = dataextract.com
        self.sim= None

    def cosine_similarity(self):
        """"
        Calculate the similarity of 2 array
        """
        self.sim = -1 * (spatial.distance.cosine((self.ref.flatten())/255, (self.com.flatten())/255) - 1)
        return self.sim
        
    def new_algorithm(self):
        return

