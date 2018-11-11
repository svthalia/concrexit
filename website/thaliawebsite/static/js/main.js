$(function () {
    $('[data-toggle="tooltip"]').tooltip();

    $("#language-switcher").click(function (e) {
        e.preventDefault();
        $("#change-language-form").submit();
        return false;
    });
});

$.fancybox.defaults.btnTpl.close = '<a title="{{CLOSE}}" class="fancybox-button fancybox-button--close" data-fancybox-close href="javascript:;"><i class="fas fa-times"></i></a>';
$.fancybox.defaults.btnTpl.arrowRight = '<a title="{{NEXT}}" class="fancybox-button fancybox-button--arrow_right" data-fancybox-next href="javascript:;"><i class="fas fa-arrow-right"></i></a>';
$.fancybox.defaults.btnTpl.arrowLeft = '<a title="{{PREV}}" class="fancybox-button fancybox-button--arrow_left" data-fancybox-prev href="javascript:;"><i class="fas fa-arrow-left"></i></a>';
$.fancybox.defaults.btnTpl.thumbs = '<a title="{{THUMBS}}" class="fancybox-button fancybox-button--thumbs" data-fancybox-thumbs href="javascript:;"><i class="fas fa-th"></i></a>';
$.fancybox.defaults.btnTpl.download = '<a title="{{DOWNLOAD}}" class="fancybox-button fancybox-button--download" data-fancybox-download href="javascript:;"><i class="fas fa-download"></i></a>';
$.fancybox.defaults.i18n.django = {
    CLOSE: gettext('Close'),
    NEXT: gettext('Next'),
    PREV: gettext('Previous'),
    ERROR: gettext('The requested content cannot be loaded. <br/> Please try again later.'),
    PLAY_START: gettext("Start slideshow"),
    PLAY_STOP: gettext("Pause slideshow"),
    FULL_SCREEN: gettext("Full screen"),
    THUMBS: gettext("Thumbnails"),
    DOWNLOAD: gettext("Download"),
    SHARE: gettext("Share"),
    ZOOM: gettext("Zoom")
};
$.fancybox.defaults.lang = 'django';
