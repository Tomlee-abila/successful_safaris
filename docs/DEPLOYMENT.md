# Deployment & Local Operations Guide

This guide details how to configure, run, and deploy the Successful Luxury Safaris application in both local development and secure production environments.

---

## 1. Local Development Setup

To run the application locally, follow these instructions. 

### Prerequisites
- Python 3.12+
- Optional: PostgreSQL (if you want to test with a Postgres database; otherwise, the app defaults to SQLite automatically)

### Step-by-Step Setup
1. **Navigate to the Backend:**
   ```bash
   cd backend
   ```

2. **Activate the Virtual Environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Environment Variables (`.env`):**
   We provide a helper script to copy `.env.example` and automatically generate a secure `DJANGO_SECRET_KEY`:
   ```bash
   python setup_env.py
   ```
   By default, the `.env` file is set up to connect to PostgreSQL. If you want to use **SQLite** locally, simply open `.env` and comment out the lines starting with `DB_*`.

5. **Start PostgreSQL Service (Optional):**
   If you chose to use PostgreSQL in step 4, start the database service via Docker:
   ```bash
   docker-compose up -d db
   ```

6. **Initialize the Database:**
   Apply database migrations:
   ```bash
   python manage.py migrate
   ```

7. **Seed Initial Data:**
   Seed the site sitemap and RBAC permissions first:
   ```bash
   python manage.py seed_sitemap
   ```
   Then, seed the full business demo data:
   ```bash
   python manage.py seed_business --clear
   ```

8. **Create a Superuser:**
   Run our helper script to quickly set up an administrative user:
   ```bash
   python create_admin.py
   ```
   *(This script will prompt you for credentials or read them from your `.env` variables if specified).*

9. **Run the Development Server:**
   ```bash
   python manage.py runserver
   ```
   The site will be available locally at `http://127.0.0.1:8000/`.


---

## 2. Docker & Production Deployment

For production deployments, the application is configured to run containerized using **Docker** and **Docker Compose**, with **PostgreSQL** as the primary database and **Gunicorn/WhiteNoise** for serving the app and static assets.

### Docker Configuration Files
- **`backend/Dockerfile`**: Compiles python dependencies, runs `collectstatic`, and sets up Gunicorn.
- **`docker-compose.yml`**: Orchestrates the web application and a PostgreSQL database.

### Environment Variable Settings
Set the following environment variables in your deployment environment or a `.env` file at the root of the project:

| Variable | Description | Recommended Value |
| :--- | :--- | :--- |
| `DJANGO_SECRET_KEY` | Secret key for cryptographic signing | Unique, random string (e.g. `openssl rand -hex 32`) |
| `DJANGO_DEBUG` | Django debug mode toggler | `False` |
| `DJANGO_ALLOWED_HOSTS` | Safe domains hosting the app | E.g. `successfulsafaris.com,www.successfulsafaris.com` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://safari_user:password@db:5432/successful_safaris` |
| `DJANGO_CORS_ALLOW_ALL_ORIGINS` | Toggles open CORS access | `False` |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Permitted origins | E.g. `https://successfulsafaris.com` |
| `GOOGLE_CLIENT_ID` | OAuth2 Google Client ID | Obtain from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | OAuth2 Google Client Secret | Obtain from Google Cloud Console |

### Running with Docker Compose
1. **Build and Start Services:**
   ```bash
   docker-compose up -d --build
   ```
   This command pulls the database image, builds the web application container, applies database migrations, seeds the sitemap, and starts Gunicorn.

2. **Seed Business Demo Data (in container):**
   Once the containers are active, seed the database with demo products, packages, and destinations:
   ```bash
   docker-compose exec web python manage.py seed_business
   ```

3. **Check Logs:**
   ```bash
   docker-compose logs -f web
   ```

4. **Shutdown Services:**
   ```bash
   docker-compose down -v
   ```

---

## 3. Production Security Checklist

Before exposing the application to public traffic, ensure the following production security configurations are enforced.

### Running Security Audits
Run the built-in Django deployment check to scan for any misconfigurations:
```bash
docker-compose exec web python manage.py check --deploy
```

### Key Security Measures Configured
- **DEBUG Disable:** Always set `DJANGO_DEBUG=False`. Enabling debug in production leaks raw tracebacks and configuration internals to the public.
- **Allowed Hosts:** Restrict `DJANGO_ALLOWED_HOSTS` to your actual domains to protect against HTTP Host Header attacks.
- **Security Headers & Cookies:** When `DJANGO_DEBUG=False`, security headers are active:
  - `SECURE_SSL_REDIRECT = True` (Ensures all traffic is upgraded to HTTPS)
  - `SESSION_COOKIE_SECURE = True` / `CSRF_COOKIE_SECURE = True` (Flags cookies to only be transmitted over secure HTTPS connections)
  - `SECURE_HSTS_SECONDS = 31536000` (Enforces HTTP Strict Transport Security)
- **Static Assets:** Static files are compressed and cached dynamically via **WhiteNoise** directly out of Gunicorn, eliminating the need to set up external storage buckets for static resources.

---

## 4. cPanel Deployment (Phusion Passenger)

For shared hosting environments running cPanel, Phusion Passenger is utilized as the WSGI server. We have customized the codebase to support database, media, and static folder isolation out of the box in cPanel to ensure that codebase updates/redeployments do not delete user data or uploads.

Detailed step-by-step instructions for cPanel setup are located in:
👉 [cPanel Deployment Guide (docs/CPANEL_DEPLOYMENT.md)](file:///home/tomlee/Desktop/dev/Successful%20Safaris/docs/CPANEL_DEPLOYMENT.md)

