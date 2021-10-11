django.jQuery(function() {
    var $ = django.jQuery;
    var csrfToken = $('#content-main').data('csrf');

    $.tablesorter.addParser({
        id: 'payment',
        is: function(s) {
            return false;
        },
        format: function(s, t, node) {
            return $(node).find('select').val();
        },
        type: 'text'
    });

    $('table').tablesorter({
        cssHeader: 'sortable',
    });

    var payment_previous;
    $('select[name=payment]').on('focus', function () {
        payment_previous = this.value;
    }).change(function() {
        var select = $(this);
        var id = $(this).parents('tr').data('id');
        var none = $(this).data('none');

        if (payment_previous === $(this).val()) {
            return;
        }

        if ($(this).val() === none) {
            $(this).removeClass('paid');
        } else {
            $(this).addClass('paid');
        }

        $.ajax({
            url: '/api/v1/pizzas/orders/' + id + '/',
            type: 'PATCH',
            data: JSON.stringify({payment: $(this).val()}),
            headers : {
                'X-CSRFToken': csrfToken,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        }).done(function(data) {
            if (data.payment === none) {
                select.removeClass('paid');
            } else {
                select.addClass('paid');
            }
            select.val(data.payment);
            $('table').trigger('update');
        }).fail(function(xhr) {
            var data = $.parseJSON(xhr.responseText);
            if (data.message !== undefined) {
                alert(data.message);
            } else if (data.payment !== undefined) {
                alert(data.payment.join('\n'));
            }
        });
    });

    $('a.deletelink').click(function() {
        if (confirm(gettext('Are you sure you want to delete this order?'))) {
            var id = $(this).parents('tr').data('id');
            var button = $(this);

            $.ajax({
                url: '/api/v1/pizzas/orders/' + id + '/',
                type: 'DELETE',
                headers : {
                    'X-CSRFToken': csrfToken,
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            }).done(function() {
                button.parents('tr').remove();
                $('table').trigger('update');
            }).fail(function(xhr) {
                var data = $.parseJSON(xhr.responseText);
                if (data.message !== undefined) {
                    alert(data.message);
                } else if (data.payment !== undefined) {
                    alert(data.payment.join('\n'));
                }
            });
        }
    });

    $('#searchbar').on('input', function() {
        var input = this.value.toLowerCase();
        $('#result_list tbody tr').each(function(i, e) {
            var tr = $(this);
            var show = false;
            $(this).find('td').each(function(j, t) {
                if (j > 2) {
                    return;
                }
                if ($(t).text().toLowerCase().indexOf(input) !== -1) {
                    show = true;
                }
            });
            if (show) {
                tr.show();
            } else {
                tr.hide();
            }
        });
    });
});
