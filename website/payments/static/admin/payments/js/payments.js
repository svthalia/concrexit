django.jQuery(function () {
    var $ = django.jQuery;
    $(".payments-row a").click(function(e) {
        e.preventDefault();
        var type = $(e.target).data('type');
        var href = $(e.target).data('href');
        var form = $('<form></form>');
        form.attr("method", "post");
        form.attr("action", href);

        var field = $('<input/>');
        field.attr("type", "hidden");
        field.attr("name", 'type');
        field.attr("value", type);
        form.append(field);

        var csrf = $('<input/>');
        csrf.attr("type", "hidden");
        csrf.attr("name", 'csrfmiddlewaretoken');
        csrf.attr("value", $("input[name='csrfmiddlewaretoken']").val());
        form.append(csrf);

        $(document.body).append(form);
        form.submit();
    });
});
