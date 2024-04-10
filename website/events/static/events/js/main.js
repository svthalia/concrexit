const BIRTHDAYS_COOKIE = 'showbirthdays';
const VIEW_COOKIE = 'calendarview';
const DATE_STORAGE = 'calendardate';
const SOURCES = {
    events: {
        id: 'event',
        url: '/api/calendarjs/events/',
    },
    birthdays: {
        id: 'birthdays',
        url: '/api/calendarjs/birthdays/',
    },
    external: {
        id: 'external',
        url: '/api/calendarjs/external/',
    },
    unpublished: {
        id: 'unpublished',
        url: '/api/calendarjs/events/unpublished/',
    },
};

function checkViewState(calendar) {
    let buttonText = gettext('show birthdays');
    if (calendar.getEventSourceById(SOURCES.birthdays.id)) {
        calendar.getEventSourceById(SOURCES.birthdays.id).remove();
    }
    if (window.innerWidth <= 768) {
        calendar.setOption('header', {
            right: ''
        });
    } else {
        if (calendar.view.type === 'list') {
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
    const showBirthdaysBtn = calendar.el.querySelector('.fc-showBirthdays-button');
    if (showBirthdaysBtn) {
        showBirthdaysBtn.innerHTML = buttonText;
    }
}

function strip(html){
   let doc = new DOMParser().parseFromString(html, 'text/html');
   return doc.body.textContent || "";
}

document.addEventListener('DOMContentLoaded', function () {
    let lastKnownWidth = window.innerWidth;
    const calendarEl = document.getElementById('calendar');

    const showUnpublished = calendarEl.dataset.showUnpublished === 'true';
    let defaultDate = calendarEl.dataset.defaultDate;
    const isAuthenticated = calendarEl.dataset.authenticated === 'true';
    const language = calendarEl.dataset.language;

    const eventSources = [SOURCES.events, SOURCES.external];
    if (showUnpublished) {
        eventSources.push(SOURCES.unpublished);
    }
    if (Cookies.get(BIRTHDAYS_COOKIE)) {
        eventSources.push(SOURCES.birthdays);
    }

    let defaultView = window.innerWidth < 979 ? 'list' : 'timeGridWeek';
    if (Cookies.get(VIEW_COOKIE) !== undefined && window.innerWidth >= 979) {
        defaultView = Cookies.get(VIEW_COOKIE);
    }

    if (sessionStorage.getItem(DATE_STORAGE)) {
        defaultDate = sessionStorage.getItem(DATE_STORAGE);
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        plugins: ['timeGrid', 'dayGrid', 'bootstrap', listViewPlugin],
        aspectRatio: 1.8,
        themeSystem: 'bootstrap',
        defaultView: defaultView,
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
        eventClick: function ({ jsEvent, event }) {
            if (event.url && event.extendedProps.blank) {
                jsEvent.preventDefault();
                window.open(event.url, '_blank');
            }
        },
        eventRender: function ({ el, event, isStart, view }) {
            el.setAttribute(
                'title', event.extendedProps.description);
            if (isStart && view.type !== 'list') {
                const regInfoElem = document.createElement('div');
                regInfoElem.classList.add('mt-2', 'fc-title');
                regInfoElem.title = event.extendedProps.registration_info;
                regInfoElem.textContent = strip(event.extendedProps.registration_info);
                el.children[0].appendChild(regInfoElem);
            }
        },
        viewSkeletonRender: function ({ view }) {
            const prevView = Cookies.get(VIEW_COOKIE);

            if (view.type !== prevView) {
                Cookies.set(VIEW_COOKIE, view.type);
                checkViewState(calendar);
            }
        },
        datesRender: function () {
            const date = calendar.getDate();
            sessionStorage.setItem(DATE_STORAGE, date.toISOString());
        },
        windowResize: function () {
            if (window.innerWidth !== lastKnownWidth) {
                lastKnownWidth = window.innerWidth;
                const view = (lastKnownWidth <= 768) ? 'list' : Cookies.get(VIEW_COOKIE);
                const currentView = calendar.view;
                if (view !== currentView.type) {
                    calendar.changeView(view);
                } else {
                    checkViewState(calendar);
                }
            }
        }
    });

    calendar.render();
    checkViewState(calendar);
});
