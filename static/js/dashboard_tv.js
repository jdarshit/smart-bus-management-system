function formatShiftLabel(shift) {
  if (shift === 'shift2') return 'SHIFT 2';
  return 'SHIFT 1';
}

function statusClass(status) {
  if (status === 'On Time') return 'on-time';
  if (status === 'Late') return 'late';
  return 'waiting';
}

function updateClock() {
  const now = new Date();
  const clock = document.getElementById('clock');
  if (!clock) return;
  clock.textContent = now.toLocaleTimeString('en-GB', {
    hour12: false,
    timeZone: 'Asia/Kolkata',
  });
}

const lastState = new Map();

function busCardTemplate(bus, state, statusText, arrival) {
  return `
    <section class="bus-card ${state}" data-bus="${bus.bus_number || '--'}">
      <div class="bus-title" data-field="bus_number">${bus.bus_number || '--'}</div>
      <div class="meta" data-field="license_plate">${bus.license_plate || '—'}</div>
      <div class="meta" data-field="driver_name">Driver: ${bus.driver_name || '—'}</div>
      <div class="meta" data-field="route_name">Route: ${bus.route_name || '—'}</div>
      <div class="meta" data-field="arrival_time">Arrival: ${arrival}</div>
      <div class="status-line" data-field="status">Status: <span class="status-chip ${state}">${statusText}</span></div>
    </section>
  `;
}

function renderCards(payload) {
  const grid = document.getElementById('busGrid');
  if (!grid) return;

  const shiftNode = document.getElementById('activeShift');
  if (shiftNode) {
    shiftNode.textContent = `ACTIVE SHIFT: ${formatShiftLabel(payload.active_shift)}`;
  }

  const buses = payload.buses || [];
  buses.forEach((bus) => {
    const key = bus.bus_number || '--';
    const state = statusClass(bus.status);
    const statusText = bus.status || 'Waiting';
    const arrival = bus.arrival_time || '--:--:--';
    const serialized = JSON.stringify({
      license_plate: bus.license_plate || '—',
      driver_name: bus.driver_name || '—',
      route_name: bus.route_name || '—',
      arrival,
      statusText,
      state,
    });

    if (lastState.get(key) === serialized) return;
    lastState.set(key, serialized);

    const card = grid.querySelector(`[data-bus="${key}"]`);
    if (!card) {
      grid.insertAdjacentHTML('beforeend', busCardTemplate(bus, state, statusText, arrival));
      return;
    }

    card.classList.remove('on-time', 'late', 'waiting');
    card.classList.add(state);

    const lp = card.querySelector('[data-field="license_plate"]');
    if (lp) lp.textContent = bus.license_plate || '—';
    const dn = card.querySelector('[data-field="driver_name"]');
    if (dn) dn.textContent = `Driver: ${bus.driver_name || '—'}`;
    const rn = card.querySelector('[data-field="route_name"]');
    if (rn) rn.textContent = `Route: ${bus.route_name || '—'}`;
    const at = card.querySelector('[data-field="arrival_time"]');
    if (at) at.textContent = `Arrival: ${arrival}`;
    const st = card.querySelector('[data-field="status"]');
    if (st) st.innerHTML = `Status: <span class="status-chip ${state}">${statusText}</span>`;
  });
}

async function fetchBusStatus() {
  try {
    const resp = await fetch('/api/bus_status', { credentials: 'same-origin' });
    if (!resp.ok) return;
    const data = await resp.json();
    renderCards(data);
  } catch (error) {
    console.warn('fetchBusStatus failed', error);
  }
}

function enterFullscreenMode() {
  const el = document.documentElement;
  if (!document.fullscreenElement && el.requestFullscreen) {
    el.requestFullscreen().catch(() => {
    });
  }
}

setInterval(fetchBusStatus, 500);
setInterval(updateClock, 1000);
enterFullscreenMode();
updateClock();
fetchBusStatus();
