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

        source_folder = 'output/{}/{}'.format(zoomLvl, tileX)
        source_file = '{}/{}.png'.format(source_folder, tileY)


        # Replace spaces with underscores in the mine_name
        mine_name = mine_name.replace(" ", "_")

        # Replace spaces with hyphens in the mine_name
        mine_name = mine_name.replace(" ", "-")


        destination_folder = 'model_samples'
        destination_filename = '{}/{}.png'.format(destination_folder, mine_name)

        # # Create the destination folder if it doesn't exist
        # os.makedirs(destination_folder, exist_ok=True)
        #
        # # Correct the path separator for Windows
        # source_folder = source_folder.replace("/", "\\")
        # source_file = source_file.replace("/", "\\")
        # destination_folder = destination_folder.replace("/", "\\")
        # destination_filename = destination_filename.replace("/", "\\")

        shutil.copy(source_file, destination_filename)

if __name__ == '__main__':
    # Define your data here as a list of dictionaries, similar to your previous JSON data
    # data = [
    #     # {"name": "Paddington Gold Mine", "tile": {"x": 857, "y": 420, "z": 10}},
    #     # {"name": "Jundee Mine Site", "tile": {"x": 855, "y": 434, "z": 10}},
    #     # {"name": "Yarrie mine", "tile": {"x": 854, "y": 452, "z": 10}},
    #     # {"name": "Marvel Loch Gold Mine", "tile": {"x": 851, "y": 417, "z": 10}},
    #     # {"name": "Red 5 Darlot Gold Mine", "tile": {"x": 856, "y": 429, "z": 10}},
    #     # {"name": "Fortnum Gold Mine", "tile": {"x": 848, "y": 437, "z": 10}},
    #     # {"name": "Mount Tom Price mine", "tile": {"x": 846, "y": 445, "z": 10}},
    #     # {"name": "Nicolsons Gold Mine", "tile": {"x": 874, "y": 458, "z": 10}},
    #     # {"name": "Maitland Mine", "tile": {"x": 853, "y": 433, "z": 10}},
    #     # {"name": "Warriedar Mine", "tile": {"x": 844, "y": 425, "z": 10}},
    #     # {"name": "Kailis Mine Site", "tile": {"x": 856, "y": 426, "z": 10}},
    #     # {"name": "Mulgarrie Mine", "tile": {"x": 857, "y": 421, "z": 10}},
    #     # {"name": "Whundo Mine", "tile": {"x": 844, "y": 450, "z": 10}},
    #     # {"name": "Western Queen Mine", "tile": {"x": 845, "y": 430, "z": 10}},
    #     # {"name": "Mount Caudan Mine", "tile": {"x": 852, "y": 417, "z": 10}},
    #     # {"name": "Tuckabianna Gold Mine", "tile": {"x": 848, "y": 430, "z": 10}},
    #     # {"name": "Reid Find Mine", "tile": {"x": 856, "y": 418, "z": 10}},
    #     # {"name": "Evolution Mining/Barrick Gold Mine", "tile": {"x": 931, "y": 410, "z": 10}},
    #     {"name": "Tarrawonga Coal Mine", "tile": {"x": 939, "y": 420, "z": 10}},
    #     {"name": "Centennial Cooranbong Mine", "tile": {"x": 942, "y": 412, "z": 10}},
    #     {"name": "Golden Gate Gold Mine", "tile": {"x": 942, "y": 417, "z": 10}},
    #     {"name": "Peakhill Open Cut Gold Mine", "tile": {"x": 933, "y": 413, "z": 10}},
    #     {"name": "Canbelego Mine", "tile": {"x": 928, "y": 417, "z": 10}},
    #     {"name": "Ravensworth Mine", "tile": {"x": 941, "y": 414, "z": 10}},
    #     {"name": "Cadia Hill Gold Mine", "tile": {"x": 935, "y": 410, "z": 10}},
    #     {"name": "Integra Underground Coal Mine", "tile": {"x": 941, "y": 414, "z": 10}},
    #     {"name": "Springvale Coal Mine", "tile": {"x": 938, "y": 411, "z": 10}},
    #     {"name": "Bulga Open Cut Mine", "tile": {"x": 941, "y": 413, "z": 10}},
    #     {"name": "Manuka Mine", "tile": {"x": 926, "y": 415, "z": 10}},
    #     {"name": "CSA Mine", "tile": {"x": 926, "y": 417, "z": 10}},
    #     {"name": "BHP Mt Arthur Coal", "tile": {"x": 941, "y": 414, "z": 10}},
    #     {"name": "Drayton Mine", "tile": {"x": 941, "y": 414, "z": 10}},
    #     {"name": "Whitehaven - Rocglen Coal Mine", "tile": {"x": 939, "y": 419, "z": 10}},
    #     {"name": "Cordeaux Mine", "tile": {"x": 940, "y": 407, "z": 10}},
    #     {"name": "Atlas Mine", "tile": {"x": 919, "y": 409, "z": 10}},
    #     {"name": "Beltana Highwall Mine", "tile": {"x": 941, "y": 413, "z": 10}},
    #     {"name": "Glencore - Mount Owen", "tile": {"x": 941, "y": 414, "z": 10}},
    #     {"name": "Boggabri Coal Mine", "tile": {"x": 939, "y": 420, "z": 10}},
    #     {"name": "Swamp Creek Mine", "tile": {"x": 931, "y": 402, "z": 10}},
    #     {"name": "Clean Teq Sunrise Mine", "tile": {"x": 931, "y": 413, "z": 10}},
    #     {"name": "Endeavor Mine", "tile": {"x": 926, "y": 418, "z": 10}},
    #     {"name": "Snapper Mineral Sands Mine", "tile": {"x": 916, "y": 410, "z": 10}},
    #     {"name": "Hunter Valley Operations", "tile": {"x": 941, "y": 414, "z": 10}},
    #     {"name": "Hera Mine", "tile": {"x": 928, "y": 415, "z": 10}},
    #     {"name": "Ginkgo Mine", "tile": {"x": 916, "y": 411, "z": 10}},
    #     {"name": "Duralie Coal", "tile": {"x": 944, "y": 414, "z": 10}},
    #     {"name": "Bulga-Warkworth Mine", "tile": {"x": 941, "y": 413, "z": 10}},
    #     {"name": "Narrabri Coal Mine", "tile": {"x": 938, "y": 420, "z": 10}},
    #     {"name": "Moolarben coal mine", "tile": {"x": 938, "y": 415, "z": 10}}
    # ]

    # data = [
    #     # {"name": "Mulgarrie Mine", "tile": {"x": 428, "y": 213, "z": 9}},
    #     # {"name": "Whundo Mine", "tile": {"x": 428, "y": 210, "z": 9}},
    #     # {"name": "Western Queen Mine", "tile": {"x": 422, "y": 225, "z": 9}},
    #     # {"name": "Mount Caudan Mine", "tile": {"x": 422, "y": 215, "z": 9}},
    #     # {"name": "Tuckabianna Gold Mine", "tile": {"x": 426, "y": 208, "z": 9}},
    #     # {"name": "Reid Find Mine", "tile": {"x": 424, "y": 215, "z": 9}},
    #     # {"name": "Evolution Mining/Barrick Gold Mine", "tile": {"x": 428, "y": 209, "z": 9}},
    #     {"name": "Tarrawonga Coal Mine", "tile": {"x": 465, "y": 205, "z": 9}},
    #     {"name": "Centennial Cooranbong Mine", "tile": {"x": 469, "y": 210, "z": 9}},
    #     {"name": "Golden Gate Gold Mine", "tile": {"x": 471, "y": 206, "z": 9}},
    #     {"name": "Peakhill Open Cut Gold Mine", "tile": {"x": 471, "y": 208, "z": 9}},
    #     {"name": "Canbelego Mine", "tile": {"x": 466, "y": 206, "z": 9}},
    #     {"name": "Ravensworth Mine", "tile": {"x": 464, "y": 208, "z": 9}},
    #     {"name": "Cadia Hill Gold Mine", "tile": {"x": 470, "y": 207, "z": 9}},
    #     {"name": "Integra Underground Coal Mine", "tile": {"x": 467, "y": 205, "z": 9}},
    #     {"name": "Springvale Coal Mine", "tile": {"x": 470, "y": 207, "z": 9}},
    #     {"name": "Bulga Open Cut Mine", "tile": {"x": 469, "y": 205, "z": 9}},
    #     {"name": "Manuka Mine", "tile": {"x": 470, "y": 206, "z": 9}},
    #     {"name": "CSA Mine", "tile": {"x": 463, "y": 207, "z": 9}},
    #     {"name": "BHP Mt Arthur Coal", "tile": {"x": 463, "y": 208, "z": 9}},
    #     {"name": "Drayton Mine", "tile": {"x": 470, "y": 207, "z": 9}},
    #     {"name": "Whitehaven - Rocglen Coal Mine", "tile": {"x": 469, "y": 209, "z": 9}},
    #     {"name": "Cordeaux Mine", "tile": {"x": 470, "y": 203, "z": 9}},
    #     {"name": "Atlas Mine", "tile": {"x": 459, "y": 204, "z": 9}},
    #     {"name": "Beltana Highwall Mine", "tile": {"x": 470, "y": 206, "z": 9}},
    #     {"name": "Glencore - Mount Owen", "tile": {"x": 470, "y": 207, "z": 9}},
    #     {"name": "Boggabri Coal Mine", "tile": {"x": 469, "y": 210, "z": 9}},
    #     {"name": "Swamp Creek Mine", "tile": {"x": 465, "y": 201, "z": 9}},
    #     {"name": "Clean Teq Sunrise Mine", "tile": {"x": 465, "y": 206, "z": 9}},
    #     {"name": "Endeavor Mine", "tile": {"x": 463, "y": 209, "z": 9}},
    #     {"name": "Snapper Mineral Sands Mine", "tile": {"x": 458, "y": 205, "z": 9}},
    #     {"name": "Hunter Valley Operations", "tile": {"x": 470, "y": 207, "z": 9}},
    #     {"name": "Hera Mine", "tile": {"x": 464, "y": 207, "z": 9}},
    #     {"name": "Ginkgo Mine", "tile": {"x": 458, "y": 205, "z": 9}},
    #     {"name": "Duralie Coal", "tile": {"x": 472, "y": 207, "z": 9}},
    #     {"name": "Bulga-Warkworth Mine", "tile": {"x": 470, "y": 206, "z": 9}},
    #     {"name": "Narrabri Coal Mine", "tile": {"x": 469, "y": 210, "z": 9}},
    #     {"name": "Moolarben coal mine", "tile": {"x": 469, "y": 207, "z": 9}},
    # ]

    data = [
        # {"name": "Mulgarrie Mine", "tile": {"x": 1713, "y": 852, "z": 11}},
        # {"name": "Whundo Mine", "tile": {"x": 1715, "y": 842, "z": 11}},
        # {"name": "Western Queen Mine", "tile": {"x": 1689, "y": 901, "z": 11}},
        # {"name": "Mount Caudan Mine", "tile": {"x": 1690, "y": 861, "z": 11}},
        # {"name": "Tuckabianna Gold Mine", "tile": {"x": 1704, "y": 834, "z": 11}},
        # {"name": "Reid Find Mine", "tile": {"x": 1696, "y": 861, "z": 11}},
        # {"name": "Evolution Mining/Barrick Gold Mine", "tile": {"x": 1712, "y": 837, "z": 11}},
        {"name": "Tarrawonga Coal Mine", "tile": {"x": 1862, "y": 820, "z": 11}},
        {"name": "Centennial Cooranbong Mine", "tile": {"x": 1878, "y": 840, "z": 11}},
        {"name": "Golden Gate Gold Mine", "tile": {"x": 1885, "y": 824, "z": 11}},
        {"name": "Peakhill Open Cut Gold Mine", "tile": {"x": 1884, "y": 835, "z": 11}},
        {"name": "Canbelego Mine", "tile": {"x": 1867, "y": 826, "z": 11}},
        {"name": "Ravensworth Mine", "tile": {"x": 1856, "y": 834, "z": 11}},
        {"name": "Cadia Hill Gold Mine", "tile": {"x": 1883, "y": 828, "z": 11}},
        {"name": "Integra Underground Coal Mine", "tile": {"x": 1871, "y": 821, "z": 11}},
        {"name": "Springvale Coal Mine", "tile": {"x": 1883, "y": 828, "z": 11}},
        {"name": "Bulga Open Cut Mine", "tile": {"x": 1877, "y": 822, "z": 11}},
        {"name": "Manuka Mine", "tile": {"x": 1883, "y": 827, "z": 11}},
        {"name": "CSA Mine", "tile": {"x": 1853, "y": 830, "z": 11}},
        {"name": "BHP Mt Arthur Coal", "tile": {"x": 1853, "y": 835, "z": 11}},
        {"name": "Drayton Mine", "tile": {"x": 1882, "y": 829, "z": 11}},
        {"name": "Whitehaven - Rocglen Coal Mine", "tile": {"x": 1882, "y": 829, "z": 11}},
        {"name": "Cordeaux Mine", "tile": {"x": 1878, "y": 839, "z": 11}},
        {"name": "Atlas Mine", "tile": {"x": 1881, "y": 815, "z": 11}},
        {"name": "Beltana Highwall Mine", "tile": {"x": 1839, "y": 818, "z": 11}},
        {"name": "Glencore - Mount Owen", "tile": {"x": 1883, "y": 826, "z": 11}},
        {"name": "Boggabri Coal Mine", "tile": {"x": 1883, "y": 828, "z": 11}},
        {"name": "Swamp Creek Mine", "tile": {"x": 1878, "y": 840, "z": 11}},
        {"name": "Clean Teq Sunrise Mine", "tile": {"x": 1863, "y": 804, "z": 11}},
        {"name": "Endeavor Mine", "tile": {"x": 1862, "y": 826, "z": 11}},
        {"name": "Snapper Mineral Sands Mine", "tile": {"x": 1852, "y": 837, "z": 11}},
        {"name": "Hunter Valley Operations", "tile": {"x": 1832, "y": 821, "z": 11}},
        {"name": "Hera Mine", "tile": {"x": 1856, "y": 830, "z": 11}},
        {"name": "Ginkgo Mine", "tile": {"x": 1833, "y": 822, "z": 11}},
        {"name": "Duralie Coal", "tile": {"x": 1888, "y": 829, "z": 11}},
        {"name": "Bulga-Warkworth Mine", "tile": {"x": 1883, "y": 827, "z": 11}},
        {"name": "Narrabri Coal Mine", "tile": {"x": 1876, "y": 841, "z": 11}},
        {"name": "Moolarben coal mine", "tile": {"x": 1876, "y": 830, "z": 11}},
    ]

    # Call the function with your data
    extract_image(data)