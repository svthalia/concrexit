var FC = $.fullCalendar; // a reference to FullCalendar's root namespace
var View = FC.View;      // the class that all views must inherit from
var ListView;          // our subclass

ListView = View.extend({ // make a subclass of View

    title: gettext("Upcoming Events"),

    updateTitle: function () {
        // this space intentionally left blank
    },

    computeRange: function (date) {
        var range = View.prototype.computeRange.call(this, date);
        range.end.add(1, 'years');
        return range;
    },

    renderEvents: function (events) {
        var ul = $('<ul>').addClass('toggles');

        if (this.opt('maxEvents') != undefined) {
            events = events.slice(0, this.opt('maxEvents'));
        }

        events.sort(function (a, b) {
            return a.start < b.start ? -1 : a.start > b.start ? 1 : 0;
        });

        for (var i = 0; i < events.length; i++) {
            var e = events[i];
            var li = $('<li>').attr('id', 'event' + i);
            var date = e.start.date() + '-' + (e.start.month() + 1) + '-' + e.start.year(); // Javascript you so silly
            if (!e.is_birthday) {
                li.append('<div class="toggle-title"><a href="#"><span></span>' + e.title + ' (' + date + ')</a></div>');

                if (e.blank) {
                    li.append('<div class="toggle-content">' + e.description + '<br><br><a target="_blank" href="' + e.url + '">' + gettext('> To the event page') + '</a></div>');
                } else {
                    li.append('<div class="toggle-content">' + e.description + '<br><br><a href="' + e.url + '">' + gettext('> To the event page') + '</a></div>');
                }
            } else {
                li.append('<div class="toggle-title birthday"><a href="#">' + e.title + ' (' + date + ')</a></div>');
            }

            if (e.registered) {
                li.append('<div class="event-indication" title="' + gettext("Registered for this event") + '"><div class="has-registration"></div></div>');
            } else if (e.registered !== null) {
                li.append('<div class="event-indication" title="' + gettext("Not registered for this event") + '"><div class="no-registration"></div></div>');
            }

            if (e.backgroundColor !== null) {
                li.css('background-color', e.backgroundColor);
            }

            if (e.textColor !== null) {
                li.find(".toggle-title a").css('color', e.textColor);
                li.find(".toggle-content a").css('color', e.textColor);
            }

            ul.append(li);
        }
        // This originates from theme_thimbus/themes/thimbus/assets/js/scripts_dev.js,
        // but was only executed when the document was rendered, and not afterwards.
        // By including it here, the toggle above also gets rendered.
        ul.delegate('.toggle-title', 'click', function (e) {
            var $this = $(this), $parent = $this.closest('li');
            e.preventDefault();
            if ($this.hasClass('birthday')) {
                return;
            }
            if ($parent.hasClass('current')) {
                $parent.removeClass('current').find('.toggle-content').stop().css('display', 'block').slideUp(500, 'easeOutExpo');
            } else {
                $parent.addClass('current').find('.toggle-content').stop().css('display', 'none').slideDown(500, 'easeOutExpo');
                $parent.siblings('.current').find('.toggle-title').trigger('click');
            };
        });
        this.el.html(ul);

        $('.event-indication').tooltip();
    },
});

FC.views.list = ListView; // register our class with the view system
