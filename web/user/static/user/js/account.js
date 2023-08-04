$(document).ready(
    function(){

    $("#edit-name-button").on('click',(function(e) {
        $("#show-name").css('display','none')
        $("#change-name").css('display','inline-block')
        $("#show-email").css('display','inline-block')
        $("#change-email").css('display','none')
        $("#show-company").css('display','inline-block')
        $("#change-company").css('display','none')

    }))
    $("#edit-name-confirm-button").on('click',(function(e) {
        $("#show-name").css('display','inline-block')
        $("#change-name").css('display','none')

    }))
    $("#edit-email-button").on('click',(function(e) {
        $("#show-email").css('display','none')
        $("#change-email").css('display','inline-block')
        $("#show-name").css('display','inline-block')
        $("#change-name").css('display','none')
        $("#show-company").css('display','inline-block')
        $("#change-company").css('display','none')
    }))
    $("#edit-email-confirm-button").on('click',(function(e) {
        $("#show-email").css('display','inline-block')
        $("#change-email").css('display','none')
    }))

    $("#edit-company-button").on('click',(function(e) {
        $("#show-company").css('display','none')
        $("#change-company").css('display','inline-block')
        $("#show-name").css('display','inline-block')
        $("#change-name").css('display','none')
        $("#show-email").css('display','inline-block')
        $("#change-email").css('display','none')
    }))
    $("#edit-company-confirm-button").on('click',(function(e) {
        $("#show-company").css('display','inline-block')
        $("#change-company").css('display','none')
    }))

    $("#passwd-button").on('click',(function(e) {
        $("#passwd-button").css('display','none')
        $("#change-passwd").css('display','inline-block')
    }))
    $("#edit-company-confirm-button").on('click',(function(e) {
        $("#passwd-button").css('display','inline-block')
        $("#change-passwd").css('display','none')
    }))
    $("#edit-passwd-cancel-button").on('click',(function(e) {
        $("#change-passwd").resetForm()
        $("#passwd-button").css('display','inline-block')
        $("#change-passwd").css('display','none')
        $("#client-error").css('display','none')
        $("#new-password1-cross-marker").css('display','none')
        $("#new-password2-cross-marker").css('display','none')

    }))
    $("#edit-company-cancel-button").on('click',(function(e) {
        $("#change-company").resetForm()
        $("#company-button").css('display','inline-block')
       
        $("#show-company").css('display','inline-block')
        $("#change-company").css('display','none')
        $("#company-error").css('display','none')
     

    }))
    $("#edit-email-cancel-button").on('click',(function(e) {
        $("#change-email").resetForm()
        $("#email-button").css('display','inline-block')
        
        $("#show-email").css('display','inline-block')
        $("#change-email").css('display','none')
        $("#email-error").css('display','none')
     

    }))
    $("#edit-name-cancel-button").on('click',(function(e) {
        $("#change-name").resetForm()
        $("#name-button").css('display','inline-block')
     
        $("#show-name").css('display','inline-block')
        $("#change-name").css('display','none')
        $("#name-error").css('display','none')
     

    }))
    }
  );
  
