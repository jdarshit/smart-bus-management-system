document.addEventListener('DOMContentLoaded', () => {
    const widget = document.getElementById('liveArrivalsWidget');
    if (!widget) return;

    const latestUrl = widget.getAttribute('data-latest-url') || '/api/latest-arrivals?limit=10';
    const summaryUrl = widget.getAttribute('data-summary-url') || '/api/bus-status-summary';
    const tableBody = document.getElementById('latestArrivalsTableBody');
    const onTimeCount = document.getElementById('onTimeBusesCount');
    const lateCount = document.getElementById('lateBusesCount');
    const totalCount = document.getElementById('totalArrivalsTodayCount');

    function badge(status) {
        return status === 'on_time'
            ? '<span class="badge bg-success">On Time</span>'
            : '<span class="badge bg-danger">Late</span>';
    }

    function renderRows(arrivals) {
        if (!tableBody) return;
        if (!arrivals || arrivals.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">No arrivals recorded yet.</td></tr>';
            return;
        }

        const columnCount = tableBody.closest('table')?.querySelectorAll('thead th').length || 5;
        tableBody.innerHTML = arrivals.map((item) => {
            if (columnCount === 3) {
                return `
                    <tr>
                        <td><strong>${item.bus_number}</strong></td>
                        <td class="text-muted small">${item.arrival_time}</td>
                        <td>${badge(item.status)}</td>
                    </tr>`;
            }

            return `
                <tr>
                    <td><strong>${item.bus_number}</strong></td>
                    <td>${item.route_name || 'N/A'}</td>
                    <td>${item.driver_name || 'Unassigned'}</td>
                    <td>${item.arrival_time}</td>
                    <td>${badge(item.status)}</td>
                </tr>`;
        }).join('');
    }

    async function refreshLatestArrivals() {
        try {
            const response = await fetch(latestUrl, { headers: { 'Accept': 'application/json' } });
            if (!response.ok) return;
            const data = await response.json();
            renderRows(data.arrivals || []);
        } catch (error) {
            console.error('Live arrivals fetch failed:', error);
        }
    }

    async function refreshSummary() {
        try {
            const response = await fetch(summaryUrl, { headers: { 'Accept': 'application/json' } });
            if (!response.ok) return;
            const data = await response.json();
            if (onTimeCount) onTimeCount.textContent = data.on_time_buses ?? 0;
            if (lateCount) lateCount.textContent = data.late_buses ?? 0;
            if (totalCount) totalCount.textContent = data.total_arrivals_today ?? 0;
        } catch (error) {
            console.error('Bus status summary fetch failed:', error);
        }
    }

    refreshLatestArrivals();
    refreshSummary();
    setInterval(() => {
        refreshLatestArrivals();
        refreshSummary();
    }, 5000);
});
