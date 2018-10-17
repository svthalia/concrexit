$(function () {
    var statistics = $('#members-statistics').data('statistics');
    var cohortSizes = statistics.cohort_sizes;
    var memberTypeDistribution = statistics.member_type_distribution;
    var pizzaOrders = statistics.total_pizza_orders;
    var currentPizzaOrders = statistics.current_pizza_orders;

    new Chart($('#membersTypeChart'), {
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
                        cohortSizes[0].member + cohortSizes[0].supporter + cohortSizes[0].honorary,
                        cohortSizes[1].member + cohortSizes[1].supporter + cohortSizes[1].honorary,
                        cohortSizes[2].member + cohortSizes[2].supporter + cohortSizes[2].honorary,
                        cohortSizes[3].member + cohortSizes[3].supporter + cohortSizes[3].honorary,
                        cohortSizes[4].member + cohortSizes[4].supporter + cohortSizes[4].honorary,
                        cohortSizes[5].member + cohortSizes[5].supporter + cohortSizes[5].honorary,
                    ],
            }]
        },
        options: {
            aspectRatio: 1,
            legend: {
                display: false
            },
            title: {
                display: true,
                text: gettext("Total number of (honary) members and benefactors per cohort"),
            },
            plugins: {
                labels: {
                    render: 'label',
                    fontColor: '#fff',
                    arc: true,
                    position: 'border',
                }
            }
        }
    });
});
