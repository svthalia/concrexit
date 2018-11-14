$(function () {
    $(".photo-card a").fancybox({
        buttons: [
            "download",
            "thumbs",
            "close"
        ],
        afterShow: function(instance, current) {
            $(instance.$refs.container)
              .find("[data-fancybox-download]")
              .attr("href", current.opts.download);
        }
    });
});
