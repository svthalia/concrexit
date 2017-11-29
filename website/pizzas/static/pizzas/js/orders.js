$(function() {
    $('table').tablesort();

    $('thead th.paid-title, thead th.collected-title').data('sortBy', function (th, td, tablesort) {
        return $(td).find('.btn').val();
    });

    $('thead th.numeric-title').data('sortBy', function (th, td, tablesort) {
        return parseInt($(td).html().replace('€', ''));
    });

    $('input.paid-button').click(function() {
        var id = $(this).data('id');
        var paid = $(this).data('paid');
        var button = $(this);
        $.ajax({
            url: '/api/v1/pizzas/orders/' + id + '/',
            type: 'PATCH',
            data: JSON.stringify({paid: !paid}),
            headers : {
                'X-CSRFToken': csrf_token,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        }).success(function(data, status) {
            button.data('paid', data.paid);
            if (data.paid) {
                button.addClass('btn-style3');
                button.removeClass('btn-style4');
                button.val(gettext('Yes'));
            } else {
                button.addClass('btn-style4');
                button.removeClass('btn-style3');
                button.val(gettext('No'));
            }
            button.blur();
        }).fail(function(xhr, status) {
            var data = $.parseJSON(xhr.responseText);
            if (data.message !== undefined) {
                alert(data.message);
            } else if (data.paid !== undefined) {
                alert(data.paid.join('\n'));
            }
        });
    });
});
