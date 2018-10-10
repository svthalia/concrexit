$(function () {
    $(".partner-image-card a").fancybox({
        helpers: {
            title: {
                type: 'float'
            }
        },
		padding: 0,
        tpl: {
		    closeBtn: '<a title="Close" class="btn btn-primary fancybox-close" href="javascript:;"><i class="fas fa-times"></i></a>',
            next: '<a title="Next" class="fancybox-nav fancybox-next" href="javascript:;"><span class="btn btn-primary"><i class="fas fa-arrow-right"></i></span></a>',
            prev: '<a title="Previous" class="fancybox-nav fancybox-prev" href="javascript:;"><span class="btn btn-primary"><i class="fas fa-arrow-left"></i></span></a>'
        }
    });

    var windowhash = window.location.hash;
    if (windowhash) {
        var element = $('[data-target="' + windowhash + '"]');
        element.click();
        $([document.documentElement, document.body]).scrollTop(element.offset().top);
    }

    $('.card-header a').click(function (e) {
        e.preventDefault();
    });

    $('.external-vacancy').click(function (e) {
        e.preventDefault();
        var href = $(e.target).attr('href');
        var element = $('[data-target="' + href + '"]');
        element.click();
        $([document.documentElement, document.body]).scrollTop(element.offset().top);
    });

    mixitup('#partners-vacancies', {
        selectors: {
            control: '.nav-link'
        }
    });
});
