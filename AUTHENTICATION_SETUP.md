cd # Authentication System Setup

## Overview
A complete authentication system has been implemented for the Food Management application with the following features:

## Features Implemented

### 1. User Registration
- **Form Fields:**
  - Username (unique validation)
  - Email (unique validation, email format validation)
  - First Name & Last Name
  - Full Name
  - Household Size (minimum 1)
  - Dietary Preferences (dropdown: none, vegetarian, vegan, pescatarian, gluten-free, keto, other)
  - Budget Range (dropdown: low, medium, high)
  - Location (optional - for future local features)
  - Password (with confirmation, Django password validators applied)

- **Validation:**
  - Email uniqueness check
  - Username uniqueness check
  - Password strength validation (Django's built-in validators)
  - Required field validation
  - Bootstrap-styled form with error messages

### 2. User Login
- Username/email login
- Password authentication
- "Remember me" redirect to next page
- Bootstrap-styled login form
- Error message display

### 3. User Logout
- Secure logout functionality
- Redirect to login page with success message

### 4. User Profile
- **Profile Model (UserProfile):**
  - One-to-one relationship with Django User
  - Full name
  - Household size
  - Dietary preferences
  - Budget range
  - Location
  - Auto-created when user registers
  - Auto-updated timestamps

- **Profile Management:**
  - View and edit profile information
  - Update email, name, and all profile fields
  - Form validation
  - Success/error messages

### 5. Security Features
- Password hashing (Django's default PBKDF2)
- CSRF protection
- Session-based authentication
- Login required decorators
- Secure password validators:
  - Minimum length (8 characters)
  - Common password check
  - Numeric-only password prevention
  - User attribute similarity check

## File Structure

```
accounts/
├── __init__.py
├── admin.py          # Admin interface for UserProfile
├── apps.py
├── forms.py          # Registration, Login, Profile forms
├── models.py         # UserProfile model
├── urls.py           # URL routing
└── views.py          # Registration, Login, Logout, Profile views

templates/
├── base.html         # Base template with navigation
└── accounts/
    ├── register.html
    ├── login.html
    └── profile.html

static/
└── css/
    └── style.css     # Custom styles
```

## Database Setup

After setting up the project, run migrations:

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

This will create:
- UserProfile table
- Link UserProfile to Django's User model

## URL Routes

- `/accounts/register/` - User registration
- `/accounts/login/` - User login
- `/accounts/logout/` - User logout
- `/accounts/profile/` - User profile view/edit

## Settings Configuration

The following settings have been configured in `settings.py`:

- `INSTALLED_APPS`: Added 'accounts' app
- `TEMPLATES`: Added templates directory
- `STATIC_URL` and `STATICFILES_DIRS`: Static files configuration
- `MEDIA_URL` and `MEDIA_ROOT`: Media files configuration
- `LOGIN_URL`: Redirect to login page
- `LOGIN_REDIRECT_URL`: Redirect after login
- `LOGOUT_REDIRECT_URL`: Redirect after logout

## Admin Interface

UserProfile is registered in Django admin with:
- Inline editing with User model
- List display: full_name, user, household_size, dietary_preferences, budget_range, location
- Search functionality
- Filtering options

## Next Steps

1. Run migrations to create database tables
2. Create superuser: `python manage.py createsuperuser`
3. Test registration, login, and profile functionality
4. Implement dashboard, inventory, logs, and resources apps
5. Update navigation links when other apps are ready

## Notes

- All forms use Bootstrap 5 styling for consistent UI
- Error messages are displayed using Django's messages framework
- The authentication system is ready for integration with other apps
- Profile is automatically created when a user registers (via Django signals)

