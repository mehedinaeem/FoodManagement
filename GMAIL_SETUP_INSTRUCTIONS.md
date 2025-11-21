# Gmail Setup Instructions for mehedinaeem00@gmail.com

## ✅ Email Configuration Updated

Your email address `mehedinaeem00@gmail.com` has been configured in `settings.py`.

## ⚠️ IMPORTANT: You Need to Add App Password

The settings are configured, but you need to add your Gmail App Password to make it work.

## Step-by-Step Setup

### Step 1: Enable 2-Factor Authentication

1. Go to: https://myaccount.google.com/security
2. Sign in with: `mehedinaeem00@gmail.com`
3. Find "2-Step Verification" section
4. Click "Get Started" or "Turn On"
5. Follow the setup process (usually requires your phone)

### Step 2: Create App Password

1. Go to: https://myaccount.google.com/apppasswords
   - Or: Google Account → Security → 2-Step Verification → App passwords
2. You'll see a dropdown menu
3. Select:
   - **App**: "Mail"
   - **Device**: "Other (Custom name)"
4. Enter name: `Food Management`
5. Click **"Generate"**
6. You'll see a 16-character password like: `abcd efgh ijkl mnop`
7. **COPY THIS PASSWORD** (you can't see it again!)

### Step 3: Add Password to settings.py

1. Open: `FoodManagement/settings.py`
2. Find line with: `EMAIL_HOST_PASSWORD = ''`
3. Replace with: `EMAIL_HOST_PASSWORD = 'your-16-char-password'`
   - Example: `EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'`
   - You can keep or remove spaces - both work

### Step 4: Test Email Sending

```bash
# Test without sending (dry run)
python manage.py send_expiration_emails --dry-run

# Test with actual email sending
python manage.py send_expiration_emails
```

## Current Configuration

**File**: `FoodManagement/settings.py`

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'mehedinaeem00@gmail.com'  # ✅ Configured
EMAIL_HOST_PASSWORD = ''  # ⚠️ ADD YOUR APP PASSWORD HERE
DEFAULT_FROM_EMAIL = 'Food Management <mehedinaeem00@gmail.com>'
```

## Troubleshooting

### Problem: "Authentication failed"
- **Solution**: Make sure you're using App Password, not your regular Gmail password
- App Password is 16 characters (with or without spaces)

### Problem: "Less secure app access"
- **Solution**: Gmail no longer supports "less secure apps"
- You MUST use App Password (requires 2-Factor Authentication)

### Problem: "Can't find App Passwords option"
- **Solution**: You need to enable 2-Factor Authentication first
- App Passwords only appear after 2FA is enabled

### Problem: "Connection refused"
- **Solution**: Check your internet connection
- Make sure EMAIL_HOST = 'smtp.gmail.com' and EMAIL_PORT = 587

## Quick Checklist

- [ ] Enabled 2-Factor Authentication on Gmail
- [ ] Created App Password at https://myaccount.google.com/apppasswords
- [ ] Copied the 16-character App Password
- [ ] Added App Password to `settings.py` (EMAIL_HOST_PASSWORD)
- [ ] Tested with `--dry-run` first
- [ ] Tested actual email sending

## Security Note

- ✅ App Passwords are safe - they're separate from your main password
- ✅ You can revoke App Passwords anytime
- ✅ Each App Password is unique and can be deleted individually
- ❌ Never share your App Password
- ❌ Don't commit passwords to Git (use environment variables in production)

## After Setup

Once configured, emails will be sent to users when:
- Items expire (expiration date passed)
- Items are expiring in 2 days
- Items are expiring today/tomorrow

Run the command daily:
```bash
python manage.py send_expiration_emails
```

Or set up a cron job to run automatically.

