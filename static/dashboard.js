document.addEventListener('DOMContentLoaded', () => {
    const analysisForm = document.getElementById('analysis-form');
    if (analysisForm) {
        analysisForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            const form = event.target;
            const formData = new FormData(form);
            const loader = document.getElementById('loader');
            const resultsDiv = document.getElementById('results');
            const accuracySpan = document.getElementById('accuracy');
            const chartContainer = document.getElementById('accuracyChart');
            let chart = Chart.getChart(chartContainer); // Get existing chart instance

            // If a chart instance exists, destroy it before creating a new one
            if (chart) {
                chart.destroy();
            }

            loader.style.display = 'block';
            resultsDiv.style.display = 'none';

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                const results = await response.json();

                if (response.ok) {
                    accuracySpan.textContent = (results.test_accuracy * 100).toFixed(2) + '%';
                    
                    // Render the new chart
                    const ctx = chartContainer.getContext('2d');
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: Array.from({length: results.training_history.accuracy.length}, (_, i) => i + 1),
                            datasets: [{
                                label: 'Training Accuracy',
                                data: results.training_history.accuracy,
                                borderColor: 'rgb(75, 192, 192)',
                                tension: 0.1
                            },
                            {
                                label: 'Validation Accuracy',
                                data: results.training_history.val_accuracy,
                                borderColor: 'rgb(255, 99, 132)',
                                tension: 0.1
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: { display: true, text: 'Accuracy' }
                                },
                                x: {
                                    title: { display: true, text: 'Epoch' }
                                }
                            }
                        }
                    });

                    resultsDiv.style.display = 'block';
                } else {
                    alert('Error: ' + results.error);
                }
            } catch (error) {
                console.error('An error occurred:', error);
                alert('An unexpected error occurred. Please check the console.');
            } finally {
                loader.style.display = 'none';
            }
        });
    }
});