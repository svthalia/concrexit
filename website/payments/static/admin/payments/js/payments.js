(django.jQuery || jQuery)(function () {
    var $ = django.jQuery || jQuery;
    $(".payments-row a.process").click(function(e) {
        e.preventDefault();
        var type = $(e.target).data('type');
        var next = $(e.target).data('next');
        var href = $(e.target).data('href');
        var form = $('<form></form>');
        form.attr("method", "post");
        form.attr("action", href);

        var field = $('<input/>');
        field.attr("type", "hidden");
        field.attr("name", 'type');
        field.attr("value", type);
        form.append(field);

        if (next) {
            var redirect = $('<input/>');
            redirect.attr("type", "hidden");
            redirect.attr("name", 'next');
            redirect.attr("value", window.location);
            form.append(redirect);
        }

        var csrf = $('<input/>');
        csrf.attr("type", "hidden");
        csrf.attr("name", 'csrfmiddlewaretoken');
        csrf.attr("value", $("input[name='csrfmiddlewaretoken']").val());
        form.append(csrf);

        $(document.body).append(form);
        form.submit();
    });
});
