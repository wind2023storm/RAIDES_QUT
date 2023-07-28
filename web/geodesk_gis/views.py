import json
import os
import random
import string
from django.http import JsonResponse
from PIL import Image

from django.conf import settings
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from geodesk_gis import models

from mapplotter.apps.preprocessor import Preprocessor
from mapplotter.map_plotter import Map_plotter
from tmi_similarity.src.dataextract import DataExtractor
from tmi_similarity.src.similarity import Similarity

UserModel = get_user_model()

Image.MAX_IMAGE_PIXELS = 502732897

@login_required
def plotter(request):
    """
    Data processor view. Required params:
    project_url,
    data_file=None
    """

    template_name = "gis/map_upload.html"
    all_maps = models.MapFile.objects.all()

    context = {
        "all_maps": all_maps,
    }

    return render(request, template_name, context=context)

def tmi(request):
    
    template_name = "gis/tmi_overlay.html"

    context = {
    }

    return render(request, template_name, context=context)

@login_required
def file_uploader(request):
    if request.method == 'POST':
        data = request.POST
        print(data)
        header_row = int(data.get('header_row')) if data.get('header_row') else None
        if data.get('existing_process_file_id'):
            pf_id = int(data.get('existing_process_file_id'))
            map_file = models.MapFile.objects.get(id = pf_id)
            map_file.header_row=header_row
            map_file.save(update_fields=["header_row"]) 
        else:
            uploaded_file = request.FILES.get('uploaded_file')
            map_file = models.MapFile.objects.create(expected_filename=uploaded_file.name,
                file=uploaded_file, header_row=header_row)

        filepath = map_file.file.path

        data = {
            "file_uploaded": True,
            "filepath": filepath,
            'sheet_names': "h_sample_central_qld.csv",
        }

        return JsonResponse(data, content_type="application/json")

@login_required
def mapplotter(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        filepath = data.get('filepath')

        prepro=Preprocessor()
        df = prepro.preprocessing(filename=filepath)
        latitudeCol, longitudeCol = prepro.get_latitude_and_longitude()
        prepro.create_dataframe()
        prepro.get_element_coordinate()
        elements = prepro.get_elements()
        latitude = []
        longitude = []
        for i in latitudeCol:
            latitude.append(i)
        for i in longitudeCol:
            longitude.append(i)
        data = {
            "elements": elements,
            "latitude": latitude,
            "longitude": longitude
        }

        return JsonResponse(data, content_type="application/json")

def id_generator(size=10, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
    
@login_required
def crop_image(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        filename1 = "crop_"+ id_generator() +".png"
        filename2 = "crop_"+ id_generator() +".png"
        
        if not os.path.isdir('./media_root/media/cropped_tif_files/'):
            os.mkdir('./media_root/media/cropped_tif_files/')

        filepath1 = "./media_root/media/cropped_tif_files/" + filename1
        filepath2 = "./media_root/media/cropped_tif_files/" + filename2
        with Image.open('./gis/static/gis/img/output.png') as im:
            width = 140.9
            widthAdjustment2 = 0
            widthAdjustment1 = 0
            if data['polygon1']['geometry']['coordinates'][0][1][0] < 146.9:
                widthAdjustment1 = 0.4 * (146.9 - data['polygon1']['geometry']['coordinates'][0][1][0])/5.9
            if data['polygon2']['geometry']['coordinates'][0][1][0] < 146.9:
                widthAdjustment2 = 0.4 * (146.9 - data['polygon2']['geometry']['coordinates'][0][1][0])/5.9
            if data['polygon1']['geometry']['coordinates'][0][1][0] > 146.9:
                widthAdjustment1 = -0.37 * ((data['polygon1']['geometry']['coordinates'][0][1][0] - 146.9))/6.6
            if data['polygon2']['geometry']['coordinates'][0][1][0] > 146.9:
                widthAdjustment2 = -0.37 * ((data['polygon2']['geometry']['coordinates'][0][1][0]) - 146.9)/6.6
            widthDiv = 12.7
            height = 28.3
            heightAdj1 = 0
            heightAdj2 = 0
            if data['polygon1']['geometry']['coordinates'][0][1][1] > -32.47:
                heightAdj1 = 0.146 * (data['polygon1']['geometry']['coordinates'][0][1][1] + 32.47)/4.2
            if data['polygon2']['geometry']['coordinates'][0][1][1] > -32.47:
                print("OK")
                heightAdj2 = 0.146 * (data['polygon2']['geometry']['coordinates'][0][1][1] + 32.47)/4.2
            if data['polygon1']['geometry']['coordinates'][0][1][1] < -32.47:
                heightAdj1 = -0.146 * (-32.47 - data['polygon1']['geometry']['coordinates'][0][1][1])/4.8
            if data['polygon2']['geometry']['coordinates'][0][1][1] < -32.47:
                print("OK2")
                heightAdj2 = -0.146 * (-32.47 - data['polygon2']['geometry']['coordinates'][0][1][1])/4.8

            print(heightAdj2)
            print(heightAdj1)
            heightDiv = 9.1
            im_crop1 = im.crop((round(((data['polygon1']['geometry']['coordinates'][0][1][0]-width + widthAdjustment1)/widthDiv)*im.width, 2), round(((abs(data['polygon1']['geometry']['coordinates'][0][1][1])-height + heightAdj1)/heightDiv)*im.height, 3), round(((data['polygon1']['geometry']['coordinates'][0][3][0]-width + widthAdjustment1)/widthDiv)*im.width, 2), round(((abs(data['polygon1']['geometry']['coordinates'][0][3][1])-height + heightAdj1)/heightDiv)*im.height, 3)))
            print(data['polygon1']['geometry']['coordinates'])
            im_crop1.save(fp=filepath1, format='PNG')
            map_file = models.CropFile.objects.create(expected_filename=filename1,
                file=filepath1)
            im_crop2 = im.crop((round(((data['polygon2']['geometry']['coordinates'][0][1][0]-width + widthAdjustment2)/widthDiv)*im.width, 2), round(((abs(data['polygon2']['geometry']['coordinates'][0][1][1])-height + heightAdj2)/heightDiv)*im.height, 3), round(((data['polygon2']['geometry']['coordinates'][0][3][0]-width + widthAdjustment2)/widthDiv)*im.width, 2), round(((abs(data['polygon2']['geometry']['coordinates'][0][3][1])-height + heightAdj2)/heightDiv)*im.height, 3)))
            print(data['polygon2']['geometry']['coordinates'])
            im_crop2.save(fp=filepath2, format='PNG')
            map_file = models.CropFile.objects.create(expected_filename=filename2,
                file=filepath2)
            print(filepath1)
        extractor = DataExtractor(filepath1, filepath2)
        similarity = Similarity(extractor)
        print(similarity.cosine_similarity())

        data = {
            "similarity": similarity.cosine_similarity(),
        }

        return JsonResponse(data, content_type="application/json")

def serve_tif(request):
    
    template_name = "gis/serve_tif.html"

    context = {
        "image": "gis/img/Map.tif",
    }

    return render(request, template_name, context=context)