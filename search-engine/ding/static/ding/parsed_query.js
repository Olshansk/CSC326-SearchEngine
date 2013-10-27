var numResultsLoaded = 0;
var noMoreResults = false;

$(document).ready(function (){    
    validate();
    $('input.form-control').change(validate);
    $( window ).scroll(scroll);
});

$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

function getURLParameter(name) {
    return decodeURI(
        (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,null])[1]
    );
}

function scroll(){
	if ($(window).scrollTop() + $(window).height() > $(document).height() - 50) {
        numResultsLoaded++;
        var query = getURLParameter("query")
        var url = 'http://localhost:8000/ding/parsed_query/' + query + "/" + numResultsLoaded + '/';
    	console.log("near bottom!" + numResultsLoaded + url);
        if (noMoreResults) {
            return;
        }
    	$.ajax({
    		url : url,
    		dataType : 'json',
    		type : 'GET',
    		success: function(data)
		    {
                if (data.length == 0) {
                    noMoreResults = true;
                } else {
                    $.each(data, function(index) {
		        	     var source = $("#search_result").html();
					   var template = Handlebars.compile(source);
					   var html = template(data[index].fields);
					   $("ul.search-results-list").append(html);
        		    });
                }
		    }
		});
    }
}

function validate(){
    if ($('input.form-control').val().length > 0) {
        $("button.btn-default").prop("disabled", false);
    }
    else {
        $("button.btn-default").prop("disabled", true);
    }
}
