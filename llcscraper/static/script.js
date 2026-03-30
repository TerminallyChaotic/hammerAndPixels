// SMTP provider presets
const SMTP_PRESETS = {
    gmail:      { server: 'smtp.gmail.com',       port: 587,  security: 'starttls', help: 'Use an App Password from myaccount.google.com > Security > App Passwords' },
    outlook:    { server: 'smtp.office365.com',    port: 587,  security: 'starttls', help: 'Use your Microsoft account password or app password' },
    yahoo:      { server: 'smtp.mail.yahoo.com',   port: 587,  security: 'starttls', help: 'Generate an app password at login.yahoo.com > Account Security' },
    protonmail: { server: '127.0.0.1',             port: 1025, security: 'starttls', help: 'Requires Proton Mail Bridge running on localhost:1025' },
    sendgrid:   { server: 'smtp.sendgrid.net',     port: 587,  security: 'starttls', help: 'Use "apikey" as username and your SendGrid API key as password' },
    custom:     { server: '',                      port: 587,  security: 'starttls', help: 'Enter your SMTP server details manually' }
};

// --- Tab switching ---

function showTab(tabName) {
    const contents = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.tab-button');

    contents.forEach(c => c.classList.remove('active'));
    buttons.forEach(b => b.classList.remove('active'));

    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');

    // Lazy-load data
    if (tabName === 'dashboard') loadStats();
    else if (tabName === 'llcs') loadLLCs();
    else if (tabName === 'queue') loadEmailQueue();
    else if (tabName === 'history') loadEmailHistory();
    else if (tabName === 'logs') loadLogs();
}

// --- SMTP provider change ---

function onProviderChange() {
    const provider = document.getElementById('smtp_provider').value;
    const preset = SMTP_PRESETS[provider];
    const isCustom = (provider === 'custom');

    document.getElementById('smtp_server').value = preset.server;
    document.getElementById('smtp_port').value = preset.port;
    document.getElementById('smtp_security').value = preset.security;
    document.getElementById('smtp_help').textContent = preset.help;

    document.getElementById('smtp_server').readOnly = !isCustom;
    document.getElementById('smtp_port').readOnly = !isCustom;
    document.getElementById('smtp_security').disabled = !isCustom;
}

// --- Settings ---

function loadSettings() {
    fetch('/api/settings')
        .then(res => res.json())
        .then(data => {
            document.getElementById('scrape_lookback_days').value = data.scrape_lookback_days || '7';
            document.getElementById('scrape_frequency_hours').value = data.scrape_frequency_hours || '12';
            document.getElementById('scrape_times').value = data.scrape_times || '';
            document.getElementById('daily_email_limit').value = data.daily_email_limit || '10';
            document.getElementById('auto_send_enabled').checked = data.auto_send_enabled === true || data.auto_send_enabled === 'true';
            document.getElementById('email_from_name').value = data.email_from_name || 'Jesse';
            document.getElementById('site_url').value = data.site_url || 'https://hammerandpixels.com';

            // SMTP
            document.getElementById('smtp_email').value = data.smtp_email || '';
            document.getElementById('smtp_provider').value = data.smtp_provider || 'gmail';
            document.getElementById('smtp_server').value = data.smtp_server || 'smtp.gmail.com';
            document.getElementById('smtp_port').value = data.smtp_port || 587;
            document.getElementById('smtp_security').value = data.smtp_security || 'starttls';
            onProviderChange();
        })
        .catch(err => console.error('Error loading settings:', err));
}

function saveSettings() {
    const settings = {
        scrape_lookback_days: parseInt(document.getElementById('scrape_lookback_days').value) || 7,
        scrape_frequency_hours: parseInt(document.getElementById('scrape_frequency_hours').value) || 12,
        scrape_times: document.getElementById('scrape_times').value,
        daily_email_limit: parseInt(document.getElementById('daily_email_limit').value) || 10,
        auto_send_enabled: document.getElementById('auto_send_enabled').checked,
        email_from_name: document.getElementById('email_from_name').value,
        site_url: document.getElementById('site_url').value,
        smtp_email: document.getElementById('smtp_email').value,
        smtp_password: document.getElementById('smtp_password').value,
        smtp_provider: document.getElementById('smtp_provider').value,
        smtp_server: document.getElementById('smtp_server').value,
        smtp_port: parseInt(document.getElementById('smtp_port').value) || 587,
        smtp_security: document.getElementById('smtp_security').value,
    };

    fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    })
        .then(res => res.json())
        .then(() => {
            showMessage('Settings saved successfully!', 'success');
            document.getElementById('smtp_password').value = '';
            loadSchedulerStatus();
        })
        .catch(err => showMessage('Error: ' + err.message, 'error'));
}

// --- Dashboard stats ---

function loadStats() {
    fetch('/api/stats')
        .then(res => res.json())
        .then(stats => {
            document.getElementById('stat-total').textContent = stats.total_llcs || 0;
            document.getElementById('stat-pending-enrichment').textContent = stats.pending_enrichment || 0;
            document.getElementById('stat-have-email').textContent = stats.have_email || 0;
            document.getElementById('stat-approved').textContent = stats.approved || 0;
            document.getElementById('stat-sent').textContent = stats.emails_sent || 0;
            document.getElementById('stat-today').textContent = stats.emails_today || 0;
            document.getElementById('stat-skipped').textContent = stats.skipped || 0;
            document.getElementById('stat-have-website').textContent = stats.have_website || 0;
        })
        .catch(err => console.error('Error loading stats:', err));
}

// --- LLCs table ---

let llcCurrentPage = 0;
const LLC_PAGE_SIZE = 50;

function loadLLCs(page) {
    if (page !== undefined) llcCurrentPage = page;
    const offset = llcCurrentPage * LLC_PAGE_SIZE;

    const status = document.getElementById('filter-outreach')?.value || '';
    const enrichment = document.getElementById('filter-enrichment')?.value || '';
    const search = document.getElementById('filter-search')?.value || '';
    const dateFrom = document.getElementById('filter-date-from')?.value || '';
    const dateTo = document.getElementById('filter-date-to')?.value || '';

    let url = '/api/llcs?limit=' + LLC_PAGE_SIZE + '&offset=' + offset;
    if (status) url += '&outreach_status=' + encodeURIComponent(status);
    if (enrichment) url += '&enrichment_status=' + encodeURIComponent(enrichment);
    if (search) url += '&search=' + encodeURIComponent(search);
    if (dateFrom) url += '&date_from=' + encodeURIComponent(dateFrom);
    if (dateTo) url += '&date_to=' + encodeURIComponent(dateTo);

    fetch(url)
        .then(res => res.json())
        .then(llcs => {
            const tbody = document.getElementById('llc-table-body');
            tbody.innerHTML = '';

            // Update pagination controls
            const pagingDiv = document.getElementById('llc-paging');
            if (pagingDiv) {
                const prevDisabled = llcCurrentPage === 0;
                const nextDisabled = llcs.length < LLC_PAGE_SIZE;
                pagingDiv.innerHTML =
                    '<button class="btn btn-small" ' + (prevDisabled ? 'disabled' : '') +
                    ' onclick="loadLLCs(' + (llcCurrentPage - 1) + ')">Prev</button>' +
                    ' <span style="margin:0 10px;">Page ' + (llcCurrentPage + 1) + '</span> ' +
                    '<button class="btn btn-small" ' + (nextDisabled ? 'disabled' : '') +
                    ' onclick="loadLLCs(' + (llcCurrentPage + 1) + ')">Next</button>';
            }

            if (llcs.length === 0) {
                const tr = document.createElement('tr');
                const td = document.createElement('td');
                td.colSpan = 7;
                td.textContent = llcCurrentPage === 0
                    ? 'No LLCs found. Run the scraper to get started!'
                    : 'No more results.';
                td.style.textAlign = 'center';
                td.style.padding = '20px';
                tr.appendChild(td);
                tbody.appendChild(tr);
                return;
            }

            llcs.forEach(llc => {
                const tr = document.createElement('tr');

                // Business name
                const tdName = document.createElement('td');
                tdName.textContent = llc.business_name;
                tr.appendChild(tdName);

                // Filing date
                const tdDate = document.createElement('td');
                tdDate.textContent = llc.filing_date || '-';
                tr.appendChild(tdDate);

                // Address
                const tdAddr = document.createElement('td');
                tdAddr.textContent = llc.principal_address || '-';
                tdAddr.title = llc.principal_address || '';
                tdAddr.style.maxWidth = '200px';
                tdAddr.style.overflow = 'hidden';
                tdAddr.style.textOverflow = 'ellipsis';
                tdAddr.style.whiteSpace = 'nowrap';
                tdAddr.style.cursor = 'help';
                tr.appendChild(tdAddr);

                // Has website
                const tdWeb = document.createElement('td');
                const webBadge = document.createElement('span');
                if (llc.has_website === 1) {
                    webBadge.className = 'badge badge-yes';
                    webBadge.textContent = 'Yes';
                } else if (llc.has_website === -1) {
                    webBadge.className = 'badge badge-no';
                    webBadge.textContent = 'No';
                } else {
                    webBadge.className = 'badge badge-unknown';
                    webBadge.textContent = '?';
                }
                tdWeb.appendChild(webBadge);
                tr.appendChild(tdWeb);

                // Email
                const tdEmail = document.createElement('td');
                tdEmail.textContent = llc.email_address || '-';
                tr.appendChild(tdEmail);

                // Outreach status
                const tdStatus = document.createElement('td');
                const statusBadge = document.createElement('span');
                statusBadge.className = 'badge badge-' + (llc.outreach_status || 'pending');
                statusBadge.textContent = (llc.outreach_status || 'pending').charAt(0).toUpperCase()
                    + (llc.outreach_status || 'pending').slice(1);
                tdStatus.appendChild(statusBadge);
                tr.appendChild(tdStatus);

                // Actions
                const tdActions = document.createElement('td');
                tdActions.className = 'actions';

                if (llc.outreach_status === 'pending' || llc.outreach_status === null) {
                    const approveBtn = document.createElement('button');
                    approveBtn.className = 'btn btn-success btn-small';
                    approveBtn.textContent = 'Approve';
                    approveBtn.onclick = () => approveLLC(llc.id);
                    tdActions.appendChild(approveBtn);

                    const skipBtn = document.createElement('button');
                    skipBtn.className = 'btn btn-secondary btn-small';
                    skipBtn.textContent = 'Skip';
                    skipBtn.onclick = () => skipLLC(llc.id);
                    tdActions.appendChild(skipBtn);
                }

                if (llc.email_address && llc.outreach_status !== 'sent') {
                    const previewBtn = document.createElement('button');
                    previewBtn.className = 'btn btn-small';
                    previewBtn.style.background = '#b5652a';
                    previewBtn.style.color = '#fff';
                    previewBtn.textContent = 'Preview';
                    previewBtn.onclick = () => previewEmail(llc.id);
                    tdActions.appendChild(previewBtn);
                }

                tr.appendChild(tdActions);
                tbody.appendChild(tr);
            });
        })
        .catch(err => console.error('Error loading LLCs:', err));
}

function approveLLC(id) {
    fetch('/api/llcs/' + id + '/approve', { method: 'POST' })
        .then(res => res.json())
        .then(() => {
            loadLLCs();
            showMessage('LLC approved for outreach', 'success');
        })
        .catch(err => showMessage('Error: ' + err.message, 'error'));
}

function skipLLC(id) {
    fetch('/api/llcs/' + id + '/skip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'manually skipped' })
    })
        .then(res => res.json())
        .then(() => {
            loadLLCs();
            showMessage('LLC skipped', 'success');
        })
        .catch(err => showMessage('Error: ' + err.message, 'error'));
}

// --- Email preview modal ---

function previewEmail(id) {
    fetch('/api/email-preview/' + id)
        .then(res => res.json())
        .then(data => {
            document.getElementById('preview-subject').textContent = 'Subject: ' + data.subject;
            document.getElementById('preview-to').textContent = 'To: ' + data.to;
            document.getElementById('preview-body').innerHTML = data.html;
            document.getElementById('preview-send-btn').onclick = () => sendSingleEmail(id);
            document.getElementById('modal-overlay').classList.add('active');
        })
        .catch(err => showMessage('Error loading preview: ' + err.message, 'error'));
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
}

function sendSingleEmail(id) {
    fetch('/api/llcs/' + id + '/send', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            closeModal();
            if (data.success) {
                showMessage('Email sent!', 'success');
                loadLLCs();
                loadStats();
            } else {
                showMessage('Send failed: ' + (data.error || 'unknown error'), 'error');
            }
        })
        .catch(err => showMessage('Error: ' + err.message, 'error'));
}

// --- Email queue & history ---

function loadEmailQueue() {
    fetch('/api/llcs?outreach_status=approved&limit=50')
        .then(res => res.json())
        .then(llcs => {
            const container = document.getElementById('queue-list');
            container.innerHTML = '';

            if (llcs.length === 0) {
                container.innerHTML = '<p style="padding:15px;text-align:center;color:#888;">No emails in queue. Approve LLCs from the LLCs tab to add them.</p>';
                return;
            }

            llcs.forEach(llc => {
                const div = document.createElement('div');
                div.style.cssText = 'display:flex;justify-content:space-between;align-items:center;padding:10px 12px;border-bottom:1px solid #e8e2d9;';

                const info = document.createElement('div');
                info.innerHTML = '<strong>' + escapeHtml(llc.business_name) + '</strong>'
                    + '<br><span style="color:#888;font-size:0.85em;">'
                    + escapeHtml(llc.email_address || 'no email') + '</span>';
                div.appendChild(info);

                const actions = document.createElement('div');
                if (llc.email_address) {
                    const sendBtn = document.createElement('button');
                    sendBtn.className = 'btn btn-success btn-small';
                    sendBtn.textContent = 'Send';
                    sendBtn.onclick = () => sendSingleEmail(llc.id);
                    actions.appendChild(sendBtn);
                }
                const previewBtn = document.createElement('button');
                previewBtn.className = 'btn btn-small';
                previewBtn.style.cssText = 'background:#b5652a;color:#fff;margin-left:5px;';
                previewBtn.textContent = 'Preview';
                previewBtn.onclick = () => previewEmail(llc.id);
                actions.appendChild(previewBtn);

                div.appendChild(actions);
                container.appendChild(div);
            });
        })
        .catch(err => console.error('Error loading queue:', err));
}

function loadEmailHistory() {
    fetch('/api/email-history')
        .then(res => res.json())
        .then(history => {
            const container = document.getElementById('history-list');
            container.innerHTML = '';

            if (history.length === 0) {
                container.innerHTML = '<p style="padding:15px;text-align:center;color:#888;">No emails sent yet.</p>';
                return;
            }

            history.forEach(entry => {
                const div = document.createElement('div');
                div.className = 'log-entry';

                const ts = document.createElement('span');
                ts.className = 'log-timestamp';
                ts.textContent = new Date(entry.sent_at).toLocaleString();
                div.appendChild(ts);

                const msg = document.createElement('span');
                msg.className = 'log-message';
                msg.textContent = entry.business_name + ' -> ' + entry.to_address;
                div.appendChild(msg);

                const badge = document.createElement('span');
                badge.className = 'log-status ' + entry.status;
                badge.textContent = entry.status.toUpperCase();
                div.appendChild(badge);

                container.appendChild(div);
            });
        })
        .catch(err => console.error('Error loading history:', err));
}

function sendAllEmails() {
    if (!confirm('Send outreach emails to all approved LLCs?')) return;

    fetch('/api/send-emails', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadEmailQueue();
                loadStats();
            } else {
                showMessage(data.message, 'error');
            }
        })
        .catch(err => showMessage('Error: ' + err.message, 'error'));
}

// --- Scraper & enricher triggers ---

function runScraperNow() {
    showMessage('Running scraper...', 'success');
    fetch('/api/run-scraper', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadStats();
            } else {
                showMessage('Error: ' + data.message, 'error');
            }
        })
        .catch(err => showMessage('Error: ' + err.message, 'error'));
}

function runEnricherNow() {
    showMessage('Running enricher...', 'success');
    fetch('/api/run-enricher', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadLLCs();
                loadStats();
            } else {
                showMessage('Error: ' + data.message, 'error');
            }
        })
        .catch(err => showMessage('Error: ' + err.message, 'error'));
}

// --- CSV import ---

function importCSV() {
    const csv = document.getElementById('csv-input').value.trim();
    if (!csv) {
        showMessage('Please paste CSV data first', 'error');
        return;
    }

    fetch('/api/import-csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ csv: csv })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                document.getElementById('csv-input').value = '';
                loadStats();
            } else {
                showMessage('Error: ' + data.message, 'error');
            }
        })
        .catch(err => showMessage('Error: ' + err.message, 'error'));
}

// --- Logs ---

function loadLogs() {
    fetch('/api/logs')
        .then(res => res.json())
        .then(logs => {
            const container = document.getElementById('logs-list');
            container.innerHTML = '';

            if (logs.length === 0) {
                container.innerHTML = '<p>No logs yet.</p>';
                return;
            }

            logs.forEach(log => {
                const entry = document.createElement('div');
                entry.className = 'log-entry';

                const ts = document.createElement('span');
                ts.className = 'log-timestamp';
                ts.textContent = new Date(log.timestamp).toLocaleString();
                entry.appendChild(ts);

                const msg = document.createElement('span');
                msg.className = 'log-message';
                msg.textContent = log.message;
                entry.appendChild(msg);

                const status = document.createElement('span');
                status.className = 'log-status ' + log.status;
                status.textContent = log.status.toUpperCase();
                entry.appendChild(status);

                container.appendChild(entry);
            });
        })
        .catch(err => console.error('Error loading logs:', err));
}

// --- Scheduler status ---

function loadSchedulerStatus() {
    fetch('/api/scheduler-status')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('scheduler-info');
            container.innerHTML = '';

            if (data.running && data.jobs && data.jobs.length > 0) {
                const p1 = document.createElement('p');
                p1.innerHTML = '<strong>Scheduler is running</strong>';
                container.appendChild(p1);

                data.jobs.forEach(job => {
                    const p = document.createElement('p');
                    const nextRun = job.next_run ? new Date(job.next_run).toLocaleString() : 'unknown';
                    p.textContent = job.name + ' - Next: ' + nextRun;
                    container.appendChild(p);
                });
            } else {
                const p = document.createElement('p');
                p.textContent = 'Scheduler is not running. Save settings to start.';
                container.appendChild(p);
            }
        })
        .catch(err => console.error('Error loading scheduler status:', err));
}

// --- Utilities ---

function showMessage(message, type) {
    const statusDiv = document.getElementById('status-message');
    statusDiv.textContent = message;
    statusDiv.className = type;
    setTimeout(() => {
        statusDiv.className = '';
        statusDiv.textContent = '';
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// --- Auto-refresh ---

setInterval(loadSchedulerStatus, 30000);
setInterval(() => {
    const activeTab = document.querySelector('.tab-content.active');
    if (activeTab) {
        if (activeTab.id === 'llcs') loadLLCs();
        else if (activeTab.id === 'dashboard') loadStats();
    }
}, 60000);

// --- Init ---

document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    loadStats();
    loadSchedulerStatus();
});
