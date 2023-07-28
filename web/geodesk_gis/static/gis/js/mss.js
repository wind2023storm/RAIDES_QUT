var longitude;
var latitude;
var map;
var L;

$(window).on("map:init", function (event) {
  map = event.detail.map;
  L = L
});

$(document).ready(function () {
  $("#process_id").val(0);
  $('#file_uploader_modal').modal('show');
  function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }
  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrf_token);
          }
      }
  });

  ///////////////////// Lib select scroll animation /////////////////
  $('.libs_collapse').on('shown.bs.collapse', function (e) {
    $('html, body').animate({
      scrollTop: $(this).offset().top
    });
  })

  /////////////////// File Uploader Modal ////////////////

  $("#select_existing_data").on("change", function(e){
    $("#file_uploader_form [name='existing_process_file_id']").val ($(this).val() )
  })

  $(".file_upload_area").click(function (e) {
    $("#file_uploader_form [name='uploaded_file']").click();
  });

  var uploader_inner_html = $(".file_upload_area .inner-content").html();
  $("#file_uploader_form [name='uploaded_file']").on("change", function (e) {
    let file = $("#file_uploader_form [name='uploaded_file']").val();
    if (file) {
      // console.log(this.files[0].name);
      // console.log(this.files[0].size)
      $(".file_upload_area .inner-content").html(
        `<div>${this.files[0].name}</div>`
      );
    } else {
      $(".file_upload_area .inner-content").html(uploader_inner_html);
    }
  });

  let data_processor = $("#data-processor");

  $(data_processor).find(`[tab-name='load_data']`).tab('show')
  //////////////  click event on change-tab//////////////////
  $(data_processor).find(".change-tab").click(function (e) {
      let clicked_item = $(this);
      let clicked_items_old_text = $(clicked_item).html();
      $(clicked_item)
        .html(
          `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...`
        )
        
      setTimeout(function () {
        let target_tab = $(clicked_item).attr("next-tab");
        let current_tab = $(data_processor).find(".tab-activation.active")
        $(current_tab).tab().trigger('hidden');
        $(current_tab).removeClass("active").find("i.icon").attr("class", "icon");
        // $(data_processor).find(`[tab-name='${target_tab}']`).addClass("active");
        $(data_processor).find(`[tab-name='${target_tab}']`).tab('show')
        let nav_icon = $(data_processor).find(".nav-link.active").attr("nav-icon");
        $(data_processor).find(".nav-link.active").find("i.icon").addClass(`${nav_icon}`);
        let progressbar_value = parseInt(
          $(data_processor).find(`.card-body [tab-name='${target_tab}']`).attr("data-progress")
        );
        $(data_processor).find(".progress-bar").attr("aria-valuenow", progressbar_value).css("width", `${progressbar_value}%`).html(`${progressbar_value}%`);
        $(clicked_item).html(`${clicked_items_old_text}`).prop("disabled", false);

        $("html, body").animate({
          scrollTop: $(data_processor).offset().top,
        });
      }, 1000);
    });

  ////////////////// On change of input check ///////////////////
  $(".form-check-input-btn .form-check-input").on("change", function (e) {
    if ($(this).prop("checked")) {
      $(this)
        .closest(".form-check-input-btn")
        .find(".form-check-btn")
        .addClass("active");
      let target_form_modal = $(this).attr("target-form-modal");
        // .closest(".form-check-input-btn.has-form-modal")

      if (target_form_modal) {
        $("#cleaner_action_1_modal").modal("show");
        $(`${target_form_modal}`).modal("show");
      }
    } else {
      $(this)
        .closest(".form-check-input-btn")
        .find(".form-check-btn")
        .removeClass("active");
    }
  });

  //////////////////////////// Data Loader Change /////////////////////
  $("input[name='cleaner_lab']").on("change", function(e){
    if($(this).val()=='2'){
      $("[elements-of='petrosea_load_data']").removeClass("d-none");
      $("[elements-of='load_data']").addClass("d-none")
    }
    else{
      $("[elements-of='load_data']").removeClass("d-none");
      $("[elements-of='petrosea_load_data']").addClass("d-none")
    }
  })

  ///////////// Data Filter ///////////
  $("input[name='filter_missing_data']").on("input", function () {
    let minimum_data_missing = parseInt($(this).val());
    $(".range-output").html(`${minimum_data_missing}%`);
    let rows = $("table#remove_columns tbody tr");
    $(rows).removeClass("bg-warning").removeClass("text-white").find(".c-check").prop("checked", false);
    $.each(rows, function (index, row) {
      let data_missing = parseInt($(row).attr("data-missing"));
      if (data_missing > minimum_data_missing) {
        $(row).addClass("bg-warning").addClass("text-white");
        $(row).find(".c-check").prop("checked", true);
      }
    });
  });

  var polygon1 = null;
  var polygon2 = null;
  var size = 0.045;
	const url =
		"http://127.0.0.1:8000/static/gis/img/TMI_RTP_1VD_4326.tif";

	L.tileLayer('/static/gis/img/output/{z}/{x}/{y}.png', {
			minZoom: 1,
			maxZoom: 18,
			attribution: 'ESO/INAF-VST/OmegaCAM',
			tms: true
	}).addTo(map);

	var imageUrl = '/static/gis/img/k_crop.png',
	imageBounds = [[-29, 138], [-11.9, 153.6]];
	//L.imageOverlay(imageUrl, imageBounds, interactive=true).addTo(map);
	L.control.scale().addTo(map);
	map.doubleClickZoom.disable(); 
	map.flyTo([-26, 135], 6)
	map.on('dblclick', function(ev) {
			console.log(parseInt($("[name = 'process_id']").val()))
        if (parseInt($("[name = 'process_id']").val())  < 2){
        console.log(ev.latlng)
        lat_min = ev.latlng.lat - size;
        lat_max = ev.latlng.lat + size;
        long_min = ev.latlng.lng - (size / Math.cos(ev.latlng.lat*Math.PI/180));
        long_max = ev.latlng.lng + (size / Math.cos(ev.latlng.lat*Math.PI/180));
        var latlngs = [[lat_max, long_max],[lat_max, long_min],[lat_min, long_min],[lat_min, long_max]]
        if (!map.hasLayer(polygon1)) {
            polygon1 = L.polygon(latlngs, {color: 'red'}).addTo(map)
            polygon1.on('click', function() {
            console.log(map.hasLayer(polygon1))
            polygon1.remove();
            $("#process_id").val(parseInt($("[name = 'process_id']").val()) - 1);
            console.log(map.hasLayer(polygon1))
            })
        }
        $("#process_id").val(parseInt($("[name = 'process_id']").val()) + 1);
			}
	})
	
  $(document).find(".submit").click(function (e) {
    $.ajax({
      url: "http://127.0.0.1:8000/gis/crop",
      data: JSON.stringify({"polygon1":polygon1.toGeoJSON(),
      "comparison":'MSS',
      "csrfmiddlewaretoken":csrf_token}),
      type: "POST",
      contentType: false,
      processData: false,
      dataType: "json",
      cache: false,
      success: function (data) {
        console.log(data)
        $("#modal-content").empty()
        $("#modal-content").append(`
          <p> The similarity between the two areas is ` + data['similarity'] + ` </p>
        `);
        $('#view_task_modal').modal('show');
        $('#view_task_modal').click(function (event) 
        {
          console.log(event.currentTarget)
          if($(event.target).closest("#modal_body").length === 0) {
            $('#view_task_modal').modal('hide');
          }     
        });
      },
      error: function (data) {
      },
    });
  })

  $(document).find(".sizeSelection").click(function (e) {
    if (e.currentTarget.id == "x-small"){
      size = 0.0225
    }
    if (e.currentTarget.id == "small"){
      size = 0.045
    }
    else if (e.currentTarget.id == "medium"){
      size = 0.0675
    }
    else if (e.currentTarget.id == "large"){
      size = 0.09
    }
  })


});
