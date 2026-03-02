document.addEventListener('DOMContentLoaded', () => {
    const analysisForm = document.getElementById('analysis-form');
    const loader = document.getElementById('loader');
    const resultsDiv = document.getElementById('results');
    const accuracySpan = document.getElementById('accuracy');
    const dataTableContainer = document.getElementById('data-table-container');
    const cmContainer = document.getElementById('confusion-matrix-chart');
    let chart; // To hold the chart instance

    if (analysisForm) {
        analysisForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            const form = event.target;
            const formData = new FormData(form);

            // If a chart instance exists, destroy it before creating a new one
            if (chart) {
                chart.destroy();
            }

            loader.style.display = 'block';
            resultsDiv.style.display = 'none';
            dataTableContainer.innerHTML = '<p>Your data will appear here after analysis.</p>'; // Reset

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Server error: ${response.status} ${response.statusText}. ${errorText}`);
                }

                const results = await response.json();

                if (results.error) {
                    alert('Error: ' + results.error);
                } else {
                    accuracySpan.textContent = (results.test_accuracy * 100).toFixed(2) + '%';

                    // Render the confusion matrix
                    if (results.confusion_matrix && results.class_labels) {
                        renderConfusionMatrix(results.confusion_matrix, results.class_labels);
                    }
                    
                    // Render the data table
                    if (results.data_preview && results.data_preview.length > 0) {
                        const table = document.createElement('table');
                        const thead = document.createElement('thead');
                        const tbody = document.createElement('tbody');
                        
                        // Create header row
                        const headerRow = document.createElement('tr');
                        Object.keys(results.data_preview[0]).forEach(key => {
                            const th = document.createElement('th');
                            th.textContent = key;
                            headerRow.appendChild(th);
                        });
                        thead.appendChild(headerRow);

                        // Create body rows
                        results.data_preview.forEach(rowData => {
                            const row = document.createElement('tr');
                            Object.values(rowData).forEach(value => {
                                const td = document.createElement('td');
                                td.textContent = value;
                                row.appendChild(td);
                            });
                            tbody.appendChild(row);
                        });

                        table.appendChild(thead);
                        table.appendChild(tbody);
                        
                        dataTableContainer.innerHTML = ''; // Clear placeholder
                        dataTableContainer.appendChild(table);
                    }

                    resultsDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('An error occurred:', error);
                alert('An unexpected error occurred: ' + error.message);
            } finally {
                loader.style.display = 'none';
            }
        });
    }

    function renderConfusionMatrix(matrix, labels) {
        const data = {
            labels: labels,
            datasets: []
        };

        // Create a dataset for each row of the matrix
        matrix.forEach((row, i) => {
            const dataset = {
                label: labels[i],
                data: row,
                backgroundColor: `rgba(75, 192, 192, ${0.2 + (i / labels.length) * 0.6})`,
                borderColor: 'white',
                borderWidth: 1
            };
            data.datasets.push(dataset);
        });

        const ctx = cmContainer.getContext('2d');
        chart = new Chart(ctx, {
            type: 'bar', // Using bar chart to create a heatmap-like matrix
            data: data,
            options: {
                indexAxis: 'y',
                scales: {
                    x: {
                        stacked: true,
                        ticks: {
                            beginAtZero: true
                        },
                        title: {
                            display: true,
                            text: 'Predicted'
                        }
                    },
                    y: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Actual'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.x !== null) {
                                    label += context.parsed.x;
                                }
                                return `Predicted ${context.label}: ${context.raw}`;
                            }
                        }
                    }
                }
            }
        });
    }
});