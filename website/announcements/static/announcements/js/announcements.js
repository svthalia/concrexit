(function() {
    $('.announcement .close').click(function() {
        $(this).parent().remove();
        $.ajax({
            // make sure this matches the url defined in announcements/urls.py
            url: "/announcements/close-announcement",
            type: "POST",
            beforeSend: function(xhr){
                xhr.setRequestHeader("X-CSRFToken", Cookies.get('csrftoken'));
            },
            data: {id: $(this).data('announcement-id')},
        })
    });
})();
