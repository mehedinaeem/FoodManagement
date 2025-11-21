# Email Notifications for Expiring Items

This feature sends automated email alerts to users when their food items are about to expire.

## Features

- **Automatic Alerts**: Sends emails starting 2 days before expiration
- **Urgent Reminders**: Sends additional reminders for items expiring today or tomorrow
- **Duplicate Prevention**: Tracks sent emails to avoid duplicates
- **Beautiful HTML Emails**: Professional email templates with styling
- **User-Friendly**: Includes links to inventory and AI risk analysis

## Setup

### 1. Email Configuration

Edit `FoodManagement/settings.py`:

**For Development (Console Backend - emails printed to console):**
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**For Production (SMTP):**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # or your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Food Management <noreply@foodmanagement.com>'
SITE_URL = 'https://yourdomain.com'  # Your production domain
```

### 2. Run Migrations

```bash
python manage.py migrate inventory
```

### 3. Schedule the Command

Run the command daily using cron or a scheduled task:

**Linux/Mac (Cron):**
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM
0 9 * * * cd /path/to/FoodManagement && source venv/bin/activate && python manage.py send_expiration_emails
```

**Windows (Task Scheduler):**
- Create a scheduled task that runs daily
- Command: `python manage.py send_expiration_emails`
- Working directory: Your project directory

**Docker/Cloud:**
- Use your platform's scheduled task feature (e.g., AWS EventBridge, Google Cloud Scheduler)
- Or use Celery Beat for more advanced scheduling

## Usage

### Manual Execution

```bash
# Send emails for items expiring in 2 days (default)
python manage.py send_expiration_emails

# Send emails for items expiring in 3 days
python manage.py send_expiration_emails --days 3

# Dry run (see what would be sent without actually sending)
python manage.py send_expiration_emails --dry-run
```

### Command Options

- `--days N`: Number of days before expiration to send alerts (default: 2)
- `--dry-run`: Preview emails without sending them

## How It Works

1. **Daily Check**: The command runs daily and checks for items expiring in N days (default: 2)
2. **Grouping**: Items are grouped by user to send one email per user
3. **Tracking**: Each sent email is recorded in `ExpirationEmailNotification` to prevent duplicates
4. **Urgent Reminders**: Additional reminders are sent for items expiring today or tomorrow
5. **Email Content**: Includes item details, expiration dates, and links to manage inventory

## Email Template

The email includes:
- List of expiring items with details
- Days until expiration
- Links to inventory and AI risk analysis
- Tips to reduce waste
- Professional HTML and plain text versions

## Database Model

The `ExpirationEmailNotification` model tracks:
- Which items had emails sent
- When emails were sent
- Days before expiration when email was sent
- Prevents duplicate emails

## Testing

1. **Dry Run Test:**
   ```bash
   python manage.py send_expiration_emails --dry-run
   ```

2. **Create Test Data:**
   - Add inventory items with expiration dates 2 days from now
   - Run the command to see emails in console (development mode)

3. **Production Test:**
   - Configure SMTP settings
   - Use `--dry-run` first to verify
   - Then run without `--dry-run` to send actual emails

## Troubleshooting

**Emails not sending:**
- Check EMAIL_BACKEND setting
- Verify SMTP credentials (if using SMTP)
- Check email server logs
- Ensure users have valid email addresses

**Duplicate emails:**
- The system prevents duplicates automatically
- Check `ExpirationEmailNotification` records in admin

**Command not found:**
- Ensure you're in the project directory
- Activate virtual environment
- Check that management command file exists

## Notes

- Emails are sent starting 2 days before expiration (configurable)
- Each user receives one email per day with all their expiring items
- Urgent reminders are sent separately for today/tomorrow expirations
- The system tracks sent emails to avoid duplicates

