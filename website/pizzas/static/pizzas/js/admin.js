django.jQuery(function () {
    var $ = django.jQuery;
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

        var successCallback = function(data) {
            if (!data) {
                select.removeClass('paid');
            } else {
                select.addClass('paid');
            }
            select.val(data ? data.payment.type: none);
        };

        var failCallback = function(xhr) {
            select.val(payment_previous);

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
