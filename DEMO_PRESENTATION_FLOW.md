# Demo Presentation Flow

Use this script for a smooth 2-3 minute final project demo.

## 1. Opening (15-20 sec)

Say:

This is Smart Bus Management System, a Flask-based platform for college transport operations with role-based access, attendance tracking, mileage logs, and IoT-ready APIs.

## 2. Authentication Flow (20 sec)

Show:

- Login page
- Role-based redirection after login

Say:

Each user role gets a dedicated dashboard and controlled permissions.

## 3. Admin Workflow (30-40 sec)

Show:

- Admin dashboard
- Bus management page
- Reports or RFID logs section

Say:

Admin can manage buses, monitor operations, and control system-level workflows.

## 4. Student Workflow (25-30 sec)

Show:

- Student dashboard
- Attendance marking with pickup stop

Say:

Students can mark attendance in allowed time window and manage pickup stop details.

## 5. Driver Workflow (25-30 sec)

Show:

- Driver dashboard
- Stop-wise student data
- Attendance logs table

Say:

Drivers can quickly review assigned route data and attendance visibility.

## 6. Mileage Module (20-25 sec)

Show:

- Mileage upload form (driver)
- Pending and approval status view (admin/management)

Say:

Mileage evidence upload and approval improves accountability and operational records.

## 7. GPS and IoT Integration (25-35 sec)

Show:

- Live bus map page
- API health endpoints output
- Optional bus status API response

Say:

System supports GPS ingestion and RFID arrival workflows for real-time visibility.

## 8. Technical Close (20 sec)

Say:

The project uses Flask, SQLAlchemy, Bootstrap, and modular service-route architecture. It is GitHub-ready, deployment-ready, and structured for future scalability.

## 9. Backup Commands for Live Demo

Run these if needed before starting:

```powershell
python -m compileall app.py routes models services
python -c "from app import create_app; app=create_app(); print('ok', len(app.url_map._rules))"
python app.py
```

## 10. If Asked in Viva

Q: What problem does this solve?
A: It digitizes attendance, bus operations, and live tracking in one unified workflow.

Q: What makes it smart?
A: IoT-ready RFID and GPS APIs plus role-based operational visibility.

Q: Future improvements?
A: Full model unification migration, automated test suite, and push notifications.
