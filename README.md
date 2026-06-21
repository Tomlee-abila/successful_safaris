# Successful Luxury Safaris

A premium safari booking and e-commerce platform built with Django.

## Project Structure

The project follows a Domain-Driven Multi-App architecture:

- **`backend/`**: Django project root.
  - **`destinations/`**: Manages countries, national parks, and accommodations.
  - **`packages/`**: Handles safari tour packages and itineraries.
  - **`bookings/`**: Manages customer bookings, travelers, and payments.
  - **`shop/`**: E-commerce system for safari gear and apparel.
  - **`users/`**: Extended user profiles and loyalty system.
  - **`inventory/`**: Site metadata and RBAC permission matrix.
  - **`crm/`**: Customer inquiries, reviews, and trip documents.
  - **`blog/`**: Safari journal and news.
  - **`core/`**: Main frontend views and routing.

## Setup & Running the Application

### 1. Database & Environment Setup
Ensure you have Python 3.12+ and a PostgreSQL server running (or start the containerized Postgres database in the background):
```bash
# Start containerized PostgreSQL database
docker-compose up -d db

# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Initialization
```bash
# Apply migrations
python manage.py migrate

# Seed site inventory & permissions
python manage.py seed_sitemap

# Seed full business demo data (Destinations, Packages, Products, etc.)
# Use --clear if you encounter unique constraint errors or want a fresh start
python manage.py seed_business --clear
```

### 3. Running the Server
```bash
python manage.py runserver
```
The site will be available at `http://127.0.0.1:8000/`.

## Administrative Access
To access the Django Admin (`/admin/`), you will need a superuser:
```bash
python manage.py createsuperuser
```

## Testing & QA
The project includes a deep functional QA script:
```bash
python deep_qa.py
```
This script verifies routes, API endpoints, and basic workflow integrity.

## Deployment & Operations
For detailed instructions on how to configure and deploy this application in both development and production (using Docker), refer to the [Deployment & Operations Guide](file:///home/tomlee/Desktop/dev/Successful%20Safaris/docs/DEPLOYMENT.md).

