# MySQL Connection Setup Guide

## Problem: "Access denied for user 'root'@'localhost' (using password: NO)"

This error means your database connection is trying to connect **without a password**. The password variable is empty.

---

## Step 1: Find Your MySQL Root Password

### If you just installed MySQL:

**On Windows:**
1. Open **MySQL 8.0 Command Line Client** from Start Menu
2. It might ask for password—if you set one during installation, enter it
3. If it connects without asking, the password is empty

**Test connection:**
```bash
mysql -u root -p
```
- If prompted for password, enter it
- If it connects immediately, password is empty

### Check if you have credentials:

```bash
mysql -u root
```
- If you get `mysql>` prompt → **No password is set**
- If you get error → **Password is required**

---

## Step 2: Create `.env` File in Project Root

Copy `.env.example` to create `.env`:

```bash
copy .env.example .env
```

**Edit `.env` with your actual credentials:**

```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_password_here
MYSQL_DB=smart_bus_db
```

### Examples:

**If MySQL root has NO password:**
```ini
MYSQL_PASSWORD=
```

**If MySQL root password is "admin123":**
```ini
MYSQL_PASSWORD=admin123
```

---

## Step 3: Install python-dotenv (Loads .env)

```powershell
pip install python-dotenv
```

---

## Step 4: Update config.py to Load .env

Update your `config.py`:

```python
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "smartbus-dev-secret-key")

    # MySQL database settings
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")  # Must be set in .env!
    MYSQL_DB = os.getenv("MYSQL_DB", "smart_bus_db")

    # Build connection string
    if MYSQL_PASSWORD:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        )
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

---

## Step 5: Ensure MySQL Database Exists

Open MySQL command line:

```bash
mysql -u root -p
```

Enter your password (if set).

**Create database:**

```sql
CREATE DATABASE smart_bus_db;
SHOW DATABASES;
```

You should see `smart_bus_db` in the list.

---

## Step 6: Run Flask-Migrate Commands

From project root:

### Initialize migrations (one-time):
```powershell
$env:FLASK_APP="app.py"
flask db init
```

### Generate migration from models:
```powershell
$env:FLASK_APP="app.py"
flask db migrate -m "create users table"
```

If successful, you'll see:
```
INFO  [alembic.runtime.migration] Context impl MySQLImpl.
INFO  [alembic.runtime.migration] Will assume utf8 character set.
INFO  [alembic.env] Detected added table 'users'
...
  Generating C:\...\migrations\versions\xyz_create_users_table.py ... done
```

### Apply migration to database:
```powershell
$env:FLASK_APP="app.py"
flask db upgrade
```

If successful:
```
INFO  [alembic.runtime.migration] Context impl MySQLImpl.
INFO  [alembic.runtime.migration] Will assume utf8 character set.
INFO  [alembic.migration] Running upgrade -> xyz, create users table
```

---

## Step 7: Verify Table Creation in MySQL

Open MySQL command line:

```bash
mysql -u root -p
```

**Check if table was created:**

```sql
USE smart_bus_db;
SHOW TABLES;
```

Should show:
```
+-------------------+
| Tables_in_smart_bus_db |
+-------------------+
| alembic_version   |
| users             |
+-------------------+
```

**View table structure:**

```sql
DESCRIBE users;
```

Output should show:
```
+---------------+--------------+------+-----+-------------------+-------------------+
| Field         | Type         | Null | Key | Default           | Extra             |
+---------------+--------------+------+-----+-------------------+-------------------+
| id            | int          | NO   | PRI | NULL              | auto_increment    |
| name          | varchar(100) | NO   |     | NULL              |                   |
| email         | varchar(120) | NO   | UNI | NULL              |                   |
| password_hash | varchar(255) | NO   |     | NULL              |                   |
| role          | varchar(50)  | NO   |     | NULL              |                   |
| created_at    | datetime     | NO   |     | CURRENT_TIMESTAMP |                   |
+---------------+--------------+------+-----+-------------------+-------------------+
```

---

## Complete Checklist

- [ ] Find your MySQL root password
- [ ] Create `.env` file with MySQL credentials
- [ ] Install python-dotenv: `pip install python-dotenv`
- [ ] Update config.py to load .env
- [ ] Create database: `CREATE DATABASE smart_bus_db;`
- [ ] Run: `flask db init`
- [ ] Run: `flask db migrate -m "create users table"`
- [ ] Run: `flask db upgrade`
- [ ] Verify in MySQL: `SHOW TABLES;`
- [ ] Test signup at `http://127.0.0.1:5000/signup`

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'dotenv'"
```bash
pip install python-dotenv
```

### Error: "Access denied for user 'root'@'localhost'"
- Check .env has correct password
- Verify MySQL is running: `mysql -u root -p`
- Check password in .env doesn't have special characters that need escaping

### Error: "Can't connect to MySQL server on 'localhost'"
- MySQL is not running
- Start MySQL service on Windows (Services app) or `mysql --help` on terminal

### Error: "Unknown database 'smart_bus_db'"
- Run: `CREATE DATABASE smart_bus_db;` in MySQL shell

---

## Quick Reference: Connection String Format

- **With password:** `mysql+pymysql://root:password123@localhost:3306/smart_bus_db`
- **No password:** `mysql+pymysql://root@localhost:3306/smart_bus_db`

Python automatically builds this based on your config.py and .env file.
