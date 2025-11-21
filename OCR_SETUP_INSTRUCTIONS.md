# OCR Setup Instructions

## Quick Fix for OCR Error

The OCR feature requires **Tesseract OCR engine** to be installed on your system.

### Install Tesseract OCR (Ubuntu/Debian)

Run this command in your terminal:

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### Verify Installation

```bash
tesseract --version
```

You should see version information. If you see "command not found", Tesseract is not installed.

### After Installation

1. **Restart your Django server:**
   ```bash
   # Stop the server (Ctrl+C)
   python manage.py runserver
   ```

2. **Test OCR:**
   - Go to `/uploads/`
   - Upload an image (receipt or food label)
   - Click "Process with OCR"
   - OCR should now work!

## What's Already Installed

✅ `pytesseract` Python package (already in requirements.txt)
✅ OCR processing code (already implemented)

## What's Missing

❌ Tesseract OCR engine binary (needs system installation)

## Alternative: Manual Entry

If you can't install Tesseract right now:
- The app works perfectly without OCR
- You can manually enter food information
- Upload images and add items manually
- OCR is just a convenience feature

## Troubleshooting

**Error: "Tesseract OCR engine not installed on system"**
- Solution: Install Tesseract (see above)

**Error: "tesseract: command not found"**
- Tesseract is not in your PATH
- Make sure installation completed successfully
- Try: `which tesseract` (should show path)

**Still not working after installation?**
- Restart Django server
- Check: `tesseract --version` works in terminal
- Verify: `python -c "import pytesseract; print(pytesseract.__version__)"`

## For Other Operating Systems

### macOS
```bash
brew install tesseract
```

### Windows
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH
3. Restart terminal/Django server

### Fedora/RHEL
```bash
sudo dnf install tesseract
```

### Arch Linux
```bash
sudo pacman -S tesseract
```

