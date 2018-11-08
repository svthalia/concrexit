/* Render statistics on statistics page */
var pieOptions = {
    allowPointSlect: true,
    cursor: 'pointer',
    dataLabels : {
        enabled: true,
        formatter:function() { // Omit zero values
            if(this.y != 0) {
                return this.point.name + ": " + this.y; // TODO: add newline <br /> ?
            }
        },
        distance: -50
    }
};
$(function () {
    Highcharts.theme = {
        colors: ['#AE0046', '#E62272', '#E6478A', '#CC2482', '#8E1056', '#DC3472'],
        title: {
            style: {
                color: '#000',
                font: 'bold 16px "Open Sans"'
            }
        },
        subtitle: {
            style: {
                color: '#666666',
                font: 'bold 12px "Open Sans"'
            }
        },
        credits: false,  // Free for non-profit
        legend: {
            itemStyle: {
                font: '9pt "Open Sans"',
                color: 'black'
            },
            itemHoverStyle: {
                color: 'gray'
            }
        }
    };

    var statistics = $('#members-statistics').data('statistics');
    var cohortSizes = statistics.cohort_sizes;
    var memberTypeDistribution = statistics.member_type_distribution;
    var pizzaOrders = statistics.total_pizza_orders;
    var currentPizzaOrders = statistics.current_pizza_orders;

    // Apply the theme
    Highcharts.setOptions(Highcharts.theme);

    $('#membersTypeChart').highcharts({
        chart: {
            type: 'pie'
        },
        title: {
            text: gettext('Members per member type'),
        },
        plotOptions: {
            pie: pieOptions
        },
        series: [{
            name: 'Thalianen',
            colorByPoint: true,
            data : [{
                name: gettext('Members'),
                y: memberTypeDistribution.member
            },{
                name: gettext('Benefactors'),
                y: memberTypeDistribution.supporter
            },{
                name: gettext('Honorary Members'),
                y: memberTypeDistribution.honorary
            }]
        }]
    });

    $('#totalYearChart').highcharts({
        chart: {
            type: 'pie'
        },
        title: {
            text: gettext("Total number of (honary) members and benefactors per cohort"),
        },
        plotOptions: {
            pie: pieOptions
        },
        series: [{
            name: gettext("People"),
            colorByPoint: true,
            data : [{
                name: cohortSizes[0].cohort,
                y: cohortSizes[0].member + cohortSizes[0].supporter + cohortSizes[0].honorary
            },{
                name: cohortSizes[1].cohort,
                y: cohortSizes[1].member + cohortSizes[1].supporter + cohortSizes[1].honorary
            },{
                name: cohortSizes[2].cohort,
                y: cohortSizes[2].member + cohortSizes[2].supporter + cohortSizes[2].honorary
            },{
                name: cohortSizes[3].cohort,
                y: cohortSizes[3].member + cohortSizes[3].supporter + cohortSizes[3].honorary
            },{
                name: cohortSizes[4].cohort,
                y: cohortSizes[4].member + cohortSizes[4].supporter + cohortSizes[4].honorary
            },{
                name: cohortSizes[5].cohort,
                y: cohortSizes[5].member + cohortSizes[5].supporter + cohortSizes[5].honorary
            }]
        }]
    });

    $('#membersYearChart').highcharts({
        chart: {
            type: 'pie'
        },
        title: {
            text: gettext("Members per cohort (honorary excluded)"),
        },
        plotOptions: {
            pie: pieOptions
        },
        series: [{
            name: gettext("Members"),
            colorByPoint: true,
            data : [{
                name: cohortSizes[0].cohort,
                y: cohortSizes[0].member
            },{
                name: cohortSizes[1].cohort,
                y: cohortSizes[1].member
            },{
                name: cohortSizes[2].cohort,
                y: cohortSizes[2].member
            },{
                name: cohortSizes[3].cohort,
                y: cohortSizes[3].member
            },{
                name: cohortSizes[4].cohort,
                y: cohortSizes[4].member
            },{
                name: cohortSizes[5].cohort,
                y: cohortSizes[5].member
            }]
        }]
    });


    $('#benefactorsYearChart').highcharts({
        chart: {
            type: 'pie'
        },
        title: {
            text: gettext("Benefactors per cohort"),
        },
        plotOptions: {
            pie: pieOptions
        },
        series: [{
            name: gettext("Benefactors"),
            colorByPoint: true,
            data : [{
                name: cohortSizes[0].cohort,
                y: cohortSizes[0].supporter
            },{
                name: cohortSizes[1].cohort,
                y: cohortSizes[1].supporter
            },{
                name: cohortSizes[2].cohort,
                y: cohortSizes[2].supporter
            },{
                name: cohortSizes[3].cohort,
                y: cohortSizes[3].supporter
            },{
                name: cohortSizes[4].cohort,
                y: cohortSizes[4].supporter
            },{
                name: cohortSizes[5].cohort,
                y: cohortSizes[5].supporter
            }]
        }]
    });

    $('#pizzaTotalTypeChart').highcharts({
        chart: {
            type: 'pie'
        },
        title: {
            text: gettext("Total pizza orders of type"),
        },
        plotOptions: {
            pie: pieOptions
        },
        series: [{
            name: 'Pizzas',
            colorByPoint: true,
            data : [{
                name: pizzaOrders[0].name,
                y: pizzaOrders[0].total
            },{
                name: pizzaOrders[1].name,
                y: pizzaOrders[1].total
            },{
                name: pizzaOrders[2].name,
                y: pizzaOrders[2].total
            },{
                name: pizzaOrders[3].name,
                y: pizzaOrders[3].total
            },{
                name: pizzaOrders[4].name,
                y: pizzaOrders[4].total
            },{
                name: pizzaOrders[5].name,
                y: pizzaOrders[5].total
            }]
        }]
    });

    if (currentPizzaOrders != null) {
        $('#pizzaCurrentTypeChart').highcharts({
            chart: {
                type: 'pie'
            },
            title: {
                text: gettext("Current pizza orders of type"),
            },
            plotOptions: {
                pie: pieOptions
            },
            series: [{
                name: 'Pizzas',
                colorByPoint: true,
                data : [{
                    name: currentPizzaOrders[0].name,
                    y: currentPizzaOrders[0].total
                },{
                    name: currentPizzaOrders[1].name,
                    y: currentPizzaOrders[1].total
                },{
                    name: currentPizzaOrders[2].name,
                    y: currentPizzaOrders[2].total
                },{
                    name: currentPizzaOrders[3].name,
                    y: currentPizzaOrders[3].total
                },{
                    name: currentPizzaOrders[4].name,
                    y: currentPizzaOrders[4].total
                },{
                    name: currentPizzaOrders[5].name,
                    y: currentPizzaOrders[5].total
                }]
            }]
        });
    }
});
