django.jQuery(function () {
    var $ = django.jQuery;

    function switchLanguage(newLang, success) {
        var currentLang = $('html').attr('lang');
        if (currentLang === newLang) {
            success();
            return;
        }
        django.jQuery.ajax({
            url: '/i18n/setlang/',
            type: 'POST',
            data: {
                'language': newLang
            },
            headers: {
                "X-CSRFToken": Cookies.get('csrftoken')
            },
            dataType: 'json'
        }).done(function () {
            $('html').attr('lang', newLang);
            success();
        });
    }

    function pad(num, size) {
        var s = "0" + num;
        return s.substr(s.length-size);
    }

    function formatDate(dateStr, format) {
        var currentLang = $('html').attr('lang');

        var date = new Date(dateStr);
        var day = date.getDate();
        var month = date.getMonth() + 1;
        var year = date.getFullYear();
        var hours = date.getHours();
        var minutes = date.getMinutes();
        var seconds = date.getSeconds();

        if (format === 'time') {
            return pad(hours) + ':' + pad(minutes) + ':' + pad(seconds);
        }
        if (currentLang === 'nl') {
            return pad(day) + '-' + pad(month) + '-' + pad(year);
        }
        return pad(year) + '-' + pad(month) + '-' + pad(day);
    }

    function setFields(id, data, lang) {
        $('#id_newsletterevent_set-' +  id + '-title_' + lang)
            .val(data['title']);
        tinyMCE.get('id_newsletterevent_set-' +  id + '-description_' + lang)
            .setContent(data['description']);
        $('#id_newsletterevent_set-' +  id + '-what_' + lang)
            .val(data['title']);
        $('#id_newsletterevent_set-' +  id + '-where_' + lang)
            .val(data['location']);

        if (lang === 'en') {
            $('#id_newsletterevent_set-' +  id + '-price')
                .val(data['price']);
            $('#id_newsletterevent_set-' +  id + '-penalty_costs')
                .val(data['fine']);
            $('#id_newsletterevent_set-' +  id + '-start_datetime_0')
                .val(formatDate(data['start'], 'date'));
            $('#id_newsletterevent_set-' +  id + '-start_datetime_1')
                .val(formatDate(data['start'], 'time'));
            $('#id_newsletterevent_set-' +  id + '-end_datetime_0')
                .val(formatDate(data['start'], 'date'));
            $('#id_newsletterevent_set-' +  id + '-end_datetime_1')
                .val(formatDate(data['end'], 'time'));
        }
    }

    function getEvent(pk, success) {
        var originalLang = $('html').attr('lang');
        switchLanguage('nl', function () {
            $.ajax({
                url: '/api/v1/events/' + pk,
                type: 'GET',
                dataType: 'json'
            }).done(function(data) {
                success(data, 'nl');
                switchLanguage('en', function () {
                    $.ajax({
                        url: '/api/v1/events/' + pk,
                        type: 'GET',
                        dataType: 'json'
                    }).done(function(data) {
                        success(data, 'en');
                        switchLanguage(originalLang, function() {});
                    });
                });
            });
        });
    }

    $(".field-event select").change(function() {
        var id = $(this).attr('name').replace('newsletterevent_set-', '')[0];
        getEvent($(this).val(), function(data, lang) {
            setFields(id, data, lang);
        });
    });
});
