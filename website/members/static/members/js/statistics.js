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
                y: total_stats_member_type.member
            },{
                name: gettext('Benefactors'),
                y: total_stats_member_type.supporter
            },{
                name: gettext('Honorary Members'),
                y: total_stats_member_type.honorary
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
                name: total_stats_year[0].cohort,
                y: total_stats_year[0].member + total_stats_year[0].supporter + total_stats_year[0].honorary
            },{
                name: total_stats_year[1].cohort,
                y: total_stats_year[1].member + total_stats_year[1].supporter + total_stats_year[1].honorary
            },{
                name: total_stats_year[2].cohort,
                y: total_stats_year[2].member + total_stats_year[2].supporter + total_stats_year[2].honorary
            },{
                name: total_stats_year[3].cohort,
                y: total_stats_year[3].member + total_stats_year[3].supporter + total_stats_year[3].honorary
            },{
                name: total_stats_year[4].cohort,
                y: total_stats_year[4].member + total_stats_year[4].supporter + total_stats_year[4].honorary
            },{
                name: total_stats_year[5].cohort,
                y: total_stats_year[5].member + total_stats_year[5].supporter + total_stats_year[5].honorary
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
                name: total_stats_year[0].cohort,
                y: total_stats_year[0].member
            },{
                name: total_stats_year[1].cohort,
                y: total_stats_year[1].member
            },{
                name: total_stats_year[2].cohort,
                y: total_stats_year[2].member
            },{
                name: total_stats_year[3].cohort,
                y: total_stats_year[3].member
            },{
                name: total_stats_year[4].cohort,
                y: total_stats_year[4].member
            },{
                name: total_stats_year[5].cohort,
                y: total_stats_year[5].member
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
                name: total_stats_year[0].cohort,
                y: total_stats_year[0].supporter
            },{
                name: total_stats_year[1].cohort,
                y: total_stats_year[1].supporter
            },{
                name: total_stats_year[2].cohort,
                y: total_stats_year[2].supporter
            },{
                name: total_stats_year[3].cohort,
                y: total_stats_year[3].supporter
            },{
                name: total_stats_year[4].cohort,
                y: total_stats_year[4].supporter
            },{
                name: total_stats_year[5].cohort,
                y: total_stats_year[5].supporter
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
                name: total_pizza_orders[0].name,
                y: total_pizza_orders[0].total
            },{
                name: total_pizza_orders[1].name,
                y: total_pizza_orders[1].total
            },{
                name: total_pizza_orders[2].name,
                y: total_pizza_orders[2].total
            },{
                name: total_pizza_orders[3].name,
                y: total_pizza_orders[3].total
            },{
                name: total_pizza_orders[4].name,
                y: total_pizza_orders[4].total
            },{
                name: total_pizza_orders[5].name,
                y: total_pizza_orders[5].total
            }]
        }]
    });

    if (current_pizza_orders != null) {
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
                    name: current_pizza_orders[0].name,
                    y: current_pizza_orders[0].total
                },{
                    name: current_pizza_orders[1].name,
                    y: current_pizza_orders[1].total
                },{
                    name: current_pizza_orders[2].name,
                    y: current_pizza_orders[2].total
                },{
                    name: current_pizza_orders[3].name,
                    y: current_pizza_orders[3].total
                },{
                    name: current_pizza_orders[4].name,
                    y: current_pizza_orders[4].total
                },{
                    name: current_pizza_orders[5].name,
                    y: current_pizza_orders[5].total
                }]
            }]
        });
    }
});
