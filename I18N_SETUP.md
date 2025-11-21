# Multi-Language Support (i18n) Setup Guide

## Overview

The Food Management application supports multiple languages using Django's internationalization (i18n) framework. Currently supported languages:

- **English (en)** - Default
- **Bengali/Bangla (bn)** - বাংলা
- **Arabic (ar)** - العربية
- **Spanish (es)** - Español

## Installation Requirements

To compile translation files, you need GNU gettext tools:

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install gettext
```

### macOS
```bash
brew install gettext
```

### Windows
Download from: https://mlocati.github.io/articles/gettext-iconv-windows.html

## Generating Translation Files

After marking strings for translation in your code:

```bash
# Generate .po files for all languages
python manage.py makemessages -l bn -l ar -l es --ignore=venv

# Compile .po files to .mo files (required for translations to work)
python manage.py compilemessages
```

## Adding New Translations

1. **Mark strings in templates:**
   ```django
   {% load i18n %}
   {% trans "Your text here" %}
   ```

2. **Mark strings in Python code:**
   ```python
   from django.utils.translation import gettext as _
   message = _("Your text here")
   ```

3. **Regenerate translation files:**
   ```bash
   python manage.py makemessages -l bn -l ar -l es
   ```

4. **Edit the .po files** in `locale/<language>/LC_MESSAGES/django.po`

5. **Compile translations:**
   ```bash
   python manage.py compilemessages
   ```

## Language Switching

Users can switch languages using the language dropdown in the navigation bar. The selected language is stored in the session and persists across pages.

## RTL Support

Arabic (ar) automatically uses right-to-left (RTL) layout. The base template includes:
- `dir="rtl"` attribute for Arabic
- CSS rules for RTL layout adjustments

## Current Translation Status

### Bengali (bn)
- ✅ Navigation menu
- ✅ Dashboard
- ✅ Authentication pages
- ✅ Common actions and buttons
- ✅ Form labels
- ✅ Status values
- ✅ Categories

### Arabic (ar)
- ✅ Basic navigation
- ✅ RTL layout support

### Spanish (es)
- ✅ Basic navigation

## Notes

- Translation files are located in `locale/<language>/LC_MESSAGES/`
- `.po` files are human-readable translation files
- `.mo` files are compiled binary files used by Django
- Always run `compilemessages` after editing `.po` files
- The application falls back to English if a translation is missing

