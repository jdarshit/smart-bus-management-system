# GitHub Release Checklist

Use this checklist before pushing the final project.

## 1. Local Quality Gate

- [ ] Virtual environment activates correctly
- [ ] Dependencies install from `requirements.txt`
- [ ] `python -m compileall app.py routes models services` passes
- [ ] App boots: `python -c "from app import create_app; app=create_app(); print('ok')"`
- [ ] Main workflows smoke-tested:
  - [ ] Login/signup
  - [ ] Student attendance
  - [ ] Driver dashboard
  - [ ] Admin bus management
  - [ ] Mileage upload/approve
  - [ ] GPS/IoT API endpoints

## 2. Security and Secrets

- [ ] `.env` is NOT committed
- [ ] No real credentials in source files
- [ ] `SECRET_KEY` changed for production
- [ ] Production mail/app secrets configured in host platform

## 3. Repository Hygiene

- [ ] `README.md` is present and up to date
- [ ] `.gitignore` excludes venv, db, logs, env files
- [ ] Large/unnecessary local files removed
- [ ] Migration files are consistent with current schema
- [ ] No temporary debug prints or throwaway scripts left

## 4. Deployment Readiness

- [ ] `render.yaml` and `Procfile` reflect current app entrypoint
- [ ] `runtime.txt` matches deployed Python version
- [ ] Database URL and SMTP settings set in deployment environment
- [ ] Health checks return success (`/health`, `/api/health`)

## 5. Suggested Git Commands

```powershell
git init
git add .
git commit -m "Final polish: UI/UX refresh, route fixes, runtime hardening"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## 6. Post-Push Verification

- [ ] Open repository and confirm docs render correctly
- [ ] Verify no secrets leaked in commit history
- [ ] Deploy once from clean clone
- [ ] Capture screenshots/demo GIF for project showcase
