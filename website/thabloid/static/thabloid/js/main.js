$(function () {
    mixitup('#thabloid-index', {
        selectors: {
            control: '.nav-link'
        }
    });

    $('#thabloid-index .thabloid-card .btn.open').click(function (e) {
        e.preventDefault();
        $.ajax(this.href).done(function (data) {
            $.fancybox(data,
                {
                    padding: 0,
                    tpl: {
                        closeBtn: '<a title="Close" class="btn btn-secondary fancybox-close" href="javascript:;"><i class="fas fa-times"></i></a>',
                        next: '<a title="Next" class="fancybox-nav fancybox-next" href="javascript:;"><span class="btn btn-secondary"><i class="fas fa-arrow-right"></i></span></a>',
                        prev: '<a title="Previous" class="fancybox-nav fancybox-prev" href="javascript:;"><span class="btn btn-secondary"><i class="fas fa-arrow-left"></i></span></a>'
                    },
                    loop: false,
                    openEffect: 'elastic',
                    closeEffect: 'elastic',
                    helpers: {
                        overlay: {
                            css: {'background-color': 'rgba(0, 0, 0, 0.9)'},
                            locked: true
                        }
                    }
                });
        });
    });
});
