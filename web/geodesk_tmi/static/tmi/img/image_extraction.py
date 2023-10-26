import shutil
import json
import os

##########Image extraction for the model

def extract_image(data):
    for entry in data:
        tileX = entry['tile']['x']
        tileY = entry['tile']['y']
        zoomLvl = entry['tile']['z']
        mine_name = entry['name']

        source_folder = '/geodesk_tmi/static/tmi/img/output/{}/{}/{}'.format(zoomLvl, tileX, tileY)
        source_file = '{}/{}.png'.format(source_folder, tileY)

        destination_folder = 'geodesk_tmi/geodesk_tmi_model/model_samples/'
        destination_filename = '{}/{}.png'.format(destination_folder, mine_name)

        # # Create the destination folder if it doesn't exist
        # os.makedirs(destination_folder, exist_ok=True)

        # # Correct the path separator for Windows
        # source_folder = source_folder.replace("/", "\\")
        # source_file = source_file.replace("/", "\\")
        # destination_folder = destination_folder.replace("/", "\\")
        # destination_filename = destination_filename.replace("/", "\\")

        shutil.copy(source_file, destination_filename)


if __name__ == '__main__':
    # Define your data here as a list of dictionaries, similar to your previous JSON data
    data = [
        # {"name": "Paddington Gold Mine", "tile": {"x": 857, "y": 420, "z": 10}},
        # {"name": "Jundee Mine Site", "tile": {"x": 855, "y": 434, "z": 10}},
        # {"name": "Yarrie mine", "tile": {"x": 854, "y": 452, "z": 10}},
        # {"name": "Marvel Loch Gold Mine", "tile": {"x": 851, "y": 417, "z": 10}},
        # {"name": "Red 5 Darlot Gold Mine", "tile": {"x": 856, "y": 429, "z": 10}},
        # {"name": "Fortnum Gold Mine", "tile": {"x": 848, "y": 437, "z": 10}},
        # {"name": "Mount Tom Price mine", "tile": {"x": 846, "y": 445, "z": 10}},
        # {"name": "Nicolsons Gold Mine", "tile": {"x": 874, "y": 458, "z": 10}},
        # {"name": "Maitland Mine", "tile": {"x": 853, "y": 433, "z": 10}},
        # {"name": "Warriedar Mine", "tile": {"x": 844, "y": 425, "z": 10}},
        # {"name": "Kailis Mine Site", "tile": {"x": 856, "y": 426, "z": 10}},
        # {"name": "Mulgarrie Mine", "tile": {"x": 857, "y": 421, "z": 10}},
        # {"name": "Whundo Mine", "tile": {"x": 844, "y": 450, "z": 10}},
        # {"name": "Western Queen Mine", "tile": {"x": 845, "y": 430, "z": 10}},
        # {"name": "Mount Caudan Mine", "tile": {"x": 852, "y": 417, "z": 10}},
        # {"name": "Tuckabianna Gold Mine", "tile": {"x": 848, "y": 430, "z": 10}},
        # {"name": "Reid Find Mine", "tile": {"x": 856, "y": 418, "z": 10}},
        {"name": "Evolution Mining/Barrick Gold Mine", "tile": {"x": 931, "y": 410, "z": 10}},
        {"name": "Tarrawonga Coal Mine", "tile": {"x": 939, "y": 420, "z": 10}},
        {"name": "Centennial Cooranbong Mine", "tile": {"x": 942, "y": 412, "z": 10}},
        {"name": "Golden Gate Gold Mine", "tile": {"x": 942, "y": 417, "z": 10}},
        {"name": "Peakhill Open Cut Gold Mine", "tile": {"x": 933, "y": 413, "z": 10}},
        {"name": "Canbelego Mine", "tile": {"x": 928, "y": 417, "z": 10}},
        {"name": "Ravensworth Mine", "tile": {"x": 941, "y": 414, "z": 10}},
        {"name": "Cadia Hill Gold Mine", "tile": {"x": 935, "y": 410, "z": 10}},
        {"name": "Integra Underground Coal Mine", "tile": {"x": 941, "y": 414, "z": 10}},
        {"name": "Springvale Coal Mine", "tile": {"x": 938, "y": 411, "z": 10}},
        {"name": "Bulga Open Cut Mine", "tile": {"x": 941, "y": 413, "z": 10}},
        {"name": "Manuka Mine", "tile": {"x": 926, "y": 415, "z": 10}},
        {"name": "CSA Mine", "tile": {"x": 926, "y": 417, "z": 10}},
        {"name": "BHP Mt Arthur Coal", "tile": {"x": 941, "y": 414, "z": 10}},
        {"name": "Drayton Mine", "tile": {"x": 941, "y": 414, "z": 10}},
        {"name": "Whitehaven - Rocglen Coal Mine", "tile": {"x": 939, "y": 419, "z": 10}},
        {"name": "Cordeaux Mine", "tile": {"x": 940, "y": 407, "z": 10}},
        {"name": "Atlas Mine", "tile": {"x": 919, "y": 409, "z": 10}},
        {"name": "Beltana Highwall Mine", "tile": {"x": 941, "y": 413, "z": 10}},
        {"name": "Glencore - Mount Owen", "tile": {"x": 941, "y": 414, "z": 10}},
        {"name": "Boggabri Coal Mine", "tile": {"x": 939, "y": 420, "z": 10}},
        {"name": "Swamp Creek Mine", "tile": {"x": 931, "y": 402, "z": 10}},
        {"name": "Clean Teq Sunrise Mine", "tile": {"x": 931, "y": 413, "z": 10}},
        {"name": "Endeavor Mine", "tile": {"x": 926, "y": 418, "z": 10}},
        {"name": "Snapper Mineral Sands Mine", "tile": {"x": 916, "y": 410, "z": 10}},
        {"name": "Hunter Valley Operations", "tile": {"x": 941, "y": 414, "z": 10}},
        {"name": "Hera Mine", "tile": {"x": 928, "y": 415, "z": 10}},
        {"name": "Ginkgo Mine", "tile": {"x": 916, "y": 411, "z": 10}},
        {"name": "Duralie Coal", "tile": {"x": 944, "y": 414, "z": 10}},
        {"name": "Bulga-Warkworth Mine", "tile": {"x": 941, "y": 413, "z": 10}},
        {"name": "Narrabri Coal Mine", "tile": {"x": 938, "y": 420, "z": 10}},
        {"name": "Moolarben coal mine", "tile": {"x": 938, "y": 415, "z": 10}}
    ]

    # Call the function with your data
    extract_image(data)