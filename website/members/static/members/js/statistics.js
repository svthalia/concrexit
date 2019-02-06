$(function () {
    var statistics = $('#members-statistics').data('statistics');
    var cohortSizes = statistics.cohort_sizes;
    var memberTypeDistribution = statistics.member_type_distribution;
    var pizzaOrders = statistics.total_pizza_orders;
    var currentPizzaOrders = statistics.current_pizza_orders;

    Chart.defaults.global.aspectRatio = 1;
    Chart.defaults.global.legend.display = false;
    Chart.defaults.global.title.display = true;

    var pluginOptions = {
        labels: {
            render: 'label',
            fontColor: '#000000',
            arc: false,
            position: 'outside',
            fontsize: 16,
            fontstyle: 'bold',
            fontFamily: '"Open Sans"'
        }
    };

    new Chart($('#members-type-chart'), {
        type: 'pie',
        data: {
            labels:
                [
                    gettext('Members'),
                    gettext('Benefactors'),
                    gettext('Honorary Members'),
                ],
            datasets: [{
                backgroundColor: [
                    '#AE0046',
                    '#E62272',
                    '#E6478A',
                ],
                data:
                    [
                        memberTypeDistribution.member,
                        memberTypeDistribution.benefactor,
                        memberTypeDistribution.honorary
                    ],
            }]
        },
        options: {
            title: {
                text: gettext('Members per member type'),
            },
            plugins: pluginOptions,
        }
    });

    new Chart($('#total-year-chart'), {
        type: 'pie',
        data: {
            labels:
                [
                    cohortSizes[0].cohort,
                    cohortSizes[1].cohort,
                    cohortSizes[2].cohort,
                    cohortSizes[3].cohort,
                    cohortSizes[4].cohort,
                    cohortSizes[5].cohort
                ],
            datasets: [{
                backgroundColor: [
                    '#AE0046',
                    '#E62272',
                    '#E6478A',
                    '#CC2482',
                    '#8E1056',
                    '#DC3472',
                ],
                data:
                    [
                        cohortSizes[0].member + cohortSizes[0].benefactor + cohortSizes[0].honorary,
                        cohortSizes[1].member + cohortSizes[1].benefactor + cohortSizes[1].honorary,
                        cohortSizes[2].member + cohortSizes[2].benefactor + cohortSizes[2].honorary,
                        cohortSizes[3].member + cohortSizes[3].benefactor + cohortSizes[3].honorary,
                        cohortSizes[4].member + cohortSizes[4].benefactor + cohortSizes[4].honorary,
                        cohortSizes[5].member + cohortSizes[5].benefactor + cohortSizes[5].honorary,
                    ],
            }]
        },
        options: {
            title: {
                text: gettext("Total number of (honary) members and benefactors per cohort"),
            },
            plugins: pluginOptions,
        }
    });

    new Chart($('#members-year-chart'), {
        type: 'pie',
        data: {
            labels:
                [
                    cohortSizes[0].cohort,
                    cohortSizes[1].cohort,
                    cohortSizes[2].cohort,
                    cohortSizes[3].cohort,
                    cohortSizes[4].cohort,
                    cohortSizes[5].cohort
                ],
            datasets: [{
                backgroundColor: [
                    '#AE0046',
                    '#E62272',
                    '#E6478A',
                    '#CC2482',
                    '#8E1056',
                    '#DC3472',
                ],
                data:
                    [
                        cohortSizes[0].member,
                        cohortSizes[1].member,
                        cohortSizes[2].member,
                        cohortSizes[3].member,
                        cohortSizes[4].member,
                        cohortSizes[5].member,
                    ],
            }]
        },
        options: {
            title: {
                text: gettext("Members per cohort (honorary excluded)"),
            },
            plugins: pluginOptions,
        }
    });

    new Chart($('#benefactors-year-chart'), {
        type: 'pie',
        data: {
            labels:
                [
                    cohortSizes[0].cohort,
                    cohortSizes[1].cohort,
                    cohortSizes[2].cohort,
                    cohortSizes[3].cohort,
                    cohortSizes[4].cohort,
                    cohortSizes[5].cohort
                ],
            datasets: [{
                backgroundColor: [
                    '#AE0046',
                    '#E62272',
                    '#E6478A',
                    '#CC2482',
                    '#8E1056',
                    '#DC3472',
                ],
                data:
                    [
                        cohortSizes[0].benefactor,
                        cohortSizes[1].benefactor,
                        cohortSizes[2].benefactor,
                        cohortSizes[3].benefactor,
                        cohortSizes[4].benefactor,
                        cohortSizes[5].benefactor,
                    ],
            }]
        },
        options: {
            title: {
                text: gettext("Benefactors per cohort"),
            },
            plugins: pluginOptions,
        }
    });

    new Chart($('#pizza-total-type-chart'), {
        type: 'pie',
        data: {
            labels:
                [
                    pizzaOrders[0].name,
                    pizzaOrders[1].name,
                    pizzaOrders[2].name,
                    pizzaOrders[3].name,
                    pizzaOrders[4].name,
                    pizzaOrders[5].name
                ],
            datasets: [{
                backgroundColor: [
                    '#AE0046',
                    '#E62272',
                    '#E6478A',
                    '#CC2482',
                    '#8E1056',
                    '#DC3472',
                ],
                data:
                    [
                        pizzaOrders[0].total,
                        pizzaOrders[1].total,
                        pizzaOrders[2].total,
                        pizzaOrders[3].total,
                        pizzaOrders[4].total,
                        pizzaOrders[5].total
                    ],
            }]
        },
        options: {
            title: {
                text: gettext("Total pizza orders of type"),
            },
            plugins: pluginOptions,
        }
    });

    if (current_pizza_orders != null) {
        new Chart($('#pizza-current-type-chart'), {
            type: 'pie',
            data: {
                labels:
                    [
                        currentPizzaOrders[0].name,
                        currentPizzaOrders[1].name,
                        currentPizzaOrders[2].name,
                        currentPizzaOrders[3].name,
                        currentPizzaOrders[4].name,
                        currentPizzaOrders[5].name
                    ],
                datasets: [{
                    backgroundColor: [
                        '#AE0046',
                        '#E62272',
                        '#E6478A',
                        '#CC2482',
                        '#8E1056',
                        '#DC3472',
                    ],
                    data:
                        [
                            currentPizzaOrders[0].total,
                            currentPizzaOrders[1].total,
                            currentPizzaOrders[2].total,
                            currentPizzaOrders[3].total,
                            currentPizzaOrders[4].total,
                            currentPizzaOrders[5].total
                        ],
                }]
            },
            options: {
                title: {
                    text: gettext("Current pizza orders of type"),
                },
                plugins: pluginOptions,
            }
        });
    }
});
