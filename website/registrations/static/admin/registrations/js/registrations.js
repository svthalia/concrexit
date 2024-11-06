django.jQuery(function () {
    var $ = django.jQuery;
    $(".registrations-row a").click(function(e) {
        e.preventDefault();
        var didConfirm = confirm("Are you sure you want to excecute this action? Be warned that this doesn't save the form.");
        if(didConfirm) {
            var action = $(e.target).data('action');
            var href = $(e.target).data('href');
            var form = $('<form></form>');
            form.attr("method", "post");
            form.attr("action", href);

            var field = $('<input/>');
            field.attr("type", "hidden");
            field.attr("name", 'action');
            field.attr("value", action);
            form.append(field);

            var csrf = $('<input/>');
            csrf.attr("type", "hidden");
            csrf.attr("name", 'csrfmiddlewaretoken');
            csrf.attr("value", $("input[name='csrfmiddlewaretoken']").val());
            form.append(csrf);

            $(document.body).append(form);
            form.submit();
        }
        return false;
    });
});
