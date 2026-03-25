# Flask-Migrate Setup & Workflow Guide

## What is Flask-Migrate?

Flask-Migrate uses Alembic to manage database migrations. Migrations are version-controlled scripts that track all changes to your database schema.

**Why use migrations?**
- Track database changes over time
- Easy rollback to previous schema versions
- Team collaboration (everyone applies same migrations)
- Production-safe deployments

---

## Step-by-Step Migration Workflow

### Step 1: Initialize Migrations (One-time setup)

```bash
set FLASK_APP=app.py
flask db init
```

This creates a `migrations/` folder with migration configuration.

**Output:** Creates `migrations/` directory with alembic scripts.

---

### Step 2: Create Initial Migration from Models

```bash
set FLASK_APP=app.py
flask db migrate -m "Initial migration: create users table"
```

**What it does:**
- Scans all `db.Model` classes in your app
- Compares with current database schema
- Auto-generates migration file in `migrations/versions/`

**Output:** Creates file like `migrations/versions/001_initial_migration.py`

---

### Step 3: Apply Migration to Database

```bash
set FLASK_APP=app.py
flask db upgrade
```

**What it does:**
- Reads all pending migrations
- Executes SQL to create tables in MySQL

**Output:** Creates `users` table in `smart_bus_db`

---

## How to Use Migrations Going Forward

### When you modify a model:

**Example:** Add `phone_number` field to User:

```python
# models/user_model.py
class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(20))  # NEW FIELD
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
```

**Then run:**

```bash
set FLASK_APP=app.py
flask db migrate -m "Add phone_number to User"
flask db upgrade
```

---

## Common Flask-Migrate Commands

```bash
# Check migration status
flask db current

# List all migrations
flask db history

# Downgrade to previous version
flask db downgrade

# Show SQL for a migration (without applying)
flask db migrate --sql
```

---

## File Structure After Migration Init

```
project/
├── app.py
├── config.py
├── extensions.py
├── models/
│   ├── __init__.py
│   └── user_model.py
├── routes/
│   └── auth_routes.py
├── migrations/                 # NEW - Created by init
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/              # Auto-generated migration files
│       └── 001_initial_migration.py
└── ...
```

---

## Troubleshooting

**Error: "Can't find app"**
- Make sure `FLASK_APP=app.py` is set before running commands

**Error: "Target database is not up to date"**
- Run: `flask db upgrade`

**Error: "Already offline, cannot rollback"**
- Migrations are not tracking correctly. Check `migrations/alembic.ini`

---

## MySQL Setup Reminder

Before running migrations, ensure:

1. MySQL is running
2. Database exists:
   ```sql
   CREATE DATABASE smart_bus_db;
   ```
3. Credentials in config.py or .env are correct

---

## Next Steps

After migrations are set up:
1. Run `flask db init` from project root
2. Run `flask db migrate -m "Initial migration"`
3. Run `flask db upgrade`
4. Test signup at `http://127.0.0.1:5000/signup`
5. Check users in MySQL:
   ```sql
   USE smart_bus_db;
   SELECT * FROM users;
   ```
