# Food Management

A full-stack web application for tracking food usage, managing inventories, and promoting sustainable food practices. Supporting SDG 2: Zero Hunger and SDG 12: Responsible Consumption and Production.

## Tech Stack

- **Backend:** Django 5.2.8
- **Database:** SQLite (development)
- **Frontend:** Bootstrap 5, HTML5, CSS3
- **Python:** 3.12+

## Setup Instructions

### 1. Create and Activate Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
# Create migrations for accounts app
python manage.py makemigrations accounts

# Apply all migrations
python manage.py migrate
```

### 4. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Project Structure

```
FoodManagement/
├── FoodManagement/        # Main project settings
├── accounts/              # User auth + profiles
├── inventory/             # Food items + user inventory (coming soon)
├── logs/                  # Daily consumption logs (coming soon)
├── resources/             # Sustainable practice resources (coming soon)
├── dashboard/             # Dashboard (coming soon)
├── uploads/               # Receipt / label uploads (coming soon)
├── templates/             # Global templates
├── static/                # CSS, JS
└── media/                 # Uploaded images
```

## Features Implemented

### ✅ Authentication System
- User registration with validation
- Login/Logout functionality
- User profile management
- Password security (Django validators)
- Profile fields: full name, household size, dietary preferences, budget range, location

### 🚧 Coming Soon
- Food inventory management
- Consumption logging
- Resources for sustainable practices
- Image upload for food scanning
- Dashboard with tracking summaries

## URL Routes

- `/` - Home (redirects to login or dashboard)
- `/accounts/register/` - User registration
- `/accounts/login/` - User login
- `/accounts/logout/` - User logout
- `/accounts/profile/` - User profile view/edit
- `/admin/` - Django admin interface
- `/dashboard/` - Dashboard (placeholder)

## Environment Configuration

No environment variables required for development. The project uses SQLite database by default.

## Seed Data

Seed data scripts will be added for:
- Food items database (15-20 entries)
- Resources database (15-20 entries)

## Notes

- Make sure to activate the virtual environment before running any Django commands
- The database file `db.sqlite3` will be created automatically after running migrations
- Static files are served automatically in development mode
