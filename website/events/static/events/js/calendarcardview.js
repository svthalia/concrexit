var FC = $.fullCalendar; // a reference to FullCalendar's root namespace
var View = FC.View;      // the class that all views must inherit from
var CardView;          // our subclass

CardView = View.extend({ // make a subclass of View

    title: 'Aankomende evenementen',
    months: ['Jan', 'Feb', 'Maa', 'Apr', 'Mei', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec'],

    updateTitle: function() {
        // this space intentionally left blank
    },

    computeRange: function(date) {
        var range = View.prototype.computeRange.call(this, date);
        range.end.add(1, 'years');
        return range;
    },

    renderEvents: function(events) {
        wrapperDiv = $('<div>').addClass('blog');
        wrapperUl = $('<ul>').addClass('row');

        if (this.opt('maxEvents') != undefined) {
            events = events.slice(0, this.opt('maxEvents'));
        }

        events.forEach(function (event) {
            html =
            '<li class="post span6 has-overlay event">' +
              '<a href="'+ event.url +'">' +
                '<div class="post-inner">' +
                  '<div class="post-body">' +
                    '<h2>' + event.title + '</h2>' +
                    '<div class="post-date circle">' +
                      '<div class="circle-border"></div>' +
                      '<div class="circle-inner">' + event.start.date() +
                        '<span>' + this.months[event.start.month()] + '</span>'+
                      '</div>' +
                    '</div>'+
                    '<div class="post-excerpt">' +
                      '<p>' + this.trimDescription(event.description, 135) + '</p>' +
                    '</div>' +
                  '</div>' +
                '</div>' +
              '</a>' +
            '</li>';

            wrapperUl.append($(html));
        }.bind(this));
        wrapperDiv.append(wrapperUl);
        this.el.html(wrapperDiv);
    },

    trimDescription: function(description, maxLength) {
        description += " ";
        var trimmedString = description.substr(0, maxLength);

        // retrim if possibly in middle of a word
        if (trimmedString != description) {
            trimmedString = trimmedString.substr(0, Math.min(trimmedString.length, trimmedString.lastIndexOf(" ")));
            trimmedString += "...";
        }

        return trimmedString.trim();
    }
});

FC.views.card = CardView; // register our class with the view system
