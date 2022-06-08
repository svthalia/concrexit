Fancybox.bind('[data-fancybox="gallery"]',
    {
        Toolbar: {
            display: [
                "thumbs",
                "close",
            ],
        },
    }
);

$(function () {
    var windowhash = window.location.hash;
    if (windowhash) {
        var element = $('[data-bs-target="' + windowhash + '"]');
        element.click();
        $([document.documentElement, document.body]).scrollTop(element.offset().top);
    }

    $('.card-header a').click(function (e) {
        e.preventDefault();
    });

    $('.external-vacancy').click(function (e) {
        e.preventDefault();
        var href = $(e.target).attr('href');
        var element = $('[data-bs-target="' + href + '"]');
        element.click();
        $([document.documentElement, document.body]).scrollTop(element.offset().top);
    });

    mixitup('#partners-vacancies', {
        selectors: {
            control: '.nav-link'
        }
    });
});
