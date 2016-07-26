$(function() {

    function select_meeting(year) {
        $("#alvcontainer > div").hide();
        $("#meeting-"+year).show();
    }

    $(".meeting-btn").on('click', function(e) {
        select_meeting($(this).data('year'));
    })

    $("#alvselect").on('change', function(e) {
        select_meeting($("#alvselect").val());
    })

});
