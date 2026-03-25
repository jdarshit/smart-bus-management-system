async function fetchHtmlDocument(url) {
  const response = await fetch(url, { credentials: 'same-origin' });
  if (!response.ok) {
    throw new Error(`Failed to load ${url}`);
  }
  const html = await response.text();
  return new DOMParser().parseFromString(html, 'text/html');
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) node.textContent = value;
}

async function initAdminDashboard() {
  const studentsPanel = document.getElementById('recentStudentsList');
  const arrivalsPanel = document.getElementById('recentArrivalsList');
  const driversPanel = document.getElementById('driverOverviewList');
  if (!studentsPanel || !arrivalsPanel || !driversPanel) return;

  try {
    const [studentsDoc, driversDoc] = await Promise.all([
      fetchHtmlDocument('/students/'),
      fetchHtmlDocument('/drivers/'),
    ]);

    const studentRows = Array.from(studentsDoc.querySelectorAll('tbody > tr'))
      .filter((row) => !row.classList.contains('collapse') && row.children.length >= 5)
      .slice(0, 5);
    studentsPanel.innerHTML = studentRows.length ? studentRows.map((row) => {
      const cells = row.querySelectorAll('td');
      return `
        <div class="panel-list-item">
          <div>
            <div class="fw-bold">${cells[0]?.textContent?.trim() || '—'}</div>
            <div class="meta">${cells[1]?.textContent?.trim() || '—'} • Year ${cells[2]?.textContent?.trim() || '—'}</div>
          </div>
          <span class="stop-chip">${cells[4]?.textContent?.trim() || '—'}</span>
        </div>`;
    }).join('') : '<div class="text-muted">No student records available.</div>';

    const driverRows = Array.from(driversDoc.querySelectorAll('tbody > tr'))
      .filter((row) => !row.classList.contains('collapse') && row.children.length >= 5)
      .slice(0, 5);
    driversPanel.innerHTML = driverRows.length ? driverRows.map((row) => {
      const cells = row.querySelectorAll('td');
      const img = cells[0]?.querySelector('img');
      return `
        <div class="panel-list-item">
          <div class="d-flex align-items-center gap-3">
            ${img ? `<img src="${img.getAttribute('src')}" style="width:44px;height:44px;border-radius:12px;object-fit:cover;">` : '<div class="stat-icon-wrap" style="width:44px;height:44px;font-size:1rem;background:#e2e8f0;color:#334155;"><i class="bi bi-person"></i></div>'}
            <div>
              <div class="fw-bold">${cells[1]?.textContent?.trim() || '—'}</div>
              <div class="meta">${cells[2]?.textContent?.trim() || '—'} • Bus ${cells[4]?.textContent?.trim() || '—'}</div>
            </div>
          </div>
          <div class="meta">${cells[3]?.textContent?.trim() || '—'}</div>
        </div>`;
    }).join('') : '<div class="text-muted">No driver records available.</div>';

    async function loadRecentArrivals() {
      const arrivalsRes = await fetch('/admin/api/bus-arrivals', { credentials: 'same-origin' });
      const arrivalsData = arrivalsRes.ok ? await arrivalsRes.json() : { arrivals: [] };
      const arrivals = (arrivalsData.arrivals || []).slice(0, 6);
      arrivalsPanel.innerHTML = arrivals.length ? arrivals.map((row) => `
        <div class="panel-list-item">
          <div>
            <div class="fw-bold">${row.bus_number || '—'}</div>
            <div class="meta">${row.route_name || '—'} • ${row.driver_name || '—'}</div>
          </div>
          <div class="text-end">
            <div class="fw-semibold">${row.arrival_time || '—'}</div>
            <span class="badge ${row.status === 'Late' ? 'bg-danger' : 'bg-success'}">${row.status || 'On Time'}</span>
          </div>
        </div>`).join('') : '<div class="text-muted">No recent bus arrivals.</div>';
    }

    await loadRecentArrivals();
    window.setInterval(loadRecentArrivals, 1000);
  } catch (error) {
    studentsPanel.innerHTML = '<div class="text-muted">Unable to load recent students.</div>';
    driversPanel.innerHTML = '<div class="text-muted">Unable to load driver overview.</div>';
    arrivalsPanel.innerHTML = '<div class="text-muted">Unable to load bus arrivals.</div>';
  }
}

async function initAttendanceDashboard() {
  const wrapper = document.getElementById('attendanceSummary');
  if (!wrapper) return;

  const todayPresent = Number(wrapper.dataset.present || '0');
  const absentNode = document.getElementById('attendanceAbsent');
  const unmarkedNode = document.getElementById('attendanceUnmarked');
  const totalNode = document.getElementById('attendanceTotal');

  try {
    const studentsDoc = await fetchHtmlDocument('/students/');
    const totalStudents = Array.from(studentsDoc.querySelectorAll('tbody > tr'))
      .filter((row) => !row.classList.contains('collapse') && row.children.length >= 5).length;
    const absent = 0;
    const unmarked = Math.max(totalStudents - todayPresent - absent, 0);
    setText('attendanceTotal', totalStudents);
    if (absentNode) absentNode.textContent = absent;
    if (unmarkedNode) unmarkedNode.textContent = unmarked;
  } catch (error) {
    if (totalNode) totalNode.textContent = '—';
    if (absentNode) absentNode.textContent = '—';
    if (unmarkedNode) unmarkedNode.textContent = '—';
  }
}

async function initDriverDashboard() {
  const routeNode = document.getElementById('driverRouteName');
  if (!routeNode) return;
  const busNumber = routeNode.dataset.busNumber;
  if (!busNumber) return;

  try {
    const response = await fetch('/api/bus_status', { credentials: 'same-origin' });
    if (!response.ok) return;
    const payload = await response.json();
    const buses = payload.buses || [];
    const match = buses.find((bus) => bus.bus_number === busNumber);
    routeNode.textContent = match?.route_name || 'Route not available';
  } catch (error) {
    routeNode.textContent = 'Route not available';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initAdminDashboard();
  initAttendanceDashboard();
  initDriverDashboard();
});
