let currentActiveShift = null;

function renderActiveShift(shift) {
  const badge = document.getElementById('activeShiftBadge');
  const shift1Btn = document.getElementById('shift1Btn');
  const shift2Btn = document.getElementById('shift2Btn');
  if (!badge || !shift1Btn || !shift2Btn) return;

  const normalized = shift === 'shift2' ? 'shift2' : 'shift1';
  currentActiveShift = normalized;
  badge.textContent = `Active: ${normalized.toUpperCase()}`;

  shift1Btn.classList.toggle('btn-primary', normalized === 'shift1');
  shift1Btn.classList.toggle('btn-outline-primary', normalized !== 'shift1');
  shift2Btn.classList.toggle('btn-primary', normalized === 'shift2');
  shift2Btn.classList.toggle('btn-outline-primary', normalized !== 'shift2');
}

async function setShift(shift) {
  try {
    const resp = await fetch('/api/set_shift', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ shift }),
    });
    if (!resp.ok) return;
    const data = await resp.json();
    renderActiveShift(data.active_shift);
  } catch (error) {
    console.warn('setShift failed', error);
  }
}

async function fetchBusArrivals() {
  try {
    const resp = await fetch('/admin/api/bus-arrivals', { credentials: 'same-origin' });
    if (!resp.ok) return;

    const data = await resp.json();
    const body = document.getElementById('busArrivalBody');
    if (!body) return;

    renderActiveShift(data.active_shift);

    const rows = data.arrivals || [];
    if (!rows.length) {
      body.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3">No arrivals yet.</td></tr>';
      return;
    }

    body.innerHTML = rows.map((row) => {
      const badgeClass = row.status === 'On Time' ? 'bg-success' : 'bg-danger';
      return `
        <tr>
          <td><strong>${row.bus_number}</strong></td>
          <td>${row.license_plate || '—'}</td>
          <td>${row.driver_name || '—'}</td>
          <td>${row.route_name || '—'}</td>
          <td>${row.arrival_time}</td>
          <td><span class="badge ${badgeClass}">${row.status}</span></td>
          <td><span class="badge bg-info text-dark">${(row.shift || 'shift1').toUpperCase()}</span></td>
        </tr>
      `;
    }).join('');

    const updated = document.getElementById('lastUpdated');
    if (updated) updated.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    console.warn('fetchBusArrivals failed', error);
  }
}

const shift1Btn = document.getElementById('shift1Btn');
const shift2Btn = document.getElementById('shift2Btn');
if (shift1Btn) shift1Btn.addEventListener('click', () => setShift('shift1'));
if (shift2Btn) shift2Btn.addEventListener('click', () => setShift('shift2'));

setInterval(fetchBusArrivals, 500);
fetchBusArrivals();
