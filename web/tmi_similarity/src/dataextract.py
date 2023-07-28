from PIL import Image
import numpy as np

class DataExtractor:
    def __init__(self, ref_loc, com_loc):
        self.ref = None
        self.com = None
        self.ref_loc = ref_loc
        self.com_loc = com_loc
        self.get_rgb_array()

    def get_rgb_array(self, type_img ='RGB'):
        ''''
        reference_path: the location that store the (./media_root/media/cropped_tif_files/)
        comparison_path: the location that store the (./media_root/media/cropped_tif_files/)
        type_img: RGBA, RGB
        '''
        img_ref = Image.open(self.ref_loc).convert(type_img)
        img_com = Image.open(self.com_loc).convert(type_img)
        img_ref = img_ref.resize((255,255))
        img_com = img_com.resize((255,255))
        self.ref = np.array(img_ref)
        self.com = np.array(img_com)

        

