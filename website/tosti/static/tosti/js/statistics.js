const COLORS = [
    '#e8b365',
    '#e6ac56',
    '#e3a345',
    '#e19a33',
    '#de9221',
    '#cc861e',
    '#ba7a1c',
    '#a96f19',
    '#976317',
    '#855714',
    '#734c11',
    '#62400f',
    '#50340c',
    '#3e2909',
    '#50340c',
    '#62400f',
    '#734c11',
    '#855714',
    '#976317',
    '#a96f19',
    '#ba7a1c',
    '#cc861e',
    '#de9221',
    '#e19a33',
    '#e3a345',
    '#e3a345',
    '#e6ac56',
    '#e8b568'
];


document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("canvas.statistics-canvas").forEach((canvas) => {

            const data = JSON.parse(canvas.dataset.data);
            const datasets = data["datasets"];
            const labels = data["labels"];
            const title = canvas.dataset.title;
            const chartType = canvas.dataset.chartType;

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

            datasets.forEach((dataset, index) => {

                if (datasets.length > 1) {
                    dataset.backgroundColor = COLORS[index % COLORS.length];
                    if (chartType === "line") {
                        dataset.borderColor = COLORS[index % COLORS.length];
                    }
                } else {
                    dataset.backgroundColor = COLORS;
                    if (chartType === "line") {
                        dataset.borderColor = COLORS;
                    }
                }

                config.data.datasets.push(dataset);
            });


            new Chart(canvas, config);
        }
    );
});
