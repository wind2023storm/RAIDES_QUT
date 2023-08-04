// Collapse click
$("[data-bs-toggle=sidebar-colapse]").click(function () {
    SidebarCollapse();
});

function SidebarCollapse() {
    $(".side-orefox").toggleClass("d-none");
    $(".side-item").toggleClass("collapse-item");
    $(".collapse-align").toggleClass("align-items-center");
    $(".sidebar-expanded").toggleClass("sidebar-collapsed");

    // Collapse/Expand icon
    $("#collapse-icon").toggleClass("fa-angle-left fa-angle-right");

    $('#content').css('margin-left', $('#sidebar').width());
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}

$(document).ready(function () {
    // Get the button
    let scrollUpButton = document.getElementById("scrollUp");

    // When the user scrolls down 20px from the top of the document, show the button
    window.onscroll = function () {
        scrollFunction();
    };

    function scrollFunction() {
        if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
            scrollUpButton.style.display = "block";
        } else {
            scrollUpButton.style.display = "none";
        }
    }

    // $('.nav-tabs').on('shown.bs.tab', '[data-bs-toggle="tab"]', function (e) {
    //     let target_id = $(this).data('bs-target');
    //     let $target = $(target_id);

    //     $target.find('.dataTable').each(function () {
    //         let dataTable = $(this).DataTable();

    //         if (dataTable.ajax.url()) {
    //             dataTable.ajax.reload().draw();
    //         }
    //     });
    // });

    function updateCategorySelector($selector) {
        let $form = $selector.closest('form');
        let category_name = $selector.data('category');
        let category_selected = $selector.find('option:selected').val();

        // Loop all categories related to this select field
        $form.find(`select[type="category"][name="${category_name}"]`).each(function (i, e) {
            let selected = false;

            $(e).find('option[data-category]').each(function (i, o) {
                if ($(o).data('category') === category_selected) {
                    $(o).show();

                    if (!selected){
                        $(o).prop("selected", "selected");
                        selected = true;
                    }
                } else {
                    $(o).hide();
                }
            });

            if (!selected) {
                $(e).val('');
            }
        });
    }

    $('select[data-category]').on('change', function () {
        updateCategorySelector($(this));
    }).each( function () {
        updateCategorySelector($(this));
    });

});
// $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
//     $.fn.dataTable.tables({visible: true, api: true}).columns.adjust();
// });

/* The following code will populate dynamic modalforms that are related to some DataTable entry
e.g., in the project table, the actions would open up a modalform.

The dynamic fields that are populated should be named as per the data key in the table.

Example 1:
<b id="project"></b>  // Would be auto-populated from the datatable row key value 'project'

Example 2:
<b id="project[owner]"><b>  // Would be auto-populated from a nested key value pair
 */
// TODO: Optimize this if possible, should only run when the modal with a nested data-form-dynamic modalform is shown
$('.modal').on('show.bs.modal', function (event) {
    let dynamicForm = $(this).find('form[data-form-dynamic="true"]');
    let relatedTable = $(event.relatedTarget).parents('table').first();

    if (dynamicForm.length && relatedTable.length) {
        let tr = $(event.relatedTarget).closest('tr');
        let row = relatedTable.DataTable().row(tr);

        // Store the row index for which the modal was activated from as an attribute in the form object
        // this is for ajax queries that intend on retrieving data from the datatable.
        $(dynamicForm).attr('row-index', row.index());

        $.each(row.data(), function (key, value) {

            // Some datatable information is stored in object rather than plain strings, so we have to loop through it
            if (typeof value === 'object') {
                $.each(value, function (subKey, subValue) {
                    dynamicForm.find(`*[id="${key}[${subKey}]"]`).text(subValue);
                })
            } else {
                dynamicForm.find(`*[id="${key}"]`).text(value);
            }
        });
    }
});

$(function ($) {
    /**
     * Displays a forms errors underneath the element in which the error was made for, otherwise display
     * the error at the bottom of the form
     * @param json  JSON containing element ID's as keys and associated error as value
     */
    $.fn.displayFormErrors = function (json) {
        let form = $(this);
        form.clearFormErrors();

        $.each(json, function (key, value) {
            $.each(value, function (i, error) {

                let $input = (key === '__all__') ?
                    form.find('input, textarea, select').filter(':visible:last') :
                    form.find('*[name=' + key + ']');

                let $errorElement = $input.next('p[id=' + key + 'Error]');

                // Django form errors won't have the 'message' key
                let message = (typeof error === 'object' && 'message' in error) ? error.message : error

                console.log(key === '__all__');

                if ($errorElement.length) {
                    $errorElement.text(message);
                } else {
                    $input.after('<p id="' + key + 'Error" class="text-ofx-red" type="error">' + message + '</p>');
                }
            });
        });
    };

    /**
     * Resets the contents of a form. Also removes any errors created via form.displayFormErrors()
     */
    $.fn.resetForm = function () {
        let form = $(this)
        form[0].reset();

        form.clearFormErrors();
    };

    /**
     * Removes any errors created via form.displayFormErrors() extension
     */
    $.fn.clearFormErrors = function () {
        $(this).find('[type="error"]').each(function (i, field) {
            field.remove();
        });
    };

    /**
     * Adds a 'spinner' icon to an element and disables it. Maintains original element size.
     * @returns {*|jQuery} Original HTML within the element for use when using element.removeSpinner()
     */
    $.fn.addSpinner = function () {
        let originalHtml = $(this).html();
        let width = $(this).width();
        let height = $(this).height();
        $(this).blur();
        $(this).prop("disabled", true);
        $(this).html('<span class="fa fa-spinner fa-spin" role="status"></span>');
        $(this).height(height);
        $(this).width(width);

        return originalHtml
    }

    /**
     * Removes the spinner from an element and restores the supplied original HTML. For use with element.addSpinner()
     * @param originalHTML
     */
    $.fn.removeSpinner = function (originalHTML) {
        $(this).prop('disabled', false);
        $(this).html(originalHTML);
    }

    return this;
}(jQuery));

/* Instantiates any tooltips created on a page, including those generated at runtime */
$(document).ready(function () {
    $('body').tooltip({
        selector: '[data-bs-toggle="tooltip"]',
        boundary: 'window',
        container: 'body',
        fallbackPlacements: ['bottom']  // , 'top', 'left', 'right'
    });

    // Adjusts columns to fit on any datatables in a nav tab when it is shown
    $('.nav-link').on('shown.bs.tab', function () {
        let $target = $($(this).data('bs-target'));

        if ($target) {
            $target.find('.dataTable').each(function () {
                $(this).DataTable().columns.adjust().draw();
            })
        }
    });
});

$('#createProjectForm').on('submit', function (e) {
    e.preventDefault()
    let $form = $(this);
    let $submitBtn = $form.find('[type="submit"]');
    let submitHtml = $submitBtn.html();

    $.ajax({
        type: 'POST',
        url: window.location.origin + `/project/post/create/`,
        data: $form.serialize(),
        beforeSend: function () {
            $submitBtn.addSpinner();
        },
        success: function (data) {
            window.location.href = data['url'];
        },
        error: function (response) {
            $form.displayFormErrors(response['responseJSON']);
        },
        complete: function () {
            $submitBtn.removeSpinner(submitHtml);
        }
    });
});
