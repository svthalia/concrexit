const COLORS = [
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


$(document).ready(function () {
    $("canvas").each(function (index, canvas) {

            const datasets = $(canvas).data("data")["datasets"];
            const labels = $(canvas).data("data")["labels"];
            const title = $(canvas).data("title");
            const chartType = $(canvas).data("chart-type");

            let config = {
                type: chartType,
                data: {
                    labels: labels,
                    datasets: [],
                },
                options: {

                    plugins: {

                        title: {
                            display: true,
                            text: title,
                            font: {
                                size: 16
                            },
                        },

                        legend: {
                            display: false,
                        },

                    },
                }
            }

            if (chartType === "bar") {
                config.options.scales = {
                    x: {
                        stacked: chartType === "bar",
                    },
                    y: {
                        stacked: chartType === "bar",
                    }
                }
            }

            datasets.forEach(function (dataset, index) {

                if (datasets.length > 1) {
                    dataset.backgroundColor = COLORS[index]
                } else {
                    dataset.backgroundColor = COLORS
                }

                config.data.datasets.push(dataset)
            });


            new Chart(canvas, config)
        }
    );
});
