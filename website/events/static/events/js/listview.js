class ListView extends FullCalendar.View {
    renderSkeleton() {
        // responsible for displaying the skeleton of the view within the already-defined
        // this.el, an HTML element
        console.log(this);
    }

    unrenderSkeleton() {
        // should undo what renderSkeleton did
    }

    renderDates(dateProfile) {
        // responsible for rendering the given dates
    }

    unrenderDates() {
        // should undo whatever renderDates does
    }

    renderEvents(eventStore, eventUiHash) {
        const events = Object.values(eventStore.instances);

        var root = $("<div>").addClass("accordion bordered");

        events.sort(function (a, b) {
            return a.range.start < b.range.start ? -1 :
                a.range.start > b.range.start ? 1 : 0;
        });

        if (events.length === 0) {
            var alertEl = document.createElement('div');
            alertEl.id = 'fc-no-events';
            alertEl.classList.add('alert', 'alert-info');
            var text = document.createTextNode(gettext('No events planned in the selected period.'));
            alertEl.appendChild(text);
            this.el.appendChild(alertEl);
        }

        for (let i = 0; i < events.length; i++) {
            const instance = events[i];
            const def = eventStore.defs[instance.defId];

            console.log(instance, def);
            console.log(def.extendedProps);

            if (def.extendedProps.isBirthday) {
                break;
            }

            // var date = def.range.start.toLocaleString();
            // console.log(def.range.start);

            // var eventCard = $("<div>").addClass("card mb-0");
            //
            // var eventIndicator = $("<div>")
            //     .addClass("event-indication")
            //     .attr("style", "background-color: " + e.backgroundColor);
            // var cardHead = $("<div>").addClass("card-header collapsed")
            //     .attr("data-toggle", "collapse")
            //     .attr("data-target", "#event-content-" + i);
            //
            // cardHead.append(eventIndicator);
            // cardHead.append("<div class=\"title\">" + e.title + " " +
            //     "(<span class=\"date\">" + date + "</span>)</div>");
            //
            // var cardContent = $("<div>")
            //     .addClass("collapse")
            //     .attr("id", "event-content-" + i);
            //
            // var url = $("<a>")
            //     .addClass("btn btn-primary")
            //     .attr("href", e.url)
            //     .attr("target", e.blank ? "_blank" : "_self")
            //     .html(gettext("Go to event"));
            //
            // var cardBody = $("<div>")
            //     .addClass("card-body")
            //     .html("<p>" + e.description + "</p>");
            // cardBody.append(url);
            //
            // cardContent.append(cardBody);
            // eventCard.append(cardHead);
            // eventCard.append(cardContent);
            //
            // root.append(eventCard);
            // this.el.appendChild(root);
        }
    }

    unrenderEvents() {
        const noEventsEl = document.getElementById('fc-no-events');
        if (noEventsEl) {
            noEventsEl.remove();
        }
        // should undo whatever renderEvents does
    }

}

const listViewPlugin = FullCalendar.createPlugin({
    views: {
        list: ListView
    }
});
