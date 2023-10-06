import json
import os
import random
from random import randrange
import string
from django.http import JsonResponse
from PIL import Image
import shutil

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from geodesk_gis import models

from mapplotter.apps.preprocessor import Preprocessor
from tmi_similarity.src.dataextract import DataExtractor
from tmi_similarity.src.similarity import Similarity
from Orefox_ModelDemo.SampleComparison import runModel
import math

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


def compare(request):
    template_name = "gis/compare_tmi.html"

    context = {
    }

    return render(request, template_name, context=context)


def project_area_input_selection(request):
    template_name = "gis/compare_tmi.html"
    if request.method == "POST":
        selected_input_method = request.POST.get("area_selection")
        print("Selected input method:", selected_input_method)

        print("Form data: ", request.POST)

        if selected_input_method == "Upload":
            output_text = "You have selected to upload .shp file"
        elif selected_input_method == "Enter":
            output_text = "You have selected to enter the coordinates"
        elif selected_input_method == "Select":
            output_text = "You have selected to select area on the map"
        else:
            output_text = "No selection has been made stupid"

        return render(request, template_name, context={"output_text": output_text})
    return render(request, template_name, context={})


def output_model_result(request):
    latitude_selected = request.POST.get('latitude')
    longitude_selected = request.POST.get('longitude')
    print(latitude_selected, " ", longitude_selected)
    similarityResult = runModel() * 100
    template_name = "gis/compare_tmi.html"
    # simulated_result = randrange(0, 100, 1)
    result_explanation_1 = "A similarity range of 1% to 15% signifies a very low degree of resemblance between the " \
                           "compared areas."
    result_explanation_2 = "A similarity range of 16% to 30% indicates a relatively low level of resemblance " \
                           "between the compared areas."
    result_explanation_3 = "A similarity range of 31% to 45% signifies a moderate degree of resemblance " \
                           "between the compared areas."
    result_explanation_4 = "A similarity range of 46% to 60% indicates a relatively substantial degree of " \
                           "resemblance between the compared areas."
    result_explanation_5 = "A similarity range of 61% to 75% signifies a significant degree of resemblance " \
                           "between the compared areas."
    result_explanation_6 = "A similarity range of 76% to 90% signifies a very high degree of resemblance " \
                           "between the compared areas."
    result_explanation_7 = "A similarity range of 91% to 100% represents an extremely high level of correspondence " \
                           "and likeness between the compared areas."

    model_result = str(similarityResult) + " %" + " similarity" + " - "

    if similarityResult < 15:
        model_result = model_result + result_explanation_1
    elif similarityResult < 30:
        model_result = model_result + result_explanation_2
    elif similarityResult < 45:
        model_result = model_result + result_explanation_3
    elif similarityResult < 60:
        model_result = model_result + result_explanation_4
    elif similarityResult < 75:
        model_result = model_result + result_explanation_5
    elif similarityResult < 90:
        model_result = model_result + result_explanation_6
    else:
        model_result = model_result + result_explanation_7

    #longitude = longitude_selected #-32.37203571087116 + randrange(1, 50)
    #latitude = latitude_selected # 143.67483653628386 - randrange(1, 50)

    # context = {
    #     'longitude': longitude_selected,
    #     'latitude': latitude_selected,
    #     'model_result': model_result
    # }
    #
    # return render(request, template_name, context)

    print(model_result)

    response_data = {'model_result' : model_result}

    # Return a JSON response
    return JsonResponse(response_data)

def extract_image(request):

    tileX = request.POST.get('tile_X')
    tileY = request.POST.get('tile_Y')
    print(tileX, tileY)
    source_file = 'geodesk_gis/static/gis/img/output/10/'+tileX+"/"+tileY+'.png'
    destination_folder = 'Orefox_ModelDemo/selected_sample/img.png'
    display_folder = 'geodesk_gis/static/gis/img/to_display/img.png'
    shutil.copy(source_file, destination_folder)
    shutil.copy(source_file, display_folder)
    return JsonResponse({"message": "Image is sent to the model"})

def display_image_update(request):
    return render(request, "selected_image.html")

@login_required
def file_uploader(request):
    if request.method == 'POST':
        data = request.POST
        print(data)
        header_row = int(data.get('header_row')) if data.get('header_row') else None
        if data.get('existing_process_file_id'):
            pf_id = int(data.get('existing_process_file_id'))
            map_file = models.MapFile.objects.get(id=pf_id)
            map_file.header_row = header_row
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

        prepro = Preprocessor()
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
        filename1 = "crop_" + id_generator() + ".png"
        filename2 = "crop_" + id_generator() + ".png"

        if not os.path.isdir('./media_root/media/cropped_tif_files/'):
            os.mkdir('./media_root/media/cropped_tif_files/')

        filepath1 = "./media_root/media/cropped_tif_files/" + filename1
        filepath2 = "./media_root/media/cropped_tif_files/" + filename2
        with Image.open('./gis/static/gis/img/output.png') as im:
            width = 140.9
            widthAdjustment2 = 0
            widthAdjustment1 = 0
            if data['polygon1']['geometry']['coordinates'][0][1][0] < 146.9:
                widthAdjustment1 = 0.4 * (146.9 - data['polygon1']['geometry']['coordinates'][0][1][0]) / 5.9
            if data['polygon2']['geometry']['coordinates'][0][1][0] < 146.9:
                widthAdjustment2 = 0.4 * (146.9 - data['polygon2']['geometry']['coordinates'][0][1][0]) / 5.9
            if data['polygon1']['geometry']['coordinates'][0][1][0] > 146.9:
                widthAdjustment1 = -0.37 * (data['polygon1']['geometry']['coordinates'][0][1][0] - 146.9) / 6.6
            if data['polygon2']['geometry']['coordinates'][0][1][0] > 146.9:
                widthAdjustment2 = -0.37 * ((data['polygon2']['geometry']['coordinates'][0][1][0]) - 146.9) / 6.6
            widthDiv = 12.7
            height = 28.3
            heightAdj1 = 0
            heightAdj2 = 0
            if data['polygon1']['geometry']['coordinates'][0][1][1] > -32.47:
                heightAdj1 = 0.146 * (data['polygon1']['geometry']['coordinates'][0][1][1] + 32.47) / 4.2
            if data['polygon2']['geometry']['coordinates'][0][1][1] > -32.47:
                print("OK")
                heightAdj2 = 0.146 * (data['polygon2']['geometry']['coordinates'][0][1][1] + 32.47) / 4.2
            if data['polygon1']['geometry']['coordinates'][0][1][1] < -32.47:
                heightAdj1 = -0.146 * (-32.47 - data['polygon1']['geometry']['coordinates'][0][1][1]) / 4.8
            if data['polygon2']['geometry']['coordinates'][0][1][1] < -32.47:
                print("OK2")
                heightAdj2 = -0.146 * (-32.47 - data['polygon2']['geometry']['coordinates'][0][1][1]) / 4.8

            print(heightAdj2)
            print(heightAdj1)
            heightDiv = 9.1
            im_crop1 = im.crop((round(((data['polygon1']['geometry']['coordinates'][0][1][
                                            0] - width + widthAdjustment1) / widthDiv) * im.width, 2), round(((abs(
                data['polygon1']['geometry']['coordinates'][0][1][1]) - height + heightAdj1) / heightDiv) * im.height,
                                                                                                             3), round((
                                                                                                                               (
                                                                                                                                       data[
                                                                                                                                           'polygon1'][
                                                                                                                                           'geometry'][
                                                                                                                                           'coordinates'][
                                                                                                                                           0][
                                                                                                                                           3][
                                                                                                                                           0] - width + widthAdjustment1) / widthDiv) * im.width,
                                                                                                                       2),
                                round(((abs(data['polygon1']['geometry']['coordinates'][0][3][
                                                1]) - height + heightAdj1) / heightDiv) * im.height, 3)))
            print(data['polygon1']['geometry']['coordinates'])
            im_crop1.save(fp=filepath1, format='PNG')
            map_file = models.CropFile.objects.create(expected_filename=filename1,
                                                      file=filepath1)
            im_crop2 = im.crop((round(((data['polygon2']['geometry']['coordinates'][0][1][
                                            0] - width + widthAdjustment2) / widthDiv) * im.width, 2), round(((abs(
                data['polygon2']['geometry']['coordinates'][0][1][1]) - height + heightAdj2) / heightDiv) * im.height,
                                                                                                             3), round((
                                                                                                                               (
                                                                                                                                       data[
                                                                                                                                           'polygon2'][
                                                                                                                                           'geometry'][
                                                                                                                                           'coordinates'][
                                                                                                                                           0][
                                                                                                                                           3][
                                                                                                                                           0] - width + widthAdjustment2) / widthDiv) * im.width,
                                                                                                                       2),
                                round(((abs(data['polygon2']['geometry']['coordinates'][0][3][
                                                1]) - height + heightAdj2) / heightDiv) * im.height, 3)))
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
