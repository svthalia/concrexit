django.jQuery(function () {
    var $ = django.jQuery;

    function pad(num, size) {
        var s = "0" + num;
        return s.substr(s.length-size);
    }

    function formatDate(dateStr, format) {
        var date = new Date(dateStr);
        var day = date.getDate();
        var month = date.getMonth() + 1;
        var year = date.getFullYear();
        var hours = date.getHours();
        var minutes = date.getMinutes();
        var seconds = date.getSeconds();

        if (format === 'time') {
            return pad(hours, 2) + ':' + pad(minutes, 2) + ':' + pad(seconds, 2);
        }
        return year + '-' + pad(month, 2) + '-' + day;
    }

    function setFields(id, data) {
        $('#id_newsletterevent_set-' +  id + '-title')
            .val(data['title']);
        tinyMCE.get('id_newsletterevent_set-' +  id + '-description')
            .setContent(data['description']);
        $('#id_newsletterevent_set-' +  id + '-what')
            .val(data['title']);
        $('#id_newsletterevent_set-' +  id + '-where')
            .val(data['location']);
        $('#id_newsletterevent_set-' + id + '-url')
            .val(window.location.origin + '/events/' + data['pk'] + '/');
        $('#id_newsletterevent_set-' +  id + '-price')
            .val(data['price']);
        $('#id_newsletterevent_set-' +  id + '-penalty_costs')
            .val(data['fine']);
        $('#id_newsletterevent_set-' + id + '-show_costs_warning')
            .prop("checked", data['fine'] !== "0.00");
        $('#id_newsletterevent_set-' +  id + '-start_datetime_0')
            .val(formatDate(data['start'], 'date'));
        $('#id_newsletterevent_set-' +  id + '-start_datetime_1')
            .val(formatDate(data['start'], 'time'));
        $('#id_newsletterevent_set-' +  id + '-end_datetime_0')
            .val(formatDate(data['end'], 'date'));
        $('#id_newsletterevent_set-' +  id + '-end_datetime_1')
            .val(formatDate(data['end'], 'time'));
    }

    function getEvent(pk, success) {
        $.ajax({
            url: '/api/v1/events/' + pk,
            type: 'GET',
            dataType: 'json'
        }).done(function(data) {
            success(data, 'en');
        });
    }

    $(".field-event select").change(function() {
        var id = $(this).attr('name')
            .replace('newsletterevent_set-', '')
            .replace('-event', '');
        getEvent($(this).val(), function(data) {
            setFields(id, data);
        });
    });
});
