$('button[type="submit"]').removeAttr("data-bs-dismiss")
var longitude;
var latitude;
var map;
var L;

$(window).on("map:init", function (event) {
  map = event.detail.map;
  L = L

});

$(document).ready(function () {
  map.flyTo([-33,147],6)

  $("#dropdownMenuButton1").prop("disabled", true);

  $("#upload_button").click(function(e) {
        $('#file_uploader_modal').modal("show");
    });
    $(".close").click(function(e) {
        $('#file_uploader_modal').modal("hide");
    });
  ////////////////// popover ///////////////////////
  $('body').on('click', function (e) {
    $('.options-desc-btn').each(function () {
        // hide any open popovers when the anywhere else in the body is clicked
        if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
            $(this).popover('hide');
        }
    });

    if (!$(e.target).closest('#filter_box').length) {
      $('#filter_box').collapse('hide');
    }
  });

  $(".options-desc-btn").popover({
    // placement: "bottom",
    template:
      '<div class="popover options-popover shadow" role="tooltip"><div class="arrow"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>',
  });

  $('.options-desc-btn').click(function (e) {
    $(".options-desc-btn").not(this).popover('hide');
  });

  $(".options-desc-btn").on("inserted.bs.popover", function () {
    var showChar = 100; // How many characters are shown by default
    var ellipsestext = "...";
    var moretext = "Show more";
    var lesstext = "Show less";

    $(".options-popover .popover-body").each(function () {
      var content = $(this).html();

      if (content.length > showChar) {
        var c = content.substr(0, showChar);
        var h = content.substr(showChar, content.length - showChar);

        var html =
          c +
          '<span class="moreellipses">' +
          ellipsestext +
          '&nbsp;</span><span class="morecontent"><span>' +
          h +
          '</span>&nbsp;&nbsp;<a href="" class="morelink text-info" >' +
          moretext +
          "</a></span>";

        $(this).html(html);
      }
    });

    $(".morelink").on('click', function () {
      console.log("click")
      if ($(this).hasClass("less")) {
        $(this).removeClass("less");
        $(this).html(moretext);
      } else {
        $(this).addClass("less");
        $(this).html(lesstext);
      }
      $(this).parent().prev().toggle();
      $(this).prev().toggle();
      return false;
    });
    
  });

  $("#upload_button").click(function(e) {
    $('#file_uploader_modal').modal('show');
  })

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
  // File Upload with AJAX
  $("#file_uploader_form").on("submit", function (event) {
    event.preventDefault();
    

    let form = $(this);
    if ( !$(".existing_process_file_nav").hasClass("active") ){
      $(form).find("[name='existing_process_file_id']").val("")
    }
    let $submitBtn = $('#submit');
    let submitHtml = $submitBtn.html();
    $submitBtn.addSpinner();
    const overlay = document.createElement('div');
    overlay.classList.add('overlay');
    document.body.appendChild(overlay);
    
    $.ajax({
      url: $(form).attr("action"),
      data: new FormData($(form).get(0)),
      type: $(form).attr("method"),
      contentType: false,
      processData: false,
      dataType: "json",
      cache: false,
           
      success: function (data) {
        if (data.file_uploaded) {
          $(document)
          .find("[name='mapplotter_link']")
          .trigger("click")
          $(form)
            .find("[type='submit']")
            .html(`Load Data`).prop("disabled",false)
            
          $("#file_uploader_modal").modal("hide");
        }
        console.log("enter1")
       
        $.ajax({
          url: "http://127.0.0.1:8000/gis/map",
          data: JSON.stringify({"filepath":data.filepath,
          "csrfmiddlewaretoken":csrf_token}),
          type: "POST",
          contentType: false,
          processData: false,
          dataType: "json",
          cache: false,
          success: function (data) {
            console.log("enter")
            markerList = []
            L.control.scale().addTo(map);
            var myRenderer = L.canvas({ padding: 0.5 });
            for (const [key, value] of Object.entries(data.elements)) {
              $(".col_list_select").append(`
                <option value="${key}">${key}</option>
              `);            
            }
            $("#dropdownMenuButton1").prop("disabled", false);
            data.longitude.forEach((element, index) => {
              var circleMarker = L.circleMarker([data.latitude[index], element], {
                renderer: myRenderer,
                color: '#3388ff',
                className: index
              }).addTo(map).on("click",(e) => {
                $("#modal-content").empty()
                $("#modal-content").append(`
                  <p> The selected plotted point is ` + e.target.options.className + ` </p>
                  <p> Located at ` + e.latlng.lat + ` , ` + e.latlng.lng + `</p>
                `);
                $('#view_task_modal').modal('show');
                $('#view_task_modal').click(function (event) 
                {
                  if($(event.target).closest("#modal_body").length === 0) {
                    $('#view_task_modal').modal('hide');
                  }     
                });

              });
              markerList.push(circleMarker)
            })

            $("#filter_button").on("click", function (e) 
            {  
              e.preventDefault();
              
              var formId = e.target.form.id;
              const form = document.getElementById(formId);
              if (!form.checkValidity()) {
                  e.preventDefault();
                  e.stopPropagation();
                  form.classList.add('was-validated');
             }
             
              element = $(".col_list_select").val();
              ids = []
              data.elements[element].forEach((element, index) => {
                marker = markerList[index]
                if (element < $("#minimum").val()){
                  if (map.hasLayer(marker)){
                    map.removeLayer(marker)
                  }  
                }
                else {
                  map.addLayer(marker)
                }
              })
              
              $("#filter_box").collapse('hide')
            })

            map.flyTo([-26, 135], 6)

          },
          error: function (data) {
            
             $('#flash-message').addClass("alert alert-danger")
            $('#flash-message').text("Error in loading the data")
     
            $(form).find("[type='submit']").html(`Load Data`).prop("disabled", false);
          },
          complete:function(data){
            $submitBtn.removeSpinner(submitHtml);
            const overlay = document.querySelector('.overlay');
             document.body.removeChild(overlay); 
            setTimeout(function () {
                  if( document.getElementById("flash-message") !== null)
                  $('#flash-message').removeClass("alert alert-danger")
                  $('#flash-message').text("")
              
                }, 3000);
          }
        });
      },
      error: function (data) {
        console.log("data2",data2)
         $('#flash-message').addClass("alert alert-danger")
       $('#flash-message').text("Error in loading the data")
     
          $(form).find("[type='submit']").html(`Load Data`).prop("disabled", false);
      },
      complete:function(data){
        $submitBtn.removeSpinner(submitHtml);
         const overlay = document.querySelector('.overlay');
         document.body.removeChild(overlay); 
        setTimeout(function () {
              if( document.getElementById("flash-message") !== null)
              $('#flash-message').removeClass("alert alert-danger")
              $('#flash-message').text("")
          
            }, 3000);
      }
    });

  });
  $('#btnSubmit').on('click',function(e){
    var fileInput = $("input[type='file']");
    fileInput.closest("form").addClass("was-validated");
   if (fileInput.val() == "") {
      fileInput.addClass("is-invalid");
      $(".file_upload_area").removeClass("is-valid");
      $(".file_upload_area").addClass("is-invalid");
      fileInput.siblings(".invalid-feedback").text("Please select a file.");
    } 
    else {
      fileInput.removeClass("is-invalid");
      $(".file_upload_area").removeClass("is-invalid");
      $(".file_upload_area").addClass("is-valid");
      fileInput.siblings(".invalid-feedback").empty();
    }
})




});