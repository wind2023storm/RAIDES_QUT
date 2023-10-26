from django.http import JsonResponse
import shutil
from django.shortcuts import render
from .geodesk_tmi_model.SampleComparison import runModel


def compare(request):
    template_name = "tmi/compare_tmi.html"

    context = {
    }

    return render(request, template_name, context=context)


def project_area_input_selection(request):
    template_name = "tmi/compare_tmi.html"
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

    modelResult = runModel()
    similarityResult = float(modelResult[0])
    path_to_compared_image = modelResult[1]

    request.session['latitude'] = latitude_selected
    request.session['longitude'] = longitude_selected
    request.session['similarity_result'] = similarityResult
    request.session['path_to_compared_image'] = path_to_compared_image

    template_name = "tmi/compare_tmi.html"
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

    response_data = {'model_result' : model_result, "path_to_compared_image" : path_to_compared_image, "similarity_result" : similarityResult}
    source_file = path_to_compared_image
    destination_folder = "geodesk_tmi/static/tmi/img/to_compare/img.png"
    shutil.copy(source_file, destination_folder)

    return JsonResponse(response_data)

def extract_image(request):
    tileX = request.POST.get('tile_X')
    tileY = request.POST.get('tile_Y')
    zoomLvl = request.POST.get("zoom_lvl")
    print(tileX, tileY)
    source_file = 'geodesk_tmi/static/tmi/img/output/'+zoomLvl+"/"+tileX+"/"+tileY+'.png'
    destination_folder = 'geodesk_tmi/geodesk_tmi_model/selected_sample/img.png'
    display_folder = 'geodesk_tmi/static/tmi/img/to_display/img.png'
    shutil.copy(source_file, destination_folder)
    shutil.copy(source_file, display_folder)
    return JsonResponse({"message": "Image is sent to the model"})



def display_image_update(request):
    return render(request, "selected_image.html")


def store_results(request):
    latitude = request.POST.get("latitude_to_store")
    longitude = request.POST.get("longitude_to_store")
    similarity_result = request.POST.get("similarity_to_store")
    scale = request.POST.get("scale_to_store")
    results = request.session.get('search_results', [])
    results.append({"latitude": latitude, "longitude": longitude, "similarity": similarity_result, "scale": scale})
    sorted_results = sorted(results, key=lambda x: x["similarity"], reverse=True)
    print(sorted_results)
    request.session['search_results'] = sorted_results
    print("data is stored")
    search_results = list(sorted_results)
    return JsonResponse({"message": "Data is stored", "searchResults": search_results})


def retrieve_results(request):
    search_results = request.session.get('search_results', [])
    print ("data retrieved")
    print (search_results)
    return JsonResponse({"searchResults": search_results})


