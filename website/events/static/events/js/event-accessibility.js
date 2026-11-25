django.jQuery(function () {
    var $ = django.jQuery;
    var accessibility = $("#id_accessibility");
    var hindrance = $("#id_hindrance").closest(".form-row");

    function updateHindranceVisibility() {
        hindrance.toggle(!accessibility.prop("checked"));
    }

    accessibility.on("change", updateHindranceVisibility);
    updateHindranceVisibility();
});
