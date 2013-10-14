$(document).ready(function (){    
    validate();
    $('input.form-control').change(validate);
});

function validate(){
    if ($('input.form-control').val().length > 0) {
        $("button.btn-default").prop("disabled", false);
    }
    else {
        $("button.btn-default").prop("disabled", true);
    }
}
