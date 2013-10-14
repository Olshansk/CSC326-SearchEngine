$(document).ready(function (){    
    validate();
    $('input.search-field').change(validate);
    $('table.count-table').find('tr').click(function(){
        var rowIndex = $(this).index();
        if (rowIndex == 0) {
            return;
        }
        var keyword = $(this).find('td:nth-child(2)').text();
        $("input.search-field").val(keyword);
        $("form.search-form").submit();
    });
});

function validate(){
    if ($('input.search-field').val().length > 0) {
        $("input.submit").prop("disabled", false);
    }
    else {
        $("input.submit").prop("disabled", true);
    }
}
