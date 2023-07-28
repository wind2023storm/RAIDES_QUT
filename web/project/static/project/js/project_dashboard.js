$('button[type="submit"]').removeAttr("data-bs-dismiss")
// PROJECT FORMS

$('#deleteProjectForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/delete/`,
        data: $form.serialize(),
        success: function () {
            window.location.href = window.origin + '/project/';
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});


$('#leaveProjectForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/leave/`,
        data: $form.serialize(),
        success: function () {
            window.location.href = window.origin + '/project/';
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});

// TENEMENT FORMS

$('#addTenementForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let $submitBtn = $form.find('[type="submit"]');
    let submitHtml = $submitBtn.html();
    
    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/tenement/add/`,
        data: $form.serialize(),
        beforeSend: function (){
            $form.clearFormErrors();
            $submitBtn.addSpinner();
            const overlay = document.createElement('div');
            overlay.classList.add('overlay');
            document.body.appendChild(overlay);
        },
        success: function (data) {
            window.location.href = data['url'];
            location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        },
        complete: function () {
            $submitBtn.removeSpinner(submitHtml);
            const overlay = document.querySelector('.overlay');
            document.body.removeChild(overlay); 
        }
    });
});


$('#deleteTenementForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let tenementData = $('#tenement-table').DataTable().row($form.attr('row-index')).data();

    $.ajax({
        type: 'POST',
        url: location.origin + tenementData['permit']['slug'] + `post/relinquish/`,
        data: $form.serialize(),
        success: function () {
            window.location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});

// TARGET FORMS

$('#addEditTargetForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let $table = $('#target-table');
    let tableRow = $table.DataTable().row($form.attr('row-index'));
    let url = $('#id_target_id').val() ? location.origin + location.pathname + `post/target/edit/`+tableRow.data()['name'] : location.origin + location.pathname + `post/target/add/`;
    let $modal = $form.closest('.modal');
    let $submitBtn = $form.find('[type="submit"]');
    let submitHtml = $submitBtn.html();
     
    $.ajax({
        type: 'POST',
        url: url,
        data: $form.serialize(),
        beforeSend: function (){
            $submitBtn.addSpinner();
            const overlay = document.createElement('div');
            overlay.classList.add('overlay');
            document.body.appendChild(overlay);
        },
        success: function (response) {
            var coordinates = response.data.location.split(" ")
            var marker = L.marker(coordinates)
            var intersected_tenement = get_intersected_tenements(response.project_tenements, marker.toGeoJSON(), L.geoJson(response.tenement_data))
            if (Object.keys(intersected_tenement).length !== 0){
                response.data.permit.slug = intersected_tenement.slug
                response.data.permit.type = intersected_tenement.type
                response.data.permit.number = intersected_tenement.number
            }
            response.data.location = "[ " + coordinates[0] +", " + coordinates[1] + " ]"
            if ($('#id_target_id').val()){
                $table.DataTable().row($form.attr('row-index')).data(response.data).draw();
            }
            else{
                $table.DataTable().row.add(response.data).draw();
            }

            $modal.modal('hide');
            $form.resetForm();  
            // location.reload()
            $('#project_map_box').load(location.origin + location.pathname + `get/project_map/`);
            
        },
        error: function (response) {
            if(response['responseJSON']){
                $form.displayFormErrors(response['responseJSON']);
            }
            else{
                $form.displayFormErrors({'__all__': ['Target with this Project and Name already exists.']});
            }
            
        },
        complete: function () {
            $submitBtn.removeSpinner(submitHtml);
            const overlay = document.querySelector('.overlay');
            document.body.removeChild(overlay);
           // location.reload();
        }
    });
});

$('#addEditTargetModal').on("hidden.bs.modal", function() {
    $('#addEditTargetForm').resetForm();
});

$('#deleteTargetForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let $table = $('#target-table');
    let $modal = $form.closest('.modal');
    let tableRow = $table.DataTable().row($form.attr('row-index'));
    let formData = new FormData($form[0]);
    formData.set('name', tableRow.data()['name']);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/target/delete/`,
        data: formData,
        processData: false,
        contentType: false,
        success: function () {
            tableRow.remove().draw();
            $modal.modal('hide');
            $form.resetForm();
            //location.reload();
            $('#project_map_box').load(location.origin + location.pathname + `get/project_map/`);
            
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});


// TASK FORMS

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
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
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
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});


// MEMBER FORMS

$('#inviteUserForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let $table = $('#member-table');
    let $modal = $form.closest('.modal');
    let $submitBtn = $form.find('[type="submit"]');
    let submitHtml = $submitBtn.html();


    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/member/invite/`,
        data: $form.serialize(),
        beforeSend: function (){
            $submitBtn.addSpinner();
            const overlay = document.createElement('div');
            overlay.classList.add('overlay');
            document.body.appendChild(overlay);

        },
        success: function (response) {
            $table.DataTable().row.add(response.data).draw();
            $modal.modal('hide');
            $form.resetForm();
            location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
           // location.reload();
        },
        complete: function () {
            $submitBtn.removeSpinner(submitHtml);
            const overlay = document.querySelector('.overlay');
            document.body.removeChild(overlay);

           // location.reload();
        }
    });
});


$('#modifyMemberForm').on('submit', function (e) {
    e.preventDefault();
    let $form = $(this);
    let $table = $('#member-table');
    let $modal = $form.closest('.modal');
    let tableRow = $table.DataTable().row($form.attr('row-index'));

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/member/modify/`,
        data: $form.serialize(),
        success: function () {
            $modal.modal('hide');
            $form.resetForm();
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});


$('#deleteMemberForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let $table = $('#member-table');
    let $modal = $form.closest('.modal');
    let tableRow = $table.DataTable().row($form.attr('row-index'));

    let formData = new FormData($form[0]);
    formData.set('email', tableRow.data()['email']);

    $.ajax({
        type: 'POST',
        url: location.origin + location.pathname + `post/member/delete/`,
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

// DATASET/MODEL FORMS

$('#addDatasetForm, #addModelForm').on('submit', function (e) {
    e.preventDefault();

    let $form = $(this);
    let $modal = $form.closest('.modal');
    let $submitBtn = $form.find('[type="submit"]');
    let submitHtml = $submitBtn.html();

    let $table = '';
    let url = location.origin + location.pathname;

    switch ($form.attr('id')) {
        case 'addDatasetForm':
            $table = $('#dataset-table');
            url += 'post/dataset/add/';
            break;
        case 'addModelForm':
            $table = $('#model-table');
            url += 'post/model/add/';
            break;
        default:
            return false;
    }

    let formData = new FormData(this);

    $.ajax({
        type: 'POST',
        url: url,
        data: formData,
        contentType: false,
        processData: false,

        beforeSend: function (){
            $submitBtn.addSpinner();
        },
        success: function (response) {

            response.data.forEach(function(file) {
                $table.DataTable().row.add(file);
            })

            $table.DataTable().draw()

            $modal.modal('hide');
            $form.resetForm();
            location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
           // location.reload();
        },
        complete: function () {
            $submitBtn.removeSpinner(submitHtml);
           // location.reload();
        }
    });
});

$('#deleteDatasetForm, #deleteModelForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let $modal = $form.closest('.modal');

    let $table = '';
    let url = location.origin + location.pathname;

    switch ($form.attr('id')) {
        case 'deleteDatasetForm':
            $table = $('#dataset-table');
            url += 'post/dataset/delete/';
            break;
        case 'deleteModelForm':
            $table = $('#model-table');
            url += 'post/model/delete/';
            break;
        default:
            return false;
    }

    let $tableRow = $table.DataTable().row($form.attr('row-index'));

    let formData = new FormData(this);
    formData.set('uuid', $tableRow.data()['uuid']);

    $.ajax({
        type: 'POST',
        url: url,
        data: formData,
        processData: false,
        contentType: false,
        success: function () {
            $tableRow.remove().draw();
            $modal.modal('hide');
            $form.resetForm();
            location.reload()
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});