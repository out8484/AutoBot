document.addEventListener('DOMContentLoaded', () => {
    // State management
    const state = {
        scanResults: [],
        currentView: 'dashboard',
        isScanning: false,
    };

    // Navigation
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.view');
    const viewTitle = document.getElementById('view-title');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const viewId = item.getAttribute('data-view');
            switchView(viewId);
        });
    });

    function switchView(viewId) {
        views.forEach(v => v.classList.add('hidden'));
        document.getElementById(`${viewId}-view`).classList.remove('hidden');

        navItems.forEach(nav => {
            nav.classList.toggle('active', nav.getAttribute('data-view') === viewId);
        });

        const titles = {
            'dashboard': 'Dashboard Overview',
            'ip-scan': 'Network IP Scanner',
            'config-push': 'Automation Hub',
            'credentials': 'User Groups & Credentials',
            'logs': 'Archived Logs'
        };
        viewTitle.innerText = titles[viewId] || 'Autobot';
        state.currentView = viewId;

        if (viewId === 'dashboard') updateDashboard();
        if (viewId === 'credentials') updateCredentialsView();
        if (viewId === 'config-push') updateGroupsDropdown();
    }

    // Current Time
    setInterval(() => {
        const now = new Date();
        document.getElementById('current-time').innerText = now.toLocaleTimeString();
    }, 1000);

    // IP Scan Logic
    const startScanBtn = document.getElementById('start-scan-btn');
    const ipRangeInput = document.getElementById('ip-range');
    const scanProgressContainer = document.getElementById('scan-progress-container');
    const scanBarFill = document.getElementById('scan-bar-fill');
    const scanStatusText = document.getElementById('scan-status-text');
    const scanPercentage = document.getElementById('scan-percentage');
    const scanResultsBody = document.getElementById('scan-results-body');

    async function handleStartScan() {
        const ipRange = ipRangeInput.value.trim();
        if (!ipRange) return alert('Please enter an IP range');

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip_range: ipRange })
            });

            if (response.ok) {
                state.isScanning = true;
                scanProgressContainer.classList.remove('hidden');
                startScanBtn.disabled = true;
                pollScanStatus();
            } else {
                const err = await response.json();
                alert('Error: ' + err.detail);
            }
        } catch (error) {
            console.error('Scan error:', error);
        }
    }

    startScanBtn.addEventListener('click', handleStartScan);

    ipRangeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleStartScan();
        }
    });

    async function pollScanStatus() {
        if (!state.isScanning) return;

        try {
            const response = await fetch('/api/scan/status');
            const data = await response.json();

            // Update Progress
            const progress = data.progress;
            scanBarFill.style.width = `${progress.progress}%`;
            scanPercentage.innerText = `${progress.progress}%`;
            scanStatusText.innerText = progress.status === 'running'
                ? `Scanning ${progress.current_ip}...`
                : 'Scan Completed';

            // Update Results Table
            updateTable(data.results);
            state.scanResults = data.results;

            if (progress.status === 'completed') {
                state.isScanning = false;
                startScanBtn.disabled = false;
                updateTargetIpList();
                updateDashboard();
            } else {
                updateTargetIpList();
                setTimeout(pollScanStatus, 1000);
            }
        } catch (error) {
            console.error('Polling error:', error);
            state.isScanning = false;
        }
    }

    function updateTable(results) {
        scanResultsBody.innerHTML = results.map(res => {
            const isAvailable = res.status === 'Available';
            return `
            <tr>
                <td><span class="status-badge ${res.status.toLowerCase()}">${res.status}</span></td>
                <td><a href="#" class="ip-link" onclick="openActionModal(event, '${res.ip}')">${res.ip}</a></td>
                <td>${res.mac}</td>
                <td>${res.latency}</td>
                <td>${res.ports.join(', ') || 'None'}</td>
                <td style="font-size: 0.8rem; color: #64748b">${res.last_seen}</td>
                <td style="text-align: center;">
                    ${isAvailable ? `<input type="checkbox" class="ip-selector-cb" data-ip="${res.ip}" onchange="syncSelectedIps()">` : '-'}
                </td>
            </tr>
        `}).join('');
    }

    const actionModal = document.getElementById('action-modal');
    const pingResultBox = document.getElementById('ping-result');
    let currentActionIp = '';

    window.openActionModal = (e, ip) => {
        e.preventDefault();
        currentActionIp = ip;
        document.getElementById('action-ip-title').innerText = ip;
        document.getElementById('action-ssh').href = `ssh://${ip}`;
        document.getElementById('action-telnet').href = `telnet://${ip}`;
        pingResultBox.classList.add('hidden');
        actionModal.classList.remove('hidden');
    };

    document.getElementById('close-action-modal').onclick = () => actionModal.classList.add('hidden');

    document.getElementById('action-ping').onclick = async () => {
        pingResultBox.innerText = 'Ping in progress...';
        pingResultBox.classList.remove('hidden');
        try {
            const res = await fetch(`/api/ping/${currentActionIp}`);
            const data = await res.json();
            if (data.status === 'success') {
                pingResultBox.innerHTML = `<span style="color: var(--accent-green)">Success: ${data.latency}</span>`;
            } else {
                pingResultBox.innerHTML = `<span style="color: #ef4444">${data.message}</span>`;
            }
        } catch (err) {
            pingResultBox.innerText = 'Error: ' + err.message;
        }
    };

    window.syncSelectedIps = () => {
        const selected = Array.from(document.querySelectorAll('.ip-selector-cb:checked'))
            .map(cb => cb.getAttribute('data-ip'));
        const targetInput = document.getElementById('ssh-target-ip');
        if (targetInput) {
            targetInput.value = selected.join(', ');
        }
    };

    // Dashboard Updates
    function updateDashboard() {
        const active = state.scanResults.filter(r => r.status === 'Active').length;
        const available = state.scanResults.filter(r => r.status === 'Available').length;

        document.getElementById('total-scanned').innerText = state.scanResults.length;
        document.getElementById('active-ips').innerText = active;
        document.getElementById('available-ips').innerText = available;

        const availableBody = document.getElementById('available-ips-body');
        const availableList = state.scanResults.filter(r => r.status === 'Available').slice(0, 10);

        availableBody.innerHTML = availableList.length ? availableList.map(res => `
            <tr>
                <td>${res.ip}</td>
                <td>${res.last_seen}</td>
                <td><button class="btn primary small" onclick="selectIpForConfig('${res.ip}')">Use</button></td>
            </tr>
        `).join('') : '<tr><td colspan="3" style="text-align:center">No available IPs found. Scan network first.</td></tr>';
        updateTargetIpList();
    }

    function updateTargetIpList() {
        const datalist = document.getElementById('target-ip-list');
        if (!datalist) return;

        // Filter and map only "Available" IPs as per user's request
        const availableIps = state.scanResults
            .filter(res => res.status === 'Available')
            .map(res => res.ip);

        if (availableIps.length === 0) {
            datalist.innerHTML = '';
            return;
        }

        datalist.innerHTML = availableIps.map(ip => `
            <option value="${ip}">Available</option>
        `).join('');
    }

    window.selectIpForConfig = (ip) => {
        document.getElementById('ssh-target-ip').value = ip;
        switchView('config-push');
    };

    // Config Push Logic
    const pushConfigBtn = document.getElementById('push-config-btn');
    const terminal = document.getElementById('terminal');

    // Template logic: automatically create inputs for variables in textarea
    const sshCommands = document.getElementById('ssh-commands');
    const varsContainer = document.getElementById('dynamic-vars-container');

    function updateDynamicVars() {
        const text = sshCommands.value;
        const matches = [...text.matchAll(/\{\{([^}]+)\}\}/g)];
        const uniqueKeys = [...new Set(matches.map(m => m[1].trim()))];

        // Keep track of current values to not lose them on refresh
        const currentValues = {};
        varsContainer.querySelectorAll('input').forEach(inp => {
            currentValues[inp.getAttribute('data-key')] = inp.value;
        });

        varsContainer.innerHTML = uniqueKeys.map(key => `
            <div class="form-group" style="margin-bottom: 0; min-width: 150px;">
                <label style="font-size: 0.7rem; margin-bottom: 2px;">${key}</label>
                <input type="text" class="var-input" data-key="${key}" value="${currentValues[key] || ''}" placeholder="${key}" style="padding: 5px 8px; font-size: 0.8rem;">
            </div>
        `).join('');
    }

    sshCommands.addEventListener('input', updateDynamicVars);
    updateDynamicVars(); // Initial run

    const previewModal = document.getElementById('preview-modal');
    const previewText = document.getElementById('config-preview-text');
    const confirmPushBtn = document.getElementById('confirm-push');
    const cancelPushBtn = document.getElementById('cancel-push');
    const closeModalBtn = document.querySelector('.close-modal');

    function getFinalConfig() {
        let commands = sshCommands.value;
        varsContainer.querySelectorAll('input').forEach(inp => {
            const key = inp.getAttribute('data-key');
            const val = inp.value || "";
            // Replace all occurrences of {{key}}
            commands = commands.replaceAll(`{{${key}}}`, val);
        });
        return commands;
    }

    pushConfigBtn.addEventListener('click', () => {
        const ip = document.getElementById('ssh-target-ip').value;
        const group = document.getElementById('ssh-user-group').value;
        const username = document.getElementById('ssh-username').value;
        const password = document.getElementById('ssh-password').value;
        const commands = sshCommands.value;

        if (!ip || (!group && (!username || !password)) || !commands.trim()) {
            return alert('Please fill in Target IP, Credentials, and Commands');
        }

        // Show preview
        const finalConfig = getFinalConfig();
        previewText.innerText = finalConfig;
        previewModal.classList.remove('hidden');
    });

    const hideModal = () => previewModal.classList.add('hidden');
    cancelPushBtn.addEventListener('click', hideModal);
    closeModalBtn.addEventListener('click', hideModal);

    confirmPushBtn.addEventListener('click', async () => {
        hideModal();
        const ip = document.getElementById('ssh-target-ip').value;
        const group = document.getElementById('ssh-user-group').value;
        const username = document.getElementById('ssh-username').value;
        const password = document.getElementById('ssh-password').value;
        const commands = sshCommands.value;

        // Collect template values
        const templateValues = {};
        varsContainer.querySelectorAll('input').forEach(inp => {
            templateValues[inp.getAttribute('data-key')] = inp.value;
        });

        addLogEntry(`[STAGE 2] USER CONFIRMED. Starting deployment process...`, 'system');
        addLogEntry(`Connecting to ${ip} via NETCONF (PyEZ)...`, 'system');
        pushConfigBtn.disabled = true;

        try {
            const response = await fetch('/api/push-config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_ip: ip,
                    user_group: group || null,
                    username: username || null,
                    password: password || null,
                    commands: commands,
                    template_values: templateValues,
                    verify_commands: null,
                    device_type: "juniper_junos"
                })
            });

            const data = await response.json();

            if (!response.ok) {
                const errorMsg = data.detail || data.log || `Server Error ${response.status}`;
                addLogEntry(`[ERROR] ${errorMsg}`, 'error');
                return;
            }

            if (data.status === 'success') {
                addLogEntry(data.log || 'Task completed successfully', 'success');
            } else {
                addLogEntry(data.log || 'An unknown error occurred on the server', 'error');
            }
        } catch (error) {
            addLogEntry(`Connection Error: ${error.message}`, 'error');
        } finally {
            pushConfigBtn.disabled = false;
        }
    });

    function addLogEntry(text, type) {
        const div = document.createElement('div');
        div.className = `log-entry ${type}`;
        div.innerText = text;
        terminal.appendChild(div);
        terminal.scrollTop = terminal.scrollHeight;
    }

    document.getElementById('clear-logs').addEventListener('click', () => {
        terminal.innerHTML = '<div class="log-entry system">Logs cleared...</div>';
    });

    document.getElementById('download-logs').addEventListener('click', () => {
        const blob = new Blob([terminal.innerText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `autobot_log_${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
    });

    document.getElementById('download-results').addEventListener('click', () => {
        const json = JSON.stringify(state.scanResults, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `scan_results_${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
    });

    document.getElementById('refresh-dashboard').addEventListener('click', updateDashboard);

    // Credentials Logic
    async function updateCredentialsView() {
        const response = await fetch('/api/credentials');
        const creds = await response.json();
        const body = document.getElementById('credentials-body');

        body.innerHTML = Object.keys(creds).map(group => `
            <tr>
                <td>${group}</td>
                <td>${creds[group].username}</td>
                <td>
                    <button class="btn danger small" onclick="deleteCredential('${group}')">Delete</button>
                </td>
            </tr>
        `).join('') || '<tr><td colspan="3" style="text-align:center">No user groups saved.</td></tr>';
    }

    async function updateGroupsDropdown() {
        const response = await fetch('/api/credentials');
        const creds = await response.json();
        const select = document.getElementById('ssh-user-group');

        const currentValue = select.value;
        select.innerHTML = '<option value="">-- Select Group --</option>' +
            Object.keys(creds).map(group => `<option value="${group}">${group}</option>`).join('');
        select.value = currentValue;
    }

    document.getElementById('save-cred-btn').addEventListener('click', async () => {
        const group = document.getElementById('cred-group-name').value;
        const user = document.getElementById('cred-username').value;
        const pass = document.getElementById('cred-password').value;

        if (!group || !user || !pass) return alert('Fill all fields');

        await fetch('/api/credentials', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group_name: group, username: user, password: pass })
        });

        document.getElementById('cred-group-name').value = '';
        document.getElementById('cred-username').value = '';
        document.getElementById('cred-password').value = '';
        updateCredentialsView();
    });

    window.deleteCredential = async (group) => {
        if (!confirm(`Delete group ${group}?`)) return;
        await fetch(`/api/credentials/${group}`, { method: 'DELETE' });
        updateCredentialsView();
    };
});
