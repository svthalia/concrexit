$(function () {
    mixitup('#education-courses', {
        selectors: {
            control: '.nav-link'
        },
        animation: {
           enable: false
        }
    });

    $('.table-clickable tbody tr').click(function() {
        window.location = $(this).data('link');
    })
});