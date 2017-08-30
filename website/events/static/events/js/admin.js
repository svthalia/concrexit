django.jQuery(function () {
    var $ = django.jQuery;

    var url = $("#content-main").attr("data-url");
    var payment_url = url + "payment/";
    var present_url = url + "present/";

    $(".present-check").change(function () {
        var checkbox = $(this);
        var id = checkbox.attr("data-id");
        var checked = checkbox.prop('checked');
        post(present_url, { checked: checked, id: id }, function(result) {
            if (!result.success) {
                checkbox.prop('checked', !checked);
            }
        }, function() {
            checkbox.prop('checked', !checked);
        });
    });

    $(".payment-radio").change(function () {
        var radiobutton = $(this);
        var id = radiobutton.attr("data-id");
        var value = radiobutton.attr("data-value");
        if (radiobutton.prop('checked')) {
            post(payment_url, { value: value, id: id }, function(result) {
                if (!result.success) {
                    radiobutton.prop('checked', !checked);
                }
            }, function() {
                radiobutton.prop('checked', !checked);
            });
        }
    });
});

function post(url, data, success, error) {
    django.jQuery.post({
        url: url,
        type: 'post',
        data: data,
        headers: {
            "X-CSRFToken": getCookie('csrftoken')
        },
        dataType: 'json'
    }).done(success).fail(error);
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = django.jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
