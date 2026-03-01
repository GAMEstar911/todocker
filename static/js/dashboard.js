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

            // Hide the chart and results from previous runs
            chartContainer.style.display = 'none';
            resultsDiv.style.display = 'none';
            loader.style.display = 'block';

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                const results = await response.json();

                if (response.ok) {
                    accuracySpan.textContent = (results.test_accuracy * 100).toFixed(2) + '%';
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