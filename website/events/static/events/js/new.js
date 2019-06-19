const BIRTHDAYS_COOKIE = 'showbirthdays';
const VIEW_COOKIE = 'calendarview';
const SOURCES = {
    events: {
        id: 'event',
        url: '/api/v1/events/calendarjs/',
    },
    birthdays: {
        id: 'birthdays',
        url: '/api/v1/members/birthdays/',
    },
    partners: {
        id: 'partners',
        url: '/api/v1/partners/calendarjs/',
    },
    unpublished: {
        id: 'unpublished',
        url: '/api/v1/events/unpublished/',
    },
};

function checkResponsiveState(calendar, windowWidth, view) {
    var buttonText = gettext('show birthdays');
    if (calendar.getEventSourceById(SOURCES.birthdays.id)) {
        calendar.getEventSourceById(SOURCES.birthdays.id).remove();
    }
    if (windowWidth <= 768) {
        calendar.setOption('header', {
            right: ''
        });
    } else {
        if (view.type === 'list') {
            calendar.setOption('header', {
                right: 'list,timeGridWeek,dayGridMonth'
            });
        } else {
            if (Cookies.get(BIRTHDAYS_COOKIE)) {
                calendar.addEventSource(SOURCES.birthdays);
                buttonText = gettext('hide birthdays');
            }
            calendar.setOption('header', {
                right: 'showBirthdays, list,timeGridWeek,dayGridMonth prev,next today'
            });
        }
    }
    $('.fc-showBirthdays-button').html(buttonText);
}

document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');

    const showUnpublished = calendarEl.dataset['show-unpublished'];
    let defaultDate = calendarEl.dataset['default-date'];
    const isAuthenticated = calendarEl.dataset.authenticated;
    const language = calendarEl.dataset.language;

    const eventSources = [SOURCES.events, SOURCES.partners];
    if (showUnpublished) {
        eventSources.push(SOURCES.unpublished);
    }
    if (Cookies.get(BIRTHDAYS_COOKIE)) {
        eventSources.push(SOURCES.birthdays);
    }
    let tmpView = ($(window).width() < 979) ? 'list' : 'timeGridWeek';
    if (Cookies.get(VIEW_COOKIE) !== undefined) {
        tmpView = Cookies.get(VIEW_COOKIE);
    }

    if (window.location.hash.indexOf('date') > -1) {
        defaultDate = window.location.hash.substr(window.location.hash.indexOf('date') + 5, 24);
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        plugins: ['timeGrid', 'dayGrid', 'bootstrap', listViewPlugin],
        aspectRatio: 1.8,
        themeSystem: 'bootstrap',
        defaultView: tmpView,
        defaultDate: defaultDate,
        eventSources: eventSources,
        firstDay: 1,
        scrollTime: '14:00:00',
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
        },
        eventLimit: true,
        locale: language,
        nowIndicator: true,
        views: {
            list: {
                buttonText: gettext('list'),
                duration: { years: 5 },
                type: 'list',
                titleFormat: function() { return gettext("Upcoming Events") },
            }
        },
        customButtons:
            isAuthenticated ? {
                showBirthdays: {
                    text: Cookies.get(BIRTHDAYS_COOKIE) ? gettext('hide birthdays') : gettext('show birthdays'),
                    click: function (e) {
                        if (Cookies.get(BIRTHDAYS_COOKIE)) {
                            e.target.innerHTML = gettext('show birthdays');
                            Cookies.remove(BIRTHDAYS_COOKIE);
                            calendar.getEventSourceById(SOURCES.birthdays.id).remove();
                        } else {
                            e.target.innerHTML = gettext('hide birthdays');
                            Cookies.set(BIRTHDAYS_COOKIE, 1);
                            calendar.addEventSource(SOURCES.birthdays);
                        }
                    }
                }
            } : {},
        header: {
            right: 'showBirthdays, list,timeGridWeek,dayGridMonth prev,next today'
        },
        eventClick: function (info) {
            console.log(info);
            // if (event.url && event.blank) {
            //     // window.open(event.url, '_blank');
            //     return false;
            // } else if (event.url) {
            //     // window.replace(event.url);
            //     return false;
            // }
        },
        eventRender: function (info) {
            info.el.setAttribute(
                'title', info.event.extendedProps.description);
        },
        viewSkeletonRender: function (info) {
            const view = info.view;
            const prevView = Cookies.get(VIEW_COOKIE);

            const date = calendar.getDate();
            window.location.hash = 'date=' + date.toISOString() + '&view=' + view.type;

            if (view.type !== prevView) {
                const windowWidth = $(window).width();
                Cookies.set(VIEW_COOKIE, view.type);
                checkResponsiveState(calendar, windowWidth, view);
            }
        },
        datesRender: function (info) {
            const date = calendar.getDate();
            window.location.hash = 'date=' + date.toISOString() + '&view=' + info.view.type;
        },
        windowResize: function () {
            const windowWidth = $(window).width();
            const view = (windowWidth <= 768) ? 'list' : Cookies.get(VIEW_COOKIE);
            const currentView = calendar.view;
            if (view !== currentView.type) {
                calendar.changeView(view);
            } else {
                checkResponsiveState(calendar, windowWidth, currentView);
            }
        }
    });

    calendar.render();

    if (calendar.view.type !== tmpView) {
        calendar.changeView(tmpView);
    } else {
        var windowWidth = $(window).width();
        checkResponsiveState(calendar, windowWidth, calendar.view);
    }
});
