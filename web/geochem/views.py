import base64
import json
from mimetypes import guess_type
import os
import random
import string
import json
import pandas as pd
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse

from geochem.forms import DatasetUploadForm
from geochem.utils.analyser import Analyser
from geochem.utils.dataclean import  DataCleaner
from geochem.utils.data_utils import selected_columns_with_empty_cells, get_columns_selected, get_columns_containing_text, generate_error_string_ending, training_error_string
from project.models import ProjectMember
from .utils.report import ReportMaker
from media_file.models import MediaFile
from project.models import Project


User = get_user_model()
cleanerFile_url = ""
def id_generator(size=10, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    """Generates a random alphanumeric identifier"""
    return ''.join(random.choice(chars) for _ in range(size))

@login_required
@require_POST
def get_existing_datasets(request):
    """When the user elects to include pre-existing datasets, we have to send them back such that they can choose
    the index, columns and sheets etc."""

    # Note that this is probably not the best way to do it, as sending a large dataset as a base64 string can be
    # a chonky process.
    datasets = request.POST.getlist('datasets', [])
    
    project_memberships = ProjectMember.objects.filter(user=request.user)
    projects = project_memberships.values_list('project', flat=True).distinct()
    uploaded_files = MediaFile.objects.filter(id__in=datasets, project_files__in=projects)

    # Compile content required by the frontend to populate the datatable
    content = [{
        'id': str(dataset.id),
        'name': dataset.filename,
        'size': dataset.file.size,
        'file': base64.b64encode(dataset.file.read()).decode(),
        'mimetype': guess_type(dataset.file.path)[0]
    } for dataset in uploaded_files]

    return HttpResponse(json.dumps(content), content_type='application/json')


@login_required
@require_POST
def handle_dataset_upload(request):
    """Handles the multi-file upload component of the Geochem process. Files are merged together on the 'index' parameter

    Parameters
    ----------
        request : Request
            Expected to be a POST request accompanied with some FILES
        request.POST : MultiDictIndex
            .file : str
                Filename of the associated file in request.FILES
            .index : str
                Index column for creation of the dataframe
            .columns : list[str]
                List of columns to be kept
            .sheet : str
                Name of the sheet that the dataset is on, for use when attempting to upload
                multi-sheet Excel spreadsheets (not applicable for CSV but still exists)
        request.FILES : files[]
            zero indexed 'list' of files, index associated with request.POST entry
            can be in .XLSX, .XLS and .CSV formats.

    Notes
    -----
        Difficult to implement as a django form since the number of files/options are variable, this can be implmeneted
        later, otherwise implement some file type checks (try not to actually open them in case they are malicious)
    """
    filename = request.POST.get('filename')
    project_id = request.POST.get('project')
    datasets = request.POST.getlist('datasets')
    merged = None

    # Count of existing files within upload, no point saving the file if
    pid = None
    existing_file_count = 0

    # POST data stored in a list, cant use json.loads on it like that so have to do it for each entry
    for i, datasetStr in enumerate(datasets):
        data = json.loads(datasetStr)

        # Separate the indices for cleaner looking code
        pid = data.get('pid')
        file = request.FILES[str(i)]
        index = data.get('index')
        columns = data.get('columns')
        header = int(data.get('header'))
        sheet = data.get('sheet')

        if pid:
            existing_file_count += 1

        # Load the files, the user is allowed to upload xlsx, xls and csv files, this should handle all of them
        # Can't check file type using file.content_type since its easy to forge headers, and guess_type doesn't work
        # on in-memory data. Could potentially install the magic library to handle this but the below can handle it
        # well enough.
        try:
            df = pd.read_excel(file, sheet_name=sheet, header=header, index_col=index, usecols=[index] + columns)
        except Exception as e:
            try:
                df = pd.read_csv(file, header=header, index_col=index, usecols=[index] + columns)
            except ValueError as e:
                data = {
                    'error_message': 'Please try upload a dataset file that contains a complete header row and is uncorrupted'
                    }
                return JsonResponse(data, status=400)
            except Exception as e:
                return JsonResponse({'error': e}, status=400)

        # Merge them all together, though if we're the first index, there's nothing to merge yet
        if i == 0:
            merged = df
        else:
            merged = merged.merge(df, how='inner', left_index=True, right_index=True)

    if not merged.empty:
        # Prepare context for dataclean component
        # we get these now as the dataclean options are not to be used on the index column
        
        missing = [{'name': column, 'data': round(value, 5), 'column': column} for column, value in (merged.isnull().sum() / (merged.size/merged.columns.size)).items()]
        types = [{'name': column, 'data': str(value), 'column': column} for column, value in merged.dtypes.items()]

        # Only upload the merged file if the number of incoming datasets is greater than 1
        # or if the number of incoming existing files is 0
        if len(datasets) > 1 or existing_file_count == 0:
            filename += '.csv'
            project = Project.objects.get(id=project_id)
            file = ContentFile(merged.to_csv(index_label=index).encode('utf-8'), filename)

            upload_file = MediaFile(file=file, filename=filename, tag=MediaFile.DATASET)
            upload_file.save()

            project.files.add(upload_file)

            pid = upload_file.id

        # Reset the index
        merged.reset_index(inplace=True)

        # Get all column names for displaying the full dataset table
        columns = [{'data': column, 'title': column} for column in merged.columns.tolist()]

        context = {
            'pid': pid,
            'merged': merged.to_json(orient='records'),
            'columns': json.dumps(columns),
            'missing': json.dumps(missing),
            'types': json.dumps(types),
            'indexCol': index
        }

        return JsonResponse(context, status=200)

    # Bad request if the request is not a post or has files
    return JsonResponse({'status': 'boo'}, status=400)


@login_required
@require_POST
def handle_dataclean(request):
    """Handles the dataclean phase of the Geochem process. Takes a 'file' and utilizes the dataclean functions defined
    in the utils folder

    Parameters
    ----------
        request : Request
            Expected to be a POST request accompanied by some FILES

    Notes
    -----
        Difficult to implement as a django form since the number of files/options are variable, this can be implemented
        later, otherwise implement some file type checks (try not to actually open them in case they are malicious)
    """
    # Load the incoming JSON and turn it merge the list into a dictionary
    try:
        options = {}
        project_id = request.POST.get('project')
        pid = request.POST.get('pid')
        index_col = request.POST.get('index_col')
        project = Project.objects.get(id=project_id)
        dataset = pd.read_csv(MediaFile.objects.get(id=pid).file, index_col=index_col)

        PROJECT_PATH = f"project/{str(project)}"
        PROJECT_FOLDER = f"media_root/media/{PROJECT_PATH}"

        # Deserialize the request data
        for item in request.POST.getlist('data'):
            options.update(json.loads(item))
        # Format the json dicts for use in **kwargs
        for method, contents in options.items():
            # Fun way to get the columns from our check groups
            if contents.get('columnsOption'):
                # Columns could either be a list or dict depending on the number of items selected
                
                col_opt = contents.pop('columnsOption', [])

                if col_opt != []:
                    try:
                        options[method]['columns'] = [k for d in col_opt for k, v in d.items()]
                    except AttributeError:
                        options[method]['columns'] = list(col_opt.keys())

        # Cleans the data, saves it if changes were made and returns the file
        datacleaner = DataCleaner(dataset, options, False)
        cleaned_df = datacleaner.run()
        generated_id = id_generator()
        c_file_filename = f"{generated_id}.csv"

        if not os.path.isdir(PROJECT_FOLDER):
            os.mkdir(PROJECT_FOLDER)

        if not os.path.isdir(f"{PROJECT_FOLDER}/cleaner_files"):
            os.mkdir(f"{PROJECT_FOLDER}/cleaner_files")

        f = open(f"{PROJECT_FOLDER}/cleaner_files/{c_file_filename}", 'x')
        
        cleaned_df.to_csv(path_or_buf=f"{PROJECT_FOLDER}/cleaner_files/{c_file_filename}")
        cleaner_file = MediaFile(file=f"{PROJECT_PATH}/cleaner_files/{c_file_filename}", filename=c_file_filename, tag=MediaFile.CLEANER)
        cleaner_file.save()
        cleanerFile_url = cleaner_file.file.url
        if not os.path.isdir(f"{PROJECT_FOLDER}/reports"):
            os.mkdir(f"{PROJECT_FOLDER}/reports")

        if not os.path.isdir(f"{PROJECT_FOLDER}/reports/cleaner_reports"):
            os.mkdir(f"{PROJECT_FOLDER}/reports/cleaner_reports")

        report = ReportMaker(
            temp_filepath=f"{PROJECT_FOLDER}/reports/cleaner_reports/")

        c_report_filename = f"cleaner_report_{generated_id}.pdf"

        try:
            report.make_cleaner_report(datacleaner=datacleaner,
                            filename=f"{PROJECT_FOLDER}/reports/cleaner_reports/{c_report_filename}",
                            instance_name=f"{str(project)}_{generated_id}", csv_file_url=cleaner_file.file.url)

        except Exception as e:
            data = {
                'error_message': str(e),
            }
            return JsonResponse(data, status=400)

        cleaner_report = MediaFile(file=f"{PROJECT_PATH}/reports/cleaner_reports/{c_report_filename}", tag=MediaFile.CLEANER_REPORT)
        cleaner_report.save()

        types = [{'name': column, 'data': str(value), 'column': column} for column, value in cleaned_df.dtypes.items()]

        columns = [{'data': column, 'title': column} for column in cleaned_df.columns.tolist()]

        context = {
            'columns': json.dumps(columns),
            'types': json.dumps(types),
            'filename': generated_id,
            'cleanerFile': cleaner_file.id,
            'cleanerReport': cleaner_report.id
        }

        return JsonResponse(context, status=200)
    except Exception as e:
        data = {
                'error_message': str(e),
            }
        return JsonResponse(data, status=400)

@login_required
# @require_POST does this require post
def handle_dataanalysis(request):
    """Handles the data analysis phase of the Geochem process. Takes a 'file' and utilizes the dataanalyser functions defined
    in the utils folder

    Parameters
    ----------
        request : Request
            Expected to be a POST request accompanied by some FILES

    Notes
    -----
        Difficult to implement as a django form since the number of files/options are variable, this can be implemented
        later, otherwise implement some file type checks (try not to actually open them in case they are malicious)
    """
    # Load the incoming JSON and turn it merge the list into a dictionary
    options = {}
    project_id = request.POST.get('project')
    pid = request.POST.get('pid')
    cleaner_report_id = request.POST.get('cleanerReport')
    cleaner_file_id = request.POST.get('cleanerFile')
    index_col = request.POST.get('index_col')
    project = Project.objects.get(id=project_id)
    dataset = pd.read_csv(MediaFile.objects.get(id=cleaner_file_id).file, index_col=index_col)

    ANALYSER_REPORTS_FOLDER = f"media_root/media/project/{str(project)}/reports/analyser_reports"

    # Deserialize the request data
    for item in request.POST.getlist('data'):
        options.update(json.loads(item))

    if ('Unnamed: 0' in dataset):
        dataset.drop(columns=['Unnamed: 0'], inplace=True)
    for column in dataset.columns:
        dataset[column] = pd.to_numeric(dataset[column], errors='ignore', downcast="float")
    
    # handling exceptions here as this is a critical part of the geochem process
    try:
        columns_selected = get_columns_selected(options)
        selected_subset = dataset[columns_selected]
        s = selected_subset.select_dtypes(include='object').columns
        dataset[s] = dataset[s].astype("float")
    except ValueError as e:
        error_message = "Columns selected for analysis cannot have cells containing text"

        problem_columns = get_columns_containing_text(dataset)
        error_message += generate_error_string_ending(options, problem_columns)

        data = {
            'error_message': error_message
        }
        
        return JsonResponse(data, content_type="application/json", status=400)

    analyser = Analyser(dataset, str(project), options)

    try:
        cols_with_empty = selected_columns_with_empty_cells(dataset[columns_selected])
        if cols_with_empty:
            raise Exception
        analyser.run()
    except Exception as e:
        training_string = training_error_string(e)
        if training_string:
            error_message = training_string

            data = {
                'error_message': error_message
            }

            return JsonResponse(data, content_type="application/json", status=400)
        
        error_message = "Columns selected for analysis cannot contain empty cells"

        error_message += generate_error_string_ending(options, cols_with_empty)

        data = {
            'error_message': error_message
        }

        return JsonResponse(data, content_type="application/json", status=400)
    
    filename = f"analysis_report_{pid}.pdf"

    if not os.path.isdir(ANALYSER_REPORTS_FOLDER):
        os.mkdir(ANALYSER_REPORTS_FOLDER)
    
    report = ReportMaker(
        temp_filepath=ANALYSER_REPORTS_FOLDER)
    
    try:
        report.make_analysis_report(analyser=analyser,
                        filepath=f"{ANALYSER_REPORTS_FOLDER}/{filename}")
    except Exception as e:
        error_message = str(e)

        if error_message == "All column headers are incorrect.":
            error_message = "Column headers selected for analysis are of incorrect data type"

        data = {
            'error_message': error_message
        }

        return JsonResponse(data, content_type="application/json", status=400)
    
    analysis_report = MediaFile(file=f"project/{str(project)}/reports/analyser_reports/{filename}", filename=filename, tag=MediaFile.ANALYSIS_REPORT)
    analysis_report.save()
    cleaner_report = MediaFile.objects.get(id=cleaner_report_id)
    cleaner_file = MediaFile.objects.get(id=cleaner_file_id)

    data = {
        'cleaning_report': cleaner_report.file.url,
        'analysis_report': analysis_report.file.url,
        'cleaner_file': cleaner_file.file.url
    }
    return JsonResponse(data, content_type="application/json")


@login_required
def geochem_home(request):
    """Renders geochem pages to user"""

    # all ProjectMember relationships of a user
    proj_members = ProjectMember.objects.filter(user=request.user)
    # projects that a user belongs to
    projects = Project.objects.filter(id__in=proj_members.values('project'))
    # all media files related to projects accessible by a user
    related_files = MediaFile.objects.filter(id__in=projects.values('files'), tag=MediaFile.DATASET).values_list('id', 'filename')

    upload_form = DatasetUploadForm(projects=projects)

    return render(request, "geochem/home.html", {
        'upload_form': upload_form,
        'process_files': related_files,
    })

def download_csv(request):
    file_path = cleanerFile_url

    # Check if the file exists
    if not os.path.exists(file_path):
            return HttpResponse("File not found", status=404)

    # Open the file and create a response object
    with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="data.csv"'

    return response