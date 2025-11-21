# Outlook Email Authentication Troubleshooting

## ❌ Current Error

```
SMTPAuthenticationError: (535, b'5.7.3 Authentication unsuccessful
```

This means Outlook is rejecting your email/password combination.

## 🔧 Solutions

### Solution 1: Enable SMTP AUTH in Outlook Account

Outlook/Office 365 may have SMTP AUTH disabled by default.

**Steps:**
1. Go to: https://outlook.office.com
2. Sign in with: `outlook_A4E7CAB42C216044@outlook.com`
3. Go to Settings → Mail → Sync email
4. Look for "SMTP AUTH" or "Authenticated SMTP"
5. Enable it if available

**OR** (if you have admin access):
1. Go to: https://admin.microsoft.com
2. Settings → Mail → POP and IMAP
3. Enable "Authenticated SMTP"

### Solution 2: Use App Password (If 2FA is Enabled)

If you have 2-Factor Authentication enabled on your Outlook account:

1. Go to: https://account.microsoft.com/security
2. Sign in with your Outlook account
3. Go to "Security" → "Advanced security options"
4. Look for "App passwords"
5. Create a new app password for "Mail"
6. Use that app password instead of your regular password

### Solution 3: Check Account Type

**Personal Outlook.com accounts** sometimes have restrictions:
- May need to enable "Less secure app access" (deprecated)
- May require app passwords
- May have SMTP disabled by default

**Office 365/Work accounts**:
- Usually require admin to enable SMTP AUTH
- May need app passwords if MFA is enabled

### Solution 4: Try Alternative SMTP Settings

Some Outlook accounts use different SMTP servers:

**Option A: Try smtp-mail.outlook.com**
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

**Option B: Try port 25**
```python
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
```

### Solution 5: Verify Password

1. Try logging into https://outlook.office.com with your credentials
2. Make sure the password is correct
3. Check if the account is locked or requires password reset

## 🧪 Test Email Connection

After making changes, test with:

```python
python manage.py shell
```

Then in the shell:
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
    print("✅ Email sent!")
except Exception as e:
    print(f"❌ Error: {e}")
```

## 📋 Quick Checklist

- [ ] Verified password is correct
- [ ] Enabled SMTP AUTH in account settings
- [ ] Created App Password if 2FA is enabled
- [ ] Checked account type (personal vs work)
- [ ] Tried alternative SMTP settings
- [ ] Tested email connection

## 🔄 Alternative: Use Gmail Instead

If Outlook continues to have issues, Gmail is often easier:

1. Use Gmail account
2. Enable 2-Factor Authentication
3. Create App Password
4. Update settings.py with Gmail SMTP

Gmail SMTP is more reliable for automated emails.

