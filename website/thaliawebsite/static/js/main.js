$(function () {
    $('[data-toggle="tooltip"]').tooltip();

    $("#language-switcher").click(function(e) {
        e.preventDefault();
        $("#change-language-form").submit();
        return false;
    });
});
