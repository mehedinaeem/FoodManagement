# Food Management

A full-stack web application for tracking food usage, managing inventories, and promoting sustainable food practices. Supporting SDG 2: Zero Hunger and SDG 12: Responsible Consumption and Production.

## Tech Stack

- **Backend:** Django 5.2.8
- **Database:** SQLite (development)
- **Frontend:** Bootstrap 5, HTML5, CSS3, JavaScript
- **Python:** 3.12+
- **Image Processing:** Pillow 12.0.0

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
# Apply all migrations (creates all database tables)
python manage.py migrate
```

### 4. Seed Database with Initial Data

```bash
# Seed food items database (20 common household foods)
python manage.py seed_food_items

# Seed resources database (21 sustainable practice resources)
python manage.py seed_resources
```

### 5. Create Superuser (Required for Admin Access)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account. You'll need:
- Username
- Email address (optional)
- Password (will be hidden for security)

### 6. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Environment Configuration

No environment variables are required for development. The project uses:

- **Database:** SQLite (default Django database, stored in `db.sqlite3`)
- **Static Files:** Served from `static/` directory
- **Media Files:** Stored in `media/` directory (user uploads)
- **Debug Mode:** Enabled by default (set `DEBUG = False` for production)

### Production Considerations

For production deployment, you should:
- Set `DEBUG = False` in `settings.py`
- Configure a production database (PostgreSQL recommended)
- Set up proper static file serving
- Configure media file storage (AWS S3, etc.)
- Set `ALLOWED_HOSTS` appropriately
- Use environment variables for `SECRET_KEY`

## Seed Data Usage Instructions

### Food Items Database

The food items database contains 20 common household foods with:
- Item name and category
- Typical expiration period (in days)
- Sample cost per unit
- Storage tips
- Descriptions

**Command:**
```bash
python manage.py seed_food_items
```

**What it does:**
- Creates/updates 20 food items in the reference database
- Safe to run multiple times (updates existing items)
- Includes fruits, vegetables, dairy, grains, meat, and beverages

**Access:**
- Browse at `/inventory/food-items/`
- Use when adding items to personal inventory
- Reference for expiration and cost information

### Resources Database

The resources database contains 21 sustainable practice resources with:
- Title and description
- Category (waste reduction, storage tips, meal planning, etc.)
- Resource type (article, video, guide, tip, recipe, tool, website)
- External URLs (where applicable)

**Command:**
```bash
python manage.py seed_resources
```

**What it does:**
- Creates/updates 21 resources
- Safe to run multiple times (updates existing resources)
- Includes waste reduction, storage tips, meal planning, budget tips, nutrition, and sustainability resources

**Access:**
- Browse at `/resources/`
- View personalized recommendations at `/resources/tracking/`
- Filter by category and type

## Project Structure

```
FoodManagement/
├── FoodManagement/        # Main project settings
│   ├── settings.py        # Django settings
│   ├── urls.py            # Main URL configuration
│   ├── views.py           # Home and dashboard views
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
│
├── accounts/              # User authentication & profiles
│   ├── models.py         # UserProfile model
│   ├── views.py          # Registration, login, logout, profile
│   ├── forms.py          # Registration and profile forms
│   ├── urls.py           # Account URLs
│   └── admin.py          # Admin interface
│
├── logs/                  # Food consumption logging
│   ├── models.py         # FoodLog model
│   ├── views.py          # CRUD operations for logs
│   ├── forms.py          # Log forms and filters
│   ├── urls.py           # Log URLs
│   └── admin.py          # Admin interface
│
├── inventory/             # Food inventory management
│   ├── models.py         # InventoryItem and FoodItem models
│   ├── views.py          # Inventory and food items views
│   ├── forms.py          # Inventory forms and filters
│   ├── urls.py           # Inventory URLs
│   ├── admin.py          # Admin interface
│   └── management/
│       └── commands/
│           └── seed_food_items.py  # Seed command
│
├── resources/             # Sustainable practice resources
│   ├── models.py         # Resource model
│   ├── views.py          # Resource views and tracking
│   ├── forms.py          # Resource filters
│   ├── tracking.py       # Tracking logic and recommendations
│   ├── urls.py           # Resource URLs
│   ├── admin.py          # Admin interface
│   └── management/
│       └── commands/
│           └── seed_resources.py  # Seed command
│
├── uploads/               # Image uploads (receipts, labels)
│   ├── models.py         # Upload model
│   ├── views.py          # Upload CRUD operations
│   ├── forms.py          # Upload and association forms
│   ├── urls.py           # Upload URLs
│   └── admin.py          # Admin interface
│
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── landing.html      # Landing page
│   ├── dashboard_placeholder.html  # Dashboard
│   ├── accounts/         # Authentication templates
│   ├── logs/             # Log templates
│   ├── inventory/        # Inventory templates
│   ├── resources/        # Resource templates
│   └── uploads/          # Upload templates
│
├── static/                # Static files
│   └── css/
│       └── style.css     # Custom styles
│
├── media/                 # User uploaded files
│   └── uploads/          # Uploaded images
│
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── db.sqlite3            # SQLite database (created after migrations)
```

## Code Organization

The project follows Django best practices with clear separation of concerns:

### Models (`models.py`)
- Each app has its own models file
- Models define database structure
- Includes relationships, validators, and helper methods

### Views (`views.py`)
- Business logic and request handling
- Separate views for each app
- Login required decorators for protected views
- Clean separation of concerns

### Forms (`forms.py`)
- Form definitions and validation
- Custom widgets and styling
- Filter forms for search functionality

### URLs (`urls.py`)
- URL routing for each app
- Namespaced URLs (e.g., `accounts:login`)
- Main URLs file includes all app URLs

### Templates
- Organized by app in separate directories
- Base template for common layout
- Reusable components
- Responsive design

### Admin (`admin.py`)
- Admin interface configuration
- List displays, filters, and search
- Inline editing where appropriate

## Features Implemented

### ✅ Authentication & User Management
- User registration with validation
- Login/Logout functionality
- User profile management
- Password security (Django validators)
- Profile fields: full name, household size, dietary preferences, budget range, location

### ✅ User Profile & Consumption Logging
- Profile page with edit functionality
- Daily food consumption logging
- Manual inventory management
- Consumption history tracking

### ✅ Food Items & Inventory Database
- Seeded food items database (20 items)
- Reference database with expiration and cost info
- User inventory management
- Expiration tracking and alerts

### ✅ Resources for Sustainable Practices
- Seeded resources database (21 resources)
- Categories: waste reduction, storage tips, meal planning, budget tips, nutrition, sustainability
- Filtering and search functionality

### ✅ Basic Tracking Logic
- Rule-based resource recommendations
- Category matching (e.g., dairy → storage tips)
- Pattern detection (expiring items → preservation)
- Transparent explanations for recommendations

### ✅ Image Upload for Food Scanning
- Upload interface for receipts and food labels
- JPG/PNG support (max 10MB)
- Manual association with inventory or logs
- Image gallery view

### ✅ User Dashboard
- Statistics overview
- Recent logs and inventory
- Recommended resources
- Quick actions
- Clear navigation

## URL Routes

### Authentication
- `/` - Home (redirects to login or dashboard)
- `/accounts/register/` - User registration
- `/accounts/login/` - User login
- `/accounts/logout/` - User logout
- `/accounts/profile/` - User profile view/edit

### Food Logs
- `/logs/` - List all food logs
- `/logs/create/` - Create new log
- `/logs/<id>/` - View log details
- `/logs/<id>/edit/` - Edit log
- `/logs/<id>/delete/` - Delete log
- `/logs/history/` - Consumption history

### Inventory
- `/inventory/` - List user inventory
- `/inventory/create/` - Add inventory item
- `/inventory/<id>/` - View item details
- `/inventory/<id>/edit/` - Edit item
- `/inventory/<id>/delete/` - Delete item
- `/inventory/<id>/mark-consumed/` - Mark as consumed
- `/inventory/food-items/` - Browse food items database
- `/inventory/food-items/<id>/` - View food item details

### Resources
- `/resources/` - List all resources
- `/resources/<id>/` - View resource details
- `/resources/tracking/` - Tracking & recommendations

### Uploads
- `/uploads/` - List all uploads
- `/uploads/create/` - Upload new image
- `/uploads/<id>/` - View upload and manage associations
- `/uploads/<id>/delete/` - Delete upload

### Admin
- `/admin/` - Django admin interface (requires superuser)

## Admin Interface

Access the admin interface at `/admin/` after creating a superuser.

**Available Models:**
- Users & User Profiles
- Food Logs
- Inventory Items & Food Items
- Resources
- Uploads

**Features:**
- List views with filtering
- Search functionality
- Inline editing
- Bulk actions

## Development Notes

- Always activate the virtual environment before running Django commands
- The database file `db.sqlite3` is created automatically after migrations
- Static files are served automatically in development mode
- Media files are stored in `media/` directory
- Seed commands can be run multiple times safely (updates existing data)

## Testing the Application

1. **Create a user account:**
   - Visit `/accounts/register/`
   - Fill in registration form
   - Login at `/accounts/login/`

2. **Add inventory items:**
   - Go to `/inventory/create/`
   - Or browse `/inventory/food-items/` and add from database

3. **Log food consumption:**
   - Go to `/logs/create/`
   - Enter food details and date consumed

4. **View recommendations:**
   - Check dashboard at `/dashboard/`
   - Or visit `/resources/tracking/` for detailed analysis

5. **Upload images:**
   - Go to `/uploads/create/`
   - Upload receipt or food label
   - Associate with inventory or log

## Troubleshooting

**Issue: Migrations not working**
- Ensure virtual environment is activated
- Check that all apps are in `INSTALLED_APPS`
- Run `python manage.py makemigrations` for each app

**Issue: Static files not loading**
- Run `python manage.py collectstatic` (for production)
- Check `STATIC_URL` and `STATICFILES_DIRS` in settings

**Issue: Media files not uploading**
- Ensure `media/` directory exists
- Check `MEDIA_URL` and `MEDIA_ROOT` in settings
- Verify file permissions

**Issue: Seed commands not found**
- Ensure virtual environment is activated
- Check that management commands are in correct location
- Verify app is in `INSTALLED_APPS`

## License

This project is part of a hackathon submission supporting SDG 2: Zero Hunger and SDG 12: Responsible Consumption and Production.

