var FC = $.fullCalendar; // a reference to FullCalendar's root namespace
var View = FC.View;      // the class that all views must inherit from
var ListView;          // our subclass

ListView = View.extend({
    title: gettext("Upcoming Events"),

    computeTitle: function (d) {
        return this.title;
    },

    fetchInitialEvents: function (dateProfile) {
        var calendar = this.calendar;
        var today = new Date();

        return calendar.requestEvents(
            calendar.msToMoment(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0), false),
            calendar.msToMoment(Date.UTC(today.getFullYear() + 2, today.getMonth(), today.getDate(), 0, 0, 0), false)
        );
    },

    renderEvents: function (events) {
        var root = $("<div>").addClass("accordion bordered");

        events.sort(function (a, b) {
            return a.start < b.start ? -1 : a.start > b.start ? 1 : 0;
        });

        if (events.length === 0) {
            this.el.html('<div class="alert alert-info">' + gettext('No events planned in the selected period.') +'</div>');
        }

        for (var i = 0; i < events.length; i++) {
            var e = events[i];
            if (e.is_birthday) {
                break;
            }

            var date = e.start.format('YYYY-MM-DD HH:mm');

            var eventCard = $("<div>").addClass("card mb-0");

            var eventIndicator = $("<div>")
                .addClass("event-indication")
                .attr("style", "background-color: " + e.backgroundColor);
            var cardHead = $("<div>").addClass("card-header collapsed")
                .attr("data-toggle", "collapse")
                .attr("data-target", "#event-content-" + i);

            cardHead.append(eventIndicator);
            cardHead.append("<div class=\"title\">" + e.title + " " +
                "(<span class=\"date\">" + date + "</span>)</div>");

            var cardContent = $("<div>")
                .addClass("collapse")
                .attr("id", "event-content-" + i);

            var url = $("<a>")
                .addClass("btn btn-primary")
                .attr("href", e.url)
                .attr("target", e.blank ? "_blank" : "_self")
                .html(gettext("Go to event"));

            var cardBody = $("<div>")
                .addClass("card-body")
                .html("<p>" + e.description + "</p>");
            cardBody.append(url);

            cardContent.append(cardBody);
            eventCard.append(cardHead);
            eventCard.append(cardContent);

            root.append(eventCard);
            this.el.html(root);
        }
    },
});

FC.views.list = ListView; // register our class with the view system
