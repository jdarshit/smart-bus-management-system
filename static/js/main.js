// Smart Bus Management System - Main JS

document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const body = document.body;

    const closeSidebar = () => {
        if (!sidebar) return;
        sidebar.classList.remove('show');
        body.classList.remove('sidebar-open');
    };

    const openSidebar = () => {
        if (!sidebar) return;
        sidebar.classList.add('show');
        body.classList.add('sidebar-open');
    };

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            if (sidebar.classList.contains('show')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });

        sidebar.querySelectorAll('.sidebar-item').forEach((link) => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    closeSidebar();
                }
            });
        });

        document.addEventListener('click', (event) => {
            if (window.innerWidth > 768 || !sidebar.classList.contains('show')) return;
            const clickedInsideSidebar = sidebar.contains(event.target);
            const clickedToggle = sidebarToggle.contains(event.target);
            if (!clickedInsideSidebar && !clickedToggle) {
                closeSidebar();
            }
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                closeSidebar();
            }
        });
    }

    const currentLocation = window.location.pathname;
    document.querySelectorAll('.sidebar-item').forEach((item) => {
        const href = item.getAttribute('href');
        if (!href) return;
        if (currentLocation === href || currentLocation.startsWith(`${href}/`)) {
            item.classList.add('active');
        }
    });
});

function validateForm(formElement) {
    const form = document.querySelector(formElement);
    if (!form) return false;

    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    inputs.forEach((input) => {
        if (!String(input.value || '').trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    return isValid;
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function checkPasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    return strength;
}

async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };

    if (data && ['POST', 'PUT', 'PATCH'].includes(method.toUpperCase())) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        const result = await response.json();
        return { success: response.ok, status: response.status, data: result };
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;

    const container = document.querySelector('.main-content .content-wrapper') || document.body;
    container.prepend(alertDiv);

    setTimeout(() => alertDiv.remove(), 5000);
}

function filterTable(tableId, searchInputId) {
    const searchInput = document.getElementById(searchInputId);
    const table = document.getElementById(tableId);
    if (!searchInput || !table) return;

    searchInput.addEventListener('keyup', function onKeyUp() {
        const searchTerm = this.value.toLowerCase();
        table.querySelectorAll('tbody tr').forEach((row) => {
            row.style.display = row.textContent.toLowerCase().includes(searchTerm) ? '' : 'none';
        });
    });
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
    });
}

function formatTime(timeString) {
    return new Date(timeString).toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
}

function setButtonLoading(buttonElement, isLoading = true, defaultText = 'Submit') {
    if (!buttonElement) return;
    if (isLoading) {
        buttonElement.disabled = true;
        buttonElement.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    } else {
        buttonElement.disabled = false;
        buttonElement.innerHTML = defaultText;
    }
}

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal || typeof bootstrap === 'undefined') return;
    new bootstrap.Modal(modal).show();
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal || typeof bootstrap === 'undefined') return;
    const instance = bootstrap.Modal.getInstance(modal);
    if (instance) instance.hide();
}

function initAttendanceChart() {
    const ctx = document.getElementById('attendanceChart');
    if (!ctx || typeof Chart === 'undefined' || ctx.dataset.labels) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Weekly Attendance',
                data: [65, 72, 80, 88, 92, 78, 65],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.06)',
                tension: 0.4,
                fill: true,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: true, position: 'top' } },
        },
    });
}

function initBusStatusChart() {
    const ctx = document.getElementById('busStatusChart');
    if (!ctx || typeof Chart === 'undefined' || ctx.dataset.labels) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Active', 'Maintenance', 'Idle'],
            datasets: [{
                data: [18, 5, 10],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                borderColor: '#fff',
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { position: 'bottom' } },
        },
    });
}

window.addEventListener('load', () => {
    initAttendanceChart();
    initBusStatusChart();
});
