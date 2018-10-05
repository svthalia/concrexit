$(function () {
    console.log('hello');
    $(".partner-image-card a").fancybox({
        helpers: {
            title: {
                type: 'float'
            }
        },
        padding: 0
    });

    var windowhash = window.location.hash;
    $('[data-target="' + windowhash + '"]').click();

    $('.card-header a').click(function (e) {
        e.preventDefault();
    });
});
