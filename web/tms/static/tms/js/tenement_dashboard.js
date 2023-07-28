$('button[type="submit"]').removeAttr("data-bs-dismiss")
var quantity_input = document.getElementById('id_quantity');
quantity_input.value=""
$("#id_activity").attr("disabled","True")
var Unit_Labels = {"0" : "Days" ,"1" : "Holes","2":"Days","3": "Lines","4" : "Days","5":"Lines","6":"Days",

"7":"Samples","8":"Samples","9":"Days","10":"Days"}
var Quantity_Labels = {"0" : "NA" ,"1" : "Meters","2":"NA","3": "Line Kilometres","4" : "NA","5":"Line Kilometres","6":"NA",

"7":"NA","8":"Kilograms","9":"NA","10":"NA"}
var Activity_Choices = {    //DESKTOP
    "0": [
         [ 0, 'Consultancy Studies'],
        [1, 'Geological and Geophysical Review'],
       [2, 'Geophysical Data Reprocessing'], 
        [3, 'Gravity Data Reprocessing'],
       [4, 'Gravity Data Reprocessing (Fixed Cost)'], 
       [5, 'Magnetic Data Reprocessing'],
        [ 6, 'Magnetic Data Reprocessing (Fixed Cost)'], 
        [7, 'Seismic Data Reprocessing'], 
        [8, 'Seismic Data Reprocessing (Fixed Cost)'],
        [9, 'Technical Review']
    ],
    // DRILLING
    "1":[
        
        [10, 'Air Core Drilling'],
        [ 11, 'Augur Drilling'],
        [12, 'Diamond'],
        [13, 'Directional'],
        [14, 'Geotechnical Drilling'],
        [15, 'Hammer'],
        [16, 'Large Diameter'],
        [17, 'Mixed Type'],
        [18, 'Mud'],
        [ 19, 'Percussion'],
        [ 20, 'Precollar'],
        [ 21, 'Reverse Circulation'],
        [ 22, 'Sonic/Vibratory Drilling'],
        [ 23, 'Tri-Cone']
    ],
    "2" :[
       // FEASIBILITY_STUDIES
        [24, 'Bankable Feasibility Study (BFS)'],
        [25, 'Definitive Feasibility Study (DFS)'],
        [26, 'Engineering and Design'],
        [27, 'Environmental Assessment'],
        [28, 'Market Analysis'],
        [29, 'Mine Planning'],
        [30, 'Preliminary Feasibility Study (PFS)'],
        [31, 'Scoping Study']
    ],
    // GEOPHYSICS
    "3" :[
       
        [32, 'Downhole Geophysics'],
        [33, 'Downhole Survey'],
        [34, 'Electromagnetic'],
        [35, 'Gravity'],
        [36, 'Ground Penetrating Radar'],
        [37, 'Induce Polarisation'],
        [38, 'Magnetics'],
        [39, 'Magnetotellurics'],
        [40, 'Radiometric'],
        [41, 'Resistivity'],
        [42, 'Seismic (2 Dimensional)'],
        [43, 'Seismic (3 Dimensional)'],
        [44, 'Self Potential'],
        [45, 'Sub-audio Magnetics']
    ],
    // MAPPING
    "4":[
        
        [46, 'Alteration'],
        [47, 'Geological'],
        [48, 'Reconnaissance'],
        [49, 'Structural']
    ],
    //REMOTE_SENSING
"5":[
    
        [50, 'Aerial Photography (Broader Spectrum Imagery)'],
        [51, 'Interpretation and Modelling'],
        [52, 'Aerial Photography (Visible Imagery)'],
        [53, 'Broader Spectrum Imagery'],
        [54, 'Satellite Imagery (Visible Imagery)']

],
// RESOURCE_EVALUATION
"6":[
   
   [ 55, 'Metallurgical Studies'],
   [ 56, 'Geological Modelling'],
   [ 57, 'JORC Resource Estimation'],
   [58, 'Resource Modelling']
],
// SAMPLE_ANALYSIS
  
"7":[
        [59, 'Bulk Leach Extracted Gold'],
        [60, 'Chromatographic Soils/Gas'],
        [61, 'Drill Sample Assays'],
        [62, 'General Sample Assays'],
        [63, 'Mineral/Petrology'],
        [64, 'Mobile Metal Ion'],
        [65, 'Multi-Element'],
        [66, 'Portable Analytical Tools'],
        [67, 'Rock Chips'],
        [68, 'Soils']
],
//SAMPLE_COLLECTION  
"8":[
     [69, 'Costeaning'],
    [70, 'Hand Sampling'],
    [71, 'Rock Chips'],
    [72, 'Soils'],
    [73, 'Stream Sediments'],
    [74, 'Trenching']
],
// SITE_LOGISTICS

"9":[
    [75, 'Access or Drill Site Preparation costs'],
    [76, 'Vehicle / Accomodation'],
    [77, 'Rehabilitiation costs']
],
// SITE_TECHNICAL
  "10":[
        [78, 'Chip logging'],
        [79, 'Consultancy Cost'],
        [80, 'Core logging'],
        [81, 'Geotechnical logging'],
        [82, 'Internal Project Staff Cost'],
        [83, 'Program Supervision']
]
    

}

function populate_Activity_Unit_Quantity_Dropdown() {
    // Get the selected key from the discipline dropdown
    
    var selectedKey = document.getElementById("id_discipline").value;
    $("#id_activity").removeAttr("disabled")
    // Get a reference to the activity dropdown
    var dropdown2 = document.getElementById("id_activity");
    
    // Clear any existing options from the activity dropdown
    dropdown2.innerHTML = "";
    
    // Populate the second dropdown based on the selected key from the discipline dropdown
    for (var i = 0; i < Activity_Choices[selectedKey].length; i++) {
      dropdown2.innerHTML += "<option value='" + Activity_Choices[selectedKey][i][0] + "'>" + Activity_Choices[selectedKey][i][1] + "</option>";
    }
    //Define Unit based on discipline selected
        var unit_input = document.getElementById('id_units');

        // Get the parent element
        var parent = unit_input.parentNode;

        var unit_label = parent.querySelector('span');

        if (unit_label) {
            unit_label.innerText = Unit_Labels[selectedKey];
        } else {
          // If no span element is found, create a new one and append it to the parent element
          unit_label = document.createElement('span');
          unit_label.style.color = "green"
          unit_label.innerText = Unit_Labels[selectedKey];
          parent.appendChild(unit_label);
        }

        //Define Qunatity based on discipline selected
        var quantity_input = document.getElementById('id_quantity');
        qlabel = Quantity_Labels[selectedKey];
        
            // Get the parent element
            var parent = quantity_input.parentNode;

            var quantity_label = parent.querySelector('span');

            if (quantity_label) {
                if(qlabel !== "NA"){ 
                     quantity_label.innerText = Quantity_Labels[selectedKey];
                     quantity_input.value = ""
                     quantity_input.disabled = false
               }
               else{
                 quantity_label.innerText = "Not applicable for this Discipline"
                 //quantity_input.disabled = true
                 quantity_input.value = "0.0"
               }
            } else {
            // If no span element is found, create a new one and append it to the parent element
                quantity_label = document.createElement('span');
                quantity_label.style.color = "green"
                if(qlabel !== "NA"){ 
                    quantity_label.innerText = Quantity_Labels[selectedKey]
                    quantity_input.value = ""
                    quantity_input.disabled = false
                }
                else{
                    quantity_label.innerText = "Not applicable for this Discipline"                  
                    //quantity_input.disabled = true
                    quantity_input.value = "0.0"
                }
                parent.appendChild(quantity_label);
            }
        }
             
  $("#id_discipline").change(populate_Activity_Unit_Quantity_Dropdown)

// $('#addTargetForm').on('submit', function (e) {
//     e.preventDefault();
//     let $form = $(this);
//     let $table = $('#target-table');
//     let $modal = $form.closest('.modal');

//     $.ajax({
//         type: 'POST',
//         url: location.origin + location.pathname + `post/target/add/`,
//         data: $form.serialize(),
//         success: function (response) {
//             var marker = L.marker(response.data.location.split(" "))
//             var intersected_tenement = get_intersected_tenements(response.project_tenements, marker.toGeoJSON(), L.geoJson(response.tenement_data))
//             if (Object.keys(intersected_tenement).length !== 0)
//                         response.data.permit.slug = intersected_tenement.slug
//                         response.data.permit.type = intersected_tenement.type
//                         response.data.permit.number = intersected_tenement.number

//             $table.DataTable().row.add(response.data).draw();
//             $modal.modal('hide');
//             $form.resetForm();
//             location.reload()
//             $('#tenement_map_box').load(location.origin + location.pathname + `get/tenement_map/`);
           
//         },
//         error: function (response) {
//             $form.displayFormErrors(response['responseJSON']);
//             //location.reload();
//         }
//     });
// });
// $('#deleteTargetForm').on('submit', function (e) {
//     e.preventDefault();
//     let $form = $(this);
//     let $table = $('#target-table');
//     let $modal = $form.closest('.modal');
//     let tableRow = $table.DataTable().row($form.attr('row-index'));

//     let formData = new FormData($form[0]);
//     formData.set('name', tableRow.data()['name']);

//     $.ajax({
//         type: 'POST',
//         url: location.origin + location.pathname + `post/target/delete/`,
//         data: formData,
//         processData: false,
//         contentType: false,
//         success: function () {
//             tableRow.remove().draw();
//             $modal.modal('hide');
//             $form.resetForm();
//             location.href = '#';
//             location.reload()
//             $('#project_map_box').load(location.origin + location.pathname + `get/project_map/`);
//         },
//         error: function (response) {
//             $form.displayFormErrors(response['responseJSON']);
//         }
//     });
// });

$('#createTaskForm').on('submit', function (e) {
    e.preventDefault();

    let $form = $(this);
    let $table = $('#task-table');
    let $modal = $form.closest('.modal');

    let formData = new FormData(this);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/task/add/`,
        data: formData,
        contentType: false,
        processData: false,

        success: function (response) {
            $table.DataTable().row.add(response.data).draw();
            $modal.modal('hide');
            $form.resetForm();
            location.href = '#';
            location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
            // location.href = '#';
            //location.reload();
               
            $('#flash-message').addClass("alert alert-danger")
            $('#flash-message').text("Error in loading the data")
            window.scrollTo(0, 0);
        },
        complete : function(){
            setTimeout(function () {
                if( document.getElementById("flash-message") !== null)
                document.getElementById("flash-message").style.display = "none";
              }, 3000);
        }
    });
});

$('#deleteTaskForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let $table = $('#task-table');
    let $modal = $form.closest('.modal');
    let tableRow = $table.DataTable().row($form.attr('row-index'))

    let formData = new FormData($form[0]);
    formData.set('task', tableRow.data()['id']);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/task/delete/`,
        data: formData,
        processData: false,
        contentType: false,
        success: function () {
            tableRow.remove().draw();
            $modal.modal('hide');
            $form.resetForm();
            location.href="#"
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});

$('#createWorkProgramForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let $table = $('#activity-table');
    let $modal = $form.closest('.modal');
    let formData = new FormData(this);
    let discipline_selected = $("#id_discipline").find(":selected").text();
    let activity_selected = $("#id_activity").find(":selected").text();
    let last_unit_label =  $("#id_units_label").find(":selected").text();
    let last_quantity_label = $("#id_quantity_label").find(":selected").text();
    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/workload/add/`,
        data: formData,
        contentType: false,
        processData: false,

        success: function (response) {
            console.log(response)
            response.data.actual_expenditure = 0
            $table.DataTable().row.add({
                 'year':response.data.year,
                 'discipline':discipline_selected,
                 'activity':activity_selected,
                 'units':response.data.units ,
                 'units_display':last_unit_label,
                 'quantity':last_quantity_label == 'N/A' ? '':response.data.quantity,
                 'quantity_display':last_quantity_label, //== 'N/A' ? '':last_quantity_label,
                 'expenditure': response.data.expenditure,
                 'actual_expenditure':0,
                 'receipts':{},
                 'actions':null,
                 }
                 ).draw()

            $modal.modal('hide');
            $form.resetForm();
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});

$('#createWorkProgramReceiptForm').on('submit', function (e) {
    e.preventDefault();
    //TODO: handle post after backend is done
    let $form = $(this);
    let $table = $('#activity-table');
    let $modal = $form.closest('.modal');
    let tableRow = $table.DataTable().row($form.attr('row-index'))

    let formData = new FormData(this);
    formData.set('program', tableRow.data()['program_id']);
    console.log(tableRow.data()['program_id'])
    $.ajax(
        {
        type: 'POST',
        url: location.origin + location.pathname  + `post/workload/receipt/${tableRow.data()['program_id']}/add/`,
        data: formData,
        contentType: false,
        processData: false,

        success: function (response) {
            $modal.modal('hide');
            $form.resetForm();
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});

$('#deleteWorkProgramForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let $table = $('#activity-table');
    let $modal = $form.closest('.modal');
    let tableRow = $table.DataTable().row($form.attr('row-index'))

    let formData = new FormData($form[0]);
    formData.set('program', tableRow.data()['program_id']);

    console.log(formData);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/workload/delete/`,
        data: formData,
        processData: false,
        contentType: false,
        success: function () {
            tableRow.remove().draw();
            $modal.modal('hide');
            $form.resetForm();
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});
$('#deleteTenementForm').on('submit', function (e) {
    e.preventDefault();
    let formData = new FormData(this);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/relinquish/`,
        data: formData,
        processData: false,
        contentType: false,
        success: function () {
            window.location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});