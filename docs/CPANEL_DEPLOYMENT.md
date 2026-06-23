# cPanel Deployment Guide: Successful Luxury Safaris

This document details the configuration requirements and step-by-step instructions to deploy the Django backend of the **Successful Luxury Safaris** platform onto a standard **cPanel hosting environment** (using Phusion Passenger).

---

## 💾 Database Choice: PostgreSQL vs. SQLite vs. MySQL

To protect your persistent data (user accounts, e-commerce transactions, bookings) and user-uploaded media files from being accidentally deleted during codebase updates, we have designed the settings to store database and asset files **outside** the `backend/` code directory by default.

This means you can completely delete the `successful_safaris/backend/` folder during a major update, re-upload it, and the website will resume right where it left off with all user data and photos completely intact.

We support three database configurations:

1. **PostgreSQL (Recommended)**: Best if your cPanel plan enables it. Data is stored safely inside the PostgreSQL database server.
2. **SQLite (Simplest for Isolation)**: The SQLite file (`db.sqlite3`) will reside in the parent directory (`successful_safaris/db.sqlite3`). Deleting the code folder will not touch it.
3. **MySQL/MariaDB (Fallback)**: Standard built-in cPanel databases.

---

## ⚙️ Step-by-Step cPanel Deployment Workflow

### 1. Create the Database (If using PostgreSQL or MySQL)

If you are using **SQLite**, skip this step entirely! Django will automatically create `db.sqlite3` outside your code folder.

#### Option A: PostgreSQL (Recommended)
1. Log into your cPanel dashboard.
2. Click **PostgreSQL Database Wizard** in the Databases section.
3. Create database `username_safari_db`, user `username_safari_user`, set a strong password, and assign **All Privileges**.

#### Option B: MySQL (Fallback)
1. Click **MySQL® Databases** in the Databases section.
2. Create database `username_safari_db`, user `username_safari_user`, set a strong password, and assign **All Privileges**.

---

### 2. Uploading the Code
1. Archive the `/backend` folder (or the whole project if utilizing a Git deployment pipeline) as a `.zip` file.
2. Open cPanel's **File Manager** and navigate to your home directory (e.g., `/home/username/`).
3. Upload the `.zip` archive and extract it. 
   - Put your code in `/home/username/successful_safaris/backend/`.
   - Your persistent files (`db.sqlite3`, `media/`, `staticfiles/`) will sit safely next to it in `/home/username/successful_safaris/`.

---

### 3. Setup the Python Application in cPanel
1. Navigate to **Setup Python App** (in the *Software* category of cPanel).
2. Click **Create Application**.
3. Fill in the parameters as follows:
   
| Parameter | Value / Recommendation | Description |
| :--- | :--- | :--- |
| **Python Version** | `3.12.x` (or `3.11.x`) | Ensure it matches your development environment (Django 6.0.5 requires Python >= 3.10). |
| **Application Root** | `successful_safaris/backend` | Path to the directory containing `manage.py` and `passenger_wsgi.py`. |
| **Application URL** | `https://yourdomain.com` (or a subdomain) | The domain where the backend API and templates will serve. |
| **Application Startup File** | `passenger_wsgi.py` | Tells Passenger which file to run. |
| **Application Entry point** | `application` | The callable inside `passenger_wsgi.py`. |

4. Click **Create**. This initializes the application and generates a Python virtual environment (`venv`) for your site.

---

### 4. Configure Environment Variables via `.env` file

Instead of manually typing variables inside the cPanel GUI, we have configured the project to support loading environment variables from a `.env` file inside your application root (`successful_safaris/backend/.env`).

Create a file named `.env` inside your `backend/` folder on cPanel and paste the following content:

```ini
# ── Django Core Settings ──────────────────────────────────────────────
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=django-insecure-slnkhczw-super-secret-key-998877
DJANGO_ALLOWED_HOSTS=successfulluxurysafaris.co.ke,www.successfulluxurysafaris.co.ke

# ── Database Configurations ───────────────────────────────────────────
# To use SQLite (e.g. for local development), comment out the DB_* lines below.
DB_ENGINE=django.db.backends.postgresql
DB_NAME=slnkhczw_safari_db
DB_USER=slnkhczw_safari_user
DB_PASSWORD=bisT@2#7C#&8p(=S
DB_HOST=localhost
DB_PORT=5432

# ── Directory Configurations (Safe Outside-Backend Storage) ──────────
DJANGO_MEDIA_ROOT=/home/slnkhczw/successful_safaris/media
DJANGO_STATIC_ROOT=/home/slnkhczw/successful_safaris/staticfiles

# ── Administrative Credentials (Optional helper vars) ─────────────────
SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@successfulluxurysafaris.co.ke
SUPERUSER_PASSWORD=ChangeThisPassword123!
```

> [!NOTE]
> Setting database credentials as individual variables (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`) means **you do not need to URL-encode your database password**. Django handles special characters automatically when these fields are loaded separately.

---

### 5. Install Python Dependencies
1. Copy the virtual environment activation command shown at the top of the Setup Python App page.
2. Log into your cPanel server via **SSH** (or open the **Terminal** tool inside cPanel).
3. Paste the activation command and press Enter.
4. Navigate to the application root:
   ```bash
   cd /home/username/successful_safaris/backend/
   ```
5. Run the dependency installation helper script:
   ```bash
   python install_deps.py
   ```
   *(This script automatically upgrades pip, installs the precompiled binary wheel for `psycopg2-binary` to avoid compiler errors, and then installs the rest of requirements.txt).*


---

### 6. Run Migrations & Seed Database
While still in the activated SSH session:
1. **Apply Migrations**:
   ```bash
   python manage.py migrate
   ```
2. **Seed Initial Business Data**:
   ```bash
   python manage.py seed_business
   ```
3. **Seed Sitemap**:
   ```bash
   python manage.py seed_sitemap
   ```
4. **Create / Update Admin Superuser**:
   To simplify superuser creation, we have provided a helper script `create_admin.py`. Run it via:
   ```bash
   python create_admin.py
   ```
   * *If the credentials `SUPERUSER_USERNAME`, `SUPERUSER_EMAIL`, and `SUPERUSER_PASSWORD` are specified in `.env`, the script will create/update the superuser instantly.*
   * *If not specified in `.env`, the script will guide you interactively in the terminal.*

---

### 7. Static & Media Asset Delivery (Preserving User Uploads)

By default, Django is now configured to put user-uploaded media files in `/home/username/successful_safaris/media/` and static files in `/home/username/successful_safaris/staticfiles/`—both of which sit safely outside your code folder.

To expose them to the web server:

1. **Collect Static Files**:
   In your SSH terminal:
   ```bash
   python manage.py collectstatic --noinput
   ```
2. **Establish Symbolic Links inside `public_html`**:
   Link your website's public static and media routes to the persistent directories located outside your code folder:
   ```bash
   ln -s /home/username/successful_safaris/staticfiles /home/username/public_html/static
   ln -s /home/username/successful_safaris/media /home/username/public_html/media
   ```

---

## 📈 Summary Checklist
- [x] `passenger_wsgi.py` configured and added to `/backend`.
- [x] Settings modified to support automatic `.env` file loading.
- [x] Database configuration split into user-friendly individual variables (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).
- [x] `create_admin.py`, `setup_env.py`, and `install_deps.py` scripts added and tracked in Git.
- [x] Migrations run successfully.
- [x] `collectstatic` executed.
- [x] Media/Static directories symlinked into `public_html`.
- [x] Python application restarted in cPanel.
