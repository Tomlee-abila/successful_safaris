# Deployment & Local Operations Guide

This guide details how to configure, run, and deploy the Successful Luxury Safaris application in both local development and secure production environments.

---

## 1. Local Development Setup

To run the application locally, follow these instructions:

### Prerequisites
- Python 3.12+
- PostgreSQL database server (running locally or via Docker Compose)

### Step-by-Step Setup
1. **Start the PostgreSQL Service (via Docker Compose):**
   To easily run PostgreSQL locally in the background without configuring a manual database server:
   ```bash
   docker-compose up -d db
   ```
   This spins up the database container on port `5432` matching the default project configuration.

2. **Navigate to the Backend:**
   ```bash
   cd backend
   ```

3. **Activate the Virtual Environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the Database:**
   Apply Django database migrations to the PostgreSQL database:
   ```bash
   python manage.py migrate
   ```

5. **Seed Initial Data:**
   Seed the site sitemap and RBAC permissions first:
   ```bash
   python manage.py seed_sitemap
   ```
   Then, seed the full business demo data (destinations, packages, products, etc.):
   ```bash
   # Use --clear to ensure a clean state
   python manage.py seed_business --clear
   ```

6. **Create a Superuser (Optional):**
   To log in to `/admin/`:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server:**
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
