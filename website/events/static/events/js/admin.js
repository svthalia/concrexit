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

    var payment_previous;
    $('select[name=payment]').on('focus', function () {
        payment_previous = this.value;
    }).change(function() {
        var select = $(this);
        var url = $(this).parents('tr').data("url");
        var none = $(this).data('none');

        if (payment_previous === $(this).val()) {
            return;
        }

        if ($(this).val() === none) {
            $(this).removeClass('paid');
        } else {
            $(this).addClass('paid');
        }

        patch(url, { payment: $(this).val() }, function(data) {
            if (data.payment === none) {
                select.removeClass('paid');
            } else {
                select.addClass('paid');
            }
            select.val(data.payment);
            $('table').trigger('update');
        }, function(xhr) {
            var data = $.parseJSON(xhr.responseText);
            if (data.message !== undefined) {
                alert(data.message);
            } else if (data.payment !== undefined) {
                alert(data.payment.join('\n'));
            }
        });
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
            var val = $(node).find('select').val();
            if (val === 'no_payment') {
                return '';
            }
            return $(node).find('select').val();
        },
        type: 'text'
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
