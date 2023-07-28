$('button[type="submit"]').removeAttr("data-bs-dismiss")

$('#deleteProjectForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let projectData = $('#project-table').DataTable().row($form.attr('row-index')).data();

    $.ajax({
        type: 'POST',
        url: projectData['slug'] + `post/delete/`,
        data: $form.serialize(),
        success: function () {
            window.location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});

$('#deleteTenementForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let tenementData = $('#tenement-table').DataTable().row($form.attr('row-index')).data();

    $.ajax({
        type: 'POST',
        url: tenementData['permit']['slug'] + `post/relinquish/`,
        data: $form.serialize(),
        success: function () {
            window.location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});

$('#leaveProjectForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let projectData = $('#project-table').DataTable().row($form.attr('row-index')).data();

    $.ajax({
        type: 'POST',
        url: projectData['slug'] + `post/leave/`,
        data: $form.serialize(),
        success: function () {
            window.location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});


$('#addTenementForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let $submitBtn = $form.find('[type="submit"]');
    let submitHtml = $submitBtn.html();

    $.ajax({
        type: 'POST',
        url: `p/${this.project.value}/post/tenement/add/`,
        data: $form.serialize(),
        beforeSend: function (){
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

$('#inviteUserForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let projectData = $('#project-table').DataTable().row($form.attr('row-index')).data();

    $.ajax({
        type: 'POST',
        url: projectData['slug'] + `post/member/invite/`,
        data: $form.serialize(),
        success: function () {
            window.location.reload();
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        }
    });
});