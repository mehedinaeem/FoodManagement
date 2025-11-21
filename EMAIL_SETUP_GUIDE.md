# Email Setup Guide

## 📧 Where Email Configuration is Located

**File**: `FoodManagement/settings.py` (lines 145-163)

## 🎯 Two Options for Email Setup

### Option 1: Development Mode (No Email Account Needed) ✅ CURRENT SETTING

**For Testing Only** - Emails are printed to the console/terminal, not actually sent.

**Current Configuration** (in `settings.py`):
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**How it works:**
- When you run `python manage.py send_expiration_emails`
- Emails are displayed in the terminal/console
- No actual emails are sent
- **No email account setup needed**

**To test:**
```bash
python manage.py send_expiration_emails
# You'll see the email content printed in the terminal
```

---

### Option 2: Production Mode (Real Email Sending) 📨

**For Real Emails** - You need to configure an email account (Gmail, Outlook, etc.)

## Step-by-Step Email Setup

### For Gmail (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Create an App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter name: "Food Management"
   - Click "Generate"
   - **Copy the 16-character password** (you'll need this)

3. **Update `settings.py`**:

```python
# Email Configuration
# Change from console backend to SMTP backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Gmail SMTP Configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'  # Your Gmail address
EMAIL_HOST_PASSWORD = 'your-16-char-app-password'  # The app password from step 2
DEFAULT_FROM_EMAIL = 'Food Management <your-email@gmail.com>'

# Site URL for email links
SITE_URL = 'http://localhost:8000'  # Change to your domain in production
```

4. **Replace the placeholders:**
   - `your-email@gmail.com` → Your actual Gmail address
   - `your-16-char-app-password` → The app password you generated

### For Outlook/Office 365

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@outlook.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'Food Management <your-email@outlook.com>'
```

### For Other Email Providers

| Provider | EMAIL_HOST | EMAIL_PORT | EMAIL_USE_TLS |
|----------|------------|------------|---------------|
| Gmail | smtp.gmail.com | 587 | True |
| Outlook | smtp.office365.com | 587 | True |
| Yahoo | smtp.mail.yahoo.com | 587 | True |
| Custom SMTP | your-smtp-server.com | 587 or 465 | True or False |

## 📝 Complete Example Configuration

**File**: `FoodManagement/settings.py`

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Changed from console

# Gmail SMTP Configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'myfoodapp@gmail.com'  # Your email
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'  # App password (16 characters)
DEFAULT_FROM_EMAIL = 'Food Management <myfoodapp@gmail.com>'

# Site URL for email links
SITE_URL = 'http://localhost:8000'  # For development
# SITE_URL = 'https://yourdomain.com'  # For production
```

## 🧪 Testing Email Configuration

### Test 1: Dry Run (No Email Sent)
```bash
python manage.py send_expiration_emails --dry-run
```

### Test 2: Send Test Email (Console Mode)
```bash
# With console backend - email prints to terminal
python manage.py send_expiration_emails
```

### Test 3: Send Real Email (SMTP Mode)
```bash
# With SMTP backend - email actually sent
python manage.py send_expiration_emails
```

### Test 4: Django Shell Test
```bash
python manage.py shell
```

Then in the shell:
```python
from django.core.mail import send_mail
from django.conf import settings

# Test email
send_mail(
    'Test Email',
    'This is a test email from Food Management.',
    settings.DEFAULT_FROM_EMAIL,
    ['your-test-email@gmail.com'],  # Your email to receive test
    fail_silently=False,
)
```

## 🔒 Security Best Practices

1. **Never commit passwords to Git**
   - Use environment variables instead
   - Add `settings.py` to `.gitignore` if it contains passwords

2. **Use Environment Variables** (Recommended):

Create a `.env` file:
```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

Update `settings.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
```

3. **Use App Passwords** (Not your main password)
   - Gmail: Use App Passwords
   - Other providers: Use application-specific passwords

## 📍 Where Email Code is Written

### 1. Email Configuration
**File**: `FoodManagement/settings.py` (lines 145-163)
- Email backend settings
- SMTP configuration
- From email address

### 2. Email Sending Code
**File**: `inventory/management/commands/send_expiration_emails.py`
- Line 136-143: Email sending code
- Line 374-381: Expired items email sending
- Uses Django's `EmailMultiAlternatives` class

### 3. Email Templates
**Files**:
- `templates/emails/expiration_alert.html` (HTML version)
- `templates/emails/expiration_alert.txt` (Plain text version)

## ❓ Troubleshooting

### Problem: "Authentication failed"
- **Solution**: Check your email and password are correct
- For Gmail: Make sure you're using an App Password, not your regular password

### Problem: "Connection refused"
- **Solution**: Check EMAIL_HOST and EMAIL_PORT are correct
- Check your firewall/network allows SMTP connections

### Problem: "Emails not sending"
- **Solution**: 
  1. Check EMAIL_BACKEND is set to SMTP (not console)
  2. Verify all SMTP settings are correct
  3. Test with a simple email first

### Problem: "Emails going to spam"
- **Solution**:
  - Use a proper domain email (not free Gmail)
  - Set up SPF/DKIM records
  - Use a professional FROM address

## ✅ Quick Start Checklist

- [ ] Decide: Development (console) or Production (SMTP)?
- [ ] If SMTP: Get email account credentials
- [ ] If Gmail: Create App Password
- [ ] Update `settings.py` with email configuration
- [ ] Test with `--dry-run` first
- [ ] Test with actual email sending
- [ ] Set up daily cron job to run the command

## 🎯 Current Status

**Your current setting**: Console backend (emails print to terminal)
- ✅ No email account needed
- ✅ Good for testing
- ❌ Emails not actually sent

**To send real emails**: Change to SMTP backend and configure email account

