$(function() {
    $('table').tablesort();

    $('thead th.paid-title, thead th.collected-title').data('sortBy', function (th, td, tablesort) {
        return $(td).find('.btn').val();
    });

    $('input.paid-button').click(function() {
        var id = $(this).data('id');
        var button = $(this);
        $.post(paid_url, {'order': id, 'csrfmiddlewaretoken': csrf_token}, function(data) {
            if(data.success === 1) {
                button.addClass('btn-style' + (4 - data.paid));
                button.removeClass('btn-style' + (3 + data.paid));
                button.val(data.paid ? gettext('Yes') : gettext('No'));
                button.blur();
            }
            else {
                alert(data.error);
            }
        });
    });
});
