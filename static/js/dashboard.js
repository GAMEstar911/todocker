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
            const chartContainer = document.getElementById('training-chart');
            const dataTableContainer = document.getElementById('data-table-container');
            let chart = Chart.getChart(chartContainer); // Get existing chart instance

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
});