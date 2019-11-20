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
        '#E53C80',
        '#E8518E',
        '#EB679C',
        '#EE7DAA',
        '#F193B9',
        '#F3A8C7',
        '#F6BED5',
        '#F9D4E3',
    ];

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
            aspectRatio: 1.5,
            title: {
                text: gettext('Members per member type'),
            },
            plugins: { labels: false },
            scales: {
                xAxes: [{
                    ticks: {
                        autoSkip: false
                    }
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true,
                        maxTicksLimit: 10,
                    }
                }]
            }
        }
    });

    new Chart($('#total-year-chart'), {
        type: 'bar',
        data: {
            labels: Object.keys(cohortSizes),
            datasets: [
                {
                    label: gettext('Benefactor'),
                    backgroundColor: colors[2],
                    data: Object.values(cohortSizes).map(function (data) {
                        return data.benefactor;
                    }),
                },
                {
                    label: gettext('Honorary'),
                    backgroundColor: colors[1],
                    data: Object.values(cohortSizes).map(function (data) {
                        return data.honorary;
                    }),
                },
                {
                    label: gettext('Members'),
                    backgroundColor: colors[0],
                    data: Object.values(cohortSizes).map(function (data) {
                        return data.member;
                    }),
                }]
        },
        options: {
            aspectRatio: 1.5,
            title: {
                text: gettext("Total number of (honary) members and benefactors per cohort"),
            },
            scales: {
                xAxes: [{
                    autoSkip: false,
                    stacked: true
                }],
                yAxes: [{
                    stacked: true,
                    ticks: {
                        beginAtZero: true,
                        maxTicksLimit: 10,
                    }
                }]
            },
            plugins: { labels: false }
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
            maintainAspectRatio: false,
            title: {
                text: gettext("Number of members per committee"),
            },
            plugins: { labels: false },
            scales: {
                 xAxes: [{
                    ticks: {
                        autoSkip: false,
                    }
                }],
                yAxes: [{
                    ticks: {
                        beginAtZero: true,
                        maxTicksLimit: 10,
                    }
                }]
            }
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
            maintainAspectRatio: false,
            title: {
                text: gettext("Number of events"),
            },
            scales: {
                xAxes: [{
                    stacked: true,
                    autoSkip: false
                }],
                yAxes: [{
                    stacked: true,
                    ticks: {
                        beginAtZero: true,
                        maxTicksLimit: 10,
                    }
                }]
            },
            plugins: { labels: false }
        }
    });

    new Chart($('#pizza-total-type-chart'), {
        type: 'pie',
        data: {
            labels: Object.keys(pizzaOrders),
            datasets: [{
                backgroundColor: colors,
                data: Object.values(pizzaOrders),
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
                text: gettext("Total pizza orders of type"),
            },
            plugins: { labels: false },
        }
    });

    if (currentPizzaOrders != null) {
        new Chart($('#pizza-current-type-chart'), {
            type: 'pie',
            data: {
                labels: Object.keys(pizzaOrders),
                datasets: [{
                    backgroundColor: colors,
                    data: Object.values(pizzaOrders),
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
                    text: gettext("Current pizza orders of type"),
                },
                plugins: { labels: false },
            }
        });
    }

});
