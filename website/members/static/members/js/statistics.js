$(function () {
    const statistics = $('#members-statistics').data('statistics');
    const cohortSizes = statistics.cohort_sizes;
    const memberTypeDistribution = statistics.member_type_distribution;
    const pizzaOrders = statistics.total_pizza_orders;
    const currentPizzaOrders = statistics.current_pizza_orders;
    const committeeSizes = statistics.committee_sizes;
    const eventCategories = statistics.event_categories;

    Chart.defaults.global.aspectRatio = 1;
    Chart.defaults.global.legend.display = false;
    Chart.defaults.global.title.display = true;

    const colors = [
        '#E22672',
        '#CB2267',
        '#B51E5B',
        '#9E1B50',
        '#881744',
        '#711339',
        '#5A0F2E',
        '#440B22',
        '#2D0817',
        '#440B22',
        '#711339',
        '#b21e59',
        '#E53C80',
        '#E8518E',
        '#EB679C',
        '#EE7DAA',
        '#F193B9',
        '#F3A8C7',
        '#F6BED5',
        '#F9D4E3',
        '#F6BED5',
        '#F3A8C7',
        '#F193B9',
        '#EE7DAA',
        '#EB679C',
        '#E8518E',
        '#E53C80',
        '#b21e59',
        '#711339',
        '#440B22',
        '#2D0817',
        '#440B22',
        '#5A0F2E',
        '#711339',
        '#881744',
        '#9E1B50',
        '#B51E5B',
        '#CB2267',
        '#E22672'
    ];

    const smallBarChartOptions = (stacked) => ({
        aspectRatio: 1.5,
        scales: {
            xAxes: [{
                autoSkip: false,
                stacked: stacked
            }],
            yAxes: [{
                stacked: stacked,
                ticks: {
                    beginAtZero: true,
                    maxTicksLimit: 10,
                }
            }]
        },
    });

    new Chart($('#members-type-chart'), {
        type: 'bar',
        data: {
            labels: Object.keys(memberTypeDistribution),
            datasets: [{
                backgroundColor: colors,
                data: Object.values(memberTypeDistribution),
            }]
        },
        options: {
            title: {
                text: gettext('Members per member type'),
            },
            ...smallBarChartOptions(false)
        }
    });

    new Chart($('#total-year-chart'), {
        type: 'bar',
        data: {
            labels: Object.keys(cohortSizes),
            datasets: ['Benefactor', 'Honorary', 'Member'].map((type, i) => ({
                label: gettext(type),
                backgroundColor: colors[i],
                data: Object.values(cohortSizes).map((data) =>
                    data[type.toLowerCase()]
                ),
            }))
        },
        options: {
            title: {
                text: gettext("Total number of (honary) members and benefactors per cohort"),
            },
            ...smallBarChartOptions(true)
        }
    });

    const wideBarchartOptions = (stacked) => ({
        maintainAspectRatio: false,
        plugins: {labels: false},
        scales: {
            xAxes: [{
                stacked: stacked,
                autoSkip: false,
            }],
            yAxes: [{
                stacked: stacked,
                ticks: {
                    beginAtZero: true,
                    maxTicksLimit: 10,
                }
            }]
        }
    });

    new Chart($('#committees-members-chart'), {
        type: 'bar',
        data: {
            labels: Object.keys(committeeSizes),
            datasets: [{
                backgroundColor: colors,
                data: Object.values(committeeSizes),
            }]
        },
        options: {
            title: {
                text: gettext("Number of members per committee"),
            },
            ...wideBarchartOptions(false)
        }
    });

    new Chart($('#event-category-chart'), {
        type: 'bar',
        data: {
            labels: Object.keys(eventCategories),
            datasets: Object.keys(eventCategories[Object.keys(eventCategories)[0]]).map(function (key, index) {
                return {
                    label: key,
                    backgroundColor: colors[index],
                    data: Object.values(eventCategories).map(function (data) {
                        return data[key];
                    }),
                };
            }),
        },
        options: {
            title: {
                text: gettext("Number of events"),
            },
            ...wideBarchartOptions(true)
        }
    });

    const pizzaChart = (elem, data, text) =>
        new Chart(elem, {
            type: 'pie',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    backgroundColor: colors,
                    data: Object.values(data),
                }]
            },
            options: {
                xAxes: [{
                    ticks: {
                        autoSkip: false
                    }
                }],
                aspectRatio: 1.5,
                title: {
                    text: gettext(text),
                },
            }
        });

    pizzaChart($('#pizza-total-type-chart'), pizzaOrders, "Total pizza orders of type");

    if (currentPizzaOrders != null) {
        pizzaChart($('#pizza-current-type-chart'), currentPizzaOrders, "Current pizza orders of type");
    }

});
