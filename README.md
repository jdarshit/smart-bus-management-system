# Smart Bus Management System

A production-oriented Flask application for college bus operations with role-based dashboards, attendance, mileage evidence uploads, IoT RFID arrivals, and GPS/live tracking APIs.

## Highlights

- Role-based portals: `admin`, `management`, `driver`, `student`
- Attendance workflow with dashboard summaries
- Mileage upload and approval flow
- IoT-ready RFID bus arrival APIs
- GPS ingestion + live bus map endpoints
- Bus status snapshot APIs
- Modernized responsive UI shell (mobile sidebar, polished cards, typography, motion)

## Tech Stack

- Backend: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Mail
- Database: SQLite (default local) / MySQL (configurable)
- Frontend: Jinja2 templates, Bootstrap 5, custom CSS/JS
- IoT Integration: ESP32-compatible RFID/GPS API endpoints

## Project Structure

- `app.py`: app factory, config wiring, blueprint registration
- `config.py`: environment-driven settings
- `models/`: ORM models
- `routes/`: web and API endpoints
- `services/`: business logic layer
- `templates/`: Jinja templates
- `static/`: CSS/JS/images
- `migrations/`: database migration scripts

## Quick Start (Local)

1. Create and activate virtual environment.
2. Install dependencies.
3. Configure `.env`.
4. Initialize database.
5. Run app.

### Windows PowerShell example

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python init_db.py
python app.py
```

Open: `http://127.0.0.1:5000`

## Environment Variables

Minimum recommended `.env` keys:

```env
FLASK_ENV=development
SECRET_KEY=change-this-for-production
DATABASE_URL=sqlite:///smartbus.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_USE_TLS=true
MAIL_USE_SSL=false
UPLOAD_FOLDER=uploads/mileage
```

For MySQL, refer to:

- `MYSQL_SETUP.md`
- `MYSQL_PASSWORD_SETUP.md`

## Available Route Groups

- Auth: `/auth/*`
- Student: `/students/*`
- Driver: `/drivers/*`
- Attendance: `/attendance/*`
- Admin: `/admin/*`
- Buses: `/buses/*`
- Reports: `/reports/*`
- Mileage: `/mileage/*`
- API Health: `/api/health`
- GPS APIs: `/api/gps`, `/api/all_bus_locations`, `/api/student_bus_location/<id>`
- Bus Status APIs: `/api/bus_status`, `/api/bus_status/<bus_id>`
- IoT Bus Arrival APIs: `/api/bus-arrival`, `/api/latest-arrivals`, `/api/bus-status`

## Performance and UX Improvements Included

- Shared design tokens and modern typography (`Plus Jakarta Sans` + `Sora`)
- Improved responsive layout and mobile sidebar behavior
- Better nav active-state handling for nested routes
- Static file max-age caching enabled for faster repeat loads
- Safer file serving in mileage uploads

## Deployment

Deployment guides are already included:

- `DEPLOYMENT_GUIDE.md`
- `render.yaml`
- `Procfile`
- `runtime.txt`

## Validation Commands

```powershell
python -m compileall app.py routes models services
python -c "from app import create_app; app=create_app(); print('ok', len(app.url_map._rules))"
```

## Notes

- This repository contains legacy and newer model variants in parallel. The app is currently wired to a stable compatible set and starts successfully.
- If you plan major schema evolution, do it with migrations and end-to-end route/template sync.
