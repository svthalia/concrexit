$(function() {
    var csrfToken = $('#pizzas-orders').data('csrf');

    $('table').tablesorter({
        headerTemplate: '{content} {icon}',
        cssIconNone: 'fas fa-sort',
        cssIconAsc: 'fas fa-sort-up',
        cssIconDesc: 'fas fa-sort-down'
    });

    $('thead th.paid-title').data('sortBy', function (th, td, tablesort) {
        return $(td).find('.btn').data('paid');
    });

    $('thead th.numeric-title').data('sortBy', function (th, td, tablesort) {
        return parseInt($(td).html().replace('€', ''));
    });

    $('a.paid-button').click(function() {
        var id = $(this).data('id');
        var paid = $(this).data('paid');
        var button = $(this);
        $.ajax({
            url: '/api/v1/pizzas/orders/' + id + '/',
            type: 'PATCH',
            data: JSON.stringify({paid: !paid}),
            headers : {
                'X-CSRFToken': csrfToken,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        }).done(function(data) {
            button.data('paid', data.paid);
            if (data.paid) {
                button.addClass('btn-success');
                button.removeClass('btn-danger');
                button.html(gettext('Yes'));
            } else {
                button.addClass('btn-danger');
                button.removeClass('btn-success');
                button.html(gettext('No'));
            }
            button.blur();
        }).fail(function(xhr) {
            var data = $.parseJSON(xhr.responseText);
            if (data.message !== undefined) {
                alert(data.message);
            } else if (data.paid !== undefined) {
                alert(data.paid.join('\n'));
            }
        });
    });
});
