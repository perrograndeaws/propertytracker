document.addEventListener('DOMContentLoaded', function() {
    const singleSearchForm = document.getElementById('singleSearchForm');
    const fileUploadForm = document.getElementById('fileUploadForm');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const resultsSummary = document.getElementById('resultsSummary');
    const resultsTable = document.getElementById('resultsTable');

    // Single address search
    singleSearchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const address = document.getElementById('singleAddress').value.trim();
        if (!address) return;

        showLoading();
        
        try {
            const formData = new FormData();
            formData.append('address', address);
            
            const response = await fetch('/search-single', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            displaySingleResult(result);
            
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while searching. Please try again.');
        } finally {
            hideLoading();
        }
    });

    // File upload
    fileUploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        
        if (!file) return;

        showLoading();
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/upload-file', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            displayBulkResults(data);
            
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while processing the file. Please try again.');
        } finally {
            hideLoading();
        }
    });

    function showLoading() {
        loading.classList.remove('hidden');
        results.classList.add('hidden');
    }

    function hideLoading() {
        loading.classList.add('hidden');
    }

    function displaySingleResult(result) {
        const data = {
            results: [result],
            total_searched: 1,
            successful: result.status !== 'Error' && result.status !== 'Not Found' ? 1 : 0,
            failed: result.status === 'Error' || result.status === 'Not Found' ? 1 : 0
        };
        displayBulkResults(data);
    }

    function displayBulkResults(data) {
        // Show summary
        resultsSummary.innerHTML = `
            <div class="summary">
                <div class="summary-stats">
                    <div class="stat-card">
                        <div class="stat-number">${data.total_searched}</div>
                        <div class="stat-label">Total Searched</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.successful}</div>
                        <div class="stat-label">Found</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.failed}</div>
                        <div class="stat-label">Not Found/Error</div>
                    </div>
                </div>
            </div>
        `;

        // Create results table with properly formatted clickable links
        let tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Address</th>
                        <th>Status</th>
                        <th>Type</th>
                        <th>Beds/Baths</th>
                        <th>Sq Ft</th>
                        <th>Zillow</th>
                        <th>Realtor.com</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.results.forEach(property => {
            const statusClass = getStatusClass(property.status);
            const bedroomBath = `${property.bedrooms || 'N/A'}/${property.bathrooms || 'N/A'}`;
            
            // Ensure links are properly formatted and escaped
            const zillowLink = property.zillow_link || '#';
            const realtorLink = property.realtor_link || '#';
            
            tableHTML += `
                <tr>
                    <td>${escapeHtml(property.address)}</td>
                    <td class="${statusClass}">${escapeHtml(property.status)}</td>
                    <td>${escapeHtml(property.property_type || 'N/A')}</td>
                    <td>${bedroomBath}</td>
                    <td>${property.square_feet || 'N/A'}</td>
                    <td><a href="${escapeHtml(zillowLink)}" target="_blank" rel="noopener noreferrer" class="property-link zillow-link">🏠 View on Zillow</a></td>
                    <td><a href="${escapeHtml(realtorLink)}" target="_blank" rel="noopener noreferrer" class="property-link realtor-link">🏡 View on Realtor.com</a></td>
                </tr>
            `;

            if (property.error) {
                tableHTML += `
                    <tr>
                        <td colspan="7" class="error-text">Error: ${escapeHtml(property.error)}</td>
                    </tr>
                `;
            }
        });

        tableHTML += '</tbody></table>';
        resultsTable.innerHTML = tableHTML;
        
        // Add click event listeners to ensure links work properly
        addLinkEventListeners();
        
        results.classList.remove('hidden');
    }

    function addLinkEventListeners() {
        // Add explicit click handlers for property links
        document.querySelectorAll('.property-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const url = this.getAttribute('href');
                if (url && url !== '#') {
                    // Log the click for analytics
                    console.log(`Opening: ${url}`);
                    // Open in new tab
                    window.open(url, '_blank', 'noopener,noreferrer');
                }
            });
        });
    }

    function getStatusClass(status) {
        if (!status) return '';
        
        const statusLower = status.toLowerCase();
        if (statusLower.includes('active') || statusLower.includes('for sale')) {
            return 'status-active';
        } else if (statusLower.includes('pending')) {
            return 'status-pending';
        } else if (statusLower.includes('sold')) {
            return 'status-sold';
        } else if (statusLower.includes('error')) {
            return 'status-error';
        }
        return '';
    }

    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
    }
});