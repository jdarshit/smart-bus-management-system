# Smart Bus Management System - Production Deployment Guide

This guide prepares the project for deployment on Render or Railway with a hosted MySQL database and live ESP32 RFID integration.

## 1) Project file placement

Keep these files at the project root:
- `app.py`
- `config.py`
- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `render.yaml`
- `.env.example`
- `migrations/`

Templates and static assets remain in:
- `templates/`
- `static/`

IoT firmware remains in:
- `iot/esp32_rfid_code.ino`

## 2) Local run steps

1. Create and activate virtual environment:
   - Windows PowerShell:
     - `python -m venv .venv`
     - `.\.venv\Scripts\Activate.ps1`

2. Install dependencies:
   - `pip install -r requirements.txt`

3. Copy environment template:
   - `copy .env.example .env`

4. Set `.env` values (minimum required):
   - `SECRET_KEY`
   - `DATABASE_URL` (or local `MYSQL_*` values)
   - `MAIL_*` values for OTP

5. Run migrations:
   - `flask db upgrade`

6. Run app locally:
   - `python app.py`

7. Verify health endpoints:
   - `http://127.0.0.1:5000/health`
   - `http://127.0.0.1:5000/api/health`

## 3) Production environment variables

Set these on Render/Railway:

Core:
- `FLASK_ENV=production`
- `SECRET_KEY=<strong-random-value>`
- `DATABASE_URL=<hosted-mysql-connection-string>`
- `PORT` (provided automatically by platform)

Email OTP:
- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USE_TLS`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`

Uploads and limits:
- `UPLOAD_FOLDER=uploads/mileage`
- `ALLOWED_EXTENSIONS=png,jpg,jpeg,gif,pdf`
- `MAX_CONTENT_LENGTH=5242880`

Session and API:
- `SESSION_COOKIE_SECURE=True`
- `SESSION_COOKIE_SAMESITE=Lax`
- `PERMANENT_SESSION_LIFETIME_SECONDS=7200`
- `CORS_ORIGINS=*`

IoT settings:
- `BUS_ARRIVAL_CUTOFF_HOUR=9`
- `BUS_ARRIVAL_CUTOFF_MINUTE=10`
- `BUS_ARRIVAL_DEBOUNCE_SECONDS=15`

## 4) Render deployment steps

1. Push code to GitHub (steps in section 6).
2. In Render, click **New +** -> **Web Service**.
3. Connect your GitHub repo.
4. Build command:
   - `pip install -r requirements.txt`
5. Start command:
   - `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
6. Add all required environment variables.
7. Deploy.
8. After first successful deploy, run database migrations from Render shell:
   - `flask db upgrade`
9. Validate:
   - `/health` returns `ok`
   - `/api/health` returns JSON status

Note: `render.yaml` is already provided for infrastructure-as-code style deployment.

## 5) Railway deployment steps

1. Create new project in Railway.
2. Connect GitHub repository.
3. Add a MySQL service in Railway or connect external MySQL.
4. Set service start command:
   - `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
5. Add environment variables listed above.
6. Deploy service.
7. Run migration command from Railway shell:
   - `flask db upgrade`
8. Validate health endpoints on generated public domain.

## 6) How to push this project to GitHub

From project root:

1. Initialize git (if needed):
   - `git init`
2. Add remote:
   - `git remote add origin https://github.com/<your-user>/<your-repo>.git`
3. Add files:
   - `git add .`
4. Commit:
   - `git commit -m "Production deployment hardening for Smart Bus system"`
5. Push:
   - `git branch -M main`
   - `git push -u origin main`

Important:
- `.env` is excluded by `.gitignore`.
- Never commit live secrets.

## 7) Database migrations in production

Run after every schema change:

- Create migration locally:
  - `flask db migrate -m "describe change"`
- Commit migration files to git.
- Deploy code.
- Run upgrade in production shell:
  - `flask db upgrade`

This keeps Flask-Migrate fully operational in production.

## 8) IoT ESP32 URL update after deployment

After deployment, update ESP32 firmware in `iot/esp32_rfid_code.ino`:

- Set:
  - `SERVER_IP` / URL host to your production domain
  - Example endpoint:
    - `https://your-app-name.onrender.com/api/bus-arrival`

Recommended firmware update approach:
- Replace host value and re-upload firmware to each gate ESP32.
- Ensure school WiFi allows outbound HTTPS to your deployed domain.

## 9) CORS and ESP32 access

- API routes are exposed under `/api/*`.
- CORS is configured via `CORS_ORIGINS` (default `*`) for browser-based clients.
- ESP32 itself is not browser-based and can post directly to public endpoint.

## 10) File uploads in production

Current setup works for demos/small deployments:
- Files saved under `uploads/mileage`.
- Type validation and max-size limits are enforced.

Platform limitation:
- Render/Railway ephemeral filesystem may lose uploaded files during redeploy/restart.

Recommended long-term storage:
- Cloudinary
- Amazon S3

## 11) How to test the live system

1. Health check:
   - `GET https://<your-domain>/health`
   - `GET https://<your-domain>/api/health`
2. Login test (admin/user dashboards).
3. OTP test using existing email flow and `/test-email`.
4. Mileage upload test:
   - Upload PNG/JPG/PDF and verify DB record.
5. IoT test:
   - Send POST from Postman/ESP32:
     - `POST https://<your-domain>/api/bus-arrival`
     - Body: `{"rfid_uid":"<known_uid>"}`
6. Live arrival verification:
   - Open admin dashboard and management dashboard.
   - Confirm new arrival appears and status counters update.

## 12) Verify live arrival logs after deployment

Use one or more of:
- Render/Railway service logs (request-level output)
- Database query:
  - `SELECT id, bus_id, arrival_time, status FROM arrivals ORDER BY id DESC LIMIT 20;`
- API check:
  - `GET https://<your-domain>/api/latest-arrivals?limit=20`

If arrivals are missing:
- Verify RFID UID is assigned to an existing bus.
- Check ESP32 network access and deployed URL.
- Confirm no 404/409 responses in ESP32 serial logs.
