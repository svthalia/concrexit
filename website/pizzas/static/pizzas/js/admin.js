django.jQuery(function () {
    var $ = django.jQuery;

    $(".present-check").change(function () {
        var checkbox = $(this);
        var url = checkbox.parent().parent().data("url");
        var checked = checkbox.prop('checked');
        request('PATCH', url, { present: checked }, function(result) {
            checkbox.prop('checked', result.present);
            $("table").trigger("update");
        }, function() {
            checkbox.prop('checked', !checked);
        });
    });

    var payment_previous;
    $('select[name=payment]').on('focus', function () {
        payment_previous = this.value;
    }).change(function() {
        var select = $(this);
        var url = $(this).parents('tr').data("payable-url");
        var none = $(this).data('none');

        if (payment_previous === $(this).val()) {
            return;
        }
        $('table').trigger('update', false).trigger('sortReset');

        var successCallback = function(data) {
            if (!data) {
                select.removeClass('paid');
            } else {
                select.addClass('paid');
            }
            select.val(data ? data.payment.type: none);
            $('table').trigger('update', false);
        };

        var failCallback = function(xhr) {
            select.val(payment_previous);
            $('table').trigger('update', false);

            if (payment_previous === none) {
                select.removeClass('paid');
            } else {
                select.addClass('paid');
            }

            var data = $.parseJSON(xhr.responseText);
            if (data.detail !== undefined) {
                alert(data.detail);
            }
        };

        if ($(this).val() === none) {
            $(this).removeClass('paid');
            request('DELETE', url, null, successCallback, failCallback);
        } else {
            $(this).addClass('paid');
            request('PATCH', url, { payment_type: $(this).val() }, successCallback, failCallback);
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
        id: 'payment',
        is: function(s) {
            return false;
        },
        format: function(s, t, node) {
            const val = node.firstElementChild.value;
            if (val === 'no_payment') {
                return 'z';
            }
            return val;
        },
        type: "text",
    });

    $.tablesorter.addParser({
        id: "sortval",
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

function request(method, url, data, success, error) {
    django.jQuery.ajax({
        url: url,
        type: method,
        data: data,
        headers: {
            "X-CSRFToken": Cookies.get('csrftoken')
        },
        dataType: 'json'
    }).done(success).fail(error);
}
