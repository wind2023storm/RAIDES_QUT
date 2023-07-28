
  
function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie != '') {
        let cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, 10) === ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

function convert_filesize(value) {
    /* Just converts file size into readable format, base unit is bytes */
    let base = 1
    let unit = 'B'

    if (value < Math.pow(2, 20)) {
        base = Math.pow(2, 10)
        unit = 'KB'
    } else if (value < Math.pow(2, 30)) {
        base = Math.pow(2, 20)
        unit = 'MB'
    } else if (value < Math.pow(2, 40)) {
        base = Math.pow(2, 30)
        unit = 'GB'
    } else if (value >= Math.pow(2, 40)) {
        base = Math.pow(2, 40)
        unit = 'TB'
    }

    return (value / base).toFixed(2) + unit;
}

function dataCleanForm_prev_tab() {
    /* Activates the previous tab in the navigation tabs */
    let tabHeader = $('#nav-tab .active')
    let tabContent = $('#nav-primary .active')
    let table = $('#mergedData');

    table.DataTable().clear().destroy();
    table.empty();
    tabHeader.removeClass('active');
    tabContent.removeClass('active');
    tabHeader.prev('.nav-item').addClass('active');
    tabContent.prev('.tab-pane').addClass('active');
}

function prev_tab() {
    /* Activates the previous tab in the navigation tabs */
   // alert("hello")
   // let dataTable = $(this).find('#mergedData').DataTable();
  // $('#mergedData').DataTable().clear().draw()
    let tabHeader = $('#nav-tab .active')
    let tabContent = $('#nav-primary .active')
    let table = $('#mergedData');

    table.DataTable().clear().destroy();
    table.empty();
    tabHeader.removeClass('active');
    tabContent.removeClass('active');
    tabHeader.prev('.nav-item').addClass('active');
    tabContent.prev('.tab-pane').addClass('active');
}

function prev_tab() {
    /* Activates the previous tab in the navigation tabs */
    let tabHeader = $('#nav-tab .active')
    let tabContent = $('#nav-primary .active')
    tabHeader.removeClass('active');
    tabContent.removeClass('active');
    tabHeader.prev('.nav-item').addClass('active');
    tabContent.prev('.tab-pane').addClass('active');
    
}

function next_tab() {
    /* Activates the next tab in the navigation tabs */
    let tabHeader = $('#nav-tab .active')
    let tabContent = $('#nav-primary .active')

    tabHeader.removeClass('active');
    tabContent.removeClass('active');
    tabHeader.next('.nav-item').addClass('active');
    tabContent.next('.tab-pane').addClass('active');
    topFunction(); // code is in appboard.css
}

function restart() {
    /* Activates the next tab in the navigation tabs */
    datasetFiles.clearData();
    $("#datacleanFormOptions").find("form").each(function() {
     
        this.reset(); // 'this' refers to the DOM element of the form
    }); 
    $("#datacleanFormOptions").find("input.include").each(function() {$(this).val("0"); })
    $("#dataAnalysisFormOptions").find("form").each(function() {        
        this.reset(); // 'this' refers to the DOM element of the form
    }); $("#dataAnalysisFormOptions").find("input.include").each(function() {$(this).val("0"); })
    $(" .card-header").each(function() {
        $(this).removeClass("functionIncluded");
        $(this).removeClass("functionNotIncluded");
    });
    $(" .card").each(function() {
        $(this).removeClass("borderfunctionIncluded");
        $(this).removeClass("borderfunctionNotIncluded");
    });
    $("#uploadForm")[0].reset()
  
    location.reload()

}

function get_dataset_preview(sheet, header = 0, columns = '!ref', showRows = 10) {
    /* Returns a dataset as an HTML table preview */
    /* alternatively we can use XLSX.utils.sheet_to_html() but it's limited in options available */
    let html = '';
    let range = XLSX.utils.decode_range(sheet['!ref']);

    let cell;

    html += '<tbody>';
    for (let R = range.s.r; R <= range.e.r; R++) {

        /* If the row is 'less' than the header it will be gray, if it is the header, blue border and text */
        html += `<tr ${R === header ? 'class="bd-ofx-blue bg-ofx-blue text-ofx-light"' : R < header ? 'class="text-ofx-gray"' : ''}><td>${R}</td>`;

        /* Now add the cell values to each column */
        for (let C = range.s.c; C <= range.e.c; C++) {

            try {
                cell = sheet[XLSX.utils.encode_cell({c: C, r: R})].v;
            } catch (e) {
                cell = '';
            } finally {
                html += `<td>${cell}</td>`
            }
        }

        html += `</tr>`;
    }
    html += '</tbody>';

    return html;
}

function get_sheet_headers(sheet, headerRow) {
    /* Attempts to find the header row and retrieves both the row number and header column names */
    const dummyValue = '#EMPTY_'
    let headers = []
    let range = XLSX.utils.decode_range(sheet['!ref']);

    /* SheetJS has fun ways of declaring certain attributes of a sheet
    range.s.c is equal to the start column and range.e.c is the end column */
    let R = parseInt(headerRow);
    let C = range.s.c;
    let cell;

    // Collect the header names
    do {
        cell = sheet[XLSX.utils.encode_cell({c: C, r: R})]

        /* Spreadsheets don't have a value attribute on empty cells so handle by inputting dummy value */
        try {
            headers.push(cell.v);
        } catch (e) {
            headers.push(dummyValue + C);
        } finally {
            C += 1;
        }

        /* If there are more undefined cells than not in the row, it's probably not the header
        * row we're looking for */
        let countUndefined = headers.filter(e => {
            return String(e).includes(dummyValue)
        }).length;
        let countDefined = headers.length - countUndefined;

        if (countUndefined > countDefined) {
            headers = [];
            R += 1;
            C = range.s.c;
        }

    } while (C <= range.e.c && R <= range.e.r)

    // TODO: Handle when a header row is not found

    return [headers, R];
}

function populate_index_column_selects(headers, indexSelect, columnSelect) {
    /* Populate index and column select fields */
    indexSelect.children('option').remove();
    columnSelect.children('option').remove();

    $.each(headers, function (index, value) {
        let indexOption = $('<option>', {value: value, text: value})
        let columnOption = $('<option>', {value: value, text: value, selected: true})

        /* Set the first item as selected, and disable the first column as it's needed */
        if (index === 0) {
            indexOption.prop('selected', true);
            columnOption.prop('disabled', true);
        }

        /* Add them to the select fields */
        indexSelect.append(indexOption)
        columnSelect.append(columnOption)
    })
}

/* General JS */
(function ($, undefined) {
    '$:nomunge'; // Used by YUI compressor.

    $.fn.serializeObject = function () {
        let obj = $(this);
        let fields = {};
        let groups = {};

        $.each(this.serializeArray(), function (i, o) {
            let name = o.name;
            let value = o.value;

            let element = $(obj.find(`[name="${name}"]`).first());
            let group = element.data('group');

            if (group) {
                value = {[name]: value}
                groups[group] = groups[group] === undefined ? value
                    : $.isArray(groups[group]) ? groups[group].concat(value)
                        : [groups[group], value];
            } else {
                fields[name] = fields[name] === undefined ? value
                    : $.isArray(fields[name]) ? fields[name].concat(value)
                        : [fields[name], value];
            }
        });

        return Object.assign({}, fields, groups);
    };
})(jQuery);

function clear_existing_datasets_dropdown() {
    let dropdown = document.getElementById("bs-select-1");
    dropdown_children = dropdown.childNodes[0];

    let foo = (node) => {
        let classAttribute = node.getAttribute('class');

        if (classAttribute != null && classAttribute.includes('selected')) {
            node.classList.remove("selected");
        }
    };

    dropdown_children.childNodes.forEach(foo);
}

/* FILE UPLOAD JS */

/* DataTransfer object where datasets are stored */
const datasetFiles = new DataTransfer();

/* For some reason this stops data tables from doing weird stuff with other page js interactions */


$(document).ready(function () {
  
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        alert("tab2")
        $($.fn.dataTable.tables(true)).DataTable()
            .columns.adjust();
    });
    $('#dataset-table').DataTable({
        'ordering': false,
        'searching': false,
        'stateSave': false,
        'info': false,
        'bPaginate': false,                
        'autoWidth': true,
        "responsive": true,
        'columnDefs': [
             { targets: [5], className: 'noowrap' }
        ],
        
        'columns': [
            {
                data: 'dataset',
                render: function (file, type, row, index) {

                    let pid = (file.id) ? `<input type="text" name="pid" value="${file.id}">` : '';

                    // If we haven't got a filename in the filename field, run for first item in thing
                    if (index.row === 0) {
                        let filenameField = $('#filename');

                        if (!filenameField.val()) {
                            let fileNameIndex = file.name.lastIndexOf("/") + 1;
                            let dotIndex = file.name.lastIndexOf('.');
                            let output = file.name.substr(fileNameIndex, dotIndex < fileNameIndex ? file.name.length : dotIndex);

                            filenameField.val(output);
                        }
                    }

                    return `<span name="${file.name}" class="mh-100">${file.name} <span class="text-xs text-muted float-right">${convert_filesize(file.size)}</span>${pid}`;
                }
            },
            {
                data: 'sheet',
                defaultContent: `<select class="selectpicker border" data-style="btn-ofx-light" data-type="sheet" name="sheet">`
            },
            {
                data: 'header',
                defaultContent: `<input class="form-control" type="number" data-style="btn-ofx-light" name="header" value=0>`
            },
            {
                data: 'index',
                defaultContent: `<select class="selectpicker border" data-style="btn-ofx-light" data-type="index" name="index">`
            },
            {
                data: 'columns',
                 defaultContent: `<select class="selectpicker border" data-style="btn-ofx-light" data-type="columns" name="columns" multiple>`
            },
            {
                data: 'actions',
                defaultContent:
                    `<button type="button" class="btn btn-sm float-right btn-ofx-fa-red datasetdelete" data-toggle="tooltip" data-placement="left" title="Remove">
                                <span class="fa fa-trash"></span>
                            </button>
                            <button type="button" class="btn btn-sm float-right btn-ofx-fa-blue previewdataset" data-toggle="tooltip" data-placement="left" title="Preview Dataset">
                                <span class="fa fa-search"></span>
                            </button>`
            },
        ],
        createdRow: function (row, data, dataIndex, cells) {

            /* Find the sheet options, since they weren't passed in with other data you have to access their
            contents using jquery selectors */
            let sheetSelect = $(cells[1]).find('select');
            let headerInput = $(cells[2]).find('input');
            let indexSelect = $(cells[3]).find('select');
            let columnSelect = $(cells[4]).find('select');

            let reader = new FileReader();

            reader.onload = function (e) {
                let data = e.target.result;
                let workbook = XLSX.readFile(data);

                /* Populate the sheet select field */
                $(workbook.SheetNames).each(function () {
                    sheetSelect.append($('<option>', {value: this, text: this}));
                })


                /* Get the sheet headers */
                let [headers, headerRow] = get_sheet_headers(workbook.Sheets[sheetSelect.val()], headerInput.val())

                headerInput.val(headerRow);

                /* Populate index and column select fields */
                populate_index_column_selects(headers, indexSelect, columnSelect);

                /* Render the 'select picker' for the above items */
                $(row).find('.selectpicker').selectpicker('render');
            }
            reader.readAsArrayBuffer(datasetFiles.items[dataIndex].getAsFile())
        }
    });
});

/* Dataset Table interactions */
$(document).on('change', '#dataset-table input, #dataset-table select', function () {
    /* Get some information about the element and its row */
    let elementName = $(this).attr('name');
    let row = $(this).parents('#dataset-table').DataTable().row($(this).closest('tr'));
    let rowIndex = row.index();

    /* Get the select fields in the table row */
    let sheetSelect = $(row.cell(rowIndex, 1).node()).find('select');
    let headerInput = $(row.cell(rowIndex, 2).node()).find('input');
    let indexSelect = $(row.cell(rowIndex, 3).node()).find('select');
    let columnSelect = $(row.cell(rowIndex, 4).node()).find('select');

    /* Begin operations on the dataset */
    let reader = new FileReader();

    reader.onload = function (e) {
        let data = e.target.result;
        let workbook = XLSX.readFile(data);

        /* Do different stuff depending on the element changed */
        switch (elementName) {
            /* Ignore the fallthrough error here, it's intentional */
            case 'sheet':
                headerInput.val(0);
            case 'header':
                let [headers, headerRow] = get_sheet_headers(workbook.Sheets[sheetSelect.val()], headerInput.val());

                headerInput.val(headerRow);
                populate_index_column_selects(headers, indexSelect, columnSelect);
                break;
            case 'index':
                let currentIndex = indexSelect.find('option:selected').text();

                /* If the index was changed, re-enable the column if it was disabled before */
                columnSelect.find('option').each(function () {
                    if (currentIndex === this.value) {
                        $(this).prop({disabled: true, selected: true})
                    } else {
                        $(this).prop({disabled: false})
                    }
                })
                break;
            default:
                return false;
        }

        /* Refresh the select pickers in the row */
        $(row.node()).find('select').selectpicker('refresh');
    }

    reader.readAsArrayBuffer(datasetFiles.items[rowIndex].getAsFile());
})

$(document).on('click', '.datasetdelete', function (e) {
    /* Hide the tooltip first, it bugs out otherwise */
    $(this).tooltip('hide');

    /* Get the row and table */
    let row = $(this).closest('tr').get(0);
    let dataTable = $('#dataset-table').dataTable()
    let rowIndex = dataTable.fnGetPosition(row);
    let datasetName = row.childNodes[0].childNodes[0].getAttribute('name');

    /* Delete the row and the file stored in the DataTransfer object */
    datasetNames = datasetNames.filter(name => name !== datasetName);
    dataTable.fnDeleteRow(rowIndex);
    datasetFiles.items.remove(rowIndex);
    if(dataTable.DataTable().rows().count() >0)
    $("#upload-merge").attr("disabled",false)
  else
  $("#upload-merge").attr("disabled",true)
})

$(document).on('click', '.previewdataset', function (e) {
    $(this).tooltip('hide');

    let row = $(this).closest('tr');
    let dataTable = $('#dataset-table').dataTable()
    let sheetName = row.find('select[name="sheet"]').val();
    let headerRow = row.find('input[name="header"]').val();
    let columns = row.find('select[name="columns"]').val();
    let rowIndex = dataTable.fnGetPosition(row.get(0));
    let previewTable = $('#previewDatasetModal #previewTable');

    $('#previewDatasetModal').modal('toggle');

    let reader = new FileReader();
    reader.onload = function (e) {
        let data = e.target.result;
        let workbook = XLSX.readFile(data);

        previewTable.html(get_dataset_preview(workbook.Sheets[sheetName], headerRow, columns));
    }
    reader.readAsArrayBuffer(datasetFiles.items[rowIndex].getAsFile());

    return false;
});

// Dataset preview close button functionality
$(document).on('click', '#previewDatasetClose', () => {
    $('#previewDatasetModal').modal('toggle');
});

$('input[type="checkbox"][data-action="selectAll"]').on('click', function (e) {
    let dataGroup = $(this).data('group');
    let checkState = $(this).prop("checked");
    $(this).closest('table').find(`input[type="checkbox"][data-group="${dataGroup}"`).each(function () {
        $(this).prop('checked', checkState)
    })
})
$('input[type="checkbox"][data-action="selectAll"] > .selectOne').on('click', function (e) {
    let allCheckBox = true;
  
    let checkState = $(this).prop("checked");
    console.log("comes",checkState)
    if(checkState){
        console.log("comes true")
  
        $(this).closest('table').find('input[type="checkbox"][data-action="selectOne"]').each(function () {
            if($(this).prop('checked') == false){
                console.log("comes false all")
  
                 allCheckBox = false
            }
        })
        $('input[type="checkbox"][data-action="selectAll"]').prop('checked', allCheckBox)
    }
    else{
        console.log("comes false")
  
        $('input[type="checkbox"][data-action="selectAll"]').prop('checked', False)
    }
    
})
/* File adding stuff */
$('#dataset-field').change(function () {
    /* When the upload field is changed, add the files to the datatable and store them in the datasetFiles object. */
    let datasetModal = $('#addDatasetModal');
    let datasetTable = $('#dataset-table');
    let datasetField = $(this);

    for (let dataset of datasetField[0].files) {
        datasetFiles.items.add(dataset);
        datasetTable.DataTable().row.add({
            'dataset': dataset
        }).draw();
    }

    /* 
    
    
    the dataset file field */
    $(this).val('');
    datasetModal.modal('toggle')
    $("#upload-merge").attr("disabled",false)
})

$('#filename').keypress(function (e) {
    /* Disables certain character inputs on the filename input */
    let char = String.fromCharCode(e.which);

    return !(/^[\\/:*?"<>|]+$/.test(char))
});

let indexCol;

/* Data Upload tab post requests */
$('#uploadForm').submit(function (e) {
    e.preventDefault();

    /* Uploads the data using a FormData object since handling nested json is a pain normally */
    let dataTable = $(this).find('#dataset-table').DataTable();
    let project = $(this).find('select[name="project"]').val();

    let formData = new FormData();
    formData.append('csrfmiddlewaretoken', getCSRFToken());
    formData.append('filename', $(this).find('input[name="filename"]').val());
    formData.append('project', project);
    formData.append('dataType', $(this).find('select[name="data_type"]').val());

    /* Store the project ID */
    $('meta[name="project"]').attr('content', project)

    /* Add each row to the FormData object */
    dataTable.rows().every(function (i, element) {
        let row = $(this.node());
        let file = datasetFiles.items[i].getAsFile();
        formData.append('datasets', JSON.stringify({
            file: file.name,
            pid: row.find('input[name="pid"]').val(),
            header: row.find('input[name="header"]').val(),
            sheet: row.find('select[name="sheet"]').val(),
            index: row.find('select[name="index"]').val(),
            columns: row.find('select[name="columns"]').val(),
        }))

        /* Appends the relevant file */
        formData.append(i, file);
    })

    /* Clear the DataTransfer object contents */
    datasetFiles.clearData()
   
    /* Get some information about the submit button for turning it into a spinner during the upload process */
    let submitBtn = $(this).find('button[type="submit"]');
    let submitOriginalHTML = submitBtn.html();
    let width = submitBtn.width()

    $.ajax({
        type: 'POST',
        url: handle_dataset_upload_url,
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        beforeSend: function () {
            submitBtn.blur();
            submitBtn.prop("disabled", true)
            submitBtn.html('<span class="fa fa-spinner fa-spin" role="status"></span>')
            submitBtn.width(width);
        },
        success: function (response) {
            /* TODO: Redirect to the data clean stage of the geochem process */
            $($.fn.dataTable.tables(true)).DataTable()
            .columns.adjust();
            next_tab();
            $("#datacleanFormOptions").find("form").each(function() {
     
                this.reset(); // 'this' refers to the DOM element of the form
            }); 
            $("#datacleanFormOptions").find("input.include").each(function() {$(this).val("0"); })
            $("#dataAnalysisFormOptions").find("form").each(function() {        
                this.reset(); // 'this' refers to the DOM element of the form
            }); $("#dataAnalysisFormOptions").find("input.include").each(function() {$(this).val("0"); })
            $(" .card-header").each(function() {
                $(this).removeClass("functionIncluded");
                $(this).removeClass("functionNotIncluded");
            });
            $(" .card").each(function() {
                $(this).removeClass("borderfunctionIncluded");
                $(this).removeClass("borderfunctionNotIncluded");
            });

            /* Incoming JSON data */
            let mergedJSON = JSON.parse(response.merged);
            let columnJSON = JSON.parse(response.columns);
            let typesJSON = JSON.parse(response.types);
            let missingJSON = JSON.parse(response.missing);
            // converting missing data to percentage
            missingJSON = missingJSON.map(obj => {
                obj.data = obj.data * 100;
                return obj;
              });
              
            indexCol = response.indexCol
            console.log("response",response.merged.length, response.columns.length)
            $('meta[name="pid"]').attr('content', response.pid)
             /* Populate all the dataclean tables */
            $('#mergedData').DataTable({
                searching: false,
                bSort: true,
                bDestroy: true,
                sScrollX: true,
                lengthChange: false,
                autoWidth: true,
                responsive: true,
                data: mergedJSON,
                columns: columnJSON
            }).draw();

            $('#removeColumnsTable').DataTable({
                searching: false,
                bSort: false,
                lengthChange: false,
                bDestroy: true,
                bInfo: false,
                paging: false,
                autoWidth: false,

                data: missingJSON ,
                columns: [
                    {
                        data: 'name', width: "10%",
                        mRender(data) {
                            return `<input type="checkbox" data-group="columnsOption" name="${data}">`;
                        }
                    },
                    {data: 'column', width: "40%"},
                    {data: 'data', width: "40%"},
                ]
            }).draw();

            // ensures column types are displayed to user in simple english in data cleaning phase
            console.log("missing",missingJSON)

            typesJSON.forEach((obj) => {
                obj.data = (obj.data == 'float32' || obj.data == 'float64' || obj.data == 'int32' || obj.data == 'int64') ? 'Number' : 'Text';
            });

            ['#removeNonNumeric', '#removeComma', '#handleInequalities', '#convertUnits', '#removeDuplicates'].forEach(function (item) {
                $(`${item}Table`).DataTable({
                    searching: false,
                    bSort: false,
                    lengthChange: false,
                    bDestroy: true,
                    bInfo: false,
                    paging: false,
                    autoWidth: false,
                    data: typesJSON,
                    columns: [
                        {
                            data: 'name', width: "10%",
                            mRender(data) {
                                return `<input type="checkbox" data-group="columnsOption" class="selectOne" name="${data}">`;
                            }
                        },
                        {data: 'column', width: "40%"},
                        {data: 'data', width: "40%"},
                    ]
                }).draw();
            });

            ['#subsetX'].forEach(function (item) {
                $.each(columnJSON, function (index, value) {
                    $(`${item}dropDown`).append(`
                        <option value=${value.title}>${value.title}</option>
                    `)

                });
            });
            $($.fn.dataTable.tables(true)).DataTable()
            .columns.adjust();
        },
        error: function (data) {
            /* TODO: Show some errors if the data was bad */
            if(data.responseJSON && "error_message" in data.responseJSON){
                $('#error_modal_text').html(data.responseJSON.error_message);
            }
            $('#errorModal').modal('toggle');
        },
        complete: function () {
            submitBtn.prop("disabled", false);
            submitBtn.html(submitOriginalHTML);
        }
    });
    return false;
})

let datasetNames = [];

$('#getExistingDatasetsForm').submit(function (e) {
    e.preventDefault();

    let datasetForm = $(this);
    let datasetModal = $('#addDatasetModal')
    let datasetTable = $('#dataset-table');

    /* Only let the form submit if the correct tab is open */
    if ($('#nav-existingFile').hasClass('active')) {
        $.ajax({
            type: 'POST',
            url: get_existing_dataset_url,
            data: datasetForm.serialize(),
            success: function (datasets) {

                /* The returned datasets are in base64, we need to convert them back into files */
                for (let dataset of datasets) {
                    let blob = atob(dataset.file);
                    let file = new File([blob], dataset.name, {type: dataset.mimetype});
                    var {id, ...filteredDataSet} = dataset;  // To Get all property values except "id"
                    /* Add the converted files to our datasetFiles, seems a bit unintuitive re-uploading */
                    /* files that are already on the server. This could use some fixing by someone who knows */
                    /* what they are doing. */
                    if (datasetNames.includes(dataset.name)) {
                        continue;
                    }

                    datasetNames.push(dataset.name)
                    
                    datasetFiles.items.add(file);
                    datasetTable.DataTable().row.add({
                        'dataset': filteredDataSet
                    }).draw();
                    console.log("dataset", dataset)
                }

                /* Reset the form and hide the modal */
                datasetForm[0].reset()
                datasetModal.modal('toggle')
               if(datasetTable.DataTable().rows().count() >0)
                 $("#upload-merge").attr("disabled",false)
               else
               $("#upload-merge").attr("disabled",true)

            },
            error: function (response) {
                /* TODO: Show some errors for whatever reason */
                console.log("Get Existing Dataset failed:", response);
            }
        });
        return false;
    }
})

/* DATACLEAN JS */

/* Checkbox interaction for opening associated modal if it exists */
$('#datacleanForm input[type=checkbox]').on('change', function (e) {
    if (e.target.checked) {
        let targetID = e.target.id;
        let targetModal = $(`#${targetID}Modal`);

        targetModal.modal({backdrop: 'static', keyboard: false});
        targetModal.modal('toggle')
    }
})

$('#dataAnalysisForm input[type=checkbox]').on('change', function (e) {
    if (e.target.checked == true) {
        let targetID = e.target.id;
        let targetModal = $(`#${targetID}Modal`);
  
        targetModal.modal({backdrop: 'static', keyboard: false});
        targetModal.modal('toggle')
    }
})

/* Handle modal button clicks */
$(document).on('click', 'form[data-form-group="datacleanMethod"] #btnCancel,form[data-form-group="dataAnalysisMethod"] #btnCancel', function (e) {
    /* Cancel button should disable the option, this is really janky */
    /*let modal = $(e.target).closest('.modal')[0];
    let checkBox = $(`#${modal.id.slice(0, -5)}`)

    checkBox.prop('checked', false);*/
    let includeForm = e.target.parentNode.parentNode.querySelector("input.include");
    
    cardId = includeForm.id.slice(7)
    console.log("card1",cardId)
    $(`label[for=${cardId}] .card-header`).removeClass("functionIncluded")
    $(`label[for=${cardId}] .card-header`).addClass("functionNotIncluded")
    $(`label[for=${cardId}] .card`).removeClass("borderfunctionIncluded")
    $(`label[for=${cardId}] .card`).addClass("borderfunctionNotIncluded")
    includeForm.value = "0"
    console.log("cancel",includeForm)
   
    
});

$(document).on('click', 'form[data-form-group="datacleanMethod"] #btnSubmit,form[data-form-group="dataAnalysisMethod"] #btnSubmit', function (e) {
    let includeForm = e.target.parentNode.parentNode.querySelector("input.include");
    cardId = includeForm.id.slice(7)
    includeForm.value = "1"

    $(`label[for=${cardId}] .card-header`).removeClass("functionNotIncluded")
    $(`label[for=${cardId}] .card-header`).addClass("functionIncluded")
    
    $(`label[for=${cardId}] .card`).removeClass("borderfunctionNotIncluded")
    $(`label[for=${cardId}] .card`).addClass("borderfunctionIncluded")
    console.log("submit",includeForm)

   // e.target.parent.modal('toggle')
});

/* Dataclean Form */
$('#defineUnitsForm input[name="mode"]').change(function (e) {

    $('#defineUnitsForm :input[name="mode"]').each(function (c) {
        let optionValue = $(this).val();

        /* Disable all sub-elements of unchecked boxes, this will make form data easy to post */
        $(this).parent().find('label').first().find('input, select, textarea').each(function () {

            if (optionValue === e.target.value) {
                $(this).removeAttr('disabled')
            } else {
                $(this).attr('disabled', 'disabled')
            }

        });
    });

})

let filename;
let cleanerReport;

let cleanerFile;
var cleaningMethods = [$("#remove_empty_entries"), $("#convert_uniform_units"), $("#remove_comma_sep"), 
$("#handle_inequalities"), $("#remove_non_numeric"), $("#remove_entries"), $("#remove_columns")];
// checks to see if any cleaning methods have been selected
var anyCleaningSelected = false;
$('#datacleanForm').submit(function (e) {
    e.preventDefault();

    /* Uploads the data using a FormData object since handling nested json is a pain normally */
    let datacleanForm = $(e.target);
    let formAction = datacleanForm.attr('action');
    let formData = new FormData();

    formData.append('csrfmiddlewaretoken', getCSRFToken());
    formData.append('project', $('meta[name="project"]').attr('content'));
    formData.append('pid', $('meta[name="pid"]').attr('content'));
    formData.append('index_col', indexCol);

   console.log("indexcol",indexCol)
   /* datacleanForm.find('input[type="checkbox"]:checked').each(function () {
        console.log("eeeee1",e,"this1",$(this))
     
        let inputID = $(this).attr('id');
        let modalForm = $(`#${inputID}Form`).serializeObject();
        console.log("inputID1",inputID)
        console.log("modalForm1",modalForm)
        
        formData.append(`data`, JSON.stringify({[inputID]: modalForm}));
    });*/
    $('input.include[value="1"]').each(function (e) {
        let inputID = $(this).attr('id').slice(7);
        if(inputID != "defineUnits")
        anyCleaningSelected =true;
        let modalForm =  $(`#${inputID}Form`).serializeObject();
        formData.append(`data`, JSON.stringify({[inputID]: modalForm}));
    })

    /* Clear the DataTransfer object contents */
    datasetFiles.clearData()
    
    /* Get some information about the submit button for turning it into a spinner during the upload process */
    let submitBtn = $(this).find('button[type="submit"]');
    let submitOriginalHTML = submitBtn.html();
    let width = submitBtn.width()

    $.ajax({
        type: 'POST',
        url: `${formAction}`,
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        beforeSend: function () {
            submitBtn.blur();
            submitBtn.prop("disabled", true)
            submitBtn.html('<span class="fa fa-spinner fa-spin" role="status"></span>')
            submitBtn.width(width);
        },
        success: function (data) {
            /* TODO: Redirect to the chart system component of the geochem */
            next_tab();
            $("#dataAnalysisFormOptions").find("form").each(function() {        
                this.reset(); // 'this' refers to the DOM element of the form
            }); $("#dataAnalysisFormOptions").find("input.include").each(function() {$(this).val("0"); })
            
         $("#dataAnalysisForm").find(" .card-header").each(function() {
                $(this).removeClass("functionIncluded");
                $(this).removeClass("functionNotIncluded");
            });
         $("#dataAnalysisForm").find(" .card").each(function() {
                $(this).removeClass("borderfunctionIncluded");
                $(this).removeClass("borderfunctionNotIncluded");
            });
            filename = data.filename
            cleanerFile = data.cleanerFile
            cleanerReport = data.cleanerReport

            let columnJSON = JSON.parse(data.columns);
            let typesJSON = JSON.parse(data.types);
            if (columnJSON && typesJSON){

                // ensures column types are displayed to user in simple english in data analysis phase
                typesJSON.forEach((obj) => {
                    obj.data = (obj.data === 'float64' || obj.data === 'int64' || obj.data === 'int32' || obj.data === 'float32') ? 'Number' : 'Text';
                });

                ['#pca', '#correlationCoefficents', 
                '#adaBoost', '#xgBoost', '#hierarchicalClustering', '#randomForest', '#neuralNetwork'].forEach(function (item) {
                    $(`${item}Table`).DataTable({
                        searching: false,
                        bSort: false,
                        lengthChange: false,
                        bDestroy: true,
                        bInfo: false,
                        paging: false,
                        autoWidth: false,
    
                        data: typesJSON,
                        columns: [
                            {
                                data: 'name', width: "10%",
                                mRender(data) {
                                    return `<input type="checkbox" data-group="columnsOption" name="${data}">`;
                                }
                            },
                            {data: 'column', width: "40%"},
                            {data: 'data', width: "40%"},
                        ]
                    }).draw();
                });
    
                ['#subsetX', '#adaBoostTarget', '#xgBoostTarget', '#randomForestTarget', '#neuralNetworkTarget'].forEach(function (item) {
                    $.each(columnJSON, function (index, value) {
                        $(`${item}dropDown`).append(`
                            <option value=${value.title}>${value.title}</option>
                        `)
    
                    });
                });
            }

        },
        error: function (data) {
            /* TODO: Show some errors if the data was bad */
            console.log("data1",data)
            if(data.responseJSON){
                if ("error_message" in data.responseJSON) {
                    if(data.responseJSON.error_message == "object of type 'NoneType' has no len()" || 
                    data.responseJSON.error_message =="'NoneType' object is not subscriptable"
                    ){
                        console.log("done")
                        $('#error_modal_text').html("No Columns Selected")}
                    else    
                    $('#error_modal_text').html(data.responseJSON.error_message)
                }
            }           
            $('#errorModal').modal('toggle');
      
        },
        complete: function () {
            submitBtn.prop("disabled", false)
            submitBtn.html(submitOriginalHTML);
        }
    });
    return false;
})

$('#dataAnalysisForm').submit(function (e) {
    e.preventDefault();
  
    /* Uploads the data using a FormData object since handling nested json is a pain normally */
    let dataAnalysisForm = $(e.target);
    let formAction = dataAnalysisForm.attr('action');
    let formData = new FormData();
  
    formData.append('csrfmiddlewaretoken', getCSRFToken());
    formData.append('project', $('meta[name="project"]').attr('content'));
    formData.append('pid', filename);
    formData.append('cleanerFile', cleanerFile);
    formData.append('cleanerReport', cleanerReport);
    formData.append('index_col', indexCol);

  
    $('input.include[value="1"]').each(function (e) {
        let inputID = $(this).attr('id').slice(7);
        let modalForm = $(`#${inputID}Form`).serializeObject();
  
        formData.append(`data`, JSON.stringify({[inputID]: modalForm}));
    });
  
    /* Clear the DataTransfer object contents */
    datasetFiles.clearData()
  
    /* Get some information about the submit button for turning it into a spinner during the upload process */
    let submitBtn = $(this).find('button[type="submit"]');
    let submitOriginalHTML = submitBtn.html();
    let width = submitBtn.width()
  
    $.ajax({
        type: 'POST',
        url: `${formAction}`,
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        beforeSend: function () {
            submitBtn.blur();
            submitBtn.prop("disabled", true)
            submitBtn.html('<span class="fa fa-spinner fa-spin" role="status"></span>')
            submitBtn.width(width);
        },
        success: function (data) {
            /* TODO: Redirect to the chart system component of the geochem */
            if(anyCleaningSelected){
                $("#final_report_download_container").append(`
            <a class="max-w-200 btn btn-success btn-sm rounded-0 me-3" href="${data.cleaning_report}" download>
                <i class="fas fa-download"></i> Cleaning Report
                </a>`);
            }
            $("#final_report_download_container").append(`
            <a class="max-w-200 btn btn-success btn-sm rounded-0" href="${data.analysis_report}" download>
              <i class="fas fa-download"></i> Analysis Report
            </a>
            `);
           
            console.log("jsurl",data.cleaner_file)
            next_tab();
        },
        error: function (data) {
            /* TODO: Show some errors if the data was bad */
            if (data.responseJSON && "error_message" in data.responseJSON) {
                $('#error_modal_text').html(data.responseJSON.error_message)
                $('#errorModal').modal('toggle');
            }
        },
        complete: function () {
            submitBtn.prop("disabled", false)
            submitBtn.html(submitOriginalHTML);
        }
    });
    return false;
  })