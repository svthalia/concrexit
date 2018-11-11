$(function () {
    mixitup('#thabloid-index', {
        selectors: {
            control: '.nav-link'
        }
    });

    $('#thabloid-index .thabloid-card .btn.open').click(function (e) {
        e.preventDefault();
        var downloadLink = $(this).next('.download').attr('href');
        $.ajax(this.href).done(function (data) {
            $.fancybox.open(data,
                {
                    buttons: [
                        "download",
                        "thumbs",
                        "close"
                    ],
                    afterShow: function (instance, current) {
                        $(instance.$refs.container)
                            .find("[data-fancybox-download]")
                            .attr("href", downloadLink);
                    }
                });
        });
    });
});
