$(document).ready(function () {
    $('#id_discipline').on('input', (function () {
            let discipline = $(this).val();
            let $activity = $("#id_activity");
            let options = $($activity[0]).children("option[name='activity_options']")
            let has_selected_first = false;
            options.each((i, option) => {
                if ($(option).attr('data-discipline') === discipline) {
                    $(option).show()
                    if (has_selected_first === false) {
                        has_selected_first = true
                        option.selected = true
                    }
                } else {
                    $(option).hide()
                }
            })
            let units_select = $('#id_units_label')
            let quantity_select = $("#id_quantity_label")
            units_select[0].options[discipline].selected = true;
            quantity_select[0].options[discipline].selected = true;
        })
    )
})

