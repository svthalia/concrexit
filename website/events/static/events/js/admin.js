django.jQuery(function () {
    var $ = django.jQuery;

    $(".present-check").change(function () {
        var checkbox = $(this);
        var url = checkbox.parent().parent().data("url");
        var checked = checkbox.prop('checked');
        patch(url, { present: checked }, function(result) {
            checkbox.prop('checked', result.present);
            $("table").trigger("update");
        }, function() {
            checkbox.prop('checked', !checked);
        });
    });

    $(".payment-radio").change(function () {
        var radiobutton = $(this);
        var url = radiobutton.parent().parent().data("url");
        var value = radiobutton.data("value");
        if (radiobutton.prop('checked')) {
            patch(url, { payment: value }, function(result) {
                radiobutton.prop('checked', value === result.payment);
                $("table").trigger("update");
            }, function() {
                radiobutton.prop('checked', !checked);
            });
        }
    });

    $.tablesorter.addParser({
        id: "checkbox",
        is: function(s) {
            return false;
        },
        format: function(s, t, node) {
            return $(node).children("input[type=checkbox]").is(':checked') ? 1 : 0;
        },
        type: "numeric"
    });

    $.tablesorter.addParser({
        id: "radio",
        is: function(s) {
            return false;
        },
        format: function(s, t, node) {
            return $(node).children("input[type=radio]").is(':checked') ? 1 : 0;
        },
        type: "numeric"
    });

    $.tablesorter.addParser({
        id: "date",
        is: function(s) {
            return false;
        },
        format: function(s, t, node) {
            return $(node).data("sortval");
        },
        type: "text"
    });

    $("table").tablesorter({
		sortList: [[1,0]],
        cssHeader: 'sortable',
	});
});

function patch(url, data, success, error) {
    django.jQuery.ajax({
        url: url,
        type: 'PATCH',
        data: data,
        headers: {
            "X-CSRFToken": Cookies.get('csrftoken')
        },
        dataType: 'json'
    }).done(success).fail(error);
}
