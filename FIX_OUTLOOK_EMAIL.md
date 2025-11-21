# Fix Outlook Email Authentication Issue

## ❌ Problem

**Error**: `SMTPAuthenticationError: (535, b'5.7.3 Authentication unsuccessful`

Outlook is rejecting your email/password. This is a common issue.

## ✅ Solutions (Try in Order)

### Solution 1: Verify Password and Account

1. **Test login manually:**
   - Go to: https://outlook.office.com
   - Try logging in with: `outlook_A4E7CAB42C216044@outlook.com`
   - Password: `Jkkniu1234`
   - If login fails, password is wrong - update it

2. **Check if account is locked:**
   - Go to: https://account.microsoft.com/security
   - Check account status

### Solution 2: Enable SMTP AUTH (Most Common Fix)

**For Personal Outlook.com accounts:**

1. Go to: https://outlook.live.com/mail
2. Click Settings (gear icon) → View all Outlook settings
3. Go to Mail → Sync email
4. Look for "SMTP AUTH" or "Authenticated SMTP"
5. Enable it

**OR** (if available):
1. Go to: https://account.microsoft.com/security
2. Look for "App passwords" or "SMTP settings"
3. Enable SMTP access

### Solution 3: Create App Password (If 2FA Enabled)

If you have 2-Factor Authentication enabled:

1. Go to: https://account.microsoft.com/security
2. Click "Advanced security options"
3. Find "App passwords"
4. Create new app password for "Mail"
5. Use that 16-character password in settings.py

### Solution 4: Try Different SMTP Server

Update `settings.py` with these alternatives:

**Option A: smtp-mail.outlook.com (Personal accounts)**
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

**Option B: smtp.office365.com (Office 365)**
```python
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

**Option C: Port 25 with SSL**
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
```

### Solution 5: Use Gmail Instead (Easier)

Gmail is often more reliable for automated emails:

1. Use your Gmail account
2. Enable 2-Factor Authentication
3. Create App Password
4. Update settings.py:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-16-char-app-password'
DEFAULT_FROM_EMAIL = 'Food Management <your-email@gmail.com>'
```

## 🧪 Test After Each Change

```bash
python manage.py shell
```

Then:
```python
from django.core.mail import send_mail
from django.conf import settings

try:
    send_mail(
        'Test',
        'Test message',
        settings.DEFAULT_FROM_EMAIL,
        ['outlook_A4E7CAB42C216044@outlook.com'],
        fail_silently=False,
    )
    print("✅ SUCCESS!")
except Exception as e:
    print(f"❌ Error: {e}")
```

## 📋 Current Settings

**File**: `FoodManagement/settings.py`

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-mail.outlook.com'  # or 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'outlook_A4E7CAB42C216044@outlook.com'
EMAIL_HOST_PASSWORD = 'Jkkniu1234'  # Verify this is correct
DEFAULT_FROM_EMAIL = 'Food Management <outlook_A4E7CAB42C216044@outlook.com>'
```

## ⚠️ Important Notes

1. **Password must be correct** - Test login at outlook.office.com first
2. **SMTP AUTH must be enabled** - Check account settings
3. **App Password if 2FA** - If 2FA is on, you need app password
4. **Account type matters** - Personal vs Work accounts have different settings

## 🎯 Quick Fix Checklist

- [ ] Verified password works at outlook.office.com
- [ ] Enabled SMTP AUTH in account settings
- [ ] Created App Password if 2FA is enabled
- [ ] Tried alternative SMTP server (smtp-mail.outlook.com)
- [ ] Tested email sending after each change

## 💡 Recommendation

If Outlook continues to have issues, **Gmail is more reliable** for automated emails and easier to set up.

