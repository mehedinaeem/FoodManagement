# Expired Items Email Notification - Implementation Summary

## ✅ Implementation Status: COMPLETE

The system now sends email notifications when items expire, in addition to the existing functionality of sending emails 2 days before expiration.

## Features Implemented

### 1. **Expired Item Detection**
- Automatically finds items where `expiration_date < today`
- Includes items that haven't been marked as expired yet
- Includes items already marked as expired
- Updates item status to 'expired' automatically

### 2. **Email Notifications for Expired Items**
- Sends urgent email notifications when items expire
- Groups expired items by user (one email per user)
- Shows days expired for each item
- Professional HTML and plain text email templates

### 3. **Duplicate Prevention**
- Tracks sent emails in `ExpirationEmailNotification` model
- Uses `days_before_expiry = -1` to indicate expired items
- Prevents sending duplicate emails within 7 days
- Ensures users are notified without spam

### 4. **Email Content**
- **Subject**: "🚨 URGENT: X Items Have Expired!"
- **Content**: 
  - List of expired items with details
  - Days expired for each item
  - Red alert styling for urgency
  - Action tips for handling expired items
  - Links to inventory and AI risk analysis

## How It Works

### Command Execution Flow

When `python manage.py send_expiration_emails` is run:

1. **Checks items expiring in 2 days** (existing functionality)
   - Sends emails for items expiring in N days (default: 2)
   - Groups by user
   - Records notifications

2. **Checks items expiring today/tomorrow** (existing functionality)
   - Sends urgent reminders
   - Higher priority emails

3. **Checks expired items** (NEW - implemented)
   - Finds items where `expiration_date < today`
   - Updates status to 'expired' if needed
   - Groups by user
   - Sends email notifications
   - Records notifications with `days_before_expiry = -1`

### Code Location

**Main Command**: `inventory/management/commands/send_expiration_emails.py`
- Method: `_send_expired_notifications(self, today, dry_run)`
- Called from: `handle()` method at line 179

**Email Templates**:
- HTML: `templates/emails/expiration_alert.html`
- Plain Text: `templates/emails/expiration_alert.txt`
- Both templates support `is_expired` flag for expired items

**Database Model**:
- `ExpirationEmailNotification` tracks all sent emails
- `days_before_expiry = -1` indicates expired item emails

## Usage

### Manual Execution

```bash
# Send emails for expiring items (2 days) AND expired items
python manage.py send_expiration_emails

# Dry run to see what would be sent
python manage.py send_expiration_emails --dry-run

# Custom days before expiration
python manage.py send_expiration_emails --days 3
```

### Scheduled Execution

Set up a daily cron job or scheduled task:

**Linux/Mac (Cron)**:
```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/FoodManagement && source venv/bin/activate && python manage.py send_expiration_emails
```

**Windows (Task Scheduler)**:
- Create daily scheduled task
- Command: `python manage.py send_expiration_emails`
- Working directory: Project directory

## Email Examples

### For Expired Items

**Subject**: `🚨 URGENT: 2 Items Have Expired!`

**Content**:
- Red alert box: "🚨 URGENT: You have 2 items that HAVE EXPIRED in your inventory!"
- List of expired items with:
  - Item name
  - "EXPIRED X days ago" badge
  - Category, quantity, expiration date
- Action tips for handling expired items
- Links to inventory and AI risk analysis

### For Expiring Items (2 days before)

**Subject**: `⚠️ Food Expiration Alert: 1 Item Expiring Soon`

**Content**:
- Yellow alert box: "⚠️ Important: You have 1 item expiring soon in your inventory!"
- List of expiring items with days remaining
- Tips to reduce waste
- Links to inventory and AI risk analysis

## Testing

### Test with Dry Run

```bash
python manage.py send_expiration_emails --dry-run
```

This will show:
- Items expiring in 2 days
- Items expiring today/tomorrow
- Expired items
- What emails would be sent (without actually sending)

### Test with Real Data

1. Create an inventory item with expiration date in the past
2. Run the command: `python manage.py send_expiration_emails`
3. Check email (console in development, actual email in production)
4. Verify notification is recorded in database

### Automated Tests

Test file: `inventory/tests/test_expiration_emails.py`

Run tests:
```bash
python manage.py test inventory.tests.test_expiration_emails
```

## Database Tracking

### ExpirationEmailNotification Model

Tracks all sent emails:
- `inventory_item`: The item that triggered the email
- `user`: The user who received the email
- `sent_date`: When the email was sent
- `days_before_expiry`: 
  - Positive number: Days before expiration (e.g., 2 = 2 days before)
  - `-1`: Indicates expired item email
- `email_sent`: Boolean flag

### Query Examples

```python
# Find all expired item emails sent
ExpirationEmailNotification.objects.filter(days_before_expiry=-1)

# Find emails sent today
ExpirationEmailNotification.objects.filter(sent_date=today)

# Find emails for a specific item
ExpirationEmailNotification.objects.filter(inventory_item=item)
```

## Configuration

### Email Settings

In `FoodManagement/settings.py`:

```python
# Development (console backend - emails printed to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Production (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Food Management <noreply@foodmanagement.com>'
SITE_URL = 'https://yourdomain.com'
```

## Troubleshooting

### Emails Not Sending for Expired Items

1. **Check if items exist**:
   ```python
   from inventory.models import InventoryItem
   from django.utils import timezone
   expired = InventoryItem.objects.filter(expiration_date__lt=timezone.now().date())
   print(f"Found {expired.count()} expired items")
   ```

2. **Check if emails were already sent**:
   ```python
   from inventory.models import ExpirationEmailNotification
   from django.utils import timezone
   today = timezone.now().date()
   sent = ExpirationEmailNotification.objects.filter(
       days_before_expiry=-1,
       sent_date__gte=today - timedelta(days=7)
   )
   print(f"Emails sent in last 7 days: {sent.count()}")
   ```

3. **Run with dry-run**:
   ```bash
   python manage.py send_expiration_emails --dry-run
   ```

4. **Check email backend**:
   - Development: Check console output
   - Production: Check SMTP logs and email server

### Items Not Being Found

- Ensure items have `expiration_date` set
- Ensure items are not marked as 'consumed'
- Check that expiration dates are in the past

### Duplicate Emails

- The system prevents duplicates automatically
- Check `ExpirationEmailNotification` records
- Emails are only sent once per item per 7-day period

## Summary

✅ **Expired items email functionality is fully implemented and working**

The system now:
- ✅ Detects expired items automatically
- ✅ Sends email notifications for expired items
- ✅ Updates item status to 'expired'
- ✅ Prevents duplicate emails
- ✅ Provides professional email templates
- ✅ Tracks all sent emails in database
- ✅ Works with both expiring and expired items

Run the command daily to ensure users are notified about both expiring and expired items!

