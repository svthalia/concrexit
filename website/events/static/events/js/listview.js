class ListView extends FullCalendar.View {
    renderEvents(eventStore, eventUiHash) {
        const skeleton = document.createElement('div');
        skeleton.id = 'fc-listview';
        skeleton.classList.add('accordion', 'bordered');

        const locale = this.dateEnv.locale.codeArg;
        const now = new Date();
        const events = Object.values(eventStore.instances)
            .filter(function (value) {
                return value.range.end > now;
            })
            .sort(function (a, b) {
                return a.range.start < b.range.start ? -1 :
                    a.range.start > b.range.start ? 1 : 0;
            });

        if (events.length === 0) {
            var alertEl = document.createElement('div');
            alertEl.id = 'fc-no-events';
            alertEl.classList.add('alert', 'alert-info');
            alertEl.append(gettext('No events planned in the selected period.'));
            this.el.append(alertEl);
        }

        for (let i = 0; i < events.length; i++) {
            const instance = events[i];
            const def = eventStore.defs[instance.defId];

            if (def.extendedProps.isBirthday) {
                break;
            }

            var date = instance.range.start.toLocaleDateString(locale, {
                hour: '2-digit',
                minute: '2-digit',
                day: 'numeric',
                month: 'long',
                weekday: 'long',
                year: 'numeric',
                timeZone: 'UTC',
                hour12: locale !== 'nl',
            });

            const eventCard = document.createElement('div');
            eventCard.classList.add('card', 'mb-0');

            const eventIndicator = document.createElement('div');
            eventIndicator.classList.add('event-indication');
            eventIndicator.classList.add(def.ui.classNames);
            eventIndicator.dataset.bsToggle = 'tooltip';
            eventIndicator.dataset.bsOriginalTitle = def.extendedProps.registration_info;
            eventIndicator.title = def.extendedProps.registration_info;

            const cardHead = document.createElement('div');
            cardHead.classList.add('card-header', 'collapsed');
            cardHead.dataset.bsToggle = 'collapse';
            cardHead.dataset.bsTarget = '#event-content-' + i;

            const cardTitle = document.createElement('div');
            cardTitle.classList.add('title');
            const cardDate = document.createElement('span');
            cardDate.append(date);
            cardTitle.append(def.title + ' (');
            cardTitle.append(cardDate);
            cardTitle.append(')');

            cardHead.append(eventIndicator);
            cardHead.append(cardTitle);

            const cardContent = document.createElement('div');
            cardContent.classList.add('collapse');
            cardContent.id = 'event-content-' + i;

            const url = document.createElement('a');
            url.classList.add('btn', 'btn-primary');
            url.href = def.url;
            url.target = def.extendedProps.blank ? '_blank' : '_self';
            url.append(gettext("Go to event"));

            const cardBody = document.createElement('div');
            cardBody.classList.add('card-body');
            const cardBodyText = document.createElement('p');
            cardBodyText.append(def.extendedProps.description);
            cardBody.append(cardBodyText);
            cardBody.append(url);

            cardContent.append(cardBody);
            eventCard.append(cardHead);
            eventCard.append(cardContent);

            skeleton.append(eventCard);
        }
        this.el.append(skeleton);
        $('[data-bs-toggle="tooltip"]').tooltip();
    }

    unrenderEvents() {
        const noEventsEl = this.el.querySelector('#fc-no-events');
        if (noEventsEl) {
            noEventsEl.remove();
        }

        const listView = this.el.querySelector('#fc-listview');
        if (listView) {
            listView.remove();
        }
    }
}

const listViewPlugin = FullCalendar.createPlugin({
    views: {
        list: ListView
    }
});
