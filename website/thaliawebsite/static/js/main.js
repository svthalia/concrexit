$(function () {
    $('[data-toggle="tooltip"]').tooltip();

    $("#language-switcher").click(function(e) {
        e.preventDefault();
        var selector = $("#language-switcher");
        var next = selector.data('next');
        var lang = selector.data('lang');
        var href = selector.data('href');

        var form = $('<form></form>');
        form.attr("method", "post");
        form.attr("action", href);

        var langField = $('<input/>');
        langField.attr("type", "hidden");
        langField.attr("name", "language");
        langField.attr("value", lang);
        form.append(langField);

        var nextField = $('<input/>');
        nextField.attr("type", "hidden");
        nextField.attr("name", "next");
        nextField.attr("value", next);
        form.append(nextField);

        var csrfField = $('<input/>');
        csrfField.attr("type", "hidden");
        csrfField.attr("name", 'csrfmiddlewaretoken');
        csrfField.attr("value", Cookies.get('csrftoken'));
        form.append(csrfField);

        $(document.body).append(form);
        form.submit();
        return false;
    });
});
