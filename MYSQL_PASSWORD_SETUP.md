# MySQL Connection Setup - Quick Fix

## Current Status
✗ MySQL connectivity error: "Access denied for user 'root'@'localhost' (using password: NO)"

This means MySQL root account requires a password, but `.env` file has an empty password.

---

## Solution Options

### Option 1: Use MySQL with NO Password (If Available)

If your MySQL root has no password, update `.env`:

```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=smart_bus_db
```

Then ensure database exists:
1. Open MySQL 8.0 Command Line Client (from Start Menu)
2. At prompt, type: `CREATE DATABASE IF NOT EXISTS smart_bus_db;`
3. Then run migrations

---

### Option 2: Use MySQL with Password

**Step 1: Find MySQL Command Line Client**
- Open Start Menu
- Search for "MySQL 8.0 Command Line Client" 
- Click it → Enter your root password when prompted

**Step 2: Update .env file**

Edit `.env` with your MySQL credentials:

```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_mysql_password
MYSQL_DB=smart_bus_db
```

Example if password is "admin123":
```ini
MYSQL_PASSWORD=admin123
```

**Step 3: Create Database**

In MySQL command line:
```sql
CREATE DATABASE IF NOT EXISTS smart_bus_db;
EXIT;
```

---

### Option 3: Enable MySQL No-Password Access

In MySQL command line (as root):

```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY '';
FLUSH PRIVILEGES;
EXIT;
```

Then update `.env`:
```ini
MYSQL_PASSWORD=
```

---

## After Setting Password

**Update `.env` file**, then run:

```powershell
$env:FLASK_APP="app.py"
& ".\.venv\Scripts\python.exe" -m flask db migrate -m "create users table"
```

**If successful, you'll see:**
```
...
Detected added table 'users'
Generating ...\migrations\versions\001_create_users_table.py ... done
```

---

## Next: Apply Migration

```powershell
$env:FLASK_APP="app.py"
& ".\.venv\Scripts\python.exe" -m flask db upgrade
```

**If successful:**
```
INFO  [alembic.migration] Running upgrade  -> 001, create users table
```

---

## Verify Table Created

Use MySQL command line:

```sql
USE smart_bus_db;
SHOW TABLES;
DESCRIBE users;
```

Should show `users` table with 6 columns.

---

## Instructions to Complete

1. **Find your MySQL root password** (check where MySQL was installed or in docs)
2. **Update `.env` file** with the password
3. **Run Flask migrations** using commands above
4. **Verify tables created** using commands above

Once done, Flask signup/login will work with real MySQL database!
