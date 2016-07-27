$(function() {
    function scrollSlider(slider, direction) {
        var wrapper = slider.children('.policywrapper');
        var delta = direction * (slider.width() + 20); // +20 for margin
        if (wrapper.scrollLeft() + delta <= 0) {
            slider.children('.slider-control-prev').fadeOut(200);
        }
        else {
            slider.children('.slider-control-prev').fadeIn(200);
        }
        if (wrapper.scrollLeft() + 2*delta >= wrapper.children('ul').width()) {
            slider.children('.slider-control-next').fadeOut(200);
        }
        else {
            slider.children('.slider-control-next').fadeIn(200);
        }
        wrapper.animate({scrollLeft: wrapper.scrollLeft() + delta});
    }

    $('.slider-control-next').click(function() {
        scrollSlider($(this).parent(), 1);
    });

    $('.slider-control-prev').click(function() {
        scrollSlider($(this).parent(), -1);
    });
});
