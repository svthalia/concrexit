$(function() {

    function select_meeting(year) {
        $("#meetingcontainer > div").hide();
        $("#meeting-"+year).show();
        fix_heights($("#meeting-"+year));
    }

    $(".meeting-btn").on('click', function(e) {
        select_meeting($(this).data('year'));
    })

    $("#alvselect").on('change', function(e) {
        select_meeting($("#alvselect").val());
    })

    function fix_heights(obj) {
        var heights = new Array();

        // // Loop to get all element heights
        obj.find('.gw-go-col').each(function() {
            // Need to let sizes be whatever they want so no overflow on resize
            $(this).css('min-height', '0');
            $(this).css('max-height', 'none');
            $(this).css('height', 'auto');

            // Then add size (no units) to array
            heights.push($(this).height());
        });

        // // Find max height of all elements
        var max = Math.max.apply( Math, heights );

        // // Set all heights to max height
        obj.find('.gw-go-col').each(function() {
            $(this).css('height', max + 'px');
        });
    };

    fix_heights($("#meetingcontainer > div"));
});
