function checkResponsiveState(calendarElement, windowWidth, view) {
    if (windowWidth <= 768) {
        calendarElement.fullCalendar('option', 'header', {
            right: 'prev,next today'
        });
    } else {
        if (view.name === 'list') {
            calendarElement.fullCalendar('option', 'header', {
                right: 'list,agendaWeek,month prev,next today'
            });
        } else {
            calendarElement.fullCalendar('option', 'header', {
                right: 'showBirthdays, list,agendaWeek,month prev,next today'
            });
        }
    }
}

$(function () {
    var calendarElement = $('#calendar');
    var sources = {
        events: "/api/v1/events/calendarjs",
        birthdays: "/api/v1/members/birthdays",
        partners: "/api/v1/partners/calendarjs",
        unpublishedEvents: "/api/v1/events/unpublished"
    };

    var showUnpublished = calendarElement.data('show-unpublished');
    var defaultDate = calendarElement.data('default-date');
    var isAuthenticated = calendarElement.data('authenticated');
    var language = calendarElement.data('language');

    var eventSources = [sources.events, sources.partners];
    if (showUnpublished) {
        eventSources.push(sources.unpublishedEvents);
    }
    if (Cookies.get('showbirthdays')) {
        eventSources.push(sources.birthdays);
    }
    var tmpView = ($(window).width() < 979) ? 'list' : 'agendaWeek';
    if (Cookies.get('agendaview') !== undefined) {
        tmpView = Cookies.get('agendaview');
    }

    // History idea and code parts from
    // https://github.com/fullcalendar/fullcalendar/issues/659#issuecomment-132535804
    // and https://github.com/fullcalendar/fullcalendar/issues/659#issuecomment-245544401
    var startDate = new Date(defaultDate);
    var tmpYear = startDate.getFullYear();
    var tmpMonth = startDate.getMonth();
    var tmpDay = startDate.getDate();
    var vars = window.location.hash.split("&");
    for (var i = 0; i < vars.length; i++) {
        if (vars[i].match("^#year")) tmpYear = vars[i].substring(6);
        if (vars[i].match("^month")) tmpMonth = vars[i].substring(6) - 1;
        if (vars[i].match("^day")) tmpDay = vars[i].substring(4);
        if (vars[i].match("^view")) tmpView = vars[i].substring(5);
    }

    calendarElement.fullCalendar({
        aspectRatio: 1.8,
        theme: 'bootstrap4',
        eventSources: eventSources,
        defaultView: tmpView,
        firstDay: 1,
        scrollTime: '14:00:00',
        timeFormat: 'HH:mm',
        eventLimit: true,
        locale: language,
        views: {
            list: {
                buttonText: gettext('list'),
                duration: {weeks: 1}
            }
        },
        defaultDate: defaultDate,
        customButtons:
            isAuthenticated ? {
                showBirthdays: {
                    text: Cookies.get('showbirthdays') ? gettext('hide birthdays') : gettext('show birthdays'),
                    click: function (e) {
                        if (e.target.innerHTML == gettext('hide birthdays')) {
                            e.target.innerHTML = gettext('show birthdays');
                            Cookies.remove('showbirthdays');
                            calendarElement.fullCalendar('removeEventSource', sources.birthdays);
                        } else {
                            e.target.innerHTML = gettext('hide birthdays');
                            Cookies.set('showbirthdays', 1);
                            calendarElement.fullCalendar('addEventSource', sources.birthdays);
                        }
                    }
                }
            } : {}
        ,
        header: {
            right: 'showBirthdays, list,agendaWeek,month prev,next today'
        },
        eventClick: function (event) {
            if (event.url && event.blank) {
                window.open(event.url, '_blank');
                return false;
            } else if (event.url) {
                window.replace(event.url);
                return false;
            }
        },
        eventRender: function (event, element) {
            element.attr('title', event.description);
        },
        viewRender: function (view) {
            var prevView = Cookies.get('agendaview');
            var moment = calendarElement.fullCalendar('getDate');
            if (moment && moment.isValid()) {
                window.location.hash = 'year=' + moment.format('YYYY') + '&month=' + (moment.format('M')) + '&day=' + moment.format('DD') + '&view=' + view.name;
            }

            if (view.name !== prevView) {
                var windowWidth = $(window).width();
                Cookies.set('agendaview', view.name);
                checkResponsiveState(calendarElement, windowWidth, view.name);
            }
        }
        ,
        windowResize: function () {
            var windowWidth = $(window).width();
            var view = (windowWidth <= 768) ? 'list' : Cookies.get('agendaview');
            var currentView = $('#calendar').fullCalendar('getView');
            if (view !== currentView.name) {
                calendarElement.fullCalendar('changeView', view);
            } else {
                checkResponsiveState(calendarElement, windowWidth, currentView.name);
            }
        }
    })
    ;

    var date = new Date(tmpYear, tmpMonth, tmpDay, 0, 0, 0);
    var moment = calendarElement.fullCalendar('getDate');
    var view = calendarElement.fullCalendar('getView');
    if (date.getFullYear() !== moment.format('YYYY') ||
        date.getMonth() !== moment.format('M') ||
        date.getDate() !== moment.format('DD')) {
        calendarElement.fullCalendar('gotoDate', date);
    }

    if (view.name !== tmpView) {
        calendarElement.fullCalendar('changeView', tmpView);
    } else {
        var windowWidth = $(window).width();
        checkResponsiveState(calendarElement, windowWidth, view);
    }
});
