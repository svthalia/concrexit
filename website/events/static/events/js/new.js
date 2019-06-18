const BIRTHDAYS_COOKIE = 'showbirthdays';
const SOURCES = {
    events: "/api/v1/events/calendarjs/",
    birthdays: "/api/v1/members/birthdays/",
    partners: "/api/v1/partners/calendarjs/",
    unpublishedEvents: "/api/v1/events/unpublished/"
};

document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');

    const showUnpublished = calendarEl.dataset['show-unpublished'];
    const defaultDate = calendarEl.dataset['default-date'];
    const isAuthenticated = calendarEl.dataset.authenticated;
    const language = calendarEl.dataset.language;

    const eventSources = [SOURCES.events, SOURCES.partners];
    if (showUnpublished) {
        eventSources.push(SOURCES.unpublishedEvents);
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        timeZone: 'UTC',
        plugins: ['timeGrid', 'dayGrid'],
        defaultView: 'timeGridWeek',
        defaultDate: defaultDate,
        eventSources: eventSources,
        firstDay: 1,
        scrollTime: '14:00:00',
        timeFormat: 'HH:mm',
        eventLimit: true,
        locale: language,
        nowIndicator: true,
        header: {
            right: 'showBirthdays, list,timeGridWeek,dayGridMonth prev,next today'
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
    });

    calendar.render();
});
