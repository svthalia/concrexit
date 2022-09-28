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
    const windowhash = window.location.hash;
    if (windowhash) {
        const element = $('[data-bs-target="' + windowhash + '"]');
        element.click();
        $([document.documentElement, document.body]).scrollTop(element.offset().top);
    }

    $('.card-header a').click(function (e) {
        e.preventDefault();
    });

    $('.external-vacancy').click(function (e) {
        e.preventDefault();
        const href = $(e.target).attr('href');
        const element = $('[data-bs-target="' + href + '"]');
        element.click();
        $([document.documentElement, document.body]).scrollTop(element.offset().top);
    });

    mixitup('#partners-vacancies', {
        selectors: {
            control: '.nav-link'
        }
    });
});
