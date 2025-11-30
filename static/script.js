let scrapedData = [];
let isScraping = false;

function startScraping() {
    const keyword = document.getElementById('keyword').value;
    const target = document.getElementById('target').value;
    
    if (!keyword) {
        alert('Please enter a keyword');
        return;
    }
    
    // Reset UI
    document.getElementById('resultsTable').innerHTML = '';
    document.getElementById('startBtn').disabled = true;
    document.getElementById('startBtn').innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scraping...';
    document.getElementById('statusBadge').textContent = 'Running';
    document.getElementById('statusBadge').classList.add('active');
    document.getElementById('exportBtn').disabled = true;
    
    scrapedData = [];
    isScraping = true;
    
    const eventSource = new EventSource(`/api/scrape?keyword=${encodeURIComponent(keyword)}&total=${target}`);
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.status === 'data') {
            addResultRow(data.data);
            scrapedData.push(data.data);
        } else if (data.status === 'complete') {
            eventSource.close();
            finishScraping();
        } else if (data.status === 'error') {
            eventSource.close();
            alert('Error: ' + data.message);
            finishScraping();
        }
    };
    
    eventSource.onerror = function() {
        eventSource.close();
        finishScraping();
    };
}

function finishScraping() {
    isScraping = false;
    document.getElementById('startBtn').disabled = false;
    document.getElementById('startBtn').innerHTML = '<i class="fa-solid fa-play"></i> Start Scraping';
    document.getElementById('statusBadge').textContent = 'Completed';
    document.getElementById('statusBadge').classList.remove('active');
    
    if (scrapedData.length > 0) {
        document.getElementById('exportBtn').disabled = false;
    }
}

function addResultRow(item) {
    const row = document.createElement('div');
    row.className = 'table-row';
    
    const sn = scrapedData.length + 1;
    
    const websiteLink = item.WEBSITE && item.WEBSITE !== 'No' && item.WEBSITE !== 'N/A' 
        ? `<a href="${item.WEBSITE}" target="_blank">Visit <i class="fa-solid fa-external-link-alt"></i></a>` 
        : '<span style="color: var(--text-secondary)">N/A</span>';
        
    const whatsappLink = item.WHATSAPP && item.WHATSAPP !== 'N/A'
        ? `<a href="https://wa.me/${item.WHATSAPP.replace(/\D/g,'')}" target="_blank">${item.WHATSAPP}</a>`
        : '<span style="color: var(--text-secondary)">N/A</span>';
        
    const emailText = item.GMAIL && item.GMAIL !== 'N/A'
        ? `<a href="mailto:${item.GMAIL}" style="color: var(--text-primary); text-decoration: none;">${item.GMAIL}</a>`
        : '<span style="color: var(--text-secondary)">N/A</span>';

    row.innerHTML = `
        <div class="col sn">${sn}</div>
        <div class="col name" title="${item.NAME}">${item.NAME}</div>
        <div class="col contact" title="${item['CONTACT NO']}">${item['CONTACT NO']}</div>
        <div class="col email" title="${item.GMAIL}">${emailText}</div>
        <div class="col website">${websiteLink}</div>
        <div class="col whatsapp">${whatsappLink}</div>
        <div class="col location" title="${item.LOCATION}">${item.LOCATION}</div>
    `;
    
    document.getElementById('resultsTable').appendChild(row);
    
    // Auto scroll to bottom
    const tableBody = document.getElementById('resultsTable');
    tableBody.scrollTop = tableBody.scrollHeight;
}

// Export Logic
function openExportModal() {
    document.getElementById('exportModal').classList.add('active');
}

function closeExportModal() {
    document.getElementById('exportModal').classList.remove('active');
}

function exportData() {
    const filterWhatsapp = document.getElementById('filterWhatsapp').value;
    const filterWebsite = document.getElementById('filterWebsite').value;
    const filterEmail = document.getElementById('filterEmail').value;
    
    let dataToExport = scrapedData.filter(item => {
        // WhatsApp Filter
        if (filterWhatsapp === 'has') {
            if (!item.WHATSAPP || item.WHATSAPP === 'N/A') return false;
        } else if (filterWhatsapp === 'no') {
            if (item.WHATSAPP && item.WHATSAPP !== 'N/A') return false;
        }
        
        // Website Filter
        if (filterWebsite === 'has') {
            if (!item.WEBSITE || item.WEBSITE === 'No' || item.WEBSITE === 'N/A') return false;
        } else if (filterWebsite === 'no') {
            if (item.WEBSITE && item.WEBSITE !== 'No' && item.WEBSITE !== 'N/A') return false;
        }
        
        // Email Filter
        if (filterEmail === 'has') {
            if (!item.GMAIL || item.GMAIL === 'N/A') return false;
        } else if (filterEmail === 'no') {
            if (item.GMAIL && item.GMAIL !== 'N/A') return false;
        }
        
        return true;
    });
    
    if (dataToExport.length === 0) {
        alert('No data matches your filters');
        return;
    }
    
    // Convert to CSV
    const headers = ['NAME', 'CONTACT NO', 'GMAIL', 'WEBSITE', 'LOCATION', 'WHATSAPP'];
    const csvContent = [
        headers.join(','),
        ...dataToExport.map(row => headers.map(header => {
            let cell = row[header] || '';
            // Escape quotes and wrap in quotes if contains comma, newline, or quote
            if (cell.includes(',') || cell.includes('"') || cell.includes('\n')) {
                cell = `"${cell.replace(/"/g, '""')}"`;
            }
            return cell;
        }).join(','))
    ].join('\n');
    
    // Add UTF-8 BOM for proper Unicode character display in Excel
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `scraped_data_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    closeExportModal();
}
